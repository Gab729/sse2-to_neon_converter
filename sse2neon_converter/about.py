import tkinter as tk

def show_about_popup(parent):
    popup = tk.Toplevel(parent)
    popup.title("À propos – Sparky Converter")
    popup.geometry("600x500")
    popup.resizable(False, False)

    # ------------------------------
    # Icône de la fenêtre About
    # ------------------------------
    try:
        popup.iconbitmap("icone.ico")  # Windows
    except Exception:
        try:
            # Linux/macOS
            logo_img = tk.PhotoImage(file="icone.png")
            popup.iconphoto(True, logo_img)
            popup._logo_img = logo_img  # garde la référence
        except Exception as e:
            print("Impossible de charger l'icône :", e)

    # Couleurs Dark Mode
    bg = "#2e2e2e"
    fg = "#ffffff"
    entry_bg = "#3d3c3c"
    popup.configure(bg=bg)

    # Zone texte
    text = tk.Text(popup, wrap="word", bg=entry_bg, fg=fg, insertbackground=fg)
    text.pack(expand=True, fill="both", padx=10, pady=10)

    about_message = """
SSE TO NEON Converter V1.0 – Eh! -2025
Auteur : Sparky729

-----------------------------------------
Licence GPLv3
-----------------------------------------
Ce programme est distribué sous licence GNU GPLv3.
Vous êtes libre de l'utiliser, modifier et redistribuer,
mais tout dérivé doit rester open-source sous GPLv3.

-----------------------------------------
Dépendances utilisées
-----------------------------------------
Ce programme utilise sse2neon (SSE → NEON)
https://github.com/jratcliff63367/sse2neon

-----------------------------------------
Adresses de donation
-----------------------------------------
VerusCoin (VRSC) : RDAP9XeGKMVavQ7cRNr9fqXvTimihya5Wn
Solana (SOL) :E7tF9jgBCbJTKHvBf6v8BW9piBJPr34kBiTrUUZHydZz
Ethereum (ETH) : 0x912b2ce60f6ce43b317f0c625aa667c81949410b
Polygon (POL) : 0x912b2ce60f6ce43b317f0c625aa667c81949410b

Merci de supporter le projet !
"""
    text.insert("1.0", about_message)
    text.config(state="disabled")
