from __future__ import annotations

import json
import re
from typing import Dict, List, Tuple

from .logger import setup_logging

logger = setup_logging()

STOP_WORDS = {"年", "论文", "研究", "综述", "治疗", "机制", "分析", "方法"}


def _extract_year_range(text: str) -> Tuple[int | None, int | None]:
    match = re.search(r"(19\d{2}|20\d{2})\s*[-到~至]\s*(19\d{2}|20\d{2})", text)
    if match:
        start, end = int(match.group(1)), int(match.group(2))
        if start > end:
            start, end = end, start
        return start, end
    single = re.search(r"(19\d{2}|20\d{2})", text)
    if single:
        year = int(single.group(1))
        return year, year
    return None, None


def _extract_count(text: str) -> int | None:
    match = re.search(r"(\d{1,3})\s*(篇|条|个)?", text)
    if match:
        value = int(match.group(1))
        return max(1, min(value, 100))
    return None


def _extract_keywords(text: str) -> List[str]:
    cleaned = re.sub(r"(19\d{2}|20\d{2})\s*[-到~至]\s*(19\d{2}|20\d{2})", " ", text)
    cleaned = re.sub(r"(19\d{2}|20\d{2})", " ", cleaned)
    cleaned = re.sub(r"[，。,.;；/\\|]+", " ", cleaned)
    parts = [p.strip() for p in cleaned.split() if p.strip()]
    keywords = [p for p in parts if p not in STOP_WORDS]
    return keywords


def parse_user_query(text: str) -> Dict[str, object]:
    start_year, end_year = _extract_year_range(text)
    count = _extract_count(text)
    keywords = _extract_keywords(text)
    return {
        "start_year": start_year,
        "end_year": end_year,
        "count": count,
        "keywords": keywords,
    }


def _safe_json_loads(payload: str) -> Dict[str, object] | None:
    try:
        parsed = json.loads(payload)
        return parsed if isinstance(parsed, dict) else None
    except Exception:
        match = re.search(r"\{.*\}", payload, re.S)
        if not match:
            return None
        try:
            parsed = json.loads(match.group(0))
            return parsed if isinstance(parsed, dict) else None
        except Exception:
            return None


def _direct_llm_parse(text: str, config: Dict[str, object]) -> Dict[str, object] | None:
    api_key = (config.get("api_key") or "").strip() if config else ""
    if not api_key:
        return None
    try:
        from langchain_openai import ChatOpenAI
        from langchain.prompts import PromptTemplate
    except Exception as exc:
        logger.warning("direct llm init failed: %s", exc)
        return None

    prompt = PromptTemplate.from_template(
        """
你是 PubMed 检索助手。请将用户自然语言需求解析为结构化 JSON：
- start_year: 起始年份（没有则为 null）
- end_year: 结束年份（没有则为 null）
- count: 数量（没有则为 null）
- keywords: 关键词数组（英文为主，若无则空数组）
- query_string: 可直接用于 PubMed 的检索语句（字符串，若无则空字符串）

仅输出 JSON，不要任何解释。

用户输入：{input}
"""
    )

    llm = ChatOpenAI(
        model=config.get("ai_model", "gpt-3.5-turbo"),
        api_key=api_key,
        base_url=config.get("api_base", "https://api.openai.com/v1"),
        temperature=0,
    )

    try:
        response = llm.invoke(prompt.format(input=text))
        return _safe_json_loads(response.content)
    except Exception as exc:
        logger.warning("direct llm parse failed: %s", exc)
        return None


def parse_user_query_with_langchain(text: str, config: Dict[str, object]) -> Dict[str, object]:
    api_key = (config.get("api_key") or "").strip() if config else ""
    if not api_key:
        return parse_user_query(text)

    try:
        from langchain.agents import AgentExecutor, create_react_agent
        from langchain.prompts import PromptTemplate
        from langchain.tools import Tool
        from langchain_openai import ChatOpenAI
    except Exception as exc:
        logger.warning("langchain init failed: %s", exc)
        return parse_user_query(text)

    def _rule_parse(query: str) -> str:
        return json.dumps(parse_user_query(query), ensure_ascii=False)

    tools = [
        Tool.from_function(
            name="rule_parse",
            func=_rule_parse,
            description="使用规则解析用户检索需求，输出 JSON",
        )
    ]

    prompt = PromptTemplate.from_template(
        """
你是论文检索助手，请从用户输入中提取结构化字段：
- start_year: 起始年份（没有则为 null）
- end_year: 结束年份（没有则为 null）
- count: 数量（没有则为 null）
- keywords: 关键词列表（数组，可为空）

你可以使用工具来完成解析。
最终仅输出 JSON，不要额外文字。

可用工具：
{tools}

工具名称：{tool_names}

用户输入：{input}

{agent_scratchpad}
"""
    )

    llm = ChatOpenAI(
        model=config.get("ai_model", "gpt-3.5-turbo"),
        api_key=api_key,
        base_url=config.get("api_base", "https://api.openai.com/v1"),
        temperature=0,
    )

    try:
        agent = create_react_agent(llm, tools, prompt)
        executor = AgentExecutor(agent=agent, tools=tools, verbose=False, handle_parsing_errors=True)
        result = executor.invoke({"input": text})
        output = result.get("output", "")
        parsed = _safe_json_loads(output)
        if isinstance(parsed, dict):
            return parsed
    except Exception as exc:
        logger.warning("langchain parse failed, fallback to rule parse: %s", exc)

    direct = _direct_llm_parse(text, config)
    if isinstance(direct, dict):
        return direct

    return parse_user_query(text)
