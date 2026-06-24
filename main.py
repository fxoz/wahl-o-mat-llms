import glob
import os
import json
import sys
import pandas as pd

BPB_EXCEL_PATH = "bundestag-2025.xlsx"
SHEET_POSITION = 2


def load_data(json_filename):
    # Pfad zur JSON-Datei zusammenbauen
    json_path = os.path.join("evals", f"{json_filename}.json")

    if not os.path.exists(json_path):
        print(f"❌ Fehler: Die Datei {json_path} existiert nicht.")
        return None, None

    if not os.path.exists(BPB_EXCEL_PATH):
        print(f"❌ Fehler: Die Excel-Datei {BPB_EXCEL_PATH} wurde nicht gefunden.")
        return None, None

    # Daten laden
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            user_answers = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Fehler: Die JSON-Datei {json_path} ist ungültig: {e}")
        sys.exit(1)

    # Validierung der JSON-Struktur
    if not isinstance(user_answers, list):
        print(
            f"❌ Fehler: Die JSON-Datei {json_path} muss eine Liste von Antworten enthalten."
        )
        sys.exit(1)

    required_keys = {"id", "entscheidung", "doppelt_gewichten"}
    valid_decisions = {"JA", "NEUTRAL", "NEIN", "ÜBERSPRINGEN"}
    for idx, ans in enumerate(user_answers):
        if not isinstance(ans, dict):
            print(f"❌ Fehler: Antwort an Index {idx} ist kein Objekt.")
            sys.exit(1)
        if not required_keys.issubset(ans.keys()):
            print(
                f"❌ Fehler: Antwort an Index {idx} fehlen erforderliche Felder: {required_keys - ans.keys()}"
            )
            sys.exit(1)
        if not isinstance(ans["id"], int):
            print(
                f"❌ Fehler: Antwort an Index {idx} hat ein ungültiges 'id'-Feld (muss int sein)."
            )
            sys.exit(1)
        if not isinstance(ans["entscheidung"], str):
            print(
                f"❌ Fehler: Antwort an Index {idx} hat ein ungültiges 'entscheidung'-Feld (muss str sein)."
            )
            sys.exit(1)
        if ans["entscheidung"].upper() not in valid_decisions:
            print(
                f"❌ Fehler: Antwort an Index {idx} hat einen ungültigen Wert für 'entscheidung': {ans['entscheidung']}"
            )
            sys.exit(1)
        if not isinstance(ans["doppelt_gewichten"], bool):
            print(
                f"❌ Fehler: Antwort an Index {idx} hat ein ungültiges 'doppelt_gewichten'-Feld (muss bool sein)."
            )
            sys.exit(1)

    df_excel = pd.read_excel(BPB_EXCEL_PATH, sheet_name=SHEET_POSITION)
    return user_answers, df_excel


REPLACEMENT_MAP = {
    "Tierschutzpartei": "Tierschutz",
    "Die Gerechtigkeitspartei - Team Todenhöfer": "Todenhöfer",
    "Verjüngungsforschung": "Verjüngung",
    "MENSCHLICHE WELT": "MENSCHLICHE",
    "BÜNDNIS DEUTSCHLAND": "BÜNDNIS D",
}


def get_points(user_pos, party_pos, double_weight=False):
    # Mapping der Werte auf ein einheitliches Format
    mapping = {"JA": "stimme zu", "NEUTRAL": "neutral", "NEIN": "stimme nicht zu"}

    u_pos = mapping.get(user_pos.upper(), "überspringen")
    p_pos = str(party_pos).strip().lower()

    if u_pos == "überspringen":
        return 0

    # Berechnungsmatrix ohne Gewichtung
    matrix = {
        "stimme zu": {"stimme zu": 2, "neutral": 1, "stimme nicht zu": 0},
        "neutral": {"stimme zu": 1, "neutral": 2, "stimme nicht zu": 1},
        "stimme nicht zu": {"stimme zu": 0, "neutral": 1, "stimme nicht zu": 2},
    }

    base_points = matrix.get(u_pos, {}).get(p_pos, 0)

    # Bei doppelter Gewichtung werden die Punkte verdoppelt
    return base_points * 2 if double_weight else base_points


