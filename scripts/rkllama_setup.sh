#!/usr/bin/env sh
set -eu

echo "Starting RKLLama model setup..."
LEGACY_ROOT="/ollama/models/manifests"

if [ -d "$LEGACY_ROOT" ]; then
  echo "Found legacy Ollama manifests. Attempting to migrate model names to RKLLama..."
  MIGRATED_MODELS=$(find "$LEGACY_ROOT" -type f | sed 's#\\#/#g' | awk -F'/manifests/' 'NF>1 {print $2}' | awk -F'/' '
    {
      if (NF >= 3) {
        tag=$NF
        model=$(NF-1)
        if ($(NF-2) != "library") {
          model=$(NF-2) "/" model
        }
        print model ":" tag
      }
    }
  ' | sort -u)

  if [ -n "$MIGRATED_MODELS" ]; then
    for model in $MIGRATED_MODELS; do
      echo "Migrating $model to RKLLama (best-effort)..."
      payload=$(printf '{"model":"%s","stream":false}' "$model")
      if curl -fsS -X POST "http://ollama:11434/api/pull" -H "Content-Type: application/json" -d "$payload" >/dev/null; then
        echo "Migrated $model"
      else
        echo "Could not auto-migrate $model (may require manual RKLLM model setup)."
      fi
    done
  else
    echo "No legacy model names discovered from manifests."
  fi
else
  echo "No legacy Ollama data volume found; skipping migration step."
fi

REQUIRED_MODELS="mxbai-embed-large:latest qwen2.5:1.5b qwen2.5:3b"
for model in $REQUIRED_MODELS; do
  echo "Ensuring required model $model exists in RKLLama..."
  payload=$(printf '{"model":"%s","stream":false}' "$model")
  if curl -fsS -X POST "http://ollama:11434/api/pull" -H "Content-Type: application/json" -d "$payload" >/dev/null; then
    echo "Ready: $model"
  else
    echo "Failed to ensure $model. Please add it manually to RKLLama models."
  fi
done

echo "RKLLama model setup complete."
