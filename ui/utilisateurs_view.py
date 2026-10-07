# -*- coding: utf-8 -*-
"""
ui/utilisateurs_view.py
------------------------
Écran de GESTION DES UTILISATEURS (réservé à l'administrateur).

L'administrateur peut :
  - créer un nouvel utilisateur (agent ou autre administrateur) ;
  - modifier ses informations ;
  - changer son mot de passe ;
  - l'activer / le désactiver ;
  - le supprimer.

Deux sécurités importantes :
  - on ne peut pas désactiver / supprimer SON PROPRE compte ;
  - il doit toujours rester au moins UN administrateur actif.
"""

import tkinter as tk
from tkinter import ttk
import customtkinter as ctk

import database as db
import auth
from i18n import t
from ui.helpers import COULEURS, info, erreur, confirmer


def _role_vers_texte(role):
    """Traduit le code du rôle ('admin'/'agent') en texte affichable."""
    code = (role or "").lower()
    if code == "admin":
        return t("role_admin")
    if code == "agent":
        return t("role_agent")
    return role or ""


class UtilisateursView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=COULEURS["fond"])
        self._construire()
        self.rafraichir()

    def _construire(self):
        # --- Titre ---
        ctk.CTkLabel(self, text=t("users_titre"),
                     font=ctk.CTkFont(size=26, weight="bold"),
                     text_color=COULEURS["primaire"]).pack(
                         anchor="w", padx=30, pady=(26, 4))
        ctk.CTkLabel(self, text=t("users_intro"),
                     font=ctk.CTkFont(size=13), text_color=COULEURS["gris"],
                     justify="left").pack(anchor="w", padx=30, pady=(0, 14))

        # --- Barre de boutons ---
        barre = ctk.CTkFrame(self, fg_color="transparent")
        barre.pack(fill="x", padx=30, pady=(0, 10))

        ctk.CTkButton(barre, text="➕  " + t("btn_nouvel_utilisateur"),
                      fg_color=COULEURS["vert"], hover_color="#166638",
                      command=self._nouvel_utilisateur).pack(side="left")
        ctk.CTkButton(barre, text="✏  " + t("btn_modifier"),
                      fg_color=COULEURS["accent"],
                      command=self._modifier).pack(side="left", padx=(8, 0))
        ctk.CTkButton(barre, text="🔑  " + t("btn_changer_mdp"),
                      fg_color=COULEURS["primaire2"],
                      command=self._changer_mdp).pack(side="left", padx=(8, 0))
        ctk.CTkButton(barre, text="♻  " + t("btn_reinit_mdp"),
                      fg_color="#e67e22", hover_color="#ca6f1e",
                      command=self._reinitialiser_mdp).pack(side="left", padx=(8, 0))
        ctk.CTkButton(barre, text="⏻  " + t("btn_activer") + " / " + t("btn_desactiver"),
                      fg_color=COULEURS["gris"], hover_color="#555",
                      command=self._basculer_actif).pack(side="left", padx=(8, 0))
        ctk.CTkButton(barre, text="🗑  " + t("btn_supprimer"),
                      fg_color=COULEURS["rouge"], hover_color="#922b21",
                      command=self._supprimer).pack(side="right")

        # --- Tableau des utilisateurs ---
        cadre = ctk.CTkFrame(self, fg_color=COULEURS["carte"], corner_radius=10)
        cadre.pack(fill="both", expand=True, padx=30, pady=(0, 20))

        colonnes = ("nom", "identifiant", "email", "role", "statut")
        self.tableau = ttk.Treeview(cadre, columns=colonnes, show="headings",
                                    selectmode="browse")
        entetes = {
            "nom": t("col_nom_prenom"), "identifiant": t("champ_identifiant"),
            "email": t("champ_email"), "role": t("col_role"),
            "statut": t("col_statut"),
        }
        largeurs = {"nom": 200, "identifiant": 160, "email": 200,
                    "role": 130, "statut": 90}
        for c in colonnes:
            self.tableau.heading(c, text=entetes[c])
            self.tableau.column(c, width=largeurs[c], anchor="w")

        scroll = ttk.Scrollbar(cadre, orient="vertical",
                               command=self.tableau.yview)
        self.tableau.configure(yscrollcommand=scroll.set)
        self.tableau.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        scroll.pack(side="right", fill="y", pady=10, padx=(0, 10))

        # Mémorise l'id de chaque ligne affichée
        self._ids = {}

    # ------------------------------------------------------------------ #
    def rafraichir(self):
        for ligne in self.tableau.get_children():
            self.tableau.delete(ligne)
        self._ids = {}
        for u in db.lister_utilisateurs():
            nom_complet = f'{u["prenom"] or ""} {u["nom"] or ""}'.strip()
            statut = t("statut_actif") if u["actif"] else t("statut_inactif")
            item = self.tableau.insert("", "end", values=(
                nom_complet, u["identifiant"], u["email"] or "",
                _role_vers_texte(u["role"]), statut))
            self._ids[item] = u["id"]

    def _selection_id(self):
        """Renvoie l'id de l'utilisateur sélectionné, ou None."""
        sel = self.tableau.selection()
        if not sel:
            info("Info", t("msg_selectionner"))
            return None
        return self._ids.get(sel[0])

    # ------------------------------------------------------------------ #
    def _nouvel_utilisateur(self):
        dlg = _DialogueUtilisateur(self, mode="creer")
        if dlg.resultat is None:
            return
        d = dlg.resultat
        try:
            db.creer_utilisateur(nom=d["nom"], prenom=d["prenom"],
                                 identifiant=d["identifiant"], email=d["email"],
                                 mot_de_passe=auth.MOT_DE_PASSE_DEFAUT,
                                 role=d["role"], actif=d["actif"],
                                 doit_changer_mdp=1,
                                 permissions=d.get("permissions", ""))
            info("Info", t("msg_utilisateur_cree") + "\n\n"
                 + t("mdp_defaut_info").format(mdp=auth.MOT_DE_PASSE_DEFAUT))
            self.rafraichir()
        except ValueError as e:
            erreur("Erreur", str(e))

    def _modifier(self):
        uid = self._selection_id()
        if uid is None:
            return
        u = db.get_utilisateur(uid)
        valeurs = {
            "nom": u["nom"], "prenom": u["prenom"] or "",
            "identifiant": u["identifiant"], "email": u["email"] or "",
            "role": u["role"], "actif": u["actif"],
        }
        dlg = _DialogueUtilisateur(self, mode="modifier", valeurs=valeurs)
        if dlg.resultat is None:
            return
        d = dlg.resultat

        # Sécurité : ne pas retirer le dernier administrateur actif
        if u["role"] == "admin" and (d["role"] != "admin" or not d["actif"]):
            if db.compter_admins_actifs() <= 1:
                erreur("Erreur", t("msg_dernier_admin"))
                return
        try:
            db.modifier_utilisateur(uid, nom=d["nom"], prenom=d["prenom"],
                                    identifiant=d["identifiant"], email=d["email"],
                                    role=d["role"], actif=d["actif"])
            info("Info", t("msg_enregistre"))
            self.rafraichir()
        except ValueError as e:
            erreur("Erreur", str(e))

    def _changer_mdp(self):
        uid = self._selection_id()
        if uid is None:
            return
        dlg = _DialogueMotDePasse(self)
        if dlg.resultat is None:
            return
        db.changer_mot_de_passe(uid, dlg.resultat)
        info("Info", t("msg_mdp_change"))

    def _reinitialiser_mdp(self):
        uid = self._selection_id()
        if uid is None:
            return
        if not confirmer(t("btn_reinit_mdp"),
                         t("msg_reinit_ok").format(mdp=auth.MOT_DE_PASSE_DEFAUT)):
            return
        db.reinitialiser_mot_de_passe(uid)
        info("Info", t("msg_reinit_ok").format(mdp=auth.MOT_DE_PASSE_DEFAUT))

    def _basculer_actif(self):
        uid = self._selection_id()
        if uid is None:
            return
        if uid == auth.id_courant():
            erreur("Erreur", t("msg_pas_soi_meme"))
            return
        u = db.get_utilisateur(uid)
        nouvel_etat = 0 if u["actif"] else 1
        # Sécurité : garder au moins un administrateur actif
        if u["role"] == "admin" and nouvel_etat == 0 and db.compter_admins_actifs() <= 1:
            erreur("Erreur", t("msg_dernier_admin"))
            return
        db.definir_actif(uid, nouvel_etat)
        self.rafraichir()

    def _supprimer(self):
        uid = self._selection_id()
        if uid is None:
            return
        if uid == auth.id_courant():
            erreur("Erreur", t("msg_pas_soi_meme"))
            return
        u = db.get_utilisateur(uid)
        if u["role"] == "admin" and db.compter_admins_actifs() <= 1:
            erreur("Erreur", t("msg_dernier_admin"))
            return
        if not confirmer(t("btn_supprimer"), t("msg_confirmer_suppr")):
            return
        db.supprimer_utilisateur(uid)
        self.rafraichir()


