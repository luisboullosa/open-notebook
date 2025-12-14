# Archived Dev/Test Artifacts

This file documents dev/test artifacts moved to `scripts/archived/` during the `anki/cleanup` branch work.

Why archived
- These files were used for local development, debugging, and manual verification of the Anki pipeline (Whisper/Piper tests, temporary model responses, and example payloads).
- They are not required for production functionality and clutter the repository root; archiving keeps them available for future reference while decluttering the repo.

Files moved
- gen_response.json
- insight_full.json
- openapi_whisper.json
- piper_wyoming_out.raw
- preview.json
- test_whisper.wav
- tmp_parser.py
- tmp_payload.json
- tmp_resp.json
- tmp_transform_response.json
- test_card_creation_paths.py
- test_card_generation_extended.py

Scripts moved to `scripts/archived/`
- scripts/generate_test_wav.py
- scripts/piper_http_proxy.py
- scripts/test_audio_service_transcribe.py
- scripts/test_piper_wyoming.py
- scripts/http/* (HTTP examples for manual API calls)

How to restore
- To restore an archived file, use `git mv scripts/archived/<file> <desired/path>` and commit the change.

Recommendation
- Keep archives for now until CI/QA has validated the cleanup.
- After validation, consider removing the largest binary artifacts (e.g., `test_whisper.wav`, `piper_wyoming_out.raw`) or storing them in an external storage if needed.
