# SEO Meta Extractor API (x402 Origin)

Minimal FastAPI service for extracting SEO metadata from a URL.

## Local Run
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## API
- `GET /health`
- `POST /meta` body: `{ "url": "https://example.com", "max_keywords": 10 }`

## Security
x402 proxy forwards `x-api-key`. Origin must require it.

## Render Deploy (Free)
1) Push this repo to GitHub.
2) Create new **Web Service** on Render.
3) Build command: `pip install -r requirements.txt`
4) Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5) Choose free instance.

The public URL from Render becomes the origin for x402.
