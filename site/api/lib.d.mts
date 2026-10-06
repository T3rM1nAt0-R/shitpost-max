export declare const SLUG_RE: RegExp;
export declare const MAX_BODY_BYTES: number;
export type VoteResult = { ok: true; slug: string; delta: 1 | -1 } | { ok: false; error: string };
export declare function parseFleet(text: string): Set<string>;
export declare function parseVotesFile(text: string): Record<string, number>;
export declare function validateVote(body: unknown, allow: Set<string>): VoteResult;
export declare function parseVoteBody(text: string, allow: Set<string>): VoteResult;
export declare function applyVote(totals: Record<string, number>, slug: string, delta: number): number;
export interface RateLimiter {
  take(key: string, now?: number): boolean;
  prune(now?: number): void;
  readonly size: number;
}
export declare function createRateLimiter(opts?: { capacity?: number; windowMs?: number; maxKeys?: number }): RateLimiter;
export declare function clientIp(
  headers: Record<string, string | string[] | undefined>,
  remoteAddress: string | undefined,
): string;
