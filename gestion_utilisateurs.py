# -*- coding: utf-8 -*-
"""
gestion_utilisateurs.py
------------------------
Outil EN LIGNE DE COMMANDE (terminal) pour gérer les comptes utilisateurs
du logiciel APLM BUZNESS COMPANY, SANS ouvrir l'application.

On peut créer aussi bien un ADMINISTRATEUR qu'un AGENT.

------------------------------------------------------------------
COMMENT LANCER (dans le terminal, depuis le dossier APLM_Voyages) :

    python gestion_utilisateurs.py

Un menu s'affiche : créer un compte, lister les comptes, changer un mot de
passe, activer/désactiver un compte.

Option avancée : pointer une base précise (par ex. celle d'un serveur) :

    python gestion_utilisateurs.py --db "C:\\chemin\\vers\\aplm.db"
------------------------------------------------------------------

⚠️ Par défaut, l'outil travaille sur LA MÊME base que l'application installée
   (Documents\\APLM BUZNESS COMPANY\\data\\aplm.db) si elle existe ; sinon sur
   la base du dossier du projet (data\\aplm.db).

⚠️ En mode multi-postes, lancez cet outil sur l'ordinateur SERVEUR (celui qui
   détient la base).
"""

import os
import sys
import getpass

# Évite tout plantage d'affichage sur les terminaux Windows qui n'acceptent
# pas certains caractères (emojis...) : on remplace au lieu de planter.
try:
    sys.stdout.reconfigure(errors="replace")
except Exception:
    pass

import config


# ===========================================================================
#  1) Choix de la base de données à utiliser
# ===========================================================================
def choisir_base():
    """Détermine quel fichier de base utiliser (avec priorité au --db fourni)."""
    args = sys.argv[1:]
    if "--db" in args:
        i = args.index("--db")
        if i + 1 < len(args):
            return args[i + 1]

    # Base de l'application INSTALLÉE (version APLM)
    base_installee = os.path.join(
        os.path.expanduser("~"), "Documents", "APLM BUZNESS COMPANY",
        "data", "aplm.db")
    if os.path.exists(base_installee):
        return base_installee

    # Sinon : base du projet (mode développement)
    return config.DB_PATH


# On fixe la base AVANT d'importer database (qui lit config.DB_PATH)
config.DB_PATH = choisir_base()

# On force le mode LOCAL (accès direct au fichier, pas par le réseau)
import reseau
reseau._cache = {"mode": "local", "hote": "127.0.0.1", "port": 5000, "cle": ""}

import auth
import database as db
db.initialiser_base()


# ===========================================================================
#  2) Petits outils d'affichage / saisie
# ===========================================================================
def titre(texte):
    print()
    print("=" * 56)
    print("  " + texte)
    print("=" * 56)


def demander(question, obligatoire=False):
    while True:
        valeur = input(question).strip()
        if valeur or not obligatoire:
            return valeur
        print("  ⚠ Ce champ est obligatoire.")


def _saisir_secret(invite):
    """Saisie masquée si possible ; sinon saisie normale (secours).

    Si l'entrée n'est pas une vraie console (ex : réponses automatiques),
    on lit normalement pour éviter tout blocage."""
    try:
        if not sys.stdin.isatty():
            return input(invite)
        return getpass.getpass(invite)
    except Exception:
        return input(invite)


def demander_mot_de_passe():
    """Demande un mot de passe (masqué) avec confirmation et longueur mini."""
    while True:
        mdp = _saisir_secret("  Mot de passe (la saisie peut rester invisible) : ")
        if len(mdp) < 4:
            print("  ⚠ Le mot de passe doit contenir au moins 4 caractères.")
            continue
        mdp2 = _saisir_secret("  Confirmez le mot de passe : ")
        if mdp != mdp2:
            print("  ⚠ Les deux mots de passe ne sont pas identiques. Réessayez.")
            continue
        return mdp


def choisir_utilisateur():
    """Affiche la liste numérotée et renvoie l'id choisi (ou None)."""
    utilisateurs = db.lister_utilisateurs()
    if not utilisateurs:
        print("  (Aucun utilisateur enregistré.)")
        return None
    print()
    for i, u in enumerate(utilisateurs, start=1):
        etat = "actif" if u["actif"] else "INACTIF"
        print(f"  {i}. {u['identifiant']:<16} | {u['role']:<6} | "
              f"{(u['prenom'] or '') + ' ' + (u['nom'] or '')} | {etat}")
    choix = demander("\n  Numéro du compte (ou vide pour annuler) : ")
    if not choix.isdigit():
        return None
    n = int(choix)
    if 1 <= n <= len(utilisateurs):
        return utilisateurs[n - 1]["id"]
    return None


