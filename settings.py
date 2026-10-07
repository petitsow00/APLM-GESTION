# -*- coding: utf-8 -*-
"""
settings.py
------------
Gère les PARAMÈTRES personnalisables de l'agence (version standard).

Depuis cette version, ces informations sont enregistrées dans la base de
données PARTAGÉE (table `parametres_agence`, voir database.py) et non plus
dans un simple fichier local. Résultat concret : sur un poste en mode
« serveur » ou « client » (multi-postes, Windows comme Mac), tous les
ordinateurs connectés affichent exactement les mêmes coordonnées d'agence
et le même logo sur les reçus — une seule saisie suffit, où que ce soit.

Un fichier local (data/parametres.json) sert UNIQUEMENT de copie de secours :
affichage instantané sans attendre le réseau, et poursuite du travail si la
connexion au serveur est momentanément coupée. La base de données reste la
source de vérité :
    - charger()      : lecture instantanée du cache local (aucun réseau).
    - synchroniser() : va chercher la version la plus récente partagée.
    - sauvegarder()  : écrit d'abord dans la base partagée, puis met à jour
                       le cache local si l'écriture a réussi.
"""

import os
import json
import base64
import config

# Même emplacement que l'ancien fichier de réglages : une installation déjà
# configurée avant cette mise à jour retrouve directement ses valeurs (elles
# servent alors de point de départ, migré automatiquement vers la base
# partagée lors de la première synchronisation - voir synchroniser()).
CACHE_PATH = os.path.join(config.DATA_DIR, "parametres.json")

_DEFAUTS = {
    "nom": "",
    "slogan": "",
    "adresse": "",
    "telephone": "",
    "email": "",
    "site_web": "",
    "rccm": "",
    "devise": "FCFA",
}

_cache = None


def _charger_fichier_cache():
    donnees = dict(_DEFAUTS)
    if os.path.exists(CACHE_PATH):
        try:
            with open(CACHE_PATH, "r", encoding="utf-8") as f:
                enregistre = json.load(f)
            if isinstance(enregistre, dict):
                donnees.update({k: v for k, v in enregistre.items() if k in _DEFAUTS})
        except Exception:
            pass  # fichier abîmé -> on garde les valeurs par défaut
    return donnees


def _ecrire_fichier_cache(donnees):
    try:
        os.makedirs(config.DATA_DIR, exist_ok=True)
        with open(CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump({k: donnees.get(k, "") for k in _DEFAUTS}, f,
                      ensure_ascii=False, indent=2)
    except Exception:
        pass  # le cache local est un confort, pas une obligation


def charger():
    """Renvoie les paramètres actuellement connus (cache local), SANS accès
    réseau — rapide, toujours disponible même hors connexion au serveur.
    Appeler synchroniser() pour aller chercher la version la plus récente
    partagée par les autres postes."""
    global _cache
    if _cache is None:
        _cache = _charger_fichier_cache()
    return _cache


def get(cle, defaut=""):
    """Renvoie la valeur d'un paramètre (ex: settings.get('nom'))."""
    return charger().get(cle, defaut)


def nom_agence():
    """Nom à afficher ; renvoie un texte neutre si rien n'est encore saisi."""
    return get("nom") or ""


def devise():
    return get("devise") or "FCFA"


def est_configure():
    """True si l'agence a au moins renseigné son nom."""
    return bool(get("nom").strip())


def synchroniser():
    """Va chercher les paramètres les plus récents dans la base partagée et
    met à jour le cache local + le fichier logo, pour que ce poste affiche
    toujours les mêmes informations que les autres.

    Ne lève JAMAIS d'exception : en cas de souci réseau (serveur injoignable,
    coupure momentanée...), on continue simplement avec la dernière version
    connue localement (voir charger()). Renvoie True si la synchronisation a
    bien eu lieu, False sinon."""
    global _cache
    try:
        import database as db
        ligne = db.get_parametres_agence()

        if ligne is None or not (ligne.get("nom") or "").strip():
            # La base partagée n'a pas encore de vraies informations
            # d'agence. Si CE poste a déjà des réglages locaux (installation
            # mise à jour depuis une ancienne version), on les utilise comme
            # point de départ commun, une seule fois.
            locales = _charger_fichier_cache()
            if locales.get("nom", "").strip():
                sauvegarder(locales)
            return False

        nouvelles = {k: (ligne.get(k) or "") for k in _DEFAUTS}
        if not nouvelles.get("devise"):
            nouvelles["devise"] = "FCFA"
        _cache = nouvelles
        _ecrire_fichier_cache(nouvelles)
        _synchroniser_logo(ligne.get("logo_base64"), ligne.get("logo_format"))
        return True
    except Exception:
        return False


def _synchroniser_logo(logo_base64, logo_format):
    """Réécrit le fichier logo local à partir de la base partagée, afin que
    tout le code existant (pdf_receipt.py, pdf_listes.py, guide_pdf.py...),
    qui lit directement config.LOGO_PATH, continue de fonctionner SANS
    aucune modification."""
    if not logo_base64:
        return
    try:
        donnees = base64.b64decode(logo_base64)
    except Exception:
        return
    try:
        os.makedirs(config.ASSETS_DIR, exist_ok=True)
        # Évite une écriture disque inutile si le logo n'a pas changé.
        if os.path.exists(config.LOGO_PATH):
            with open(config.LOGO_PATH, "rb") as f:
                if f.read() == donnees:
                    return
        with open(config.LOGO_PATH, "wb") as f:
            f.write(donnees)
    except Exception:
        pass


def sauvegarder(valeurs):
    """Enregistre les paramètres saisis par l'agence dans la base PARTAGÉE
    (immédiatement visibles par tous les postes connectés, Windows comme
    Mac), puis met à jour le cache local.

    Lève une exception si l'écriture dans la base échoue (ex. serveur
    réseau injoignable en mode « client ») : l'écran Réglages doit alors
    prévenir clairement l'utilisateur plutôt que de laisser croire à une
    sauvegarde réussie qui n'a en réalité pas eu lieu."""
    global _cache
    import database as db

    logo_base64 = None
    logo_format = None
    if os.path.exists(config.LOGO_PATH):
        try:
            with open(config.LOGO_PATH, "rb") as f:
                logo_base64 = base64.b64encode(f.read()).decode("ascii")
            logo_format = (os.path.splitext(config.LOGO_PATH)[1]
                            .lstrip(".").upper() or "PNG")
        except Exception:
            logo_base64 = None
            logo_format = None

    db.definir_parametres_agence(valeurs, logo_base64=logo_base64,
                                 logo_format=logo_format)

    nouvelles = dict(charger())
    nouvelles.update({k: v for k, v in valeurs.items() if k in _DEFAUTS})
    if not nouvelles.get("devise"):
        nouvelles["devise"] = "FCFA"
    _cache = nouvelles
    _ecrire_fichier_cache(nouvelles)
    return nouvelles
