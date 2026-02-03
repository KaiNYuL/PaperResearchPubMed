from __future__ import annotations

from datetime import datetime
import json
import re
from difflib import SequenceMatcher
from typing import Any, Dict, List, Tuple

from .agent import parse_user_query_with_langchain
from .logger import setup_logging
from .pubmed import search_papers

logger = setup_logging()


def _contains_chinese(text: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", text))


def _translate_keywords(keywords: List[str], config: Dict[str, Any]) -> List[str]:
    if not keywords:
        return keywords
    if config and config.get("auto_translate") is False:
        return keywords
    if not any(_contains_chinese(kw) for kw in keywords):
        return keywords
    api_key = (config.get("api_key") or "").strip() if config else ""
    if not api_key:
        return keywords

    try:
        from langchain_openai import ChatOpenAI
        from langchain.prompts import PromptTemplate
    except Exception as exc:
        logger.warning("translate init failed: %s", exc)
        return keywords

    prompt = PromptTemplate.from_template(
        """
你是医学检索助手。请将以下中文关键词翻译成英文检索关键词。
要求：
1) 仅输出 JSON 数组，不要任何解释。
2) 尽量使用 PubMed 常见学术英文词汇。

关键词：{keywords}
"""
    )

    llm = ChatOpenAI(
        model=config.get("ai_model", "gpt-3.5-turbo"),
        api_key=api_key,
        base_url=config.get("api_base", "https://api.openai.com/v1"),
        temperature=0,
    )

    try:
        response = llm.invoke(prompt.format(keywords=", ".join(keywords)))
        translated = json.loads(response.content)
        if isinstance(translated, list) and all(isinstance(x, str) for x in translated):
            return [x.strip() for x in translated if x.strip()]
    except Exception as exc:
        logger.warning("translate failed, fallback to original: %s", exc)
    return keywords


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip().lower()


def _tokenize(text: str) -> List[str]:
    if not text:
        return []
    if re.search(r"[\u4e00-\u9fff]", text):
        return [ch for ch in text if re.match(r"[\u4e00-\u9fff]", ch)]
    return re.findall(r"[a-z0-9]+", text.lower())


def _similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def _jaccard(a_tokens: List[str], b_tokens: List[str]) -> float:
    if not a_tokens or not b_tokens:
        return 0.0
    a_set, b_set = set(a_tokens), set(b_tokens)
    inter = a_set.intersection(b_set)
    union = a_set.union(b_set)
    return len(inter) / max(len(union), 1)


def _match_dimension(paper: Dict[str, Any], keywords: List[str]) -> Tuple[str, int]:
    title = _normalize_text(paper.get("title", ""))
    abstract = _normalize_text(paper.get("abstract", ""))
    kw_list = [_normalize_text(kw) for kw in paper.get("keywords", [])]
    kw_text = " ".join(kw_list)

    for kw in keywords:
        low = _normalize_text(kw)
        if not low:
            continue
        if any(low in k for k in kw_list):
            return "关键字", 0
        if _similarity(low, kw_text) >= 0.6:
            return "关键字", 0

    for kw in keywords:
        low = _normalize_text(kw)
        if not low:
            continue
        if low in title:
            return "标题", 1
        if _similarity(low, title) >= 0.55:
            return "标题", 1

    for kw in keywords:
        low = _normalize_text(kw)
        if not low:
            continue
        if low in abstract:
            return "摘要", 2
        if _similarity(low, abstract) >= 0.5:
            return "摘要", 2

    # token-level relatedness
    title_tokens = _tokenize(title)
    abstract_tokens = _tokenize(abstract)
    keyword_tokens = _tokenize(" ".join(keywords))
    if _jaccard(keyword_tokens, title_tokens) >= 0.2:
        return "标题", 1
    if _jaccard(keyword_tokens, abstract_tokens) >= 0.15:
        return "摘要", 2

    return "摘要", 3


def _clean_papers(papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    cleaned = []
    seen = set()
    for paper in papers:
        title = (paper.get("title") or "").strip()
        abstract = (paper.get("abstract") or "").strip()
        keywords = paper.get("keywords") or []
        if not title or not abstract:
            continue
        key = title.lower()
        if key in seen:
            continue
        seen.add(key)
        paper["keywords"] = keywords
        cleaned.append(paper)
    return cleaned


def crawl_papers(user_query: str, count: int | None, config: Dict[str, Any] | None = None) -> Dict[str, Any]:
    parsed = parse_user_query_with_langchain(user_query, config or {})
    keywords = parsed.get("keywords", [])
    if not keywords:
        return {
            "error": "未识别到有效关键词，建议补充核心主题词",
            "suggestion": f"{datetime.now().year-2}-{datetime.now().year} 年 主题词1 主题词2",
        }
    translated_keywords = _translate_keywords(keywords, config or {})
    parsed["translated_keywords"] = translated_keywords
    max_results = count or parsed.get("count") or 10
    start_year = parsed.get("start_year")
    end_year = parsed.get("end_year")

    query_string = (parsed.get("query_string") or "").strip()
    if query_string:
        query = query_string
    elif translated_keywords:
        if len(translated_keywords) == 1:
            query = translated_keywords[0]
        else:
            query = " OR ".join(translated_keywords)
            query = f"({query})"
    else:
        query = user_query
    logger.info("crawl start | query=%s | years=%s-%s | count=%s", query, start_year, end_year, max_results)
    papers = search_papers(query, start_year, end_year, max_results)
    if not papers:
        logger.info("crawl retry | relax year filter and increase retmax")
        papers = search_papers(query, None, None, max(50, max_results * 5))
    if not papers and query != user_query:
        logger.info("crawl retry | use raw query")
        papers = search_papers(user_query, None, None, max(50, max_results * 5))
    papers = _clean_papers(papers)

    enriched = []
    for paper in papers:
        dimension, rank = _match_dimension(paper, keywords)
        if rank > 2:
            continue
        enriched.append(
            {
                "title": paper.get("title", ""),
                "keywords": paper.get("keywords", []),
                "abstract": paper.get("abstract", ""),
                "match_dimension": dimension,
                "published_date": paper.get("published_date", ""),
                "doi": paper.get("doi"),
                "authors": paper.get("authors", []),
                "_rank": rank,
            }
        )

    enriched.sort(key=lambda x: (x.get("_rank", 99), x.get("published_date", "")), reverse=False)
    for item in enriched:
        item.pop("_rank", None)

    logger.info("crawl done | result=%s", len(enriched))
    return {
        "query": user_query,
        "extracted": parsed,
        "papers": enriched[:max_results],
    }
