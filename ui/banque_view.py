# -*- coding: utf-8 -*-
"""
ui/banque_view.py
-----------------
Module 🏦 BANQUE : comptes bancaires, versements/dépôts, retraits et soldes.
Rappel : la banque est un JOURNAL DE TRÉSORERIE, séparé des ventes. Un dépôt
n'est PAS une vente (pas de double comptage).
"""

import tkinter as tk
from tkinter import ttk
import customtkinter as ctk

import config
import banque as bq
from ui.helpers import COULEURS, FormulaireDialog, confirmer, info, erreur
from ui.operation_dialog import formater


class BanqueView(ctk.CTkFrame):
    def __init__(self, parent, on_changement=None):
        super().__init__(parent, fg_color=COULEURS["fond"])
        self.on_changement = on_changement
        self._construire()
        self.rafraichir()

    def _construire(self):
        ctk.CTkLabel(self, text="🏦  Banque",
                     font=ctk.CTkFont(size=26, weight="bold"),
                     text_color=COULEURS["primaire"]).pack(
                         anchor="w", padx=30, pady=(26, 8))

        # --- Bandeau des soldes par compte ---
        self.bandeau = ctk.CTkFrame(self, fg_color=COULEURS["carte"], corner_radius=10)
        self.bandeau.pack(fill="x", padx=30, pady=(0, 10))

        # --- Barre d'actions ---
        barre = ctk.CTkFrame(self, fg_color="transparent")
        barre.pack(fill="x", padx=30, pady=(0, 8))
        ctk.CTkButton(barre, text="+ Compte", fg_color=COULEURS["primaire2"],
                      width=100, command=self.nouveau_compte).pack(side="left")
        ctk.CTkButton(barre, text="⬇ Versement", fg_color=COULEURS["vert"],
                      hover_color="#166638", width=120,
                      command=self.versement).pack(side="left", padx=6)
        ctk.CTkButton(barre, text="⬆ Retrait", fg_color=COULEURS["rouge"],
                      hover_color="#922b21", width=110,
                      command=self.retrait).pack(side="left", padx=6)
        ctk.CTkButton(barre, text="Supprimer mouvement", fg_color=COULEURS["gris"],
                      width=170, command=self.supprimer).pack(side="right")

        cadre = ctk.CTkFrame(self, fg_color=COULEURS["carte"], corner_radius=10)
        cadre.pack(fill="both", expand=True, padx=30, pady=(0, 24))
        cols = ("date", "compte", "type", "montant", "motif", "tiers", "reference")
        entetes = {"date": "Date", "compte": "Compte", "type": "Type",
                   "montant": "Montant", "motif": "Motif", "tiers": "Origine/Bénéf.",
                   "reference": "Référence"}
        largeurs = {"date": 90, "compte": 130, "type": 90, "montant": 110,
                    "motif": 150, "tiers": 140, "reference": 120}
        self.tableau = ttk.Treeview(cadre, columns=cols, show="headings",
                                    selectmode="browse")
        for c in cols:
            self.tableau.heading(c, text=entetes[c])
            self.tableau.column(c, width=largeurs[c],
                                anchor="e" if c == "montant" else "w")
        scroll = ttk.Scrollbar(cadre, orient="vertical", command=self.tableau.yview)
        self.tableau.configure(yscrollcommand=scroll.set)
        self.tableau.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        scroll.pack(side="right", fill="y", pady=10, padx=(0, 10))
        self.tableau.tag_configure("v", foreground=COULEURS["vert"])
        self.tableau.tag_configure("r", foreground=COULEURS["rouge"])

    # ---------------------------------------------------------------- #
    def _comptes_map(self):
        comptes = bq.lister_comptes()
        libelles, mapping = [], {}
        for c in comptes:
            lib = f'{c["nom"]}' + (f' ({c["banque"]})' if c["banque"] else "")
            libelles.append(lib)
            mapping[lib] = c["id"]
        return libelles, mapping

    def rafraichir(self):
        # Bandeau soldes
        for w in self.bandeau.winfo_children():
            w.destroy()
        soldes = bq.soldes_tous_comptes()
        if not soldes:
            ctk.CTkLabel(self.bandeau, text="Aucun compte bancaire. "
                         "Cliquez sur « + Compte » pour en créer un.",
                         text_color=COULEURS["gris"]).pack(padx=14, pady=12, anchor="w")
        total = 0
        for s in soldes:
            total += s["solde_actuel"]
            bloc = ctk.CTkFrame(self.bandeau, fg_color=COULEURS["fond"], corner_radius=8)
            bloc.pack(side="left", padx=10, pady=10)
            ctk.CTkLabel(bloc, text=s["compte_nom"].upper(),
                         font=ctk.CTkFont(size=11, weight="bold"),
                         text_color=COULEURS["gris"]).pack(anchor="w", padx=12, pady=(8, 0))
            ctk.CTkLabel(bloc, text=formater(s["solde_actuel"]) + f' {config.DEVISE}',
                         font=ctk.CTkFont(size=18, weight="bold"),
                         text_color=COULEURS["primaire"]).pack(anchor="w", padx=12, pady=(0, 8))
        if len(soldes) > 1:
            ctk.CTkLabel(self.bandeau, text=f'TOTAL : {formater(total)} {config.DEVISE}',
                         font=ctk.CTkFont(size=14, weight="bold"),
                         text_color=COULEURS["vert"]).pack(side="right", padx=16)

        # Mouvements
        for l in self.tableau.get_children():
            self.tableau.delete(l)
        for m in bq.lister_mouvements():
            tag = "v" if m["type"] == "versement" else "r"
            signe = "+" if m["type"] == "versement" else "-"
            self.tableau.insert("", "end", iid=str(m["id"]), tags=(tag,), values=(
                (m["date_mouvement"] or "")[:10], m["compte_nom"] or "",
                "Versement" if m["type"] == "versement" else "Retrait",
                signe + formater(m["montant"]), m["motif"] or "",
                m["categorie"] or m["tiers"] or "", m["reference_bancaire"] or ""))
        if self.on_changement:
            self.on_changement()

    # ---------------------------------------------------------------- #
    def nouveau_compte(self):
        champs = [
            {"cle": "nom", "label": "Nom du compte *", "type": "texte"},
            {"cle": "banque", "label": "Banque", "type": "texte"},
            {"cle": "numero", "label": "Numéro de compte", "type": "texte"},
            {"cle": "solde_initial", "label": "Solde initial", "type": "nombre"},
        ]
        dlg = FormulaireDialog(self.winfo_toplevel(), "Nouveau compte bancaire", champs)
        if dlg.resultat is None:
            return
        r = dlg.resultat
        if not r["nom"]:
            erreur("Erreur", "Le nom du compte est obligatoire.")
            return
        bq.creer_compte(r["nom"], r["banque"], r["numero"], r["solde_initial"])
        self.rafraichir()

    def versement(self):
        libelles, mapping = self._comptes_map()
        if not libelles:
            erreur("Erreur", "Créez d'abord un compte bancaire.")
            return
        champs = [
            {"cle": "compte", "label": "Compte", "type": "liste", "options": libelles},
            {"cle": "montant", "label": f"Montant ({config.DEVISE})", "type": "nombre"},
            {"cle": "date", "label": "Date", "type": "date"},
            {"cle": "origine", "label": "Origine des fonds", "type": "liste",
             "options": bq.ORIGINES_VERSEMENT},
            {"cle": "motif", "label": "Motif", "type": "texte"},
            {"cle": "reference_bancaire", "label": "Référence bancaire", "type": "texte"},
            {"cle": "num_bordereau", "label": "N° de bordereau", "type": "texte"},
            {"cle": "notes", "label": "Observations", "type": "zone"},
        ]
        dlg = FormulaireDialog(self.winfo_toplevel(), "⬇ Versement / dépôt", champs)
        if dlg.resultat is None:
            return
        r = dlg.resultat
        if not r["montant"] or r["montant"] <= 0:
            erreur("Erreur", "Montant invalide.")
            return
        bq.creer_versement(mapping[r["compte"]], r["montant"], r["date"],
                           origine=r["origine"], motif=r["motif"],
                           reference_bancaire=r["reference_bancaire"],
                           num_bordereau=r["num_bordereau"], notes=r["notes"])
        self.rafraichir()

    def retrait(self):
        libelles, mapping = self._comptes_map()
        if not libelles:
            erreur("Erreur", "Créez d'abord un compte bancaire.")
            return
        champs = [
            {"cle": "compte", "label": "Compte", "type": "liste", "options": libelles},
            {"cle": "montant", "label": f"Montant ({config.DEVISE})", "type": "nombre"},
            {"cle": "date", "label": "Date", "type": "date"},
            {"cle": "categorie", "label": "Catégorie", "type": "liste",
             "options": bq.CATEGORIES_RETRAIT},
            {"cle": "beneficiaire", "label": "Bénéficiaire", "type": "texte"},
            {"cle": "motif", "label": "Motif", "type": "texte"},
            {"cle": "reference_bancaire", "label": "Référence bancaire", "type": "texte"},
            {"cle": "num_cheque", "label": "N° de chèque", "type": "texte"},
            {"cle": "notes", "label": "Observations", "type": "zone"},
        ]
        dlg = FormulaireDialog(self.winfo_toplevel(), "⬆ Retrait", champs)
        if dlg.resultat is None:
            return
        r = dlg.resultat
        if not r["montant"] or r["montant"] <= 0:
            erreur("Erreur", "Montant invalide.")
            return
        bq.creer_retrait(mapping[r["compte"]], r["montant"], r["date"],
                         categorie=r["categorie"], beneficiaire=r["beneficiaire"],
                         motif=r["motif"], reference_bancaire=r["reference_bancaire"],
                         num_cheque=r["num_cheque"], notes=r["notes"])
        self.rafraichir()

    def supprimer(self):
        sel = self.tableau.selection()
        if not sel:
            info("Info", "Sélectionnez un mouvement.")
            return
        if confirmer("Supprimer", "Supprimer ce mouvement bancaire ?"):
            bq.supprimer_mouvement(int(sel[0]))
            self.rafraichir()
