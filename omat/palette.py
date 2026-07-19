"""Color palettes shared by both tools.

Keep per-party / per-fraktion brand colors and the model palette together so
the visualization stays consistent across Wahl-O-Mat and Real-O-Mat.
"""

from __future__ import annotations

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

WAHLOMAT_PARTY_COLORS: dict[str, str] = {
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

# The Real-O-Mat covers the seven Bundestagsfraktionen of the 2021–2025 term.
REALOMAT_PARTY_COLORS: dict[str, str] = {
    "SPD": "#E3000F",
    "CDU / CSU": "#5a5f66",
    "GRÜNE": "#46A62E",
    "FDP": "#FFCC00",
    "AfD": "#009EE0",
    "Die Linke": "#BE3075",
    "BSW": "#9C27B0",
}


def assign_model_colors(labels: list[str]) -> dict[str, str]:
    """Assign a stable color from :data:`MODEL_PALETTE` to each label."""
    return {label: MODEL_PALETTE[i % len(MODEL_PALETTE)] for i, label in enumerate(labels)}