# ===========================================================================
#  Boîtes de dialogue dédiées (avec mots de passe masqués)
# ===========================================================================
class _DialogueUtilisateur(ctk.CTkToplevel):
    """Formulaire de création / modification d'un utilisateur.
    En mode 'creer', on demande aussi le mot de passe (masqué)."""

    def __init__(self, parent, mode="creer", valeurs=None):
        super().__init__(parent)
        self.resultat = None
        self._mode = mode
        valeurs = valeurs or {}

        titre = t("titre_nouvel_utilisateur") if mode == "creer" \
            else t("titre_modifier_utilisateur")
        self.title(titre)
        self.configure(fg_color=COULEURS["fond"])
        self.resizable(False, False)

        ctk.CTkLabel(self, text=titre,
                     font=ctk.CTkFont(size=18, weight="bold"),
                     text_color=COULEURS["primaire"]).pack(
                         padx=22, pady=(18, 8), anchor="w")

        zone = ctk.CTkFrame(self, fg_color=COULEURS["carte"], corner_radius=12)
        zone.pack(fill="both", expand=True, padx=22, pady=6)

        self.e_nom = self._champ(zone, t("champ_nom"), valeurs.get("nom", ""))
        self.e_prenom = self._champ(zone, t("champ_prenom"), valeurs.get("prenom", ""))
        self.e_identifiant = self._champ(zone, t("champ_identifiant"),
                                         valeurs.get("identifiant", ""))
        self.e_email = self._champ(zone, t("champ_email"), valeurs.get("email", ""))

        # Rôle (menu déroulant)
        ctk.CTkLabel(zone, text=t("champ_role"),
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=COULEURS["texte"], anchor="w").pack(
                         fill="x", padx=16, pady=(8, 0))
        role_actuel = (valeurs.get("role") or "agent").lower()
        self.var_role = ctk.StringVar(
            value=t("role_admin") if role_actuel == "admin" else t("role_agent"))
        ctk.CTkOptionMenu(zone, values=[t("role_agent"), t("role_admin")],
                          variable=self.var_role,
                          fg_color=COULEURS["primaire"],
                          button_color=COULEURS["primaire2"]).pack(
                              fill="x", padx=16, pady=(2, 4))

        # Compte actif (case à cocher)
        self.var_actif = ctk.BooleanVar(value=bool(valeurs.get("actif", 1)))
        ctk.CTkCheckBox(zone, text=t("champ_actif"), variable=self.var_actif,
                        fg_color=COULEURS["vert"]).pack(
                            anchor="w", padx=16, pady=(6, 8))

        # --- Permissions détaillées (pour un agent) ---
        ctk.CTkLabel(zone, text=t("perm_titre"),
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=COULEURS["primaire"], anchor="w").pack(
                         fill="x", padx=16, pady=(8, 0))
        ctk.CTkLabel(zone, text=t("perm_note_admin"),
                     font=ctk.CTkFont(size=10), text_color=COULEURS["gris"],
                     anchor="w", wraplength=430, justify="left").pack(
                         fill="x", padx=16, pady=(0, 2))
        perms_existantes = set(
            p.strip() for p in (valeurs.get("permissions") or "").split(",")
            if p.strip())
        zone_perms = ctk.CTkScrollableFrame(zone, fg_color=COULEURS["fond"],
                                            height=170)
        zone_perms.pack(fill="x", padx=16, pady=(2, 8))
        self.vars_perms = {}
        for cle, cle_i18n in auth.PERMISSIONS:
            var = ctk.BooleanVar(value=(cle in perms_existantes))
            ctk.CTkCheckBox(zone_perms, text=t(cle_i18n), variable=var,
                            fg_color=COULEURS["vert"]).pack(
                                anchor="w", padx=6, pady=3)
            self.vars_perms[cle] = var

        # Mot de passe : à la création, on utilise le mot de passe par défaut
        # (Teranga99) que l'utilisateur devra changer à sa première connexion.
        if mode == "creer":
            ctk.CTkLabel(zone,
                         text="🔑  " + t("mdp_defaut_info").format(
                             mdp=auth.MOT_DE_PASSE_DEFAUT),
                         font=ctk.CTkFont(size=12),
                         text_color=COULEURS["primaire"],
                         wraplength=440, justify="left").pack(
                             fill="x", padx=16, pady=(10, 8))

        # Boutons
        barre = ctk.CTkFrame(self, fg_color="transparent")
        barre.pack(fill="x", padx=22, pady=(8, 16))
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

    def _champ(self, parent, label, valeur="", secret=False):
        ctk.CTkLabel(parent, text=label,
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=COULEURS["texte"], anchor="w").pack(
                         fill="x", padx=16, pady=(8, 0))
        champ = ctk.CTkEntry(parent, show="•" if secret else "")
        if valeur:
            champ.insert(0, str(valeur))
        champ.pack(fill="x", padx=16, pady=(2, 2))
        return champ

    def _valider(self):
        nom = self.e_nom.get().strip()
        identifiant = self.e_identifiant.get().strip()
        if not nom or not identifiant:
            erreur("Erreur", t("msg_champs_requis"))
            return
        role = "admin" if self.var_role.get() == t("role_admin") else "agent"
        permissions = ",".join(cle for cle, var in self.vars_perms.items()
                               if var.get())
        resultat = {
            "nom": nom,
            "prenom": self.e_prenom.get().strip(),
            "identifiant": identifiant,
            "email": self.e_email.get().strip(),
            "role": role,
            "actif": 1 if self.var_actif.get() else 0,
            "permissions": permissions,
        }
        self.resultat = resultat
        self.grab_release()
        self.destroy()

    def _annuler(self):
        self.resultat = None
        self.grab_release()
        self.destroy()


