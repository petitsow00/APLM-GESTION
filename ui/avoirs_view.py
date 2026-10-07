# -*- coding: utf-8 -*-
"""
ui/avoirs_view.py
------------------
Rubrique AVOIR (cagnotte du client).

Ici on suit l'argent qu'un client verse D'AVANCE, petit à petit, jusqu'à
réunir la somme nécessaire pour payer son voyage.

  - Un DÉPÔT fait monter la cagnotte (le client apporte de l'argent).
  - Une UTILISATION fait descendre la cagnotte (on paie un dossier avec).

Le SOLDE de la cagnotte = total déposé - total utilisé.

Réservé à l'administrateur (voir ui/app.py).
"""

from datetime import datetime, date
from tkinter import ttk
import customtkinter as ctk

import config
import database as db
from i18n import t
from pdf_receipt import formater_montant
from ui.helpers import (COULEURS, info, erreur, confirmer,
                        FormulaireDialog, CALENDRIER_DISPO)

if CALENDRIER_DISPO:
    from tkcalendar import DateEntry


class AvoirsView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=COULEURS["fond"])
        self._map_client = {}     # libellé affiché -> id du client
        self._ids = {}            # ligne du tableau -> id du mouvement
        self._construire()
        self._charger_clients()
        self.rafraichir()

    # ------------------------------------------------------------------ #
    #  Construction de l'écran
    # ------------------------------------------------------------------ #
    def _construire(self):
        ctk.CTkLabel(self, text=t("avoir_titre"),
                     font=ctk.CTkFont(size=26, weight="bold"),
                     text_color=COULEURS["primaire"]).pack(
                         anchor="w", padx=30, pady=(26, 4))
        ctk.CTkLabel(self, text=t("avoir_intro"),
                     font=ctk.CTkFont(size=13), text_color=COULEURS["gris"],
                     justify="left", wraplength=900).pack(
                         anchor="w", padx=30, pady=(0, 12))

        # --- Barre : choix du client + solde ---
        barre = ctk.CTkFrame(self, fg_color=COULEURS["carte"], corner_radius=10)
        barre.pack(fill="x", padx=30, pady=(0, 12))
        ligne_c = ctk.CTkFrame(barre, fg_color="transparent")
        ligne_c.pack(fill="x", padx=14, pady=12)

        ctk.CTkLabel(ligne_c, text=t("avoir_choisir_client"),
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=COULEURS["texte"]).pack(side="left", padx=(0, 6))
        self.var_client = ctk.StringVar(value="")
        self.menu_client = ctk.CTkOptionMenu(
            ligne_c, values=[""], variable=self.var_client, width=320,
            fg_color=COULEURS["primaire"], button_color=COULEURS["primaire2"],
            command=lambda _=None: self.rafraichir())
        self.menu_client.pack(side="left")

        self.lbl_solde = ctk.CTkLabel(
            ligne_c, text="", font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COULEURS["vert"])
        self.lbl_solde.pack(side="right")

        # --- Formulaire : ajouter un dépôt ---
        form = ctk.CTkFrame(self, fg_color=COULEURS["carte"], corner_radius=10)
        form.pack(fill="x", padx=30, pady=(0, 12))
        ctk.CTkLabel(form, text=t("avoir_ajouter_depot"),
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=COULEURS["primaire"]).pack(
                         anchor="w", padx=14, pady=(10, 2))
        l1 = ctk.CTkFrame(form, fg_color="transparent")
        l1.pack(fill="x", padx=14, pady=(0, 12))

        ctk.CTkLabel(l1, text=t("recu_date"),
                     text_color=COULEURS["texte"]).pack(side="left", padx=(0, 4))
        self.w_date = self._champ_date(l1, date.today())

        ctk.CTkLabel(l1, text=t("champ_montant"),
                     text_color=COULEURS["texte"]).pack(side="left", padx=(14, 4))
        self.e_montant = ctk.CTkEntry(l1, width=120)
        self.e_montant.pack(side="left")

        ctk.CTkLabel(l1, text=t("champ_mode"),
                     text_color=COULEURS["texte"]).pack(side="left", padx=(14, 4))
        self.var_mode = ctk.StringVar(value=config.MODES_PAIEMENT[0])
        ctk.CTkOptionMenu(l1, values=config.MODES_PAIEMENT, variable=self.var_mode,
                          width=140, fg_color=COULEURS["primaire"],
                          button_color=COULEURS["primaire2"]).pack(side="left")

        ctk.CTkLabel(l1, text=t("champ_notes"),
                     text_color=COULEURS["texte"]).pack(side="left", padx=(14, 4))
        self.e_notes = ctk.CTkEntry(l1, width=180)
        self.e_notes.pack(side="left")

        ctk.CTkButton(l1, text="➕  " + t("avoir_depot"),
                      fg_color=COULEURS["vert"], hover_color="#166638",
                      command=self._ajouter_depot).pack(side="right")

        # --- Barre d'actions ---
        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.pack(fill="x", padx=30, pady=(0, 6))
        ctk.CTkButton(actions, text="💳  " + t("avoir_utiliser"),
                      fg_color=COULEURS["accent"], hover_color="#2471a3",
                      command=self._utiliser).pack(side="left")
        ctk.CTkButton(actions, text="🗑  " + t("btn_supprimer"),
                      fg_color=COULEURS["rouge"], hover_color="#922b21",
                      command=self._supprimer).pack(side="right")

        # --- Tableau des mouvements ---
        cadre = ctk.CTkFrame(self, fg_color=COULEURS["carte"], corner_radius=10)
        cadre.pack(fill="both", expand=True, padx=30, pady=(4, 16))
        colonnes = ("date", "type", "montant", "mode", "notes")
        self.tableau = ttk.Treeview(cadre, columns=colonnes, show="headings",
                                    selectmode="browse")
        entetes = {"date": t("recu_date"), "type": t("col_type"),
                   "montant": t("champ_montant"), "mode": t("champ_mode"),
                   "notes": t("champ_notes")}
        largeurs = {"date": 100, "type": 130, "montant": 140,
                    "mode": 140, "notes": 300}
        for c in colonnes:
            self.tableau.heading(c, text=entetes[c])
            self.tableau.column(c, width=largeurs[c],
                                anchor="e" if c == "montant" else "w")
        scroll = ttk.Scrollbar(cadre, orient="vertical",
                               command=self.tableau.yview)
        self.tableau.configure(yscrollcommand=scroll.set)
        self.tableau.pack(side="left", fill="both", expand=True,
                          padx=(10, 0), pady=10)
        scroll.pack(side="right", fill="y", pady=10, padx=(0, 10))

    # ------------------------------------------------------------------ #
    #  Petits outils dates (identiques à l'écran Dépenses)
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
            return datetime.strptime(widget.get().strip(),
                                     "%Y-%m-%d").strftime("%Y-%m-%d")
        except ValueError:
            return None

    # ------------------------------------------------------------------ #
    #  Chargement des clients dans le menu déroulant
    # ------------------------------------------------------------------ #
    def _charger_clients(self):
        self._map_client = {}
        libelles = []
        for c in db.lister_clients():
            nom = f'{c["nom"]} {c["prenom"] or ""}'.strip()
            if c["code"]:
                nom = f'{nom} ({c["code"]})'
            self._map_client[nom] = c["id"]
            libelles.append(nom)
        if libelles:
            self.menu_client.configure(values=libelles)
            if self.var_client.get() not in self._map_client:
                self.var_client.set(libelles[0])
        else:
            self.menu_client.configure(values=[t("avoir_aucun_client")])
            self.var_client.set(t("avoir_aucun_client"))

    def _client_courant(self):
        """Renvoie l'id du client sélectionné (ou None si aucun)."""
        return self._map_client.get(self.var_client.get())

    # ------------------------------------------------------------------ #
    #  Affichage / rafraîchissement
    # ------------------------------------------------------------------ #
    def rafraichir(self):
        # Vide le tableau
        for ligne in self.tableau.get_children():
            self.tableau.delete(ligne)
        self._ids = {}

        client_id = self._client_courant()
        if client_id is None:
            self.lbl_solde.configure(text="")
            return

        # Solde de la cagnotte
        s = db.get_solde_avoir(client_id)
        self.lbl_solde.configure(
            text=f'{t("avoir_solde")} : {formater_montant(s["solde"])}   '
                 f'({t("avoir_depots")} {formater_montant(s["depots"])} · '
                 f'{t("avoir_utilises")} {formater_montant(s["utilises"])})')

        # Liste des mouvements
        for m in db.lister_avoirs(client_id):
            type_txt = (t("avoir_depot") if m["type"] == "depot"
                        else t("avoir_utilisation"))
            # Un dépôt s'affiche en +, une utilisation en -
            signe = "+" if m["type"] == "depot" else "-"
            montant_txt = f'{signe} {formater_montant(m["montant"])}'
            item = self.tableau.insert("", "end", values=(
                (m["date_mouvement"] or "")[:10], type_txt, montant_txt,
                m["mode"] or "", m["notes"] or ""))
            self._ids[item] = m["id"]

    # ------------------------------------------------------------------ #
    #  Ajouter un dépôt
    # ------------------------------------------------------------------ #
    def _lire_montant(self, widget):
        txt = widget.get().strip().replace(" ", "").replace(",", ".")
        try:
            valeur = float(txt)
        except ValueError:
            return None
        return valeur

    def _ajouter_depot(self):
        client_id = self._client_courant()
        if client_id is None:
            erreur("Erreur", t("avoir_aucun_client"))
            return
        montant = self._lire_montant(self.e_montant)
        if montant is None or montant <= 0:
            erreur("Erreur", t("msg_montant_invalide"))
            return
        date_dep = self._lire_date(self.w_date)
        if not date_dep:
            erreur("Erreur", t("msg_dates_invalides"))
            return
        db.creer_depot_avoir(client_id, montant,
                             mode=self.var_mode.get(),
                             date_mouvement=date_dep,
                             notes=self.e_notes.get().strip())
        self.e_montant.delete(0, "end")
        self.e_notes.delete(0, "end")
        info("Info", t("avoir_depot_ok"))
        self.rafraichir()

    # ------------------------------------------------------------------ #
    #  Utiliser l'avoir pour payer un dossier
    # ------------------------------------------------------------------ #
    def _utiliser(self):
        client_id = self._client_courant()
        if client_id is None:
            erreur("Erreur", t("avoir_aucun_client"))
            return
        solde = db.get_solde_avoir(client_id)["solde"]
        if solde <= 0:
            erreur("Erreur", t("avoir_montant_trop_grand"))
            return

        # Dossiers du client (pour choisir lequel payer)
        dossiers = db.lister_dossiers(client_id=client_id)
        if not dossiers:
            erreur("Erreur", t("avoir_aucun_dossier"))
            return
        map_dossier = {}
        options = []
        for d in dossiers:
            libelle = f'{d["reference"]} - {d["titre"] or ""}'.strip(" -")
            map_dossier[libelle] = d["id"]
            options.append(libelle)

        champs = [
            {"cle": "dossier", "label": t("avoir_choisir_dossier"),
             "type": "liste", "options": options},
            {"cle": "montant", "label": f'{t("champ_montant")} '
             f'({t("avoir_solde")} : {formater_montant(solde)})',
             "type": "nombre"},
            {"cle": "date", "label": t("recu_date"), "type": "date"},
            {"cle": "notes", "label": t("champ_notes"), "type": "zone"},
        ]
        dlg = FormulaireDialog(self, t("avoir_utiliser"), champs)
        if dlg.resultat is None:
            return
        r = dlg.resultat
        montant = r.get("montant") or 0
        if montant <= 0:
            erreur("Erreur", t("msg_montant_invalide"))
            return
        if montant > solde:
            erreur("Erreur", t("avoir_montant_trop_grand"))
            return
        date_util = (r.get("date") or "").strip() or \
            date.today().strftime("%Y-%m-%d")
        dossier_id = map_dossier.get(r.get("dossier"))
        db.creer_utilisation_avoir(client_id, montant,
                                   dossier_id=dossier_id,
                                   date_mouvement=date_util,
                                   notes=r.get("notes", ""))
        info("Info", t("avoir_utilisation_ok"))
        self.rafraichir()

    # ------------------------------------------------------------------ #
    #  Supprimer un mouvement
    # ------------------------------------------------------------------ #
    def _supprimer(self):
        sel = self.tableau.selection()
        if not sel:
            info("Info", t("msg_selectionner"))
            return
        if not confirmer(t("btn_supprimer"), t("msg_confirmer_suppr")):
            return
        db.supprimer_avoir(self._ids.get(sel[0]))
        self.rafraichir()
