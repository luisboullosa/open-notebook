#!/usr/bin/env bash
set -euo pipefail
#
# Install and start llama-server systemd services on the Orange Pi.
# Run as root on the device, or via:
#   ssh root@192.168.2.129 'bash -s' < scripts/llama_setup.sh
#
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== llama-server setup ==="

# ---- Copy unit files ----
for svc in llama-chat.service llama-embed.service; do
  src="${SCRIPT_DIR}/${svc}"
  if [ ! -f "$src" ]; then
    echo "ERROR: ${src} not found. Run this script from the repo root."
    exit 1
  fi
  echo "Installing ${svc} ..."
  cp "$src" /etc/systemd/system/
done

systemctl daemon-reload

# ---- Ensure the chat model exists ----
CHAT_MODEL="/root/projects/models/gemma-3-1b-it-Q8_0.gguf"
if [ ! -f "$CHAT_MODEL" ]; then
  echo "WARNING: Chat model not found at ${CHAT_MODEL}."
  echo "         Download it manually or update the service file path."
fi

# ---- Pre-download embedding model (llama-server caches to ~/.cache/llama.cpp) ----
EMBED_CACHE="$HOME/.cache/llama.cpp"
EMBED_FILE=$(find "$EMBED_CACHE" -name '*mxbai*' -type f 2>/dev/null | head -1)
if [ -z "$EMBED_FILE" ]; then
  echo "Pre-downloading mxbai-embed-large GGUF (first run only) ..."
  /root/projects/rk-llama.cpp/build/bin/llama-server \
    --host 127.0.0.1 --port 19999 --embedding \
    -hf ChristianAzinn/mxbai-embed-large-v1-gguf \
    --no-warmup &
  DL_PID=$!
  # Wait for model load or failure (max 5 min)
  for i in $(seq 1 60); do
    if curl -sf http://127.0.0.1:19999/health >/dev/null 2>&1; then
      echo "Embedding model downloaded and ready."
      break
    fi
    if ! kill -0 $DL_PID 2>/dev/null; then
      echo "ERROR: llama-server exited during download."
      exit 1
    fi
    sleep 5
  done
  kill $DL_PID 2>/dev/null || true
  wait $DL_PID 2>/dev/null || true
else
  echo "Embedding model already cached: ${EMBED_FILE}"
fi

# ---- Enable and start ----
for svc in llama-chat llama-embed; do
  systemctl enable "${svc}.service"
  systemctl restart "${svc}.service"
  echo "Started ${svc}.service"
done

echo ""
echo "=== Verification ==="
sleep 3

for port in 8081 8082; do
  if curl -sf "http://localhost:${port}/health" >/dev/null 2>&1; then
    echo "  Port ${port}: OK"
  else
    echo "  Port ${port}: NOT READY (may still be loading)"
  fi
done

echo ""
echo "Chat server:     http://localhost:8081  (gemma-3-1b-it)"
echo "Embedding server: http://localhost:8082  (mxbai-embed-large)"
echo ""
echo "Done. Configure open-notebook with:"
echo "  OPENAI_COMPATIBLE_BASE_URL_LLM=http://host.docker.internal:8081/v1"
echo "  OPENAI_COMPATIBLE_BASE_URL_EMBEDDING=http://host.docker.internal:8082/v1"
