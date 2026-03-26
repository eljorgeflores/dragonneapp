"""Carga del schema, validación jsonschema y versión strict para OpenAI."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from config import BASE_DIR

try:
    import jsonschema
except ImportError:  # pragma: no cover
    jsonschema = None

SCHEMA_PATH = BASE_DIR / "schemas" / "revenue_report.schema.json"


def load_schema() -> Dict[str, Any]:
    with open(SCHEMA_PATH, encoding="utf-8") as f:
        return json.load(f)


def _strip_meta(node: Any) -> Any:
    if isinstance(node, dict):
        return {k: _strip_meta(v) for k, v in node.items() if not k.startswith("$")}
    if isinstance(node, list):
        return [_strip_meta(x) for x in node]
    return node


def prepare_schema_for_openai_strict(schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    OpenAI Responses API json_schema strict: additionalProperties false y
    required = todas las keys de properties en cada object.
    """
    schema = _strip_meta(schema)

    def walk(obj: Any) -> Any:
        if isinstance(obj, dict):
            t = obj.get("type")
            if t == "object" and "properties" in obj:
                props = {k: walk(v) for k, v in obj["properties"].items()}
                keys = list(props.keys())
                return {
                    **{k: v for k, v in obj.items() if k not in ("properties", "required", "additionalProperties")},
                    "type": "object",
                    "properties": props,
                    "required": keys,
                    "additionalProperties": False,
                }
            if t == "array" and "items" in obj:
                return {
                    **{k: walk(v) for k, v in obj.items() if k != "items"},
                    "type": "array",
                    "items": walk(obj["items"]),
                }
            return {k: walk(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [walk(x) for x in obj]
        return obj

    out = walk(schema)
    if isinstance(out, dict) and out.get("type") == "object" and "properties" in out:
        keys = list(out["properties"].keys())
        out["required"] = keys
        out["additionalProperties"] = False
    return out


def validate_revenue_report(data: Dict[str, Any]) -> None:
    if jsonschema is None:
        raise RuntimeError("jsonschema no está instalado. Añádelo a requirements.txt")
    jsonschema.validate(instance=data, schema=load_schema())


def validation_errors(data: Dict[str, Any]) -> str:
    if jsonschema is None:
        return "jsonschema no instalado"
    try:
        validate_revenue_report(data)
        return ""
    except jsonschema.ValidationError as e:
        return str(e.message)
