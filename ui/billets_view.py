# -*- coding: utf-8 -*-
"""
ui/billets_view.py
------------------
Module ✈️ BILLETS : liste des billets + ajout / modification / suppression
+ enregistrement des paiements. Utilise OperationDialog (sélecteur de client
intelligent + calculs automatiques).
"""

import tkinter as tk
from tkinter import ttk
import customtkinter as ctk

import config
import database as db
import activites as act
from ui.helpers import (COULEURS, FormulaireDialog, confirmer, info, erreur)
from ui.operation_dialog import OperationDialog, formater

STATUTS_BILLET = ["En attente", "Confirmée", "Émise", "Annulée"]
TYPES_VOL = ["Aller-retour", "Aller simple", "Multi-destinations"]


def champs_billet():
    """Définit les champs du formulaire billet (repris du §6)."""
    return [
        {"cle": "type_billet", "label": "Type de billet", "type": "liste",
         "options": TYPES_VOL},
        {"cle": "passager", "label": "Passager", "type": "texte"},
        {"cle": "statut", "label": "Statut", "type": "liste", "options": STATUTS_BILLET},
        {"cle": "pnr", "label": "PNR", "type": "texte"},
        {"cle": "compagnie", "label": "Compagnie aérienne", "type": "texte"},
        {"cle": "num_billet", "label": "Numéro de billet", "type": "texte"},
        {"cle": "classe", "label": "Classe", "type": "liste",
         "options": config.CLASSES_VOYAGE},
        {"cle": "date_reservation", "label": "Date de réservation", "type": "date"},
        {"cle": "date_limite_emission", "label": "Date limite d'émission (OPC)",
         "type": "date"},
        {"cle": "ville_depart", "label": "Ville de départ", "type": "texte"},
        {"cle": "date_depart", "label": "Date de départ", "type": "date"},
        {"cle": "ville_arrivee", "label": "Ville d'arrivée", "type": "texte"},
        {"cle": "num_vol_aller", "label": "N° de vol (aller)", "type": "texte"},
        {"cle": "date_retour", "label": "Date de retour", "type": "date"},
        {"cle": "num_vol_retour", "label": "N° de vol (retour)", "type": "texte"},
        {"cle": "bagage_soute", "label": "Bagage en soute", "type": "texte"},
        # --- Champs INTERNES (jamais sur le reçu) ---
        {"cle": "gds", "label": "GDS (interne)", "type": "liste",
         "options": [""] + config.GDS},
        {"cle": "consolidateur", "label": "Consolidateur (interne)", "type": "liste",
         "options": [""] + config.CONSOLIDATEURS},
        # --- Finances ---
        {"cle": "prix_fournisseur", "label": "Prix fournisseur (coût)", "type": "nombre"},
        {"cle": "prix_client", "label": "Prix de vente (client)", "type": "nombre"},
        {"cle": "frais_service", "label": "Frais de service", "type": "nombre"},
        {"cle": "autres_frais", "label": "Autres frais", "type": "nombre"},
        {"cle": "reduction", "label": "Réduction", "type": "nombre"},
        {"cle": "tva_taux", "label": "Taux TVA % (sur frais de service)", "type": "nombre"},
        {"cle": "notes", "label": "Observations", "type": "zone"},
    ]


