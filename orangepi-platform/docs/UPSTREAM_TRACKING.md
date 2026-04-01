# Upstream Tracking

This repo should treat Open Notebook upstream as a dependency and reference source, not as a branch to merge continuously.

## Upstream source

- Repository: `https://github.com/lfnovo/open-notebook`
- Published image tag: `lfnovo/open_notebook:v1-latest-single`

## Current known published multi-arch image digests

- amd64: `sha256:fdea66dec64a48618af586649d15591b1f9b48c829864ae0732c960e69a336ec`
- arm64: `sha256:a3c9c6a7e8e3aca7c0dadccf8b6cd762fea7b3285508f97d682aeadca4fc8b5d`

If you want deterministic deployments, pin by digest instead of by mutable tag.

## Review cadence

- check upstream when you want a new feature or bugfix
- review changes to image behavior, env vars, and deployment assumptions
- do not merge upstream source into this repo by default

## Local deltas this repo owns

- Orange Pi Docker Compose topology
- LAN Caddy routing and certificate handling
- rk-llama replacement for Ollama
- model migration and verification helpers
- deployment scripts
- local addon overlays