# Local Addons

This folder contains local extensions and deployment overlays that are intentionally kept separate from the core Open Notebook repository layout.

## What belongs here

- `cdisc/`: the local CDISC dummy-data generator frontend and its mirrored API.
- `deploy/`: local overlay compose files, Caddy configs, and Windows-focused deployment helpers.
- `archive/open-notebook-bridge/`: earlier experiments that injected custom CDISC/Ollama code directly into `api/`, `commands/`, and `frontend/src/`. These are kept for reference, but they are not part of the active deployment path.

## What stays in the core repo

- Open Notebook application code: `api/`, `open_notebook/`, `frontend/`, `commands/`
- Upstream docs and deployment guides: `docs/`, `README.md`, `ORANGEPI_DEPLOYMENT.md`
- Upstream Orange Pi support: `docker-compose.orangepi.dev.yml`, `Caddyfile.lan`, `scripts/orangepi_deploy.sh`, `scripts/rkllama_setup.sh`

## Active local deployment model

The active custom deployment uses:

- base Orange Pi stack from `docker-compose.orangepi.dev.yml`
- addon services from `local-addons/deploy/docker-compose.orangepi.addons.yml`
- CDISC runtime from `local-addons/cdisc/`
- a custom Caddy LAN config from `local-addons/deploy/Caddyfile.lan.cdisc`

Example addon startup flow:

```bash
docker compose -f docker-compose.orangepi.dev.yml -f local-addons/deploy/docker-compose.orangepi.addons.yml up -d
```

When the `/cdisc` route is needed, deploy `local-addons/deploy/Caddyfile.lan.cdisc` as the live `Caddyfile.lan` on the Orange Pi.

## Local-only runtime artifacts

These are intentionally not part of versioned addon code:

- `.secrets/`
- `docker.orangepi.local.env`
- `duckdns.env`
- `letsencrypt/`
- `local_backups/`

## Current separation decision

- Keep upstream Open Notebook files as close to base as possible.
- Keep local CDISC and Windows deployment helpers out of the core app tree.
- Keep archived experiments available, but not wired into the running app.