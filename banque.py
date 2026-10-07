# -*- coding: utf-8 -*-
"""
banque.py
---------
MODULE BANQUE (Étape 12) : journal de trésorerie de l'agence.

RÈGLE ABSOLUE (§13 du cahier des charges) — NE PAS COMPTER DEUX FOIS :
    Un mouvement bancaire est un MOUVEMENT D'ARGENT, pas une vente.
    - Un VERSEMENT (dépôt) fait MONTER le solde d'un compte bancaire.
    - Un RETRAIT fait DESCENDRE le solde.
    Le chiffre d'affaires se calcule ailleurs (à partir des opérations),
    JAMAIS à partir des mouvements bancaires. Ce module est autonome.

Tables :
    - comptes_bancaires  : les comptes (nom, banque, n°, solde initial)
    - mouvements_bancaires : chaque versement / retrait

Solde d'un compte = solde_initial + total versements - total retraits.
"""

from datetime import datetime
import database as db


# Origine des fonds pour un VERSEMENT (§12)
ORIGINES_VERSEMENT = ["Dépôt espèces", "Recettes", "Encaissement client",
                      "Virement reçu", "Autre"]
# Catégorie d'un RETRAIT (§12)
CATEGORIES_RETRAIT = ["Retrait espèces", "Paiement fournisseur", "Frais bancaires",
                      "Dépense agence", "Avance", "Autre"]


# ===========================================================================
#  INITIALISATION
# ===========================================================================
def initialiser():
    """Crée les tables du module Banque si besoin (100 % additif)."""
    conn = db.get_connexion()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS comptes_bancaires (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            nom           TEXT NOT NULL,
            banque        TEXT,
            numero        TEXT,
            solde_initial REAL DEFAULT 0,
            devise        TEXT,
            actif         INTEGER NOT NULL DEFAULT 1,
            notes         TEXT,
            date_creation TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS mouvements_bancaires (
            id                 INTEGER PRIMARY KEY AUTOINCREMENT,
            compte_id          INTEGER NOT NULL,
            type               TEXT NOT NULL,      -- 'versement' ou 'retrait'
            date_mouvement     TEXT,
            montant            REAL NOT NULL DEFAULT 0,
            motif              TEXT,
            categorie          TEXT,               -- origine (versement) / catégorie (retrait)
            tiers              TEXT,               -- bénéficiaire (retrait)
            client_id          INTEGER,            -- client concerné (facultatif)
            reference_bancaire TEXT,
            piece_reference    TEXT,               -- n° bordereau / n° chèque
            piece_justificative TEXT,              -- chemin d'un fichier joint
            notes              TEXT,
            date_creation      TEXT,
            cree_par           INTEGER,
            FOREIGN KEY (compte_id) REFERENCES comptes_bancaires(id) ON DELETE CASCADE,
            FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE SET NULL
        )
    """)
    conn.commit()
    conn.close()


def _maintenant():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ===========================================================================
#  COMPTES BANCAIRES
# ===========================================================================
def creer_compte(nom, banque="", numero="", solde_initial=0, devise="",
                 notes=""):
    conn = db.get_connexion()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO comptes_bancaires
            (nom, banque, numero, solde_initial, devise, actif, notes, date_creation)
        VALUES (?, ?, ?, ?, ?, 1, ?, ?)
    """, (nom, banque, numero, solde_initial or 0, devise, notes, _maintenant()))
    conn.commit()
    nid = cur.lastrowid
    conn.close()
    db.enregistrer_activite("Création", "Compte bancaire", nom)
    return nid


def modifier_compte(compte_id, nom, banque="", numero="", solde_initial=0,
                    devise="", actif=1, notes=""):
    conn = db.get_connexion()
    conn.execute("""
        UPDATE comptes_bancaires SET
            nom=?, banque=?, numero=?, solde_initial=?, devise=?, actif=?, notes=?
        WHERE id=?
    """, (nom, banque, numero, solde_initial or 0, devise,
          1 if actif else 0, notes, compte_id))
    conn.commit()
    conn.close()


def supprimer_compte(compte_id):
    conn = db.get_connexion()
    conn.execute("DELETE FROM comptes_bancaires WHERE id=?", (compte_id,))
    conn.commit()
    conn.close()
    db.enregistrer_activite("Suppression", "Compte bancaire", f"#{compte_id}")


def lister_comptes(actifs_seulement=False):
    conn = db.get_connexion()
    base = "SELECT * FROM comptes_bancaires"
    if actifs_seulement:
        base += " WHERE actif=1"
    base += " ORDER BY nom"
    lignes = conn.execute(base).fetchall()
    conn.close()
    return lignes


def get_compte(compte_id):
    conn = db.get_connexion()
    ligne = conn.execute(
        "SELECT * FROM comptes_bancaires WHERE id=?", (compte_id,)).fetchone()
    conn.close()
    return ligne


