"""Render Wahl-O-Mat *and* Real-O-Mat results into one self-contained ``index.html``.

Both tools share the same result-file shape and therefore the same
aggregation/visualization pipeline (see :mod:`omat.results`).  This
script loads each tool's results, aggregates them, renders the per-tool
notes markdown, and injects a single ``TOOLS`` payload into the template.
"""

from __future__ import annotations

import json
import os
import sys

from omat.palette import REALOMAT_PARTY_COLORS, WAHLOMAT_PARTY_COLORS
from omat.results import aggregate, build_tools_html, load_results
from omat.markdown import render_markdown

OUTPUT_FILE = "index.html"
TEMPLATE_PATH = "assets/template.html"

WAHLOMAT_ELECTION = "bundestagswahl-2025"
WAHLOMAT_RESULTS_DIR = "results"
WAHLOMAT_NOTES = "assets/wahlomat_notes.md"

REALOMAT_ELECTION = "realomat-btw2025"
REALOMAT_RESULTS_DIR = "real-o-mat-results"
REALOMAT_NOTES = "assets/realomat_notes.md"


def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def build_tool(
    *,
    tool_id: str,
    label: str,
    subtitle: str,
    source: str,
    notes_path: str,
    results_dir: str,
    election: str,
    party_colors: dict[str, str],
) -> dict:
    """Aggregate one tool's results into a tool descriptor for the template."""
    models = load_results(results_dir, election)
    data = aggregate(models, party_colors, election=election)
    notes_html = render_markdown(read_text(notes_path))
    return {
        "id": tool_id,
        "label": label,
        "subtitle": subtitle,
        "source": source,
        "notes_html": notes_html,
        "data": data,
        "models_count": len(data["models"]),
        "parties_count": len(data["parties"]),
    }


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    tools = [
        build_tool(
            tool_id="wahlomat",
            label="Wahl-O-Mat",
            subtitle="Parteipositionen aus Wahlprogrammen (bpb)",
            source="Daten: Bundeszentrale für politische Bildung (bpb)",
            notes_path=WAHLOMAT_NOTES,
            results_dir=WAHLOMAT_RESULTS_DIR,
            election=WAHLOMAT_ELECTION,
            party_colors=WAHLOMAT_PARTY_COLORS,
        ),
        build_tool(
            tool_id="realomat",
            label="Real-O-Mat",
            subtitle="Tatsächliches Abstimmungsverhalten im Bundestag",
            source="Daten: fragdenstaat.de · CC-BY-SA 4.0",
            notes_path=REALOMAT_NOTES,
            results_dir=REALOMAT_RESULTS_DIR,
            election=REALOMAT_ELECTION,
            party_colors=REALOMAT_PARTY_COLORS,
        ),
    ]

    html = build_tools_html(tools, TEMPLATE_PATH)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ Visualisierung erstellt: {OUTPUT_FILE}")
    for t in tools:
        print(
            f"   {t['label']}: {t['models_count']} Modelle · "
            f"{t['parties_count']} "
            f"{'Parteien' if t['id'] == 'wahlomat' else 'Fraktionen'}"
        )
    print("   Öffne die Datei im Browser, um die Ergebnisse zu erkunden.")


if __name__ == "__main__":
    main()
