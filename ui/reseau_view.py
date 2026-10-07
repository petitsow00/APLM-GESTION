# -*- coding: utf-8 -*-
"""
ui/reseau_view.py
------------------
Écran RÉGLAGES RÉSEAU (multi-postes) — réservé à l'administrateur.

Permet de choisir comment CET ordinateur fonctionne :
    - Seul       : base locale (comme avant).
    - Serveur    : cet ordinateur partage la base sur le réseau du bureau.
    - Client     : cet ordinateur se connecte au serveur (par son adresse IP).

+ adresse IP du serveur, port, et clé secrète partagée.
"""

import customtkinter as ctk

import reseau
import db_client
import db_serveur
from i18n import t
from ui.helpers import COULEURS, info, erreur


# Correspondance texte affiché <-> valeur enregistrée
_MODES = [
    ("local", "Seul (cet ordinateur uniquement)"),
    ("serveur", "Serveur (ce PC partage la base)"),
    ("client", "Client (se connecte au serveur)"),
]
_TXT_VERS_MODE = {txt: val for val, txt in _MODES}
_MODE_VERS_TXT = {val: txt for val, txt in _MODES}


class ReseauView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=COULEURS["fond"])
        self._construire()

    def _construire(self):
        ctk.CTkLabel(self, text="Réglages réseau (multi-postes)",
                     font=ctk.CTkFont(size=24, weight="bold"),
                     text_color=COULEURS["primaire"]).pack(
                         anchor="w", padx=30, pady=(22, 4))
        ctk.CTkLabel(self, text="Choisissez comment cet ordinateur travaille "
                                "avec les autres postes du bureau.",
                     font=ctk.CTkFont(size=13), text_color=COULEURS["gris"]).pack(
                         anchor="w", padx=30, pady=(0, 14))

        carte = ctk.CTkFrame(self, fg_color=COULEURS["carte"], corner_radius=12)
        carte.pack(fill="x", padx=30, pady=(0, 12))

        # --- Mode ---
        ctk.CTkLabel(carte, text="Rôle de cet ordinateur",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=COULEURS["texte"]).pack(anchor="w", padx=20, pady=(18, 2))
        self.var_mode = ctk.StringVar(value=_MODE_VERS_TXT.get(reseau.mode()))
        ctk.CTkOptionMenu(carte, values=[txt for _, txt in _MODES],
                          variable=self.var_mode, width=360,
                          command=lambda _: self._maj_affichage(),
                          fg_color=COULEURS["primaire"],
                          button_color=COULEURS["primaire2"]).pack(anchor="w", padx=20, pady=(0, 6))

        # --- Adresse IP du serveur (pour un client) ---
        self.lbl_hote = ctk.CTkLabel(carte, text="Adresse IP du serveur "
                                     "(ex : 192.168.1.10)",
                                     font=ctk.CTkFont(size=13, weight="bold"),
                                     text_color=COULEURS["texte"])
        self.e_hote = ctk.CTkEntry(carte, width=280)
        self.e_hote.insert(0, reseau.hote())

        # --- Port ---
        self.lbl_port = ctk.CTkLabel(carte, text="Port réseau (laisser 5000 si vous ne savez pas)",
                                     font=ctk.CTkFont(size=13, weight="bold"),
                                     text_color=COULEURS["texte"])
        self.e_port = ctk.CTkEntry(carte, width=140)
        self.e_port.insert(0, str(reseau.port()))

        # --- Clé partagée ---
        self.lbl_cle = ctk.CTkLabel(carte, text="Clé secrète partagée "
                                    "(la même sur tous les postes)",
                                    font=ctk.CTkFont(size=13, weight="bold"),
                                    text_color=COULEURS["texte"])
        self.e_cle = ctk.CTkEntry(carte, width=280)
        self.e_cle.insert(0, reseau.cle())

        for w in (self.lbl_hote, self.e_hote, self.lbl_port, self.e_port,
                  self.lbl_cle, self.e_cle):
            w.pack(anchor="w", padx=20, pady=(6, 0))

        # --- Zone d'information (IP locale / statut) ---
        self.lbl_info = ctk.CTkLabel(carte, text="", font=ctk.CTkFont(size=12),
                                     text_color=COULEURS["primaire"],
                                     wraplength=560, justify="left")
        self.lbl_info.pack(anchor="w", padx=20, pady=(12, 6))

        # --- Boutons ---
        barre = ctk.CTkFrame(carte, fg_color="transparent")
        barre.pack(fill="x", padx=20, pady=(4, 18))
        ctk.CTkButton(barre, text="💾  " + t("btn_enregistrer"),
                      fg_color=COULEURS["vert"], hover_color="#166638",
                      command=self._enregistrer).pack(side="left")
        self.btn_test = ctk.CTkButton(barre, text="🔌  Tester la connexion",
                                      fg_color=COULEURS["accent"],
                                      command=self._tester)
        self.btn_test.pack(side="left", padx=(10, 0))
        self.btn_serveur = ctk.CTkButton(barre, text="▶  Démarrer le serveur",
                                         fg_color=COULEURS["primaire2"],
                                         command=self._demarrer_serveur)
        self.btn_serveur.pack(side="left", padx=(10, 0))

        # --- Aide ---
        ctk.CTkLabel(self, text="ℹ  Après avoir changé le rôle, FERMEZ puis "
                                "ROUVREZ le logiciel pour appliquer le changement.\n"
                                "Sur le PC serveur : notez l'adresse IP affichée et "
                                "donnez-la aux autres postes (avec la clé).",
                     font=ctk.CTkFont(size=12), text_color=COULEURS["gris"],
                     justify="left").pack(anchor="w", padx=34, pady=(0, 10))

        self._maj_affichage()

    # ------------------------------------------------------------------ #
    def _mode_choisi(self):
        return _TXT_VERS_MODE.get(self.var_mode.get(), "local")

    def _maj_affichage(self):
        """Affiche/masque les champs selon le rôle choisi + infos utiles."""
        mode = self._mode_choisi()
        etat_client = "normal" if mode == "client" else "disabled"
        self.e_hote.configure(state=etat_client)
        self.btn_test.configure(state=etat_client)
        self.btn_serveur.configure(
            state="normal" if mode == "serveur" else "disabled")

        if mode == "serveur":
            self.lbl_info.configure(
                text=f"Adresse IP de CE serveur : {reseau.adresse_ip_locale()}\n"
                     f"Donnez cette adresse (et la clé) aux autres postes.")
        elif mode == "client":
            self.lbl_info.configure(
                text="Ce poste se connectera au serveur indiqué ci-dessus.")
        else:
            self.lbl_info.configure(
                text="Ce poste travaille seul, sur sa propre base locale.")

    def _valeurs(self):
        return {
            "mode": self._mode_choisi(),
            "hote": self.e_hote.get().strip() or "127.0.0.1",
            "port": self.e_port.get().strip() or "5000",
            "cle": self.e_cle.get().strip(),
        }

    def _enregistrer(self):
        reseau.sauvegarder(self._valeurs())
        info("Info", "Réglages réseau enregistrés.\n\n"
                     "Fermez puis rouvrez le logiciel pour appliquer le nouveau rôle.")
        self._maj_affichage()

    def _tester(self):
        v = self._valeurs()
        ok, message = db_client.tester_connexion(v["hote"], int(v["port"]), v["cle"])
        (info if ok else erreur)("Test de connexion", message)

    def _demarrer_serveur(self):
        # On enregistre d'abord (port/clé) puis on démarre
        reseau.sauvegarder(self._valeurs())
        ok, message = db_serveur.demarrer_serveur()
        (info if ok else erreur)("Serveur", message)
        self._maj_affichage()
