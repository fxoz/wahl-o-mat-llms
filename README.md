# `wahl-o-mat-llms`

How do LLMs (Large Language Models) feel about political stances in Germany?
Which parties would they vote for?

This project lets LLMs answer **two** established position-finding instruments
and visualizes the resulting alignment per party / Fraktion:

| Tool | What it compares | Source | Thesen | Parteien / Fraktionen |
| --- | --- | --- | --- | --- |
| **Wahl-O-Mat** | Party *programs* (what parties promise) | [bpb](https://www.bpb.de/themen/wahl-o-mat/) | 38 | 28 Parteien |
| **Real-O-Mat** | *Actual voting behavior* in the Bundestag (what parties did) | [fragdenstaat.de](https://real-o-mat.de/) | 20 | 7 Fraktionen |

The difference is the point: a party's program vs. its actual votes often
diverge.

## Methodology

### Wahl-O-Mat
- **LLM prompting** – done manually, it's one large prompt (`notes/prompt.md`).
  The field `eigene_meinung` precedes `entscheidung` so even non-reasoning
  models can form a (minimally) informed decision.
- **Party positions** – official data from the *Bundeszentrale für politische
  Bildung* (bpb).
- **Score calculation** – the official Wahl-O-Mat
  [Rechenmodell](https://www.bpb.de/system/files/dokument_pdf/Rechenmodell_des_Wahl-O-Mat.pdf):
  a 2 / 1 / 0 points matrix (`stimme zu` / `neutral` / `stimme nicht zu`),
  double-weighted theses count twice, skipped theses are excluded.

### Real-O-Mat
- **LLM prompting** – one prompt (`notes/real-o-mat-prompt.md`). Per thesis the
  available answer options mirror what at least one Fraktion actually gave
  (`richtig` / `nicht weit genug` / `zu weit`), exactly like the website.
- **Fraktion positions** – the JSON dataset from
  [real-o-mat.de](https://real-o-mat.de/) (CC-BY-SA 4.0), based on Bundestag
  votes Sept 2021 – Dec 2024.
- **Score calculation** – per the [Real-O-Mat
  Methodik](https://real-o-mat.de/methodik/): full match = 100 %, no match =
  0 %. Nicht-wertbare Positionen (`/`, e.g. abstention without clear position
  or Fraktion did not yet exist) count as 0 %, doubly-weighted theses count
  twice, skipped theses are removed from the denominator.

## Repository structure

```
omat/                       shared library (both tools)
├── markdown.py             tiny Markdown → HTML renderer
├── palette.py              model palette + per-tool party colors
└── results.py              result loading / aggregation / HTML build

evaluate.py                 Wahl-O-Mat: score evals/*.json against the bpb Excel
evaluate_realomat.py        Real-O-Mat: score real-o-mat-evals/*.json against real-o-mat.json
visualize.py                build index.html containing both visualizations

bundestag-2025.xlsx         bpb source data for the Wahl-O-Mat  (gitignored)
real-o-mat.json             source data for the Real-O-Mat

evals/                      Wahl-O-Mat LLM answers (one file per model)
results/                    Wahl-O-Mat scored results
real-o-mat-evals/           Real-O-Mat LLM answers (one file per model)
real-o-mat-results/         Real-O-Mat scored results

notes/
├── prompt.md               Wahl-O-Mat prompt
└── real-o-mat-prompt.md    Real-O-Mat prompt
assets/
├── template.html           shared visualization template (tool toggle)
├── wahlomat_notes.md       on-page notes for the Wahl-O-Mat tab
└── realomat_notes.md       on-page notes for the Real-O-Mat tab
index.html                  generated, self-contained visualization (GitHub Pages)
```

Anything prefixed `real-o-mat-` belongs to the Real-O-Mat; `evals/` /
`results/` (no prefix) belong to the Wahl-O-Mat. Both evaluators write the
**same result-file shape** (`{eval, results: [{Kurz, Name, Punkte,
Übereinstimmung}]}`), so the whole aggregation + visualization pipeline lives
only once in `omat/`.

## Reproduce

### Requirements
- [uv](https://github.com/astral-sh/uv#installation)

### Prompt LLMs
You prompt the LLMs manually – just copy a prompt and paste it into your model
of choice.

- **Wahl-O-Mat:** copy `notes/prompt.md`
- **Real-O-Mat:** copy `notes/real-o-mat-prompt.md`

Save the model's filled JSON answer as `evals/<model>.json` (Wahl-O-Mat) or
`real-o-mat-evals/<model>.json` (Real-O-Mat).

### Steps
1. **Wahl-O-Mat source:** download the bpb Excel for an election from the
   [bpb Archiv](https://www.bpb.de/themen/wahl-o-mat/45484/archiv/) (or
   [directly for 2025](https://www.bpb.de/system/files/datei/Wahl-O-Mat_Bundestagswahl_2025_Datensatz_v1.02.zip)),
   unzip the Excel into the repo root. If its path or sheet changes, adjust
   `BPB_EXCEL_PATH` / `SHEET_POSITION` in `evaluate.py`.
2. **Real-O-Mat source:** `real-o-mat.json` is already committed; to refresh,
   download the current JSON from <https://real-o-mat.de/>.

3. Score:
   ```bash
   uv sync
   uv run evaluate.py           # Wahl-O-Mat → results/
   uv run evaluate_realomat.py  # Real-O-Mat → real-o-mat-results/
   ```

### Visualize
```bash
uv run visualize.py
```
Generates a self-contained `index.html` with both tools side by side (toggle
at the top), served directly by GitHub Pages.
