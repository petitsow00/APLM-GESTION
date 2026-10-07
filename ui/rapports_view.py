# -*- coding: utf-8 -*-
"""
ui/rapports_view.py
-------------------
Module 📊 RAPPORTS : chiffres d'une période (jour / semaine / mois /
personnalisé), filtrables par activité. Fonctionne à partir des vraies
données, indépendamment de l'écran comptable.
"""

from datetime import datetime, timedelta
import customtkinter as ctk

import config
import rapports as rap
import activites as act
from ui.helpers import COULEURS, erreur
from ui.operation_dialog import formater

try:
    from tkcalendar import DateEntry
    CAL = True
except Exception:
    CAL = False


class RapportsView(ctk.CTkFrame):
    def __init__(self, parent, on_changement=None):
        super().__init__(parent, fg_color=COULEURS["fond"])
        self._construire()
        self.generer_mois()

    def _construire(self):
        ctk.CTkLabel(self, text="📊  Rapports",
                     font=ctk.CTkFont(size=26, weight="bold"),
                     text_color=COULEURS["primaire"]).pack(
                         anchor="w", padx=30, pady=(26, 8))

        barre = ctk.CTkFrame(self, fg_color=COULEURS["carte"], corner_radius=10)
        barre.pack(fill="x", padx=30, pady=(0, 10))

        ctk.CTkButton(barre, text="Aujourd'hui", width=100, fg_color=COULEURS["primaire2"],
                      command=self.generer_jour).pack(side="left", padx=(12, 4), pady=10)
        ctk.CTkButton(barre, text="Cette semaine", width=110, fg_color=COULEURS["primaire2"],
                      command=self.generer_semaine).pack(side="left", padx=4, pady=10)
        ctk.CTkButton(barre, text="Ce mois", width=90, fg_color=COULEURS["primaire2"],
                      command=self.generer_mois).pack(side="left", padx=4, pady=10)

        ctk.CTkLabel(barre, text="Du").pack(side="left", padx=(14, 2))
        if CAL:
            self.d1 = DateEntry(barre, date_pattern="yyyy-mm-dd", width=12)
            self.d2 = DateEntry(barre, date_pattern="yyyy-mm-dd", width=12)
        else:
            self.d1 = ctk.CTkEntry(barre, width=110, placeholder_text="AAAA-MM-JJ")
            self.d2 = ctk.CTkEntry(barre, width=110, placeholder_text="AAAA-MM-JJ")
        self.d1.pack(side="left", padx=2)
        ctk.CTkLabel(barre, text="au").pack(side="left", padx=2)
        self.d2.pack(side="left", padx=2)

        self.act_var = ctk.StringVar(value="Toutes")
        ctk.CTkOptionMenu(barre, values=["Toutes", "Billets", "Hôtels",
                                         "Assurances", "Visa"],
                          variable=self.act_var, width=120,
                          fg_color=COULEURS["primaire"],
                          button_color=COULEURS["primaire2"]).pack(side="left", padx=(12, 4))
        ctk.CTkButton(barre, text="Générer", fg_color=COULEURS["vert"],
                      hover_color="#166638", width=100,
                      command=self.generer_perso).pack(side="left", padx=6)

        self.titre_periode = ctk.CTkLabel(self, text="",
                                          font=ctk.CTkFont(size=15, weight="bold"),
                                          text_color=COULEURS["primaire"])
        self.titre_periode.pack(anchor="w", padx=32, pady=(4, 4))

        self.zone = ctk.CTkScrollableFrame(self, fg_color=COULEURS["fond"])
        self.zone.pack(fill="both", expand=True, padx=24, pady=(0, 20))

    # ---------------------------------------------------------------- #
    def _activite_filtre(self):
        m = {"Billets": "billet", "Hôtels": "hotel", "Assurances": "assurance",
             "Visa": "visa"}
        return m.get(self.act_var.get())

    def _set_dates(self, d1, d2):
        for w, v in ((self.d1, d1), (self.d2, d2)):
            if CAL:
                try:
                    w.set_date(v)
                except Exception:
                    pass
            else:
                w.delete(0, "end"); w.insert(0, v)

    def generer_jour(self):
        t = datetime.now().strftime("%Y-%m-%d")
        self._set_dates(t, t)
        self._afficher(t, t, "Aujourd'hui — " + t)

    def generer_semaine(self):
        now = datetime.now()
        lundi = (now - timedelta(days=now.weekday())).strftime("%Y-%m-%d")
        t = now.strftime("%Y-%m-%d")
        self._set_dates(lundi, t)
        self._afficher(lundi, t, f"Cette semaine ({lundi} au {t})")

    def generer_mois(self):
        now = datetime.now()
        prem = now.strftime("%Y-%m-01")
        t = now.strftime("%Y-%m-%d")
        self._set_dates(prem, t)
        self._afficher(prem, t, f"Ce mois ({prem} au {t})")

    def generer_perso(self):
        d1 = self.d1.get().strip()
        d2 = self.d2.get().strip()
        if not d1 or not d2:
            erreur("Dates", "Veuillez saisir les deux dates.")
            return
        self._afficher(d1, d2, f"Du {d1} au {d2}")

    # ---------------------------------------------------------------- #
    def _afficher(self, d1, d2, titre):
        self.titre_periode.configure(
            text=titre + (f"  ·  {self.act_var.get()}"
                          if self.act_var.get() != "Toutes" else ""))
        r = rap.rapport(d1, d2, activite=self._activite_filtre())
        for w in self.zone.winfo_children():
            w.destroy()

        cartes = [
            ("Billets", r["nb_billets"], COULEURS["accent"], False),
            ("Hôtels", r["nb_hotels"], COULEURS["accent"], False),
            ("Assurances", r["nb_assurances"], COULEURS["accent"], False),
            ("Visa", r["nb_visas"], COULEURS["accent"], False),
            ("Chiffre d'affaires", r["chiffre_affaires"], COULEURS["primaire"], True),
            ("Encaissements", r["encaissements"], COULEURS["vert"], True),
            ("Créances (reste à payer)", r["creances"], COULEURS["rouge"], True),
            ("Coûts fournisseurs", r["couts_fournisseurs"], COULEURS["gris"], True),
            ("Marge", r["marge"], COULEURS["vert"], True),
            ("TVA (sur frais service)", r["tva"], COULEURS["gris"], True),
            ("Versements bancaires", r["versements_bancaires"], COULEURS["vert"], True),
            ("Retraits bancaires", r["retraits_bancaires"], COULEURS["rouge"], True),
            ("Solde bancaire", r["solde_bancaire"], COULEURS["primaire"], True),
        ]
        grille = ctk.CTkFrame(self.zone, fg_color="transparent")
        grille.pack(fill="both", expand=True)
        for i, (titre_c, valeur, couleur, montant) in enumerate(cartes):
            carte = ctk.CTkFrame(grille, fg_color=COULEURS["carte"], corner_radius=10)
            carte.grid(row=i // 4, column=i % 4, padx=8, pady=8, sticky="nsew")
            grille.grid_columnconfigure(i % 4, weight=1)
            ctk.CTkLabel(carte, text=titre_c.upper(),
                         font=ctk.CTkFont(size=11, weight="bold"),
                         text_color=COULEURS["gris"], wraplength=150).pack(
                             anchor="w", padx=12, pady=(10, 0))
            texte = (formater(valeur) + f" {config.DEVISE}") if montant else str(valeur)
            ctk.CTkLabel(carte, text=texte,
                         font=ctk.CTkFont(size=18, weight="bold"),
                         text_color=couleur).pack(anchor="w", padx=12, pady=(0, 10))
