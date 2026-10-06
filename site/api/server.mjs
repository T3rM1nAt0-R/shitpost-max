// shitpostmax upvotes API. Node 22, zero dependencies.
//   GET  /api/votes   -> {slug: total}
//   POST /api/vote    {slug, delta: 1|-1} -> {slug, total}
//   GET  /api/health  -> {ok: true}
import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import {
  MAX_BODY_BYTES,
  applyVote,
  clientIp,
  createRateLimiter,
  parseFleet,
  parseVoteBody,
  parseVotesFile,
} from "./lib.mjs";

const PORT = Number(process.env.PORT || 3000);
const HOST = process.env.HOST || "0.0.0.0";
const FLEET_FILE = process.env.FLEET_FILE || "/app/fleet.json";
const DATA_DIR = process.env.DATA_DIR || "/data";
const VOTES_FILE = path.join(DATA_DIR, "votes.json");
const FLUSH_MS = 2000;
const RATE_PER_MIN = Number(process.env.RATE_PER_MIN || 30);

const log = (...a) => console.log(new Date().toISOString(), ...a);

function loadFleet() {
  try {
    const set = parseFleet(fs.readFileSync(FLEET_FILE, "utf8"));
    log(`fleet: ${set.size} slugs from ${FLEET_FILE}`);
    return set;
  } catch (err) {
    log(`fleet: cannot load ${FLEET_FILE} (${err.message}); all votes will be rejected`);
    return new Set();
  }
}

function loadVotes() {
  let text;
  try {
    text = fs.readFileSync(VOTES_FILE, "utf8");
  } catch (err) {
    if (err.code !== "ENOENT") log(`votes: cannot read ${VOTES_FILE} (${err.message})`);
    return Object.create(null);
  }
  try {
    const v = parseVotesFile(text);
    log(`votes: loaded ${Object.keys(v).length} slugs`);
    return v;
  } catch (err) {
    const bak = `${VOTES_FILE}.${Date.now()}.bak`;
    try {
      fs.renameSync(VOTES_FILE, bak);
      log(`votes: corrupt file (${err.message}); moved to ${bak}, starting empty`);
    } catch (e2) {
      log(`votes: corrupt file (${err.message}); could not back up (${e2.message}), starting empty`);
    }
    return Object.create(null);
  }
}

const allow = loadFleet();
const totals = loadVotes();
const limiter = createRateLimiter({ capacity: RATE_PER_MIN, windowMs: 60_000 });
let dirty = false;

function flush() {
  if (!dirty) return;
  dirty = false;
  const tmp = `${VOTES_FILE}.tmp`;
  try {
    fs.writeFileSync(tmp, JSON.stringify(totals));
    fs.renameSync(tmp, VOTES_FILE);
  } catch (err) {
    dirty = true;
    log(`votes: flush failed (${err.message})`);
  }
}

const flushTimer = setInterval(flush, FLUSH_MS);
const pruneTimer = setInterval(() => limiter.prune(), 60_000);

function send(res, status, body, extra = {}) {
  const json = JSON.stringify(body);
  res.writeHead(status, {
    "Content-Type": "application/json; charset=utf-8",
    "Content-Length": Buffer.byteLength(json),
    "Cache-Control": "no-store",
    "X-Content-Type-Options": "nosniff",
    ...extra,
  });
  res.end(json);
}

function readBody(req, res, cb) {
  const declared = Number(req.headers["content-length"] || 0);
  if (declared > MAX_BODY_BYTES) {
    send(res, 413, { error: "body too large" }, { Connection: "close" });
    req.destroy();
    return;
  }
  const chunks = [];
  let size = 0;
  let done = false;
  req.on("data", (c) => {
    if (done) return;
    size += c.length;
    if (size > MAX_BODY_BYTES) {
      done = true;
      send(res, 413, { error: "body too large" }, { Connection: "close" });
      req.destroy();
      return;
    }
    chunks.push(c);
  });
  req.on("end", () => {
    if (!done) {
      done = true;
      cb(Buffer.concat(chunks).toString("utf8"));
    }
  });
  req.on("error", () => {
    done = true;
  });
}

const routes = {
  "/api/health": ["GET", "HEAD"],
  "/api/votes": ["GET", "HEAD"],
  "/api/vote": ["POST"],
};

const server = http.createServer((req, res) => {
  const url = (req.url || "/").split("?")[0];
  const methods = routes[url];
  if (!methods) return send(res, 404, { error: "not found" });
  if (!methods.includes(req.method)) return send(res, 405, { error: "method not allowed" }, { Allow: methods.join(", ") });

  if (url === "/api/health") return send(res, 200, { ok: true });
  if (url === "/api/votes") return send(res, 200, totals);

  // POST /api/vote
  const ip = clientIp(req.headers, req.socket.remoteAddress);
  if (!limiter.take(ip)) return send(res, 429, { error: "slow down" }, { "Retry-After": "10" });
  readBody(req, res, (text) => {
    const v = parseVoteBody(text, allow);
    if (!v.ok) return send(res, 400, { error: v.error });
    const total = applyVote(totals, v.slug, v.delta);
    dirty = true;
    send(res, 200, { slug: v.slug, total });
  });
});

server.headersTimeout = 10_000;
server.requestTimeout = 10_000;
server.listen(PORT, HOST, () => log(`listening on ${HOST}:${PORT}, data in ${DATA_DIR}`));

function shutdown(sig) {
  log(`${sig}: flushing and exiting`);
  clearInterval(flushTimer);
  clearInterval(pruneTimer);
  flush();
  server.close(() => process.exit(0));
  setTimeout(() => process.exit(0), 3000).unref();
}
process.on("SIGTERM", () => shutdown("SIGTERM"));
process.on("SIGINT", () => shutdown("SIGINT"));
