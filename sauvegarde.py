# -*- coding: utf-8 -*-
"""
sauvegarde.py
--------------
Sauvegardes AUTOMATIQUES de la base de données.

But : ne JAMAIS perdre les données de l'agence.

Fonctionnement :
    - À chaque ouverture du logiciel, on fait une copie de la base dans un
      dossier « Sauvegardes », avec la date du jour dans le nom du fichier.
    - Une seule sauvegarde par jour (si celle du jour existe déjà, on ne
      refait rien).
    - On conserve les 30 dernières sauvegardes (les plus anciennes sont
      effacées automatiquement) pour ne pas encombrer le disque.

La copie utilise l'outil intégré de SQLite (méthode « backup »), qui produit
une copie fiable même si la base est en cours d'utilisation.

⚠️ En mode « client » (multi-postes), il n'y a pas de base locale à copier :
   c'est le PC SERVEUR qui détient la base et fait les sauvegardes.
"""

import os
import glob
import sqlite3
from datetime import datetime

import config


def dossier_sauvegardes():
    """Renvoie (et crée si besoin) le dossier où sont rangées les sauvegardes."""
    dossier = os.path.join(config.APP_HOME, "Sauvegardes")
    os.makedirs(dossier, exist_ok=True)
    return dossier


def _copier_base(source, destination):
    """Copie fiable de la base SQLite (méthode backup)."""
    src = sqlite3.connect(source)
    dst = sqlite3.connect(destination)
    try:
        with dst:
            src.backup(dst)
    finally:
        src.close()
        dst.close()


def sauvegarde_auto(max_sauvegardes=30):
    """Fait la sauvegarde du jour si elle n'existe pas encore.
    Renvoie le chemin de la sauvegarde, ou None si rien n'a été fait."""
    # Pas de base locale à sauvegarder en mode client
    try:
        import reseau
        if reseau.est_client():
            return None
    except Exception:
        pass

    if not os.path.exists(config.DB_PATH):
        return None

    dossier = dossier_sauvegardes()
    nom = "aplm_" + datetime.now().strftime("%Y-%m-%d") + ".db"
    destination = os.path.join(dossier, nom)

    if not os.path.exists(destination):
        try:
            _copier_base(config.DB_PATH, destination)
        except Exception:
            return None

    _nettoyer(dossier, max_sauvegardes)
    return destination


def sauvegarde_manuelle():
    """Force une sauvegarde immédiate (avec l'heure dans le nom, pour ne pas
    écraser celle du jour). Renvoie le chemin créé, ou None en cas d'échec."""
    try:
        import reseau
        if reseau.est_client():
            return None
    except Exception:
        pass
    if not os.path.exists(config.DB_PATH):
        return None
    dossier = dossier_sauvegardes()
    nom = "aplm_" + datetime.now().strftime("%Y-%m-%d_%Hh%M") + ".db"
    destination = os.path.join(dossier, nom)
    try:
        _copier_base(config.DB_PATH, destination)
    except Exception:
        return None
    return destination


def _nettoyer(dossier, maximum):
    """Ne garde que les `maximum` sauvegardes les plus récentes."""
    fichiers = sorted(glob.glob(os.path.join(dossier, "aplm_*.db")))
    if len(fichiers) > maximum:
        for vieux in fichiers[:len(fichiers) - maximum]:
            try:
                os.remove(vieux)
            except Exception:
                pass
