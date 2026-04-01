# CDISC Addon

This folder contains the local CDISC dummy-data generator addon.

## Contents

- static frontend files for the `/cdisc` UI
- `api/` mirror service used by the frontend for generation, polling, download, and health checks

## Why this lives here

The CDISC addon is not part of the core Open Notebook application model. It is deployed alongside Open Notebook on the Orange Pi, but it is intentionally isolated so the core repository can stay close to upstream.

## Runtime wiring

- Compose overlay: `local-addons/deploy/docker-compose.orangepi.addons.yml`
- Caddy LAN route config: `local-addons/deploy/Caddyfile.lan.cdisc`

## Notes

The working deployment path is the mirrored API in `api/` inside this folder, not the archived bridge code under `local-addons/archive/open-notebook-bridge/`.