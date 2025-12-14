# Anki Integration To-Do List

## Card & Deck Creation & Testing

- [ ] **Check all instantiation paths for card/deck creation**
  - [ ] Create cards from source (via source context menu or batch action)
  - [ ] Create cards from notebook (via notebook view)
  - [ ] Create cards from deck (add new cards to existing deck)
  - [ ] Verify card creation succeeds for all paths without errors
  - [ ] Test with various source types (PDF, markdown, web, etc.)

- [ ] **Verify card format correctness**
  - [ ] Cards display with correct fields (front, back, pronunciation, image, etc.)
  - [ ] Cloze format renders properly if used
  - [ ] Images/media references are correct
  - [ ] HTML/markup in card content is clean and renders well

- [ ] **Assess card quality**
  - [ ] Generated content is grammatically correct
  - [ ] Card content is semantically appropriate and relevant
  - [ ] Card difficulty level is suitable for target CEFR level
  - [ ] Generated cards are diverse (not repetitive)
  - [ ] Cards follow good spaced repetition principles

## Template Development

- [ ] **Implement anki_multicard template as Insights**
  - [ ] Create transformation template for multi-card generation
  - [ ] Store generated card sets as source_insight records
  - [ ] Allow users to review insights before adding to deck
  - [ ] Link insights to source for traceability

- [ ] **Provide card/deck creation templates**
  - [ ] Create template for generating basic flashcards from source content
  - [ ] Create template for deck organization (by topic, CEFR level, etc.)
  - [ ] Create template for batch card generation from multiple sources
  - [ ] Document template customization options
  - [ ] Allow users to create custom templates via UI

## Media Integration

- [ ] **Implement image search/creation for cards**
  - [ ] Research image search APIs (Unsplash, Pexels, or self-hosted alternatives)
  - [ ] Implement image search based on card content/keywords
  - [ ] Generate images if search not available (e.g., via DALL-E or Stable Diffusion)
  - [ ] Store images with cards in Anki deck
  - [ ] Verify images load correctly in Anki clients

- [ ] **Implement text-to-speech for pronunciation cards**
  - [ ] Research pronunciation guide formats (IPA, respelling, etc.)
  - [ ] Evaluate Piper models for target languages (quality, speed, CEFR support)
  - [ ] Integrate TTS generation with card creation pipeline
  - [ ] Generate audio files and embed in cards
  - [ ] Test audio playback in Anki desktop and mobile clients
  - [ ] Document supported languages and voice options

## Export & Download

- [ ] **Implement APKG export functionality**
  - [ ] Generate valid APKG (Anki deck package) files
  - [ ] Include card content, images, and audio media
  - [ ] Support batch export (multiple decks/selections)
  - [ ] Add download button to UI for deck export
  - [ ] Test APKG import in Anki desktop client
  - [ ] Verify compatibility with AnkiWeb sync

## Documentation

- [ ] **Update user documentation for Anki features**
  - [ ] Document how to create cards from sources/notebooks
  - [ ] Provide guide for CEFR level selection
  - [ ] Explain card template customization
  - [ ] Add troubleshooting section for Anki integration
  - [ ] Include examples of good vs. poor card generation

## Integration Testing

- [ ] **End-to-end testing workflow**
  - [ ] Upload source → Generate cards → Review → Export → Import to Anki
  - [ ] Test with different languages and CEFR levels
  - [ ] Verify database consistency (card tracking, audit logs)
  - [ ] Test concurrent card generation requests
  - [ ] Monitor resource usage during large batch operations


  ## Cleanup Suggestions (next actions)

  These are suggested steps to tidy the repo, remove or archive unused artifacts, and create a PR with the changes.

  - [ ] **Inventory scripts**: list files in `scripts/` and top-level helper scripts, mark ones no longer used (candidates: `tmp_parser.py`, `test_piper_wyoming.py`, `piper_http_proxy.py`).
  - [ ] **Smoke-run important scripts**: run any small test scripts to confirm they're still functional before removal.
  - [ ] **Archive rather than delete**: move confirmed-unused scripts into `scripts/archived/` and add a short note in `ARCHIVE.md` describing why.
  - [ ] **Inspect Docker volumes**: run `docker volume ls` and compare with `docker-compose.dev.yml` volumes (`whisper-models`, `piper-data`, `ollama_data`, `frontend_node_modules`) to identify orphaned volumes.
  - [ ] **Prune unused Docker volumes**: after confirmation, run `docker volume rm` for orphaned volumes or `docker system prune --volumes` if appropriate (backup first).
  - [ ] **Persist media files**: verify `notebook_data/uploads` contains generated audio/images; move or back up large media if needed.
  - [ ] **Update `docker-compose.dev.yml`**: remove unused volumes entries from `volumes:` block if they are truly not used by any service.
  - [ ] **Run tests & linters**: `pytest`, `ruff`, `mypy` to ensure cleanup didn't break imports or references.
  - [ ] **Commit & open PR**: create branch `anki/cleanup`, commit changes (including `ANKI_TODO.md` and any archival moves), push and open a pull request describing the cleanup.

  Notes:
  - Prefer archiving over deletion until CI/QA validates behavior.
  - When removing volumes, ensure backups exist for any important model caches (e.g., `whisper-models`).
  - If you want, I can perform the inventory and create the branch+commit now — tell me to proceed.
