# -*- coding: utf-8 -*-
"""
activites.py
------------
MODULE DES 4 ACTIVITÉS SÉPARÉES de l'agence :
    ✈️ billets   🏨 hotels   🛡️ assurances   🛂 visas

Idée directrice (réorganisation 2026) :
    - Chaque activité a SA table et SES champs propres.
    - Chaque opération est reliée DIRECTEMENT au client (client_id).
    - Les CALCULS financiers sont automatiques et IDENTIQUES partout :
          total_client = prix_client + frais_service + autres_frais - reduction
          marge        = total_client - prix_fournisseur
          reste_a_payer = total_client - total_des_paiements
      (choix validé par l'utilisateur : la base est le PRIX DE VENTE).
    - Les paiements se rattachent à l'opération (module paiements unifié).

Ce module NE touche PAS la comptabilité. La resynchronisation comptable est
faite séparément (comptabilite.py, Étape 13), sans double comptage.
"""

from datetime import datetime
import database as db


# Les 4 activités : clé interne -> (préfixe de référence, libellé lisible)
ACTIVITES = {
    "billet":    ("BIL", "Billet"),
    "hotel":     ("HOT", "Hôtel"),
    "assurance": ("ASS", "Assurance"),
    "visa":      ("VIS", "Visa"),
}

# TVA par défaut proposée (Sénégal = 18 %). 0 = pas de TVA sur l'opération.
# La MÉTHODE d'application en comptabilité sera confirmée à l'Étape 13.
TVA_DEFAUT = 18.0


# ===========================================================================
#  CRÉATION / MISE À JOUR DES TABLES (réorganisation)
# ===========================================================================
def _colonnes_finances():
    return """
        prix_fournisseur REAL DEFAULT 0,
        prix_client      REAL DEFAULT 0,
        frais_service    REAL DEFAULT 0,
        autres_frais     REAL DEFAULT 0,
        reduction        REAL DEFAULT 0,
        tva_taux         REAL DEFAULT 0,
    """


def _debut_commun():
    return """
        id                    INTEGER PRIMARY KEY AUTOINCREMENT,
        reference             TEXT,
        client_id             INTEGER NOT NULL,
        dossier_id            INTEGER,
        source_reservation_id INTEGER,
        passager              TEXT,
        statut                TEXT,
    """


def _fin_commun():
    return """
        mode_paiement      TEXT,
        reference_paiement TEXT,
        notes              TEXT,
        date_creation      TEXT,
        cree_par           INTEGER,
        FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
    """


def initialiser():
    """Crée les tables des 4 activités si besoin, enrichit la fiche client
    et met à niveau la table des paiements. Sans effet si déjà fait.
    100 % additif : aucune donnée existante n'est supprimée."""
    conn = db.get_connexion()
    cur = conn.cursor()

    cur.execute(f"""CREATE TABLE IF NOT EXISTS billets (
        {_debut_commun()}
        type_billet TEXT, pnr TEXT, compagnie TEXT, num_billet TEXT, classe TEXT,
        date_reservation TEXT, date_limite_emission TEXT,
        ville_depart TEXT, date_depart TEXT, ville_arrivee TEXT, date_arrivee TEXT,
        num_vol_aller TEXT, escales TEXT,
        ville_depart_retour TEXT, date_retour TEXT, ville_arrivee_retour TEXT,
        date_arrivee_retour TEXT, num_vol_retour TEXT,
        bagage_cabine TEXT, bagage_soute TEXT,
        gds TEXT, consolidateur TEXT,
        {_colonnes_finances()}
        {_fin_commun()}
    )""")

    cur.execute(f"""CREATE TABLE IF NOT EXISTS hotels (
        {_debut_commun()}
        nom_hotel TEXT, ville TEXT, pays TEXT, adresse TEXT, categorie TEXT,
        type_hebergement TEXT, date_arrivee TEXT, date_depart TEXT,
        nb_nuits INTEGER DEFAULT 0, nb_adultes INTEGER DEFAULT 0,
        nb_enfants INTEGER DEFAULT 0, nb_chambres INTEGER DEFAULT 0,
        type_chambre TEXT, type_lit TEXT, formule TEXT,
        num_reservation TEXT, date_reservation TEXT,
        {_colonnes_finances()}
        {_fin_commun()}
    )""")

    cur.execute(f"""CREATE TABLE IF NOT EXISTS assurances (
        {_debut_commun()}
        compagnie_assurance TEXT, num_police TEXT, type_assurance TEXT,
        destination TEXT, zone_couverture TEXT, date_debut TEXT, date_fin TEXT,
        motif_voyage TEXT, date_naissance TEXT, nationalite TEXT, num_passeport TEXT,
        {_colonnes_finances()}
        {_fin_commun()}
    )""")

    cur.execute(f"""CREATE TABLE IF NOT EXISTS visas (
        {_debut_commun()}
        pays_destination TEXT, type_visa TEXT, motif TEXT, nb_entrees TEXT,
        duree TEXT, date_voyage_prevue TEXT, num_dossier TEXT, date_ouverture TEXT,
        centre_depot TEXT, ambassade TEXT, date_depot TEXT, date_rdv TEXT,
        nationalite TEXT, num_passeport TEXT, date_exp_passeport TEXT,
        {_colonnes_finances()}
        {_fin_commun()}
    )""")

    conn.commit()
    conn.close()

    # Fiche client enrichie + paiements rattachés à l'opération
    db.enrichir_fiche_client()
    db.migrer_paiements_operations()


