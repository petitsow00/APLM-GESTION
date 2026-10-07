# -*- coding: utf-8 -*-
"""
ui/clients_view.py
-------------------
Écran de gestion des clients : liste, recherche, ajout, modification,
suppression, et surtout la FICHE CLIENT UNIQUE avec tout son historique
(billets, hôtels, assurances, visas, soldes) — §2 du cahier des charges.
"""

import tkinter as tk
from tkinter import ttk
import customtkinter as ctk

import database as db
import activites as act
import config
from i18n import t
from ui.helpers import (COULEURS, FormulaireDialog, confirmer, info, erreur)
from ui.operation_dialog import formater


class ClientsView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=COULEURS["fond"])
        self._construire()
        self.rafraichir()

    def _construire(self):
        ctk.CTkLabel(self, text=t("menu_clients"),
                     font=ctk.CTkFont(size=26, weight="bold"),
                     text_color=COULEURS["primaire"]).pack(
                         anchor="w", padx=30, pady=(26, 10))

        barre = ctk.CTkFrame(self, fg_color="transparent")
        barre.pack(fill="x", padx=30, pady=(0, 10))

        self.recherche_var = ctk.StringVar()
        entree = ctk.CTkEntry(barre, placeholder_text=t("btn_rechercher") + "...",
                              textvariable=self.recherche_var, width=260)
        entree.pack(side="left")
        entree.bind("<KeyRelease>", lambda e: self.rafraichir())

        ctk.CTkButton(barre, text="📋 Fiche / Historique", fg_color=COULEURS["primaire2"],
                      command=self.fiche, width=160).pack(side="left", padx=(10, 0))

        ctk.CTkButton(barre, text="+ " + t("btn_ajouter"),
                      fg_color=COULEURS["vert"], hover_color="#166638",
                      command=self.ajouter, width=110).pack(side="right", padx=(8, 0))
        ctk.CTkButton(barre, text=t("btn_modifier"),
                      fg_color=COULEURS["accent"], command=self.modifier,
                      width=100).pack(side="right", padx=(8, 0))
        ctk.CTkButton(barre, text=t("btn_supprimer"),
                      fg_color=COULEURS["rouge"], hover_color="#922b21",
                      command=self.supprimer, width=100).pack(side="right", padx=(8, 0))

        cadre = ctk.CTkFrame(self, fg_color=COULEURS["carte"], corner_radius=10)
        cadre.pack(fill="both", expand=True, padx=30, pady=(0, 24))

        colonnes = ("code", "nom", "prenom", "telephone", "passeport")
        self.tableau = ttk.Treeview(cadre, columns=colonnes, show="headings",
                                    selectmode="browse")
        entetes = {"code": t("col_code"), "nom": t("champ_nom"),
                   "prenom": t("champ_prenom"), "telephone": t("champ_telephone"),
                   "passeport": "N° passeport"}
        largeurs = {"code": 90, "nom": 170, "prenom": 150, "telephone": 150,
                    "passeport": 150}
        for c in colonnes:
            self.tableau.heading(c, text=entetes[c])
            self.tableau.column(c, width=largeurs[c], anchor="w")
        scroll = ttk.Scrollbar(cadre, orient="vertical", command=self.tableau.yview)
        self.tableau.configure(yscrollcommand=scroll.set)
        self.tableau.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        scroll.pack(side="right", fill="y", pady=10, padx=(0, 10))
        self.tableau.bind("<Double-1>", lambda e: self.fiche())

    # ------------------------------------------------------------------ #
    def rafraichir(self):
        for ligne in self.tableau.get_children():
            self.tableau.delete(ligne)
        for c in db.lister_clients(self.recherche_var.get().strip()):
            passeport = c["num_passeport"] if "num_passeport" in c.keys() else ""
            self.tableau.insert("", "end", iid=str(c["id"]), values=(
                c["code"], c["nom"], c["prenom"] or "",
                c["telephone"] or "", passeport or ""))

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
            {"cle": "date_naissance", "label": "Date de naissance", "type": "date"},
            {"cle": "nationalite", "label": "Nationalité", "type": "texte"},
            {"cle": "num_passeport", "label": "Numéro de passeport", "type": "texte"},
            {"cle": "date_exp_passeport", "label": "Expiration du passeport", "type": "date"},
            {"cle": "adresse", "label": t("champ_adresse"), "type": "texte"},
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
        # Détection de doublon (§5) : on prévient avant de créer
        doublons = db.detecter_doublons(nom=r["nom"], prenom=r["prenom"],
                                        telephone=r["telephone"], email=r["email"],
                                        num_passeport=r["num_passeport"])
        if doublons:
            d = doublons[0]["client"]
            if not confirmer("Client déjà existant ?",
                             f'Un client semble déjà exister :\n\n'
                             f'{d["nom"]} {d["prenom"] or ""} ({d["code"]})\n'
                             f'Correspondance : {doublons[0]["critere"]}\n\n'
                             f'Voulez-vous quand même créer une NOUVELLE fiche ?'):
                return
        db.creer_client(r["nom"], r["prenom"], r["telephone"], r["email"],
                        r["adresse"], "", "", r["notes"],
                        date_naissance=r["date_naissance"], nationalite=r["nationalite"],
                        num_passeport=r["num_passeport"],
                        date_exp_passeport=r["date_exp_passeport"])
        self.rafraichir()

    def modifier(self):
        cid = self._id_selectionne()
        if cid is None:
            return
        client = db.get_client(cid)
        cles = ("nom", "prenom", "telephone", "email", "date_naissance",
                "nationalite", "num_passeport", "date_exp_passeport",
                "adresse", "notes")
        valeurs = {k: (client[k] if k in client.keys() and client[k] else "")
                   for k in cles}
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
                           r["adresse"], "", "", r["notes"],
                           date_naissance=r["date_naissance"],
                           nationalite=r["nationalite"],
                           num_passeport=r["num_passeport"],
                           date_exp_passeport=r["date_exp_passeport"])
        self.rafraichir()

    def fiche(self):
        cid = self._id_selectionne()
        if cid is None:
            return
        FicheClient(self.winfo_toplevel(), cid)

    def supprimer(self):
        cid = self._id_selectionne()
        if cid is None:
            return
        client = db.get_client(cid)
        msg = t("msg_confirmer_suppr") + f"\n\n{client['nom']} {client['prenom'] or ''}"
        msg += "\n\n(Toutes ses opérations et paiements liés seront aussi supprimés.)"
        if confirmer(t("btn_supprimer"), msg):
            db.supprimer_client(cid)
            self.rafraichir()