# ===========================================================================
#  3) Actions
# ===========================================================================
def creer_compte(role):
    role_txt = "ADMINISTRATEUR" if role == "admin" else "AGENT"
    titre(f"Créer un {role_txt}")
    nom = demander("  Nom : ", obligatoire=True)
    prenom = demander("  Prénom : ")
    identifiant = demander("  Identifiant de connexion : ", obligatoire=True)
    email = demander("  E-mail (facultatif) : ")
    # Mot de passe par défaut Teranga99 ; l'utilisateur devra le changer
    # à sa première connexion (doit_changer_mdp=1).
    try:
        db.creer_utilisateur(nom=nom, prenom=prenom, identifiant=identifiant,
                             mot_de_passe=auth.MOT_DE_PASSE_DEFAUT, email=email,
                             role=role, actif=1, doit_changer_mdp=1)
        print(f"\n  [OK] Compte {role_txt} « {identifiant} » créé avec succès.")
        print(f"       Mot de passe par défaut : {auth.MOT_DE_PASSE_DEFAUT}")
        print("       -> L'utilisateur devra le changer à sa première connexion.")
    except ValueError as e:
        print(f"\n  [ERREUR] {e}")


def lister():
    titre("Liste des utilisateurs")
    utilisateurs = db.lister_utilisateurs()
    if not utilisateurs:
        print("  (Aucun utilisateur enregistré.)")
        return
    print(f"  {'IDENTIFIANT':<18}{'RÔLE':<10}{'NOM':<26}{'ÉTAT'}")
    print("  " + "-" * 58)
    for u in utilisateurs:
        etat = "actif" if u["actif"] else "INACTIF"
        nom = f"{u['prenom'] or ''} {u['nom'] or ''}".strip()
        print(f"  {u['identifiant']:<18}{u['role']:<10}{nom:<26}{etat}")


def changer_mdp():
    titre("Changer un mot de passe")
    uid = choisir_utilisateur()
    if uid is None:
        print("  Annulé.")
        return
    mdp = demander_mot_de_passe()
    db.changer_mot_de_passe(uid, mdp)
    print("\n  ✅ Mot de passe modifié.")


def basculer_actif():
    titre("Activer / Désactiver un compte")
    uid = choisir_utilisateur()
    if uid is None:
        print("  Annulé.")
        return
    u = db.get_utilisateur(uid)
    nouvel_etat = 0 if u["actif"] else 1
    if u["role"] == "admin" and nouvel_etat == 0 and db.compter_admins_actifs() <= 1:
        print("\n  ❌ Impossible : il doit rester au moins un administrateur actif.")
        return
    db.definir_actif(uid, nouvel_etat)
    print(f"\n  ✅ Compte « {u['identifiant']} » "
          f"{'activé' if nouvel_etat else 'désactivé'}.")


# ===========================================================================
#  4) Menu principal
# ===========================================================================
def menu():
    print()
    print("****************************************************")
    print("*   APLM BUZNESS COMPANY - GESTION DES COMPTES     *")
    print("****************************************************")
    print(f"  Base utilisée : {config.DB_PATH}")
    print(f"  Comptes existants : {db.compter_utilisateurs()}")

    while True:
        print()
        print("  1 - Créer un ADMINISTRATEUR")
        print("  2 - Créer un AGENT")
        print("  3 - Lister les utilisateurs")
        print("  4 - Changer un mot de passe")
        print("  5 - Activer / Désactiver un compte")
        print("  0 - Quitter")
        choix = input("\n  Votre choix : ").strip()

        if choix == "1":
            creer_compte("admin")
        elif choix == "2":
            creer_compte("agent")
        elif choix == "3":
            lister()
        elif choix == "4":
            changer_mdp()
        elif choix == "5":
            basculer_actif()
        elif choix == "0":
            print("\n  À bientôt !\n")
            break
        else:
            print("  ⚠ Choix invalide.")


if __name__ == "__main__":
    menu()
