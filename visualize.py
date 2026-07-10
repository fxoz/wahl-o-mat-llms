import json
import glob
import os
from html import escape

# Which election should be visualized? The part after the ``--`` in the result
# filenames (e.g. ``bundestagswahl-2025`` for ``gemini-...--bundestagswahl-2025.json``).
ELECTION = "bundestagswahl-2025"
RESULTS_DIR = "results"
OUTPUT_FILE = "index.html"

# Brand colors for well-known German parties (used as row accent dots).
PARTY_COLORS: dict[str, str] = {
    "SPD": "#E3000F",
    "CDU / CSU": "#5a5f66",
    "GRÜNE": "#46A62E",
    "FDP": "#FFCC00",
    "AfD": "#009EE0",
    "Die Linke": "#BE3075",
    "BSW": "#9C27B0",
    "FREIE WÄHLER": "#FF8C00",
    "Tierschutz": "#8BC34A",
    "PIRATEN": "#7d4cdb",
    "Volt": "#5B3E96",
    "SSW": "#E58FAE",
    "Die PARTEI": "#9aa0a6",
    "ÖDP": "#a3c948",
    "MLPD": "#d32f2f",
    "SGP": "#ef6c00",
    "MERA25": "#c2185b",
    "PdF": "#26a69a",
    "PdH": "#42a5f5",
    "dieBasis": "#6d4c41",
    "BüSo": "#8d6e63",
    "WerteUnion": "#37474f",
    "BÜNDNIS D": "#5c6bc0",
    "Bündnis C": "#7986cb",
    "BP": "#90a4ae",
}

# Distinctive palette for coloring each LLM/model.
MODEL_PALETTE: list[str] = [
    "#7aa2f7",
    "#bb9af7",
    "#e0af68",
    "#9ece6a",
    "#f7768e",
    "#7dcfff",
    "#ff9e64",
    "#c0caf5",
    "#94cf7c",
    "#f4a7d7",
]


def load_results(election: str) -> list[dict]:
    """Load every result file matching ``*--{election}.json`` from the results dir."""
    pattern = os.path.join(RESULTS_DIR, f"*--{election}.json")
    paths = sorted(glob.glob(pattern))
    if not paths:
        raise FileNotFoundError(
            f"Keine Ergebnisdateien gefunden für die Wahl '{election}' in {RESULTS_DIR}/ "
            f"(Muster: *--{election}.json)"
        )

    models: list[dict] = []
    for path in paths:
        with open(path, "r", encoding="utf-8") as f:
            models.append(json.load(f))
    return models


def _assign_model_colors(labels: list[str]) -> dict[str, str]:
    colors: dict[str, str] = {}
    for i, label in enumerate(labels):
        colors[label] = MODEL_PALETTE[i % len(MODEL_PALETTE)]
    return colors


def aggregate(models: list[dict], election: str) -> dict:
    """Build the data payload consumed by the HTML visualization."""
    model_labels = [m["eval"] for m in models]
    model_colors = _assign_model_colors(model_labels)

    # Collect every party and their per-model score.
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

    # Per-party stats; sort by average agreement (desc) by default.
    parties: list[dict] = []
    for kurz in party_order:
        vals = [v["pct"] for v in scores[kurz].values()]
        avg = sum(vals) / len(vals) if vals else 0.0
        parties.append(
            {
                "kurz": kurz,
                "name": party_names[kurz],
                "color": PARTY_COLORS.get(kurz, "#7d8597"),
                "avg": round(avg, 1),
                "min": round(min(vals), 1) if vals else 0.0,
                "max": round(max(vals), 1) if vals else 0.0,
                "count": len(vals),
            }
        )
    parties.sort(key=lambda p: p["avg"], reverse=True)

    # Summary headline numbers.
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


HTML_TEMPLATE = open("assets/template.html", "r", encoding="utf-8").read()


def build_html(payload: dict) -> str:
    """Render the results into a single self-contained HTML document."""
    data_json = json.dumps(payload, ensure_ascii=False)
    election = escape(payload["election"])
    return HTML_TEMPLATE.replace("__ELECTION__", election).replace(
        "__DATA__", data_json
    )


def render(election: str, output_file: str) -> dict:
    """Aggregate results for an election and write an HTML visualization file.

    Returns the assembled payload so callers can print a short summary.
    """
    models = load_results(election)
    payload = aggregate(models, election)
    html = build_html(payload)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)
    return payload


def main() -> None:
    import sys

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    payload = render(ELECTION, OUTPUT_FILE)
    print(f"✅ Visualisierung erstellt: {OUTPUT_FILE}")
    print(f"   Wahl: {ELECTION}")
    print(
        f"   Modelle: {len(payload['models'])} · Parteien: {payload['summary']['parties']}"
    )
    print(f"   Öffne die Datei im Browser, um die Ergebnisse zu erkunden.")


if __name__ == "__main__":
    main()
