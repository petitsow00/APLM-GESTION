# -*- coding: utf-8 -*-
"""
ui/login_view.py
-----------------
Fenêtre de CONNEXION affichée au démarrage du logiciel.

Deux situations gérées automatiquement :

  1) PREMIÈRE UTILISATION (aucun compte n'existe encore)
     -> on affiche un formulaire pour créer le compte ADMINISTRATEUR.

  2) UTILISATION NORMALE (des comptes existent déjà)
     -> on affiche le formulaire de connexion (identifiant + mot de passe).

Quand la connexion réussit, on enregistre l'utilisateur connecté (auth.py)
et la fenêtre se ferme ; le logiciel principal peut alors s'ouvrir.
"""

import customtkinter as ctk

import database as db
import auth
import settings
from i18n import t
from ui.helpers import COULEURS, info, erreur


class LoginWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.reussi = False              # deviendra True si la connexion réussit

        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        nom_agence = settings.nom_agence() or "APLM BUZNESS COMPANY"
        self.title(nom_agence + " — " + t("login_titre"))
        self.geometry("460x620")
        self.resizable(False, False)
        self.configure(fg_color=COULEURS["fond"])

        self._contenu = None
        self._charger()
        self._centrer()

    # ------------------------------------------------------------------ #
    def _centrer(self):
        self.update_idletasks()
        larg, haut = 460, 620
        x = (self.winfo_screenwidth() - larg) // 2
        y = (self.winfo_screenheight() - haut) // 2
        self.geometry(f"{larg}x{haut}+{max(x,0)}+{max(y,0)}")

    def _charger(self):
        """(Re)construit l'écran de connexion selon le mode (local / serveur)
        et l'état de la base. Appelée aussi après un changement de serveur."""
        if self._contenu is not None:
            self._contenu.destroy()
        self._contenu = ctk.CTkFrame(self, fg_color="transparent")
        self._contenu.pack(fill="both", expand=True)

        # --- Bandeau haut ---
        haut = ctk.CTkFrame(self._contenu, fg_color=COULEURS["primaire"],
                            corner_radius=0, height=110)
        haut.pack(fill="x")
        haut.pack_propagate(False)
        ctk.CTkLabel(haut, text="✈  APLM BUZNESS COMPANY",
                     font=ctk.CTkFont(size=20, weight="bold"),
                     text_color="white").pack(pady=(26, 2))
        ctk.CTkLabel(haut, text=t("app_titre"),
                     font=ctk.CTkFont(size=12),
                     text_color="#9fb6cf").pack()

        # --- On détermine l'état (avec gestion d'un serveur injoignable) ---
        self._erreur_reseau = None
        try:
            db.initialiser_base()
            self.premiere_utilisation = (db.compter_utilisateurs() == 0)
            # Récupère les coordonnées d'agence partagées (mêmes sur tous
            # les postes connectés) avant d'afficher le titre de la fenêtre.
            settings.synchroniser()
            nom_agence = settings.nom_agence() or "APLM BUZNESS COMPANY"
            self.title(nom_agence + " — " + t("login_titre"))
        except Exception as e:
            self._erreur_reseau = str(e)
            self.premiere_utilisation = False

        # --- Carte centrale ---
        carte = ctk.CTkFrame(self._contenu, fg_color=COULEURS["carte"],
                             corner_radius=14)
        carte.pack(fill="both", expand=True, padx=30, pady=(20, 6))

        if self._erreur_reseau:
            self._construire_erreur_reseau(carte)
        elif self.premiere_utilisation:
            self._construire_premier_admin(carte)
        else:
            self._construire_connexion(carte)

        # --- Barre du bas : configurer le serveur ---
        self._barre_serveur()

    def _barre_serveur(self):
        """Bouton (toujours visible) pour configurer la connexion au serveur."""
        import reseau
        bas = ctk.CTkFrame(self._contenu, fg_color="transparent")
        bas.pack(fill="x", padx=30, pady=(0, 14))
        if reseau.est_client():
            etat = f"Serveur : {reseau.hote()}:{reseau.port()}"
        elif reseau.est_serveur():
            etat = "Ce PC est le serveur"
        else:
            etat = "Mode : cet ordinateur seul"
        ctk.CTkLabel(bas, text=etat, font=ctk.CTkFont(size=11),
                     text_color=COULEURS["gris"]).pack(anchor="w")
        ctk.CTkButton(bas, text="🌐  Se connecter à un serveur",
                      height=34, fg_color=COULEURS["accent"],
                      hover_color="#2471a3",
                      command=self._ouvrir_config_serveur).pack(fill="x", pady=(4, 0))

    def _construire_erreur_reseau(self, carte):
        """Affiché quand le serveur est configuré mais injoignable."""
        ctk.CTkLabel(carte, text="⚠  Serveur injoignable",
                     font=ctk.CTkFont(size=18, weight="bold"),
                     text_color=COULEURS["rouge"]).pack(
                         anchor="w", padx=24, pady=(26, 6))
        ctk.CTkLabel(carte, text=self._erreur_reseau,
                     font=ctk.CTkFont(size=12), text_color=COULEURS["gris"],
                     wraplength=360, justify="left").pack(
                         anchor="w", padx=24, pady=(0, 12))
        ctk.CTkButton(carte, text="↻  Réessayer",
                      height=42, fg_color=COULEURS["accent"],
                      command=self._charger).pack(fill="x", padx=24, pady=(6, 20))

    def _ouvrir_config_serveur(self):
        dlg = _DialogueServeur(self)
        if dlg.resultat is not None:
            self._charger()   # on recharge avec la nouvelle configuration

    # ------------------------------------------------------------------ #
    #  CAS 1 : création du premier administrateur
    # ------------------------------------------------------------------ #
    def _construire_premier_admin(self, carte):
        ctk.CTkLabel(carte, text=t("firstrun_titre"),
                     font=ctk.CTkFont(size=18, weight="bold"),
                     text_color=COULEURS["primaire"]).pack(
                         anchor="w", padx=24, pady=(22, 4))
        ctk.CTkLabel(carte, text=t("firstrun_intro"),
                     font=ctk.CTkFont(size=12), text_color=COULEURS["gris"],
                     wraplength=360, justify="left").pack(
                         anchor="w", padx=24, pady=(0, 12))

        self.e_nom = self._champ(carte, t("champ_nom"))
        self.e_prenom = self._champ(carte, t("champ_prenom"))
        self.e_identifiant = self._champ(carte, t("champ_identifiant"))
        self.e_mdp = self._champ(carte, t("champ_mdp"), secret=True)
        self.e_mdp2 = self._champ(carte, t("champ_mdp_confirm"), secret=True)

        ctk.CTkButton(carte, text="✓  " + t("firstrun_creer"),
                      height=44, fg_color=COULEURS["vert"],
                      hover_color="#166638",
                      font=ctk.CTkFont(size=14, weight="bold"),
                      command=self._creer_premier_admin).pack(
                          fill="x", padx=24, pady=(16, 20))

        self.bind("<Return>", lambda e: self._creer_premier_admin())

    def _creer_premier_admin(self):
        nom = self.e_nom.get().strip()
        prenom = self.e_prenom.get().strip()
        identifiant = self.e_identifiant.get().strip()
        mdp = self.e_mdp.get()
        mdp2 = self.e_mdp2.get()

        if not nom or not identifiant or not mdp:
            erreur(t("login_echec"), t("msg_champs_requis"))
            return
        if len(mdp) < 4:
            erreur(t("login_echec"), t("msg_mdp_court"))
            return
        if mdp != mdp2:
            erreur(t("login_echec"), t("msg_mdp_differents"))
            return

        try:
            db.creer_utilisateur(nom=nom, prenom=prenom, identifiant=identifiant,
                                 mot_de_passe=mdp, role="admin", actif=1)
        except ValueError as e:
            erreur(t("login_echec"), str(e))
            return

        # Connexion automatique du nouvel administrateur
        resultat = db.authentifier(identifiant, mdp)
        if resultat["ok"]:
            auth.definir_utilisateur_courant(resultat["utilisateur"])
            self.reussi = True
            self.destroy()

    # ------------------------------------------------------------------ #
    #  CAS 2 : connexion normale
    # ------------------------------------------------------------------ #
    def _construire_connexion(self, carte):
        ctk.CTkLabel(carte, text=t("login_titre"),
                     font=ctk.CTkFont(size=18, weight="bold"),
                     text_color=COULEURS["primaire"]).pack(
                         anchor="w", padx=24, pady=(26, 4))
        ctk.CTkLabel(carte, text=t("login_intro"),
                     font=ctk.CTkFont(size=12), text_color=COULEURS["gris"],
                     wraplength=360, justify="left").pack(
                         anchor="w", padx=24, pady=(0, 18))

        self.e_identifiant = self._champ(carte, t("champ_identifiant"))
        self.e_mdp = self._champ(carte, t("champ_mdp"), secret=True)

        ctk.CTkButton(carte, text="→  " + t("login_bouton"),
                      height=44, fg_color=COULEURS["accent"],
                      hover_color="#2471a3",
                      font=ctk.CTkFont(size=14, weight="bold"),
                      command=self._connexion).pack(
                          fill="x", padx=24, pady=(20, 20))

        self.e_identifiant.focus_set()
        self.bind("<Return>", lambda e: self._connexion())

    def _connexion(self):
        identifiant = self.e_identifiant.get().strip()
        mdp = self.e_mdp.get()
        if not identifiant or not mdp:
            erreur(t("login_echec"), t("msg_champs_requis"))
            return

        resultat = db.authentifier(identifiant, mdp)
        if not resultat["ok"]:
            erreur(t("login_echec"), resultat["raison"])
            self.e_mdp.delete(0, "end")
            return

        utilisateur = resultat["utilisateur"]
        auth.definir_utilisateur_courant(utilisateur)
        db.enregistrer_activite("Connexion", "Session", identifiant)

        # Mot de passe par défaut -> changement OBLIGATOIRE avant d'entrer
        if utilisateur["doit_changer_mdp"]:
            dlg = _DialogueChangementObligatoire(self, utilisateur["id"])
            if not dlg.reussi:
                auth.deconnecter()
                erreur(t("chg_titre"), t("msg_chg_obligatoire"))
                self.e_mdp.delete(0, "end")
                return

        self.reussi = True
        self.destroy()

    # ------------------------------------------------------------------ #
    def _champ(self, parent, label, secret=False):
        """Crée un libellé + un champ de saisie, et renvoie le champ."""
        ctk.CTkLabel(parent, text=label,
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=COULEURS["texte"], anchor="w").pack(
                         fill="x", padx=24, pady=(6, 0))
        champ = ctk.CTkEntry(parent, height=38,
                             show="•" if secret else "")
        champ.pack(fill="x", padx=24, pady=(2, 2))
        return champ


