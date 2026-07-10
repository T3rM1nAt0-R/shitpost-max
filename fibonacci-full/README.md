# fibonacci-full

A fire-and-forget shitpost-max plugin that emits one full Fibonacci number per tick using Python's arbitrary-precision integers.

- `fibonacci_plugin.py` — plugin implementation
- `tick.py` — cron entry point; run this each tick
- `fibonacci.txt` — one Fibonacci number per line
- `state.jsonl` — harness-written JSONL metadata log
- `fibonacci_state.json` — internal running state `(a, b, n, tick)`

## Algorithm

`F(0) = 0`, `F(1) = 1`, `F(n) = F(n-1) + F(n-2)`.
The plugin stores the next number to emit in `a` and the one after in `b`.
Each tick emits `a`, then shifts `(a, b) = (b, a + b)`.

## Configuration

- `TICK_SECONDS=60` — intended cron interval (the harness does not enforce this)
- `commit_template = "fibonacci F({n}): {fibonacci}"`

## Running

```bash
python fibonacci-full/tick.py
```

Each invocation appends exactly one Fibonacci number and commits.