class _DialogueMotDePasse(ctk.CTkToplevel):
    """Petit formulaire pour saisir un nouveau mot de passe (masqué, confirmé)."""

    def __init__(self, parent):
        super().__init__(parent)
        self.resultat = None
        self.title(t("titre_changer_mdp"))
        self.configure(fg_color=COULEURS["fond"])
        self.resizable(False, False)

        ctk.CTkLabel(self, text=t("titre_changer_mdp"),
                     font=ctk.CTkFont(size=18, weight="bold"),
                     text_color=COULEURS["primaire"]).pack(
                         padx=22, pady=(18, 8), anchor="w")

        zone = ctk.CTkFrame(self, fg_color=COULEURS["carte"], corner_radius=12)
        zone.pack(fill="both", expand=True, padx=22, pady=6)

        ctk.CTkLabel(zone, text=t("champ_nouveau_mdp"),
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=COULEURS["texte"], anchor="w").pack(
                         fill="x", padx=16, pady=(10, 0))
        self.e_mdp = ctk.CTkEntry(zone, show="•")
        self.e_mdp.pack(fill="x", padx=16, pady=(2, 2))

        ctk.CTkLabel(zone, text=t("champ_mdp_confirm"),
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=COULEURS["texte"], anchor="w").pack(
                         fill="x", padx=16, pady=(8, 0))
        self.e_mdp2 = ctk.CTkEntry(zone, show="•")
        self.e_mdp2.pack(fill="x", padx=16, pady=(2, 10))

        barre = ctk.CTkFrame(self, fg_color="transparent")
        barre.pack(fill="x", padx=22, pady=(8, 16))
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

    def _valider(self):
        mdp = self.e_mdp.get()
        mdp2 = self.e_mdp2.get()
        if not mdp:
            erreur("Erreur", t("msg_champs_requis"))
            return
        if len(mdp) < 4:
            erreur("Erreur", t("msg_mdp_court"))
            return
        if mdp != mdp2:
            erreur("Erreur", t("msg_mdp_differents"))
            return
        self.resultat = mdp
        self.grab_release()
        self.destroy()

    def _annuler(self):
        self.resultat = None
        self.grab_release()
        self.destroy()
