# -*- coding: utf-8 -*-
"""
migration_etape5.py
-------------------
ÉTAPE 5 du chantier de réorganisation : SÉPARER LES 4 ACTIVITÉS.

Ce que fait ce programme (UNIQUEMENT sur la COPIE DE TRAVAIL) :
  1) Crée 4 nouvelles tables séparées : billets, hotels, assurances, visas.
     - Chacune est reliée DIRECTEMENT au client (client_id).
     - Chacune a SES champs propres + les champs financiers communs
       (prix_fournisseur, prix_client, frais_service, autres_frais, reduction).
  2) Recopie les opérations existantes de la table `reservations` dans le bon
     tiroir, selon leur `type_billet` :
        - "Billet d'avion"  -> table billets
        - "Assurance"       -> table assurances
        (les hôtels/visas n'ont pas encore de données : tables créées vides)
  3) NE SUPPRIME RIEN : les tables `reservations` et `dossiers` restent intactes.
     Chaque ligne recopiée garde `source_reservation_id` = l'id d'origine
     (traçabilité + évite tout double comptage plus tard).

SÉCURITÉ : refuse de tourner ailleurs que sur un fichier « ...travail... ».
La vraie base et la comptabilité ne sont PAS touchées par ce programme.
"""

import os
import sqlite3
from datetime import datetime

# ---------------------------------------------------------------------------
# Base cible = COPIE DE TRAVAIL uniquement
# ---------------------------------------------------------------------------
DB = os.path.join(os.path.dirname(__file__), "data", "aplm_travail.db")

# Garde-fou : on n'accepte QUE la copie de travail.
if "travail" not in os.path.basename(DB).lower():
    raise SystemExit("SÉCURITÉ : ce programme ne s'exécute que sur aplm_travail.db")


def _maintenant():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ---------------------------------------------------------------------------
# Colonnes financières communes aux 4 activités (préparent l'Étape 10)
# ---------------------------------------------------------------------------
COLONNES_FINANCES = """
    prix_fournisseur REAL DEFAULT 0,   -- coût payé au fournisseur
    prix_client      REAL DEFAULT 0,   -- prix de vente de base au client
    frais_service    REAL DEFAULT 0,   -- frais de service de l'agence
    autres_frais     REAL DEFAULT 0,   -- autres frais éventuels
    reduction        REAL DEFAULT 0,   -- remise accordée au client
"""

# Colonnes communes de rattachement / traçabilité
COLONNES_COMMUNES_DEBUT = """
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    reference             TEXT,             -- ex: BIL-2026-0001 (rempli plus tard)
    client_id             INTEGER NOT NULL, -- LIEN DIRECT vers le client
    dossier_id            INTEGER,          -- ancien dossier (compatibilité)
    source_reservation_id INTEGER,          -- id d'origine si recopié de reservations
    passager              TEXT,             -- nom du voyageur/bénéficiaire
    statut                TEXT,
"""

COLONNES_COMMUNES_FIN = """
    mode_paiement      TEXT,   -- indicatif (les vrais paiements = module séparé)
    reference_paiement TEXT,
    notes              TEXT,
    date_creation      TEXT,
    cree_par           INTEGER,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
"""


