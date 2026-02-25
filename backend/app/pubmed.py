from __future__ import annotations

import os
import time
from typing import Dict, List, Optional
from xml.etree import ElementTree

import requests
from bs4 import BeautifulSoup

try:
    from pymed import PubMed
except Exception:  # pragma: no cover - optional
    PubMed = None


def _clean_text(text: Optional[str]) -> str:
    if not text:
        return ""
    return " ".join(text.split())


def _search_with_pymed(query: str, max_results: int) -> List[Dict[str, object]]:
    if PubMed is None:
        return []
    pubmed = PubMed(tool="paper-agent", email="example@example.com")
    results = pubmed.query(query, max_results=max_results)
    papers = []
    for article in results:
        medline = article.toDict()
        papers.append(
            {
                "title": _clean_text(medline.get("title")),
                "keywords": [kw for kw in medline.get("keywords", []) if kw],
                "abstract": _clean_text(medline.get("abstract")),
                "published_date": str(medline.get("pubdate", "")),
                "doi": medline.get("doi"),
                "authors": [a.get("lastname", "") for a in medline.get("authors", []) if a],
            }
        )
    return papers


def _build_esearch_params(query: str, start_year: Optional[int], end_year: Optional[int], retmax: int) -> Dict[str, str]:
    params = {
        "db": "pubmed",
        "term": query,
        "retmode": "xml",
        "retmax": str(retmax),
        "sort": "relevance",
    }
    if start_year and end_year:
        params.update(
            {
                "mindate": str(start_year),
                "maxdate": str(end_year),
                "datetype": "pdat",
            }
        )
    return params


def _request_with_retry(url: str, params: Dict[str, str], timeout: int) -> requests.Response:
    retries = int(os.getenv("PUBMED_RETRIES", "3"))
    backoff = float(os.getenv("PUBMED_RETRY_BACKOFF", "1.5"))
    for attempt in range(retries):
        try:
            resp = requests.get(url, params=params, timeout=timeout)
            resp.raise_for_status()
            return resp
        except Exception:
            if attempt >= retries - 1:
                raise
            time.sleep(backoff * (attempt + 1))


def _search_with_eutils(query: str, start_year: Optional[int], end_year: Optional[int], max_results: int) -> List[Dict[str, object]]:
    base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    esearch = f"{base}/esearch.fcgi"
    efetch = f"{base}/efetch.fcgi"

    params = _build_esearch_params(query, start_year, end_year, max_results)
    resp = _request_with_retry(esearch, params=params, timeout=20)

    root = ElementTree.fromstring(resp.text)
    id_list = [elem.text for elem in root.findall(".//IdList/Id") if elem.text]
    if not id_list:
        return []

    fetch_params = {
        "db": "pubmed",
        "id": ",".join(id_list),
        "retmode": "xml",
    }
    fetch_resp = _request_with_retry(efetch, params=fetch_params, timeout=30)
    fetch_root = ElementTree.fromstring(fetch_resp.text)

    papers: List[Dict[str, object]] = []
    for article in fetch_root.findall(".//PubmedArticle"):
        title = _clean_text("".join(article.findalltext(".//ArticleTitle")))
        abstract = _clean_text(" ".join(article.findalltext(".//Abstract/AbstractText")))
        keywords = [kw.text for kw in article.findall(".//KeywordList/Keyword") if kw.text]

        pub_date = ""
        year = article.findtext(".//PubDate/Year")
        medline_date = article.findtext(".//PubDate/MedlineDate")
        if year:
            pub_date = year
        elif medline_date:
            pub_date = medline_date

        doi = None
        for id_elem in article.findall(".//ArticleId"):
            if id_elem.get("IdType") == "doi":
                doi = id_elem.text
                break

        authors = []
        for author in article.findall(".//Author"):
            last = author.findtext("LastName")
            first = author.findtext("ForeName")
            name = " ".join([p for p in [first, last] if p])
            if name:
                authors.append(name)

        papers.append(
            {
                "title": title,
                "keywords": keywords,
                "abstract": abstract,
                "published_date": pub_date,
                "doi": doi,
                "authors": authors,
            }
        )
    return papers


def _parse_pubmed_article_page(url: str) -> Dict[str, object]:
    resp = _request_with_retry(url, params={}, timeout=20)
    soup = BeautifulSoup(resp.text, "html.parser")

    title = _clean_text(soup.select_one("h1.heading-title").get_text(" ", strip=True) if soup.select_one("h1.heading-title") else "")
    abstract_block = soup.select_one("div.abstract-content")
    abstract = ""
    if abstract_block:
        abstract = _clean_text(abstract_block.get_text(" ", strip=True))

    keywords = [kw.get_text(strip=True) for kw in soup.select("span.keyword") if kw.get_text(strip=True)]

    pub_date = ""
    citation = soup.select_one("span.cit")
    if citation:
        pub_date = _clean_text(citation.get_text(" ", strip=True))

    doi = None
    doi_node = soup.select_one("span.identifier.doi")
    if doi_node:
        doi = _clean_text(doi_node.get_text(" ", strip=True)).replace("doi:", "").strip()

    authors = [a.get_text(strip=True) for a in soup.select("div.authors-list span.authors-list-item") if a.get_text(strip=True)]

    return {
        "title": title,
        "keywords": keywords,
        "abstract": abstract,
        "published_date": pub_date,
        "doi": doi,
        "authors": authors,
    }


def _search_with_html(query: str, max_results: int) -> List[Dict[str, object]]:
    base = "https://pubmed.ncbi.nlm.nih.gov"
    resp = _request_with_retry(base + "/", params={"term": query}, timeout=20)
    soup = BeautifulSoup(resp.text, "html.parser")
    links = []
    for link in soup.select("a.docsum-title"):  # search results
        href = link.get("href")
        if not href:
            continue
        if href.startswith("/"):
            links.append(base + href)
        elif href.startswith("http"):
            links.append(href)
        if len(links) >= max_results:
            break

    papers: List[Dict[str, object]] = []
    for url in links:
        try:
            papers.append(_parse_pubmed_article_page(url))
        except Exception:
            continue
    return papers


def search_papers(query: str, start_year: Optional[int], end_year: Optional[int], max_results: int) -> List[Dict[str, object]]:
    try:
        if PubMed is not None:
            results = _search_with_pymed(query, max_results)
            if results:
                return results
    except Exception:
        time.sleep(0.2)
    try:
        return _search_with_eutils(query, start_year, end_year, max_results)
    except Exception:
        time.sleep(0.2)
    return _search_with_html(query, max_results)
