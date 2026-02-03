from __future__ import annotations

from typing import Any, Dict

from .config import load_config, save_config
from .exporter import export_docs
from .logger import setup_logging
from .services import crawl_papers

logger = setup_logging()


def response_ok(data: Any = None, message: str = "success") -> Dict[str, Any]:
    return {"code": 0, "message": message, "data": data}


def response_error(message: str, data: Any = None) -> Dict[str, Any]:
    return {"code": 1, "message": message, "data": data}


def handle_get_config() -> Dict[str, Any]:
    return response_ok(load_config())


def handle_save_config(payload: Dict[str, Any]) -> Dict[str, Any]:
    saved = save_config(payload)
    return response_ok(saved, "配置已保存")


def handle_crawl_paper(payload: Dict[str, Any]) -> Dict[str, Any]:
    query = (payload.get("query") or "").strip()
    if not query:
        return response_error("请输入检索需求，例如‘2024-2026 年 糖尿病 机器学习 治疗’")
    count = payload.get("count")
    config = load_config()
    result = crawl_papers(query, count, config)
    if "error" in result:
        return response_error(result["error"], {"suggestion": result.get("suggestion")})
    return response_ok(result)


def handle_export_doc(payload: Dict[str, Any]) -> Dict[str, Any]:
    papers = payload.get("papers") or []
    fmt = payload.get("format") or "markdown"
    output_dir = payload.get("output_dir")
    filename = payload.get("filename")
    if not papers:
        return response_error("没有可导出的论文数据")
    try:
        path = export_docs(papers, fmt, output_dir, filename)
        return response_ok({"file_path": path}, "导出成功")
    except Exception as exc:
        logger.exception("export failed")
        return response_error(f"导出失败：{exc}")


def handle_check_env() -> Dict[str, Any]:
    required = [
        "fastapi",
        "flask",
        "requests",
        "yaml",
        "docx",
        "pymed",
        "langchain",
        "langchain_openai",
        "bs4",
        "markdown",
    ]
    missing = []
    for pkg in required:
        try:
            __import__(pkg)
        except Exception:
            missing.append(pkg)
    if missing:
        return response_ok({"missing": missing}, "检测到缺失依赖")
    return response_ok({"missing": []}, "环境完整")
