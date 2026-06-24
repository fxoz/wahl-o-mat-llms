# `wahl-o-mat-llms`

How do LLMs (Large Language Models) feel about political stances in Germany?
Which parties would they vote for (I used data from the federal election 2025)?

## Methodology

- LLM prompting
  - Done manually. It's just one large prompt (`prompt.md`).
  - To increase accuracy/quality on non-reasoning models, the field `eigene_meinung` is used as a short summary of the LLM's opinion on the party positions. Because this field occurs before `entscheidung`, it allows for a more (albeit minimally) informed decision.
- Party positions
  - Official data from Bundeszentrale für politische Bildung
- Score calculation
  - Based on the official algorithm of the Wahl-O-Mat which is publicly available: [Rechenmodell](https://www.bpb.de/system/files/dokument_pdf/Rechenmodell_des_Wahl-O-Mat.pdf)


## Reproduce

### Requirements
- [uv](https://github.com/astral-sh/uv#installation)

### Prompt LLMs

Unfortunately, you will need to manually prompt the LLMs.
As it's just one large prompt, you can easily copy the content of `prompt.md` and paste it into your LLM of choice.

This shouldn't take *much* more effort than copying the model ID into a program and running it :)

### Steps

1. Download the excel file of an election from the archive of the Bundeszentrale für politische Bildung (bpb):
   - [bpb Archiv](https://www.bpb.de/themen/wahl-o-mat/45484/archiv/)

    Or, for quick acess:
    - [Wahl-O-Mat Bundestagswahl 2025 (Direct download)](https://www.bpb.de/system/files/datei/Wahl-O-Mat_Bundestagswahl_2025_Datensatz_v1.02.zip)

    Unzip the excel file into the root directory of this repository.

2. Change `BPB_EXCEL_PATH` in `interpreter.py` to the path of the excel file from the previous step. Optional, if the format of the excel file changes, you can also change `SHEET_POSITION` to the sheet with the party positions, 0-indexed. How? At the bottom of the excel file, you can see the sheet names. It's usually the third sheet, so the default value is 2.

3. Run: 
    ```bash
    uv sync
    uv run main.py
    ```


### Visualize

Run `uv run visualize.py` to generate a self-contained HTML file with a visualization of the results. It saves the file as `index.html` so Github Pages can serve it directly.