# -*- coding: utf-8 -*-
"""
auth.py
--------
Sécurité des comptes utilisateurs du logiciel APLM BUZNESS COMPANY.

Ce fichier s'occupe de DEUX choses simples :

  1) LES MOTS DE PASSE
     On ne stocke JAMAIS le mot de passe en clair dans la base.
     On enregistre une version "chiffrée" (impossible à relire) grâce à
     l'outil `hashlib` qui est DÉJÀ inclus dans Python (rien à installer).

  2) L'UTILISATEUR CONNECTÉ ("la session")
     Une fois qu'une personne s'est connectée, on retient son compte ici,
     pour savoir « qui fait quoi » (traçabilité) partout dans le logiciel.
"""

import hashlib
import hmac
import os


# ===========================================================================
#  1) MOTS DE PASSE (chiffrement sécurisé)
# ===========================================================================
# On utilise PBKDF2 (un standard reconnu) avec :
#   - un "sel" (salt) : une valeur aléatoire différente pour chaque compte,
#     qui empêche de deviner deux mots de passe identiques.
#   - un grand nombre de répétitions : rend le calcul volontairement lent,
#     ce qui protège contre les tentatives de piratage par essais.
_NB_ITERATIONS = 200_000

# Mot de passe attribué par défaut à chaque nouveau compte créé par un
# administrateur. L'utilisateur DEVRA le changer à sa première connexion.
MOT_DE_PASSE_DEFAUT = "Teranga99"


def chiffrer_mot_de_passe(mot_de_passe, sel_hex=None):
    """Chiffre un mot de passe.

    Renvoie un couple (sel_hex, empreinte_hex) :
      - sel_hex      : le "sel" aléatoire, à conserver dans la base
      - empreinte_hex: la version chiffrée du mot de passe

    Si on fournit un `sel_hex` existant, on réutilise ce même sel
    (utile pour VÉRIFIER un mot de passe lors de la connexion).
    """
    if sel_hex is None:
        sel = os.urandom(16)                 # 16 octets aléatoires
        sel_hex = sel.hex()
    else:
        sel = bytes.fromhex(sel_hex)

    empreinte = hashlib.pbkdf2_hmac(
        "sha256",
        mot_de_passe.encode("utf-8"),
        sel,
        _NB_ITERATIONS,
    )
    return sel_hex, empreinte.hex()


def verifier_mot_de_passe(mot_de_passe, sel_hex, empreinte_attendue_hex):
    """Vérifie qu'un mot de passe saisi correspond bien à l'empreinte stockée.
    Renvoie True si le mot de passe est correct, False sinon."""
    if not sel_hex or not empreinte_attendue_hex:
        return False
    _, empreinte_calculee = chiffrer_mot_de_passe(mot_de_passe, sel_hex)
    # Comparaison sécurisée (résistante à certaines attaques de mesure du temps)
    return hmac.compare_digest(empreinte_calculee, empreinte_attendue_hex)


# ===========================================================================
#  2) UTILISATEUR CONNECTÉ (session en mémoire)
# ===========================================================================
# On garde ici, en mémoire, le compte de la personne actuellement connectée.
# C'est remis à zéro à chaque démarrage du logiciel (il faut se reconnecter).
_utilisateur_courant = None


def definir_utilisateur_courant(utilisateur):
    """Enregistre l'utilisateur qui vient de se connecter.
    `utilisateur` est une ligne de la table `utilisateurs` (ou un dictionnaire)."""
    global _utilisateur_courant
    _utilisateur_courant = utilisateur


def deconnecter():
    """Oublie l'utilisateur connecté (déconnexion)."""
    global _utilisateur_courant
    _utilisateur_courant = None


def utilisateur_courant():
    """Renvoie l'utilisateur connecté, ou None si personne n'est connecté."""
    return _utilisateur_courant


def est_connecte():
    return _utilisateur_courant is not None


def id_courant():
    """Renvoie l'identifiant (id) de l'utilisateur connecté, ou None."""
    if _utilisateur_courant is None:
        return None
    try:
        return _utilisateur_courant["id"]
    except Exception:
        return None


def nom_courant():
    """Renvoie le nom complet de l'utilisateur connecté (pour l'affichage)."""
    if _utilisateur_courant is None:
        return ""
    try:
        nom = (_utilisateur_courant["nom"] or "").strip()
        prenom = (_utilisateur_courant["prenom"] or "").strip()
        complet = f"{prenom} {nom}".strip()
        return complet or (_utilisateur_courant["identifiant"] or "")
    except Exception:
        return ""


def est_admin():
    """Renvoie True si l'utilisateur connecté est administrateur."""
    if _utilisateur_courant is None:
        return False
    try:
        return (_utilisateur_courant["role"] or "").lower() == "admin"
    except Exception:
        return False


# ===========================================================================
#  3) PERMISSIONS DÉTAILLÉES (ce que chaque agent a le droit de faire)
# ===========================================================================
# L'ADMINISTRATEUR a TOUJOURS toutes les permissions (rien à cocher pour lui).
# Pour un AGENT, l'administrateur coche ce qu'il a le droit de faire.
# Chaque permission a une "clé" (mot de code) et un texte affiché (via i18n).
PERMISSIONS = [
    ("gerer_clients",       "perm_gerer_clients"),
    ("gerer_dossiers",      "perm_gerer_dossiers"),
    ("encaisser_paiements", "perm_encaisser_paiements"),
    ("generer_recus",       "perm_generer_recus"),
    ("gerer_avoirs",        "perm_gerer_avoirs"),
    ("gerer_depenses",      "perm_gerer_depenses"),
    ("voir_finances",       "perm_voir_finances"),
    ("voir_comptabilite",   "perm_voir_comptabilite"),
    ("supprimer",           "perm_supprimer"),
]

# Liste des clés seules (pratique pour les vérifications)
CLES_PERMISSIONS = [cle for cle, _ in PERMISSIONS]


def permissions_courantes():
    """Renvoie la liste des permissions (clés) de l'utilisateur connecté.
    Un administrateur reçoit TOUTES les permissions."""
    if est_admin():
        return list(CLES_PERMISSIONS)
    if _utilisateur_courant is None:
        return []
    try:
        brut = _utilisateur_courant["permissions"] or ""
    except Exception:
        brut = ""
    return [p.strip() for p in brut.split(",") if p.strip()]


def a_permission(cle):
    """Renvoie True si l'utilisateur connecté a le droit `cle`.
    L'administrateur a toujours tout ; sinon on regarde ses permissions."""
    if est_admin():
        return True
    return cle in permissions_courantes()
