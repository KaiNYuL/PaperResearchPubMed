from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api_handlers import (
    handle_check_env,
    handle_crawl_paper,
    handle_export_doc,
    handle_get_config,
    handle_save_config,
)
from .models import ConfigRequest, CrawlRequest, ExportRequest

app = FastAPI(title="Paper Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/get_config")
async def get_config():
    return handle_get_config()


@app.post("/api/save_config")
async def save_config(req: ConfigRequest):
    return handle_save_config(req.dict(exclude_none=True))


@app.post("/api/crawl_paper")
async def crawl_paper(req: CrawlRequest):
    return handle_crawl_paper(req.dict(exclude_none=True))


@app.post("/api/export_doc")
async def export_doc(req: ExportRequest):
    return handle_export_doc(req.dict(exclude_none=True))


@app.get("/api/check_env")
async def check_env():
    return handle_check_env()