class _DialogueChangementObligatoire(ctk.CTkToplevel):
    """Écran OBLIGATOIRE de changement de mot de passe à la première connexion.

    Tant que l'utilisateur n'a pas choisi un nouveau mot de passe (différent du
    mot de passe par défaut), il ne peut pas entrer dans le logiciel."""

    def __init__(self, parent, utilisateur_id):
        super().__init__(parent)
        self.reussi = False
        self._uid = utilisateur_id
        self.title(t("chg_titre"))
        self.configure(fg_color=COULEURS["fond"])
        self.resizable(False, False)

        ctk.CTkLabel(self, text="🔒  " + t("chg_titre"),
                     font=ctk.CTkFont(size=18, weight="bold"),
                     text_color=COULEURS["primaire"]).pack(
                         padx=22, pady=(18, 4), anchor="w")
        ctk.CTkLabel(self, text=t("chg_intro"),
                     font=ctk.CTkFont(size=12), text_color=COULEURS["gris"],
                     wraplength=380, justify="left").pack(
                         anchor="w", padx=22, pady=(0, 10))

        zone = ctk.CTkFrame(self, fg_color=COULEURS["carte"], corner_radius=12)
        zone.pack(fill="both", expand=True, padx=22, pady=6)

        ctk.CTkLabel(zone, text=t("champ_nouveau_mdp"),
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=COULEURS["texte"], anchor="w").pack(
                         fill="x", padx=16, pady=(12, 0))
        self.e_mdp = ctk.CTkEntry(zone, show="•")
        self.e_mdp.pack(fill="x", padx=16, pady=(2, 2))

        ctk.CTkLabel(zone, text=t("champ_mdp_confirm"),
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=COULEURS["texte"], anchor="w").pack(
                         fill="x", padx=16, pady=(8, 0))
        self.e_mdp2 = ctk.CTkEntry(zone, show="•")
        self.e_mdp2.pack(fill="x", padx=16, pady=(2, 12))

        ctk.CTkButton(self, text="✓  " + t("chg_valider"),
                      height=42, fg_color=COULEURS["vert"], hover_color="#166638",
                      font=ctk.CTkFont(size=14, weight="bold"),
                      command=self._valider).pack(fill="x", padx=22, pady=(6, 18))

        self.e_mdp.focus_set()
        self.bind("<Return>", lambda e: self._valider())
        self.update_idletasks()
        self.transient(parent)
        self.grab_set()
        self.wait_window(self)

    def _valider(self):
        mdp = self.e_mdp.get()
        mdp2 = self.e_mdp2.get()
        if len(mdp) < 4:
            erreur(t("chg_titre"), t("msg_mdp_court"))
            return
        if mdp != mdp2:
            erreur(t("chg_titre"), t("msg_mdp_differents"))
            return
        if mdp == auth.MOT_DE_PASSE_DEFAUT:
            erreur(t("chg_titre"), t("msg_mdp_egal_defaut"))
            return
        db.changer_mot_de_passe(self._uid, mdp)
        self.reussi = True
        self.grab_release()
        self.destroy()


