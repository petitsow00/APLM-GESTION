# -*- coding: utf-8 -*-
"""
reseau.py
----------
Configuration du MODE RÉSEAU de l'application (multi-postes sur le réseau
local du bureau).

Trois modes possibles :

  - "local"   : l'ordinateur travaille SEUL, sur sa propre base (comme avant).
  - "serveur" : CET ordinateur détient la base ET la partage sur le réseau
                local ; les autres postes s'y connectent.
  - "client"  : CET ordinateur n'a pas la base ; il se connecte au serveur
                (par son adresse IP) pour lire/écrire les mêmes données.

Ces réglages sont enregistrés dans un petit fichier : data/reseau.json.
Une CLÉ partagée (mot de passe technique) protège l'accès au serveur.

SÉCURITÉ : chaque installation génère automatiquement sa PROPRE clé
aléatoire au tout premier lancement (au lieu d'une valeur identique pour
tous les clients du logiciel). Pour connecter un autre poste (Windows ou
Mac), l'administrateur copie cette clé depuis Réglages réseau (sur le PC
serveur) et la colle sur le poste qui rejoint le serveur. Une installation
déjà configurée AVANT cette mise à jour garde sa clé actuelle (rien n'est
changé automatiquement sur une base existante).
"""

import os
import json
import socket
import secrets
import config

RESEAU_PATH = os.path.join(config.DATA_DIR, "reseau.json")

_DEFAUTS = {
    "mode": "local",              # local | serveur | client
    "hote": "127.0.0.1",          # adresse IP du serveur (pour un client)
    "port": 5000,                 # port réseau utilisé
    "cle": "",                    # générée automatiquement au 1er lancement (voir charger())
}

_cache = None


def _generer_cle_aleatoire():
    """Clé propre à CETTE installation (16 caractères hexadécimaux) —
    personne d'autre ne peut la deviner, contrairement à une valeur fixe
    partagée par toutes les installations du logiciel."""
    return secrets.token_hex(8)


def charger():
    global _cache
    if _cache is not None:
        return _cache
    donnees = dict(_DEFAUTS)
    premiere_fois = not os.path.exists(RESEAU_PATH)
    if not premiere_fois:
        try:
            with open(RESEAU_PATH, "r", encoding="utf-8") as f:
                enreg = json.load(f)
            if isinstance(enreg, dict):
                donnees.update({k: v for k, v in enreg.items() if k in _DEFAUTS})
        except Exception:
            pass
    a_generer = not donnees.get("cle")
    if a_generer:
        # 1er lancement (ou fichier sans clé) : on génère et on fixe
        # immédiatement une clé unique, pour que le serveur et ce poste
        # utilisent toujours la même valeur par la suite.
        donnees["cle"] = _generer_cle_aleatoire()
    _cache = donnees
    if a_generer:
        sauvegarder(donnees)
    return _cache


def sauvegarder(nouvelles_valeurs):
    global _cache
    donnees = charger().copy()
    donnees.update({k: v for k, v in nouvelles_valeurs.items() if k in _DEFAUTS})
    # Normalise le port en entier
    try:
        donnees["port"] = int(donnees["port"])
    except (ValueError, TypeError):
        donnees["port"] = 5000
    os.makedirs(config.DATA_DIR, exist_ok=True)
    with open(RESEAU_PATH, "w", encoding="utf-8") as f:
        json.dump(donnees, f, ensure_ascii=False, indent=2)
    _cache = donnees
    return donnees


def get(cle, defaut=None):
    return charger().get(cle, defaut)


def mode():
    return charger().get("mode", "local")


def est_client():
    return mode() == "client"


def est_serveur():
    return mode() == "serveur"


def hote():
    return charger().get("hote", "127.0.0.1")


def port():
    try:
        return int(charger().get("port", 5000))
    except (ValueError, TypeError):
        return 5000


def cle():
    return charger().get("cle", "")


def adresse_ip_locale():
    """Devine l'adresse IP de CET ordinateur sur le réseau local
    (celle à communiquer aux autres postes). Renvoie '127.0.0.1' en cas d'échec."""
    ip = "127.0.0.1"
    try:
        # Astuce : on ouvre une "fausse" connexion sortante pour connaître
        # l'IP de la carte réseau utilisée (aucune donnée n'est envoyée).
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
    except Exception:
        try:
            ip = socket.gethostbyname(socket.gethostname())
        except Exception:
            pass
    return ip