def migrer_reservations_vers_activites():
    """Recopie les réservations existantes vers billets/assurances selon leur
    type. IDEMPOTENT : une réservation déjà recopiée (repérée par
    source_reservation_id) n'est jamais recopiée deux fois. Ne supprime rien.
    Renvoie (nb_billets, nb_assurances, nb_ignores)."""
    conn = db.get_connexion()
    cur = conn.cursor()

    # Réservations déjà migrées (pour ne pas doublonner)
    deja = set()
    for table in ("billets", "assurances", "hotels", "visas"):
        for r in cur.execute(
                f"SELECT source_reservation_id FROM {table} "
                f"WHERE source_reservation_id IS NOT NULL").fetchall():
            deja.add(r["source_reservation_id"])

    lignes = cur.execute("""
        SELECT r.*, d.client_id AS client_id, d.statut AS dossier_statut
        FROM reservations r JOIN dossiers d ON d.id = r.dossier_id
    """).fetchall()

    nb_b = nb_a = nb_i = 0
    for r in lignes:
        if r["id"] in deja:
            continue
        type_op = (r["type_billet"] or "").strip().lower()
        if "billet" in type_op or "avion" in type_op:
            cur.execute("""
                INSERT INTO billets
                    (client_id, dossier_id, source_reservation_id, passager, statut,
                     pnr, compagnie, num_billet, classe, ville_depart, ville_arrivee,
                     date_depart, date_retour, gds, consolidateur,
                     prix_fournisseur, prix_client, notes, date_creation, cree_par)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (r["client_id"], r["dossier_id"], r["id"], r["passager"],
                  r["dossier_statut"], r["pnr"], r["compagnie"], r["num_billet"],
                  r["classe"], r["ville_depart"], r["ville_arrivee"],
                  r["date_depart"], r["date_retour"], r["gds"], r["consolidateur"],
                  r["prix_achat"] or 0, r["prix_vente"] or 0,
                  r["notes"], r["date_creation"], r["cree_par"]))
            nb_b += 1
        elif "assur" in type_op:
            cur.execute("""
                INSERT INTO assurances
                    (client_id, dossier_id, source_reservation_id, passager, statut,
                     compagnie_assurance, num_police, destination, date_debut, date_fin,
                     prix_fournisseur, prix_client, notes, date_creation, cree_par)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (r["client_id"], r["dossier_id"], r["id"], r["passager"],
                  r["dossier_statut"], r["compagnie"], r["num_billet"],
                  r["ville_arrivee"], r["date_depart"], r["date_retour"],
                  r["prix_achat"] or 0, r["prix_vente"] or 0,
                  r["notes"], r["date_creation"], r["cree_par"]))
            nb_a += 1
        else:
            nb_i += 1

    conn.commit()
    conn.close()
    return nb_b, nb_a, nb_i


# ===========================================================================
#  CALCULS AUTOMATIQUES (identiques pour les 4 activités)
# ===========================================================================
def _f(x):
    try:
        return float(x or 0)
    except (TypeError, ValueError):
        return 0.0