# ===========================================================================
#  MOUVEMENTS : VERSEMENTS / RETRAITS
# ===========================================================================
def _creer_mouvement(compte_id, type_mvt, montant, date_mouvement="", motif="",
                     categorie="", tiers="", client_id=None,
                     reference_bancaire="", piece_reference="",
                     piece_justificative="", notes=""):
    if not date_mouvement:
        date_mouvement = datetime.now().strftime("%Y-%m-%d")
    conn = db.get_connexion()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO mouvements_bancaires
            (compte_id, type, date_mouvement, montant, motif, categorie, tiers,
             client_id, reference_bancaire, piece_reference, piece_justificative,
             notes, date_creation, cree_par)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (compte_id, type_mvt, date_mouvement, montant or 0, motif, categorie,
          tiers, client_id, reference_bancaire, piece_reference,
          piece_justificative, notes, _maintenant(), db.auth.id_courant()))
    conn.commit()
    nid = cur.lastrowid
    conn.close()
    db.enregistrer_activite(
        "Versement" if type_mvt == "versement" else "Retrait",
        "Banque", f"{montant} (compte #{compte_id})")
    return nid


def creer_versement(compte_id, montant, date_mouvement="", origine="", motif="",
                    client_id=None, reference_bancaire="", num_bordereau="",
                    piece_justificative="", notes=""):
    """Dépôt / entrée d'argent sur un compte bancaire (fait MONTER le solde)."""
    return _creer_mouvement(compte_id, "versement", montant, date_mouvement,
                            motif=motif, categorie=origine, client_id=client_id,
                            reference_bancaire=reference_bancaire,
                            piece_reference=num_bordereau,
                            piece_justificative=piece_justificative, notes=notes)


def creer_retrait(compte_id, montant, date_mouvement="", categorie="", motif="",
                  beneficiaire="", reference_bancaire="", num_cheque="",
                  piece_justificative="", notes=""):
    """Retrait / sortie d'argent d'un compte bancaire (fait DESCENDRE le solde)."""
    return _creer_mouvement(compte_id, "retrait", montant, date_mouvement,
                            motif=motif, categorie=categorie, tiers=beneficiaire,
                            reference_bancaire=reference_bancaire,
                            piece_reference=num_cheque,
                            piece_justificative=piece_justificative, notes=notes)


def supprimer_mouvement(mouvement_id):
    conn = db.get_connexion()
    conn.execute("DELETE FROM mouvements_bancaires WHERE id=?", (mouvement_id,))
    conn.commit()
    conn.close()
    db.enregistrer_activite("Suppression", "Mouvement bancaire", f"#{mouvement_id}")


def lister_mouvements(compte_id=None, type_mvt=None, date_debut=None,
                      date_fin=None):
    conn = db.get_connexion()
    base = """
        SELECT m.*, c.nom AS compte_nom,
               cl.nom AS client_nom, cl.prenom AS client_prenom
        FROM mouvements_bancaires m
        JOIN comptes_bancaires c ON c.id = m.compte_id
        LEFT JOIN clients cl ON cl.id = m.client_id
    """
    cond, params = [], []
    if compte_id is not None:
        cond.append("m.compte_id = ?"); params.append(compte_id)
    if type_mvt:
        cond.append("m.type = ?"); params.append(type_mvt)
    if date_debut:
        cond.append("substr(m.date_mouvement,1,10) >= ?"); params.append(date_debut)
    if date_fin:
        cond.append("substr(m.date_mouvement,1,10) <= ?"); params.append(date_fin)
    if cond:
        base += " WHERE " + " AND ".join(cond)
    base += " ORDER BY substr(m.date_mouvement,1,10) DESC, m.id DESC"
    lignes = conn.execute(base, params).fetchall()
    conn.close()
    return lignes


# ===========================================================================
#  SOLDES
# ===========================================================================
def solde_compte(compte_id, date_debut=None, date_fin=None):
    """Solde d'un compte = solde_initial + versements - retraits.
    Si une période est donnée, versements/retraits sont limités à la période
    (mais le solde_initial reste celui du compte)."""
    compte = get_compte(compte_id)
    if compte is None:
        return None
    conn = db.get_connexion()
    base_v = ("SELECT COALESCE(SUM(montant),0) AS t FROM mouvements_bancaires "
              "WHERE compte_id=? AND type='versement'")
    base_r = ("SELECT COALESCE(SUM(montant),0) AS t FROM mouvements_bancaires "
              "WHERE compte_id=? AND type='retrait'")
    params = [compte_id]
    suffixe = ""
    if date_debut:
        suffixe += " AND substr(date_mouvement,1,10) >= ?"
    if date_fin:
        suffixe += " AND substr(date_mouvement,1,10) <= ?"
    p2 = params + [d for d in (date_debut, date_fin) if d]
    versements = conn.execute(base_v + suffixe, p2).fetchone()["t"]
    retraits = conn.execute(base_r + suffixe, p2).fetchone()["t"]
    conn.close()
    solde_init = compte["solde_initial"] or 0
    return {
        "compte_id": compte_id,
        "compte_nom": compte["nom"],
        "solde_initial": solde_init,
        "total_versements": versements,
        "total_retraits": retraits,
        "solde_actuel": solde_init + versements - retraits,
    }


def soldes_tous_comptes():
    """Renvoie le solde de chaque compte (utile pour la vue d'ensemble)."""
    return [solde_compte(c["id"]) for c in lister_comptes()]
