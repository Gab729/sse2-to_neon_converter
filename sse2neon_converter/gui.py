#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
import threading
import os
import shutil
import re
import platform
import subprocess
import textwrap

# -----------------------------
# CONFIGURATION SSE → NEON
# -----------------------------

SSE_TO_NEON = {
    "_mm_unpacklo_epi64": "vzip1q_s64",
    "_mm_unpackhi_epi64": "vzip2q_s64",
    "_mm_blend_epi16": "vbitselectq_s16",
    "_mm_shuffle_epi32": "vextq_s32",
    "_mm_alignr_epi8": "vextq_u8",
}

NEON_HEADER = 'sse2neon.h'
FILE_EXTENSIONS = ('.c', '.cpp', '.h')

# -----------------------------
# FONCTIONS DE CONVERSION
# -----------------------------

def add_include_if_missing(content):
    include_line = f'#include "{NEON_HEADER}"'
    if include_line not in content:
        lines = content.splitlines()
        insertion_index = 0
        for i, line in enumerate(lines):
            if line.strip().startswith("#include"):
                insertion_index = i + 1
        lines.insert(insertion_index, include_line)
        return "\n".join(lines), True
    return content, False

def replace_sse_with_neon(content, file_path):
    replacements = []
    lines = content.splitlines()
    for i, line in enumerate(lines):
        original_line = line
        for sse_instr, neon_instr in SSE_TO_NEON.items():
            pattern = r'\b' + re.escape(sse_instr) + r'\b'
            if re.search(pattern, line):
                line = re.sub(pattern, neon_instr, line)
                replacements.append({
                    'file': file_path,
                    'line_number': i + 1,
                    'original': original_line.strip(),
                    'replaced': line.strip()
                })
        lines[i] = line
    return "\n".join(lines), replacements

def process_file(file_path, output_dir, base_src_dir):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    content, included = add_include_if_missing(content)
    content, replacements = replace_sse_with_neon(content, file_path)

    rel_path = os.path.relpath(file_path, base_src_dir)
    output_path = os.path.join(output_dir, rel_path)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

    return replacements, included

def process_directory(input_dir, output_dir):
    all_replacements = []
    all_includes = []
    for root, dirs, files in os.walk(input_dir):
        for file in files:
            if file.endswith(FILE_EXTENSIONS):
                file_path = os.path.join(root, file)
                replacements, included = process_file(file_path, output_dir, input_dir)
                all_replacements.extend(replacements)
                if included:
                    all_includes.append(file_path)
    return all_replacements, all_includes

# -----------------------------
# ABOUT POPUP
# -----------------------------

def show_about_popup(parent, bg_color="#f0f0f0", panel_color="#ffffff", text_color="#000000"):
    """Affiche la fenêtre About avec les couleurs dynamiques du thème."""
    about_text = textwrap.dedent("""
    SSE2 → NEON Converter
    ---------------------
    Licence: GNU GPLv3

    Ce logiciel inclut / utilise :
    - sse2neon.h (portage SSE → NEON)
      Source: https://github.com/jratcliff63367/sse2neon
      Merci à l'auteur original pour la compatibilité ARM.

    Crédits:
    - Adaptation / GUI: Sparky729

    Dons (optionnel):
    - Verus:  R_example_verus_address
    - Doge:   D_example_doge_address
    - ETH:    0xExampleEthAddress

    NOTE: Ce logiciel est fourni "tel quel". Voir la licence GNU GPLv3 complète pour les conditions.
    """).strip()

    win = tk.Toplevel(parent)
    win.title("About")
    win.resizable(False, False)
    win.geometry("560x360")
    win.configure(bg=bg_color)

    txt = scrolledtext.ScrolledText(win, wrap=tk.WORD, width=68, height=18,
                                    bg=panel_color, fg=text_color, insertbackground=text_color)
    txt.insert(tk.END, about_text)
    txt.configure(state="disabled")
    txt.pack(padx=10, pady=(10,0), fill="both", expand=True)

    btn_frame = tk.Frame(win, bg=bg_color)
    btn_frame.pack(fill="x", padx=10, pady=8)

    def copy_addresses():
        parent.clipboard_clear()
        parent.clipboard_append("Verus: R_example_verus_address\nDoge: D_example_doge_address\nETH: 0xExampleEthAddress")
        messagebox.showinfo("Copied", "Addresses copied to clipboard.")

    tk.Button(btn_frame, text="Copy donation addresses", command=copy_addresses).pack(side="left")
    tk.Button(btn_frame, text="Close", command=win.destroy).pack(side="right")

