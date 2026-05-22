#!/usr/bin/env bash
set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(CDPATH= cd -- "${SCRIPT_DIR}/.." && pwd)"

cd "${REPO_ROOT}"

export IT_SUPPORT_LOCAL_ONLY=1
export OPENAI_API_KEY=""
export IT_SUPPORT_LLM_ENABLED=0
export IT_SUPPORT_CLASSIFIER_ENABLED=0
export IT_SUPPORT_EMBEDDINGS_ENABLED=0
export ENABLE_AGENTS=0
export ENABLE_REALTIME_SUPPORT=0
export FLASK_SECRET_KEY="${FLASK_SECRET_KEY:-dev-only-local-kb-secret}"

FLASK_RUN_HOST="${FLASK_RUN_HOST:-0.0.0.0}"
FLASK_RUN_PORT="${FLASK_RUN_PORT:-5055}"

exec ./venv/bin/python -m flask --app app run \
  --host "${FLASK_RUN_HOST}" \
  --port "${FLASK_RUN_PORT}"
