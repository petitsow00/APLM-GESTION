# -*- coding: utf-8 -*-
"""
database.py
------------
Gère la base de données locale (SQLite) du logiciel APLM BUZNESS COMPANY.

SQLite = une base de données rangée dans UN seul fichier (data/aplm.db).
Aucun Internet requis : tout reste sur ton ordinateur.

Ce fichier contient :
  1) La création des tables (clients, dossiers, reservations, paiements)
  2) Toutes les fonctions pour ajouter / modifier / supprimer / lire les données
"""

import sqlite3
from datetime import datetime
import config


# ===========================================================================
#  CONNEXION À LA BASE
# ===========================================================================
def get_connexion():
    """Ouvre une connexion à la base de données locale.
    row_factory = sqlite3.Row permet de lire les colonnes par leur nom
    (ex: client['nom']) au lieu d'un simple numéro."""
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")   # respecte les liens entre tables
    return conn


# ===========================================================================
#  CRÉATION DES TABLES (exécutée une fois au démarrage)
# ===========================================================================
def initialiser_base():
    """Crée les tables si elles n'existent pas encore."""
    conn = get_connexion()
    cur = conn.cursor()

    # --- Table CLIENTS -----------------------------------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            code           TEXT,
            nom            TEXT NOT NULL,
            prenom         TEXT,
            telephone      TEXT,
            email          TEXT,
            adresse        TEXT,
            type_piece     TEXT,
            num_piece      TEXT,
            notes          TEXT,
            date_creation  TEXT
        )
    """)

    # --- Table DOSSIERS (un voyage/affaire pour un client) -----------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS dossiers (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            reference      TEXT UNIQUE,
            client_id      INTEGER NOT NULL,
            titre          TEXT,
            statut         TEXT,
            notes          TEXT,
            date_creation  TEXT,
            FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
        )
    """)

    # --- Table RESERVATIONS / BILLETS --------------------------------------
    # NOTE : gds et consolidateur sont INTERNES -> jamais imprimés sur le reçu.
    cur.execute("""
        CREATE TABLE IF NOT EXISTS reservations (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            dossier_id     INTEGER NOT NULL,
            type_billet    TEXT,
            compagnie      TEXT,
            pnr            TEXT,
            num_billet     TEXT,
            passager       TEXT,
            ville_depart   TEXT,
            ville_arrivee  TEXT,
            date_depart    TEXT,
            date_retour    TEXT,
            classe         TEXT,
            gds            TEXT,          -- INTERNE (Amadeus/Galileo/APG)
            consolidateur  TEXT,          -- INTERNE (Raya/Bleujay/Travelgenex)
            prix_achat     REAL DEFAULT 0,-- INTERNE (coût agence)
            prix_vente     REAL DEFAULT 0,-- montant facturé au client
            notes          TEXT,
            date_creation  TEXT,
            FOREIGN KEY (dossier_id) REFERENCES dossiers(id) ON DELETE CASCADE
        )
    """)

    # --- Table PAIEMENTS ---------------------------------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS paiements (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            dossier_id     INTEGER NOT NULL,
            montant        REAL NOT NULL,
            mode           TEXT,
            reference      TEXT,
            date_paiement  TEXT,
            notes          TEXT,
            date_creation  TEXT,
            FOREIGN KEY (dossier_id) REFERENCES dossiers(id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()


# ===========================================================================
#  PETITS OUTILS
# ===========================================================================
def _maintenant():
    """Renvoie la date + heure actuelle sous forme de texte."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def generer_reference_dossier():
    """Fabrique une référence unique du type DOS-2026-0001 (générique)."""
    conn = get_connexion()
    annee = datetime.now().strftime("%Y")
    prefixe = f"DOS-{annee}-"
    ligne = conn.execute(
        "SELECT COUNT(*) AS n FROM dossiers WHERE reference LIKE ?",
        (prefixe + "%",)
    ).fetchone()
    conn.close()
    numero = (ligne["n"] or 0) + 1
    return f"{prefixe}{numero:04d}"


def generer_code_client():
    """Fabrique un code client du type CLT-0001."""
    conn = get_connexion()
    ligne = conn.execute("SELECT COUNT(*) AS n FROM clients").fetchone()
    conn.close()
    numero = (ligne["n"] or 0) + 1
    return f"CLT-{numero:04d}"


# ===========================================================================
#  CLIENTS  (ajouter / modifier / supprimer / lister)
# ===========================================================================
def creer_client(nom, prenom="", telephone="", email="", adresse="",
                 type_piece="", num_piece="", notes=""):
    conn = get_connexion()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO clients
            (code, nom, prenom, telephone, email, adresse,
             type_piece, num_piece, notes, date_creation)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (generer_code_client(), nom, prenom, telephone, email, adresse,
          type_piece, num_piece, notes, _maintenant()))
    conn.commit()
    nouvel_id = cur.lastrowid
    conn.close()
    return nouvel_id


def modifier_client(client_id, nom, prenom="", telephone="", email="",
                    adresse="", type_piece="", num_piece="", notes=""):
    conn = get_connexion()
    conn.execute("""
        UPDATE clients SET
            nom=?, prenom=?, telephone=?, email=?, adresse=?,
            type_piece=?, num_piece=?, notes=?
        WHERE id=?
    """, (nom, prenom, telephone, email, adresse,
          type_piece, num_piece, notes, client_id))
    conn.commit()
    conn.close()


def supprimer_client(client_id):
    """Supprime un client ET tous ses dossiers/réservations/paiements liés."""
    conn = get_connexion()
    conn.execute("DELETE FROM clients WHERE id=?", (client_id,))
    conn.commit()
    conn.close()


def lister_clients(recherche=""):
    """Renvoie la liste des clients, éventuellement filtrée par un mot-clé."""
    conn = get_connexion()
    if recherche:
        motif = f"%{recherche}%"
        lignes = conn.execute("""
            SELECT * FROM clients
            WHERE nom LIKE ? OR prenom LIKE ? OR telephone LIKE ?
               OR email LIKE ? OR code LIKE ?
            ORDER BY nom, prenom
        """, (motif, motif, motif, motif, motif)).fetchall()
    else:
        lignes = conn.execute(
            "SELECT * FROM clients ORDER BY nom, prenom").fetchall()
    conn.close()
    return lignes


def get_client(client_id):
    conn = get_connexion()
    ligne = conn.execute(
        "SELECT * FROM clients WHERE id=?", (client_id,)).fetchone()
    conn.close()
    return ligne


# ===========================================================================
#  DOSSIERS
# ===========================================================================
def creer_dossier(client_id, titre="", statut="Ouvert", notes=""):
    conn = get_connexion()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO dossiers (reference, client_id, titre, statut, notes, date_creation)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (generer_reference_dossier(), client_id, titre, statut, notes, _maintenant()))
    conn.commit()
    nouvel_id = cur.lastrowid
    conn.close()
    return nouvel_id


def modifier_dossier(dossier_id, titre="", statut="", notes=""):
    conn = get_connexion()
    conn.execute("""
        UPDATE dossiers SET titre=?, statut=?, notes=? WHERE id=?
    """, (titre, statut, notes, dossier_id))
    conn.commit()
    conn.close()


def supprimer_dossier(dossier_id):
    conn = get_connexion()
    conn.execute("DELETE FROM dossiers WHERE id=?", (dossier_id,))
    conn.commit()
    conn.close()


def lister_dossiers(recherche="", client_id=None):
    """Liste les dossiers avec le nom du client (jointure)."""
    conn = get_connexion()
    base = """
        SELECT d.*, c.nom AS client_nom, c.prenom AS client_prenom
        FROM dossiers d
        JOIN clients c ON c.id = d.client_id
    """
    conditions = []
    params = []
    if client_id is not None:
        conditions.append("d.client_id = ?")
        params.append(client_id)
    if recherche:
        motif = f"%{recherche}%"
        conditions.append(
            "(d.reference LIKE ? OR d.titre LIKE ? OR c.nom LIKE ? OR c.prenom LIKE ?)")
        params.extend([motif, motif, motif, motif])
    if conditions:
        base += " WHERE " + " AND ".join(conditions)
    base += " ORDER BY d.date_creation DESC"
    lignes = conn.execute(base, params).fetchall()
    conn.close()
    return lignes


def get_dossier(dossier_id):
    conn = get_connexion()
    ligne = conn.execute("""
        SELECT d.*, c.nom AS client_nom, c.prenom AS client_prenom,
               c.telephone AS client_telephone, c.email AS client_email,
               c.adresse AS client_adresse, c.code AS client_code
        FROM dossiers d
        JOIN clients c ON c.id = d.client_id
        WHERE d.id=?
    """, (dossier_id,)).fetchone()
    conn.close()
    return ligne


# ===========================================================================
#  RESERVATIONS / BILLETS
# ===========================================================================
def creer_reservation(dossier_id, type_billet="", compagnie="", pnr="",
                      num_billet="", passager="", ville_depart="",
                      ville_arrivee="", date_depart="", date_retour="",
                      classe="", gds="", consolidateur="",
                      prix_achat=0, prix_vente=0, notes=""):
    conn = get_connexion()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO reservations
            (dossier_id, type_billet, compagnie, pnr, num_billet, passager,
             ville_depart, ville_arrivee, date_depart, date_retour, classe,
             gds, consolidateur, prix_achat, prix_vente, notes, date_creation)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (dossier_id, type_billet, compagnie, pnr, num_billet, passager,
          ville_depart, ville_arrivee, date_depart, date_retour, classe,
          gds, consolidateur, prix_achat, prix_vente, notes, _maintenant()))
    conn.commit()
    nouvel_id = cur.lastrowid
    conn.close()
    return nouvel_id


def modifier_reservation(reservation_id, type_billet="", compagnie="", pnr="",
                         num_billet="", passager="", ville_depart="",
                         ville_arrivee="", date_depart="", date_retour="",
                         classe="", gds="", consolidateur="",
                         prix_achat=0, prix_vente=0, notes=""):
    conn = get_connexion()
    conn.execute("""
        UPDATE reservations SET
            type_billet=?, compagnie=?, pnr=?, num_billet=?, passager=?,
            ville_depart=?, ville_arrivee=?, date_depart=?, date_retour=?,
            classe=?, gds=?, consolidateur=?, prix_achat=?, prix_vente=?, notes=?
        WHERE id=?
    """, (type_billet, compagnie, pnr, num_billet, passager,
          ville_depart, ville_arrivee, date_depart, date_retour,
          classe, gds, consolidateur, prix_achat, prix_vente, notes,
          reservation_id))
    conn.commit()
    conn.close()


def supprimer_reservation(reservation_id):
    conn = get_connexion()
    conn.execute("DELETE FROM reservations WHERE id=?", (reservation_id,))
    conn.commit()
    conn.close()


def lister_reservations(dossier_id):
    conn = get_connexion()
    lignes = conn.execute("""
        SELECT * FROM reservations WHERE dossier_id=? ORDER BY id
    """, (dossier_id,)).fetchall()
    conn.close()
    return lignes


def get_reservation(reservation_id):
    conn = get_connexion()
    ligne = conn.execute(
        "SELECT * FROM reservations WHERE id=?", (reservation_id,)).fetchone()
    conn.close()
    return ligne


# ===========================================================================
#  PAIEMENTS
# ===========================================================================
def creer_paiement(dossier_id, montant, mode="", reference="",
                   date_paiement="", notes=""):
    if not date_paiement:
        date_paiement = datetime.now().strftime("%Y-%m-%d")
    conn = get_connexion()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO paiements
            (dossier_id, montant, mode, reference, date_paiement, notes, date_creation)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (dossier_id, montant, mode, reference, date_paiement, notes, _maintenant()))
    conn.commit()
    nouvel_id = cur.lastrowid
    conn.close()
    return nouvel_id


def supprimer_paiement(paiement_id):
    conn = get_connexion()
    conn.execute("DELETE FROM paiements WHERE id=?", (paiement_id,))
    conn.commit()
    conn.close()


def lister_paiements(dossier_id):
    conn = get_connexion()
    lignes = conn.execute("""
        SELECT * FROM paiements WHERE dossier_id=? ORDER BY date_paiement, id
    """, (dossier_id,)).fetchall()
    conn.close()
    return lignes


# ===========================================================================
#  SOLDES ET STATISTIQUES
# ===========================================================================
def get_solde_dossier(dossier_id):
    """Calcule pour un dossier :
       - total_vente : somme des prix de vente (ce que le client doit)
       - total_paye  : somme des paiements reçus
       - solde       : ce qu'il reste à payer (peut être négatif = trop-perçu)"""
    conn = get_connexion()
    v = conn.execute(
        "SELECT COALESCE(SUM(prix_vente),0) AS t FROM reservations WHERE dossier_id=?",
        (dossier_id,)).fetchone()["t"]
    p = conn.execute(
        "SELECT COALESCE(SUM(montant),0) AS t FROM paiements WHERE dossier_id=?",
        (dossier_id,)).fetchone()["t"]
    conn.close()
    return {"total_vente": v, "total_paye": p, "solde": v - p}


def statistiques_globales():
    """Chiffres pour le tableau de bord."""
    conn = get_connexion()
    nb_clients = conn.execute("SELECT COUNT(*) AS n FROM clients").fetchone()["n"]
    nb_dossiers = conn.execute("SELECT COUNT(*) AS n FROM dossiers").fetchone()["n"]
    total_vente = conn.execute(
        "SELECT COALESCE(SUM(prix_vente),0) AS t FROM reservations").fetchone()["t"]
    total_achat = conn.execute(
        "SELECT COALESCE(SUM(prix_achat),0) AS t FROM reservations").fetchone()["t"]
    total_paye = conn.execute(
        "SELECT COALESCE(SUM(montant),0) AS t FROM paiements").fetchone()["t"]
    conn.close()
    return {
        "nb_clients": nb_clients,
        "nb_dossiers": nb_dossiers,
        "total_vente": total_vente,
        "total_achat": total_achat,
        "total_paye": total_paye,
        "solde_global": total_vente - total_paye,
        # BÉNÉFICE = prix de vente - prix d'achat (sur toutes les réservations)
        "benefice": total_vente - total_achat,
    }


# ===========================================================================
#  HISTORIQUE DES TRANSACTIONS PAR PÉRIODE
# ===========================================================================
def lister_transactions_periode(date_debut, date_fin):
    """Renvoie la liste unifiée des transactions entre deux dates INCLUSES.

    Deux types d'opérations sont réunis :
      - « Vente »        : une réservation/billet (prix d'achat, prix de vente, bénéfice)
      - « Encaissement » : un paiement reçu (montant, mode de paiement)

    date_debut / date_fin : texte au format 'AAAA-MM-JJ'.
    Chaque élément renvoyé est un dictionnaire simple, facile à afficher/imprimer.
    """
    conn = get_connexion()
    transactions = []

    # --- Ventes (réservations) ---
    ventes = conn.execute("""
        SELECT substr(r.date_creation, 1, 10) AS date_op,
               c.nom AS client_nom, c.prenom AS client_prenom,
               d.reference AS reference,
               r.type_billet AS type_billet,
               COALESCE(r.prix_achat, 0) AS prix_achat,
               COALESCE(r.prix_vente, 0) AS prix_vente
        FROM reservations r
        JOIN dossiers d ON d.id = r.dossier_id
        JOIN clients  c ON c.id = d.client_id
        WHERE substr(r.date_creation, 1, 10) BETWEEN ? AND ?
    """, (date_debut, date_fin)).fetchall()
    for v in ventes:
        client = f'{v["client_nom"]} {v["client_prenom"] or ""}'.strip()
        transactions.append({
            "date": v["date_op"] or "",
            "client": client,
            "reference": v["reference"] or "",
            "type": "Vente",
            "montant": v["prix_vente"],
            "mode": "",
            "prix_achat": v["prix_achat"],
            "prix_vente": v["prix_vente"],
            "benefice": v["prix_vente"] - v["prix_achat"],
        })

    # --- Encaissements (paiements) ---
    paiements = conn.execute("""
        SELECT substr(p.date_paiement, 1, 10) AS date_op,
               c.nom AS client_nom, c.prenom AS client_prenom,
               d.reference AS reference,
               COALESCE(p.montant, 0) AS montant,
               p.mode AS mode
        FROM paiements p
        JOIN dossiers d ON d.id = p.dossier_id
        JOIN clients  c ON c.id = d.client_id
        WHERE substr(p.date_paiement, 1, 10) BETWEEN ? AND ?
    """, (date_debut, date_fin)).fetchall()
    for p in paiements:
        client = f'{p["client_nom"]} {p["client_prenom"] or ""}'.strip()
        transactions.append({
            "date": p["date_op"] or "",
            "client": client,
            "reference": p["reference"] or "",
            "type": "Encaissement",
            "montant": p["montant"],
            "mode": p["mode"] or "",
            "prix_achat": None,
            "prix_vente": None,
            "benefice": None,
        })

    conn.close()
    # Tri par date croissante
    transactions.sort(key=lambda x: x["date"])
    return transactions


def totaux_transactions_periode(date_debut, date_fin):
    """Calcule les totaux d'une période (dates INCLUSES) :
       - total_ventes      : somme des prix de vente (réservations)
       - total_achats      : somme des prix d'achat (réservations)
       - total_encaisse    : somme des paiements reçus
       - total_benefice    : total_ventes - total_achats
       - total_restant     : total_ventes - total_encaisse (reste à payer sur la période)
    """
    conn = get_connexion()
    total_ventes = conn.execute("""
        SELECT COALESCE(SUM(prix_vente), 0) AS t FROM reservations
        WHERE substr(date_creation, 1, 10) BETWEEN ? AND ?
    """, (date_debut, date_fin)).fetchone()["t"]
    total_achats = conn.execute("""
        SELECT COALESCE(SUM(prix_achat), 0) AS t FROM reservations
        WHERE substr(date_creation, 1, 10) BETWEEN ? AND ?
    """, (date_debut, date_fin)).fetchone()["t"]
    total_encaisse = conn.execute("""
        SELECT COALESCE(SUM(montant), 0) AS t FROM paiements
        WHERE substr(date_paiement, 1, 10) BETWEEN ? AND ?
    """, (date_debut, date_fin)).fetchone()["t"]
    conn.close()
    return {
        "total_ventes": total_ventes,
        "total_achats": total_achats,
        "total_encaisse": total_encaisse,
        "total_benefice": total_ventes - total_achats,
        "total_restant": total_ventes - total_encaisse,
    }


# Permet de tester ce fichier seul : python database.py
if __name__ == "__main__":
    initialiser_base()
    print("Base de données initialisée avec succès :", config.DB_PATH)
