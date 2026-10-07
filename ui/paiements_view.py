# -*- coding: utf-8 -*-
"""
ui/paiements_view.py
--------------------
Module 💰 PAIEMENTS (transversal) : tous les paiements de l'agence, tous
dossiers/opérations confondus. On peut ajouter un paiement (en choisissant le
client puis l'opération à régler) ou en supprimer un.
"""

import tkinter as tk
from tkinter import ttk
import customtkinter as ctk

import config
import database as db
import activites as act
from ui.helpers import COULEURS, confirmer, info, erreur
from ui.operation_dialog import formater

try:
    from tkcalendar import DateEntry
    CAL = True
except Exception:
    CAL = False


class PaiementsView(ctk.CTkFrame):
    def __init__(self, parent, on_changement=None):
        super().__init__(parent, fg_color=COULEURS["fond"])
        self.on_changement = on_changement
        self._construire()
        self.rafraichir()

    def _construire(self):
        ctk.CTkLabel(self, text="💰  Paiements",
                     font=ctk.CTkFont(size=26, weight="bold"),
                     text_color=COULEURS["primaire"]).pack(
                         anchor="w", padx=30, pady=(26, 10))

        barre = ctk.CTkFrame(self, fg_color="transparent")
        barre.pack(fill="x", padx=30, pady=(0, 10))
        self.recherche_var = ctk.StringVar()
        e = ctk.CTkEntry(barre, placeholder_text="Rechercher (client, référence, mode)…",
                         textvariable=self.recherche_var, width=280)
        e.pack(side="left")
        e.bind("<KeyRelease>", lambda ev: self.rafraichir())
        ctk.CTkButton(barre, text="+ Nouveau paiement", fg_color=COULEURS["vert"],
                      hover_color="#166638", command=self.ajouter).pack(
                          side="right", padx=(6, 0))
        ctk.CTkButton(barre, text="Supprimer", fg_color=COULEURS["rouge"],
                      hover_color="#922b21", command=self.supprimer).pack(
                          side="right", padx=(6, 0))

        cadre = ctk.CTkFrame(self, fg_color=COULEURS["carte"], corner_radius=10)
        cadre.pack(fill="both", expand=True, padx=30, pady=(0, 24))
        cols = ("date", "client", "objet", "mode", "reference", "montant")
        entetes = {"date": "Date", "client": "Client", "objet": "Opération",
                   "mode": "Mode", "reference": "Référence", "montant": "Montant"}
        largeurs = {"date": 100, "client": 170, "objet": 150, "mode": 110,
                    "reference": 140, "montant": 120}
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

    def _objet(self, p):
        if p["operation_type"]:
            libelle = act.ACTIVITES.get(p["operation_type"], (None, p["operation_type"]))[1]
            return f'{libelle} #{p["operation_id"]}'
        if p["dossier_id"]:
            return f'Dossier #{p["dossier_id"]}'
        return "—"

    def rafraichir(self):
        for l in self.tableau.get_children():
            self.tableau.delete(l)
        for p in db.lister_tous_paiements(self.recherche_var.get().strip()):
            client = f'{p["client_nom"] or ""} {p["client_prenom"] or ""}'.strip() or "—"
            self.tableau.insert("", "end", iid=str(p["id"]), values=(
                (p["date_paiement"] or "")[:10], client, self._objet(p),
                p["mode"] or "", p["reference"] or "", formater(p["montant"])))
        if self.on_changement:
            self.on_changement()

    def supprimer(self):
        sel = self.tableau.selection()
        if not sel:
            info("Info", "Sélectionnez un paiement.")
            return
        if confirmer("Supprimer", "Supprimer ce paiement ?"):
            db.supprimer_paiement_operation(int(sel[0]))
            self.rafraichir()

    def ajouter(self):
        dlg = _DialoguePaiement(self.winfo_toplevel())
        if dlg.enregistre:
            self.rafraichir()


