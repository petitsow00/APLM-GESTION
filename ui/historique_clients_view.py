# -*- coding: utf-8 -*-
"""
ui/historique_clients_view.py
------------------------------
Rubrique « Historique clients ».

⚠️ Cette rubrique n'affiche PAS l'historique détaillé de chaque client.
   Elle sert UNIQUEMENT à générer la liste complète de tous les clients
   enregistrés, sous forme de document PDF professionnel.
"""

import tkinter as tk
from tkinter import ttk
import customtkinter as ctk

import database as db
import settings
import pdf_listes
from i18n import t
from ui.helpers import COULEURS, info, erreur


class HistoriqueClientsView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=COULEURS["fond"])
        self._construire()
        self.rafraichir()

    def _construire(self):
        # --- Titre ---
        ctk.CTkLabel(self, text=t("hist_clients_titre"),
                     font=ctk.CTkFont(size=26, weight="bold"),
                     text_color=COULEURS["primaire"]).pack(
                         anchor="w", padx=30, pady=(26, 4))
        ctk.CTkLabel(self, text=t("hist_clients_intro"),
                     font=ctk.CTkFont(size=13),
                     text_color=COULEURS["gris"], justify="left").pack(
                         anchor="w", padx=30, pady=(0, 14))

        # --- Barre d'action : bouton PDF ---
        barre = ctk.CTkFrame(self, fg_color="transparent")
        barre.pack(fill="x", padx=30, pady=(0, 10))

        self.info_nb = ctk.CTkLabel(barre, text="",
                                    font=ctk.CTkFont(size=13, weight="bold"),
                                    text_color=COULEURS["primaire"])
        self.info_nb.pack(side="left")

        ctk.CTkButton(barre, text="📄  " + t("btn_liste_clients_pdf"),
                      fg_color=COULEURS["vert"], hover_color="#166638",
                      height=42, command=self.generer_pdf,
                      width=280).pack(side="right")

        # --- Aperçu de la liste (lecture seule) ---
        cadre = ctk.CTkFrame(self, fg_color=COULEURS["carte"], corner_radius=10)
        cadre.pack(fill="both", expand=True, padx=30, pady=(0, 24))

        colonnes = ("num", "nom", "telephone", "email", "date")
        self.tableau = ttk.Treeview(cadre, columns=colonnes, show="headings",
                                    selectmode="browse")
        entetes = {
            "num": t("col_num"), "nom": t("col_nom_prenom"),
            "telephone": t("champ_telephone"), "email": t("champ_email"),
            "date": t("col_date_enreg"),
        }
        largeurs = {"num": 50, "nom": 220, "telephone": 150,
                    "email": 240, "date": 160}
        for c in colonnes:
            self.tableau.heading(c, text=entetes[c])
            self.tableau.column(c, width=largeurs[c], anchor="w")

        scroll = ttk.Scrollbar(cadre, orient="vertical",
                               command=self.tableau.yview)
        self.tableau.configure(yscrollcommand=scroll.set)
        self.tableau.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        scroll.pack(side="right", fill="y", pady=10, padx=(0, 10))

    # ------------------------------------------------------------------ #
    def rafraichir(self):
        for ligne in self.tableau.get_children():
            self.tableau.delete(ligne)
        clients = db.lister_clients()
        for i, c in enumerate(clients, start=1):
            nom_complet = f'{c["nom"]} {c["prenom"] or ""}'.strip()
            date_enr = (c["date_creation"] or "")[:10]
            self.tableau.insert("", "end", values=(
                i, nom_complet, c["telephone"] or "",
                c["email"] or "", date_enr))
        self.info_nb.configure(text=f'{t("dash_clients")} : {len(clients)}')

    def generer_pdf(self):
        # L'en-tête du PDF a besoin du nom de l'agence (Réglages)
        if not settings.est_configure():
            erreur("Erreur", t("msg_nom_requis"))
            return
        if not db.lister_clients():
            info("Info", t("msg_aucun_client"))
            return
        try:
            chemin = pdf_listes.generer_liste_clients(ouvrir=True)
            info("Info", f'{t("msg_pdf_genere")}\n{chemin}')
        except Exception as e:
            erreur("Erreur", str(e))
