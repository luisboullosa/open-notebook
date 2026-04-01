# Orange Pi Platform Repo Scaffold

This folder is the starting point for splitting the Orange Pi deployment out of the Open Notebook fork into its own Git repository.

The goal is to keep only the platform and deployment layer here:

- Orange Pi Docker Compose files
- LAN Caddy configuration
- rk-llama setup and migration helpers
- deployment scripts
- lightweight sidecar services such as the Whisper OpenAI adapter

This scaffold intentionally does not include the Open Notebook application source tree.
It is designed to run against the published upstream image:

- `lfnovo/open_notebook:v1-latest-single`

## Intended extraction

Create a new repository and move the contents of this folder to that repo root.

Suggested repository name:

- `open-notebook-orangepi`

## Layout

- `compose/`: Orange Pi compose files
- `config/`: Caddy and service navigator config
- `docs/`: migration notes and upstream tracking notes
- `env/`: environment file templates
- `scripts/`: deployment and rk-llama helpers
- `services/`: lightweight sidecars owned by this platform repo
- `runtime/`: local runtime state on the Orange Pi host; ignored by git

## Quick start

1. Copy `env/open-notebook.env.example` to `env/open-notebook.env`.
2. Fill in the password, encryption key, and LAN IP values.
3. Place LAN TLS assets under `runtime/letsencrypt/lan/` if you want HTTPS through Caddy.
4. Run:

```bash
docker compose --env-file env/open-notebook.env -f compose/docker-compose.orangepi.dev.yml up -d
```

## What to migrate from the current fork

- `docker-compose.orangepi.dev.yml`
- `docker.orangepi.env`
- `Caddyfile.lan`
- `scripts/orangepi_deploy.sh`
- `scripts/rkllama_setup.sh`
- `scripts/verify_rkllama_migration.sh`
- `scripts/whisper_openai_adapter/`
- `setup_guide/service-navigator/index.html`
- any local addon overlays you still want to keep

## What not to move here

- `api/`
- `open_notebook/`
- `commands/`
- `frontend/`
- `tests/`

Those belong to the upstream app, not to the Orange Pi platform repo.