# -*- coding: utf-8 -*-
"""
db_serveur.py
--------------
Mini-serveur intégré qui PARTAGE la base de données sur le réseau local.

À lancer sur l'ordinateur « serveur » (celui qui détient la base). Les autres
postes (« clients ») s'y connectent via db_client.py.

Fonctionnement :
    - On démarre un petit serveur web local (module standard http.server).
    - Il écoute les requêtes des clients :
        * POST /sql  -> exécute une requête SQL sur la base locale et renvoie
                        le résultat (lignes, lastrowid...).
        * GET  /ping -> simple test de disponibilité.
    - Chaque requête doit fournir la bonne CLÉ (en-tête X-Cle), sinon refus.
    - Un verrou (Lock) garantit que les écritures ne se chevauchent pas
      (accès concurrents sûrs : pas d'écrasement silencieux).

Sécurité : la clé partagée protège l'accès. Les mots de passe des comptes
sont déjà chiffrés dans la base. À utiliser sur un réseau local de confiance.
"""

import json
import sqlite3
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import config
import reseau


_verrou = threading.Lock()
_connexion = None
_serveur = None
_thread = None


def _get_conn():
    """Connexion SQLite unique, partagée entre les threads (protégée par verrou)."""
    global _connexion
    if _connexion is None:
        _connexion = sqlite3.connect(config.DB_PATH, check_same_thread=False)
        _connexion.row_factory = sqlite3.Row
        _connexion.execute("PRAGMA foreign_keys = ON")
        _connexion.execute("PRAGMA busy_timeout = 5000")
        try:
            # WAL : améliore l'accès simultané lecture/écriture (plusieurs postes)
            _connexion.execute("PRAGMA journal_mode = WAL")
        except Exception:
            pass
    return _connexion


def _executer(sql, params):
    """Exécute une requête sous verrou et renvoie un dictionnaire résultat."""
    with _verrou:
        conn = _get_conn()
        cur = conn.execute(sql, params)
        lignes = []
        if cur.description is not None:
            colonnes = [d[0] for d in cur.description]
            for r in cur.fetchall():
                lignes.append({col: r[col] for col in colonnes})
        conn.commit()
        return {
            "ok": True,
            "rows": lignes,
            "lastrowid": cur.lastrowid,
            "rowcount": cur.rowcount,
        }


class _Handler(BaseHTTPRequestHandler):
    # On coupe les messages de log par défaut (trop bavards)
    def log_message(self, *args):
        pass

    def _repondre(self, code, donnees):
        corps = json.dumps(donnees).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(corps)))
        self.end_headers()
        self.wfile.write(corps)

    def _cle_ok(self):
        attendue = reseau.cle() or ""
        fournie = self.headers.get("X-Cle", "") or ""
        # Si aucune clé n'est configurée, on accepte (déconseillé mais pratique).
        if attendue == "":
            return True
        return fournie == attendue

    def do_GET(self):
        if self.path == "/ping":
            if not self._cle_ok():
                return self._repondre(403, {"ok": False, "erreur": "Clé incorrecte."})
            return self._repondre(200, {"ok": True, "message": "Serveur APLM en ligne."})
        self._repondre(404, {"ok": False, "erreur": "Adresse inconnue."})

    def do_POST(self):
        if self.path != "/sql":
            return self._repondre(404, {"ok": False, "erreur": "Adresse inconnue."})
        if not self._cle_ok():
            return self._repondre(403, {"ok": False, "erreur": "Clé incorrecte."})
        try:
            longueur = int(self.headers.get("Content-Length", 0))
            corps = self.rfile.read(longueur)
            requete = json.loads(corps.decode("utf-8"))
            sql = requete.get("sql", "")
            params = requete.get("params", []) or []
            resultat = _executer(sql, params)
            self._repondre(200, resultat)
        except sqlite3.Error as e:
            self._repondre(400, {"ok": False, "erreur": f"SQL : {e}"})
        except Exception as e:
            self._repondre(500, {"ok": False, "erreur": str(e)})


def demarrer_serveur():
    """Démarre le serveur en arrière-plan (thread). Sans effet s'il tourne déjà.
    Renvoie (True, message) ou (False, message)."""
    global _serveur, _thread
    if _thread is not None and _thread.is_alive():
        return True, "Le serveur tourne déjà."
    try:
        _serveur = ThreadingHTTPServer(("0.0.0.0", reseau.port()), _Handler)
    except OSError as e:
        return False, (f"Impossible de démarrer le serveur sur le port "
                       f"{reseau.port()} : {e}. Ce port est peut-être déjà utilisé.")
    _thread = threading.Thread(target=_serveur.serve_forever, daemon=True)
    _thread.start()
    return True, (f"Serveur démarré sur le port {reseau.port()}. "
                  f"Adresse à donner aux autres postes : {reseau.adresse_ip_locale()}")


def arreter_serveur():
    global _serveur
    if _serveur is not None:
        try:
            _serveur.shutdown()
        except Exception:
            pass
        _serveur = None
