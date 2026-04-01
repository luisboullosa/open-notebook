#!/usr/bin/env bash
set -euo pipefail

SSH_KEY=""
REMOTE_DIR="~/open-notebook-orangepi"
COMPOSE_FILE="compose/docker-compose.orangepi.dev.yml"
ENV_FILE="env/open-notebook.env"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --ssh-key)
      SSH_KEY="$2"; shift 2 ;;
    --remote-dir)
      REMOTE_DIR="$2"; shift 2 ;;
    --compose)
      COMPOSE_FILE="$2"; shift 2 ;;
    --env-file)
      ENV_FILE="$2"; shift 2 ;;
    --help|-h)
      echo "Usage: $0 [--ssh-key /path/to/key] [--remote-dir ~/path] [--compose compose/file.yml] [--env-file env/file] [user@]host"
      exit 0 ;;
    --*)
      echo "Unknown option: $1" >&2
      exit 1 ;;
    *)
      if [[ -z "${HOST:-}" ]]; then
        HOST="$1"
      else
        echo "Unexpected argument: $1" >&2
        exit 1
      fi
      shift ;;
  esac
done

HOST=${HOST:-root@192.168.2.129}

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing env file: $ENV_FILE" >&2
  echo "Copy env/open-notebook.env.example to $ENV_FILE first." >&2
  exit 2
fi

SSH_OPTS=()
if [[ -n "$SSH_KEY" ]]; then
  SSH_OPTS=(-i "$SSH_KEY")
fi

echo "Deploying Orange Pi platform repo to $HOST"
echo "Remote directory: $REMOTE_DIR"

ssh "${SSH_OPTS[@]}" "$HOST" "mkdir -p $REMOTE_DIR/runtime/notebook_data $REMOTE_DIR/runtime/surreal_data $REMOTE_DIR/runtime/letsencrypt"

if command -v rsync >/dev/null 2>&1; then
  rsync -av --delete \
    --exclude '.git/' \
    --exclude 'runtime/notebook_data/' \
    --exclude 'runtime/surreal_data/' \
    --exclude 'runtime/letsencrypt/' \
    --exclude '.venv/' \
    -e "ssh ${SSH_OPTS[*]}" \
    ./ "$HOST:$REMOTE_DIR/"
else
  tar --exclude='./.git' --exclude='./runtime/notebook_data' --exclude='./runtime/surreal_data' --exclude='./runtime/letsencrypt' -czf - . | \
    ssh "${SSH_OPTS[@]}" "$HOST" "mkdir -p $REMOTE_DIR && tar -C $REMOTE_DIR -xzf -"
fi

ssh "${SSH_OPTS[@]}" "$HOST" "cd $REMOTE_DIR && docker compose --env-file $ENV_FILE -f $COMPOSE_FILE pull && docker compose --env-file $ENV_FILE -f $COMPOSE_FILE up -d --remove-orphans"

echo "Deployment complete."