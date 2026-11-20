# Security

## Reporting

Please report vulnerabilities privately through GitHub's "Report a vulnerability" button on
this repository rather than in a public issue.

## Design notes

- Passwords are hashed with scrypt (N=2^14, r=8, p=1) and a random 16-byte salt.
- Access tokens are HS256 JWTs; secrets shorter than 32 bytes are rejected.
- Upload names are reduced to a safe base name; originals are stored under their
  content-hash id, never under the user-supplied name.
- Uploads are capped by `RAGFORGE_MAX_UPLOAD_MB` and parsed with standard-library or
  pure-Python parsers only.
- `/ask` is rate-limited per user.
- Document content is passed to the LLM as data inside numbered context blocks. Prompt
  injection inside uploaded documents is still possible with any RAG system; only index
  documents from sources you trust, and keep the answering model free of tools.