class BilletsView(ctk.CTkFrame):
    ACTIVITE = "billet"
    TITRE = "✈️  Billets"

    def __init__(self, parent, on_changement=None):
        super().__init__(parent, fg_color=COULEURS["fond"])
        self.on_changement = on_changement
        self._construire()
        self.rafraichir()

    def _construire(self):
        ctk.CTkLabel(self, text=self.TITRE,
                     font=ctk.CTkFont(size=26, weight="bold"),
                     text_color=COULEURS["primaire"]).pack(
                         anchor="w", padx=30, pady=(26, 10))

        barre = ctk.CTkFrame(self, fg_color="transparent")
        barre.pack(fill="x", padx=30, pady=(0, 10))
        self.recherche_var = ctk.StringVar()
        e = ctk.CTkEntry(barre, placeholder_text="Rechercher (client, PNR, passager)…",
                         textvariable=self.recherche_var, width=280)
        e.pack(side="left")
        e.bind("<KeyRelease>", lambda ev: self.rafraichir())

        ctk.CTkButton(barre, text="+ Nouveau", fg_color=COULEURS["vert"],
                      hover_color="#166638", width=120,
                      command=self.ajouter).pack(side="right", padx=(8, 0))
        ctk.CTkButton(barre, text="Modifier", fg_color=COULEURS["accent"],
                      width=100, command=self.modifier).pack(side="right", padx=(8, 0))
        ctk.CTkButton(barre, text="💰 Paiement", fg_color=COULEURS["primaire2"],
                      width=110, command=self.payer).pack(side="right", padx=(8, 0))
        ctk.CTkButton(barre, text="Supprimer", fg_color=COULEURS["rouge"],
                      hover_color="#922b21", width=100,
                      command=self.supprimer).pack(side="right", padx=(8, 0))

        cadre = ctk.CTkFrame(self, fg_color=COULEURS["carte"], corner_radius=10)
        cadre.pack(fill="both", expand=True, padx=30, pady=(0, 24))
        cols = ("reference", "client", "passager", "trajet", "statut", "total", "reste")
        entetes = {"reference": "Référence", "client": "Client", "passager": "Passager",
                   "trajet": "Trajet", "statut": "Statut", "total": "Total client",
                   "reste": "Reste à payer"}
        largeurs = {"reference": 110, "client": 150, "passager": 130, "trajet": 140,
                    "statut": 90, "total": 110, "reste": 110}
        self.tableau = ttk.Treeview(cadre, columns=cols, show="headings",
                                    selectmode="browse")
        for c in cols:
            self.tableau.heading(c, text=entetes[c])
            self.tableau.column(c, width=largeurs[c],
                                anchor="e" if c in ("total", "reste") else "w")
        scroll = ttk.Scrollbar(cadre, orient="vertical", command=self.tableau.yview)
        self.tableau.configure(yscrollcommand=scroll.set)
        self.tableau.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        scroll.pack(side="right", fill="y", pady=10, padx=(0, 10))
        self.tableau.tag_configure("du", foreground=COULEURS["rouge"])
        self.tableau.tag_configure("ok", foreground=COULEURS["vert"])
        self.tableau.bind("<Double-1>", lambda e: self.modifier())

    def rafraichir(self):
        for l in self.tableau.get_children():
            self.tableau.delete(l)
        for o in act.lister_operations(self.ACTIVITE, self.recherche_var.get().strip()):
            t = act.totaux_operation(self.ACTIVITE, o["id"])
            client = f'{o["client_nom"]} {o["client_prenom"] or ""}'.strip()
            trajet = f'{o["ville_depart"] or "?"}→{o["ville_arrivee"] or "?"}'
            tag = "du" if t["reste_a_payer"] > 0 else "ok"
            self.tableau.insert("", "end", iid=str(o["id"]), tags=(tag,), values=(
                o["reference"] or "", client, o["passager"] or "", trajet,
                o["statut"] or "", formater(t["total_client"]),
                formater(t["reste_a_payer"])))
        if self.on_changement:
            self.on_changement()

    def _id_selectionne(self):
        sel = self.tableau.selection()
        if not sel:
            info("Info", "Veuillez sélectionner une ligne dans la liste.")
            return None
        return int(sel[0])

    def ajouter(self):
        dlg = OperationDialog(self.winfo_toplevel(), "Nouveau billet", champs_billet())
        if dlg.resultat is None:
            return
        act.creer_operation(self.ACTIVITE, dlg.resultat["client_id"],
                            dlg.resultat["donnees"])
        self.rafraichir()

    def modifier(self):
        oid = self._id_selectionne()
        if oid is None:
            return
        o = act.get_operation(self.ACTIVITE, oid)
        valeurs = {k: (o[k] if o[k] is not None else "") for k in o.keys()}
        c = db.get_client(o["client_id"])
        nom = f'{c["nom"]} {c["prenom"] or ""}'.strip() if c else "?"
        dlg = OperationDialog(self.winfo_toplevel(), "Modifier le billet",
                              champs_billet(), valeurs=valeurs,
                              client_fixe=(o["client_id"], nom))
        if dlg.resultat is None:
            return
        act.modifier_operation(self.ACTIVITE, oid, dlg.resultat["donnees"])
        self.rafraichir()

    def supprimer(self):
        oid = self._id_selectionne()
        if oid is None:
            return
        if confirmer("Supprimer", "Supprimer définitivement ce billet ?"):
            act.supprimer_operation(self.ACTIVITE, oid)
            self.rafraichir()

    def payer(self):
        oid = self._id_selectionne()
        if oid is None:
            return
        t = act.totaux_operation(self.ACTIVITE, oid)
        champs = [
            {"cle": "info", "label": f"Total {formater(t['total_client'])} · "
             f"Déjà payé {formater(t['total_paye'])} · "
             f"Reste {formater(t['reste_a_payer'])}", "type": "texte"},
            {"cle": "montant", "label": f"Montant ({config.DEVISE})", "type": "nombre"},
            {"cle": "mode", "label": "Mode de paiement", "type": "liste",
             "options": config.MODES_PAIEMENT},
            {"cle": "date_paiement", "label": "Date", "type": "date"},
            {"cle": "reference", "label": "Référence", "type": "texte"},
            {"cle": "notes", "label": "Observations", "type": "zone"},
        ]
        dlg = FormulaireDialog(self.winfo_toplevel(), "Enregistrer un paiement", champs)
        if dlg.resultat is None:
            return
        r = dlg.resultat
        if not r["montant"] or r["montant"] <= 0:
            erreur("Erreur", "Le montant doit être supérieur à 0.")
            return
        act.creer_paiement_operation(self.ACTIVITE, oid, r["montant"], r["mode"],
                                     r["reference"], r["date_paiement"], r["notes"])
        info("Paiement", "Paiement enregistré.")
        self.rafraichir()
