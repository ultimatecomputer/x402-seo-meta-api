

@app.get("/")
def root():
    return {"ok": True, "service": "seo-meta"}
