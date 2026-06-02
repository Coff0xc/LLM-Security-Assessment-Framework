# -*- coding: utf-8 -*-
"""
数据集 API Blueprint

提供数据集列表、上传和预览端点。
"""

import json
from pathlib import Path
from flask import Blueprint, request, jsonify, current_app
from .auth import require_api_key

datasets_bp = Blueprint("datasets", __name__, url_prefix="/api/datasets")


def _get_datasets_dir() -> Path:
    """获取数据集目录"""
    return Path(current_app.config["PROJECT_ROOT"]) / "datasets"


@datasets_bp.route("", methods=["GET"])
def list_datasets():
    """数据集列表"""
    datasets = [
        {
            "name": "advbench",
            "description": "AdvBench standard test set",
            "samples": 520,
            "type": "builtin",
        },
    ]

    custom_path = _get_datasets_dir()
    if custom_path.exists():
        for f in custom_path.glob("*.json"):
            try:
                with open(f, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                    datasets.append(
                        {
                            "name": f"custom:{f.name}",
                            "description": f"Custom: {f.stem}",
                            "samples": len(data) if isinstance(data, list) else 0,
                            "type": "custom",
                        }
                    )
            except Exception:
                pass

    return jsonify(datasets)


@datasets_bp.route("/upload", methods=["POST"])
@require_api_key
def upload_dataset():
    """上传自定义数据集"""
    if "file" not in request.files:
        # 尝试 JSON body 方式
        data = request.get_json()
        if not data:
            return (
                jsonify({"error": "No file or JSON data provided", "code": "NO_DATA"}),
                400,
            )

        name = data.get("name", "")
        samples = data.get("samples", [])

        if not name or not samples:
            return (
                jsonify({"error": "Missing name or samples", "code": "MISSING_FIELDS"}),
                400,
            )

        datasets_dir = _get_datasets_dir()
        datasets_dir.mkdir(parents=True, exist_ok=True)

        filepath = datasets_dir / f"{name}.json"
        with open(filepath, "w", encoding="utf-8") as fh:
            json.dump(samples, fh, ensure_ascii=False, indent=2)

        return (
            jsonify(
                {
                    "message": "Dataset uploaded",
                    "name": f"custom:{name}.json",
                    "samples": len(samples),
                }
            ),
            201,
        )

    file = request.files["file"]
    if not file.filename or not file.filename.endswith(".json"):
        return (
            jsonify({"error": "Only JSON files supported", "code": "INVALID_FORMAT"}),
            400,
        )

    datasets_dir = _get_datasets_dir()
    datasets_dir.mkdir(parents=True, exist_ok=True)

    filepath = datasets_dir / file.filename
    file.save(str(filepath))

    try:
        with open(filepath, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        count = len(data) if isinstance(data, list) else 0
    except Exception:
        count = 0

    return (
        jsonify(
            {
                "message": "Dataset uploaded",
                "name": f"custom:{file.filename}",
                "samples": count,
            }
        ),
        201,
    )


@datasets_bp.route("/<name>/preview", methods=["GET"])
def preview_dataset(name):
    """预览数据集"""
    limit = request.args.get("limit", 10, type=int)

    if name == "advbench":
        try:
            from forgedan.datasets import DatasetLoader

            ds = DatasetLoader.load("advbench")
            samples = ds.sample(min(limit, 20), seed=42)
            return jsonify(
                {
                    "name": "advbench",
                    "total": 520,
                    "preview": [
                        {"goal": s.goal, "category": s.category.value} for s in samples
                    ],
                }
            )
        except Exception as e:
            return jsonify({"error": str(e), "code": "LOAD_FAILED"}), 500

    # 自定义数据集
    clean_name = name.replace("custom:", "")
    filepath = _get_datasets_dir() / clean_name
    if not filepath.exists():
        # 尝试加上 .json
        filepath = _get_datasets_dir() / f"{clean_name}.json"

    if not filepath.exists():
        return jsonify({"error": "Dataset not found", "code": "NOT_FOUND"}), 404

    try:
        with open(filepath, "r", encoding="utf-8") as fh:
            data = json.load(fh)

        items = data if isinstance(data, list) else []
        return jsonify(
            {
                "name": name,
                "total": len(items),
                "preview": items[:limit],
            }
        )
    except Exception as e:
        return jsonify({"error": str(e), "code": "LOAD_FAILED"}), 500
