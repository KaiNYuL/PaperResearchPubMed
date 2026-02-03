from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class CrawlRequest(BaseModel):
    query: str = Field(..., description="用户检索需求")
    count: Optional[int] = Field(None, description="期望数量")


class PaperItem(BaseModel):
    title: str
    keywords: List[str]
    abstract: str
    match_dimension: str
    published_date: str
    doi: Optional[str] = None
    authors: Optional[List[str]] = None


class CrawlResponse(BaseModel):
    query: str
    extracted: Dict[str, Any]
    papers: List[PaperItem]


class ExportRequest(BaseModel):
    papers: List[Dict[str, Any]]
    format: str = Field("markdown", description="markdown/txt/word")
    output_dir: Optional[str] = None
    filename: Optional[str] = None


class ConfigRequest(BaseModel):
    ai_model: Optional[str] = None
    api_base: Optional[str] = None
    api_key: Optional[str] = None
    auto_translate: Optional[bool] = None
    theme_color: Optional[str] = None
    font_size: Optional[str] = None
    output_bg: Optional[str] = None