def creer_tables(cur):
    # On repart de zéro pour ces 4 tables NEUVES (relançable sans risque).
    for t in ("billets", "hotels", "assurances", "visas"):
        cur.execute(f"DROP TABLE IF EXISTS {t}")

    # --- ✈️ BILLETS ---------------------------------------------------------
    cur.execute(f"""
        CREATE TABLE billets (
            {COLONNES_COMMUNES_DEBUT}
            type_billet          TEXT,   -- Aller simple / Aller-retour / Multi
            pnr                  TEXT,
            compagnie            TEXT,
            num_billet           TEXT,
            classe               TEXT,
            date_reservation     TEXT,
            date_limite_emission TEXT,   -- OPC (date limite d'émission)
            ville_depart         TEXT,
            date_depart          TEXT,
            ville_arrivee        TEXT,
            date_arrivee         TEXT,
            num_vol_aller        TEXT,
            escales              TEXT,
            ville_depart_retour  TEXT,
            date_retour          TEXT,
            ville_arrivee_retour TEXT,
            date_arrivee_retour  TEXT,
            num_vol_retour       TEXT,
            bagage_cabine        TEXT,
            bagage_soute         TEXT,
            gds                  TEXT,   -- INTERNE (jamais sur le reçu)
            consolidateur        TEXT,   -- INTERNE (jamais sur le reçu)
            {COLONNES_FINANCES}
            {COLONNES_COMMUNES_FIN}
        )
    """)

    # --- 🏨 HÔTELS ----------------------------------------------------------
    cur.execute(f"""
        CREATE TABLE hotels (
            {COLONNES_COMMUNES_DEBUT}
            nom_hotel        TEXT,
            ville            TEXT,
            pays             TEXT,
            adresse          TEXT,
            categorie        TEXT,   -- étoiles / catégorie
            type_hebergement TEXT,
            date_arrivee     TEXT,
            date_depart      TEXT,
            nb_nuits         INTEGER DEFAULT 0,
            nb_adultes       INTEGER DEFAULT 0,
            nb_enfants       INTEGER DEFAULT 0,
            nb_chambres      INTEGER DEFAULT 0,
            type_chambre     TEXT,
            type_lit         TEXT,
            formule          TEXT,   -- Sans repas / PDJ / Demi / Complète / Tout compris
            num_reservation  TEXT,
            date_reservation TEXT,
            {COLONNES_FINANCES}
            {COLONNES_COMMUNES_FIN}
        )
    """)

    # --- 🛡️ ASSURANCES ------------------------------------------------------
    cur.execute(f"""
        CREATE TABLE assurances (
            {COLONNES_COMMUNES_DEBUT}
            compagnie_assurance TEXT,
            num_police          TEXT,
            type_assurance      TEXT,
            destination         TEXT,
            zone_couverture     TEXT,
            date_debut          TEXT,
            date_fin            TEXT,
            motif_voyage        TEXT,
            date_naissance      TEXT,   -- de l'assuré (si différent du client)
            nationalite         TEXT,
            num_passeport       TEXT,
            {COLONNES_FINANCES}
            {COLONNES_COMMUNES_FIN}
        )
    """)

    # --- 🛂 ASSISTANCE VISA -------------------------------------------------
    cur.execute(f"""
        CREATE TABLE visas (
            {COLONNES_COMMUNES_DEBUT}
            pays_destination   TEXT,
            type_visa          TEXT,
            motif              TEXT,   -- Tourisme / Affaires / Études / ...
            nb_entrees         TEXT,   -- Simple / Double / Multiple
            duree              TEXT,
            date_voyage_prevue TEXT,
            num_dossier        TEXT,
            date_ouverture     TEXT,
            centre_depot       TEXT,
            ambassade          TEXT,
            date_depot         TEXT,
            date_rdv           TEXT,
            nationalite        TEXT,
            num_passeport      TEXT,
            date_exp_passeport TEXT,
            {COLONNES_FINANCES}
            {COLONNES_COMMUNES_FIN}
        )
    """)


