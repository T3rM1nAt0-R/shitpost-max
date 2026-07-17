import json
import re
import glob
import os
import textwrap

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")
ground_truth = json.load(open(os.path.join(os.path.dirname(__file__), "ground_truth.json")))
test_cases = ground_truth["spec_to_code"]["test_cases"]

BUG_FIND_SIGNALS = [
    "duplicate", "two q", "second q", "two separate q", "repeated q",
    "second &q", "extra q=", "another q=", "conflicting q", "another &q",
    "second q=", "two competing q", "overrides the", "overwrites the",
]


def grade_bug_find(text: str) -> str:
    low = text.lower()
    low = re.sub(r"[`*_]", "", low)
    hit = any(sig in low for sig in BUG_FIND_SIGNALS) or (
        low.count("q=") >= 1 and "language" in low
        and any(k in low for k in ("ignor", "overrid", "overwrit", "clobber", "drop", "never combine", "not combined", "only honor"))
    )
    return "PASS" if hit else "FAIL"


def strip_cli_trailer(text: str) -> str:
    return re.sub(r"\n?To resume this session:.*$", "", text, flags=re.DOTALL).strip()


def extract_code(text: str) -> str:
    text = strip_cli_trailer(text)
    m = re.search(r"```(?:python)?\s*\n(.*?)```", text, re.DOTALL)
    raw = m.group(1) if m else None
    if raw is None:
        idx = text.rfind("def parse_duration")
        if idx == -1:
            return ""
        raw = text[idx:]
    return textwrap.dedent(raw).strip("\n")


def grade_spec_to_code(text: str):
    code = extract_code(text)
    if not code.strip():
        return "FAIL", "no extractable code"
    ns = {}
    try:
        exec(code, ns)
    except Exception as e:
        return "FAIL", f"code failed to exec: {e}"
    fn = ns.get("parse_duration")
    if fn is None:
        return "FAIL", "parse_duration not defined"
    failures = []
    for case in test_cases:
        try:
            result = fn(case["input"])
            if "expected_error" in case:
                failures.append(f"input={case['input']!r} expected ValueError, got {result!r}")
            elif result != case["expected"]:
                failures.append(f"input={case['input']!r} expected {case['expected']}, got {result!r}")
        except ValueError:
            if "expected_error" not in case:
                failures.append(f"input={case['input']!r} expected {case['expected']}, got ValueError")
        except Exception as e:
            failures.append(f"input={case['input']!r} raised unexpected {type(e).__name__}: {e}")
    if failures:
        return "FAIL", "; ".join(failures)
    return "PASS", "all 10 cases passed"


def clean_tone_copy(text: str) -> str:
    text = strip_cli_trailer(text)
    if "\n• " in text:
        text = text.rsplit("\n• ", 1)[-1]
    elif text.startswith("• "):
        text = text[2:]
    return text.strip()


def parse_combined(raw: str):
    parts = re.split(r"TASK\s*[123]:\s*", raw)
    parts = [p.strip() for p in parts if p.strip()]
    return parts


rows = []

# CLI-arm files: one file per (model, task)
cli_files = glob.glob(os.path.join(RESULTS_DIR, "*__bug_find.json"))
models_seen = set()
for f in sorted(cli_files):
    d = json.load(open(f))
    model = d["model"]
    if model.startswith("claude"):
        continue
    models_seen.add(model)
    bug_text = d["raw_output"]
    spec_file = f.replace("__bug_find.json", "__spec_to_code.json")
    tone_file = f.replace("__bug_find.json", "__tone_copy.json")
    spec_text = json.load(open(spec_file))["raw_output"] if os.path.exists(spec_file) else ""
    tone_text = json.load(open(tone_file))["raw_output"] if os.path.exists(tone_file) else ""
    elapsed = d.get("elapsed_sec", 0) + (json.load(open(spec_file)).get("elapsed_sec", 0) if os.path.exists(spec_file) else 0) + (json.load(open(tone_file)).get("elapsed_sec", 0) if os.path.exists(tone_file) else 0)

    bug_verdict = grade_bug_find(bug_text)
    spec_verdict, spec_detail = grade_spec_to_code(spec_text)
    rows.append({
        "model": model,
        "bug_find": bug_verdict,
        "spec_to_code": spec_verdict,
        "spec_detail": spec_detail,
        "tone_copy_text": clean_tone_copy(tone_text),
        "total_elapsed_sec": round(elapsed, 1),
    })

# Claude combined files
for f in sorted(glob.glob(os.path.join(RESULTS_DIR, "claude_*__combined.json"))):
    d = json.load(open(f))
    model = d["model"]
    parts = parse_combined(d["raw_output"])
    if len(parts) < 3:
        rows.append({"model": model, "bug_find": "FAIL", "spec_to_code": "FAIL",
                      "spec_detail": "could not parse 3 labeled sections",
                      "tone_copy_text": "", "total_elapsed_sec": d.get("elapsed_sec_total_call", 0)})
        continue
    bug_text, spec_text, tone_text = parts[0], parts[1], parts[2]
    bug_verdict = grade_bug_find(bug_text)
    spec_verdict, spec_detail = grade_spec_to_code(spec_text)
    rows.append({
        "model": model,
        "bug_find": bug_verdict,
        "spec_to_code": spec_verdict,
        "spec_detail": spec_detail,
        "tone_copy_text": clean_tone_copy(tone_text),
        "total_elapsed_sec": d.get("elapsed_sec_total_call", 0),
    })

json.dump(rows, open(os.path.join(RESULTS_DIR, "..", "graded.json"), "w"), indent=2, ensure_ascii=False)
for r in rows:
    print(f"{r['model']:35s} bug={r['bug_find']:4s} spec={r['spec_to_code']:4s} time={r['total_elapsed_sec']}s")
    if r["spec_to_code"] == "FAIL":
        print(f"    -> {r['spec_detail']}")
