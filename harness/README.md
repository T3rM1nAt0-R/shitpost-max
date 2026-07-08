# shitpost-max harness

The shared `tick() → produce → append → commit → push` base class. Each
plugin subclasses `Shitpost`, implements `produce()`, and lets the harness
handle persistence, commits, and pushes.

## Writing a plugin

Create a directory under the repo root and add an entry-point script such as
`tick.py`:

```python
# uptime-witness/tick.py
from harness.shitpost_base import Shitpost


class UptimeWitness(Shitpost):
    name = "uptime-witness"
    internal = False
    commit_template = "uptime: {ok}/{total} OK"

    def produce(self):
        # Return a dict for one state.jsonl line + summary.json.
        return {"ok": 3, "total": 3}


if __name__ == "__main__":
    UptimeWitness().run_tick()
```

That's it. `run_tick()` will:

1. Call `produce()`.
2. Append the result to `state.jsonl` with a UTC timestamp.
3. Write `summary.json` with the same payload.
4. Format the commit message from `commit_template`.
5. `git add`, `git commit`, and `git push` in the plugin directory.

## Return shapes

- `dict`: one state line; `commit_template` formats against it.
- `(summary_dict, [detail_dict, ...])`: each detail dict becomes its own
  state line (sharing one timestamp), `summary.json` uses `summary_dict`,
  and the commit message formats against `summary_dict`.
- `None`: skip this tick silently -- nothing is written and no commit is
  made.

## Error handling

If `produce()` raises, the harness logs the traceback to stderr, appends an
error line to `state.jsonl`, skips the commit, and returns normally so the
next cron tick is not blocked.

## Scheduling

Add one crontab line per plugin, matching the entry-point filename from the
plugin's own `design.md`:

```cron
*/5 * * * * cd /path/to/shitpost-max/uptime-witness && python3 tick.py
```
