#!/bin/bash
# ============================================================
#  Lanceur macOS pour APLM BUZNESS COMPANY
#  Double-cliquez sur ce fichier pour démarrer le logiciel.
#
#  (La 1re fois seulement, rendez-le exécutable en ouvrant
#   l'application "Terminal" et en tapant :
#      chmod +x "Lancer APLM.command"
#   puis appuyez sur Entrée.)
# ============================================================

# Se placer dans le dossier du logiciel (là où est ce fichier)
cd "$(dirname "$0")"

# Démarrer le logiciel avec Python 3
python3 main.py
