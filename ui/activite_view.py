# -*- coding: utf-8 -*-
"""
ui/activite_view.py
-------------------
Écran GÉNÉRIQUE pour les 4 activités séparées (billets / hôtels / assurances /
visa). Une seule classe `ActiviteView` s'adapte à chaque activité grâce à une
configuration (titre, champs, colonne de détail, statuts).

Chaque activité concrète (BilletsView, HotelsView, ...) est une petite
sous-classe qui fournit sa configuration.
"""

import tkinter as tk
from tkinter import ttk
import customtkinter as ctk

import config
import database as db
import activites as act
from ui.helpers import (COULEURS, FormulaireDialog, confirmer, info, erreur)
from ui.operation_dialog import OperationDialog, formater
from ui.documents_dialog import DocumentsDialog


# --------------------------------------------------------------------------- #
#  Blocs de champs réutilisables
# --------------------------------------------------------------------------- #
def champs_finances():
    return [
        {"cle": "prix_fournisseur", "label": "Prix fournisseur (coût)", "type": "nombre"},
        {"cle": "prix_client", "label": "Prix de vente (client)", "type": "nombre"},
        {"cle": "frais_service", "label": "Frais de service", "type": "nombre"},
        {"cle": "autres_frais", "label": "Autres frais", "type": "nombre"},
        {"cle": "reduction", "label": "Réduction", "type": "nombre"},
        {"cle": "tva_taux", "label": "Taux TVA % (sur frais de service)", "type": "nombre"},
        {"cle": "notes", "label": "Observations", "type": "zone"},
    ]


