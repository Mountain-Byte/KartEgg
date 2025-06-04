import tkinter as tk
from tkinter import messagebox
import json
import os
from datetime import datetime

def start_learning(group, cards, parent_window=None, on_close=None):
    # Schließe das Hauptfenster, falls übergeben
    if parent_window:
        parent_window.destroy()
    show_learning_window(cards, group, on_close=on_close)

def show_learning_window(cards, group, on_close=None):
    current_index = 0
    results = []

    def show_card():
        card = cards[current_index]
        question_label.config(text=f"Frage:\n{card.question}")
        answer_label.config(text="")

    def show_answer():
        card = cards[current_index]
        answer_label.config(text=f"Antwort:\n{card.answer}")

    def rate_card(feedback):
        nonlocal current_index
        card = cards[current_index]
        results.append((card.question, feedback))
        next_card()

    def next_card():
        nonlocal current_index
        current_index += 1
        if current_index >= len(cards):
            # Fehlende Karten als "unbekannt" markieren
            learned_questions = {q for q, _ in results}
            for card in cards:
                if card.question not in learned_questions:
                    results.append((card.question, "unbekannt"))

            summary = {"richtig": 0, "falsch": 0, "unsicher": 0, "unbekannt": 0}
            for _, result in results:
                if result in summary:
                    summary[result] += 1

            save_learning_results(group, results)

            info = (
                f"Lernen abgeschlossen!\n\n"
                f"✅ Richtig: {summary['richtig']}\n"
                f"❌ Falsch: {summary['falsch']}\n"
                f"❓ Unsicher: {summary['unsicher']}\n"
                f"❔ Unbekannt: {summary['unbekannt']}"
            )
            messagebox.showinfo("Fertig", info)

            if on_close:
                try:
                    on_close()
                except Exception as e:
                    print("Fehler beim Callback:", e)

            learn_window.destroy()

            # Hauptfenster nach Lernmodus neu starten
            from ui.main_ui import start_main_app
            start_main_app(group)
        else:
            show_card()


    def on_window_close():
        # Alle noch nicht bewerteten Karten als "unbekannt" ergänzen
        for i in range(current_index, len(cards)):
            results.append((cards[i].question, "unbekannt"))

        # Ergebnisse speichern
        save_learning_results(group, results)

        # Optional: Callback aufrufen (z. B. für Diagramm)
        if on_close:
            try:
                on_close()
            except Exception as e:
                print("Fehler beim Callback (Fensterschließen):", e)

        # Fenster schließen
        learn_window.destroy()

        # Hauptfenster neu starten
        from ui.main_ui import start_main_app
        start_main_app(group)


    learn_window = tk.Tk()
    learn_window.title("Lernmodus")
    learn_window.protocol("WM_DELETE_WINDOW", on_window_close)

    question_label = tk.Label(learn_window, text="", font=("Arial", 14), wraplength=400, justify="center")
    question_label.pack(pady=10)

    answer_label = tk.Label(learn_window, text="", font=("Arial", 12), fg="gray", wraplength=400, justify="center")
    answer_label.pack(pady=10)

    btn_frame = tk.Frame(learn_window)
    btn_frame.pack(pady=10)

    tk.Button(btn_frame, text="Antwort zeigen", command=show_answer).pack(side=tk.LEFT, padx=5)

    feedback_frame = tk.Frame(learn_window)
    feedback_frame.pack(pady=5)

    tk.Button(feedback_frame, text="✅ Richtig", command=lambda: rate_card("richtig")).pack(side=tk.LEFT, padx=5)
    tk.Button(feedback_frame, text="❌ Falsch", command=lambda: rate_card("falsch")).pack(side=tk.LEFT, padx=5)
    tk.Button(feedback_frame, text="❓ Unsicher", command=lambda: rate_card("unsicher")).pack(side=tk.LEFT, padx=5)

    show_card()
    learn_window.mainloop()

def save_learning_results(group, results):
    folder = os.path.join("cards", group)
    os.makedirs(folder, exist_ok=True)
    stats_file = os.path.join(folder, "stats.json")

    # Zähle alle Bewertungen
    summary = {
        "timestamp": datetime.now().isoformat(),
        "richtig": 0,
        "falsch": 0,
        "unsicher": 0,
        "unbekannt": 0,
        "details": []
    }

    for question, result in results:
        if result in summary:
            summary[result] += 1
        else:
            summary["unbekannt"] += 1  # Fallback falls ein unbekannter Wert kommt
        summary["details"].append({"question": question, "result": result})

    # Alte Daten laden
    if os.path.exists(stats_file):
        try:
            with open(stats_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            data = []
    else:
        data = []

    # Neue Session anhängen
    data.append(summary)

    with open(stats_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)



        

        

