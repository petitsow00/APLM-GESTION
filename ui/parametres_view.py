# -*- coding: utf-8 -*-
"""
ui/parametres_view.py
----------------------
Écran « Réglages » : chaque agence y saisit ses propres informations
(nom, adresse, téléphone, monnaie...) et choisit son logo.
Ces informations sont enregistrées dans data/parametres.json et apparaissent
ensuite sur les reçus.
"""

import os
import shutil
from tkinter import filedialog
import customtkinter as ctk

import config
import settings
from i18n import t
from ui.helpers import COULEURS, info, erreur

try:
    from PIL import Image
    PIL_DISPO = True
except Exception:
    PIL_DISPO = False


class ParametresView(ctk.CTkFrame):
    def __init__(self, parent, on_enregistre=None):
        super().__init__(parent, fg_color=COULEURS["fond"])
        self.on_enregistre = on_enregistre   # appelé après sauvegarde
        self._champs = {}
        self._construire()

    def _construire(self):
        ctk.CTkLabel(self, text=t("param_titre"),
                     font=ctk.CTkFont(size=26, weight="bold"),
                     text_color=COULEURS["primaire"]).pack(
                         anchor="w", padx=30, pady=(26, 4))
        ctk.CTkLabel(self, text=t("param_intro"),
                     font=ctk.CTkFont(size=13), text_color=COULEURS["gris"],
                     justify="left").pack(anchor="w", padx=30, pady=(0, 16))

        zone = ctk.CTkScrollableFrame(self, fg_color=COULEURS["carte"],
                                      corner_radius=12)
        zone.pack(fill="both", expand=True, padx=30, pady=(0, 20))

        params = settings.charger()
        definitions = [
            ("nom",       t("champ_nom_agence")),
            ("slogan",    t("champ_slogan")),
            ("adresse",   t("champ_adresse")),
            ("telephone", t("champ_telephone")),
            ("email",     t("champ_email")),
            ("site_web",  t("champ_site")),
            ("rccm",      t("champ_rccm")),
            ("devise",    t("champ_devise")),
        ]
        for cle, label in definitions:
            ctk.CTkLabel(zone, text=label,
                         font=ctk.CTkFont(size=13, weight="bold"),
                         text_color=COULEURS["texte"], anchor="w").pack(
                             fill="x", padx=16, pady=(12, 0))
            entree = ctk.CTkEntry(zone, height=36)
            valeur = params.get(cle, "")
            if valeur:
                entree.insert(0, str(valeur))
            entree.pack(fill="x", padx=16, pady=(2, 2))
            self._champs[cle] = entree

        # --- Section logo ---
        ctk.CTkLabel(zone, text=t("param_logo"),
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=COULEURS["texte"], anchor="w").pack(
                         fill="x", padx=16, pady=(18, 0))
        ligne_logo = ctk.CTkFrame(zone, fg_color="transparent")
        ligne_logo.pack(fill="x", padx=16, pady=(2, 10))
        ctk.CTkButton(ligne_logo, text="🖼  " + t("param_choisir_logo"),
                      fg_color=COULEURS["accent"], command=self.choisir_logo,
                      width=200).pack(side="left")
        self.lbl_logo = ctk.CTkLabel(
            ligne_logo,
            text=(t("param_logo_actuel") if os.path.exists(config.LOGO_PATH)
                  else t("param_logo_absent")),
            font=ctk.CTkFont(size=12), text_color=COULEURS["gris"])
        self.lbl_logo.pack(side="left", padx=14)

        # --- Bouton enregistrer ---
        barre = ctk.CTkFrame(self, fg_color="transparent")
        barre.pack(fill="x", padx=30, pady=(0, 20))
        ctk.CTkButton(barre, text="💾  " + t("btn_enregistrer"),
                      fg_color=COULEURS["vert"], hover_color="#166638",
                      height=44, font=ctk.CTkFont(size=15, weight="bold"),
                      command=self.enregistrer, width=220).pack(side="right")

    def choisir_logo(self):
        chemin = filedialog.askopenfilename(
            title=t("param_choisir_logo"),
            filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp *.gif"),
                       ("Tous les fichiers", "*.*")])
        if not chemin:
            return
        os.makedirs(config.ASSETS_DIR, exist_ok=True)
        try:
            if PIL_DISPO:
                # Convertit proprement l'image en PNG
                img = Image.open(chemin).convert("RGBA")
                img.save(config.LOGO_PATH, "PNG")
            else:
                shutil.copyfile(chemin, config.LOGO_PATH)
            self.lbl_logo.configure(text=t("param_logo_actuel"))
            info(t("menu_parametres"), t("param_logo_ok"))
        except Exception as e:
            erreur("Erreur", f"Impossible d'enregistrer le logo :\n{e}")

    def enregistrer(self):
        valeurs = {cle: e.get().strip() for cle, e in self._champs.items()}
        if not valeurs.get("devise"):
            valeurs["devise"] = "FCFA"
        settings.sauvegarder(valeurs)
        info(t("menu_parametres"), t("msg_param_ok"))
        if self.on_enregistre:
            self.on_enregistre()
