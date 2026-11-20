# Changelog

## 0.2.0

### Added
- Word, CSV/TSV and JSON loaders; upload content checks; duplicate boilerplate removal.
- Private documents visible only to their owner and admins, enforced in listings, search and answers.
- Background indexing for large uploads with `/jobs/{id}` status.
- Follow-up questions, answer confidence, query-term highlights.
- Document editing, download, search by name, pagination; collection deletion; re-indexing.
- User management and password change.
- Prometheus metrics, readiness endpoint, JSON logging.
- Evaluation: 14 harder questions, `--failures`, `--sweep`, `--headers`, `--dense-weight`.
- UI: conversation thread, edit dialog, toasts, error boundary, dark mode, CSV export.

### Changed
- BM25 updates incrementally: indexing 300 documents went from 2.5 s to 0.15 s.
- Dense ranking weighted 0.5 in fusion when using the offline embedder.
- Stemmer handles `-ings`; sentence splitter handles lowercase starts and abbreviations.
- Extractive answers match on content words and drop weak filler sentences.

### Fixed
- Data folder resolved relative to the backend, not the working directory.
- JWT secrets shorter than 32 bytes rejected; a strong one is generated when unset.
- SQLite connections closed in the CLI and tests.
- Dark-mode contrast for inputs, buttons and citation chips.

## 0.1.0

First release: ingestion, hybrid retrieval, cited answers with streaming, JWT auth,
evaluation harness, React UI, Docker and CI.
