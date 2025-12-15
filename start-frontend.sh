#!/usr/bin/env bash
set -euo pipefail

# Wrapper to start the Next.js production server from inside the container
cd /app/frontend

# Ensure local node_modules/.bin is on PATH so `next` is resolvable
export PATH=/app/frontend/node_modules/.bin:$PATH

# Ensure production env
export NODE_ENV=production

# Exec the start script so PID 1 replacement occurs under supervisor
exec npm run start
