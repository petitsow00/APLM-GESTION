# -*- coding: utf-8 -*-
"""
db_client.py
-------------
Connexion à DISTANCE à la base de données (mode « client »).

Le reste du logiciel utilise la base via `database.get_connexion()` qui renvoie
normalement une connexion SQLite locale. En mode client, on renvoie à la place
un objet `ConnexionDistante` qui IMITE une connexion SQLite mais envoie en
réalité chaque requête au serveur (par le réseau local), puis récupère le
résultat.

Ainsi, TOUTES les fonctions existantes (creer_client, balance, etc.)
fonctionnent SANS AUCUNE MODIFICATION : elles croient parler à SQLite.

Communication : requête HTTP POST vers http://<hote>:<port>/sql,
protégée par une clé secrète partagée (en-tête X-Cle).
"""

import json
import urllib.request
import urllib.error


class ErreurReseau(Exception):
    """Erreur de communication avec le serveur (serveur éteint, mauvaise clé...)."""
    pass


class CurseurDistant:
    """Imite un curseur SQLite : execute(), fetchone(), fetchall(), lastrowid."""

    def __init__(self, connexion):
        self._cx = connexion
        self._lignes = []
        self._index = 0
        self.lastrowid = None
        self.rowcount = -1

    def execute(self, sql, params=()):
        resultat = self._cx._envoyer(sql, params)
        self._lignes = resultat.get("rows", [])
        self._index = 0
        self.lastrowid = resultat.get("lastrowid")
        self.rowcount = resultat.get("rowcount", -1)
        return self

    def executemany(self, sql, sequence):
        for params in sequence:
            self.execute(sql, params)
        return self

    def fetchone(self):
        if self._index < len(self._lignes):
            ligne = self._lignes[self._index]
            self._index += 1
            return ligne
        return None

    def fetchall(self):
        reste = self._lignes[self._index:]
        self._index = len(self._lignes)
        return reste

    def __iter__(self):
        return iter(self.fetchall())


class ConnexionDistante:
    """Imite une connexion SQLite, mais envoie les requêtes au serveur."""

    def __init__(self, hote, port, cle):
        self._url = f"http://{hote}:{port}/sql"
        self._cle = cle or ""
        self.row_factory = None  # présent pour compatibilité, ignoré

    # --- Interface "connexion" utilisée par le reste du code ---
    def cursor(self):
        return CurseurDistant(self)

    def execute(self, sql, params=()):
        cur = CurseurDistant(self)
        return cur.execute(sql, params)

    def executemany(self, sql, sequence):
        cur = CurseurDistant(self)
        return cur.executemany(sql, sequence)

    def commit(self):
        pass  # chaque requête est déjà validée côté serveur

    def rollback(self):
        pass

    def close(self):
        pass

    # --- Envoi réel de la requête au serveur ---
    def _envoyer(self, sql, params):
        corps = json.dumps({
            "sql": sql,
            "params": list(params) if params else [],
        }).encode("utf-8")
        requete = urllib.request.Request(
            self._url, data=corps, method="POST",
            headers={"Content-Type": "application/json", "X-Cle": self._cle})
        try:
            with urllib.request.urlopen(requete, timeout=15) as reponse:
                donnees = json.loads(reponse.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            detail = ""
            try:
                detail = json.loads(e.read().decode("utf-8")).get("erreur", "")
            except Exception:
                pass
            if e.code == 403:
                raise ErreurReseau("Clé réseau incorrecte. Vérifiez la clé "
                                   "partagée dans les Réglages réseau.")
            raise ErreurReseau(f"Erreur du serveur : {detail or e}")
        except urllib.error.URLError as e:
            raise ErreurReseau(
                "Impossible de joindre le serveur. Vérifiez qu'il est allumé "
                "et que l'adresse IP / le port sont corrects.\n"
                f"Détail : {e.reason}")
        if not donnees.get("ok"):
            raise ErreurReseau(donnees.get("erreur", "Erreur inconnue du serveur."))
        return donnees


def authentifier_distant(hote, port, cle, identifiant, mot_de_passe):
    """Demande au SERVEUR de vérifier l'identifiant + le mot de passe.

    Sécurité : seul le résultat (oui/non + infos du compte, SANS le mot de
    passe chiffré) revient par le réseau. Le "hash" du mot de passe ne quitte
    jamais le serveur.
    Renvoie {"ok": True, "utilisateur": {...}} ou {"ok": False, "raison": "..."}.
    """
    url = f"http://{hote}:{port}/connexion"
    corps = json.dumps({
        "identifiant": identifiant,
        "mot_de_passe": mot_de_passe,
    }).encode("utf-8")
    requete = urllib.request.Request(
        url, data=corps, method="POST",
        headers={"Content-Type": "application/json", "X-Cle": cle or ""})
    try:
        with urllib.request.urlopen(requete, timeout=15) as reponse:
            return json.loads(reponse.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 403:
            return {"ok": False, "raison": "Clé réseau incorrecte."}
        return {"ok": False, "raison": f"Erreur du serveur : {e}"}
    except urllib.error.URLError as e:
        return {"ok": False,
                "raison": "Impossible de joindre le serveur. Vérifiez qu'il "
                          f"est allumé et que l'adresse IP / le port sont "
                          f"corrects.\nDétail : {e.reason}"}


def tester_connexion(hote, port, cle):
    """Teste la connexion au serveur. Renvoie (True, message) ou (False, message)."""
    url = f"http://{hote}:{port}/ping"
    try:
        requete = urllib.request.Request(url, headers={"X-Cle": cle or ""})
        with urllib.request.urlopen(requete, timeout=8) as reponse:
            donnees = json.loads(reponse.read().decode("utf-8"))
        if donnees.get("ok"):
            return True, "Connexion au serveur réussie."
        return False, donnees.get("erreur", "Réponse inattendue du serveur.")
    except urllib.error.HTTPError as e:
        if e.code == 403:
            return False, "Clé réseau incorrecte."
        return False, f"Erreur serveur : {e}"
    except Exception as e:
        return False, f"Serveur injoignable : {e}"
