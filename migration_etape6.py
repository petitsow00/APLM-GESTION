# -*- coding: utf-8 -*-
"""
migration_etape6.py
-------------------
ÉTAPE 6 : BASE CLIENT CENTRALE (sur la COPIE DE TRAVAIL uniquement).

1) Ajoute 4 champs manquants à la fiche client, SANS toucher aux données :
      date_naissance, nationalite, num_passeport, date_exp_passeport
   (opération « ADD COLUMN » : les 232 clients restent, les champs sont vides).
2) Fournit deux outils, fondations des Étapes 7 et 9 :
      - rechercher_clients(terme)        -> recherche par nom/prénom/tél/email/passeport
      - detecter_doublons(...)           -> repère un client déjà existant
3) Teste ces outils avec les VRAIS clients (démonstration).

SÉCURITÉ : refuse de tourner ailleurs que sur un fichier « ...travail... ».
"""

import os
import sqlite3

DB = os.path.join(os.path.dirname(__file__), "data", "aplm_travail.db")
if "travail" not in os.path.basename(DB).lower():
    raise SystemExit("SECURITE : ce programme ne s'execute que sur aplm_travail.db")


def _connexion():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def _ajouter_colonne_si_absente(cur, table, colonne, definition):
    cols = [r["name"] for r in cur.execute(f"PRAGMA table_info({table})").fetchall()]
    if colonne not in cols:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {colonne} {definition}")
        return True
    return False


# ---------------------------------------------------------------------------
# 1) AJOUT DES CHAMPS CLIENT
# ---------------------------------------------------------------------------
def enrichir_fiche_client(cur):
    ajouts = []
    for col in ("date_naissance", "nationalite", "num_passeport",
                "date_exp_passeport"):
        if _ajouter_colonne_si_absente(cur, "clients", col, "TEXT"):
            ajouts.append(col)
    return ajouts


# ---------------------------------------------------------------------------
# 2) OUTILS DE RECHERCHE / DÉTECTION DE DOUBLONS
# ---------------------------------------------------------------------------
def _norm(txt):
    """Nettoyage simple : minuscules, espaces réduits."""
    return " ".join((txt or "").strip().lower().split())


def _norm_tel(txt):
    """Garde seulement les chiffres d'un numéro de téléphone."""
    return "".join(c for c in (txt or "") if c.isdigit())


def rechercher_clients(terme, limite=20):
    """Recherche large : nom, prénom, téléphone, email, passeport, code.
    Renvoie une liste de clients correspondants."""
    conn = _connexion()
    motif = f"%{(terme or '').strip()}%"
    lignes = conn.execute("""
        SELECT * FROM clients
        WHERE nom LIKE ? OR prenom LIKE ? OR telephone LIKE ?
           OR email LIKE ? OR num_passeport LIKE ? OR code LIKE ?
        ORDER BY nom, prenom
        LIMIT ?
    """, (motif, motif, motif, motif, motif, motif, limite)).fetchall()
    conn.close()
    return lignes


def detecter_doublons(nom="", prenom="", telephone="", email="", num_passeport=""):
    """Cherche un client DÉJÀ existant, dans cet ordre de fiabilité (§5) :
         1) numéro de passeport identique
         2) téléphone identique
         3) email identique
         4) nom + prénom identiques
    Renvoie une liste de dicts {client, critere} (le meilleur en premier).
    Liste vide = aucun doublon probable -> on peut créer sans risque.
    """
    conn = _connexion()
    clients = conn.execute("SELECT * FROM clients").fetchall()
    conn.close()

    np = _norm(num_passeport)
    tel = _norm_tel(telephone)
    em = _norm(email)
    nom_n, prenom_n = _norm(nom), _norm(prenom)

    trouves, deja = [], set()

    def _ajouter(c, critere):
        if c["id"] not in deja:
            deja.add(c["id"])
            trouves.append({"client": c, "critere": critere})

    # 1) Passeport (le plus fiable)
    if np:
        for c in clients:
            if _norm(c["num_passeport"]) == np:
                _ajouter(c, "numéro de passeport")
    # 2) Téléphone
    if tel:
        for c in clients:
            if _norm_tel(c["telephone"]) == tel:
                _ajouter(c, "téléphone")
    # 3) Email
    if em:
        for c in clients:
            if _norm(c["email"]) == em:
                _ajouter(c, "email")
    # 4) Nom + prénom
    if nom_n and prenom_n:
        for c in clients:
            if _norm(c["nom"]) == nom_n and _norm(c["prenom"]) == prenom_n:
                _ajouter(c, "nom + prénom")

    return trouves


# ---------------------------------------------------------------------------
# 3) PROGRAMME PRINCIPAL + TESTS
# ---------------------------------------------------------------------------
def main():
    conn = _connexion()
    cur = conn.cursor()

    avant = cur.execute("SELECT COUNT(*) FROM clients").fetchone()[0]
    ajouts = enrichir_fiche_client(cur)
    conn.commit()
    apres = cur.execute("SELECT COUNT(*) FROM clients").fetchone()[0]
    cols = [r["name"] for r in cur.execute("PRAGMA table_info(clients)").fetchall()]

    print("ETAPE 6 sur la COPIE DE TRAVAIL :", DB)
    print("-" * 60)
    print(f"  Clients AVANT : {avant}   -> APRES : {apres}   (doit rester 232)")
    print(f"  Champs ajoutes : {', '.join(ajouts) if ajouts else '(deja presents)'}")
    print(f"  Fiche client complete : {', '.join(cols)}")

    # Prend un vrai client pour la demonstration
    ref = cur.execute(
        "SELECT * FROM clients WHERE TRIM(COALESCE(nom,''))<>'' "
        "ORDER BY id LIMIT 1").fetchone()
    conn.close()

    print("-" * 60)
    print("  TEST 1 - recherche par nom :", ref["nom"])
    res = rechercher_clients(ref["nom"])
    print(f"     -> {len(res)} client(s) trouve(s) (ex: {res[0]['nom']} {res[0]['prenom'] or ''})")

    print("-" * 60)
    print("  TEST 2 - detection de doublon (on 're-saisit' un client existant) :")
    print(f"     saisie = nom '{ref['nom']}', prenom '{ref['prenom'] or ''}', "
          f"tel '{ref['telephone'] or ''}'")
    doublons = detecter_doublons(nom=ref["nom"], prenom=ref["prenom"] or "",
                                 telephone=ref["telephone"] or "")
    if doublons:
        d = doublons[0]
        print(f"     -> DOUBLON DETECTE : {d['client']['code']} "
              f"{d['client']['nom']} {d['client']['prenom'] or ''} "
              f"(critere : {d['critere']})  [BON : on proposera de reutiliser cette fiche]")
    else:
        print("     -> aucun doublon (anormal ici !)")

    print("-" * 60)
    print("  TEST 3 - client tout nouveau (doit NE PAS etre detecte) :")
    doublons2 = detecter_doublons(nom="ZZZINEXISTANT", prenom="Personne",
                                  telephone="000000000",
                                  num_passeport="XX-AUCUN-999")
    print(f"     -> {len(doublons2)} doublon(s)  [BON si 0 : on creera une nouvelle fiche]")
    print("-" * 60)
    print("  Termine.")


if __name__ == "__main__":
    main()