# -----------------------------
# INTERFACE TKINTER + DARK MODE
# -----------------------------

class SSE2NEONApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SSE2 → NEON Converter")



        # ------------------------------
        # Icône de la fenêtre
        # ------------------------------
        self.icon_img = None  # Toujours définir pour garder référence

        # Windows : .ico
        try:
            self.root.iconbitmap("icone.ico")
        except:
            # Linux/macOS : .png
            try:
                self.icon_img = tk.PhotoImage(file="icone.png")
                self.root.iconphoto(True, self.icon_img)
            except Exception as e:
                print("Impossible de charger l'icône:", e)

        self.colors = {
            "light": {"bg":"#eef0f2","panel":"#ffffff","text":"#111111","button":"#e6e6e6","muted":"#6b7176"},
            "dark":  {"bg":"#2f3335","panel":"#3b3b3b","text":"#e7e7e7","button":"#383838","muted":"#a9afb3"}
        }
        self.theme = "light"
        self.result_folder = None

        # Layout
        self.root.columnconfigure(0, weight=0)
        self.root.columnconfigure(1, weight=1)
        self.root.columnconfigure(2, weight=0)
        self.root.rowconfigure(2, weight=1)

        # Source entry
        tk.Label(root, text="Source folder:").grid(row=0,column=0, sticky="w", padx=(10,6), pady=(12,6))
        self.src_entry = tk.Entry(root)
        self.src_entry.grid(row=0,column=1, sticky="ew", padx=(0,6), pady=(12,6))
        tk.Button(root, text="Browse", command=self.browse_src).grid(row=0,column=2, sticky="e", padx=(0,10), pady=(12,6))

        # Buttons row
        btn_frame = tk.Frame(root)
        btn_frame.grid(row=1,column=0,columnspan=3, sticky="ew", padx=10)
        btn_frame.columnconfigure(0, weight=1)
        for i in range(1,5): btn_frame.columnconfigure(i, weight=0)

        # Dark mode button
        self.dark_button = tk.Button(btn_frame, text="🌙 Dark Mode", command=self.toggle_dark_mode)
        self.dark_button.grid(row=0,column=0, sticky="w")

        # Start / Open / About buttons
        self.start_button = tk.Button(btn_frame, text="Start Conversion", command=self.start_conversion, width=18)
        self.start_button.grid(row=0,column=1, padx=(6,4))

        self.open_button = tk.Button(btn_frame, text="Open Result Folder", command=self.open_result_folder, state=tk.DISABLED, width=18)
        self.open_button.grid(row=0,column=2, padx=(4,6))

        self.about_btn = tk.Button(
            btn_frame,
            text="About",
            width=12,
            command=lambda: show_about_popup(
                self.root,
                bg_color=self.colors[self.theme]["bg"],
                panel_color=self.colors[self.theme]["panel"],
                text_color=self.colors[self.theme]["text"]
            )
        )
        self.about_btn.grid(row=0,column=3, padx=(6,0))

        # Log area
        self.log_area = scrolledtext.ScrolledText(root, wrap=tk.WORD)
        self.log_area.grid(row=2,column=0,columnspan=3, sticky="nsew", padx=10, pady=(8,10))

        # Appliquer thème initial
        self.apply_theme()

    # -----------------------------
    # Theme / Dark Mode
    # -----------------------------
    def apply_theme(self):
        t = self.colors[self.theme]
        self.root.configure(bg=t["bg"])
        for w in self.root.winfo_children():
            if isinstance(w, tk.Frame):
                w.configure(bg=t["bg"])
                for sub in w.winfo_children():
                    if isinstance(sub, tk.Button):
                        sub.configure(bg=t["button"], fg=t["text"], activebackground=t["panel"], relief=tk.RAISED)
                    elif isinstance(sub, tk.Entry):
                        sub.configure(bg=t["panel"], fg=t["text"], insertbackground=t["text"])
                    elif isinstance(sub, tk.Label):
                        sub.configure(bg=t["bg"], fg=t["text"])
            else:
                if isinstance(w, tk.Label):
                    w.configure(bg=t["bg"], fg=t["text"])
                elif isinstance(w, tk.Entry):
                    w.configure(bg=t["panel"], fg=t["text"], insertbackground=t["text"])
                elif isinstance(w, tk.Button):
                    w.configure(bg=t["button"], fg=t["text"], activebackground=t["panel"], relief=tk.RAISED)
                elif isinstance(w, scrolledtext.ScrolledText):
                    w.configure(bg=t["panel"], fg=t["text"], insertbackground=t["text"],
                                highlightbackground=t["bg"], highlightcolor=t["text"])
        self.dark_button.configure(text="☀ Light Mode" if self.theme=="dark" else "🌙 Dark Mode")

    def toggle_dark_mode(self):
        self.theme = "dark" if self.theme=="light" else "light"
        self.apply_theme()
        self.log(f"{'Dark' if self.theme=='dark' else 'Light'} mode enabled.")

    # -----------------------------
    # LOGIQUE UI
    # -----------------------------
    def browse_src(self):
        folder = filedialog.askdirectory()
        if folder:
            self.src_entry.delete(0, tk.END)
            self.src_entry.insert(0, folder)

    def log(self, text):
        self.log_area.insert(tk.END, text+"\n")
        self.log_area.see(tk.END)
        self.root.update_idletasks()

    def start_conversion(self):
        src = self.src_entry.get()
        if not src:
            messagebox.showerror("Error", "Please select a source folder")
            return
        threading.Thread(target=self.run_conversion, args=(src,), daemon=True).start()

    def run_conversion(self, src):
        self.result_folder = os.path.join(src, "result")
        self.open_button.config(state=tk.DISABLED)
        self.log(f"Starting conversion from {src} to {self.result_folder}...")

        if os.path.exists(self.result_folder):
            shutil.rmtree(self.result_folder)
        os.makedirs(self.result_folder)

        replacements, includes_added = process_directory(src, self.result_folder)

        if includes_added:
            self.log("\n=== INCLUSIONS AJOUTÉES ===")
            for f in includes_added:
                self.log(f"[INCLUDE] {f}")

        if replacements:
            self.log("\n=== REMPLACEMENTS EFFECTUÉS ===")
            for r in replacements:
                self.log(f"{r['file']} (line {r['line_number']}): {r['original']} -> {r['replaced']}")

        self.log(f"\nConversion finished! {len(replacements)} instructions replaced in {len(set([r['file'] for r in replacements]))} files.")
        self.log(f"\nYou can access the converted files here: {self.result_folder}")
        self.open_button.config(state=tk.NORMAL)

    def open_result_folder(self):
        if self.result_folder and os.path.exists(self.result_folder):
            system = platform.system()
            if system=="Windows":
                os.startfile(self.result_folder)
            elif system=="Darwin":
                subprocess.run(["open", self.result_folder])
            else:
                subprocess.run(["xdg-open", self.result_folder])
        else:
            messagebox.showerror("Error", "Result folder not found!")

# -----------------------------
# ENTRY POINT
# -----------------------------
if __name__=="__main__":
    root = tk.Tk()
    app = SSE2NEONApp(root)
    root.mainloop()
