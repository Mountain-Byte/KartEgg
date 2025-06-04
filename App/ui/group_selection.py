import os
import tkinter as tk
from tkinter import simpledialog, messagebox

def get_all_groups():
    group_path = "cards"
    return [name for name in os.listdir(group_path) if os.path.isdir(os.path.join(group_path, name))]

def select_group():
    if not os.path.exists("cards"):
        os.makedirs("cards")

    groups = [name for name in os.listdir("cards") if os.path.isdir(os.path.join("cards", name))]

    def choose_group():
        selection = listbox.curselection()
        if selection:
            selected_group.set(groups[selection[0]])
            root.destroy()

    def create_new_group():
        new_group = simpledialog.askstring("Neue Gruppe", "Name der neuen Gruppe:")
        if new_group:
            path = os.path.join("cards", new_group)
            if not os.path.exists(path):
                os.makedirs(path)
                selected_group.set(new_group)
                root.destroy()
            else:
                messagebox.showerror("Fehler", "Gruppe existiert bereits.")

    root = tk.Tk()
    selected_group = tk.StringVar()
    root.title("Gruppe auswählen")

    listbox = tk.Listbox(root)
    for group in groups:
        listbox.insert(tk.END, group)
    listbox.pack(padx=10, pady=10)

    btn_frame = tk.Frame(root)
    btn_frame.pack()

    select_btn = tk.Button(btn_frame, text="Auswählen", command=choose_group)
    select_btn.grid(row=0, column=0, padx=5)

    new_btn = tk.Button(btn_frame, text="Neue Gruppe", command=create_new_group)
    new_btn.grid(row=0, column=1, padx=5)

    root.mainloop()
    return selected_group.get() if selected_group.get() else None