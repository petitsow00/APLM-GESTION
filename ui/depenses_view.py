# -*- coding: utf-8 -*-
"""
ui/depenses_view.py
--------------------
Rubrique DÉPENSES / DÉCAISSEMENTS.

Ici on enregistre les SORTIES d'argent de l'agence : loyer, salaires,
paiement des fournisseurs/consolidateurs, frais divers, etc.

Ces dépenses alimentent AUTOMATIQUEMENT la comptabilité (journal de caisse
ou de banque + compte de charge choisi) — sans aucune double saisie.
"""

from datetime import datetime, date
from tkinter import ttk
import customtkinter as ctk

import config
import comptabilite as co
from i18n import t
from pdf_receipt import formater_montant
from ui.helpers import COULEURS, info, erreur, confirmer, CALENDRIER_DISPO

if CALENDRIER_DISPO:
    from tkcalendar import DateEntry


class DepensesView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=COULEURS["fond"])
        # Prépare les tables comptables si ce n'est pas déjà fait
        co.initialiser_comptabilite()
        self._comptes = self._charger_comptes_charge()
        self._construire()
        self.rafraichir()

    def _charger_comptes_charge(self):
        """Liste des comptes utilisables pour une dépense : charges (classe 6)
        + le compte Fournisseurs (401) pour régler une dette fournisseur."""
        options = []
        self._map_compte = {}
        for c in co.lister_comptes(classe=6):
            libelle = f'{c["numero"]} - {c["intitule"]}'
            options.append(libelle)
            self._map_compte[libelle] = c["numero"]
        c401 = co.get_compte("401")
        if c401:
            libelle = f'{c401["numero"]} - {c401["intitule"]}'
            options.append(libelle)
            self._map_compte[libelle] = "401"
        return options

    # ------------------------------------------------------------------ #
    def _construire(self):
        ctk.CTkLabel(self, text=t("dep_titre"),
                     font=ctk.CTkFont(size=26, weight="bold"),
                     text_color=COULEURS["primaire"]).pack(
                         anchor="w", padx=30, pady=(26, 4))
        ctk.CTkLabel(self, text=t("dep_intro"),
                     font=ctk.CTkFont(size=13), text_color=COULEURS["gris"],
                     justify="left").pack(anchor="w", padx=30, pady=(0, 12))

        # --- Formulaire d'ajout (2 lignes) ---
        form = ctk.CTkFrame(self, fg_color=COULEURS["carte"], corner_radius=10)
        form.pack(fill="x", padx=30, pady=(0, 12))
        l1 = ctk.CTkFrame(form, fg_color="transparent"); l1.pack(fill="x", padx=14, pady=(12, 4))
        l2 = ctk.CTkFrame(form, fg_color="transparent"); l2.pack(fill="x", padx=14, pady=(0, 12))

        # Ligne 1 : date, bénéficiaire, montant, mode
        ctk.CTkLabel(l1, text=t("champ_date_depense"), width=60,
                     text_color=COULEURS["texte"]).pack(side="left")
        self.w_date = self._champ_date(l1, date.today())

        ctk.CTkLabel(l1, text=t("champ_beneficiaire"),
                     text_color=COULEURS["texte"]).pack(side="left", padx=(14, 4))
        self.e_benef = ctk.CTkEntry(l1, width=170); self.e_benef.pack(side="left")

        ctk.CTkLabel(l1, text=t("champ_montant"),
                     text_color=COULEURS["texte"]).pack(side="left", padx=(14, 4))
        self.e_montant = ctk.CTkEntry(l1, width=110); self.e_montant.pack(side="left")

        ctk.CTkLabel(l1, text=t("champ_mode"),
                     text_color=COULEURS["texte"]).pack(side="left", padx=(14, 4))
        self.var_mode = ctk.StringVar(value=config.MODES_PAIEMENT[0])
        ctk.CTkOptionMenu(l1, values=config.MODES_PAIEMENT, variable=self.var_mode,
                          width=140, fg_color=COULEURS["primaire"],
                          button_color=COULEURS["primaire2"]).pack(side="left")

        # Ligne 2 : motif, compte, référence, bouton ajouter
        ctk.CTkLabel(l2, text=t("champ_motif"), width=60,
                     text_color=COULEURS["texte"]).pack(side="left")
        self.e_motif = ctk.CTkEntry(l2, width=200); self.e_motif.pack(side="left")

        ctk.CTkLabel(l2, text=t("champ_compte_charge"),
                     text_color=COULEURS["texte"]).pack(side="left", padx=(14, 4))
        self.var_compte = ctk.StringVar(
            value=self._comptes[0] if self._comptes else "")
        ctk.CTkOptionMenu(l2, values=self._comptes, variable=self.var_compte,
                          width=260, fg_color=COULEURS["primaire"],
                          button_color=COULEURS["primaire2"]).pack(side="left")

        ctk.CTkButton(l2, text="➕  " + t("btn_ajouter"),
                      fg_color=COULEURS["vert"], hover_color="#166638",
                      command=self._ajouter).pack(side="right")

        # --- Barre période + total ---
        barre = ctk.CTkFrame(self, fg_color="transparent")
        barre.pack(fill="x", padx=30, pady=(0, 6))
        ctk.CTkLabel(barre, text=t("champ_date_debut"),
                     text_color=COULEURS["texte"]).pack(side="left", padx=(0, 4))
        self.w_debut = self._champ_date(barre, date.today().replace(day=1))
        ctk.CTkLabel(barre, text=t("champ_date_fin"),
                     text_color=COULEURS["texte"]).pack(side="left", padx=(12, 4))
        self.w_fin = self._champ_date(barre, date.today())
        ctk.CTkButton(barre, text="🔎  " + t("btn_afficher"),
                      fg_color=COULEURS["accent"], width=120,
                      command=self.rafraichir).pack(side="left", padx=(12, 0))
        ctk.CTkButton(barre, text="🗑  " + t("btn_supprimer"),
                      fg_color=COULEURS["rouge"], hover_color="#922b21",
                      command=self._supprimer).pack(side="right")

        # --- Tableau ---
        cadre = ctk.CTkFrame(self, fg_color=COULEURS["carte"], corner_radius=10)
        cadre.pack(fill="both", expand=True, padx=30, pady=(4, 8))
        colonnes = ("date", "benef", "motif", "compte", "mode", "montant")
        self.tableau = ttk.Treeview(cadre, columns=colonnes, show="headings",
                                    selectmode="browse")
        entetes = {"date": t("recu_date"), "benef": t("col_beneficiaire"),
                   "motif": t("col_motif"), "compte": t("champ_compte_charge"),
                   "mode": t("champ_mode"), "montant": t("champ_montant")}
        largeurs = {"date": 90, "benef": 180, "motif": 200, "compte": 180,
                    "mode": 110, "montant": 120}
        for c in colonnes:
            self.tableau.heading(c, text=entetes[c])
            self.tableau.column(c, width=largeurs[c],
                                anchor="e" if c == "montant" else "w")
        scroll = ttk.Scrollbar(cadre, orient="vertical", command=self.tableau.yview)
        self.tableau.configure(yscrollcommand=scroll.set)
        self.tableau.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        scroll.pack(side="right", fill="y", pady=10, padx=(0, 10))
        self._ids = {}

        self.lbl_total = ctk.CTkLabel(self, text="",
                                      font=ctk.CTkFont(size=14, weight="bold"),
                                      text_color=COULEURS["rouge"])
        self.lbl_total.pack(anchor="e", padx=34, pady=(0, 16))

    # ------------------------------------------------------------------ #
    def _champ_date(self, parent, valeur):
        if CALENDRIER_DISPO:
            w = DateEntry(parent, date_pattern="yyyy-mm-dd", width=12,
                          background=COULEURS["primaire"], foreground="white",
                          borderwidth=1)
            try:
                w.set_date(valeur)
            except Exception:
                pass
            w.pack(side="left")
        else:
            w = ctk.CTkEntry(parent, width=110, placeholder_text="AAAA-MM-JJ")
            w.insert(0, valeur.strftime("%Y-%m-%d"))
            w.pack(side="left")
        return w

    def _lire_date(self, widget):
        if CALENDRIER_DISPO:
            try:
                return widget.get_date().strftime("%Y-%m-%d")
            except Exception:
                return None
        try:
            return datetime.strptime(widget.get().strip(), "%Y-%m-%d").strftime("%Y-%m-%d")
        except ValueError:
            return None

    def _ajouter(self):
        montant_txt = self.e_montant.get().strip().replace(" ", "").replace(",", ".")
        try:
            montant = float(montant_txt)
        except ValueError:
            erreur("Erreur", t("msg_montant_invalide"))
            return
        if montant <= 0:
            erreur("Erreur", t("msg_montant_invalide"))
            return
        date_dep = self._lire_date(self.w_date)
        if not date_dep:
            erreur("Erreur", t("msg_dates_invalides"))
            return
        compte = self._map_compte.get(self.var_compte.get(), "605")
        co.creer_depense(date_depense=date_dep,
                         beneficiaire=self.e_benef.get().strip(),
                         montant=montant, mode=self.var_mode.get(),
                         motif=self.e_motif.get().strip(),
                         compte_charge=compte)
        # Réinitialise les champs de saisie
        self.e_benef.delete(0, "end")
        self.e_montant.delete(0, "end")
        self.e_motif.delete(0, "end")
        info("Info", t("msg_enregistre"))
        self.rafraichir()

    def rafraichir(self):
        d = self._lire_date(self.w_debut)
        f = self._lire_date(self.w_fin)
        for ligne in self.tableau.get_children():
            self.tableau.delete(ligne)
        self._ids = {}
        total = 0
        for dep in co.lister_depenses(d, f):
            item = self.tableau.insert("", "end", values=(
                (dep["date_depense"] or "")[:10], dep["beneficiaire"] or "",
                dep["motif"] or "", dep["compte_charge"] or "",
                dep["mode"] or "", formater_montant(dep["montant"])))
            self._ids[item] = dep["id"]
            total += dep["montant"] or 0
        self.lbl_total.configure(
            text=f'{t("tdb_charges")} : {formater_montant(total)}')

    def _supprimer(self):
        sel = self.tableau.selection()
        if not sel:
            info("Info", t("msg_selectionner"))
            return
        if not confirmer(t("btn_supprimer"), t("msg_confirmer_suppr")):
            return
        co.supprimer_depense(self._ids.get(sel[0]))
        self.rafraichir()