class _DialogueServeur(ctk.CTkToplevel):
    """Configuration de la connexion au serveur du bureau, depuis l'écran de
    connexion (avant de se connecter). Permet à un PC 'agent' de pointer vers
    le serveur, ou de revenir en mode 'cet ordinateur seul'."""

    def __init__(self, parent):
        super().__init__(parent)
        import reseau
        self.resultat = None
        self.title("Connexion au serveur")
        self.configure(fg_color=COULEURS["fond"])
        self.resizable(False, False)

        ctk.CTkLabel(self, text="🌐  Se connecter à un serveur",
                     font=ctk.CTkFont(size=18, weight="bold"),
                     text_color=COULEURS["primaire"]).pack(
                         padx=22, pady=(18, 4), anchor="w")
        ctk.CTkLabel(self, text="Saisissez l'adresse du serveur du bureau "
                                "et la clé partagée (fournies par l'administrateur).",
                     font=ctk.CTkFont(size=12), text_color=COULEURS["gris"],
                     wraplength=380, justify="left").pack(
                         anchor="w", padx=22, pady=(0, 8))

        zone = ctk.CTkFrame(self, fg_color=COULEURS["carte"], corner_radius=12)
        zone.pack(fill="both", expand=True, padx=22, pady=6)

        self.e_hote = self._champ(zone, "Adresse IP du serveur (ex : 192.168.1.10)",
                                  reseau.hote())
        self.e_port = self._champ(zone, "Port (par défaut 5000)", str(reseau.port()))
        self.e_cle = self._champ(zone, "Clé secrète partagée", reseau.cle())

        self.lbl_test = ctk.CTkLabel(zone, text="", font=ctk.CTkFont(size=12),
                                     text_color=COULEURS["primaire"],
                                     wraplength=380, justify="left")
        self.lbl_test.pack(anchor="w", padx=16, pady=(6, 4))

        barre = ctk.CTkFrame(self, fg_color="transparent")
        barre.pack(fill="x", padx=22, pady=(4, 8))
        ctk.CTkButton(barre, text="🔌  Tester", width=110,
                      fg_color=COULEURS["accent"],
                      command=self._tester).pack(side="left")
        ctk.CTkButton(barre, text="✓  Enregistrer et se connecter", width=210,
                      fg_color=COULEURS["vert"], hover_color="#166638",
                      command=self._valider).pack(side="right")

        ctk.CTkButton(self, text="Utiliser cet ordinateur seul (mode local)",
                      fg_color="transparent", text_color=COULEURS["gris"],
                      hover_color=COULEURS["fond"],
                      command=self._mode_local).pack(pady=(0, 14))

        self.update_idletasks()
        self.transient(parent)
        self.grab_set()
        self.wait_window(self)

    def _champ(self, parent, label, valeur=""):
        ctk.CTkLabel(parent, text=label, font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=COULEURS["texte"], anchor="w").pack(
                         fill="x", padx=16, pady=(10, 0))
        e = ctk.CTkEntry(parent)
        if valeur:
            e.insert(0, str(valeur))
        e.pack(fill="x", padx=16, pady=(2, 2))
        return e

    def _lire(self):
        try:
            port = int(self.e_port.get().strip() or "5000")
        except ValueError:
            port = 5000
        return self.e_hote.get().strip(), port, self.e_cle.get().strip()

    def _tester(self):
        import db_client
        hote, port, cle = self._lire()
        ok, message = db_client.tester_connexion(hote, port, cle)
        self.lbl_test.configure(
            text=("✅ " if ok else "❌ ") + message,
            text_color=(COULEURS["vert"] if ok else COULEURS["rouge"]))

    def _valider(self):
        import reseau
        hote, port, cle = self._lire()
        if not hote:
            erreur("Erreur", "Veuillez saisir l'adresse IP du serveur.")
            return
        reseau.sauvegarder({"mode": "client", "hote": hote,
                            "port": port, "cle": cle})
        self.resultat = True
        self.grab_release()
        self.destroy()

    def _mode_local(self):
        import reseau
        reseau.sauvegarder({"mode": "local"})
        self.resultat = True
        self.grab_release()
        self.destroy()
