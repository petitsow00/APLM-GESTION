# -*- coding: utf-8 -*-
"""
ui/helpers.py
--------------
Outils réutilisables pour l'interface :
  - COULEURS : la charte graphique
  - styler_treeview() : rend les tableaux plus jolis
  - FormulaireDialog : une fenêtre de formulaire générique (ajout/modif)
  - confirmer() / info() / erreur() : petites boîtes de message
"""

import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk

try:
    from tkcalendar import DateEntry
    CALENDRIER_DISPO = True
except Exception:
    CALENDRIER_DISPO = False


# --- Charte graphique -------------------------------------------------------
COULEURS = {
    "primaire":   "#123456",   # bleu foncé
    "primaire2":  "#1f4e79",
    "accent":     "#2e86de",
    "fond":       "#f4f6f9",
    "carte":      "#ffffff",
    "texte":      "#1a1a1a",
    "gris":       "#6e6e6e",
    "vert":       "#1e8449",
    "rouge":      "#c0392b",
}


def styler_treeview():
    """Applique un style clair et lisible aux tableaux ttk.Treeview."""
    style = ttk.Style()
    try:
        style.theme_use("clam")
    except Exception:
        pass
    style.configure("Treeview",
                    background="white",
                    foreground=COULEURS["texte"],
                    rowheight=30,
                    fieldbackground="white",
                    font=("Segoe UI", 10),
                    borderwidth=0)
    style.configure("Treeview.Heading",
                    background=COULEURS["primaire"],
                    foreground="white",
                    font=("Segoe UI", 10, "bold"),
                    relief="flat")
    style.map("Treeview.Heading",
              background=[("active", COULEURS["primaire2"])])
    style.map("Treeview",
              background=[("selected", COULEURS["accent"])],
              foreground=[("selected", "white")])


# --- Petites boîtes de dialogue --------------------------------------------
def confirmer(titre, message):
    return messagebox.askyesno(titre, message)


def info(titre, message):
    messagebox.showinfo(titre, message)


def erreur(titre, message):
    messagebox.showerror(titre, message)


# --- Formulaire générique ---------------------------------------------------
class FormulaireDialog(ctk.CTkToplevel):
    """Fenêtre modale d'ajout/modification.

    champs : liste de dictionnaires, ex :
        {"cle": "nom", "label": "Nom", "type": "texte"}
        {"cle": "notes", "label": "Notes", "type": "zone"}
        {"cle": "statut", "label": "Statut", "type": "liste", "options": [...]}
        {"cle": "prix", "label": "Prix", "type": "nombre"}
        {"cle": "date_depart", "label": "Date", "type": "date"}
    valeurs : dictionnaire des valeurs existantes (pour la modification)

    Après fermeture, self.resultat vaut :
        - un dictionnaire {cle: valeur} si l'utilisateur a validé
        - None s'il a annulé
    """

    def __init__(self, parent, titre, champs, valeurs=None, largeur=520):
        super().__init__(parent)
        self.title(titre)
        self.resultat = None
        self._champs = champs
        self._widgets = {}
        valeurs = valeurs or {}

        self.configure(fg_color=COULEURS["fond"])
        self.resizable(False, False)

        # En-tête
        entete = ctk.CTkLabel(self, text=titre,
                              font=ctk.CTkFont(size=18, weight="bold"),
                              text_color=COULEURS["primaire"])
        entete.pack(padx=20, pady=(18, 10), anchor="w")

        # Zone défilante pour les champs
        zone = ctk.CTkScrollableFrame(self, fg_color=COULEURS["carte"],
                                      width=largeur, height=min(60 + 62 * len(champs), 520))
        zone.pack(padx=20, pady=5, fill="both", expand=True)

        for champ in champs:
            cle = champ["cle"]
            label = champ.get("label", cle)
            typ = champ.get("type", "texte")

            ctk.CTkLabel(zone, text=label,
                         font=ctk.CTkFont(size=12, weight="bold"),
                         text_color=COULEURS["texte"], anchor="w").pack(
                             fill="x", padx=10, pady=(8, 0))

            valeur = valeurs.get(cle, "")

            if typ == "zone":
                w = ctk.CTkTextbox(zone, height=70)
                if valeur:
                    w.insert("1.0", str(valeur))
                w.pack(fill="x", padx=10, pady=(2, 4))

            elif typ == "liste":
                options = champ.get("options", [])
                var = ctk.StringVar(value=str(valeur) if valeur else (options[0] if options else ""))
                w = ctk.CTkOptionMenu(zone, values=options, variable=var,
                                      fg_color=COULEURS["primaire"],
                                      button_color=COULEURS["primaire2"])
                w.pack(fill="x", padx=10, pady=(2, 4))
                w._var = var

            elif typ == "date" and CALENDRIER_DISPO:
                w = DateEntry(zone, date_pattern="yyyy-mm-dd", width=18,
                              background=COULEURS["primaire"], foreground="white",
                              borderwidth=1)
                if valeur:
                    try:
                        w.set_date(str(valeur))
                    except Exception:
                        pass
                else:
                    w.delete(0, "end")   # laisser vide par défaut
                w.pack(anchor="w", padx=10, pady=(2, 4))

            else:  # "texte" ou "nombre"
                w = ctk.CTkEntry(zone, placeholder_text=champ.get("aide", ""))
                if valeur not in ("", None):
                    w.insert(0, str(valeur))
                w.pack(fill="x", padx=10, pady=(2, 4))

            self._widgets[cle] = (w, typ)

        # Boutons
        barre = ctk.CTkFrame(self, fg_color="transparent")
        barre.pack(fill="x", padx=20, pady=(6, 16))
        ctk.CTkButton(barre, text="Annuler", fg_color=COULEURS["gris"],
                      hover_color="#555", command=self._annuler,
                      width=110).pack(side="right", padx=(8, 0))
        ctk.CTkButton(barre, text="Enregistrer", fg_color=COULEURS["vert"],
                      hover_color="#166638", command=self._valider,
                      width=140).pack(side="right")

        # Rendre la fenêtre modale (bloque la fenêtre principale)
        self.update_idletasks()
        self._centrer(parent)
        self.transient(parent)
        self.grab_set()
        self.wait_window(self)

    def _centrer(self, parent):
        try:
            px, py = parent.winfo_rootx(), parent.winfo_rooty()
            pw, ph = parent.winfo_width(), parent.winfo_height()
            w, h = self.winfo_width(), self.winfo_height()
            x = px + (pw - w) // 2
            y = py + (ph - h) // 2
            self.geometry(f"+{max(x,0)}+{max(y,0)}")
        except Exception:
            pass

    def _lire_valeur(self, w, typ):
        if typ == "zone":
            return w.get("1.0", "end").strip()
        if typ == "liste":
            return w._var.get()
        if typ == "date" and CALENDRIER_DISPO:
            try:
                return w.get()
            except Exception:
                return ""
        return w.get().strip()

    def _valider(self):
        resultat = {}
        for cle, (w, typ) in self._widgets.items():
            valeur = self._lire_valeur(w, typ)
            if typ == "nombre":
                if valeur == "":
                    valeur = 0
                else:
                    try:
                        valeur = float(str(valeur).replace(" ", "").replace(",", "."))
                    except ValueError:
                        erreur("Erreur", f"« {valeur} » n'est pas un nombre valide.")
                        return
            resultat[cle] = valeur
        self.resultat = resultat
        self.grab_release()
        self.destroy()

    def _annuler(self):
        self.resultat = None
        self.grab_release()
        self.destroy()
