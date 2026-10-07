#!/bin/bash
# ============================================================
#  Lanceur macOS pour APLM BUZNESS COMPANY
#  Double-cliquez sur ce fichier pour demarrer le logiciel.
#
#  (La 1re fois seulement, rendez-le executable : ouvrez le
#   Terminal, tapez  chmod +x  suivi d'un espace, puis glissez
#   ce fichier dans la fenetre, et appuyez sur Entree.)
# ============================================================

# Se placer dans le dossier du logiciel (la ou est ce fichier)
cd "$(dirname "$0")"

# Choisir la commande Python 3 disponible
PY="python3"
if ! command -v "$PY" >/dev/null 2>&1; then
    echo "Python 3 n'est pas installe."
    echo "Installez-le depuis https://www.python.org/downloads/ (version 3.12)."
    echo "Puis relancez ce fichier."
    read -n 1 -s -r -p "Appuyez sur une touche pour fermer..."
    exit 1
fi

# Verifier les composants ; les installer automatiquement la 1re fois
if ! "$PY" -c "import customtkinter, fpdf, PIL, tkcalendar" >/dev/null 2>&1; then
    echo "Premiere utilisation : installation des composants necessaires..."
    echo "(cela peut prendre 1 a 2 minutes, une seule fois)"
    "$PY" -m pip install --user -r requirements.txt
    echo "Installation terminee."
fi

# Demarrer le logiciel
"$PY" main.py
