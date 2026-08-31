# -*- coding: utf-8 -*-
"""
ui/historique_transactions_view.py
-----------------------------------
Rubrique « Historique des transactions ».

L'utilisateur choisit une période (date de début / date de fin), affiche les
transactions correspondantes (ventes + encaissements) puis peut générer un PDF.
Toutes les données proviennent directement de la base existante.
"""

from datetime import datetime, date
import tkinter as tk
from tkinter import ttk
import customtkinter as ctk

import database as db
import settings
import pdf_listes
from i18n import t
from pdf_receipt import formater_montant
from ui.helpers import COULEURS, info, erreur, CALENDRIER_DISPO

if CALENDRIER_DISPO:
    from tkcalendar import DateEntry


class HistoriqueTransactionsView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=COULEURS["fond"])
        self._construire()

    def _construire(self):
        # --- Titre ---
        ctk.CTkLabel(self, text=t("hist_transac_titre"),
                     font=ctk.CTkFont(size=26, weight="bold"),
                     text_color=COULEURS["primaire"]).pack(
                         anchor="w", padx=30, pady=(26, 4))
        ctk.CTkLabel(self, text=t("hist_transac_intro"),
                     font=ctk.CTkFont(size=13),
                     text_color=COULEURS["gris"], justify="left").pack(
                         anchor="w", padx=30, pady=(0, 14))

        # --- Barre de sélection de période ---
        barre = ctk.CTkFrame(self, fg_color=COULEURS["carte"], corner_radius=10)
        barre.pack(fill="x", padx=30, pady=(0, 12))

        interne = ctk.CTkFrame(barre, fg_color="transparent")
        interne.pack(fill="x", padx=14, pady=12)

        # Valeurs par défaut : du 1er du mois courant à aujourd'hui
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
        ctk.CTkButton(interne, text="📄  " + t("btn_generer_pdf"),
                      fg_color=COULEURS["vert"], hover_color="#166638",
                      command=self.generer_pdf, width=150).pack(side="right")

        # --- Tableau des transactions ---
        cadre = ctk.CTkFrame(self, fg_color=COULEURS["carte"], corner_radius=10)
        cadre.pack(fill="both", expand=True, padx=30, pady=(0, 8))

        colonnes = ("date", "client", "reference", "type", "montant",
                    "mode", "achat", "vente", "benefice")
        self.tableau = ttk.Treeview(cadre, columns=colonnes, show="headings",
                                    selectmode="browse")
        entetes = {
            "date": t("recu_date"), "client": t("champ_client"),
            "reference": t("champ_reference"), "type": t("col_type_op"),
            "montant": t("champ_montant"), "mode": t("champ_mode"),
            "achat": t("champ_prix_achat"), "vente": t("champ_prix_vente"),
            "benefice": t("col_benefice"),
        }
        largeurs = {"date": 90, "client": 150, "reference": 110, "type": 100,
                    "montant": 110, "mode": 100, "achat": 100, "vente": 100,
                    "benefice": 100}
        alignements = {"montant": "e", "achat": "e", "vente": "e", "benefice": "e"}
        for c in colonnes:
            self.tableau.heading(c, text=entetes[c])
            self.tableau.column(c, width=largeurs[c],
                                anchor=alignements.get(c, "w"))

        scroll = ttk.Scrollbar(cadre, orient="vertical",
                               command=self.tableau.yview)
        self.tableau.configure(yscrollcommand=scroll.set)
        self.tableau.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        scroll.pack(side="right", fill="y", pady=10, padx=(0, 10))

        # --- Bandeau des totaux ---
        self.bandeau = ctk.CTkFrame(self, fg_color="transparent")
        self.bandeau.pack(fill="x", padx=30, pady=(0, 20))
        self.lbl_totaux = ctk.CTkLabel(self.bandeau, text="",
                                       font=ctk.CTkFont(size=13, weight="bold"),
                                       text_color=COULEURS["primaire"],
                                       justify="left")
        self.lbl_totaux.pack(anchor="w")

    # ------------------------------------------------------------------ #
    def _creer_champ_date(self, parent, valeur_defaut):
        """Crée un sélecteur de date (calendrier si disponible, sinon champ texte)."""
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
        """Lit une date au format 'AAAA-MM-JJ' ; renvoie None si invalide."""
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

    def _dates_valides(self):
        """Renvoie (date_debut, date_fin) si tout est correct, sinon None."""
        d = self._lire_date(self.w_debut)
        f = self._lire_date(self.w_fin)
        if not d or not f or d > f:
            erreur("Erreur", t("msg_dates_invalides"))
            return None
        return d, f

    def afficher(self):
        dates = self._dates_valides()
        if dates is None:
            return
        date_debut, date_fin = dates

        for ligne in self.tableau.get_children():
            self.tableau.delete(ligne)

        transactions = db.lister_transactions_periode(date_debut, date_fin)
        for tr in transactions:
            type_txt = (t("type_vente") if tr["type"] == "Vente"
                        else t("type_encaissement"))
            achat = formater_montant(tr["prix_achat"]) if tr["prix_achat"] is not None else "-"
            vente = formater_montant(tr["prix_vente"]) if tr["prix_vente"] is not None else "-"
            benef = formater_montant(tr["benefice"]) if tr["benefice"] is not None else "-"
            self.tableau.insert("", "end", values=(
                tr["date"], tr["client"], tr["reference"], type_txt,
                formater_montant(tr["montant"]), tr["mode"],
                achat, vente, benef))

        # Totaux
        tot = db.totaux_transactions_periode(date_debut, date_fin)
        self.lbl_totaux.configure(text=(
            f'{t("lbl_total_ventes")} : {formater_montant(tot["total_ventes"])}     |     '
            f'{t("lbl_total_encaisse")} : {formater_montant(tot["total_encaisse"])}     |     '
            f'{t("lbl_total_achats")} : {formater_montant(tot["total_achats"])}     |     '
            f'{t("lbl_total_benefice")} : {formater_montant(tot["total_benefice"])}     |     '
            f'{t("lbl_total_restant")} : {formater_montant(tot["total_restant"])}'
        ))

        if not transactions:
            info("Info", t("msg_aucune_transac"))

    def generer_pdf(self):
        dates = self._dates_valides()
        if dates is None:
            return
        if not settings.est_configure():
            erreur("Erreur", t("msg_nom_requis"))
            return
        date_debut, date_fin = dates
        try:
            chemin = pdf_listes.generer_historique_transactions(
                date_debut, date_fin, ouvrir=True)
            info("Info", f'{t("msg_pdf_genere")}\n{chemin}')
        except Exception as e:
            erreur("Erreur", str(e))
