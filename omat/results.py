"""Shared result handling for both Wahl-O-Mat and Real-O-Mat.

Both evaluators write result files in the same shape::

    {"eval": "<model>", "results": [{Kurz, Name, Punkte, Übereinstimmung}, ...]}

Because that shape is identical, the aggregation + visualization pipeline
only lives once (here) and is reused by :mod:`visualize`.
"""

from __future__ import annotations

import glob
import json
import os
from typing import Any

from .palette import assign_model_colors

ResultRow = dict[str, Any]
ModelResult = dict[str, Any]


def load_results(results_dir: str, election: str) -> list[ModelResult]:
    """Load every result file matching ``*--{election}.json`` from a directory."""
    pattern = os.path.join(results_dir, f"*--{election}.json")
    paths = sorted(glob.glob(pattern))
    if not paths:
        raise FileNotFoundError(
            f"Keine Ergebnisdateien gefunden für '{election}' in {results_dir}/ "
            f"(Muster: *--{election}.json)"
        )
    models: list[ModelResult] = []
    for path in paths:
        with open(path, "r", encoding="utf-8") as f:
            models.append(json.load(f))
    return models


def write_result(model: str, results: list[ResultRow], path: str) -> None:
    """Write a single model's scored result file in the shared format."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"eval": model, "results": results}, f, ensure_ascii=False, indent=2)


def aggregate(
    models: list[ModelResult],
    party_colors: dict[str, str],
    *,
    election: str,
    fallback_color: str = "#7d8597",
) -> dict[str, Any]:
    """Build the data payload consumed by the HTML visualization.

    The structure is identical for both tools so the same JS renderer can
    draw either of them.
    """
    model_labels = [m["eval"] for m in models]
    model_colors = assign_model_colors(model_labels)

    party_order: list[str] = []
    party_names: dict[str, str] = {}
    scores: dict[str, dict[str, dict]] = {}  # kurz -> model -> {pct, punkte}

    for model in models:
        label = model["eval"]
        for row in model["results"]:
            kurz = row["Kurz"]
            if kurz not in party_names:
                party_order.append(kurz)
                party_names[kurz] = row["Name"]
                scores[kurz] = {}
            scores[kurz][label] = {
                "pct": float(row["Übereinstimmung"]),
                "punkte": row["Punkte"],
            }

    parties: list[dict] = []
    for kurz in party_order:
        vals = [v["pct"] for v in scores[kurz].values()]
        avg = sum(vals) / len(vals) if vals else 0.0
        parties.append(
            {
                "kurz": kurz,
                "name": party_names[kurz],
                "color": party_colors.get(kurz, fallback_color),
                "avg": round(avg, 1),
                "min": round(min(vals), 1) if vals else 0.0,
                "max": round(max(vals), 1) if vals else 0.0,
                "count": len(vals),
            }
        )
    parties.sort(key=lambda p: p["avg"], reverse=True)

    all_avgs = [p["avg"] for p in parties]
    top_party = parties[0] if parties else None
    most_divisive = max(parties, key=lambda p: p["max"] - p["min"]) if parties else None
    summary = {
        "models": len(model_labels),
        "parties": len(parties),
        "overall_avg": round(sum(all_avgs) / len(all_avgs), 1) if all_avgs else 0.0,
        "top": top_party,
        "divisive": most_divisive,
    }

    return {
        "election": election,
        "models": model_labels,
        "modelColors": model_colors,
        "parties": parties,
        "scores": scores,
        "summary": summary,
    }


def build_tools_html(
    tools: list[dict[str, Any]],
    template_path: str,
) -> str:
    """Render one self-contained HTML document from a list of tool payloads.

    Each tool dict needs ``id`` / ``label`` / ``subtitle`` / ``source`` /
    ``data`` plus pre-rendered ``notes_html``.
    """
    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()
    tools_json = json.dumps(tools, ensure_ascii=False)
    return template.replace("__TOOLS__", tools_json)
