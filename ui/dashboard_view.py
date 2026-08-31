# -*- coding: utf-8 -*-
"""
ui/dashboard_view.py
---------------------
Le tableau de bord : page d'accueil avec les chiffres clés de l'agence.
"""

import customtkinter as ctk

import database as db
from i18n import t
from pdf_receipt import formater_montant
from ui.helpers import COULEURS


class DashboardView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=COULEURS["fond"])
        self._cartes = {}
        self._construire()

    def _construire(self):
        # Titre
        ctk.CTkLabel(self, text=t("menu_dashboard"),
                     font=ctk.CTkFont(size=26, weight="bold"),
                     text_color=COULEURS["primaire"]).pack(
                         anchor="w", padx=30, pady=(26, 4))
        ctk.CTkLabel(self, text=t("dash_bienvenue") + " — APLM BUZNESS COMPANY",
                     font=ctk.CTkFont(size=14),
                     text_color=COULEURS["gris"]).pack(
                         anchor="w", padx=30, pady=(0, 20))

        # Grille de cartes
        grille = ctk.CTkFrame(self, fg_color="transparent")
        grille.pack(fill="x", padx=24)

        cartes_def = [
            ("nb_clients",   t("dash_clients"),  COULEURS["accent"]),
            ("nb_dossiers",  t("dash_dossiers"), COULEURS["primaire2"]),
            ("total_vente",  t("dash_ca"),       "#8e44ad"),
            ("total_paye",   t("dash_encaisse"), COULEURS["vert"]),
            ("solde_global", t("dash_solde"),    COULEURS["rouge"]),
            ("benefice",     t("dash_benefice"), "#e67e22"),
        ]

        for i, (cle, titre, couleur) in enumerate(cartes_def):
            carte = ctk.CTkFrame(grille, fg_color=COULEURS["carte"],
                                 corner_radius=14, border_width=0)
            carte.grid(row=i // 3, column=i % 3, padx=10, pady=10,
                       sticky="nsew", ipadx=10, ipady=6)
            grille.grid_columnconfigure(i % 3, weight=1)

            bande = ctk.CTkFrame(carte, fg_color=couleur, width=6,
                                 corner_radius=3)
            bande.pack(side="left", fill="y", padx=(10, 0), pady=14)

            interieur = ctk.CTkFrame(carte, fg_color="transparent")
            interieur.pack(side="left", fill="both", expand=True,
                           padx=16, pady=16)
            ctk.CTkLabel(interieur, text=titre.upper(),
                         font=ctk.CTkFont(size=12, weight="bold"),
                         text_color=COULEURS["gris"], anchor="w").pack(anchor="w")
            valeur_lbl = ctk.CTkLabel(interieur, text="—",
                                      font=ctk.CTkFont(size=24, weight="bold"),
                                      text_color=couleur, anchor="w")
            valeur_lbl.pack(anchor="w", pady=(4, 0))
            self._cartes[cle] = valeur_lbl

        self.rafraichir()

    def rafraichir(self):
        """Recalcule et affiche les chiffres à jour."""
        stats = db.statistiques_globales()
        self._cartes["nb_clients"].configure(text=str(stats["nb_clients"]))
        self._cartes["nb_dossiers"].configure(text=str(stats["nb_dossiers"]))
        self._cartes["total_vente"].configure(
            text=formater_montant(stats["total_vente"]))
        self._cartes["total_paye"].configure(
            text=formater_montant(stats["total_paye"]))
        self._cartes["solde_global"].configure(
            text=formater_montant(stats["solde_global"]))
        self._cartes["benefice"].configure(
            text=formater_montant(stats["benefice"]))