def recopier_depuis_reservations(cur):
    """Recopie les réservations existantes dans le bon tiroir, selon type_billet.
    On récupère le client via le dossier. Rien n'est effacé côté reservations."""
    lignes = cur.execute("""
        SELECT r.*, d.client_id AS client_id, d.statut AS dossier_statut
        FROM reservations r
        JOIN dossiers d ON d.id = r.dossier_id
    """).fetchall()

    nb_billets = nb_assur = nb_autres = 0
    for r in lignes:
        type_op = (r["type_billet"] or "").strip().lower()

        if "billet" in type_op or "avion" in type_op:
            cur.execute("""
                INSERT INTO billets
                    (client_id, dossier_id, source_reservation_id, passager,
                     statut, pnr, compagnie, num_billet, classe,
                     ville_depart, ville_arrivee, date_depart, date_retour,
                     gds, consolidateur,
                     prix_fournisseur, prix_client,
                     notes, date_creation, cree_par)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (r["client_id"], r["dossier_id"], r["id"], r["passager"],
                  r["dossier_statut"], r["pnr"], r["compagnie"], r["num_billet"],
                  r["classe"], r["ville_depart"], r["ville_arrivee"],
                  r["date_depart"], r["date_retour"], r["gds"], r["consolidateur"],
                  r["prix_achat"] or 0, r["prix_vente"] or 0,
                  r["notes"], r["date_creation"], r["cree_par"]))
            nb_billets += 1

        elif "assur" in type_op:
            cur.execute("""
                INSERT INTO assurances
                    (client_id, dossier_id, source_reservation_id, passager,
                     statut, compagnie_assurance, num_police, destination,
                     date_debut, date_fin,
                     prix_fournisseur, prix_client,
                     notes, date_creation, cree_par)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (r["client_id"], r["dossier_id"], r["id"], r["passager"],
                  r["dossier_statut"], r["compagnie"], r["num_billet"],
                  r["ville_arrivee"], r["date_depart"], r["date_retour"],
                  r["prix_achat"] or 0, r["prix_vente"] or 0,
                  r["notes"], r["date_creation"], r["cree_par"]))
            nb_assur += 1
        else:
            # Type inconnu (Hôtel/Visa/Transfert/Autre sans données spécifiques) :
            # on ne devine rien -> on le laisse dans reservations (non recopié).
            nb_autres += 1

    return nb_billets, nb_assur, nb_autres


def main():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    creer_tables(cur)
    conn.commit()

    nb_billets, nb_assur, nb_autres = recopier_depuis_reservations(cur)
    conn.commit()

    # --- Vérifications ---
    def n(t):
        return cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]

    print("ÉTAPE 5 terminée sur la COPIE DE TRAVAIL :", DB)
    print("-" * 60)
    print(f"  Nouvelles tables créées : billets, hotels, assurances, visas")
    print(f"  Billets recopiés     : {n('billets')}   (attendu ~21)")
    print(f"  Assurances recopiées : {n('assurances')} (attendu ~6)")
    print(f"  Hôtels               : {n('hotels')}     (vide, normal)")
    print(f"  Visas                : {n('visas')}      (vide, normal)")
    print(f"  Non recopiés (type autre, laissés dans reservations) : {nb_autres}")
    print("-" * 60)
    print(f"  CONTRÔLE données conservées :")
    print(f"    clients      : {n('clients')}      (doit rester 232)")
    print(f"    reservations : {n('reservations')} (INTACTE, doit rester 27)")
    print(f"    dossiers     : {n('dossiers')}     (INTACTE, doit rester 29)")
    print(f"    paiements    : {n('paiements')}    (INTACTE, doit rester 27)")
    print(f"    ecritures    : {n('ecritures')}    (comptabilité INTACTE = 78)")

    # Contrôle croisé : total recopié = total des reservations de ces 2 types
    total_types = cur.execute("""
        SELECT COUNT(*) FROM reservations
        WHERE LOWER(COALESCE(type_billet,'')) LIKE '%billet%'
           OR LOWER(COALESCE(type_billet,'')) LIKE '%avion%'
           OR LOWER(COALESCE(type_billet,'')) LIKE '%assur%'
    """).fetchone()[0]
    recopies = n('billets') + n('assurances')
    print("-" * 60)
    if recopies == total_types:
        print(f"  [OK] {recopies} operations recopiees = {total_types} attendues.")
    else:
        print(f"  [ECART] {recopies} recopiees mais {total_types} attendues !")

    conn.close()


if __name__ == "__main__":
    main()
