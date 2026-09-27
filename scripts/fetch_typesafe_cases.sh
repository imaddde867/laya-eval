#!/usr/bin/env bash
set -euo pipefail

OPENJEV_DIR="$(cd "$(dirname "$0")/../../openjev" && pwd)"
CACHE_DIR="${HOME}/.cache/jevmlx/typesafe"
RESULTS_DIR="$(cd "$(dirname "$0")/.." && pwd)/results/jevmlx_baseline"

cd "$OPENJEV_DIR"
.venv/bin/python -m benchmarks.typesafe.fetch --out "$CACHE_DIR/cases.jsonl"

mkdir -p "$RESULTS_DIR"
PYTHONPATH="$OPENJEV_DIR" .venv/bin/python .venv/bin/jevmlx eval \
  --data "$CACHE_DIR/cases.jsonl" \
  --model fast \
  --track parallel \
  --scoring labels \
  --split all \
  --out "$RESULTS_DIR"

PYTHONPATH="$OPENJEV_DIR" .venv/bin/python .venv/bin/jevmlx report \
  --predictions "$RESULTS_DIR/predictions.jsonl" \
  --out "$RESULTS_DIR/report.json"

echo "cases: $CACHE_DIR/cases.jsonl"
echo "jevmlx baseline: $RESULTS_DIR/report.json"
