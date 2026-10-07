# -*- coding: utf-8 -*-
"""
ui/comptabilite_view.py
------------------------
Écran COMPTABILITÉ (SYSCOHADA / OHADA) — réservé à l'administrateur.

Un seul écran, organisé en ONGLETS :
    Tableau de bord | Grand Livre | Balance | Journaux | Caisse/Banque |
    Résultat | Bilan | TVA | Plan comptable | Écritures (OD) | Exercices

En haut : une période (du / au) et un bouton « Mettre à jour la comptabilité »
qui reconstruit les écritures automatiques à partir des données réelles.
"""

from datetime import datetime, date
from tkinter import ttk
import customtkinter as ctk

import comptabilite as co
import pdf_comptabilite as pdfc
from i18n import t
from pdf_receipt import formater_montant
from ui.helpers import COULEURS, info, erreur, confirmer, CALENDRIER_DISPO

if CALENDRIER_DISPO:
    from tkcalendar import DateEntry


class ComptabiliteView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=COULEURS["fond"])
        co.initialiser_comptabilite()
        # Comptabilité AUTOMATIQUE : on reconstruit les écritures à partir des
        # données réelles dès l'ouverture, sans que l'utilisateur ait à cliquer.
        try:
            co.regenerer_ecritures_auto()
        except Exception:
            pass
        self._construire()
        self.rafraichir_tout()

    # ================================================================== #
    def _construire(self):
        ctk.CTkLabel(self, text=t("compta_titre"),
                     font=ctk.CTkFont(size=24, weight="bold"),
                     text_color=COULEURS["primaire"]).pack(
                         anchor="w", padx=24, pady=(18, 2))
        ctk.CTkLabel(self, text=t("compta_intro"),
                     font=ctk.CTkFont(size=12), text_color=COULEURS["gris"],
                     justify="left").pack(anchor="w", padx=24, pady=(0, 8))

        # --- Barre période + bouton de mise à jour ---
        barre = ctk.CTkFrame(self, fg_color=COULEURS["carte"], corner_radius=10)
        barre.pack(fill="x", padx=24, pady=(0, 8))
        interne = ctk.CTkFrame(barre, fg_color="transparent")
        interne.pack(fill="x", padx=12, pady=10)

        ctk.CTkLabel(interne, text=t("champ_date_debut"),
                     text_color=COULEURS["texte"]).pack(side="left", padx=(0, 4))
        self.w_debut = self._champ_date(interne, date.today().replace(month=1, day=1))
        ctk.CTkLabel(interne, text=t("champ_date_fin"),
                     text_color=COULEURS["texte"]).pack(side="left", padx=(12, 4))
        self.w_fin = self._champ_date(interne, date.today())
        ctk.CTkButton(interne, text="🔎  " + t("btn_afficher"),
                      fg_color=COULEURS["accent"], width=120,
                      command=self.rafraichir_tout).pack(side="left", padx=(12, 0))
        ctk.CTkButton(interne, text="🔄  " + t("btn_maj_compta"),
                      fg_color=COULEURS["vert"], hover_color="#166638",
                      command=self.mettre_a_jour).pack(side="right")

        # --- Onglets ---
        self.tabs = ctk.CTkTabview(self, fg_color=COULEURS["carte"],
                                   segmented_button_selected_color=COULEURS["primaire"])
        self.tabs.pack(fill="both", expand=True, padx=24, pady=(0, 16))

        self.o_tdb = self.tabs.add(t("tab_tdb"))
        self.o_gl = self.tabs.add(t("tab_grand_livre"))
        self.o_bal = self.tabs.add(t("tab_balance"))
        self.o_jrn = self.tabs.add(t("tab_journal"))
        self.o_tre = self.tabs.add(t("tab_caisse"))
        self.o_res = self.tabs.add(t("tab_resultat"))
        self.o_bil = self.tabs.add(t("tab_bilan"))
        self.o_tva = self.tabs.add(t("tab_tva"))
        self.o_plan = self.tabs.add(t("tab_plan"))
        self.o_od = self.tabs.add(t("tab_ecritures"))
        self.o_exo = self.tabs.add(t("tab_exercices"))

        self._build_tdb()
        self._build_grand_livre()
        self._build_balance()
        self._build_journaux()
        self._build_tresorerie()
        self._build_resultat()
        self._build_bilan()
        self._build_tva()
        self._build_plan()
        self._build_od()
        self._build_exercices()

    # ------------------------------------------------------------------ #
    #  Outils dates
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

    def _dates(self):
        return self._lire_date(self.w_debut), self._lire_date(self.w_fin)

    def _tableau(self, parent, colonnes, entetes, largeurs, alignements=None):
        alignements = alignements or {}
        cadre = ctk.CTkFrame(parent, fg_color="transparent")
        cadre.pack(fill="both", expand=True, padx=6, pady=6)
        tv = ttk.Treeview(cadre, columns=colonnes, show="headings", selectmode="browse")
        for c in colonnes:
            tv.heading(c, text=entetes[c])
            tv.column(c, width=largeurs[c], anchor=alignements.get(c, "w"))
        scroll = ttk.Scrollbar(cadre, orient="vertical", command=tv.yview)
        tv.configure(yscrollcommand=scroll.set)
        tv.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        return tv

    def _vider(self, tv):
        for l in tv.get_children():
            tv.delete(l)

    # ================================================================== #
    #  Actions globales
    # ================================================================== #
    def mettre_a_jour(self):
        nb = co.regenerer_ecritures_auto()
        info("Info", f'{t("msg_compta_maj")} {nb} {t("msg_compta_ecritures")}')
        self.rafraichir_tout()

    def rafraichir_tout(self):
        self._maj_tdb()
        self._maj_grand_livre()
        self._maj_balance()
        self._maj_journaux()
        self._maj_tresorerie()
        self._maj_resultat()
        self._maj_bilan()
        self._maj_tva()
        self._maj_plan()
        self._maj_od()
        self._maj_exercices()

    # ================================================================== #
    #  Onglet TABLEAU DE BORD
    # ================================================================== #
    def _build_tdb(self):
        self.tdb_cartes = {}
        grille = ctk.CTkFrame(self.o_tdb, fg_color="transparent")
        grille.pack(fill="both", expand=True, padx=10, pady=10)
        defs = [
            ("chiffre_affaires", t("tdb_ca"), "#8e44ad"),
            ("total_produits", t("tdb_produits"), COULEURS["vert"]),
            ("total_charges", t("tdb_charges"), COULEURS["rouge"]),
            ("resultat", t("tdb_resultat"), "#e67e22"),
            ("solde_caisse", t("tdb_caisse"), COULEURS["accent"]),
            ("solde_banque", t("tdb_banque"), COULEURS["primaire2"]),
            ("creances_clients", t("tdb_creances"), "#16a085"),
            ("dettes_fournisseurs", t("tdb_dettes"), "#c0392b"),
        ]
        for i, (cle, titre, couleur) in enumerate(defs):
            carte = ctk.CTkFrame(grille, fg_color=COULEURS["fond"], corner_radius=12)
            carte.grid(row=i // 4, column=i % 4, padx=8, pady=8, sticky="nsew")
            grille.grid_columnconfigure(i % 4, weight=1)
            ctk.CTkLabel(carte, text=titre.upper(),
                         font=ctk.CTkFont(size=11, weight="bold"),
                         text_color=COULEURS["gris"]).pack(anchor="w", padx=12, pady=(12, 0))
            lbl = ctk.CTkLabel(carte, text="—",
                               font=ctk.CTkFont(size=20, weight="bold"),
                               text_color=couleur)
            lbl.pack(anchor="w", padx=12, pady=(2, 12))
            self.tdb_cartes[cle] = lbl

    def _maj_tdb(self):
        d, f = self._dates()
        stats = co.tableau_de_bord(d, f)
        for cle, lbl in self.tdb_cartes.items():
            lbl.configure(text=formater_montant(stats[cle]))

    # ================================================================== #
    #  Onglet GRAND LIVRE
    # ================================================================== #
    def _build_grand_livre(self):
        haut = ctk.CTkFrame(self.o_gl, fg_color="transparent")
        haut.pack(fill="x", padx=6, pady=6)
        ctk.CTkLabel(haut, text=t("col_compte"),
                     text_color=COULEURS["texte"]).pack(side="left", padx=(0, 4))
        comptes = [t("tous_les_comptes")] + [
            f'{c["numero"]} - {c["intitule"]}' for c in co.lister_comptes()]
        self.gl_var_compte = ctk.StringVar(value=comptes[0])
        ctk.CTkOptionMenu(haut, values=comptes, variable=self.gl_var_compte,
                          width=260,
                          fg_color=COULEURS["primaire"],
                          button_color=COULEURS["primaire2"]).pack(side="left")
        ctk.CTkButton(haut, text="🔎  " + t("btn_afficher"), width=110,
                      fg_color=COULEURS["accent"],
                      command=self._maj_grand_livre).pack(side="left", padx=(10, 0))
        ctk.CTkButton(haut, text="📄  PDF", width=90,
                      fg_color=COULEURS["vert"], hover_color="#166638",
                      command=self._pdf_grand_livre).pack(side="right")

        cols = ("compte", "date", "piece", "journal", "libelle", "debit", "credit", "solde")
        ent = {"compte": t("col_compte"), "date": t("recu_date"),
               "piece": t("col_piece"), "journal": t("col_journal_c"),
               "libelle": t("col_libelle"), "debit": t("col_debit"),
               "credit": t("col_credit"), "solde": t("col_solde")}
        larg = {"compte": 70, "date": 80, "piece": 100, "journal": 60,
                "libelle": 230, "debit": 95, "credit": 95, "solde": 100}
        ali = {"debit": "e", "credit": "e", "solde": "e"}
        self.gl_tv = self._tableau(self.o_gl, cols, ent, larg, ali)

    def _gl_compte_choisi(self):
        val = self.gl_var_compte.get()
        if val == t("tous_les_comptes"):
            return None
        return val.split(" - ")[0]

    def _maj_grand_livre(self):
        d, f = self._dates()
        self._vider(self.gl_tv)
        for l in co.grand_livre(self._gl_compte_choisi(), d, f):
            self.gl_tv.insert("", "end", values=(
                l["compte"], l["date"], l["num_piece"], l["journal"],
                l["libelle"][:45], formater_montant(l["debit"]) if l["debit"] else "",
                formater_montant(l["credit"]) if l["credit"] else "",
                formater_montant(l["solde"])))

    def _pdf_grand_livre(self):
        d, f = self._dates()
        try:
            chemin = pdfc.generer_grand_livre(self._gl_compte_choisi(), d, f, ouvrir=True)
            info("Info", f'{t("msg_pdf_genere")}\n{chemin}')
        except Exception as e:
            erreur("Erreur", str(e))

    # ================================================================== #
    #  Onglet BALANCE
    # ================================================================== #
    def _build_balance(self):
        haut = ctk.CTkFrame(self.o_bal, fg_color="transparent")
        haut.pack(fill="x", padx=6, pady=6)
        ctk.CTkButton(haut, text="📄  PDF", width=90,
                      fg_color=COULEURS["vert"], hover_color="#166638",
                      command=self._pdf_balance).pack(side="right")
        cols = ("compte", "intitule", "td", "tc", "sd", "sc")
        ent = {"compte": t("col_compte"), "intitule": t("col_intitule"),
               "td": t("col_debit"), "tc": t("col_credit"),
               "sd": t("col_solde_d"), "sc": t("col_solde_c")}
        larg = {"compte": 70, "intitule": 250, "td": 100, "tc": 100, "sd": 110, "sc": 110}
        ali = {"td": "e", "tc": "e", "sd": "e", "sc": "e"}
        self.bal_tv = self._tableau(self.o_bal, cols, ent, larg, ali)

    def _maj_balance(self):
        d, f = self._dates()
        self._vider(self.bal_tv)
        for b in co.balance(d, f):
            self.bal_tv.insert("", "end", values=(
                b["compte"], b["intitule"][:48],
                formater_montant(b["total_debit"]), formater_montant(b["total_credit"]),
                formater_montant(b["solde_debiteur"]), formater_montant(b["solde_crediteur"])))

    def _pdf_balance(self):
        d, f = self._dates()
        try:
            chemin = pdfc.generer_balance(d, f, ouvrir=True)
            info("Info", f'{t("msg_pdf_genere")}\n{chemin}')
        except Exception as e:
            erreur("Erreur", str(e))

    # ================================================================== #
    #  Onglet JOURNAUX
    # ================================================================== #
    def _build_journaux(self):
        haut = ctk.CTkFrame(self.o_jrn, fg_color="transparent")
        haut.pack(fill="x", padx=6, pady=6)
        ctk.CTkLabel(haut, text=t("col_journal_c"),
                     text_color=COULEURS["texte"]).pack(side="left", padx=(0, 4))
        self._journaux = co.lister_journaux()
        vals = [f'{j["code"]} - {j["libelle"]}' for j in self._journaux]
        self.jrn_var = ctk.StringVar(value=vals[0] if vals else "")
        ctk.CTkOptionMenu(haut, values=vals, variable=self.jrn_var, width=260,
                          command=lambda _: self._maj_journaux(),
                          fg_color=COULEURS["primaire"],
                          button_color=COULEURS["primaire2"]).pack(side="left")
        ctk.CTkButton(haut, text="📄  PDF", width=90,
                      fg_color=COULEURS["vert"], hover_color="#166638",
                      command=self._pdf_journal).pack(side="right")

        cols = ("date", "piece", "libelle", "debit", "credit")
        ent = {"date": t("recu_date"), "piece": t("col_piece"),
               "libelle": t("col_libelle"), "debit": t("col_debit"),
               "credit": t("col_credit")}
        larg = {"date": 90, "piece": 120, "libelle": 380, "debit": 110, "credit": 110}
        ali = {"debit": "e", "credit": "e"}
        self.jrn_tv = self._tableau(self.o_jrn, cols, ent, larg, ali)

    def _jrn_code(self):
        v = self.jrn_var.get()
        return v.split(" - ")[0] if v else None

    def _maj_journaux(self):
        d, f = self._dates()
        self._vider(self.jrn_tv)
        code = self._jrn_code()
        if not code:
            return
        for e in co.lister_ecritures(code, d, f):
            for i, l in enumerate(co.lignes_de_ecriture(e["id"])):
                self.jrn_tv.insert("", "end", values=(
                    (e["date_ecriture"] or "") if i == 0 else "",
                    (e["num_piece"] or "") if i == 0 else "",
                    f'{l["compte"]}  {l["libelle"][:40]}',
                    formater_montant(l["debit"]) if l["debit"] else "",
                    formater_montant(l["credit"]) if l["credit"] else ""))

    def _pdf_journal(self):
        d, f = self._dates()
        try:
            chemin = pdfc.generer_journal(self._jrn_code(), d, f, ouvrir=True)
            info("Info", f'{t("msg_pdf_genere")}\n{chemin}')
        except Exception as e:
            erreur("Erreur", str(e))

    # ================================================================== #
    #  Onglet CAISSE / BANQUE
    # ================================================================== #
    def _build_tresorerie(self):
        self.tre_labels = {}
        conteneur = ctk.CTkFrame(self.o_tre, fg_color="transparent")
        conteneur.pack(fill="both", expand=True, padx=10, pady=10)
        for compte, titre in (("571", "Caisse (571)"), ("521", "Banque (521)")):
            bloc = ctk.CTkFrame(conteneur, fg_color=COULEURS["fond"], corner_radius=12)
            bloc.pack(fill="x", pady=8)
            ctk.CTkLabel(bloc, text=titre,
                         font=ctk.CTkFont(size=16, weight="bold"),
                         text_color=COULEURS["primaire"]).pack(anchor="w", padx=16, pady=(12, 4))
            grille = ctk.CTkFrame(bloc, fg_color="transparent")
            grille.pack(fill="x", padx=16, pady=(0, 8))
            lbls = {}
            for cle, lib in (("entrees", "Encaissements"), ("sorties", "Décaissements"),
                             ("solde_final", "Solde final")):
                cadre = ctk.CTkFrame(grille, fg_color="transparent")
                cadre.pack(side="left", expand=True, fill="x")
                ctk.CTkLabel(cadre, text=lib.upper(),
                             font=ctk.CTkFont(size=10, weight="bold"),
                             text_color=COULEURS["gris"]).pack(anchor="w")
                v = ctk.CTkLabel(cadre, text="—",
                                 font=ctk.CTkFont(size=17, weight="bold"),
                                 text_color=COULEURS["texte"])
                v.pack(anchor="w")
                lbls[cle] = v
            ctk.CTkButton(bloc, text="📄  PDF", width=90,
                          fg_color=COULEURS["vert"], hover_color="#166638",
                          command=lambda c=compte: self._pdf_tresorerie(c)).pack(
                              anchor="e", padx=16, pady=(0, 12))
            self.tre_labels[compte] = lbls

    def _maj_tresorerie(self):
        d, f = self._dates()
        for compte, lbls in self.tre_labels.items():
            e = co.etat_tresorerie(compte, d, f)
            lbls["entrees"].configure(text=formater_montant(e["entrees"]))
            lbls["sorties"].configure(text=formater_montant(e["sorties"]))
            lbls["solde_final"].configure(text=formater_montant(e["solde_final"]),
                                          text_color=COULEURS["primaire"])

    def _pdf_tresorerie(self, compte):
        d, f = self._dates()
        try:
            chemin = pdfc.generer_etat_tresorerie(compte, d, f, ouvrir=True)
            info("Info", f'{t("msg_pdf_genere")}\n{chemin}')
        except Exception as e:
            erreur("Erreur", str(e))

    # ================================================================== #
    #  Onglet RÉSULTAT
    # ================================================================== #
    def _build_resultat(self):
        haut = ctk.CTkFrame(self.o_res, fg_color="transparent")
        haut.pack(fill="x", padx=6, pady=6)
        ctk.CTkButton(haut, text="📄  PDF", width=90,
                      fg_color=COULEURS["vert"], hover_color="#166638",
                      command=self._pdf_resultat).pack(side="right")
        cols = ("type", "compte", "intitule", "montant")
        ent = {"type": t("col_nature"), "compte": t("col_compte"),
               "intitule": t("col_intitule"), "montant": t("champ_montant")}
        larg = {"type": 110, "compte": 70, "intitule": 300, "montant": 140}
        ali = {"montant": "e"}
        self.res_tv = self._tableau(self.o_res, cols, ent, larg, ali)
        self.res_total = ctk.CTkLabel(self.o_res, text="",
                                      font=ctk.CTkFont(size=15, weight="bold"),
                                      text_color=COULEURS["primaire"])
        self.res_total.pack(anchor="e", padx=12, pady=(0, 8))

    def _maj_resultat(self):
        d, f = self._dates()
        r = co.compte_de_resultat(d, f)
        self._vider(self.res_tv)
        for p in r["produits"]:
            self.res_tv.insert("", "end", values=(
                t("res_produits"), p["compte"], p["intitule"][:55],
                formater_montant(p["montant"])))
        for c in r["charges"]:
            self.res_tv.insert("", "end", values=(
                t("res_charges"), c["compte"], c["intitule"][:55],
                formater_montant(c["montant"])))
        couleur = COULEURS["vert"] if r["resultat"] >= 0 else COULEURS["rouge"]
        self.res_total.configure(
            text=f'{t("res_total_produits")}: {formater_montant(r["total_produits"])}   |   '
                 f'{t("res_total_charges")}: {formater_montant(r["total_charges"])}   |   '
                 f'{t("res_resultat")}: {formater_montant(r["resultat"])}',
            text_color=couleur)

    def _pdf_resultat(self):
        d, f = self._dates()
        try:
            chemin = pdfc.generer_resultat(d, f, ouvrir=True)
            info("Info", f'{t("msg_pdf_genere")}\n{chemin}')
        except Exception as e:
            erreur("Erreur", str(e))

    # ================================================================== #
    #  Onglet BILAN
    # ================================================================== #
    def _build_bilan(self):
        haut = ctk.CTkFrame(self.o_bil, fg_color="transparent")
        haut.pack(fill="x", padx=6, pady=6)
        ctk.CTkButton(haut, text="📄  PDF", width=90,
                      fg_color=COULEURS["vert"], hover_color="#166638",
                      command=self._pdf_bilan).pack(side="right")
        cols = ("cote", "compte", "intitule", "montant")
        ent = {"cote": t("col_nature"), "compte": t("col_compte"),
               "intitule": t("col_intitule"), "montant": t("champ_montant")}
        larg = {"cote": 90, "compte": 70, "intitule": 320, "montant": 140}
        ali = {"montant": "e"}
        self.bil_tv = self._tableau(self.o_bil, cols, ent, larg, ali)
        self.bil_total = ctk.CTkLabel(self.o_bil, text="",
                                      font=ctk.CTkFont(size=15, weight="bold"),
                                      text_color=COULEURS["primaire"])
        self.bil_total.pack(anchor="e", padx=12, pady=(0, 8))

    def _maj_bilan(self):
        d, f = self._dates()
        b = co.bilan(d, f)
        self._vider(self.bil_tv)
        for a in b["actif"]:
            self.bil_tv.insert("", "end", values=(
                t("bilan_actif"), a["compte"], a["intitule"][:58],
                formater_montant(a["montant"])))
        for p in b["passif"]:
            self.bil_tv.insert("", "end", values=(
                t("bilan_passif"), p["compte"], p["intitule"][:58],
                formater_montant(p["montant"])))
        self.bil_total.configure(
            text=f'{t("bilan_total_actif")}: {formater_montant(b["total_actif"])}   |   '
                 f'{t("bilan_total_passif")}: {formater_montant(b["total_passif"])}')

    def _pdf_bilan(self):
        d, f = self._dates()
        try:
            chemin = pdfc.generer_bilan(d, f, ouvrir=True)
            info("Info", f'{t("msg_pdf_genere")}\n{chemin}')
        except Exception as e:
            erreur("Erreur", str(e))

    # ================================================================== #
    #  Onglet TVA
    # ================================================================== #
    def _build_tva(self):
        self.tva_labels = {}
        conteneur = ctk.CTkFrame(self.o_tva, fg_color="transparent")
        conteneur.pack(fill="both", expand=True, padx=14, pady=14)
        for cle, lib in (("tva_collectee", t("tva_collectee")),
                         ("tva_deductible", t("tva_deductible")),
                         ("tva_a_payer", t("tva_a_payer")),
                         ("credit_tva", t("tva_credit"))):
            ligne = ctk.CTkFrame(conteneur, fg_color=COULEURS["fond"], corner_radius=10)
            ligne.pack(fill="x", pady=6)
            ctk.CTkLabel(ligne, text=lib, font=ctk.CTkFont(size=13, weight="bold"),
                         text_color=COULEURS["texte"]).pack(side="left", padx=16, pady=12)
            v = ctk.CTkLabel(ligne, text="—", font=ctk.CTkFont(size=16, weight="bold"),
                             text_color=COULEURS["primaire"])
            v.pack(side="right", padx=16)
            self.tva_labels[cle] = v
        ctk.CTkLabel(conteneur, text="ℹ  " + t("tva_note"),
                     font=ctk.CTkFont(size=11), text_color=COULEURS["gris"],
                     wraplength=600, justify="left").pack(anchor="w", pady=(10, 0))

    def _maj_tva(self):
        d, f = self._dates()
        e = co.etat_tva(d, f)
        self.tva_labels["tva_collectee"].configure(text=formater_montant(e["tva_collectee"]))
        self.tva_labels["tva_deductible"].configure(text=formater_montant(e["tva_deductible"]))
        self.tva_labels["tva_a_payer"].configure(text=formater_montant(e["tva_a_payer"]))
        self.tva_labels["credit_tva"].configure(text=formater_montant(e["credit_tva"]))

    # ================================================================== #
    #  Onglet PLAN COMPTABLE
    # ================================================================== #
    def _build_plan(self):
        cols = ("numero", "intitule", "classe", "nature")
        ent = {"numero": t("col_compte"), "intitule": t("col_intitule"),
               "classe": t("col_classe"), "nature": t("col_nature")}
        larg = {"numero": 90, "intitule": 340, "classe": 80, "nature": 120}
        self.plan_tv = self._tableau(self.o_plan, cols, ent, larg)

    def _maj_plan(self):
        self._vider(self.plan_tv)
        for c in co.lister_comptes():
            self.plan_tv.insert("", "end", values=(
                c["numero"], c["intitule"], c["classe"] or "", c["nature"] or ""))

    # ================================================================== #
    #  Onglet ÉCRITURES (OD) — saisie manuelle
    # ================================================================== #
    def _build_od(self):
        haut = ctk.CTkFrame(self.o_od, fg_color="transparent")
        haut.pack(fill="x", padx=6, pady=6)
        ctk.CTkButton(haut, text="➕  " + t("btn_nouvelle_ecriture"),
                      fg_color=COULEURS["vert"], hover_color="#166638",
                      command=self._nouvelle_od).pack(side="left")
        ctk.CTkButton(haut, text="🗑  " + t("btn_supprimer"),
                      fg_color=COULEURS["rouge"], hover_color="#922b21",
                      command=self._supprimer_od).pack(side="right")
        cols = ("date", "piece", "libelle", "montant")
        ent = {"date": t("recu_date"), "piece": t("col_piece"),
               "libelle": t("col_libelle"), "montant": t("champ_montant")}
        larg = {"date": 90, "piece": 120, "libelle": 400, "montant": 120}
        ali = {"montant": "e"}
        self.od_tv = self._tableau(self.o_od, cols, ent, larg, ali)
        self._od_ids = {}

    def _maj_od(self):
        d, f = self._dates()
        self._vider(self.od_tv)
        self._od_ids = {}
        for e in co.lister_ecritures("OD", d, f):
            item = self.od_tv.insert("", "end", values=(
                e["date_ecriture"], e["num_piece"] or "", e["libelle"] or "",
                formater_montant(e["total"])))
            self._od_ids[item] = e["id"]

    def _nouvelle_od(self):
        dlg = _DialogueEcritureOD(self)
        if dlg.resultat is None:
            return
        r = dlg.resultat
        try:
            co.creer_ecriture(r["date"], "OD", r["libelle"], r["lignes"],
                              source_type="manuel")
            info("Info", t("msg_enregistre"))
            self.rafraichir_tout()
        except ValueError as e:
            erreur("Erreur", str(e))

    def _supprimer_od(self):
        sel = self.od_tv.selection()
        if not sel:
            info("Info", t("msg_selectionner"))
            return
        if not confirmer(t("btn_supprimer"), t("msg_confirmer_suppr")):
            return
        co.supprimer_ecriture(self._od_ids.get(sel[0]))
        self.rafraichir_tout()

    # ================================================================== #
    #  Onglet EXERCICES
    # ================================================================== #
    def _build_exercices(self):
        haut = ctk.CTkFrame(self.o_exo, fg_color="transparent")
        haut.pack(fill="x", padx=6, pady=6)
        ctk.CTkButton(haut, text="➕  " + t("btn_nouvel_exercice"),
                      fg_color=COULEURS["vert"], hover_color="#166638",
                      command=self._nouvel_exercice).pack(side="left")
        ctk.CTkButton(haut, text="🔒  " + t("btn_cloturer") + " / " + t("btn_rouvrir"),
                      fg_color=COULEURS["gris"], hover_color="#555",
                      command=self._basculer_cloture).pack(side="right")
        cols = ("libelle", "debut", "fin", "etat")
        ent = {"libelle": t("champ_libelle"), "debut": t("champ_date_debut"),
               "fin": t("champ_date_fin"), "etat": t("col_cloture")}
        larg = {"libelle": 260, "debut": 130, "fin": 130, "etat": 120}
        self.exo_tv = self._tableau(self.o_exo, cols, ent, larg)
        self._exo_ids = {}

    def _maj_exercices(self):
        self._vider(self.exo_tv)
        self._exo_ids = {}
        for e in co.lister_exercices():
            etat = t("exo_cloture") if e["cloture"] else t("exo_ouvert")
            item = self.exo_tv.insert("", "end", values=(
                e["libelle"] or "", e["date_debut"] or "", e["date_fin"] or "", etat))
            self._exo_ids[item] = e["id"]

    def _nouvel_exercice(self):
        dlg = _DialogueExercice(self)
        if dlg.resultat is None:
            return
        r = dlg.resultat
        co.creer_exercice(r["libelle"], r["debut"], r["fin"])
        self._maj_exercices()

    def _basculer_cloture(self):
        sel = self.exo_tv.selection()
        if not sel:
            info("Info", t("msg_selectionner"))
            return
        eid = self._exo_ids.get(sel[0])
        exos = {e["id"]: e for e in co.lister_exercices()}
        e = exos.get(eid)
        if e is None:
            return
        co.cloturer_exercice(eid, cloture=0 if e["cloture"] else 1)
        self._maj_exercices()


# ===========================================================================
#  Dialogue : nouvelle écriture manuelle (OD)
# ===========================================================================
class _DialogueEcritureOD(ctk.CTkToplevel):
    """Saisie d'une écriture au journal OD (jusqu'à 6 lignes).
    L'écriture n'est acceptée que si Total Débit = Total Crédit."""

    NB_LIGNES = 6

    def __init__(self, parent):
        super().__init__(parent)
        self.resultat = None
        self.title(t("btn_nouvelle_ecriture"))
        self.configure(fg_color=COULEURS["fond"])
        self.geometry("640x520")

        ctk.CTkLabel(self, text=t("btn_nouvelle_ecriture"),
                     font=ctk.CTkFont(size=18, weight="bold"),
                     text_color=COULEURS["primaire"]).pack(padx=20, pady=(16, 6), anchor="w")

        entete = ctk.CTkFrame(self, fg_color="transparent")
        entete.pack(fill="x", padx=20)
        ctk.CTkLabel(entete, text=t("recu_date"),
                     text_color=COULEURS["texte"]).pack(side="left")
        self.e_date = ctk.CTkEntry(entete, width=120)
        self.e_date.insert(0, date.today().strftime("%Y-%m-%d"))
        self.e_date.pack(side="left", padx=(4, 14))
        ctk.CTkLabel(entete, text=t("col_libelle"),
                     text_color=COULEURS["texte"]).pack(side="left")
        self.e_libelle = ctk.CTkEntry(entete, width=280)
        self.e_libelle.pack(side="left", padx=(4, 0))

        # Titres des colonnes
        titres = ctk.CTkFrame(self, fg_color="transparent")
        titres.pack(fill="x", padx=20, pady=(12, 0))
        for txt, w in ((t("col_compte"), 90), (t("col_libelle"), 230),
                       (t("col_debit"), 110), (t("col_credit"), 110)):
            ctk.CTkLabel(titres, text=txt, width=w,
                         font=ctk.CTkFont(size=11, weight="bold"),
                         text_color=COULEURS["gris"], anchor="w").pack(side="left")

        self.lignes = []
        zone = ctk.CTkFrame(self, fg_color="transparent")
        zone.pack(fill="x", padx=20, pady=4)
        for _ in range(self.NB_LIGNES):
            l = ctk.CTkFrame(zone, fg_color="transparent")
            l.pack(fill="x", pady=2)
            e_cpt = ctk.CTkEntry(l, width=90); e_cpt.pack(side="left")
            e_lib = ctk.CTkEntry(l, width=230); e_lib.pack(side="left", padx=(0, 0))
            e_deb = ctk.CTkEntry(l, width=110); e_deb.pack(side="left")
            e_cre = ctk.CTkEntry(l, width=110); e_cre.pack(side="left")
            self.lignes.append((e_cpt, e_lib, e_deb, e_cre))

        barre = ctk.CTkFrame(self, fg_color="transparent")
        barre.pack(fill="x", padx=20, pady=(12, 16))
        ctk.CTkButton(barre, text=t("btn_annuler"), fg_color=COULEURS["gris"],
                      hover_color="#555", width=110,
                      command=self._annuler).pack(side="right", padx=(8, 0))
        ctk.CTkButton(barre, text=t("btn_enregistrer"), fg_color=COULEURS["vert"],
                      hover_color="#166638", width=140,
                      command=self._valider).pack(side="right")

        self.update_idletasks()
        self.transient(parent)
        self.grab_set()
        self.wait_window(self)

    def _nombre(self, texte):
        texte = (texte or "").strip().replace(" ", "").replace(",", ".")
        if not texte:
            return 0
        try:
            return float(texte)
        except ValueError:
            return None

    def _valider(self):
        lignes = []
        for e_cpt, e_lib, e_deb, e_cre in self.lignes:
            compte = e_cpt.get().strip()
            if not compte:
                continue
            deb = self._nombre(e_deb.get())
            cre = self._nombre(e_cre.get())
            if deb is None or cre is None:
                erreur("Erreur", t("msg_montant_invalide"))
                return
            lignes.append({"compte": compte, "libelle": e_lib.get().strip(),
                           "debit": deb, "credit": cre})
        if not lignes:
            erreur("Erreur", t("msg_champs_requis"))
            return
        self.resultat = {"date": self.e_date.get().strip(),
                         "libelle": self.e_libelle.get().strip(),
                         "lignes": lignes}
        self.grab_release()
        self.destroy()

    def _annuler(self):
        self.resultat = None
        self.grab_release()
        self.destroy()


# ===========================================================================
#  Dialogue : nouvel exercice
# ===========================================================================
class _DialogueExercice(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.resultat = None
        self.title(t("btn_nouvel_exercice"))
        self.configure(fg_color=COULEURS["fond"])
        self.resizable(False, False)

        ctk.CTkLabel(self, text=t("btn_nouvel_exercice"),
                     font=ctk.CTkFont(size=18, weight="bold"),
                     text_color=COULEURS["primaire"]).pack(padx=20, pady=(16, 8), anchor="w")
        zone = ctk.CTkFrame(self, fg_color=COULEURS["carte"], corner_radius=12)
        zone.pack(fill="both", expand=True, padx=20, pady=6)

        annee = date.today().year
        self.e_lib = self._champ(zone, t("champ_libelle"), f"Exercice {annee}")
        self.e_debut = self._champ(zone, t("champ_date_debut"), f"{annee}-01-01")
        self.e_fin = self._champ(zone, t("champ_date_fin"), f"{annee}-12-31")

        barre = ctk.CTkFrame(self, fg_color="transparent")
        barre.pack(fill="x", padx=20, pady=(8, 16))
        ctk.CTkButton(barre, text=t("btn_annuler"), fg_color=COULEURS["gris"],
                      hover_color="#555", width=110,
                      command=self._annuler).pack(side="right", padx=(8, 0))
        ctk.CTkButton(barre, text=t("btn_enregistrer"), fg_color=COULEURS["vert"],
                      hover_color="#166638", width=140,
                      command=self._valider).pack(side="right")

        self.update_idletasks()
        self.transient(parent)
        self.grab_set()
        self.wait_window(self)

    def _champ(self, parent, label, valeur=""):
        ctk.CTkLabel(parent, text=label, font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=COULEURS["texte"], anchor="w").pack(
                         fill="x", padx=16, pady=(8, 0))
        e = ctk.CTkEntry(parent)
        if valeur:
            e.insert(0, valeur)
        e.pack(fill="x", padx=16, pady=(2, 2))
        return e

    def _valider(self):
        if not self.e_lib.get().strip():
            erreur("Erreur", t("msg_champs_requis"))
            return
        self.resultat = {"libelle": self.e_lib.get().strip(),
                         "debut": self.e_debut.get().strip(),
                         "fin": self.e_fin.get().strip()}
        self.grab_release()
        self.destroy()

    def _annuler(self):
        self.resultat = None
        self.grab_release()
        self.destroy()
