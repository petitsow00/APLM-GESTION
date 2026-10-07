# -*- coding: utf-8 -*-
"""
ui/documents_dialog.py
----------------------
Fenêtre pour gérer les DOCUMENTS joints à une opération (facture, reçu,
police, visa, bordereau, justificatif...). On peut ajouter un fichier
(il est copié dans le dossier `documents/`), l'ouvrir ou le supprimer.
"""

import os
from tkinter import ttk, filedialog
import customtkinter as ctk

import documents as docs
from ui.helpers import COULEURS, confirmer, info, erreur

try:
    from utils import ouvrir_fichier
except Exception:
    def ouvrir_fichier(chemin):
        try:
            os.startfile(chemin)  # Windows
        except Exception:
            pass


class DocumentsDialog(ctk.CTkToplevel):
    def __init__(self, parent, operation_type, operation_id, client_id=None):
        super().__init__(parent)
        self.operation_type = operation_type
        self.operation_id = operation_id
        self.client_id = client_id
        self.title("Documents joints")
        self.configure(fg_color=COULEURS["fond"])
        self.geometry("640x460")

        ctk.CTkLabel(self, text="📎  Documents joints",
                     font=ctk.CTkFont(size=18, weight="bold"),
                     text_color=COULEURS["primaire"]).pack(anchor="w", padx=18, pady=(16, 6))

        barre = ctk.CTkFrame(self, fg_color="transparent")
        barre.pack(fill="x", padx=18, pady=(0, 8))
        self.cat_var = ctk.StringVar(value=docs.CATEGORIES[0])
        ctk.CTkOptionMenu(barre, values=docs.CATEGORIES, variable=self.cat_var,
                          fg_color=COULEURS["primaire"],
                          button_color=COULEURS["primaire2"], width=180).pack(side="left")
        ctk.CTkButton(barre, text="+ Ajouter un fichier", fg_color=COULEURS["vert"],
                      hover_color="#166638", command=self.ajouter).pack(side="left", padx=8)
        ctk.CTkButton(barre, text="Ouvrir", fg_color=COULEURS["accent"],
                      command=self.ouvrir).pack(side="right", padx=(6, 0))
        ctk.CTkButton(barre, text="Supprimer", fg_color=COULEURS["rouge"],
                      hover_color="#922b21", command=self.supprimer).pack(side="right")

        cadre = ctk.CTkFrame(self, fg_color=COULEURS["carte"], corner_radius=10)
        cadre.pack(fill="both", expand=True, padx=18, pady=(0, 16))
        cols = ("categorie", "nom", "date")
        self.tableau = ttk.Treeview(cadre, columns=cols, show="headings",
                                    selectmode="browse")
        for c, txt, w in (("categorie", "Catégorie", 150), ("nom", "Nom", 300),
                          ("date", "Ajouté le", 130)):
            self.tableau.heading(c, text=txt)
            self.tableau.column(c, width=w, anchor="w")
        self.tableau.pack(fill="both", expand=True, padx=10, pady=10)

        self.rafraichir()
        self.transient(parent)
        self.grab_set()

    def rafraichir(self):
        for l in self.tableau.get_children():
            self.tableau.delete(l)
        self._docs = docs.lister_documents(self.operation_type, self.operation_id)
        for d in self._docs:
            self.tableau.insert("", "end", iid=str(d["id"]),
                                values=(d["categorie"] or "", d["nom"] or "",
                                        (d["date_creation"] or "")[:16]))

    def ajouter(self):
        chemin = filedialog.askopenfilename(title="Choisir un fichier à joindre")
        if not chemin:
            return
        docs.enregistrer_document(
            chemin, categorie=self.cat_var.get(),
            operation_type=self.operation_type, operation_id=self.operation_id,
            client_id=self.client_id)
        self.rafraichir()

    def _selection(self):
        sel = self.tableau.selection()
        if not sel:
            info("Info", "Sélectionnez un document.")
            return None
        return int(sel[0])

    def ouvrir(self):
        did = self._selection()
        if did is None:
            return
        d = next((x for x in self._docs if x["id"] == did), None)
        if d and d["chemin"] and os.path.exists(d["chemin"]):
            ouvrir_fichier(d["chemin"])
        else:
            erreur("Erreur", "Fichier introuvable sur le disque.")

    def supprimer(self):
        did = self._selection()
        if did is None:
            return
        if confirmer("Supprimer", "Retirer ce document ?"):
            docs.supprimer_document(did)
            self.rafraichir()