def calc_totaux(prix_client=0, frais_service=0, autres_frais=0, reduction=0,
                prix_fournisseur=0, tva_taux=0, total_paye=0):
    """Applique la formule validée par l'utilisateur :
        total_client = prix_client + frais_service + autres_frais - reduction
        marge        = total_client - prix_fournisseur
    La TVA (choix utilisateur) porte sur les FRAIS DE SERVICE :
        montant_tva  = frais_service * tva_taux %      (ex : 20 000 x 18% = 3 600)
    Renvoie un dictionnaire de tous les montants calculés."""
    total_client = round(_f(prix_client) + _f(frais_service)
                         + _f(autres_frais) - _f(reduction), 2)
    marge = round(total_client - _f(prix_fournisseur), 2)
    montant_tva = round(_f(frais_service) * _f(tva_taux) / 100.0, 2) if _f(tva_taux) else 0.0
    reste = round(total_client - _f(total_paye), 2)
    return {
        "total_client": total_client,
        "marge": marge,
        "montant_tva": montant_tva,
        "total_paye": round(_f(total_paye), 2),
        "reste_a_payer": reste,
    }


def totaux_operation(activite, operation_id):
    """Calcule les totaux d'une opération existante (avec ses paiements)."""
    op = get_operation(activite, operation_id)
    if op is None:
        return None
    paye = get_total_paye_operation(activite, operation_id)
    return calc_totaux(op["prix_client"], op["frais_service"], op["autres_frais"],
                       op["reduction"], op["prix_fournisseur"], op["tva_taux"], paye)


# ===========================================================================
#  OUTILS INTERNES
# ===========================================================================
def _valider_activite(activite):
    if activite not in ACTIVITES:
        raise ValueError(f"Activité inconnue : {activite}")


def _table(activite):
    _valider_activite(activite)
    return activite + "s" if activite != "visa" else "visas"  # billets/hotels/assurances/visas


def _colonnes_table(conn, table):
    return [r["name"] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]


def generer_reference(activite):
    """Fabrique une référence unique, ex : BIL-2026-0001."""
    _valider_activite(activite)
    prefixe_court = ACTIVITES[activite][0]
    table = _table(activite)
    conn = db.get_connexion()
    annee = datetime.now().strftime("%Y")
    prefixe = f"{prefixe_court}-{annee}-"
    n = conn.execute(f"SELECT COUNT(*) AS n FROM {table} WHERE reference LIKE ?",
                     (prefixe + "%",)).fetchone()["n"]
    conn.close()
    return f"{prefixe}{(n or 0) + 1:04d}"


