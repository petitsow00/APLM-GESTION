# -*- coding: utf-8 -*-
"""
settings.py
------------
Gère les PARAMÈTRES personnalisables de l'agence (version standard).

Contrairement à config.py (qui contient les réglages techniques fixes),
ce fichier lit/écrit les informations que CHAQUE agence saisit elle-même
dans l'écran « Réglages » : nom, adresse, téléphone, monnaie, etc.

Ces informations sont enregistrées dans un simple fichier :
    data/parametres.json
Ainsi, une même version du logiciel peut servir à n'importe quelle agence.
"""

import os
import json
import config

# Emplacement du fichier de paramètres (dans le dossier de données)
PARAMS_PATH = os.path.join(config.DATA_DIR, "parametres.json")

# Valeurs par défaut : VIDES (l'agence doit saisir son nom).
# Seules la monnaie et la langue ont une valeur de départ.
_DEFAUTS = {
    "nom": "",
    "slogan": "",
    "adresse": "",
    "telephone": "",
    "email": "",
    "site_web": "",
    "rccm": "",
    "devise": "FCFA",
    "langue": "fr",
}

# Petite mémoire interne pour éviter de relire le fichier à chaque fois
_cache = None


def charger():
    """Renvoie tous les paramètres (dictionnaire), en complétant avec les
    valeurs par défaut si le fichier est absent ou incomplet."""
    global _cache
    if _cache is not None:
        return _cache
    donnees = dict(_DEFAUTS)
    if os.path.exists(PARAMS_PATH):
        try:
            with open(PARAMS_PATH, "r", encoding="utf-8") as f:
                enregistre = json.load(f)
            if isinstance(enregistre, dict):
                donnees.update({k: v for k, v in enregistre.items() if k in _DEFAUTS})
        except Exception:
            pass  # fichier abîmé -> on garde les valeurs par défaut
    _cache = donnees
    return _cache


def get(cle, defaut=""):
    """Renvoie la valeur d'un paramètre (ex: settings.get('nom'))."""
    return charger().get(cle, defaut)


def sauvegarder(nouvelles_valeurs):
    """Enregistre les paramètres saisis par l'agence dans data/parametres.json."""
    global _cache
    donnees = charger().copy()
    donnees.update({k: v for k, v in nouvelles_valeurs.items() if k in _DEFAUTS})
    os.makedirs(config.DATA_DIR, exist_ok=True)
    with open(PARAMS_PATH, "w", encoding="utf-8") as f:
        json.dump(donnees, f, ensure_ascii=False, indent=2)
    _cache = donnees
    return donnees


def nom_agence():
    """Nom à afficher ; renvoie un texte neutre si rien n'est encore saisi."""
    return get("nom") or ""


def devise():
    return get("devise") or "FCFA"


def est_configure():
    """True si l'agence a au moins renseigné son nom."""
    return bool(get("nom").strip())
