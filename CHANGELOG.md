# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Dedicated LAN HTTPS deployment guide for Orange Pi/Home Lab, including Windows and Android trust setup (`docs/deployment/lan-https.md`)
- Caddy LAN reverse-proxy configuration to front Open Notebook and related local services via HTTPS (`Caddyfile.lan`)
- Local CA certificate and CRL distribution endpoints for client trust + revocation checks (`/lan-ca.crt`, `/lan-ca.crl`)

### Changed
- Orange Pi dev compose now includes Caddy LAN HTTPS routing and cert mounts (`docker-compose.orangepi.dev.yml`)
- Service navigator links updated to prefer secure LAN endpoints where applicable

### Fixed
- Windows Schannel TLS failures for LAN certs by adding revocation-aware certificate workflow

## [1.2.4] - 2025-12-14

### Added
- Infinite scroll for notebook sources - no more 50 source limit (#325)
- Markdown table rendering in chat responses, search results, and insights (#325)

### Fixed
- Timeout errors with Ollama and local LLMs - increased to 10 minutes (#325)
- "Unable to Connect to API Server" on Docker startup - frontend now waits for API health check (#325, #315)
- SSL issues with langchain (#274)
- Query key consistency for source mutations to properly refresh infinite scroll (#325)
- Docker compose start-all flow (#323)

### Changed
- Timeout configuration now uses granular httpx.Timeout (short connect, long read) (#325)

### Dependencies
- Updated next.js to 15.4.10
- Updated httpx to >=0.27.0 for SSL fix
