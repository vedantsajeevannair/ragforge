# Deployment

## Docker Compose

```bash
cp .env.example .env      # set the LLM provider and keys here
docker compose up -d --build
```

The UI is served on port 8080; nginx proxies `/api/` to the FastAPI container and disables
buffering so streamed answers arrive token by token. Data lives in the `ragforge-data` volume.

Back up the volume, or at least `ragforge.db`, `index/` and `files/`, together: they must stay
in sync.

## Without Docker

```bash
cd backend
pip install -r requirements.txt
RAGFORGE_DATA_DIR=/var/lib/ragforge uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1

cd ../frontend
npm ci && VITE_API_URL=https://your-host/api npm run build   # serve dist/ with any web server
```

Run a **single worker**: the vector store and BM25 index live in process memory, so several
workers would each hold their own copy and miss each other's uploads.

## Checklist

- Put the API behind HTTPS (nginx, Caddy or a cloud load balancer).
- Set `RAGFORGE_CORS_ORIGINS` to your UI origin, e.g. `["https://docs.example.com"]`.
- Leave `RAGFORGE_JWT_SECRET` empty to auto-generate one, or set 32+ random bytes.
- Set `RAGFORGE_JSON_LOGS=true` and ship stderr to your log store.
- Scrape `/metrics` with Prometheus for request counts and latency histograms.
- Register the first account yourself straight after deploying: it becomes the admin.
