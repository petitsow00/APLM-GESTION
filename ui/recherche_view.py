# -*- coding: utf-8 -*-
"""
ui/recherche_view.py
--------------------
§18 : RECHERCHE GLOBALE. Un seul champ cherche partout (client, PNR, n° billet,
police d'assurance, dossier visa, référence de paiement, référence bancaire).
Un clic sur un résultat « client » ouvre directement sa fiche + historique.
"""

import tkinter as tk
from tkinter import ttk
import customtkinter as ctk

import recherche as rech
from ui.helpers import COULEURS
from ui.operation_dialog import formater
from ui.clients_view import FicheClient


class RechercheView(ctk.CTkFrame):
    def __init__(self, parent, on_changement=None):
        super().__init__(parent, fg_color=COULEURS["fond"])
        self._construire()

    def _construire(self):
        ctk.CTkLabel(self, text="🔎  Recherche globale",
                     font=ctk.CTkFont(size=26, weight="bold"),
                     text_color=COULEURS["primaire"]).pack(
                         anchor="w", padx=30, pady=(26, 6))
        ctk.CTkLabel(self, text="Cherchez un client, un PNR, un n° de billet, "
                     "une police, un dossier visa, une référence…",
                     text_color=COULEURS["gris"]).pack(anchor="w", padx=30, pady=(0, 8))

        barre = ctk.CTkFrame(self, fg_color="transparent")
        barre.pack(fill="x", padx=30, pady=(0, 8))
        self.terme = ctk.StringVar()
        e = ctk.CTkEntry(barre, textvariable=self.terme, width=420,
                         placeholder_text="Taper puis Entrée…")
        e.pack(side="left")
        e.bind("<Return>", lambda ev: self.chercher())
        ctk.CTkButton(barre, text="Rechercher", fg_color=COULEURS["vert"],
                      hover_color="#166638", command=self.chercher).pack(
                          side="left", padx=8)

        self.zone = ctk.CTkScrollableFrame(self, fg_color=COULEURS["fond"])
        self.zone.pack(fill="both", expand=True, padx=24, pady=(0, 20))

    def chercher(self):
        for w in self.zone.winfo_children():
            w.destroy()
        terme = self.terme.get().strip()
        if not terme:
            return
        res = rech.rechercher(terme)
        total = rech.compter(res)
        if total == 0:
            ctk.CTkLabel(self.zone, text="Aucun résultat.",
                         text_color=COULEURS["gris"]).pack(anchor="w", pady=10)
            return

        if res["clients"]:
            self._section("👤 Clients", [
                (f'{c["nom"]} {c["prenom"] or ""} ({c["code"] or ""})  ·  '
                 f'📞 {c["telephone"] or "—"}  ·  🛂 '
                 f'{c["num_passeport"] if "num_passeport" in c.keys() else ""}',
                 c["id"]) for c in res["clients"]], client=True)

        self._section_ops("✈️ Billets", res["billets"],
                          lambda o: f'{o["reference"]} · PNR {o["pnr"] or "—"} · '
                                    f'{o["passager"] or ""}')
        self._section_ops("🏨 Hôtels", res["hotels"],
                          lambda o: f'{o["reference"]} · {o["nom_hotel"] or ""}')
        self._section_ops("🛡️ Assurances", res["assurances"],
                          lambda o: f'{o["reference"]} · police {o["num_police"] or "—"}')
        self._section_ops("🛂 Visa", res["visas"],
                          lambda o: f'{o["reference"]} · dossier {o["num_dossier"] or "—"}')
        self._section_ops("💰 Paiements", res["paiements"],
                          lambda o: f'{formater(o["montant"])} · {o["mode"] or ""} · '
                                    f'réf {o["reference"] or "—"}', client_nom=True)
        self._section_ops("🏦 Banque", res["banque"],
                          lambda o: f'{o["compte_nom"]} · {o["type"]} '
                                    f'{formater(o["montant"])} · '
                                    f'réf {o["reference_bancaire"] or "—"}', nom_direct=True)

    def _section(self, titre, elements, client=False):
        if not elements:
            return
        ctk.CTkLabel(self.zone, text=f"{titre}  ({len(elements)})",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=COULEURS["primaire"]).pack(anchor="w", pady=(10, 2))
        for texte, cid in elements:
            ligne = ctk.CTkFrame(self.zone, fg_color=COULEURS["carte"], corner_radius=8)
            ligne.pack(fill="x", pady=3)
            ctk.CTkLabel(ligne, text=texte, anchor="w").pack(
                side="left", padx=12, pady=8)
            if client:
                ctk.CTkButton(ligne, text="Ouvrir la fiche", width=130,
                              fg_color=COULEURS["primaire2"],
                              command=lambda i=cid: FicheClient(self.winfo_toplevel(), i)
                              ).pack(side="right", padx=10)

    def _section_ops(self, titre, lignes, fmt, client_nom=False, nom_direct=False):
        if not lignes:
            return
        ctk.CTkLabel(self.zone, text=f"{titre}  ({len(lignes)})",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=COULEURS["primaire"]).pack(anchor="w", pady=(10, 2))
        for o in lignes:
            texte = fmt(o)
            if not nom_direct and ("client_nom" in o.keys()):
                texte += f'   —   {o["client_nom"] or ""} {o["client_prenom"] or ""}'.rstrip()
            cadre = ctk.CTkFrame(self.zone, fg_color=COULEURS["carte"], corner_radius=8)
            cadre.pack(fill="x", pady=3)
            ctk.CTkLabel(cadre, text=texte, anchor="w").pack(
                side="left", padx=12, pady=8)
