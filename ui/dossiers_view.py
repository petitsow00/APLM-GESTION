# -*- coding: utf-8 -*-
"""
ui/dossiers_view.py
--------------------
Écran des dossiers de voyage.

Contient DEUX classes :
  - DossiersView : la liste de tous les dossiers (avec soldes)
  - DossierDetail : la fenêtre détaillée d'UN dossier
        (réservations + paiements + solde + génération du reçu PDF)
"""

import tkinter as tk
from tkinter import ttk
import customtkinter as ctk

import database as db
import config
import settings
from i18n import t
from pdf_receipt import formater_montant, generer_recu
from ui.helpers import (COULEURS, FormulaireDialog, confirmer, info, erreur)


# =========================================================================== #
#  LISTE DES DOSSIERS
# =========================================================================== #
class DossiersView(ctk.CTkFrame):
    def __init__(self, parent, on_changement=None):
        super().__init__(parent, fg_color=COULEURS["fond"])
        self.on_changement = on_changement   # appelé quand les données changent
        self._construire()
        self.rafraichir()

    def _construire(self):
        ctk.CTkLabel(self, text=t("menu_dossiers"),
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

        ctk.CTkButton(barre, text="+ " + t("btn_ajouter"),
                      fg_color=COULEURS["vert"], hover_color="#166638",
                      command=self.nouveau_dossier, width=120).pack(
                          side="right", padx=(8, 0))
        ctk.CTkButton(barre, text=t("btn_ouvrir"),
                      fg_color=COULEURS["accent"], command=self.ouvrir,
                      width=110).pack(side="right", padx=(8, 0))
        ctk.CTkButton(barre, text=t("btn_supprimer"),
                      fg_color=COULEURS["rouge"], hover_color="#922b21",
                      command=self.supprimer, width=110).pack(side="right", padx=(8, 0))

        cadre = ctk.CTkFrame(self, fg_color=COULEURS["carte"], corner_radius=10)
        cadre.pack(fill="both", expand=True, padx=30, pady=(0, 24))

        colonnes = ("reference", "client", "titre", "statut",
                    "total", "paye", "solde")
        self.tableau = ttk.Treeview(cadre, columns=colonnes, show="headings",
                                    selectmode="browse")
        entetes = {
            "reference": t("champ_reference"), "client": t("champ_client"),
            "titre": t("champ_titre"), "statut": t("champ_statut"),
            "total": t("lbl_total_vente"), "paye": t("lbl_total_paye"),
            "solde": t("lbl_solde"),
        }
        largeurs = {"reference": 120, "client": 160, "titre": 170,
                    "statut": 90, "total": 110, "paye": 110, "solde": 110}
        for c in colonnes:
            self.tableau.heading(c, text=entetes[c])
            ancre = "e" if c in ("total", "paye", "solde") else "w"
            self.tableau.column(c, width=largeurs[c], anchor=ancre)

        scroll = ttk.Scrollbar(cadre, orient="vertical", command=self.tableau.yview)
        self.tableau.configure(yscrollcommand=scroll.set)
        self.tableau.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        scroll.pack(side="right", fill="y", pady=10, padx=(0, 10))

        self.tableau.tag_configure("du", foreground=COULEURS["rouge"])
        self.tableau.tag_configure("solde_ok", foreground=COULEURS["vert"])
        self.tableau.bind("<Double-1>", lambda e: self.ouvrir())

    def rafraichir(self):
        for ligne in self.tableau.get_children():
            self.tableau.delete(ligne)
        for d in db.lister_dossiers(self.recherche_var.get().strip()):
            solde = db.get_solde_dossier(d["id"])
            client = f'{d["client_nom"]} {d["client_prenom"] or ""}'.strip()
            tag = "du" if solde["solde"] > 0 else "solde_ok"
            self.tableau.insert("", "end", iid=str(d["id"]), tags=(tag,), values=(
                d["reference"], client, d["titre"] or "", d["statut"] or "",
                formater_montant(solde["total_vente"]),
                formater_montant(solde["total_paye"]),
                formater_montant(solde["solde"])))
        if self.on_changement:
            self.on_changement()

    def _id_selectionne(self):
        sel = self.tableau.selection()
        if not sel:
            info("Info", t("msg_selectionner"))
            return None
        return int(sel[0])

    def nouveau_dossier(self):
        clients = db.lister_clients()
        if not clients:
            erreur("Erreur", "Ajoutez d'abord au moins un client dans l'onglet Clients.")
            return
        # Construit la liste "Nom Prénom (code)" -> id
        options, correspondance = [], {}
        for c in clients:
            libelle = f'{c["nom"]} {c["prenom"] or ""} ({c["code"]})'.strip()
            options.append(libelle)
            correspondance[libelle] = c["id"]

        champs = [
            {"cle": "client", "label": t("champ_client"), "type": "liste",
             "options": options},
            {"cle": "titre", "label": t("champ_titre"), "type": "texte"},
            {"cle": "statut", "label": t("champ_statut"), "type": "liste",
             "options": config.STATUTS_DOSSIER},
            {"cle": "notes", "label": t("champ_notes"), "type": "zone"},
        ]
        dlg = FormulaireDialog(self.winfo_toplevel(),
                               "+ " + t("btn_ajouter") + " — " + t("menu_dossiers"),
                               champs)
        if dlg.resultat is None:
            return
        r = dlg.resultat
        client_id = correspondance.get(r["client"])
        if not client_id:
            erreur("Erreur", t("msg_selectionner"))
            return
        did = db.creer_dossier(client_id, r["titre"], r["statut"], r["notes"])
        self.rafraichir()
        # Ouvre directement le nouveau dossier
        DossierDetail(self.winfo_toplevel(), did, on_fermeture=self.rafraichir)

    def ouvrir(self):
        did = self._id_selectionne()
        if did is None:
            return
        DossierDetail(self.winfo_toplevel(), did, on_fermeture=self.rafraichir)

    def supprimer(self):
        did = self._id_selectionne()
        if did is None:
            return
        d = db.get_dossier(did)
        if confirmer(t("btn_supprimer"),
                     t("msg_confirmer_suppr") + f"\n\n{d['reference']}"):
            db.supprimer_dossier(did)
            self.rafraichir()


# =========================================================================== #
#  DÉTAIL D'UN DOSSIER
# =========================================================================== #
class DossierDetail(ctk.CTkToplevel):
    def __init__(self, parent, dossier_id, on_fermeture=None):
        super().__init__(parent)
        self.dossier_id = dossier_id
        self.on_fermeture = on_fermeture
        self.configure(fg_color=COULEURS["fond"])
        self.geometry("980x680")

        dossier = db.get_dossier(dossier_id)
        self.title(f'{t("menu_dossiers")} — {dossier["reference"]}')

        self._construire(dossier)
        self.rafraichir()

        self.transient(parent)
        self.protocol("WM_DELETE_WINDOW", self._fermer)

    # ---------------------------------------------------------------- #
    def _construire(self, dossier):
        # --- En-tête : infos client + dossier ---
        entete = ctk.CTkFrame(self, fg_color=COULEURS["primaire"], corner_radius=0)
        entete.pack(fill="x")
        client = f'{dossier["client_nom"]} {dossier["client_prenom"] or ""}'.strip()
        ctk.CTkLabel(entete, text=f'{dossier["reference"]}   —   {client}',
                     font=ctk.CTkFont(size=20, weight="bold"),
                     text_color="white").pack(anchor="w", padx=24, pady=(16, 2))
        sous = dossier["titre"] or ""
        if dossier["statut"]:
            sous += f'    •    {t("champ_statut")}: {dossier["statut"]}'
        ctk.CTkLabel(entete, text=sous, font=ctk.CTkFont(size=13),
                     text_color="#cdd8e4").pack(anchor="w", padx=24, pady=(0, 16))

        # --- Bandeau des totaux ---
        self.bandeau = ctk.CTkFrame(self, fg_color=COULEURS["carte"])
        self.bandeau.pack(fill="x", padx=20, pady=(14, 6))
        self.lbl_total = self._mini_stat(self.bandeau, t("lbl_total_vente"), COULEURS["primaire2"])
        self.lbl_paye = self._mini_stat(self.bandeau, t("lbl_total_paye"), COULEURS["vert"])
        self.lbl_solde = self._mini_stat(self.bandeau, t("lbl_solde"), COULEURS["rouge"])

        # Bouton reçu PDF (à droite du bandeau)
        ctk.CTkButton(self.bandeau, text="🧾 " + t("btn_recu_pdf"),
                      fg_color=COULEURS["accent"], height=42,
                      font=ctk.CTkFont(size=13, weight="bold"),
                      command=self.generer_recu).pack(side="right", padx=16, pady=12)

        # --- Deux colonnes : réservations (gauche) / paiements (droite) ---
        corps = ctk.CTkFrame(self, fg_color="transparent")
        corps.pack(fill="both", expand=True, padx=20, pady=(6, 16))
        corps.grid_columnconfigure(0, weight=3)
        corps.grid_columnconfigure(1, weight=2)
        corps.grid_rowconfigure(0, weight=1)

        # ===== Réservations =====
        bloc_r = ctk.CTkFrame(corps, fg_color=COULEURS["carte"], corner_radius=10)
        bloc_r.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        tete_r = ctk.CTkFrame(bloc_r, fg_color="transparent")
        tete_r.pack(fill="x", padx=10, pady=(10, 4))
        ctk.CTkLabel(tete_r, text=t("lbl_reservations"),
                     font=ctk.CTkFont(size=15, weight="bold"),
                     text_color=COULEURS["primaire"]).pack(side="left")
        ctk.CTkButton(tete_r, text="+", width=32, fg_color=COULEURS["vert"],
                      command=self.ajouter_reservation).pack(side="right")
        ctk.CTkButton(tete_r, text="✎", width=32, fg_color=COULEURS["accent"],
                      command=self.modifier_reservation).pack(side="right", padx=6)
        ctk.CTkButton(tete_r, text="🗑", width=32, fg_color=COULEURS["rouge"],
                      command=self.supprimer_reservation).pack(side="right")

        cols_r = ("designation", "prix")
        self.tab_resa = ttk.Treeview(bloc_r, columns=cols_r, show="headings",
                                     selectmode="browse")
        self.tab_resa.heading("designation", text=t("recu_designation"))
        self.tab_resa.heading("prix", text=t("champ_prix_vente"))
        self.tab_resa.column("designation", width=380, anchor="w")
        self.tab_resa.column("prix", width=120, anchor="e")
        self.tab_resa.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.tab_resa.bind("<Double-1>", lambda e: self.modifier_reservation())

        # ===== Paiements =====
        bloc_p = ctk.CTkFrame(corps, fg_color=COULEURS["carte"], corner_radius=10)
        bloc_p.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        tete_p = ctk.CTkFrame(bloc_p, fg_color="transparent")
        tete_p.pack(fill="x", padx=10, pady=(10, 4))
        ctk.CTkLabel(tete_p, text=t("lbl_paiements"),
                     font=ctk.CTkFont(size=15, weight="bold"),
                     text_color=COULEURS["primaire"]).pack(side="left")
        ctk.CTkButton(tete_p, text="+", width=32, fg_color=COULEURS["vert"],
                      command=self.ajouter_paiement).pack(side="right")
        ctk.CTkButton(tete_p, text="🗑", width=32, fg_color=COULEURS["rouge"],
                      command=self.supprimer_paiement).pack(side="right", padx=6)

        cols_p = ("date", "mode", "montant")
        self.tab_paie = ttk.Treeview(bloc_p, columns=cols_p, show="headings",
                                     selectmode="browse")
        self.tab_paie.heading("date", text=t("champ_date_paiement"))
        self.tab_paie.heading("mode", text=t("champ_mode"))
        self.tab_paie.heading("montant", text=t("champ_montant"))
        self.tab_paie.column("date", width=100, anchor="w")
        self.tab_paie.column("mode", width=120, anchor="w")
        self.tab_paie.column("montant", width=110, anchor="e")
        self.tab_paie.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def _mini_stat(self, parent, titre, couleur):
        cadre = ctk.CTkFrame(parent, fg_color="transparent")
        cadre.pack(side="left", padx=20, pady=12)
        ctk.CTkLabel(cadre, text=titre.upper(),
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=COULEURS["gris"]).pack(anchor="w")
        lbl = ctk.CTkLabel(cadre, text="—",
                           font=ctk.CTkFont(size=20, weight="bold"),
                           text_color=couleur)
        lbl.pack(anchor="w")
        return lbl

    # ---------------------------------------------------------------- #
    def rafraichir(self):
        # Réservations
        for l in self.tab_resa.get_children():
            self.tab_resa.delete(l)
        for r in db.lister_reservations(self.dossier_id):
            design = self._designation_courte(r)
            self.tab_resa.insert("", "end", iid=str(r["id"]),
                                 values=(design, formater_montant(r["prix_vente"])))
        # Paiements
        for l in self.tab_paie.get_children():
            self.tab_paie.delete(l)
        for p in db.lister_paiements(self.dossier_id):
            self.tab_paie.insert("", "end", iid=str(p["id"]),
                                 values=(p["date_paiement"], p["mode"] or "",
                                         formater_montant(p["montant"])))
        # Totaux
        s = db.get_solde_dossier(self.dossier_id)
        self.lbl_total.configure(text=formater_montant(s["total_vente"]))
        self.lbl_paye.configure(text=formater_montant(s["total_paye"]))
        couleur = COULEURS["rouge"] if s["solde"] > 0 else COULEURS["vert"]
        self.lbl_solde.configure(text=formater_montant(s["solde"]), text_color=couleur)

    def _designation_courte(self, r):
        parts = []
        if r["type_billet"]:
            parts.append(r["type_billet"])
        if r["compagnie"]:
            parts.append(r["compagnie"])
        if r["ville_depart"] or r["ville_arrivee"]:
            parts.append(f'{r["ville_depart"] or "?"}→{r["ville_arrivee"] or "?"}')
        return "  |  ".join(parts) if parts else "Service"

    # --------- Réservations : formulaire ---------------------------- #
    def _champs_resa(self):
        return [
            {"cle": "type_billet", "label": t("champ_type_billet"), "type": "liste",
             "options": config.TYPES_BILLET},
            {"cle": "compagnie", "label": t("champ_compagnie"), "type": "texte"},
            {"cle": "passager", "label": t("champ_passager"), "type": "texte"},
            {"cle": "ville_depart", "label": t("champ_depart"), "type": "texte"},
            {"cle": "ville_arrivee", "label": t("champ_arrivee"), "type": "texte"},
            {"cle": "date_depart", "label": t("champ_date_depart"), "type": "date"},
            {"cle": "date_retour", "label": t("champ_date_retour"), "type": "date"},
            {"cle": "classe", "label": t("champ_classe"), "type": "liste",
             "options": config.CLASSES_VOYAGE},
            {"cle": "pnr", "label": t("champ_pnr"), "type": "texte"},
            {"cle": "num_billet", "label": t("champ_num_billet"), "type": "texte"},
            {"cle": "prix_vente", "label": t("champ_prix_vente"), "type": "nombre"},
            # --- Champs INTERNES (n'apparaîtront jamais sur le reçu) ---
            {"cle": "gds", "label": t("champ_gds"), "type": "liste",
             "options": [""] + config.GDS},
            {"cle": "consolidateur", "label": t("champ_consolidateur"), "type": "liste",
             "options": [""] + config.CONSOLIDATEURS},
            {"cle": "prix_achat", "label": t("champ_prix_achat"), "type": "nombre"},
            {"cle": "notes", "label": t("champ_notes"), "type": "zone"},
        ]

    def ajouter_reservation(self):
        dlg = FormulaireDialog(self, t("btn_ajouter") + " — " + t("lbl_reservations"),
                               self._champs_resa())
        if dlg.resultat is None:
            return
        r = dlg.resultat
        db.creer_reservation(
            self.dossier_id, r["type_billet"], r["compagnie"], r["pnr"],
            r["num_billet"], r["passager"], r["ville_depart"], r["ville_arrivee"],
            r["date_depart"], r["date_retour"], r["classe"], r["gds"],
            r["consolidateur"], r["prix_achat"], r["prix_vente"], r["notes"])
        self.rafraichir()

    def modifier_reservation(self):
        sel = self.tab_resa.selection()
        if not sel:
            info("Info", t("msg_selectionner"))
            return
        rid = int(sel[0])
        resa = db.get_reservation(rid)
        valeurs = {k: (resa[k] if resa[k] is not None else "") for k in resa.keys()}
        dlg = FormulaireDialog(self, t("btn_modifier") + " — " + t("lbl_reservations"),
                               self._champs_resa(), valeurs)
        if dlg.resultat is None:
            return
        r = dlg.resultat
        db.modifier_reservation(
            rid, r["type_billet"], r["compagnie"], r["pnr"], r["num_billet"],
            r["passager"], r["ville_depart"], r["ville_arrivee"], r["date_depart"],
            r["date_retour"], r["classe"], r["gds"], r["consolidateur"],
            r["prix_achat"], r["prix_vente"], r["notes"])
        self.rafraichir()

    def supprimer_reservation(self):
        sel = self.tab_resa.selection()
        if not sel:
            info("Info", t("msg_selectionner"))
            return
        if confirmer(t("btn_supprimer"), t("msg_confirmer_suppr")):
            db.supprimer_reservation(int(sel[0]))
            self.rafraichir()

    # --------- Paiements : formulaire ------------------------------- #
    def ajouter_paiement(self):
        champs = [
            {"cle": "montant", "label": t("champ_montant") + f" ({config.DEVISE})",
             "type": "nombre"},
            {"cle": "mode", "label": t("champ_mode"), "type": "liste",
             "options": config.MODES_PAIEMENT},
            {"cle": "date_paiement", "label": t("champ_date_paiement"), "type": "date"},
            {"cle": "reference", "label": t("champ_reference"), "type": "texte"},
            {"cle": "notes", "label": t("champ_notes"), "type": "zone"},
        ]
        dlg = FormulaireDialog(self, t("btn_ajouter") + " — " + t("lbl_paiements"), champs)
        if dlg.resultat is None:
            return
        r = dlg.resultat
        if not r["montant"] or r["montant"] <= 0:
            erreur("Erreur", t("msg_montant_invalide"))
            return
        db.creer_paiement(self.dossier_id, r["montant"], r["mode"],
                          r["reference"], r["date_paiement"], r["notes"])
        self.rafraichir()

    def supprimer_paiement(self):
        sel = self.tab_paie.selection()
        if not sel:
            info("Info", t("msg_selectionner"))
            return
        if confirmer(t("btn_supprimer"), t("msg_confirmer_suppr")):
            db.supprimer_paiement(int(sel[0]))
            self.rafraichir()

    # --------- Reçu PDF --------------------------------------------- #
    def generer_recu(self):
        # La version standard exige que le nom de l'agence soit renseigné
        if not settings.est_configure():
            erreur(t("menu_parametres"), t("msg_nom_requis"))
            return
        try:
            chemin = generer_recu(self.dossier_id, ouvrir=True)
            info("PDF", t("msg_recu_genere") + f"\n\n{chemin}")
        except Exception as e:
            erreur("Erreur", f"Impossible de générer le reçu :\n{e}")

    def _fermer(self):
        if self.on_fermeture:
            self.on_fermeture()
        self.destroy()