def process_single(json_input):
    user_answers, df = load_data(json_input)
    if user_answers is None:
        return

    # Umwandlung der User-Antworten in ein schnelles Dict für Lookups (ID + 1 wegen Excel-Offset)
    user_dict = {ans["id"] + 1: ans for ans in user_answers}

    # Ergebnis-Speicher für die Parteien: { Kurzbezeichnung: { "max": X, "score": Y, "name": Z } }
    party_scores = {}

    # Gruppieren nach Partei und Thesen
    for _, row in df.iterrows():
        party_key = REPLACEMENT_MAP.get(
            row["Partei: Kurzbezeichnung"], row["Partei: Kurzbezeichnung"]
        )
        party_name = row["Partei: Name"]
        these_nr = int(row["These: Nr."])
        party_pos = row["Position: Position"]

        if party_key not in party_scores:
            party_scores[party_key] = {"name": party_name, "score": 0, "max_score": 0}

        # Prüfen, ob der Nutzer diese These beantwortet hat
        if these_nr in user_dict:
            user_ans = user_dict[these_nr]

            # Punkte berechnen
            points = get_points(
                user_ans["entscheidung"], party_pos, user_ans["doppelt_gewichten"]
            )

            # Maximal erreichbare Punkte für diese These berechnen (wenn der Nutzer zustimmt/nicht zustimmt = 2 bzw 4)
            # Wenn der Nutzer "neutral" wählt, sind max. Punkte ebenfalls 2 (bzw. 4) bei Übereinstimmung.
            # Wenn die These übersprungen wird, zählt sie nicht in die Maximalpunktzahl.
            if user_ans["entscheidung"].upper() in ["JA", "NEUTRAL", "NEIN"]:
                max_possible = 4 if user_ans["doppelt_gewichten"] else 2
                party_scores[party_key]["max_score"] += max_possible
                party_scores[party_key]["score"] += points

    # Auswertung & Sortierung
    results = []
    for party, data in party_scores.items():
        if data["max_score"] > 0:
            percentage = (data["score"] / data["max_score"]) * 100
        else:
            percentage = 0.0

        results.append(
            {
                "Kurz": party,
                "Name": data["name"],
                "Punkte": f"{data['score']}/{data['max_score']}",
                "Übereinstimmung": percentage,
            }
        )

    # Nach Übereinstimmung sortieren
    results = sorted(results, key=lambda x: x["Übereinstimmung"], reverse=True)

    # Ergebnis als JSON speichern
    os.makedirs("results", exist_ok=True)
    result_path = os.path.join("results", f"{json_input}--bundestagswahl-2025.json")
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "eval": json_input,
                "results": results,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )
    print(f"\n✅ Ergebnis gespeichert in {result_path}")

    # Ausgabe als schöne Tabelle
    print("\n" + "=" * 50)
    print(f" DEIN WAHL-O-MAT ERGEBNIS ({json_input}.json)")
    print("=" * 50)
    print(f"{'Partei':<12} | {'Punkte':<8} | Übereinstimmung")
    print("-" * 50)
    for res in results:
        print(f"{res['Kurz']:<12} | {res['Punkte']:<8} | {res['Übereinstimmung']:.1f}%")
    print("=" * 50)


def calculate_match():
    # CLI Abfrage des Dateinamens
    json_input = input(
        "Bitte den Namen der JSON-Datei eingeben (ohne 'evals/' und '.json', Enter für alle): "
    ).strip()

    if json_input:
        process_single(json_input)
    else:
        eval_files = sorted(glob.glob(os.path.join("evals", "*.json")))
        if not eval_files:
            print("❌ Keine JSON-Dateien in evals/ gefunden.")
            return
        for path in eval_files:
            name = os.path.splitext(os.path.basename(path))[0]
            print(f"\n>>> Verarbeite {name}.json ...")
            process_single(name)


if __name__ == "__main__":
    calculate_match()
