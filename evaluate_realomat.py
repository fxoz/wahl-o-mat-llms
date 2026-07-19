"""Real-O-Mat evaluator.

The Real-O-Mat (https://real-o-mat.de/) compares the **actual voting
behavior** of the seven Bundestagsfraktionen to the user's positions on
20 theses.  Unlike the Wahl-O-Mat (which scores party *programs* with a
2/1/0 matrix), the Real-O-Mat scores binary agreement:

* ``richtig``           = full match with the proposal
* ``nicht weit genug``  = rejected because it does not go far enough
* ``zu weit``           = rejected because it goes too far
* ``/`` (nicht wertbar) = abstention / party did not exist yet  -> 0% match
* skipped by the user   -> excluded from the denominator

A thesis can be doubly weighted, in which case it counts twice.  The
real-o-mat methodology is documented at
https://real-o-mat.de/methodik/.
"""

from __future__ import annotations

import glob
import json
import os
import sys

from omat.results import write_result

SOURCE_PATH = "real-o-mat.json"
EVALS_DIR = "real-o-mat-evals"
RESULTS_DIR = "real-o-mat-results"
ELECTION = "realomat-btw2025"

# Stable display package for each of the seven Fraktionen (party key -> Kurz).
REALOMAT_PARTIES: list[tuple[str, str, str]] = [
    ("spd", "SPD", "Sozialdemokratische Partei Deutschlands"),
    ("cdu", "CDU / CSU", "Christlich Demokratische Union / Christlich-Soziale Union"),
    ("fdp", "FDP", "Freie Demokratische Partei"),
    ("gruene", "GRÜNE", "Bündnis 90/Die Grünen"),
    ("bsw", "BSW", "Bündnis Sahra Wagenknecht – Vernunft und Gerechtigkeit"),
    ("linke", "Die Linke", "Die Linke"),
    ("afd", "AfD", "Alternative für Deutschland"),
]

VALID_DECISIONS = {"RICHTIG", "ZU WEIT", "NICHT WEIT GENUG", "SKIP"}
NOT_RATABLE = "/"


