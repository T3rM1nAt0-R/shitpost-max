"""Compares a fixed .env.example against a fixed .env, reporting missing/extra variables. Same verdict every tick."""

from harness.shitpost_base import Shitpost

EXAMPLE_VARS = ["DATABASE_URL", "API_KEY", "PORT", "DEBUG", "SECRET_KEY"]
ACTUAL_VARS = ["DATABASE_URL", "PORT", "DEBUG", "REDIS_URL"]


class EnvDiffPlugin(Shitpost):
    """Emit missing/extra env vars every tick (stateless, constant result)."""

    name = "env-diff"
    internal = False
    commit_template = "env-diff: {missing} missing, {extra} extra"

    def produce(self) -> dict:
        missing = sorted(set(EXAMPLE_VARS) - set(ACTUAL_VARS))
        extra = sorted(set(ACTUAL_VARS) - set(EXAMPLE_VARS))
        return {"missing": missing, "extra": extra}
