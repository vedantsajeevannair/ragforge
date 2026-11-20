# Troubleshooting

**"index at data/index has shape (n, 512), expected (n, 768)"**
The embedding dimension changed since the index was built. Either set
`RAGFORGE_EMBEDDING_DIM` back, or delete `data/index/` and run `POST /documents/reindex`
(originals in `data/files/` are re-embedded).

**Everyone was signed out after a restart.**
The JWT secret changed. Leave `RAGFORGE_JWT_SECRET` empty to use the persisted secret in
`data/.jwt_secret`, or set the same value on every start.

**Answers stream all at once instead of token by token.**
A proxy is buffering the response. With nginx set `proxy_buffering off;` for `/api/`
(the bundled `frontend/nginx.conf` already does).

**Upload returns 415 "file content is not a valid .pdf file".**
The file was renamed from another format. Export it as a real PDF, or upload it with its
actual extension.

**Upload returns 413 "document produced N chunks".**
Raise `RAGFORGE_MAX_CHUNKS_PER_DOCUMENT` or `RAGFORGE_CHUNK_SIZE`, or split the file.

**Search finds the right document but the answer says it could not find anything.**
`RAGFORGE_MIN_SCORE` may be too high for your embedder; scores from hybrid search are RRF
values around 0.01-0.05 before re-ranking. Start from 0 and raise it while watching
`make bench`.

**Uploads made by one worker are missing from another.**
Run a single API worker; the index lives in process memory (see docs/deployment.md).