def load_source(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_answers(answers: list[dict], source: dict) -> None:
    theses = source["data"]
    if len(answers) != len(theses):
        raise ValueError(
            f"Anzahl Antworten ({len(answers)}) passt nicht zur Anzahl Thesen ({len(theses)})."
        )
    expected_fields = {
        "id", "these", "kategorie", "optionen", "eigene_meinung", "entscheidung", "doppelt_gewichten"
    }
    by_index = {t["index"]: t for t in theses}
    for idx, ans in enumerate(answers):
        if set(ans.keys()) != expected_fields:
            raise ValueError(
                f"Antwort {idx} hat falsche Felder: {sorted(ans.keys())} "
                f"(erwartet: {sorted(expected_fields)})."
            )
        thesis = by_index.get(ans["id"])
        if ans["these"].strip() != thesis["thesis"].strip():
            raise ValueError(
                f"Antwort {idx} (id={ans['id']}) passt nicht zur These aus {SOURCE_PATH}."
            )
        if ans["kategorie"] != thesis["category"]:
            raise ValueError(
                f"Antwort {idx} (id={ans['id']}): 'kategorie' wurde veraendert."
            )
        # The Real-O-Mat only offers answer options that at least one Fraktion
        # actually gave (see Methodik).  Verify the per-thesis `optionen` were
        # not tampered with, then enforce the model's decision is among them.
        available = {a["answer"] for a in thesis["answers"]} - {NOT_RATABLE}
        available_upper = sorted(v.upper() for v in available)
        optionen = sorted(o.upper() for o in ans["optionen"])
        if optionen != available_upper:
            raise ValueError(
                f"Antwort {idx} (id={ans['id']}): 'optionen' {optionen} stimmt nicht mit den "
                f"verfügbaren Antworten {available_upper} aus {SOURCE_PATH} überein."
            )
        decision = ans["entscheidung"]
        if not isinstance(decision, str) or decision.upper() not in VALID_DECISIONS:
            raise ValueError(
                f"Antwort {idx}: 'entscheidung' muss aus {sorted(VALID_DECISIONS)} stammen, "
                f"ist aber {decision!r}."
            )
        if decision.upper() != "SKIP" and decision.upper() not in optionen:
            raise ValueError(
                f"Antwort {idx} (id={ans['id']}): {decision!r} ist nicht in den verfügbaren "
                f"Optionen {optionen}."
            )
        if not isinstance(ans["doppelt_gewichten"], bool):
            raise ValueError(f"Antwort {idx}: 'doppelt_gewichten' muss ein bool sein.")


def party_answers_for(thesis: dict) -> dict[str, str]:
    return {a["party"]: a["answer"] for a in thesis["answers"]}


def score_party(
    party_key: str,
    answers: list[dict],
    theses: list[dict],
) -> tuple[int, int, float]:
    """Return (points, max_points, percentage) for a single Fraktion."""
    points = 0
    max_points = 0
    theses_by_index = {t["index"]: t for t in theses}
    for ans in answers:
        decision = ans["entscheidung"].upper()
        if decision == "SKIP":
            continue
        weight = 2 if ans["doppelt_gewichten"] else 1
        max_points += weight
        thesis = theses_by_index[ans["id"]]
        party_ans = party_answers_for(thesis).get(party_key, NOT_RATABLE)
        # everything except an exact match counts as 0% — including "/"
        if party_ans != NOT_RATABLE and decision.lower() == party_ans.lower():
            points += weight
    pct = (points / max_points * 100) if max_points else 0.0
    return points, max_points, pct


def process_single(name: str, source: dict) -> None:
    eval_path = os.path.join(EVALS_DIR, f"{name}.json")
    if not os.path.exists(eval_path):
        print(f"❌ Fehler: {eval_path} existiert nicht.")
        return
    with open(eval_path, "r", encoding="utf-8") as f:
        answers = json.load(f)

    validate_answers(answers, source)

    theses = source["data"]
    results: list[dict] = []
    for party_key, kurz, full_name in REALOMAT_PARTIES:
        points, max_points, pct = score_party(party_key, answers, theses)
        results.append(
            {
                "Kurz": kurz,
                "Name": full_name,
                "Punkte": f"{points}/{max_points}",
                "Übereinstimmung": pct,
            }
        )
    results.sort(key=lambda r: r["Übereinstimmung"], reverse=True)

    result_path = os.path.join(RESULTS_DIR, f"{name}--{ELECTION}.json")
    write_result(name, results, result_path)
    print(f"\n✅ Ergebnis gespeichert in {result_path}")

    print("\n" + "=" * 56)
    print(f" DEIN REAL-O-MAT ERGEBNIS ({name}.json)")
    print("=" * 56)
    print(f"{'Fraktion':<12} | {'Punkte':<8} | Übereinstimmung")
    print("-" * 56)
    for r in results:
        print(f"{r['Kurz']:<12} | {r['Punkte']:<8} | {r['Übereinstimmung']:.1f}%")
    print("=" * 56)


def calculate_match() -> None:
    if not os.path.exists(SOURCE_PATH):
        print(f"❌ Fehler: {SOURCE_PATH} nicht gefunden.")
        return
    source = load_source(SOURCE_PATH)
    eval_files = sorted(glob.glob(os.path.join(EVALS_DIR, "*.json")))
    if not eval_files:
        print(f"❌ Keine JSON-Dateien in {EVALS_DIR}/ gefunden.")
        return
    for path in eval_files:
        name = os.path.splitext(os.path.basename(path))[0]
        print(f"\n>>> Verarbeite {name}.json ...")
        try:
            process_single(name, source)
        except ValueError as e:
            print(f"❌ {name}: {e}")
            sys.exit(1)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    calculate_match()
