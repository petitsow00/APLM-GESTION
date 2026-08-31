# -*- coding: utf-8 -*-
"""
config.py
-----------
Fichier de configuration central du logiciel APLM BUZNESS COMPANY.
Ici on range toutes les informations "fixes" de l'agence.
Modifier ce fichier suffit pour changer le nom, l'adresse, la monnaie, etc.
"""

import os
import sys

# ---------------------------------------------------------------------------
# OÙ RANGER LES DONNÉES ?
# ---------------------------------------------------------------------------
# Deux situations :
#   1) On lance depuis le code source (python main.py) -> tout reste dans le
#      dossier du projet (pratique pour le développement).
#   2) On lance la version installée (.exe créé par PyInstaller) -> le logiciel
#      range ses données dans Documents\Gestion Agence de Voyages, un endroit où
#      il a TOUJOURS le droit d'écrire, sur n'importe quel ordinateur.
# ---------------------------------------------------------------------------
NOM_DOSSIER_DONNEES = "Gestion Agence de Voyages"

if getattr(sys, "frozen", False):
    # Version installée (.exe)
    _documents = os.path.join(os.path.expanduser("~"), "Documents")
    # On choisit le dossier de données d'après le nom du programme lancé :
    #   - APLM.exe            -> Documents\APLM BUZNESS COMPANY  (données APLM existantes)
    #   - GestionVoyages.exe  -> Documents\Gestion Agence de Voyages  (version standard)
    # Ainsi une mise à jour retrouve TOUJOURS les données déjà enregistrées,
    # sans jamais mélanger les deux versions.
    _nom_exe = os.path.splitext(os.path.basename(sys.executable))[0]
    if _nom_exe.upper().startswith("APLM"):
        _nom_dossier = "APLM BUZNESS COMPANY"
    else:
        _nom_dossier = NOM_DOSSIER_DONNEES
    APP_HOME = os.path.join(_documents, _nom_dossier)
else:
    # Version développement (code source)
    APP_HOME = os.path.dirname(__file__)

# ---------------------------------------------------------------------------
# INFORMATIONS DE L'AGENCE
# ---------------------------------------------------------------------------
# VERSION STANDARD : le nom, l'adresse, etc. NE sont PLUS écrits ici.
# Chaque agence les saisit dans l'écran « Réglages » du logiciel.
# Ces valeurs sont enregistrées dans data/parametres.json (voir settings.py).
# Le dictionnaire ci-dessous ne sert que de secours (valeurs vides).
SOCIETE = {
    "nom": "",
    "slogan": "",
    "adresse": "",
    "telephone": "",
    "email": "",
    "site_web": "",
    "rccm": "",
}

# Dossier des ressources modifiables (logo, etc.)
ASSETS_DIR = os.path.join(APP_HOME, "assets")
# Chemin vers le logo (placez votre image ici : assets\logo.png)
LOGO_PATH = os.path.join(ASSETS_DIR, "logo.png")

# ---------------------------------------------------------------------------
# MONNAIE
# ---------------------------------------------------------------------------
DEVISE = "FCFA"          # monnaie principale affichée
DEVISE_SYMBOLE = "FCFA"

# ---------------------------------------------------------------------------
# CONSOLIDATEURS INTERNES
# ⚠️ IMPORTANT : ces noms sont UNIQUEMENT pour usage interne (suivi/statistiques).
#    Ils ne doivent JAMAIS apparaître sur un reçu client.
# ---------------------------------------------------------------------------
CONSOLIDATEURS = ["Raya Travel", "Bleujay", "Travelgenex"]

# ---------------------------------------------------------------------------
# GDS (systèmes de réservation) — usage interne également, jamais sur le reçu.
# ---------------------------------------------------------------------------
GDS = ["Amadeus", "Galileo", "APG"]

# ---------------------------------------------------------------------------
# LISTES UTILES POUR LES MENUS DÉROULANTS
# ---------------------------------------------------------------------------
TYPES_BILLET = ["Billet d'avion", "Hôtel", "Visa", "Assurance", "Transfert", "Autre"]
CLASSES_VOYAGE = ["Économique", "Premium Éco", "Affaires", "Première"]
MODES_PAIEMENT = ["Espèces", "Mobile Money", "Virement", "Carte bancaire", "Chèque"]
STATUTS_DOSSIER = ["Ouvert", "Confirmé", "Payé", "Émis", "Annulé", "Clôturé"]

# ---------------------------------------------------------------------------
# CHEMINS DE FICHIERS
# ---------------------------------------------------------------------------
BASE_DIR = APP_HOME
DATA_DIR = os.path.join(APP_HOME, "data")
RECUS_DIR = os.path.join(APP_HOME, "recus")          # où seront enregistrés les PDF
DB_PATH = os.path.join(DATA_DIR, "aplm.db")          # la base de données locale

# On s'assure que les dossiers existent (créés automatiquement au 1er lancement)
for _dossier in (DATA_DIR, RECUS_DIR, ASSETS_DIR):
    os.makedirs(_dossier, exist_ok=True)

# ---------------------------------------------------------------------------
# LANGUE PAR DÉFAUT ("fr" = français, "en" = anglais)
# ---------------------------------------------------------------------------
LANGUE_DEFAUT = "fr"