# ===========================================================================
#  CRÉER / MODIFIER / SUPPRIMER / LIRE une opération
# ===========================================================================
def creer_operation(activite, client_id, donnees=None):
    """Crée une opération dans la bonne table.
    `donnees` : dictionnaire {colonne: valeur}. Les clés inconnues sont ignorées
    (on ne garde que les vraies colonnes de la table -> robuste)."""
    _valider_activite(activite)
    donnees = dict(donnees or {})
    table = _table(activite)

    conn = db.get_connexion()
    cur = conn.cursor()
    colonnes = set(_colonnes_table(conn, table))

    donnees["client_id"] = client_id
    donnees.setdefault("reference", generer_reference(activite))
    donnees["date_creation"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    donnees["cree_par"] = db.auth.id_courant()

    # On ne conserve que les colonnes réellement présentes dans la table
    champs = [c for c in donnees.keys() if c in colonnes and c != "id"]
    valeurs = [donnees[c] for c in champs]
    placeholders = ", ".join("?" for _ in champs)
    cur.execute(f"INSERT INTO {table} ({', '.join(champs)}) VALUES ({placeholders})",
                valeurs)
    conn.commit()
    nid = cur.lastrowid
    conn.close()
    db.enregistrer_activite("Création", ACTIVITES[activite][1],
                            donnees.get("reference", ""))
    return nid


def modifier_operation(activite, operation_id, donnees):
    """Modifie une opération (ne met à jour que les colonnes fournies)."""
    _valider_activite(activite)
    table = _table(activite)
    conn = db.get_connexion()
    colonnes = set(_colonnes_table(conn, table))
    champs = [c for c in donnees.keys()
              if c in colonnes and c not in ("id", "client_id", "date_creation",
                                             "cree_par", "reference")]
    if champs:
        set_clause = ", ".join(f"{c}=?" for c in champs)
        valeurs = [donnees[c] for c in champs] + [operation_id]
        conn.execute(f"UPDATE {table} SET {set_clause} WHERE id=?", valeurs)
        conn.commit()
    conn.close()
    db.enregistrer_activite("Modification", ACTIVITES[activite][1], f"#{operation_id}")


def supprimer_operation(activite, operation_id):
    _valider_activite(activite)
    table = _table(activite)
    conn = db.get_connexion()
    conn.execute(f"DELETE FROM {table} WHERE id=?", (operation_id,))
    conn.commit()
    conn.close()
    db.enregistrer_activite("Suppression", ACTIVITES[activite][1], f"#{operation_id}")


def get_operation(activite, operation_id):
    table = _table(activite)
    conn = db.get_connexion()
    ligne = conn.execute(f"SELECT * FROM {table} WHERE id=?",
                         (operation_id,)).fetchone()
    conn.close()
    return ligne


def lister_operations(activite, recherche="", client_id=None):
    """Liste les opérations d'une activité (avec nom du client)."""
    table = _table(activite)
    conn = db.get_connexion()
    base = f"""
        SELECT o.*, c.nom AS client_nom, c.prenom AS client_prenom, c.code AS client_code
        FROM {table} o JOIN clients c ON c.id = o.client_id
    """
    cond, params = [], []
    if client_id is not None:
        cond.append("o.client_id = ?"); params.append(client_id)
    if recherche:
        motif = f"%{recherche}%"
        cond.append("(o.reference LIKE ? OR o.passager LIKE ? OR c.nom LIKE ? "
                    "OR c.prenom LIKE ?)")
        params += [motif, motif, motif, motif]
    if cond:
        base += " WHERE " + " AND ".join(cond)
    base += " ORDER BY o.date_creation DESC, o.id DESC"
    lignes = conn.execute(base, params).fetchall()
    conn.close()
    return lignes


def lister_clients_billets():
    """Rubrique Billets : « Liste des clients qui ont un billet »
    (Nom, Prénom, Téléphone, PNR, Prix de vente) — un billet par ligne."""
    conn = db.get_connexion()
    lignes = conn.execute("""
        SELECT c.nom AS nom, c.prenom AS prenom, c.telephone AS telephone,
               b.pnr AS pnr, b.prix_client AS prix_vente
        FROM billets b JOIN clients c ON c.id = b.client_id
        ORDER BY c.nom, c.prenom
    """).fetchall()
    conn.close()
    return lignes


def lister_operations_client(client_id):
    """HISTORIQUE CLIENT (§2) : toutes les opérations d'un client, toutes
    activités confondues, avec leur total calculé. Liste de dicts simples."""
    resultat = []
    for activite in ACTIVITES:
        for o in lister_operations(activite, client_id=client_id):
            t = calc_totaux(o["prix_client"], o["frais_service"], o["autres_frais"],
                            o["reduction"], o["prix_fournisseur"], o["tva_taux"],
                            get_total_paye_operation(activite, o["id"]))
            resultat.append({
                "activite": activite,
                "activite_libelle": ACTIVITES[activite][1],
                "id": o["id"],
                "reference": o["reference"] or "",
                "passager": o["passager"] or "",
                "statut": o["statut"] or "",
                "date": (o["date_creation"] or "")[:10],
                "total_client": t["total_client"],
                "total_paye": t["total_paye"],
                "reste_a_payer": t["reste_a_payer"],
                "marge": t["marge"],
            })
    resultat.sort(key=lambda x: x["date"], reverse=True)
    return resultat


# ===========================================================================
#  PAIEMENTS RATTACHÉS À UNE OPÉRATION (module paiements unifié)
# ===========================================================================
def creer_paiement_operation(activite, operation_id, montant, mode="",
                             reference="", date_paiement="", notes=""):
    """Enregistre un paiement rattaché à UNE opération précise (pas au dossier).
    Le client est déduit automatiquement de l'opération."""
    _valider_activite(activite)
    op = get_operation(activite, operation_id)
    if op is None:
        raise ValueError("Opération introuvable.")
    return db.creer_paiement_operation(
        client_id=op["client_id"], operation_type=activite,
        operation_id=operation_id, montant=montant, mode=mode,
        reference=reference, date_paiement=date_paiement, notes=notes)


def lister_paiements_operation(activite, operation_id):
    _valider_activite(activite)
    conn = db.get_connexion()
    lignes = conn.execute(
        "SELECT * FROM paiements WHERE operation_type=? AND operation_id=? "
        "ORDER BY date_paiement, id", (activite, operation_id)).fetchall()
    conn.close()
    return lignes


def get_total_paye_operation(activite, operation_id):
    _valider_activite(activite)
    conn = db.get_connexion()
    t = conn.execute(
        "SELECT COALESCE(SUM(montant),0) AS t FROM paiements "
        "WHERE operation_type=? AND operation_id=?",
        (activite, operation_id)).fetchone()["t"]
    conn.close()
    return t or 0
