# -*- coding: utf-8 -*-
"""
utils.py
---------
Petits outils communs, indépendants du système d'exploitation.

Objectif : que le logiciel fonctionne de la même façon sur
Windows ET sur macOS (MacBook Intel) sans rien changer aux fonctionnalités.
"""

import os
import sys
import subprocess


def ouvrir_fichier(chemin):
    """Ouvre un fichier (ex : un PDF) avec l'application par défaut du système.

    - Windows : os.startfile (comme avant)
    - macOS   : commande « open »
    - Linux   : commande « xdg-open »

    Ne provoque jamais d'erreur bloquante : si l'ouverture échoue,
    le fichier reste quand même créé sur le disque.
    """
    try:
        if sys.platform.startswith("win"):
            os.startfile(chemin)                       # Windows
        elif sys.platform == "darwin":
            subprocess.run(["open", chemin], check=False)      # macOS
        else:
            subprocess.run(["xdg-open", chemin], check=False)  # Linux
    except Exception:
        # L'ouverture automatique est un confort, pas une obligation :
        # en cas de souci, on n'interrompt pas le programme.
        pass
