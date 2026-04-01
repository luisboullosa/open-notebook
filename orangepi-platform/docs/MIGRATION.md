# Migration From The Fork

This scaffold is meant to become its own repository.

## Copy into the new repo

- everything under this `orangepi-platform/` folder
- optional addon overlays you still want to keep operating

## Leave behind in the current fork

- upstream application code
- upstream docs
- old experimental bridge code
- historical git branches and merge experiments

## Recommended cutover

1. Create a new Git repository.
2. Move the contents of `orangepi-platform/` into that repo root.
3. Copy `env/open-notebook.env.example` to `env/open-notebook.env`.
4. Fill in secrets and LAN-specific values.
5. Copy any required runtime assets to `runtime/`, especially LAN certs.
6. Run the new repo against a test Orange Pi first.
7. Once validated, stop deploying from the current fork.

## Why this works better

Your Orange Pi stack is no longer maintained as a fork of the application source.
It becomes its own deployment product that consumes the upstream image intentionally.