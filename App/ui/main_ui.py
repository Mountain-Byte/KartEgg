import os
import json
import tkinter as tk
from tkinter import messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from models import Flashcard
from data_manager import load_data, save_data, load_statistics
from ui.pie_chart import draw_pie_chart
import learning_mode
from ui.group_selection import get_all_groups

class FlashcardApp(tk.Frame):
    def __init__(self, master, group):
        super().__init__(master)
        self.master = master
        self.group = group
        self.pack(fill="both", expand=True)
        self.cards = []
        self.selected_index = None
        self.edit_mode = False
        self.file_path = os.path.join("cards", self.group, "cards.json")
        
        self.create_widgets()
        
        # Diagramm-Frame vorbereiten (muss vor draw_pie existieren!)
        self.diagram_frame = tk.Frame(self.chart_frame)
        self.diagram_frame.grid(row=0, column=0, sticky="nsew")

        self.load_cards()
        self.draw_pie()
        self.after(200, self.fix_window_size)

    def create_widgets(self):
        # Hauptframe: Spaltengewichte für 2/3 links und 1/3 rechts
        self.columnconfigure(0, weight=2)
        self.columnconfigure(1, weight=1)
        for i in range(5):
            self.rowconfigure(i, weight=0)
        self.rowconfigure(4, weight=1)

        # Linker Bereich (Eingabe + Listboxen)
        self.left_frame = tk.Frame(self)
        self.left_frame.grid(row=0, column=0, rowspan=5, sticky="nsew", padx=5, pady=5)
        self.left_frame.columnconfigure(1, weight=1)
        for i in range(5):
            self.left_frame.rowconfigure(i, weight=0)
        self.left_frame.rowconfigure(4, weight=1)

        # Gruppen-Label + Dropdown
        tk.Label(self.left_frame, text="Gruppe:").grid(row=0, column=0, sticky="w")
        self.group_var = tk.StringVar(value=self.group)
        self.group_dropdown = tk.OptionMenu(self.left_frame, self.group_var, *get_all_groups(), command=self.change_group)
        self.group_dropdown.grid(row=0, column=1, sticky="ew", pady=2)

        # Frage-Eingabe
        tk.Label(self.left_frame, text="Frage:").grid(row=1, column=0, sticky="w")
        self.question_var = tk.StringVar()
        self.question_var.trace_add("write", self.toggle_create_button)
        self.question_entry = tk.Entry(self.left_frame, textvariable=self.question_var)
        self.question_entry.grid(row=1, column=1, sticky="ew", pady=2)

        # Antwort-Eingabe
        tk.Label(self.left_frame, text="Antwort:").grid(row=2, column=0, sticky="w")
        self.answer_var = tk.StringVar()
        self.answer_var.trace_add("write", self.toggle_create_button)
        self.answer_entry = tk.Entry(self.left_frame, textvariable=self.answer_var)
        self.answer_entry.grid(row=2, column=1, sticky="ew", pady=2)

        # Button-Frame mit 6 Spalten
        button_frame = tk.Frame(self.left_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=10, sticky="ew")
        for i in range(4):
            button_frame.columnconfigure(i, weight=1, uniform="btn")
        button_frame.columnconfigure(4, weight=10)
        button_frame.columnconfigure(5, weight=1, uniform="btn")

        self.btn_create = tk.Button(button_frame, text="Karte erstellen", command=self.create_card, state="disabled")
        self.btn_edit = tk.Button(button_frame, text="Bearbeiten", command=self.edit_card, state="disabled")
        self.btn_save = tk.Button(button_frame, text="Speichern", command=self.save_card, state="disabled")
        self.btn_delete = tk.Button(button_frame, text="Löschen", command=self.delete_card, state="disabled")
        self.btn_learn = tk.Button(button_frame, text="Lernen", command=self.start_learning_mode)

        self.btn_create.grid(row=0, column=0, sticky="nsew", padx=2, ipady=5)
        self.btn_edit.grid(row=0, column=1, sticky="nsew", padx=2, ipady=5)
        self.btn_save.grid(row=0, column=2, sticky="nsew", padx=2, ipady=5)
        self.btn_delete.grid(row=0, column=3, sticky="nsew", padx=2, ipady=5)
        self.btn_learn.grid(row=0, column=5, sticky="nsew", padx=2, ipady=5)

        # Frame für Listboxen (Status + Frage + Antwort)
        self.card_listbox_frame = tk.Frame(self.left_frame)
        self.card_listbox_frame.grid(row=4, column=0, columnspan=2, sticky="nsew")
        self.card_listbox_frame.columnconfigure(0, weight=0)   # Status (schmal)
        self.card_listbox_frame.columnconfigure(1, weight=4)   # Frage
        self.card_listbox_frame.columnconfigure(2, weight=5)   # Antwort
        self.card_listbox_frame.rowconfigure(0, weight=1)

        self.status_listbox = tk.Listbox(
            self.card_listbox_frame,
            exportselection=False,
            width=4,
            justify="center",
            bd=0,
            highlightthickness=0,
            activestyle="none"
        )
        self.question_listbox = tk.Listbox(self.card_listbox_frame, exportselection=False)
        self.answer_listbox = tk.Listbox(self.card_listbox_frame, exportselection=False)

        self.status_listbox.grid(row=0, column=0, sticky="nsw", padx=(2, 1))
        self.question_listbox.grid(row=0, column=1, sticky="nsew")
        self.answer_listbox.grid(row=0, column=2, sticky="nsew")

        self.status_listbox.bind("<<ListboxSelect>>", lambda e: self.after_idle(self.on_select, e))
        self.question_listbox.bind("<<ListboxSelect>>", lambda e: self.after_idle(self.on_select, e))
        self.answer_listbox.bind("<<ListboxSelect>>", lambda e: self.after_idle(self.on_select, e))

        # Rechter Bereich (Diagramm + Info unten)
        self.chart_frame = tk.Frame(self)
        self.chart_frame.grid(row=0, column=1, rowspan=5, sticky="nsew", padx=5, pady=5)
        self.chart_frame.columnconfigure(0, weight=1)
        self.chart_frame.rowconfigure(0, weight=1)
        self.chart_frame.rowconfigure(1, weight=0)

        bottom_info_frame = tk.Frame(self.chart_frame)
        bottom_info_frame.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        bottom_info_frame.columnconfigure(0, weight=1)
        bottom_info_frame.columnconfigure(1, weight=1)

        self.card_count_label = tk.Label(bottom_info_frame, text="Karten 0 / 0", anchor="w")
        self.card_count_label.grid(row=0, column=0, sticky="w", padx=5)

        self.details_button = tk.Button(bottom_info_frame, text="Details", command=self.show_details)
        self.details_button.grid(row=0, column=1, sticky="nsew", padx=2, ipady=5)

        self.master.bind("<Button-1>", self.on_click_outside)

    def toggle_create_button(self, *args):
        if not self.edit_mode:
            q = self.question_var.get().strip()
            a = self.answer_var.get().strip()
            self.btn_create.config(state="normal" if q and a else "disabled")

    def load_latest_stats(self, base_folder="cards"):
        filepath = os.path.join(base_folder, self.group, "stats.json")
        if not os.path.exists(filepath):
            return {"details": []}
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        latest = data[-1] if isinstance(data, list) else data
        return latest


    def load_cards(self):
        self.cards = load_data(self.file_path)
        stats = self.load_latest_stats()
        details = stats.get("details", [])

        self.question_listbox.delete(0, tk.END)
        self.answer_listbox.delete(0, tk.END)
        self.status_listbox.delete(0, tk.END)

        color_map = {
            "richtig": "#4CAF50",
            "falsch": "#F44336",
            "unsicher": "#FFC107",
            "unbekannt": "#9E9E9E"
        }

        for idx, card in enumerate(self.cards):
            self.question_listbox.insert(tk.END, card.question)
            self.answer_listbox.insert(tk.END, card.answer)

            # Status aus stats.json matchen anhand der Frage
            status = "unbekannt"
            for detail in details:
                if detail["question"] == card.question:
                    status = detail.get("result", "unbekannt")
                    break
            
            self.status_listbox.insert(tk.END, "●")
            self.status_listbox.itemconfig(idx, fg=color_map.get(status, "gray"))

    def on_select(self, event):
        selected_indices = event.widget.curselection()
        if self.selected_index in selected_indices:
            return

        if getattr(self, "_syncing_selection", False):
            return
        self._syncing_selection = True

        try:
            if not selected_indices:
                self.status_listbox.selection_clear(0, tk.END)
                self.question_listbox.selection_clear(0, tk.END)
                self.answer_listbox.selection_clear(0, tk.END)
                self.selected_index = None
                self.btn_edit.config(state="disabled")
                self.btn_delete.config(state="disabled")
                return

            selected_index = selected_indices[0]

            self.status_listbox.selection_clear(0, tk.END)
            self.question_listbox.selection_clear(0, tk.END)
            self.answer_listbox.selection_clear(0, tk.END)

            self.status_listbox.selection_set(selected_index)
            self.question_listbox.selection_set(selected_index)
            self.answer_listbox.selection_set(selected_index)

            self.status_listbox.see(selected_index)
            self.question_listbox.see(selected_index)
            self.answer_listbox.see(selected_index)

            self.selected_index = selected_index
            self.btn_edit.config(state="normal")
            self.btn_delete.config(state="normal")

        finally:
            self._syncing_selection = False

    def update_card_count(self):
        total = len(self.cards)
        learned = 0

        stats_path = os.path.join("cards", self.group, "stats.json")

        if os.path.exists(stats_path):
            try:
                with open(stats_path, "r", encoding="utf-8") as f:
                    stats = json.load(f)
                    if isinstance(stats, list) and stats:
                        last_entry = stats[-1]
                        learned = last_entry.get("richtig", 0)
            except Exception as e:
                print("Fehler beim Lesen der stats.json:", e)

        self.card_count_label.config(text=f"Karten gelernt: {learned} / {total}")

    def show_details(self):
        tk.messagebox.showinfo("Details", "Detailansicht wird noch implementiert.")

    def edit_card(self):
        if self.selected_index is None:
            return
        card = self.cards[self.selected_index]
        self.question_var.set(card.question)
        self.answer_var.set(card.answer)
        self.edit_mode = True
        self.btn_save.config(state="normal")
        self.btn_create.config(state="disabled")
        self.btn_edit.config(state="disabled")
        self.btn_delete.config(state="disabled")
        self.btn_learn.config(state="disabled")

    def save_card(self):
        if self.selected_index is None:
            return
        question = self.question_var.get().strip()
        answer = self.answer_var.get().strip()
        if not question or not answer:
            messagebox.showwarning("Fehler", "Frage und Antwort dürfen nicht leer sein.")
            return
        self.cards[self.selected_index] = Flashcard(question, answer, self.group)
        save_data(self.file_path, self.cards)
        self.edit_mode = False
        self.load_cards()
        self.clear_entries()
        self.btn_save.config(state="disabled")
        self.btn_learn.config(state="normal")
        self.selected_index = None
        self.update_card_count()

    def delete_card(self):
        if self.selected_index is not None and not self.edit_mode:
            del self.cards[self.selected_index]
            save_data(self.file_path, self.cards)
            self.load_cards()
            self.clear_entries()
            self.selected_index = None
            self.btn_edit.config(state="disabled")
            self.btn_delete.config(state="disabled")
            self.update_card_count()

    def create_card(self):
        question = self.question_var.get().strip()
        answer = self.answer_var.get().strip()
        if question and answer:
            self.cards.append(Flashcard(question, answer, self.group))
            save_data(self.file_path, self.cards)
            self.load_cards()
            self.clear_entries()
            self.selected_index = None
            self.update_card_count()

    def clear_entries(self):
        self.question_var.set("")
        self.answer_var.set("")

    def change_group(self, new_group):
        self.master.destroy()
        from ui.main_ui import start_main_app
        start_main_app(new_group)

    def start_learning_mode(self):
        learning_mode.start_learning(
            self.group,
            self.cards,
            parent_window=self.master,
        )

    def draw_pie(self):
        # Nur obersten Bereich (Diagramm) löschen – nicht den ganzen chart_frame
        for widget in self.chart_frame.grid_slaves(row=0, column=0):
            widget.destroy()

        # Neues Unterframe für das Diagramm
        diagram_frame = tk.Frame(self.chart_frame)
        diagram_frame.grid(row=0, column=0, sticky="nsew")
        diagram_frame.columnconfigure(0, weight=1)
        diagram_frame.rowconfigure(0, weight=1)

        stats = load_statistics(self.group)
        fig = draw_pie_chart(stats)

        canvas = FigureCanvasTkAgg(fig, master=diagram_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

        self.update_card_count()

    def on_click_outside(self, event):
        if self.edit_mode:
            return
        widgets_to_ignore = {
            self.question_entry, self.answer_entry,
            self.btn_create, self.btn_edit, self.btn_save,
            self.btn_delete, self.btn_learn,
            self.question_listbox, self.answer_listbox
        }
        if event.widget not in widgets_to_ignore:
            self.question_listbox.selection_clear(0, tk.END)
            self.answer_listbox.selection_clear(0, tk.END)
            self.status_listbox.selection_clear(0, tk.END)
            self.selected_index = None
            self.clear_entries()
            self.btn_edit.config(state="disabled")
            self.btn_delete.config(state="disabled")

    def fix_window_size(self):
        self.master.update_idletasks()
        width = self.master.winfo_reqwidth()
        height = self.master.winfo_reqheight()
        self.master.minsize(width, height)
        self.master.geometry(f"{width}x{height}")

def start_main_app(group):
    root = tk.Tk()
    root.title(f"Karteikarten - Gruppe: {group}")
    root.state('zoomed') 

    app = FlashcardApp(root, group) 
    root.mainloop()