# --------------------------------------------------------------------------- #
#  Vue générique
# --------------------------------------------------------------------------- #
class ActiviteView(ctk.CTkFrame):
    # À définir par chaque sous-classe :
    ACTIVITE = "billet"
    TITRE = "Activité"
    COL_DETAIL = "Détail"

    def champs(self):
        raise NotImplementedError

    def detail(self, o):
        return ""

    # ---------------------------------------------------------------- #
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
        e = ctk.CTkEntry(barre, placeholder_text="Rechercher (client, référence, passager)…",
                         textvariable=self.recherche_var, width=280)
        e.pack(side="left")
        e.bind("<KeyRelease>", lambda ev: self.rafraichir())

        ctk.CTkButton(barre, text="+ Nouveau", fg_color=COULEURS["vert"],
                      hover_color="#166638", width=110,
                      command=self.ajouter).pack(side="right", padx=(6, 0))
        ctk.CTkButton(barre, text="Modifier", fg_color=COULEURS["accent"],
                      width=90, command=self.modifier).pack(side="right", padx=(6, 0))
        ctk.CTkButton(barre, text="💰 Paiement", fg_color=COULEURS["primaire2"],
                      width=105, command=self.payer).pack(side="right", padx=(6, 0))
        ctk.CTkButton(barre, text="🧾 Reçu", fg_color=COULEURS["primaire"],
                      width=90, command=self.recu).pack(side="right", padx=(6, 0))
        ctk.CTkButton(barre, text="📎 Documents", fg_color=COULEURS["gris"],
                      width=110, command=self.documents).pack(side="right", padx=(6, 0))
        ctk.CTkButton(barre, text="Supprimer", fg_color=COULEURS["rouge"],
                      hover_color="#922b21", width=95,
                      command=self.supprimer).pack(side="right", padx=(6, 0))

        cadre = ctk.CTkFrame(self, fg_color=COULEURS["carte"], corner_radius=10)
        cadre.pack(fill="both", expand=True, padx=30, pady=(0, 24))
        cols = ("reference", "client", "detail", "statut", "total", "reste")
        entetes = {"reference": "Référence", "client": "Client",
                   "detail": self.COL_DETAIL, "statut": "Statut",
                   "total": "Total client", "reste": "Reste à payer"}
        largeurs = {"reference": 110, "client": 160, "detail": 180,
                    "statut": 110, "total": 110, "reste": 110}
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
            tag = "du" if t["reste_a_payer"] > 0 else "ok"
            self.tableau.insert("", "end", iid=str(o["id"]), tags=(tag,), values=(
                o["reference"] or "", client, self.detail(o), o["statut"] or "",
                formater(t["total_client"]), formater(t["reste_a_payer"])))
        if self.on_changement:
            self.on_changement()

    def _id_selectionne(self):
        sel = self.tableau.selection()
        if not sel:
            info("Info", "Veuillez sélectionner une ligne dans la liste.")
            return None
        return int(sel[0])

    def ajouter(self):
        dlg = OperationDialog(self.winfo_toplevel(), "Nouveau — " + self.TITRE,
                              self.champs())
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
        dlg = OperationDialog(self.winfo_toplevel(), "Modifier — " + self.TITRE,
                              self.champs(), valeurs=valeurs,
                              client_fixe=(o["client_id"], nom))
        if dlg.resultat is None:
            return
        act.modifier_operation(self.ACTIVITE, oid, dlg.resultat["donnees"])
        self.rafraichir()

    def supprimer(self):
        oid = self._id_selectionne()
        if oid is None:
            return
        if confirmer("Supprimer", "Supprimer définitivement cette opération ?"):
            act.supprimer_operation(self.ACTIVITE, oid)
            self.rafraichir()

    def payer(self):
        oid = self._id_selectionne()
        if oid is None:
            return
        t = act.totaux_operation(self.ACTIVITE, oid)
        champs = [
            {"cle": "info", "label": f"Total {formater(t['total_client'])} · "
             f"Payé {formater(t['total_paye'])} · Reste {formater(t['reste_a_payer'])}",
             "type": "texte"},
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

    def documents(self):
        oid = self._id_selectionne()
        if oid is None:
            return
        o = act.get_operation(self.ACTIVITE, oid)
        DocumentsDialog(self.winfo_toplevel(), self.ACTIVITE, oid, o["client_id"])

    def recu(self):
        oid = self._id_selectionne()
        if oid is None:
            return
        import settings
        if not settings.est_configure():
            erreur("Réglages", "Renseignez d'abord le nom de l'agence "
                   "dans l'écran Réglages avant d'imprimer un reçu.")
            return
        try:
            from pdf_operation import generer_recu_operation
            chemin = generer_recu_operation(self.ACTIVITE, oid, ouvrir=True)
            info("Reçu", f"Reçu généré :\n{chemin}")
        except Exception as e:
            erreur("Erreur", f"Impossible de générer le reçu :\n{e}")


# --------------------------------------------------------------------------- #
#  Les 4 activités concrètes
# --------------------------------------------------------------------------- #
class BilletsView(ActiviteView):
    ACTIVITE = "billet"
    TITRE = "✈️  Billets"
    COL_DETAIL = "Trajet"

    def detail(self, o):
        return f'{o["ville_depart"] or "?"}→{o["ville_arrivee"] or "?"}'

    def champs(self):
        return [
            {"cle": "type_billet", "label": "Type de billet", "type": "liste",
             "options": ["Aller-retour", "Aller simple", "Multi-destinations"]},
            {"cle": "passager", "label": "Passager", "type": "texte"},
            {"cle": "statut", "label": "Statut", "type": "liste",
             "options": ["En attente", "Confirmée", "Émise", "Annulée"]},
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
            {"cle": "gds", "label": "GDS (interne)", "type": "liste",
             "options": [""] + config.GDS},
            {"cle": "consolidateur", "label": "Consolidateur (interne)", "type": "liste",
             "options": [""] + config.CONSOLIDATEURS},
        ] + champs_finances()


class HotelsView(ActiviteView):
    ACTIVITE = "hotel"
    TITRE = "🏨  Hôtels"
    COL_DETAIL = "Hôtel"

    def detail(self, o):
        return f'{o["nom_hotel"] or "?"} ({o["ville"] or ""})'

    def champs(self):
        return [
            {"cle": "passager", "label": "Client / occupant", "type": "texte"},
            {"cle": "statut", "label": "Statut", "type": "liste",
             "options": ["En attente", "Confirmée", "Payée", "Annulée"]},
            {"cle": "nom_hotel", "label": "Nom de l'hôtel", "type": "texte"},
            {"cle": "ville", "label": "Ville", "type": "texte"},
            {"cle": "pays", "label": "Pays", "type": "texte"},
            {"cle": "adresse", "label": "Adresse", "type": "texte"},
            {"cle": "categorie", "label": "Catégorie / étoiles", "type": "texte"},
            {"cle": "type_hebergement", "label": "Type d'hébergement", "type": "texte"},
            {"cle": "date_arrivee", "label": "Date d'arrivée", "type": "date"},
            {"cle": "date_depart", "label": "Date de départ", "type": "date"},
            {"cle": "nb_nuits", "label": "Nombre de nuits", "type": "texte"},
            {"cle": "nb_adultes", "label": "Nombre d'adultes", "type": "texte"},
            {"cle": "nb_enfants", "label": "Nombre d'enfants", "type": "texte"},
            {"cle": "nb_chambres", "label": "Nombre de chambres", "type": "texte"},
            {"cle": "type_chambre", "label": "Type de chambre", "type": "texte"},
            {"cle": "type_lit", "label": "Type de lit", "type": "texte"},
            {"cle": "formule", "label": "Formule", "type": "liste",
             "options": ["Sans repas", "Petit-déjeuner", "Demi-pension",
                         "Pension complète", "Tout compris"]},
            {"cle": "num_reservation", "label": "N° de réservation", "type": "texte"},
            {"cle": "date_reservation", "label": "Date de réservation", "type": "date"},
        ] + champs_finances()


class AssurancesView(ActiviteView):
    ACTIVITE = "assurance"
    TITRE = "🛡️  Assurances"
    COL_DETAIL = "Compagnie / destination"

    def detail(self, o):
        return f'{o["compagnie_assurance"] or "?"} · {o["destination"] or ""}'

    def champs(self):
        return [
            {"cle": "passager", "label": "Assuré", "type": "texte"},
            {"cle": "statut", "label": "Statut", "type": "liste",
             "options": ["En attente", "Active", "Expirée", "Annulée"]},
            {"cle": "compagnie_assurance", "label": "Compagnie d'assurance", "type": "texte"},
            {"cle": "num_police", "label": "Numéro de police", "type": "texte"},
            {"cle": "type_assurance", "label": "Type d'assurance", "type": "texte"},
            {"cle": "destination", "label": "Destination", "type": "texte"},
            {"cle": "zone_couverture", "label": "Zone de couverture", "type": "texte"},
            {"cle": "date_debut", "label": "Date de début", "type": "date"},
            {"cle": "date_fin", "label": "Date de fin", "type": "date"},
            {"cle": "motif_voyage", "label": "Motif du voyage", "type": "texte"},
            {"cle": "date_naissance", "label": "Date de naissance (assuré)", "type": "date"},
            {"cle": "nationalite", "label": "Nationalité", "type": "texte"},
            {"cle": "num_passeport", "label": "N° passeport", "type": "texte"},
        ] + champs_finances()


class VisasView(ActiviteView):
    ACTIVITE = "visa"
    TITRE = "🛂  Assistance Visa"
    COL_DETAIL = "Pays / type"

    def detail(self, o):
        return f'{o["pays_destination"] or "?"} · {o["type_visa"] or ""}'

    def champs(self):
        return [
            {"cle": "passager", "label": "Demandeur", "type": "texte"},
            {"cle": "statut", "label": "Statut du dossier", "type": "liste",
             "options": ["Nouveau", "Documents à compléter", "Prêt pour dépôt",
                         "Rendez-vous programmé", "Dossier déposé", "En traitement",
                         "Visa accordé", "Visa refusé", "Dossier annulé"]},
            {"cle": "pays_destination", "label": "Pays de destination", "type": "texte"},
            {"cle": "type_visa", "label": "Type de visa", "type": "texte"},
            {"cle": "motif", "label": "Motif", "type": "liste",
             "options": ["Tourisme", "Affaires", "Études", "Visite familiale",
                         "Transit", "Autre"]},
            {"cle": "nb_entrees", "label": "Nombre d'entrées", "type": "liste",
             "options": ["Simple", "Double", "Multiple"]},
            {"cle": "duree", "label": "Durée", "type": "texte"},
            {"cle": "date_voyage_prevue", "label": "Date prévue du voyage", "type": "date"},
            {"cle": "num_dossier", "label": "Numéro de dossier", "type": "texte"},
            {"cle": "date_ouverture", "label": "Date d'ouverture", "type": "date"},
            {"cle": "centre_depot", "label": "Centre de dépôt", "type": "texte"},
            {"cle": "ambassade", "label": "Ambassade / Consulat", "type": "texte"},
            {"cle": "date_depot", "label": "Date de dépôt", "type": "date"},
            {"cle": "date_rdv", "label": "Date du rendez-vous", "type": "date"},
            {"cle": "nationalite", "label": "Nationalité", "type": "texte"},
            {"cle": "num_passeport", "label": "N° passeport", "type": "texte"},
            {"cle": "date_exp_passeport", "label": "Expiration passeport", "type": "date"},
        ] + champs_finances()
