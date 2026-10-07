# -*- coding: utf-8 -*-
"""
ui/journal_view.py
-------------------
Écran JOURNAL DES ACTIVITÉS (réservé à l'administrateur).

Affiche l'historique des actions faites dans le logiciel :
    Date/heure | Utilisateur | Action | Objet | Détails

On peut filtrer par période (date de début / date de fin).
Les données proviennent de la table `journal_activites`, alimentée
automatiquement à chaque opération importante.
"""

from datetime import datetime, date
from tkinter import ttk
import customtkinter as ctk

import database as db
from i18n import t
from ui.helpers import COULEURS, erreur, CALENDRIER_DISPO

if CALENDRIER_DISPO:
    from tkcalendar import DateEntry


class JournalView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=COULEURS["fond"])
        self._construire()
        self.afficher()

    def _construire(self):
        ctk.CTkLabel(self, text=t("journal_titre"),
                     font=ctk.CTkFont(size=26, weight="bold"),
                     text_color=COULEURS["primaire"]).pack(
                         anchor="w", padx=30, pady=(26, 4))
        ctk.CTkLabel(self, text=t("journal_intro"),
                     font=ctk.CTkFont(size=13), text_color=COULEURS["gris"],
                     justify="left").pack(anchor="w", padx=30, pady=(0, 14))

        # --- Barre de période ---
        barre = ctk.CTkFrame(self, fg_color=COULEURS["carte"], corner_radius=10)
        barre.pack(fill="x", padx=30, pady=(0, 12))
        interne = ctk.CTkFrame(barre, fg_color="transparent")
        interne.pack(fill="x", padx=14, pady=12)

        aujourdhui = date.today()
        debut_defaut = aujourdhui.replace(day=1)

        ctk.CTkLabel(interne, text=t("champ_date_debut"),
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=COULEURS["texte"]).pack(side="left", padx=(0, 6))
        self.w_debut = self._creer_champ_date(interne, debut_defaut)

        ctk.CTkLabel(interne, text=t("champ_date_fin"),
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=COULEURS["texte"]).pack(side="left", padx=(16, 6))
        self.w_fin = self._creer_champ_date(interne, aujourdhui)

        ctk.CTkButton(interne, text="🔎  " + t("btn_afficher"),
                      fg_color=COULEURS["accent"], command=self.afficher,
                      width=130).pack(side="left", padx=(20, 0))
        ctk.CTkButton(interne, text="↻  " + t("btn_actualiser"),
                      fg_color=COULEURS["gris"], hover_color="#555",
                      command=self.afficher, width=120).pack(side="right")

        # --- Tableau ---
        cadre = ctk.CTkFrame(self, fg_color=COULEURS["carte"], corner_radius=10)
        cadre.pack(fill="both", expand=True, padx=30, pady=(0, 20))

        colonnes = ("date_heure", "utilisateur", "action", "objet", "details")
        self.tableau = ttk.Treeview(cadre, columns=colonnes, show="headings",
                                    selectmode="browse")
        entetes = {
            "date_heure": t("col_date_heure"), "utilisateur": t("col_utilisateur"),
            "action": t("col_action"), "objet": t("col_objet"),
            "details": t("col_details"),
        }
        largeurs = {"date_heure": 160, "utilisateur": 180, "action": 130,
                    "objet": 130, "details": 260}
        for c in colonnes:
            self.tableau.heading(c, text=entetes[c])
            self.tableau.column(c, width=largeurs[c], anchor="w")

        scroll = ttk.Scrollbar(cadre, orient="vertical",
                               command=self.tableau.yview)
        self.tableau.configure(yscrollcommand=scroll.set)
        self.tableau.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        scroll.pack(side="right", fill="y", pady=10, padx=(0, 10))

    # ------------------------------------------------------------------ #
    def _creer_champ_date(self, parent, valeur_defaut):
        if CALENDRIER_DISPO:
            w = DateEntry(parent, date_pattern="yyyy-mm-dd", width=12,
                          background=COULEURS["primaire"], foreground="white",
                          borderwidth=1)
            try:
                w.set_date(valeur_defaut)
            except Exception:
                pass
            w.pack(side="left")
        else:
            w = ctk.CTkEntry(parent, width=120, placeholder_text="AAAA-MM-JJ")
            w.insert(0, valeur_defaut.strftime("%Y-%m-%d"))
            w.pack(side="left")
        return w

    def _lire_date(self, widget):
        if CALENDRIER_DISPO:
            try:
                return widget.get_date().strftime("%Y-%m-%d")
            except Exception:
                return None
        texte = widget.get().strip()
        try:
            return datetime.strptime(texte, "%Y-%m-%d").strftime("%Y-%m-%d")
        except ValueError:
            return None

    def afficher(self):
        d = self._lire_date(self.w_debut)
        f = self._lire_date(self.w_fin)
        if not d or not f or d > f:
            erreur("Erreur", t("msg_dates_invalides"))
            return

        for ligne in self.tableau.get_children():
            self.tableau.delete(ligne)

        for a in db.lister_activites(date_debut=d, date_fin=f):
            self.tableau.insert("", "end", values=(
                a["date_heure"] or "", a["utilisateur_nom"] or "",
                a["action"] or "", a["objet"] or "", a["details"] or ""))
