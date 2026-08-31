# -*- coding: utf-8 -*-
"""
ui/clients_view.py
-------------------
Écran de gestion des clients : liste, recherche, ajout, modification, suppression.
"""

import tkinter as tk
from tkinter import ttk
import customtkinter as ctk

import database as db
import config
from i18n import t
from ui.helpers import (COULEURS, FormulaireDialog, confirmer, info, erreur)


class ClientsView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=COULEURS["fond"])
        self._construire()
        self.rafraichir()

    def _construire(self):
        # --- Titre ---
        ctk.CTkLabel(self, text=t("menu_clients"),
                     font=ctk.CTkFont(size=26, weight="bold"),
                     text_color=COULEURS["primaire"]).pack(
                         anchor="w", padx=30, pady=(26, 10))

        # --- Barre d'actions ---
        barre = ctk.CTkFrame(self, fg_color="transparent")
        barre.pack(fill="x", padx=30, pady=(0, 10))

        self.recherche_var = ctk.StringVar()
        entree = ctk.CTkEntry(barre, placeholder_text=t("btn_rechercher") + "...",
                              textvariable=self.recherche_var, width=260)
        entree.pack(side="left")
        entree.bind("<KeyRelease>", lambda e: self.rafraichir())

        ctk.CTkButton(barre, text="+ " + t("btn_ajouter"),
                      fg_color=COULEURS["vert"], hover_color="#166638",
                      command=self.ajouter, width=120).pack(side="right", padx=(8, 0))
        ctk.CTkButton(barre, text=t("btn_modifier"),
                      fg_color=COULEURS["accent"], command=self.modifier,
                      width=110).pack(side="right", padx=(8, 0))
        ctk.CTkButton(barre, text=t("btn_supprimer"),
                      fg_color=COULEURS["rouge"], hover_color="#922b21",
                      command=self.supprimer, width=110).pack(side="right", padx=(8, 0))

        # --- Tableau ---
        cadre = ctk.CTkFrame(self, fg_color=COULEURS["carte"], corner_radius=10)
        cadre.pack(fill="both", expand=True, padx=30, pady=(0, 24))

        colonnes = ("code", "nom", "prenom", "telephone", "email")
        self.tableau = ttk.Treeview(cadre, columns=colonnes, show="headings",
                                    selectmode="browse")
        entetes = {
            "code": t("col_code"), "nom": t("champ_nom"),
            "prenom": t("champ_prenom"), "telephone": t("champ_telephone"),
            "email": t("champ_email"),
        }
        largeurs = {"code": 90, "nom": 160, "prenom": 140,
                    "telephone": 150, "email": 220}
        for c in colonnes:
            self.tableau.heading(c, text=entetes[c])
            self.tableau.column(c, width=largeurs[c], anchor="w")

        scroll = ttk.Scrollbar(cadre, orient="vertical",
                               command=self.tableau.yview)
        self.tableau.configure(yscrollcommand=scroll.set)
        self.tableau.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        scroll.pack(side="right", fill="y", pady=10, padx=(0, 10))

        self.tableau.bind("<Double-1>", lambda e: self.modifier())

    # ------------------------------------------------------------------ #
    def rafraichir(self):
        for ligne in self.tableau.get_children():
            self.tableau.delete(ligne)
        for c in db.lister_clients(self.recherche_var.get().strip()):
            self.tableau.insert("", "end", iid=str(c["id"]), values=(
                c["code"], c["nom"], c["prenom"] or "",
                c["telephone"] or "", c["email"] or ""))

    def _id_selectionne(self):
        sel = self.tableau.selection()
        if not sel:
            info("Info", t("msg_selectionner"))
            return None
        return int(sel[0])

    def _champs(self):
        return [
            {"cle": "nom", "label": t("champ_nom"), "type": "texte"},
            {"cle": "prenom", "label": t("champ_prenom"), "type": "texte"},
            {"cle": "telephone", "label": t("champ_telephone"), "type": "texte"},
            {"cle": "email", "label": t("champ_email"), "type": "texte"},
            {"cle": "adresse", "label": t("champ_adresse"), "type": "texte"},
            {"cle": "type_piece", "label": t("champ_type_piece"), "type": "texte"},
            {"cle": "num_piece", "label": t("champ_num_piece"), "type": "texte"},
            {"cle": "notes", "label": t("champ_notes"), "type": "zone"},
        ]

    def ajouter(self):
        dlg = FormulaireDialog(self.winfo_toplevel(),
                               "+ " + t("btn_ajouter") + " — " + t("menu_clients"),
                               self._champs())
        if dlg.resultat is None:
            return
        r = dlg.resultat
        if not r["nom"]:
            erreur("Erreur", t("msg_champ_requis"))
            return
        db.creer_client(r["nom"], r["prenom"], r["telephone"], r["email"],
                        r["adresse"], r["type_piece"], r["num_piece"], r["notes"])
        self.rafraichir()

    def modifier(self):
        cid = self._id_selectionne()
        if cid is None:
            return
        client = db.get_client(cid)
        valeurs = {k: (client[k] or "") for k in
                   ("nom", "prenom", "telephone", "email", "adresse",
                    "type_piece", "num_piece", "notes")}
        dlg = FormulaireDialog(self.winfo_toplevel(),
                               t("btn_modifier") + " — " + t("menu_clients"),
                               self._champs(), valeurs)
        if dlg.resultat is None:
            return
        r = dlg.resultat
        if not r["nom"]:
            erreur("Erreur", t("msg_champ_requis"))
            return
        db.modifier_client(cid, r["nom"], r["prenom"], r["telephone"], r["email"],
                           r["adresse"], r["type_piece"], r["num_piece"], r["notes"])
        self.rafraichir()

    def supprimer(self):
        cid = self._id_selectionne()
        if cid is None:
            return
        client = db.get_client(cid)
        msg = t("msg_confirmer_suppr") + f"\n\n{client['nom']} {client['prenom'] or ''}"
        msg += "\n\n(Tous ses dossiers, réservations et paiements seront aussi supprimés.)"
        if confirmer(t("btn_supprimer"), msg):
            db.supprimer_client(cid)
            self.rafraichir()