class _DialoguePaiement(ctk.CTkToplevel):
    """Choisir un client -> une de ses opérations -> saisir le paiement."""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("Nouveau paiement")
        self.enregistre = False
        self.client_id = None
        self._operations = []
        self.configure(fg_color=COULEURS["fond"])
        self.geometry("560x620")

        ctk.CTkLabel(self, text="💰  Nouveau paiement",
                     font=ctk.CTkFont(size=18, weight="bold"),
                     text_color=COULEURS["primaire"]).pack(anchor="w", padx=18, pady=(16, 6))

        # 1) Client
        ctk.CTkLabel(self, text="1) Client", font=ctk.CTkFont(size=13, weight="bold"),
                     anchor="w").pack(fill="x", padx=18)
        self.rech = ctk.StringVar()
        e = ctk.CTkEntry(self, placeholder_text="Rechercher un client…",
                         textvariable=self.rech)
        e.pack(fill="x", padx=18, pady=(2, 4))
        e.bind("<KeyRelease>", lambda ev: self._maj_clients())
        self.tab = ttk.Treeview(self, columns=("code", "nom"), show="headings",
                                selectmode="browse", height=4)
        self.tab.heading("code", text="Code"); self.tab.column("code", width=90)
        self.tab.heading("nom", text="Nom"); self.tab.column("nom", width=380)
        self.tab.pack(fill="x", padx=18)
        self.tab.bind("<<TreeviewSelect>>", self._choisir_client)

        # 2) Opération
        ctk.CTkLabel(self, text="2) Opération à régler",
                     font=ctk.CTkFont(size=13, weight="bold"), anchor="w").pack(
                         fill="x", padx=18, pady=(8, 0))
        self.op_var = ctk.StringVar(value="")
        self.op_menu = ctk.CTkOptionMenu(self, values=["(choisir un client)"],
                                         variable=self.op_var,
                                         fg_color=COULEURS["primaire"],
                                         button_color=COULEURS["primaire2"])
        self.op_menu.pack(fill="x", padx=18, pady=(2, 6))

        # 3) Détails du paiement
        ctk.CTkLabel(self, text="3) Détails", font=ctk.CTkFont(size=13, weight="bold"),
                     anchor="w").pack(fill="x", padx=18, pady=(4, 0))
        self.montant = ctk.CTkEntry(self, placeholder_text=f"Montant ({config.DEVISE})")
        self.montant.pack(fill="x", padx=18, pady=3)
        self.mode_var = ctk.StringVar(value=config.MODES_PAIEMENT[0])
        ctk.CTkOptionMenu(self, values=config.MODES_PAIEMENT, variable=self.mode_var,
                          fg_color=COULEURS["primaire"],
                          button_color=COULEURS["primaire2"]).pack(fill="x", padx=18, pady=3)
        if CAL:
            self.date = DateEntry(self, date_pattern="yyyy-mm-dd", width=18)
            self.date.delete(0, "end")
        else:
            self.date = ctk.CTkEntry(self, placeholder_text="Date (AAAA-MM-JJ)")
        self.date.pack(anchor="w", padx=18, pady=3)
        self.ref = ctk.CTkEntry(self, placeholder_text="Référence")
        self.ref.pack(fill="x", padx=18, pady=3)

        barre = ctk.CTkFrame(self, fg_color="transparent")
        barre.pack(fill="x", padx=18, pady=(8, 14))
        ctk.CTkButton(barre, text="Annuler", fg_color=COULEURS["gris"],
                      command=self._annuler, width=110).pack(side="right", padx=(8, 0))
        ctk.CTkButton(barre, text="Enregistrer", fg_color=COULEURS["vert"],
                      hover_color="#166638", command=self._valider, width=140).pack(side="right")

        self._maj_clients()
        self.transient(parent)
        self.grab_set()
        self.wait_window(self)

    def _maj_clients(self):
        for l in self.tab.get_children():
            self.tab.delete(l)
        terme = self.rech.get().strip()
        clients = db.rechercher_clients_avance(terme) if terme else db.lister_clients()[:15]
        for c in clients:
            self.tab.insert("", "end", iid=str(c["id"]),
                            values=(c["code"] or "", f'{c["nom"]} {c["prenom"] or ""}'.strip()))

    def _choisir_client(self, _ev=None):
        sel = self.tab.selection()
        if not sel:
            return
        self.client_id = int(sel[0])
        self._operations = act.lister_operations_client(self.client_id)
        libelles = []
        self._map_ops = {}
        for o in self._operations:
            lib = (f'{o["activite_libelle"]} {o["reference"]} — '
                   f'reste {formater(o["reste_a_payer"])}')
            libelles.append(lib)
            self._map_ops[lib] = (o["activite"], o["id"])
        if not libelles:
            libelles = ["(aucune opération pour ce client)"]
        self.op_menu.configure(values=libelles)
        self.op_var.set(libelles[0])

    def _valider(self):
        if not self.client_id:
            erreur("Client", "Choisissez d'abord un client.")
            return
        choix = self.op_var.get()
        if choix not in self._map_ops:
            erreur("Opération", "Choisissez l'opération à régler.")
            return
        activite, op_id = self._map_ops[choix]
        try:
            montant = float(self.montant.get().replace(" ", "").replace(",", "."))
        except ValueError:
            montant = 0
        if montant <= 0:
            erreur("Montant", "Le montant doit être supérieur à 0.")
            return
        date = self.date.get().strip() if CAL else self.date.get().strip()
        act.creer_paiement_operation(activite, op_id, montant, self.mode_var.get(),
                                     self.ref.get().strip(), date, "")
        self.enregistre = True
        info("Paiement", "Paiement enregistré.")
        self.grab_release(); self.destroy()

    def _annuler(self):
        self.grab_release(); self.destroy()
