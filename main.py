# -*- coding: utf-8 -*-
"""
main.py
--------
Point de départ du logiciel APLM BUZNESS COMPANY.

Pour lancer le logiciel, on exécute simplement ce fichier :
    python main.py
"""

from ui.app import MainApp


def lancer():
    app = MainApp()
    app.mainloop()


if __name__ == "__main__":
    lancer()