# =========================================================================== #
#  FICHE CLIENT UNIQUE + HISTORIQUE (§2)
# =========================================================================== #
class FicheClient(ctk.CTkToplevel):
    def __init__(self, parent, client_id):
        super().__init__(parent)
        self.client_id = client_id
        self.configure(fg_color=COULEURS["fond"])
        self.geometry("860x620")
        c = db.get_client(client_id)
        self.title(f'Fiche client — {c["nom"]} {c["prenom"] or ""}')

        # En-tête
        entete = ctk.CTkFrame(self, fg_color=COULEURS["primaire"], corner_radius=0)
        entete.pack(fill="x")
        ctk.CTkLabel(entete,
                     text=f'{c["nom"]} {c["prenom"] or ""}   ({c["code"] or ""})',
                     font=ctk.CTkFont(size=20, weight="bold"),
                     text_color="white").pack(anchor="w", padx=24, pady=(14, 2))

        def val(cle):
            return c[cle] if cle in c.keys() and c[cle] else "—"
        infos = (f'📞 {val("telephone")}    ✉ {val("email")}    '
                 f'🛂 {val("num_passeport")}\n'
                 f'Nationalité : {val("nationalite")}    '
                 f'Naissance : {val("date_naissance")}    '
                 f'Passeport exp. : {val("date_exp_passeport")}')
        ctk.CTkLabel(entete, text=infos, justify="left",
                     font=ctk.CTkFont(size=12), text_color="#cdd8e4").pack(
                         anchor="w", padx=24, pady=(0, 14))

        # Bandeau soldes
        histo = act.lister_operations_client(client_id)
        total = sum(o["total_client"] for o in histo)
        paye = sum(o["total_paye"] for o in histo)
        reste = sum(o["reste_a_payer"] for o in histo)
        avoir = db.get_solde_avoir(client_id)["solde"] if hasattr(db, "get_solde_avoir") else 0

        bandeau = ctk.CTkFrame(self, fg_color=COULEURS["carte"])
        bandeau.pack(fill="x", padx=18, pady=(12, 6))
        for titre, montant, couleur in (
                ("Total opérations", total, COULEURS["primaire2"]),
                ("Déjà payé", paye, COULEURS["vert"]),
                ("Reste à payer", reste, COULEURS["rouge"]),
                ("Avoir (cagnotte)", avoir, "#8e44ad")):
            b = ctk.CTkFrame(bandeau, fg_color="transparent")
            b.pack(side="left", padx=18, pady=10)
            ctk.CTkLabel(b, text=titre.upper(), font=ctk.CTkFont(size=11, weight="bold"),
                         text_color=COULEURS["gris"]).pack(anchor="w")
            ctk.CTkLabel(b, text=formater(montant) + f' {config.DEVISE}',
                         font=ctk.CTkFont(size=17, weight="bold"),
                         text_color=couleur).pack(anchor="w")

        # Historique des opérations
        ctk.CTkLabel(self, text="Historique des opérations",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=COULEURS["primaire"]).pack(anchor="w", padx=22, pady=(8, 2))
        cadre = ctk.CTkFrame(self, fg_color=COULEURS["carte"], corner_radius=10)
        cadre.pack(fill="both", expand=True, padx=18, pady=(0, 16))
        cols = ("activite", "reference", "date", "statut", "total", "paye", "reste")
        entetes = {"activite": "Activité", "reference": "Référence", "date": "Date",
                   "statut": "Statut", "total": "Total", "paye": "Payé", "reste": "Reste"}
        larg = {"activite": 100, "reference": 120, "date": 100, "statut": 120,
                "total": 100, "paye": 100, "reste": 100}
        tab = ttk.Treeview(cadre, columns=cols, show="headings", selectmode="browse")
        for c2 in cols:
            tab.heading(c2, text=entetes[c2])
            tab.column(c2, width=larg[c2],
                       anchor="e" if c2 in ("total", "paye", "reste") else "w")
        tab.pack(fill="both", expand=True, padx=10, pady=10)
        for o in histo:
            tab.insert("", "end", values=(
                o["activite_libelle"], o["reference"], o["date"], o["statut"],
                formater(o["total_client"]), formater(o["total_paye"]),
                formater(o["reste_a_payer"])))
        if not histo:
            ctk.CTkLabel(cadre, text="Aucune opération pour ce client.",
                         text_color=COULEURS["gris"]).pack(pady=20)

        self.transient(parent)
