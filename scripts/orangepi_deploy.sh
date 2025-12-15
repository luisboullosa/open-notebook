#!/usr/bin/env bash
# Simple Orange Pi deployment script
# Usage: ./orangepi_deploy.sh [user@]host [local_secrets_dir] [repo_url]
# Defaults: host=192.168.2.129, local_secrets_dir=./secrets, repo_url will use origin remote

set -euo pipefail

SSH_KEY=""
COMPOSE_ARG=""

# parse optional flags
while [[ $# -gt 0 ]]; do
  case "$1" in
    --ssh-key)
      SSH_KEY="$2"; shift 2;;
    --compose)
      COMPOSE_ARG="$2"; shift 2;;
    --help|-h)
      echo "Usage: $0 [--ssh-key /path/to/key] [--compose /path/to/local-compose.yml] [user@]host [local_secrets_dir] [repo_url]";
      exit 0;;
    --*)
      echo "Unknown option: $1"; exit 1;;
    *)
      # first non-option is HOST
      if [ -z "${HOST+x}" ]; then
        HOST="$1"
      elif [ -z "${LOCAL_SECRETS_DIR+x}" ]; then
        LOCAL_SECRETS_DIR="$1"
      elif [ -z "${REPO_URL+x}" ]; then
        REPO_URL="$1"
      else
        shift
        continue
      fi
      shift;;
  esac
done

# defaults (if not set by flags/args)
HOST=${HOST:-root@192.168.2.129}
LOCAL_SECRETS_DIR=${LOCAL_SECRETS_DIR:-./.secrets}
REPO_URL=${REPO_URL:-}

# Try to detect repo URL if not provided
if [ -z "$REPO_URL" ]; then
  if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    REPO_URL=$(git remote get-url origin)
  else
    echo "No repo URL provided and not inside a git repo. Provide a repo URL as 3rd arg." >&2
    exit 1
  fi
fi

REMOTE_DIR="~/open-notebook"

SSH_OPTS=""
# Prefer SSH agent if available (no -i), otherwise use provided key
if [ -n "$SSH_KEY" ]; then
  if [ -n "${SSH_AUTH_SOCK:-}" ]; then
    echo "SSH agent detected (SSH_AUTH_SOCK set) — using agent, not passing -i"
    SSH_OPTS=""
  else
    SSH_OPTS="-i $SSH_KEY"
  fi
fi

echo "Deploying to $HOST (ssh will prompt for password if needed, ssh-key=${SSH_KEY:-none})"
echo "Repo: $REPO_URL"
echo "Secrets dir: $LOCAL_SECRETS_DIR"

ssh $SSH_OPTS "$HOST" bash -lc "'
  set -e
  mkdir -p $REMOTE_DIR
  cd $REMOTE_DIR
  if [ -d .git ]; then
    git fetch --all --prune
    git reset --hard origin/main || true
    git pull || true
  else
    git clone $REPO_URL . || true
  fi
  mkdir -p $REMOTE_DIR/notebook_data
'"

echo "Copying secrets from $LOCAL_SECRETS_DIR to $HOST:$REMOTE_DIR"
if [ -d "$LOCAL_SECRETS_DIR" ]; then
  if command -v rsync >/dev/null 2>&1; then
    if [ -n "$SSH_OPTS" ]; then
      rsync -av -e "ssh $SSH_OPTS" --prune-empty-dirs --relative "$LOCAL_SECRETS_DIR/" "$HOST:$REMOTE_DIR/"
    else
      rsync -av --prune-empty-dirs --relative "$LOCAL_SECRETS_DIR/" "$HOST:$REMOTE_DIR/"
    fi
  elif command -v scp >/dev/null 2>&1; then
    echo "rsync not found — using scp fallback"
    scp -r $SSH_OPTS "$LOCAL_SECRETS_DIR/" "$HOST:$REMOTE_DIR/"
  else
    echo "Neither rsync nor scp found locally — cannot copy secrets automatically." >&2
    echo "Please copy $LOCAL_SECRETS_DIR to $HOST:$REMOTE_DIR manually." >&2
  fi
else
  echo "Local secrets dir $LOCAL_SECRETS_DIR not found — skipping copy." >&2
fi

# If a LAN-friendly dev compose exists locally, copy it to remote as the compose file
COMPOSE_LOCAL="${COMPOSE_ARG:-./docker-compose.orangepi.dev.yml}"
if [ -f "$COMPOSE_LOCAL" ]; then
  echo "Found $COMPOSE_LOCAL — copying to remote as docker-compose.orangepi.dev.yml"
  scp $SSH_OPTS "$COMPOSE_LOCAL" "$HOST:$REMOTE_DIR/docker-compose.orangepi.dev.yml"
else
  echo "No $COMPOSE_LOCAL found locally — leaving existing remote compose in place." 
fi

# Verify remote has compose file; if not, try to push workspace (tar over ssh) as fallback
echo "Verifying remote compose file exists..."
if ! ssh $SSH_OPTS "$HOST" test -f $REMOTE_DIR/docker-compose.orangepi.dev.yml >/dev/null 2>&1; then
  echo "Remote compose not found. Attempting to copy workspace to remote using tar+ssh (excludes .git, large data)..."
  if command -v tar >/dev/null 2>&1 && command -v ssh >/dev/null 2>&1; then
    TAR_SSH_OPTS=""
    if [ -n "$SSH_OPTS" ]; then
      TAR_SSH_OPTS="$SSH_OPTS"
    fi
    tar --exclude='./.git' --exclude='./surreal_single_data*' --exclude='./notebook_data*' -czf - . | ssh $TAR_SSH_OPTS "$HOST" 'mkdir -p $REMOTE_DIR && tar -C $REMOTE_DIR -xzf -'
  else
    echo "tar or ssh not available locally. Falling back to scp of key files."
    scp docker-compose.orangepi.yml "$HOST:$REMOTE_DIR/" || true
    scp -r ./.secrets "$HOST:$REMOTE_DIR/" || true
  fi
else
  echo "Remote compose file exists — not copying whole workspace."
fi

echo "Installing/updating containers on remote..."
ssh "$HOST" bash -lc "'
  set -e
  cd $REMOTE_DIR
  # Use docker compose orchestrator for Orange Pi file
  if command -v docker >/dev/null 2>&1 && command -v docker-compose >/dev/null 2>&1; then
    docker compose -f docker-compose.orangepi.dev.yml pull || true
    docker compose -f docker-compose.orangepi.dev.yml up -d --remove-orphans
  else
    echo "Docker not found on remote. Install Docker and Docker Compose before running this script." >&2
    exit 2
  fi
'"

echo "Deployment finished. Remote branch and containers should be up."

echo "Important — files you should copy into $LOCAL_SECRETS_DIR before running:"
cat <<EOF
- docker.orangepi.env        (Orange Pi specific env overrides)
- docker.env                 (general docker env with secrets)
- duckdns.env                (if using dynamic DNS)
- letsencrypt/               (TLS files if you manage certs locally)
- notebook_data/             (optional: rsync your notebook_data backups, but avoid committing to git)
EOF

echo "Example: ./orangepi_deploy.sh 192.168.2.129 ./secrets https://github.com/your/repo.git"
