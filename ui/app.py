# -*- coding: utf-8 -*-
"""
ui/app.py
----------
La fenêtre principale du logiciel : menu de navigation à gauche,
zone de contenu à droite, bouton de changement de langue.

VERSION STANDARD : le nom affiché vient des Réglages de l'agence
(settings.py), il n'est plus écrit en dur dans le code.
"""

import customtkinter as ctk

import database as db
import settings
import i18n
from i18n import t
from ui.helpers import COULEURS, styler_treeview
from ui.dashboard_view import DashboardView
from ui.clients_view import ClientsView
from ui.dossiers_view import DossiersView
from ui.parametres_view import ParametresView
from ui.historique_clients_view import HistoriqueClientsView
from ui.historique_transactions_view import HistoriqueTransactionsView


class MainApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        # Prépare la base de données au démarrage
        db.initialiser_base()

        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        styler_treeview()

        self._maj_titre()
        self.geometry("1180x740")
        self.minsize(1000, 640)
        self.configure(fg_color=COULEURS["fond"])

        # Au 1er lancement (agence non configurée) -> on ouvre les Réglages
        self._vue_active = "parametres" if not settings.est_configure() else "dashboard"
        self._vue_widget = None
        self._construire()
        self.afficher(self._vue_active)

    def _maj_titre(self):
        nom = settings.nom_agence()
        self.title(nom if nom else t("app_titre"))

    # ---------------------------------------------------------------- #
    def _construire(self):
        # === Barre latérale (menu) ===
        self.sidebar = ctk.CTkFrame(self, fg_color=COULEURS["primaire"],
                                    width=230, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Nom de l'agence (depuis les Réglages)
        nom = settings.nom_agence()
        ctk.CTkLabel(self.sidebar,
                     text=nom if nom else t("champ_nom_agence"),
                     font=ctk.CTkFont(size=20, weight="bold"),
                     text_color="white", wraplength=200, justify="center").pack(
                         pady=(26, 2), padx=10)
        sous_titre = settings.get("slogan") or t("app_titre")
        ctk.CTkLabel(self.sidebar, text="✈  " + sous_titre,
                     font=ctk.CTkFont(size=11),
                     text_color="#9fb6cf", wraplength=200).pack(pady=(0, 24), padx=10)

        # Boutons de menu
        self._boutons = {}
        menus = [
            ("dashboard",  "📊  " + t("menu_dashboard")),
            ("clients",    "👤  " + t("menu_clients")),
            ("dossiers",   "📁  " + t("menu_dossiers")),
            ("hist_clients", "🧾  " + t("menu_hist_clients")),
            ("hist_transac", "📈  " + t("menu_hist_transac")),
            ("parametres", "⚙  " + t("menu_parametres")),
        ]
        for cle, libelle in menus:
            b = ctk.CTkButton(self.sidebar, text=libelle, anchor="w",
                              height=46, corner_radius=8,
                              font=ctk.CTkFont(size=14),
                              fg_color="transparent", hover_color=COULEURS["primaire2"],
                              command=lambda c=cle: self.afficher(c))
            b.pack(fill="x", padx=14, pady=4)
            self._boutons[cle] = b

        # Bas de la barre : langue
        bas = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        bas.pack(side="bottom", fill="x", pady=18, padx=14)

        ctk.CTkButton(bas, text="🌐  Français / English", height=40, corner_radius=8,
                      fg_color=COULEURS["accent"], hover_color="#2471a3",
                      command=self.changer_langue).pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(bas, text=f'{t("menu_langue")}: '
                     f'{"Français" if i18n.langue_active()=="fr" else "English"}',
                     font=ctk.CTkFont(size=11), text_color="#8ba3bf").pack()

        # === Zone de contenu ===
        self.container = ctk.CTkFrame(self, fg_color=COULEURS["fond"],
                                      corner_radius=0)
        self.container.pack(side="left", fill="both", expand=True)

    # ---------------------------------------------------------------- #
    def afficher(self, nom):
        """Affiche une vue (dashboard / clients / dossiers / parametres)."""
        self._vue_active = nom

        if self._vue_widget is not None:
            self._vue_widget.destroy()

        for cle, b in self._boutons.items():
            b.configure(fg_color=COULEURS["accent"] if cle == nom else "transparent")

        if nom == "dashboard":
            self._vue_widget = DashboardView(self.container)
        elif nom == "clients":
            self._vue_widget = ClientsView(self.container)
        elif nom == "dossiers":
            self._vue_widget = DossiersView(self.container)
        elif nom == "hist_clients":
            self._vue_widget = HistoriqueClientsView(self.container)
        elif nom == "hist_transac":
            self._vue_widget = HistoriqueTransactionsView(self.container)
        elif nom == "parametres":
            self._vue_widget = ParametresView(self.container,
                                              on_enregistre=self._apres_reglages)
        self._vue_widget.pack(fill="both", expand=True)

    def _apres_reglages(self):
        """Après enregistrement des Réglages : met à jour le titre et le menu."""
        self._maj_titre()
        self.sidebar.destroy()
        self.container.destroy()
        self._vue_widget = None
        self._construire()
        self.afficher("dashboard")

    def changer_langue(self):
        """Bascule Français <-> Anglais et reconstruit l'interface."""
        i18n.definir_langue("en" if i18n.langue_active() == "fr" else "fr")
        self._maj_titre()
        self.sidebar.destroy()
        self.container.destroy()
        self._vue_widget = None
        self._construire()
        self.afficher(self._vue_active)
