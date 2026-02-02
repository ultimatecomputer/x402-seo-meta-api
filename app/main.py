from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel, HttpUrl
import requests
from bs4 import BeautifulSoup
from collections import Counter
import re

app = FastAPI(title="SEO Meta Extractor", version="0.1.0")

API_KEY_ENV = "x-api-key"

class MetaRequest(BaseModel):
    url: HttpUrl
    max_keywords: int = 10

class MetaResponse(BaseModel):
    url: str
    title: str | None
    meta_description: str | None
    h1: str | None
    word_count: int
    top_keywords: list[dict]


def _require_api_key(x_api_key: str | None):
    # x402 proxy will pass x-api-key to origin
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing x-api-key")


def _extract_keywords(text: str, max_keywords: int):
    text = re.sub(r"[^a-zA-Z0-9\s]", " ", text).lower()
    words = [w for w in text.split() if len(w) > 3]
    counts = Counter(words)
    return [
        {"keyword": k, "count": v}
        for k, v in counts.most_common(max_keywords)
    ]


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/meta", response_model=MetaResponse)
def extract_meta(payload: MetaRequest, x_api_key: str | None = Header(default=None, alias="x-api-key")):
    _require_api_key(x_api_key)
    try:
        r = requests.get(str(payload.url), timeout=10, headers={"User-Agent": "Mozilla/5.0"})
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Fetch failed: {e}")

    if r.status_code >= 400:
        raise HTTPException(status_code=502, detail=f"Fetch failed: HTTP {r.status_code}")

    soup = BeautifulSoup(r.text, "html.parser")
    title = soup.title.string.strip() if soup.title and soup.title.string else None
    meta_desc_tag = soup.find("meta", attrs={"name": "description"})
    meta_description = meta_desc_tag["content"].strip() if meta_desc_tag and meta_desc_tag.get("content") else None
    h1_tag = soup.find("h1")
    h1 = h1_tag.get_text(strip=True) if h1_tag else None

    text = soup.get_text(separator=" ")
    words = re.sub(r"\s+", " ", text).strip()
    word_count = len(words.split()) if words else 0

    top_keywords = _extract_keywords(text, payload.max_keywords)

    return MetaResponse(
        url=str(payload.url),
        title=title,
        meta_description=meta_description,
        h1=h1,
        word_count=word_count,
        top_keywords=top_keywords,
    )


@app.get("/")
def root():
    return {"ok": True, "service": "seo-meta"}


class CompetitorRequest(BaseModel):
    url: HttpUrl
    max_keywords: int = 12


class CompetitorResponse(BaseModel):
    url: str
    title: str | None
    meta_description: str | None
    h1: str | None
    top_keywords: list[dict]
    positioning_hint: str | None


def _positioning_hint(title: str | None, h1: str | None, keywords: list[dict]):
    if not keywords:
        return None
    top = ", ".join([k["keyword"] for k in keywords[:3]])
    headline = h1 or title
    if headline:
        return f"Headline suggests focus on '{headline}'. Top themes: {top}."
    return f"Top themes: {top}."


@app.post("/competitor", response_model=CompetitorResponse)
def competitor_snapshot(payload: CompetitorRequest, x_api_key: str | None = Header(default=None, alias="x-api-key")):
    _require_api_key(x_api_key)
    try:
        r = requests.get(str(payload.url), timeout=10, headers={"User-Agent": "Mozilla/5.0"})
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Fetch failed: {e}")

    if r.status_code >= 400:
        raise HTTPException(status_code=502, detail=f"Fetch failed: HTTP {r.status_code}")

    soup = BeautifulSoup(r.text, "html.parser")
    title = soup.title.string.strip() if soup.title and soup.title.string else None
    meta_desc_tag = soup.find("meta", attrs={"name": "description"})
    meta_description = meta_desc_tag["content"].strip() if meta_desc_tag and meta_desc_tag.get("content") else None
    h1_tag = soup.find("h1")
    h1 = h1_tag.get_text(strip=True) if h1_tag else None

    text = soup.get_text(separator=" ")
    top_keywords = _extract_keywords(text, payload.max_keywords)

    return CompetitorResponse(
        url=str(payload.url),
        title=title,
        meta_description=meta_description,
        h1=h1,
        top_keywords=top_keywords,
        positioning_hint=_positioning_hint(title, h1, top_keywords),
    )
