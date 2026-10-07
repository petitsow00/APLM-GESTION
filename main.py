# -*- coding: utf-8 -*-
"""
main.py
--------
Point de départ du logiciel APLM BUZNESS COMPANY.

Pour lancer le logiciel, on exécute simplement ce fichier :
    python main.py

Déroulement :
    1) On affiche l'écran de CONNEXION (login_view).
       - Première utilisation : création du compte administrateur.
       - Ensuite : identifiant + mot de passe.
    2) Si la connexion réussit, on ouvre le logiciel principal (MainApp).
    3) Si l'utilisateur clique sur « Déconnexion », on revient à l'étape 1.
       S'il ferme la fenêtre, le logiciel se termine.
"""

import auth
import reseau
from ui.login_view import LoginWindow
from ui.app import MainApp


def lancer():
    # Si CET ordinateur est le « serveur » du bureau, on démarre le partage
    # de la base sur le réseau local dès le lancement.
    if reseau.est_serveur():
        try:
            import db_serveur
            ok, message = db_serveur.demarrer_serveur()
            print(message)
        except Exception as e:
            print("Avertissement : serveur réseau non démarré :", e)

    while True:
        # --- 1) Écran de connexion ---
        login = LoginWindow()
        login.mainloop()
        if not login.reussi:
            # L'utilisateur a fermé la fenêtre de connexion -> on quitte.
            break

        # --- 2) Logiciel principal ---
        app = MainApp()
        app.mainloop()

        # --- 3) Après fermeture du logiciel ---
        auth.deconnecter()
        if not app.se_deconnecter:
            # Fenêtre fermée (croix) -> on quitte réellement.
            break
        # Sinon : clic sur « Déconnexion » -> on reboucle vers la connexion.


if __name__ == "__main__":
    lancer()
