#!/usr/bin/env bash
set -uo pipefail
cd "$(dirname "$0")"

MODELS=(
  "kimi-code/k3"
  "kimi-code/kimi-for-coding"
  "kimi-code/kimi-for-coding-highspeed"
  "kimi-code/k2.6"
  "deepseek/deepseek-v4-flash"
  "deepseek/deepseek-reasoner"
)
TASKS=(bug_find spec_to_code tone_copy)

mkdir -p results
PROMPT_FILE=$(mktemp)
trap 'rm -f "$PROMPT_FILE"' EXIT

for model in "${MODELS[@]}"; do
  safe_model=$(echo "$model" | tr '/' '_')
  for task in "${TASKS[@]}"; do
    outfile="results/${safe_model}__${task}.json"
    if [ -f "$outfile" ]; then
      echo "skip (exists): $outfile"
      continue
    fi
    python3 -c "import json; open('$PROMPT_FILE','w').write(json.load(open('tasks.json'))['$task'])"
    prompt=$(cat "$PROMPT_FILE")
    echo "=== $model :: $task ==="
    start=$(date +%s.%N)
    output=$(timeout 120 kimi -m "$model" -p "$prompt" 2>&1)
    rc=$?
    end=$(date +%s.%N)
    elapsed=$(python3 -c "print(round($end - $start, 2))")
    RAW_OUT="$output" MODEL="$model" TASK="$task" ELAPSED="$elapsed" RC="$rc" OUTFILE="$outfile" python3 -c "
import json, os
json.dump({
    'model': os.environ['MODEL'],
    'task': os.environ['TASK'],
    'elapsed_sec': float(os.environ['ELAPSED']),
    'exit_code': int(os.environ['RC']),
    'raw_output': os.environ['RAW_OUT'],
}, open(os.environ['OUTFILE'], 'w'), ensure_ascii=False, indent=2)
"
    echo "  -> ${elapsed}s, exit=$rc"
  done
done

# Local Ollama arm (free, no Kimi budget spent)
LOCAL_MODEL="qwen2.5-coder:7b-instruct-q6_K"
for task in "${TASKS[@]}"; do
  outfile="results/local_qwen2.5-coder__${task}.json"
  if [ -f "$outfile" ]; then
    echo "skip (exists): $outfile"
    continue
  fi
  python3 -c "import json; open('$PROMPT_FILE','w').write(json.load(open('tasks.json'))['$task'])"
  echo "=== local:$LOCAL_MODEL :: $task ==="
  start=$(date +%s.%N)
  PAYLOAD_FILE=$(mktemp)
  MODEL_NAME="$LOCAL_MODEL" python3 -c "
import json, os
prompt = open('$PROMPT_FILE').read()
json.dump({'model': os.environ['MODEL_NAME'], 'prompt': prompt, 'stream': False}, open('$PAYLOAD_FILE', 'w'))
"
  response=$(curl -s http://localhost:1601/api/generate --data @"$PAYLOAD_FILE")
  rm -f "$PAYLOAD_FILE"
  end=$(date +%s.%N)
  elapsed=$(python3 -c "print(round($end - $start, 2))")
  RESP="$response" TASK="$task" ELAPSED="$elapsed" LOCAL_MODEL="$LOCAL_MODEL" OUTFILE="$outfile" python3 -c "
import json, os
try:
    d = json.loads(os.environ['RESP'])
    text = d.get('response', '')
except Exception as e:
    text = 'PARSE_ERROR: ' + str(e)
json.dump({
    'model': 'local/' + os.environ['LOCAL_MODEL'],
    'task': os.environ['TASK'],
    'elapsed_sec': float(os.environ['ELAPSED']),
    'exit_code': 0,
    'raw_output': text,
}, open(os.environ['OUTFILE'], 'w'), ensure_ascii=False, indent=2)
"
  echo "  -> ${elapsed}s"
done

echo "DONE"
