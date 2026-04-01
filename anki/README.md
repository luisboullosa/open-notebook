# Anki Folder

This folder is for local Anki-related notes, planning documents, and supporting assets.

## What is in here

- planning notes such as `ANKI_FEATURES.md` and `ANKI_TODO.md`
- local reference material and deck assets

## What is not in here

The production Anki feature implementation still lives in the core application:

- backend: `api/anki_service.py`, `api/anki_insights_service.py`, `commands/anki_commands.py`, `api/routers/anki.py`
- frontend: `frontend/src/app/(dashboard)/anki/` and `frontend/src/components/anki/`

This split keeps local working notes separate from the application code that belongs to Open Notebook itself.