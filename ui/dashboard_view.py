# -*- coding: utf-8 -*-
"""
ui/dashboard_view.py
---------------------
Le tableau de bord : page d'accueil avec les chiffres clés RÉELS de l'agence
(basés sur les 4 activités, les paiements et la banque).
"""

import customtkinter as ctk

import database as db
import rapports as rap
import auth
from i18n import t
from pdf_receipt import formater_montant
from ui.helpers import COULEURS


class DashboardView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=COULEURS["fond"])
        self._cartes = {}
        self._construire()

    def _construire(self):
        ctk.CTkLabel(self, text=t("menu_dashboard"),
                     font=ctk.CTkFont(size=26, weight="bold"),
                     text_color=COULEURS["primaire"]).pack(
                         anchor="w", padx=30, pady=(26, 4))
        ctk.CTkLabel(self, text=t("dash_bienvenue"),
                     font=ctk.CTkFont(size=14),
                     text_color=COULEURS["gris"]).pack(
                         anchor="w", padx=30, pady=(0, 16))

        zone = ctk.CTkScrollableFrame(self, fg_color=COULEURS["fond"])
        zone.pack(fill="both", expand=True, padx=6)
        grille = ctk.CTkFrame(zone, fg_color="transparent")
        grille.pack(fill="x", padx=18)

        admin = auth.est_admin()
        # (clé, titre, couleur, admin_only, est_montant)
        cartes_def = [
            ("nb_clients", "Clients", COULEURS["accent"], False, False),
            ("nb_billets", "Billets", COULEURS["primaire2"], False, False),
            ("nb_hotels", "Hôtels", COULEURS["primaire2"], False, False),
            ("nb_assurances", "Assurances", COULEURS["primaire2"], False, False),
            ("nb_visas", "Visa", COULEURS["primaire2"], False, False),
            ("dossiers_visa_en_cours", "Dossiers visa en cours", "#e67e22", False, False),
            ("ca_mois", "CA du mois", "#8e44ad", True, True),
            ("ca_jour", "CA du jour", "#8e44ad", True, True),
            ("encaissements_mois", "Encaissements (mois)", COULEURS["vert"], True, True),
            ("creances", "Créances", COULEURS["rouge"], True, True),
            ("marge_mois", "Marge du mois", COULEURS["vert"], True, True),
            ("paiements_en_attente", "Paiements en attente", COULEURS["rouge"], True, False),
            ("solde_bancaire", "Solde bancaire", COULEURS["primaire"], True, True),
        ]

        col = 0
        row = 0
        self._est_montant = {}
        for cle, titre, couleur, admin_only, montant in cartes_def:
            if admin_only and not admin:
                continue
            self._est_montant[cle] = montant
            carte = ctk.CTkFrame(grille, fg_color=COULEURS["carte"], corner_radius=14)
            carte.grid(row=row, column=col, padx=10, pady=10, sticky="nsew",
                       ipadx=8, ipady=6)
            grille.grid_columnconfigure(col, weight=1)
            bande = ctk.CTkFrame(carte, fg_color=couleur, width=6, corner_radius=3)
            bande.pack(side="left", fill="y", padx=(10, 0), pady=14)
            interieur = ctk.CTkFrame(carte, fg_color="transparent")
            interieur.pack(side="left", fill="both", expand=True, padx=16, pady=16)
            ctk.CTkLabel(interieur, text=titre.upper(),
                         font=ctk.CTkFont(size=12, weight="bold"),
                         text_color=COULEURS["gris"], anchor="w",
                         wraplength=160).pack(anchor="w")
            lbl = ctk.CTkLabel(interieur, text="—",
                               font=ctk.CTkFont(size=23, weight="bold"),
                               text_color=couleur, anchor="w")
            lbl.pack(anchor="w", pady=(4, 0))
            self._cartes[cle] = lbl
            col += 1
            if col >= 3:
                col = 0
                row += 1

        self.rafraichir()

    def rafraichir(self):
        """Recalcule et affiche les chiffres RÉELS à jour."""
        try:
            tb = rap.tableau_de_bord()
        except Exception:
            tb = {}
        tb["nb_clients"] = db.statistiques_globales().get("nb_clients", 0)

        for cle, lbl in self._cartes.items():
            valeur = tb.get(cle, 0)
            if self._est_montant.get(cle):
                lbl.configure(text=formater_montant(valeur))
            else:
                lbl.configure(text=str(valeur))
