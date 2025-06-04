import os
import json
from models import Flashcard

def load_data(file_path):
    if not os.path.exists(file_path):
        return []

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Konvertiere Dictionaries zu Flashcard-Objekten
    return [Flashcard(d["question"], d["answer"], d.get("group", "")) for d in data]

def save_data(file_path, cards):
    data = [{"question": c.question, "answer": c.answer, "group": c.group} for c in cards]
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_statistics_path(group):
    return os.path.join("cards", group, "stats.json")

def load_statistics(group):
    path = get_statistics_path(group)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list) and data:
                return data[-1]  # letzte Lernsession verwenden
            elif isinstance(data, dict):
                return data  # Kompatibilität mit alten Daten
    return {"richtig": 0, "falsch": 0, "unsicher": 0}

def save_statistics(group, stats):
    path = get_statistics_path(group)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=4, ensure_ascii=False)