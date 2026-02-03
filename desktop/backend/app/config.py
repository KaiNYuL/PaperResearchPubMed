from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Any, Dict

import yaml

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.getenv("PAPER_AGENT_DATA_DIR") or (BASE_DIR / "data"))
CONFIG_PATH = DATA_DIR / "config.yaml"

DEFAULT_CONFIG: Dict[str, Any] = {
    "ai_model": "gpt-3.5-turbo",
    "api_base": "https://api.openai.com/v1",
    "api_key": "",
    "auto_translate": True,
    "theme_color": "默认蓝",
    "font_size": "中",
    "output_bg": "白色",
}


def _merge_config(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if value is not None:
            merged[key] = value
    return merged


def load_config() -> Dict[str, Any]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_PATH.exists():
        save_config(DEFAULT_CONFIG)
        return dict(DEFAULT_CONFIG)
    try:
        data = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}
        if not isinstance(data, dict):
            return dict(DEFAULT_CONFIG)
        return _merge_config(DEFAULT_CONFIG, data)
    except Exception:
        return dict(DEFAULT_CONFIG)


def save_config(payload: Dict[str, Any]) -> Dict[str, Any]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    merged = _merge_config(DEFAULT_CONFIG, payload)
    CONFIG_PATH.write_text(yaml.safe_dump(merged, allow_unicode=True), encoding="utf-8")
    return merged
