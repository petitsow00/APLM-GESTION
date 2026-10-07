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
import auth
import i18n
from i18n import t
from ui.helpers import COULEURS, styler_treeview, erreur
from ui.dashboard_view import DashboardView
from ui.clients_view import ClientsView
from ui.dossiers_view import DossiersView
from ui.activite_view import (BilletsView, HotelsView, AssurancesView, VisasView)
from ui.paiements_view import PaiementsView
from ui.banque_view import BanqueView
from ui.rapports_view import RapportsView
from ui.recherche_view import RechercheView
from ui.parametres_view import ParametresView
from ui.historique_clients_view import HistoriqueClientsView
from ui.historique_transactions_view import HistoriqueTransactionsView
from ui.utilisateurs_view import UtilisateursView
from ui.journal_view import JournalView
from ui.depenses_view import DepensesView
from ui.avoirs_view import AvoirsView
from ui.comptabilite_view import ComptabiliteView
from ui.reseau_view import ReseauView


class MainApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        # Passe à True si l'utilisateur clique sur « Déconnexion »
        # (permet à main.py de revenir à l'écran de connexion).
        self.se_deconnecter = False
        # Prépare la base de données au démarrage
        db.initialiser_base()
        # Récupère les coordonnées d'agence et le logo partagés (mêmes sur
        # tous les postes connectés, Windows comme Mac) avant d'afficher
        # quoi que ce soit — voir settings.py.
        settings.synchroniser()
        # Réorganisation 2026 : crée les tables des 4 activités, de la banque et
        # des documents, enrichit la fiche client et met à niveau les paiements.
        import activites, banque, documents
        activites.initialiser()
        banque.initialiser()
        documents.initialiser()
        # Prépare les tables comptables (plan comptable, journaux, etc.)
        import comptabilite
        comptabilite.initialiser_comptabilite()
        # Recopie (une seule fois, idempotent) les anciennes réservations vers
        # les nouvelles activités séparées. Sans effet si déjà fait.
        try:
            activites.migrer_reservations_vers_activites()
        except Exception:
            pass
        # Sauvegarde automatique du jour (sécurité anti-perte de données)
        try:
            import sauvegarde
            sauvegarde.sauvegarde_auto()
        except Exception:
            pass

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

        # Bas de la barre (réservé EN BAS d'abord, pour rester toujours visible)
        bas = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        bas.pack(side="bottom", fill="x", pady=14, padx=14)

        # Zone de menu DÉFILANTE : tous les boutons restent accessibles même
        # si la liste est plus longue que l'écran.
        self.menu_zone = ctk.CTkScrollableFrame(self.sidebar,
                                                fg_color=COULEURS["primaire"],
                                                width=214)
        self.menu_zone.pack(side="top", fill="both", expand=True, padx=2)

        # Boutons de menu
        self._boutons = {}
        menus = [
            ("dashboard",  "📊  " + t("menu_dashboard")),
            ("recherche",  "🔎  Recherche"),
            ("clients",    "👤  " + t("menu_clients")),
            ("billets",    "✈️  Billets"),
            ("hotels",     "🏨  Hôtels"),
            ("assurances", "🛡️  Assurances"),
            ("visas",      "🛂  Assistance Visa"),
            ("hist_clients", "🧾  " + t("menu_hist_clients")),
        ]
        # Menus réservés à l'administrateur (comptabilité + données sensibles)
        if auth.est_admin():
            menus.append(("paiements", "💰  Paiements"))
            menus.append(("banque", "🏦  Banque"))
            menus.append(("rapports", "📊  Rapports"))
            menus.append(("hist_transac", "📈  " + t("menu_hist_transac")))
            menus.append(("depenses", "💸  " + t("menu_depenses")))
            menus.append(("avoir", "💰  " + t("menu_avoir")))
            menus.append(("comptabilite", "📊  " + t("menu_comptabilite")))
            menus.append(("utilisateurs", "👥  " + t("menu_utilisateurs")))
            menus.append(("journal", "📝  " + t("menu_journal")))
            menus.append(("reseau", "🌐  Réseau"))
        menus.append(("parametres", "⚙  " + t("menu_parametres")))
        for cle, libelle in menus:
            b = ctk.CTkButton(self.menu_zone, text=libelle, anchor="w",
                              height=42, corner_radius=8,
                              font=ctk.CTkFont(size=13),
                              fg_color="transparent", hover_color=COULEURS["primaire2"],
                              command=lambda c=cle: self.afficher(c))
            b.pack(fill="x", padx=8, pady=3)
            self._boutons[cle] = b

        # Utilisateur connecté
        role_txt = t("role_admin") if auth.est_admin() else t("role_agent")
        ctk.CTkLabel(bas, text=f'👤  {auth.nom_courant()}',
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color="white", anchor="w").pack(fill="x")
        ctk.CTkLabel(bas, text=f'{t("lbl_connecte")} · {role_txt}',
                     font=ctk.CTkFont(size=10),
                     text_color="#9fb6cf", anchor="w").pack(fill="x", pady=(0, 8))

        ctk.CTkButton(bas, text="⏻  " + t("btn_deconnexion"), height=38,
                      corner_radius=8, fg_color=COULEURS["rouge"],
                      hover_color="#922b21",
                      command=self.deconnexion).pack(fill="x", pady=(0, 8))

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
        elif nom == "recherche":
            self._vue_widget = RechercheView(self.container)
        elif nom == "clients":
            self._vue_widget = ClientsView(self.container)
        elif nom == "billets":
            self._vue_widget = BilletsView(self.container)
        elif nom == "hotels":
            self._vue_widget = HotelsView(self.container)
        elif nom == "assurances":
            self._vue_widget = AssurancesView(self.container)
        elif nom == "visas":
            self._vue_widget = VisasView(self.container)
        elif nom == "paiements":
            if not auth.est_admin():
                erreur("Erreur", t("msg_acces_refuse"))
                return self.afficher("dashboard")
            self._vue_widget = PaiementsView(self.container)
        elif nom == "banque":
            if not auth.est_admin():
                erreur("Erreur", t("msg_acces_refuse"))
                return self.afficher("dashboard")
            self._vue_widget = BanqueView(self.container)
        elif nom == "rapports":
            if not auth.est_admin():
                erreur("Erreur", t("msg_acces_refuse"))
                return self.afficher("dashboard")
            self._vue_widget = RapportsView(self.container)
        elif nom == "dossiers":
            self._vue_widget = DossiersView(self.container)
        elif nom == "hist_clients":
            self._vue_widget = HistoriqueClientsView(self.container)
        elif nom == "hist_transac":
            if not auth.est_admin():
                erreur("Erreur", t("msg_acces_refuse"))
                return self.afficher("dashboard")
            self._vue_widget = HistoriqueTransactionsView(self.container)
        elif nom == "depenses":
            if not auth.est_admin():
                erreur("Erreur", t("msg_acces_refuse"))
                return self.afficher("dashboard")
            self._vue_widget = DepensesView(self.container)
        elif nom == "avoir":
            if not auth.est_admin():
                erreur("Erreur", t("msg_acces_refuse"))
                return self.afficher("dashboard")
            self._vue_widget = AvoirsView(self.container)
        elif nom == "comptabilite":
            if not auth.est_admin():
                erreur("Erreur", t("msg_acces_refuse"))
                return self.afficher("dashboard")
            self._vue_widget = ComptabiliteView(self.container)
        elif nom == "utilisateurs":
            if not auth.est_admin():
                erreur("Erreur", t("msg_acces_refuse"))
                return self.afficher("dashboard")
            self._vue_widget = UtilisateursView(self.container)
        elif nom == "journal":
            if not auth.est_admin():
                erreur("Erreur", t("msg_acces_refuse"))
                return self.afficher("dashboard")
            self._vue_widget = JournalView(self.container)
        elif nom == "reseau":
            if not auth.est_admin():
                erreur("Erreur", t("msg_acces_refuse"))
                return self.afficher("dashboard")
            self._vue_widget = ReseauView(self.container)
        elif nom == "parametres":
            self._vue_widget = ParametresView(self.container,
                                              on_enregistre=self._apres_reglages)
        self._vue_widget.pack(fill="both", expand=True)

    def deconnexion(self):
        """Ferme la session et revient à l'écran de connexion (via main.py)."""
        db.enregistrer_activite("Déconnexion", "Session", auth.nom_courant())
        self.se_deconnecter = True
        self.destroy()

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
