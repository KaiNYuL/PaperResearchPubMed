from __future__ import annotations

from flask import Flask, jsonify, request

from .api_handlers import (
    handle_check_env,
    handle_crawl_paper,
    handle_export_doc,
    handle_get_config,
    handle_save_config,
)

app = Flask(__name__)


@app.get("/api/get_config")
def get_config():
    return jsonify(handle_get_config())


@app.post("/api/save_config")
def save_config():
    payload = request.get_json(silent=True) or {}
    return jsonify(handle_save_config(payload))


@app.post("/api/crawl_paper")
def crawl_paper():
    payload = request.get_json(silent=True) or {}
    return jsonify(handle_crawl_paper(payload))


@app.post("/api/export_doc")
def export_doc():
    payload = request.get_json(silent=True) or {}
    return jsonify(handle_export_doc(payload))


@app.get("/api/check_env")
def check_env():
    return jsonify(handle_check_env())
