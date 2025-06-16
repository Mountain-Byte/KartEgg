import os
import math
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
from PIL import Image, ImageTk

# --- Hilfsfunktion: Prüft, ob ein Ordner eine Gruppe ist (anhand von cards.json) ---
def is_group_folder(path):
    return os.path.isfile(os.path.join(path, "cards.json"))

def select_group():
    """
    Öffnet ein Fenster zur Auswahl oder Verwaltung von Gruppen und Ordnern.
    Rückgabe: Relativer Pfad der ausgewählten Gruppe oder None.
    """

    # --- Initialisierung Hauptfenster ---
    if not os.path.exists("cards"):
        os.makedirs("cards")

    root = tk.Tk()
    root.title("Menü")
    root.geometry("600x500")

    selected_path = tk.StringVar()  # Speichert die Auswahl für Rückgabe

    # === ICONS LADEN ===
    icon_dir = os.path.join(os.path.dirname(__file__), "Icons")

    def load_icon(path, size):
        """Lädt und skaliert ein Icon."""
        img = Image.open(path).convert("RGBA").resize((size, size), Image.LANCZOS)
        return ImageTk.PhotoImage(img)

    # Drei Größen: klein (16), mittel (48) und groß (96)
    folder_img_small = load_icon(os.path.join(icon_dir, "Icon-Ordner.png"), 16)
    group_img_small = load_icon(os.path.join(icon_dir, "Icon-Karteikarte.png"), 16)
    folder_img_medium = load_icon(os.path.join(icon_dir, "Icon-Ordner.png"), 48)
    group_img_medium = load_icon(os.path.join(icon_dir, "Icon-Karteikarte.png"), 48)
    folder_img_large = load_icon(os.path.join(icon_dir, "Icon-Ordner.png"), 96)
    group_img_large = load_icon(os.path.join(icon_dir, "Icon-Karteikarte.png"), 96)

    # === SUCHFELD MIT PLATZHALTER ===
    placeholder_text = "🔍 Suchen..."
    search_var = tk.StringVar()
    search_entry = tk.Entry(root, fg="grey")
    search_entry.pack(fill="x", padx=10, pady=(10, 0))

    def set_placeholder(*_):
        """Zeigt den Platzhaltertext im Suchfeld an, wenn leer."""
        if not search_var.get():
            search_entry.delete(0, tk.END)
            search_entry.insert(0, placeholder_text)
            search_entry.config(fg="grey")

    def clear_placeholder(event):
        """Entfernt den Platzhalter beim Fokussieren."""
        if search_entry.get() == placeholder_text:
            search_entry.delete(0, tk.END)
            search_entry.config(fg="black")

    def restore_placeholder(event):
        """Stellt den Platzhalter wieder her, wenn das Feld leer ist."""
        if not search_entry.get():
            set_placeholder()

    search_entry.bind("<FocusIn>", clear_placeholder)
    search_entry.bind("<FocusOut>", restore_placeholder)
    set_placeholder()

    def on_entry_change(event):
        """Aktualisiert die Suche bei Texteingabe."""
        if search_entry.get() != placeholder_text:
            search_var.set(search_entry.get())
    search_entry.bind("<KeyRelease>", on_entry_change)

    # === NAVIGATION (Zurück/Vorwärts) ===
    history = []
    future = []
    current_path = ["cards"]

    nav_frame = tk.Frame(root)
    nav_frame.pack(fill="x", padx=10, pady=(10, 0))
    btn_back = tk.Button(nav_frame, text="←", state="disabled")
    btn_forward = tk.Button(nav_frame, text="→", state="disabled")
    lbl_path = tk.Label(nav_frame, text="Pfad: cards", anchor="w", fg="grey")
    btn_back.pack(side="left")
    btn_forward.pack(side="left")
    lbl_path.pack(side="left", fill="x", expand=True, padx=5)

    def update_path_label(suchmodus=False):
        """Aktualisiert die Pfadanzeige oben."""
        if suchmodus:
            lbl_path.config(text="Pfad: (Suchergebnis)")
        else:
            lbl_path.config(text="Pfad: " + os.path.relpath(current_path[0], "cards"))

    # === MENÜLEISTE ===
    menubar = tk.Menu(root)

    # Datei-Menü
    file_menu = tk.Menu(menubar, tearoff=0)
    new_menu = tk.Menu(file_menu, tearoff=0)
    new_menu.add_command(label="Neuer Ordner", command=lambda: create_folder())
    new_menu.add_command(label="Neue Gruppe", command=lambda: create_group())
    file_menu.add_cascade(label="Neu", menu=new_menu)
    file_menu.add_separator()
    file_menu.add_command(label="Beenden", command=lambda: on_close())
    menubar.add_cascade(label="Datei", menu=file_menu)

    # Bearbeiten-Menü
    edit_menu = tk.Menu(menubar, tearoff=0)
    edit_menu.add_command(label="Aktualisieren", command=lambda: refresh_tree())
    edit_menu.add_separator()
    edit_menu.add_command(label="Ebene nach oben", command=lambda: move_up())
    edit_menu.add_command(label="Umbenennen", command=lambda: rename_folder())
    edit_menu.add_command(label="Löschen", command=lambda: delete_folder())
    menubar.add_cascade(label="Bearbeiten", menu=edit_menu)

    # Ansicht-Menü
    view_menu = tk.Menu(menubar, tearoff=0)
    view_menu.add_command(label="• Liste", command=lambda: set_view("Liste"))
    view_menu.add_command(label="  Buttons", command=lambda: set_view("Buttons"))
    view_menu.add_command(label="  Symbole", command=lambda: set_view("Symbole"))
    menubar.add_cascade(label="Ansicht", menu=view_menu)

    # Hilfe-Menü
    help_menu = tk.Menu(menubar, tearoff=0)
    help_menu.add_command(label="Über", command=lambda: messagebox.showinfo("Über", "Gruppen-/Ordnerauswahl\nVersion 1.0"))
    menubar.add_cascade(label="Hilfe", menu=help_menu)

    root.config(menu=menubar)

    # === TREEVIEW (Listenansicht) ===
    tree = ttk.Treeview(root, show="tree")
    tree["columns"] = ("pfad", "typ")
    tree.column("#0", width=200)
    tree.column("pfad", width=0, stretch=False)
    tree.column("typ", width=0, stretch=False)
    tree.pack(fill="both", expand=True, padx=10, pady=10)

    def on_tree_hover(event):
        """Hebt das Element unter der Maus hervor."""
        rowid = tree.identify_row(event.y)
        for item in tree.get_children():
            tree.item(item, tags=())
        if rowid:
            tree.item(rowid, tags=("hover",))

    def on_tree_leave(event):
        """Entfernt die Hervorhebung, wenn die Maus den Treeview verlässt."""
        for item in tree.get_children():
            tree.item(item, tags=())

    tree.tag_configure("hover", background="#e0e0e0")
    tree.bind("<Motion>", on_tree_hover)
    tree.bind("<Leave>", on_tree_leave)

    # === SYMBOLANSICHT (Buttons/Symbole) mit Scrollbar ===
    canvas = tk.Canvas(root, borderwidth=0, highlightthickness=0)
    scrollbar = tk.Scrollbar(root, orient="vertical", command=canvas.yview)
    icon_frame = tk.Frame(canvas)
    icon_frame_id = canvas.create_window((0, 0), window=icon_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    def show_icon_frame():
        """Blendet die Symbolansicht ein und die Listenansicht aus."""
        tree.pack_forget()
        canvas.pack(fill="both", expand=True, side="left", padx=10, pady=10)
        scrollbar.pack(fill="y", side="right")

    def hide_icon_frame():
        """Blendet die Symbolansicht aus."""
        canvas.pack_forget()
        scrollbar.pack_forget()

    def _on_mousewheel(event):
        """Ermöglicht Scrollen mit dem Mausrad in der Symbolansicht."""
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    canvas.bind_all("<MouseWheel>", _on_mousewheel)

    def on_canvas_configure(event):
        """Passt die Breite des icon_frame an die Canvas-Breite an."""
        canvas.itemconfig(icon_frame_id, width=event.width)
    canvas.bind("<Configure>", on_canvas_configure)

    # === AUSWAHL UND NAVIGATION ===
    def update_edit_menu_state():
        """Aktualisiert die Aktivierung der Bearbeiten-Menüpunkte je nach Auswahl."""
        sel = tree.selection()
        enable_rename = enable_delete = enable_move_up = False
        if sel:
            node_type = tree.item(sel[0], "values")[1]
            enable_rename = True
            enable_delete = True
            if node_type == "group":
                enable_move_up = True
        edit_menu.entryconfig("Umbenennen", state="normal" if enable_rename else "disabled")
        edit_menu.entryconfig("Löschen", state="normal" if enable_delete else "disabled")
        edit_menu.entryconfig("Ebene nach oben", state="normal" if enable_move_up else "disabled")

    def on_select(event=None):
        """Setzt den ausgewählten Pfad und aktualisiert das Menü."""
        sel = tree.selection()
        if sel:
            node_type = tree.item(sel[0], "values")[1]
            if node_type == "group":
                selected_path.set(tree.item(sel[0], "values")[0])
            else:
                selected_path.set("")
        update_edit_menu_state()

    tree.bind("<<TreeviewSelect>>", on_select)

    # === ANSICHTEN UND SUCHE ===
    def show_folder(path, query=""):
        """
        Zeigt den Inhalt eines Ordners in der Listenansicht (Treeview).
        Optional: Filtert nach Suchbegriff.
        """
        hide_icon_frame()
        tree.pack(fill="both", expand=True, padx=10, pady=10)
        for item in tree.get_children():
            tree.delete(item)
        names = sorted(os.listdir(path))
        ordner = []
        gruppen = []
        for name in names:
            abspath = os.path.join(path, name)
            if os.path.isdir(abspath):
                if is_group_folder(abspath):
                    gruppen.append(name)
                else:
                    ordner.append(name)
        for name in ordner + gruppen:
            abspath = os.path.join(path, name)
            is_group = is_group_folder(abspath)
            icon = group_img_small if is_group else folder_img_small
            tag = "group" if is_group else "folder"
            if query and query not in name.lower():
                continue
            tree.insert(
                "", "end", text=name, image=icon,
                values=(os.path.relpath(abspath, "cards"), tag), tags=(tag,)
            )
        update_path_label(suchmodus=False)
        btn_back.config(state="normal" if history else "disabled")
        btn_forward.config(state="normal" if future else "disabled")
        update_edit_menu_state()

    def insert_search_results(parent, path, query):
        """
        Rekursive Suche nach Ordnern/Gruppen, die dem Suchbegriff entsprechen.
        Zeigt Treffer in der aktuellen Ansicht an.
        """
        names = sorted(os.listdir(path))
        ordner = []
        gruppen = []
        for name in names:
            abspath = os.path.join(path, name)
            if os.path.isdir(abspath):
                if is_group_folder(abspath):
                    gruppen.append(name)
                else:
                    ordner.append(name)
        for name in ordner + gruppen:
            abspath = os.path.join(path, name)
            if query in name.lower():
                is_group = is_group_folder(abspath)
                icon = group_img_medium if is_group else folder_img_medium
                tag = "group" if is_group else "folder"
                if view_mode.get() == "Buttons":
                    def on_click(n=name, t=tag):
                        if t == "folder":
                            history.append(current_path[0])
                            current_path[0] = os.path.join(current_path[0], n)
                            future.clear()
                            search_var.set("")
                            show_icons()
                        else:
                            selected_path.set(os.path.relpath(abspath, "cards"))
                            root.destroy()
                    btn = tk.Button(icon_frame, image=icon, text=name, compound="top", width=80, height=80, wraplength=80, command=on_click)
                    btn.pack(side="left", padx=10, pady=10)
                else:
                    tree.insert(
                        parent, "end", text=name, image=icon,
                        values=(os.path.relpath(abspath, "cards"), tag), tags=(tag,)
                    )
            insert_search_results(parent if view_mode.get() == "Liste" else None, abspath, query)

    def refresh_tree():
        """
        Aktualisiert die aktuelle Ansicht (Liste oder Symbole), ggf. mit Suchfilter.
        """
        query = search_var.get().lower()
        if query == placeholder_text.lower() or not query:
            if view_mode.get() == "Buttons":
                show_icons()
            else:
                show_folder(current_path[0])
            update_path_label(suchmodus=False)
            btn_back.config(state="normal" if history else "disabled")
            btn_forward.config(state="normal" if future else "disabled")
        else:
            for item in tree.get_children():
                tree.delete(item)
            for widget in icon_frame.winfo_children():
                widget.destroy()
            insert_search_results("" if view_mode.get() == "Liste" else None, "cards", query)
            update_path_label(suchmodus=True)
            btn_back.config(state="disabled")
            btn_forward.config(state="disabled")
            if view_mode.get() == "Buttons":
                icon_frame.pack(fill="both", expand=True, padx=10, pady=10)
                tree.pack_forget()
            else:
                tree.pack(fill="both", expand=True, padx=10, pady=10)
                icon_frame.pack_forget()
        update_edit_menu_state()

    search_var.trace_add("write", lambda *args: refresh_tree())

    # Initiale Anzeige
    show_folder(current_path[0])

    # === NAVIGATION: ZURÜCK/VORWÄRTS ===
    def go_back():
        """Geht einen Schritt im Verlauf zurück."""
        if history:
            future.append(current_path[0])
            current_path[0] = history.pop()
            if view_mode.get() in ("Buttons", "Symbole"):
                show_icons()
            else:
                show_folder(current_path[0])
            update_edit_menu_state()

    def go_forward():
        """Geht einen Schritt im Verlauf vorwärts."""
        if future:
            history.append(current_path[0])
            current_path[0] = future.pop()
            if view_mode.get() in ("Buttons", "Symbole"):
                show_icons()
            else:
                show_folder(current_path[0])
            update_edit_menu_state()
    btn_back.config(command=go_back)
    btn_forward.config(command=go_forward)

    # === KONTEXTMENÜ FÜR SYMBOLANSICHT ===
    selected_icon = {"name": None, "is_group": None}

    def show_context_menu_icons(event, name=None, is_group=None):
        """
        Zeigt das Kontextmenü für ein Symbol an.
        Aktiviert 'Ebene nach oben' nur bei Gruppen.
        """
        selected_icon["name"] = name
        selected_icon["is_group"] = is_group
        if is_group:
            context_menu.entryconfig("Ebene nach oben", state="normal")
        else:
            context_menu.entryconfig("Ebene nach oben", state="disabled")
        context_menu.tk_popup(event.x_root, event.y_root)

    # === SYMBOLANSICHT (Buttons/Symbole) ===
    def show_icons():
        """
        Zeigt den aktuellen Ordner als Symbolansicht (Buttons oder große Symbole).
        Automatische Grideinteilung, Scrollbar, Kontextmenü.
        """
        show_icon_frame()
        for widget in icon_frame.winfo_children():
            widget.destroy()

        icon_frame.update_idletasks()
        names = sorted(os.listdir(current_path[0]))
        ordner = []
        gruppen = []
        for name in names:
            abspath = os.path.join(current_path[0], name)
            if os.path.isdir(abspath):
                if is_group_folder(abspath):
                    gruppen.append(name)
                else:
                    ordner.append(name)
        # Symbolgröße und Spaltenanzahl je nach Ansicht
        if view_mode.get() == "Symbole":
            # Große Symbole
            dummy = tk.Frame(icon_frame, bd=0, highlightthickness=0)
            icon_label = tk.Label(dummy, image=group_img_large, bd=0, highlightthickness=0)
            icon_label.pack()
            text_label = tk.Label(dummy, text="Test", font=("Segoe UI", 9), wraplength=110, justify="center")
            text_label.pack()
            dummy.grid(row=0, column=0, padx=18, pady=28)
            icon_frame.update_idletasks()
            real_icon_width = dummy.winfo_width()
            dummy.destroy()
            frame_width = icon_frame.winfo_width() or icon_frame.winfo_reqwidth() or 600
            max_cols = max(1, (math.floor((frame_width) / (real_icon_width + 2*18))))
            font_size = 9
        elif view_mode.get() == "Buttons":
            # Mittelgroße Symbole
            dummy = tk.Button(icon_frame, image=group_img_medium, text="Test", compound="top", width=80, height=80, wraplength=80, font=("Segoe UI", 9), anchor="center", justify="center")
            dummy.grid(row=0, column=0, padx=10, pady=10)
            icon_frame.update_idletasks()
            real_icon_width = dummy.winfo_width()
            dummy.destroy()
            frame_width = icon_frame.winfo_width() or icon_frame.winfo_reqwidth() or 600
            max_cols = max(1, math.floor(frame_width / (real_icon_width + 2*10)))
            font_size = 9
        else:
            # Listenansicht: nur eine Spalte
            max_cols = 1
            font_size = 9
        row = col = 0
        for name in ordner + gruppen:
            abspath = os.path.join(current_path[0], name)
            is_group = is_group_folder(abspath)
            if view_mode.get() == "Symbole":
                icon = group_img_large if is_group else folder_img_large
            else:
                icon = group_img_medium if is_group else folder_img_medium
            tag = "group" if is_group else "folder"
            def on_click(n=name, t=tag):
                if t == "folder":
                    history.append(current_path[0])
                    current_path[0] = os.path.join(current_path[0], n)
                    future.clear()
                    search_var.set("")
                    show_icons()
                else:
                    selected_path.set(os.path.relpath(os.path.join(current_path[0], n), "cards"))
                    root.destroy()
            if view_mode.get() == "Symbole":
                frame = tk.Frame(icon_frame, bd=0, highlightthickness=0)
                icon_label = tk.Label(frame, image=icon, bd=0, highlightthickness=0, cursor="hand2")
                icon_label.pack()
                text_label = tk.Label(frame, text=name, font=("Segoe UI", font_size), wraplength=110, justify="center", cursor="hand2")
                text_label.pack()
                icon_label.bind("<Button-1>", lambda e, n=name, t=tag: on_click(n, t))
                text_label.bind("<Button-1>", lambda e, n=name, t=tag: on_click(n, t))
                def on_enter(e, l=icon_label):
                    l.config(bg="#e0e0e0")
                def on_leave(e, l=icon_label):
                    l.config(bg=icon_frame.cget("bg"))
                icon_label.bind("<Enter>", on_enter)
                icon_label.bind("<Leave>", on_leave)
                frame.grid(row=row, column=col, padx=18, pady=28, sticky="n")
                # Kontextmenü-Bindings:
                frame.bind("<Button-3>", lambda e, n=name, g=is_group: show_context_menu_icons(e, n, g))
                icon_label.bind("<Button-3>", lambda e, n=name, g=is_group: show_context_menu_icons(e, n, g))
                text_label.bind("<Button-3>", lambda e, n=name, g=is_group: show_context_menu_icons(e, n, g))
            else:
                btn = tk.Button(
                    icon_frame,
                    image=icon,
                    text=name,
                    compound="top",
                    width=80,
                    height=80,
                    wraplength=80,
                    font=("Segoe UI", 9),
                    command=on_click,
                    anchor="center",
                    justify="center"
                )
                btn.grid(row=row, column=col, padx=10, pady=10, sticky="n")
                def on_enter(e, b=btn):
                    b.config(bg="#e0e0e0")
                def on_leave(e, b=btn):
                    b.config(bg="SystemButtonFace")
                btn.bind("<Enter>", on_enter)
                btn.bind("<Leave>", on_leave)
                btn.bind("<Button-3>", lambda e, n=name, g=is_group: show_context_menu_icons(e, n, g))
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        # Kontextmenü auf leeren Bereich:
        icon_frame.bind("<Button-3>", lambda e: empty_menu.tk_popup(e.x_root, e.y_root))
        # --- Scrollregion aktualisieren ---
        icon_frame.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))
        update_path_label(suchmodus=False)
        btn_back.config(state="normal" if history else "disabled")
        btn_forward.config(state="normal" if future else "disabled")
        update_edit_menu_state()

    # === DOPPELKLICK IM TREEVIEW ===
    def on_double_click(event):
        """Öffnet Ordner oder wählt Gruppe per Doppelklick in der Listenansicht."""
        sel = tree.selection()
        if sel:
            node_type = tree.item(sel[0], "values")[1]
            abspath = os.path.join("cards", tree.item(sel[0], "values")[0])
            if node_type == "folder":
                search_var.set("")
                history.append(current_path[0])
                current_path[0] = abspath
                future.clear()
                if view_mode.get() == "Buttons":
                    show_icons()
                else:
                    show_folder(current_path[0])
            elif node_type == "group":
                selected_path.set(tree.item(sel[0], "values")[0])
                root.destroy()
    tree.bind("<Double-1>", on_double_click)

    # === KONTEXTMENÜS ===
    context_menu = tk.Menu(root, tearoff=0)
    context_menu.add_command(label="Umbenennen", command=lambda: rename_folder())
    context_menu.add_command(label="Löschen", command=lambda: delete_folder())
    context_menu.add_separator()
    context_menu.add_command(label="Ebene nach oben", command=lambda: move_up())
    context_menu.add_separator()
    context_menu.add_command(label="Neue Gruppe", command=lambda: create_group())
    context_menu.add_command(label="Neuer Ordner", command=lambda: create_folder())

    empty_menu = tk.Menu(root, tearoff=0)
    empty_menu.add_command(label="Neue Gruppe", command=lambda: create_group())
    empty_menu.add_command(label="Neuer Ordner", command=lambda: create_folder())

    def show_context_menu(event):
        """Zeigt das Kontextmenü im Treeview an."""
        sel = tree.identify_row(event.y)
        if sel:
            tree.selection_set(sel)
            context_menu.tk_popup(event.x_root, event.y_root)
        else:
            empty_menu.tk_popup(event.x_root, event.y_root)
    tree.bind("<Button-3>", show_context_menu)

    # === DATEI- UND GRUPPENOPERATIONEN ===
    def create_folder():
        """Erstellt einen neuen Ordner im aktuellen Pfad."""
        parent_path = current_path[0]
        new_name = simpledialog.askstring("Neuer Ordner", "Name des neuen Ordners:")
        if new_name:
            new_path = os.path.join(parent_path, new_name)
            if not os.path.exists(new_path):
                os.makedirs(new_path)
                if view_mode.get() in ("Buttons", "Symbole"):
                    show_icons()
                else:
                    refresh_tree()
            else:
                messagebox.showerror("Fehler", "Ordner existiert bereits.")

    def create_group():
        """Erstellt eine neue Gruppe (Ordner mit cards.json) im aktuellen Pfad."""
        parent_path = current_path[0]
        new_name = simpledialog.askstring("Neue Gruppe", "Name der neuen Gruppe:")
        if new_name:
            new_path = os.path.join(parent_path, new_name)
            if not os.path.exists(new_path):
                os.makedirs(new_path)
                with open(os.path.join(new_path, "cards.json"), "w", encoding="utf-8") as f:
                    f.write("[]")
                if view_mode.get() in ("Buttons", "Symbole"):
                    show_icons()
                else:
                    refresh_tree()
            else:
                messagebox.showerror("Fehler", "Gruppe/Ordner existiert bereits.")

    def rename_folder():
        """Benennt einen Ordner oder eine Gruppe um (je nach Ansicht)."""
        # Symbolansicht: Rechtsklick-Auswahl verwenden
        if view_mode.get() in ("Buttons", "Symbole") and selected_icon["name"]:
            old_path = os.path.join(current_path[0], selected_icon["name"])
            new_name = simpledialog.askstring("Umbenennen", "Neuer Name:", initialvalue=os.path.basename(old_path))
            if new_name:
                new_path = os.path.join(os.path.dirname(old_path), new_name)
                if not os.path.exists(new_path):
                    os.rename(old_path, new_path)
                    show_icons()
                else:
                    messagebox.showerror("Fehler", "Name existiert bereits.")
        else:
            # Treeview-Standardverhalten
            sel = tree.selection()
            if not sel:
                return
            old_path = os.path.join("cards", tree.item(sel[0], "values")[0])
            new_name = simpledialog.askstring("Umbenennen", "Neuer Name:", initialvalue=os.path.basename(old_path))
            if new_name:
                new_path = os.path.join(os.path.dirname(old_path), new_name)
                if not os.path.exists(new_path):
                    os.rename(old_path, new_path)
                    refresh_tree()
                else:
                    messagebox.showerror("Fehler", "Name existiert bereits.")

    def delete_folder():
        """Löscht einen Ordner oder eine Gruppe (je nach Ansicht)."""
        # Symbolansicht: Rechtsklick-Auswahl verwenden
        if view_mode.get() in ("Buttons", "Symbole") and selected_icon["name"]:
            path = os.path.join(current_path[0], selected_icon["name"])
            if messagebox.askyesno("Löschen", f"Ordner/Gruppe '{os.path.basename(path)}' wirklich löschen?"):
                import shutil
                shutil.rmtree(path)
                show_icons()
        else:
            # Treeview-Standardverhalten
            sel = tree.selection()
            if not sel:
                return
            path = os.path.join("cards", tree.item(sel[0], "values")[0])
            if messagebox.askyesno("Löschen", f"Ordner/Gruppe '{os.path.basename(path)}' wirklich löschen?"):
                import shutil
                shutil.rmtree(path)
                refresh_tree()

    def move_up():
        """Verschiebt einen Ordner/eine Gruppe eine Ebene nach oben."""
        # Symbolansicht: Rechtsklick-Auswahl verwenden
        if view_mode.get() in ("Buttons", "Symbole") and selected_icon["name"]:
            rel_path = os.path.relpath(os.path.join(current_path[0], selected_icon["name"]), "cards")
            abs_path = os.path.join("cards", rel_path)
            parent_dir = os.path.dirname(abs_path)
            grandparent_dir = os.path.dirname(parent_dir)
            if os.path.abspath(parent_dir) == os.path.abspath("cards"):
                messagebox.showinfo("Hinweis", "Element ist bereits auf oberster Ebene.")
                return
            dst_path = os.path.join(grandparent_dir, os.path.basename(abs_path))
            if os.path.exists(dst_path):
                messagebox.showerror("Fehler", "Im Ziel existiert bereits ein Ordner/Gruppe mit diesem Namen.")
                return
            try:
                os.rename(abs_path, dst_path)
                show_icons()
            except Exception as e:
                messagebox.showerror("Fehler", f"Verschieben fehlgeschlagen: {e}")
        else:
            # Treeview-Standardverhalten
            sel = tree.selection()
            if not sel:
                return
            rel_path = tree.item(sel[0], "values")[0]
            abs_path = os.path.join("cards", rel_path)
            parent_dir = os.path.dirname(abs_path)
            grandparent_dir = os.path.dirname(parent_dir)
            if os.path.abspath(parent_dir) == os.path.abspath("cards"):
                messagebox.showinfo("Hinweis", "Element ist bereits auf oberster Ebene.")
                return
            dst_path = os.path.join(grandparent_dir, os.path.basename(abs_path))
            if os.path.exists(dst_path):
                messagebox.showerror("Fehler", "Im Ziel existiert bereits ein Ordner/Gruppe mit diesem Namen.")
                return
            try:
                os.rename(abs_path, dst_path)
                refresh_tree()
            except Exception as e:
                messagebox.showerror("Fehler", f"Verschieben fehlgeschlagen: {e}")

    # === DRAG & DROP IM TREEVIEW ===
    drag_data = {"item": None}

    def on_treeview_button_press(event):
        """Startet Drag & Drop im Treeview."""
        item = tree.identify_row(event.y)
        if item:
            drag_data["item"] = item

    def on_treeview_button_release(event):
        """Beendet Drag & Drop im Treeview und verschiebt ggf. das Element."""
        if not drag_data["item"]:
            return
        target_item = tree.identify_row(event.y)
        if not target_item or target_item == drag_data["item"]:
            drag_data["item"] = None
            return

        src_path = os.path.join("cards", tree.item(drag_data["item"], "values")[0])
        target_type = tree.item(target_item, "values")[1]
        if target_type != "folder":
            drag_data["item"] = None
            return

        dst_path = os.path.join("cards", tree.item(target_item, "values")[0], os.path.basename(src_path))
        if os.path.exists(dst_path):
            messagebox.showerror("Fehler", "Im Ziel existiert bereits ein Ordner/Gruppe mit diesem Namen.")
            drag_data["item"] = None
            return

        try:
            os.rename(src_path, dst_path)
            refresh_tree()
        except Exception as e:
            messagebox.showerror("Fehler", f"Verschieben fehlgeschlagen: {e}")

        drag_data["item"] = None

    tree.bind("<ButtonPress-1>", on_treeview_button_press)
    tree.bind("<ButtonRelease-1>", on_treeview_button_release)

    # === FENSTER-SCHLIESSEN ===
    def on_close():
        """Beendet das Fenster ohne Auswahl."""
        selected_path.set("")
        root.destroy()
    root.protocol("WM_DELETE_WINDOW", on_close)

    # === ANSICHT WECHSELN (Liste, Buttons, Symbole) ===
    view_mode = tk.StringVar(value="Liste")

    def update_view_menu():
        """Aktualisiert die Markierung im Ansicht-Menü."""
        view_menu.entryconfig(0, label=("• Liste" if view_mode.get() == "Liste" else "  Liste"))
        view_menu.entryconfig(1, label=("• Buttons" if view_mode.get() == "Buttons" else "  Buttons"))
        view_menu.entryconfig(2, label=("• Symbole" if view_mode.get() == "Symbole" else "  Symbole"))

    def set_view(mode):
        """Wechselt zwischen Listen- und Symbolansicht."""
        view_mode.set(mode)
        if mode in ("Buttons", "Symbole"):
            tree.pack_forget()
            show_icons()
        else:
            hide_icon_frame()
            tree.pack(fill="both", expand=True, padx=10, pady=10)
            show_folder(current_path[0])
        update_view_menu()
        update_edit_menu_state()

    # === FENSTERGRÖSSE-ÄNDERUNG: Automatische Spaltenanzahl ===
    resize_after_id = [None]  # Timeout-Handle für verzögertes Redraw
    last_size = [None]
    is_resizing = [False]
    last_cols = [None]

    def on_window_resize(event):
        """Passt die Spaltenanzahl in der Symbolansicht an die Fenstergröße an."""
        if is_resizing[0]:
            return
        size = (event.width, event.height)
        if last_size[0] == size:
            return
        last_size[0] = size

        # Berechne die aktuelle Spaltenanzahl wie in show_icons()
        if view_mode.get() == "Symbole":
            icon_size = 96
            padx = 24
            icon_width = icon_size + 2 * padx
            frame_width = (icon_frame.winfo_width() or icon_frame.winfo_reqwidth() or 600) - 32
            cols = max(1, (math.floor(frame_width / icon_width)))
        elif view_mode.get() == "Buttons":
            btn_size = 80
            padx = 10
            icon_width = btn_size + 2 * padx
            frame_width = (icon_frame.winfo_width() or icon_frame.winfo_reqwidth() or 600) - 10
            cols = max(1, math.floor(frame_width / icon_width))
        else:
            cols = None

        if last_cols[0] == cols:
            return  # Nur neu zeichnen, wenn sich die Spaltenanzahl ändert!
        last_cols[0] = cols

        is_resizing[0] = True
        if resize_after_id[0]:
            root.after_cancel(resize_after_id[0])
        def do_update():
            if view_mode.get() in ("Buttons", "Symbole"):
                show_icons()
            is_resizing[0] = False
        resize_after_id[0] = root.after(200, do_update)

    root.bind("<Configure>", on_window_resize)

    # === HAUPTSCHLEIFE ===
    root.mainloop()
    return selected_path.get() if selected_path.get() else None