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
import auth


# ===========================================================================
#  CONNEXION À LA BASE
# ===========================================================================
def get_connexion():
    """Ouvre une connexion à la base de données.

    - En mode « client » (multi-postes) : renvoie une connexion À DISTANCE
      vers le serveur du bureau (voir db_client.py). Le reste du code ne voit
      aucune différence : il croit parler à une base SQLite locale.
    - Sinon (mode « local » ou « serveur ») : connexion SQLite locale habituelle.

    row_factory = sqlite3.Row permet de lire les colonnes par leur nom
    (ex: client['nom']) au lieu d'un simple numéro."""
    import reseau
    if reseau.est_client():
        import db_client
        return db_client.ConnexionDistante(reseau.hote(), reseau.port(), reseau.cle())
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")   # respecte les liens entre tables
    conn.execute("PRAGMA busy_timeout = 5000") # attend jusqu'à 5s si la base est occupée
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

    # --- Table UTILISATEURS (comptes de connexion) -------------------------
    # role : 'admin' (accès à tout) ou 'agent' (travail quotidien).
    # actif : 1 = le compte peut se connecter, 0 = compte désactivé.
    # Le mot de passe n'est JAMAIS stocké en clair : on garde seulement
    # un "sel" (mdp_sel) et une empreinte chiffrée (mdp_hash) — voir auth.py.
    cur.execute("""
        CREATE TABLE IF NOT EXISTS utilisateurs (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            nom            TEXT NOT NULL,
            prenom         TEXT,
            identifiant    TEXT NOT NULL UNIQUE,
            email          TEXT,
            mdp_sel        TEXT,
            mdp_hash       TEXT,
            role           TEXT NOT NULL DEFAULT 'agent',
            actif          INTEGER NOT NULL DEFAULT 1,
            doit_changer_mdp INTEGER NOT NULL DEFAULT 0,
            tentatives_echouees INTEGER NOT NULL DEFAULT 0,
            bloque_jusqu_a TEXT,
            date_creation  TEXT
        )
    """)

    # --- Table JOURNAL DES ACTIVITÉS (traçabilité globale) -----------------
    # Chaque opération importante y laisse une trace :
    #   Date/heure | Utilisateur | Action | Objet | Détails
    cur.execute("""
        CREATE TABLE IF NOT EXISTS journal_activites (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            date_heure       TEXT,
            utilisateur_id   INTEGER,
            utilisateur_nom  TEXT,
            action           TEXT,
            objet            TEXT,
            details          TEXT
        )
    """)

    # --- Table AVOIRS (cagnotte du client : dépôts petit à petit) ----------
    # Un « avoir » est l'argent qu'un client verse d'avance, petit à petit,
    # jusqu'à réunir la somme nécessaire pour payer son billet/voyage.
    # Chaque ligne = UN mouvement :
    #   type = 'depot'        -> le client ajoute de l'argent (la cagnotte monte)
    #   type = 'utilisation'  -> on se sert de l'argent pour payer un dossier
    #                            (la cagnotte descend)
    # Le SOLDE de la cagnotte = somme des dépôts - somme des utilisations.
    # dossier_id : rempli seulement pour une 'utilisation' (le voyage payé).
    cur.execute("""
        CREATE TABLE IF NOT EXISTS avoirs (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id      INTEGER NOT NULL,
            type           TEXT NOT NULL,      -- 'depot' ou 'utilisation'
            montant        REAL NOT NULL,
            mode           TEXT,               -- mode de paiement (pour un dépôt)
            reference      TEXT,
            dossier_id     INTEGER,            -- dossier payé (pour une utilisation)
            notes          TEXT,
            date_mouvement TEXT,
            date_creation  TEXT,
            cree_par       INTEGER,
            FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
        )
    """)

    # --- MIGRATION : colonne "cree_par" (qui a créé l'opération ?) ---------
    # Ajoutée seulement si elle n'existe pas encore. Les données déjà
    # enregistrées ne sont pas touchées (cree_par restera vide pour elles).
    for table in ("clients", "dossiers", "reservations", "paiements"):
        _ajouter_colonne_si_absente(cur, table, "cree_par", "INTEGER")

    # Indicateur « doit changer son mot de passe » (pour les bases déjà créées)
    _ajouter_colonne_si_absente(cur, "utilisateurs", "doit_changer_mdp",
                                "INTEGER NOT NULL DEFAULT 0")
    _ajouter_colonne_si_absente(cur, "utilisateurs", "tentatives_echouees",
                                "INTEGER NOT NULL DEFAULT 0")
    _ajouter_colonne_si_absente(cur, "utilisateurs", "bloque_jusqu_a", "TEXT")

    # Permissions détaillées de l'agent (liste de clés séparées par des virgules)
    _ajouter_colonne_si_absente(cur, "utilisateurs", "permissions", "TEXT")

    # --- Table PARAMÈTRES DE L'AGENCE (nom, adresse, logo...) --------------
    # Une seule ligne (id=1). Rangée dans la base PARTAGÉE (et non plus dans
    # un fichier local par poste) pour que tous les ordinateurs connectés au
    # même serveur - Windows comme Mac - affichent exactement les mêmes
    # coordonnées et le même logo sur les reçus, sans ressaisie manuelle sur
    # chaque poste. Voir settings.py pour la couche de synchronisation.
    cur.execute("""
        CREATE TABLE IF NOT EXISTS parametres_agence (
            id           INTEGER PRIMARY KEY CHECK (id = 1),
            nom          TEXT NOT NULL DEFAULT '',
            slogan       TEXT NOT NULL DEFAULT '',
            adresse      TEXT NOT NULL DEFAULT '',
            telephone    TEXT NOT NULL DEFAULT '',
            email        TEXT NOT NULL DEFAULT '',
            site_web     TEXT NOT NULL DEFAULT '',
            rccm         TEXT NOT NULL DEFAULT '',
            devise       TEXT NOT NULL DEFAULT 'FCFA',
            logo_base64  TEXT,
            logo_format  TEXT,
            date_maj     TEXT
        )
    """)

    conn.commit()
    conn.close()


# ===========================================================================
#  PARAMÈTRES DE L'AGENCE (partagés entre tous les postes connectés)
# ===========================================================================
def get_parametres_agence():
    """Renvoie les paramètres partagés de l'agence (dict), ou None si rien
    n'a encore été enregistré (base toute neuve)."""
    conn = get_connexion()
    ligne = conn.execute(
        "SELECT * FROM parametres_agence WHERE id = 1").fetchone()
    conn.close()
    if ligne is None:
        return None
    return {k: ligne[k] for k in ligne.keys()}


def definir_parametres_agence(valeurs, logo_base64=None, logo_format=None):
    """Enregistre les paramètres partagés de l'agence.

    Si `logo_base64` vaut None, le logo déjà enregistré en base est conservé
    tel quel (évite d'effacer le logo quand on modifie juste le téléphone,
    par exemple, depuis un poste qui n'a pas encore le fichier logo local)."""
    conn = get_connexion()
    if logo_base64 is None:
        existant = conn.execute(
            "SELECT logo_base64, logo_format FROM parametres_agence "
            "WHERE id = 1").fetchone()
        if existant is not None:
            logo_base64 = existant["logo_base64"]
            logo_format = existant["logo_format"]
    conn.execute("""
        INSERT INTO parametres_agence
            (id, nom, slogan, adresse, telephone, email, site_web, rccm,
             devise, logo_base64, logo_format, date_maj)
        VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            nom=excluded.nom, slogan=excluded.slogan, adresse=excluded.adresse,
            telephone=excluded.telephone, email=excluded.email,
            site_web=excluded.site_web, rccm=excluded.rccm,
            devise=excluded.devise, logo_base64=excluded.logo_base64,
            logo_format=excluded.logo_format, date_maj=excluded.date_maj
    """, (
        valeurs.get("nom", "") or "", valeurs.get("slogan", "") or "",
        valeurs.get("adresse", "") or "", valeurs.get("telephone", "") or "",
        valeurs.get("email", "") or "", valeurs.get("site_web", "") or "",
        valeurs.get("rccm", "") or "", valeurs.get("devise", "FCFA") or "FCFA",
        logo_base64, logo_format, _maintenant(),
    ))
    conn.commit()
    conn.close()


def _ajouter_colonne_si_absente(cur, table, colonne, definition):
    """Ajoute une colonne à une table SEULEMENT si elle n'existe pas déjà.
    C'est une "migration" : cela fait évoluer la base sans perdre les données."""
    colonnes_existantes = [r["name"] for r in cur.execute(
        f"PRAGMA table_info({table})").fetchall()]
    if colonne not in colonnes_existantes:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {colonne} {definition}")


# ===========================================================================
#  PETITS OUTILS
# ===========================================================================
def _maintenant():
    """Renvoie la date + heure actuelle sous forme de texte."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _id_courant():
    """Identifiant de l'utilisateur actuellement connecté (ou None).
    Sert à enregistrer « qui a créé » chaque opération (traçabilité)."""
    return auth.id_courant()


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
                 type_piece="", num_piece="", notes="",
                 date_naissance="", nationalite="", num_passeport="",
                 date_exp_passeport=""):
    """Crée une fiche client. Les nouveaux champs (date de naissance,
    nationalité, passeport...) ne sont enregistrés que si la colonne existe
    déjà dans la base -> aucune erreur si la base n'est pas encore migrée."""
    conn = get_connexion()
    cur = conn.cursor()
    donnees = {
        "code": generer_code_client(), "nom": nom, "prenom": prenom,
        "telephone": telephone, "email": email, "adresse": adresse,
        "type_piece": type_piece, "num_piece": num_piece, "notes": notes,
        "date_creation": _maintenant(), "cree_par": _id_courant(),
        "date_naissance": date_naissance, "nationalite": nationalite,
        "num_passeport": num_passeport, "date_exp_passeport": date_exp_passeport,
    }
    cols = {r["name"] for r in cur.execute("PRAGMA table_info(clients)").fetchall()}
    champs = [c for c in donnees if c in cols]
    vals = [donnees[c] for c in champs]
    cur.execute(f"INSERT INTO clients ({', '.join(champs)}) "
                f"VALUES ({', '.join('?' for _ in champs)})", vals)
    conn.commit()
    nouvel_id = cur.lastrowid
    conn.close()
    enregistrer_activite("Création", "Client", f"{nom} {prenom}".strip())
    return nouvel_id


def modifier_client(client_id, nom, prenom="", telephone="", email="",
                    adresse="", type_piece="", num_piece="", notes="",
                    date_naissance=None, nationalite=None, num_passeport=None,
                    date_exp_passeport=None):
    """Modifie une fiche client. Les champs enrichis passés à None ne sont
    pas modifiés (utile pour compléter une fiche sans écraser le reste)."""
    conn = get_connexion()
    cur = conn.cursor()
    cols = {r["name"] for r in cur.execute("PRAGMA table_info(clients)").fetchall()}
    donnees = {
        "nom": nom, "prenom": prenom, "telephone": telephone, "email": email,
        "adresse": adresse, "type_piece": type_piece, "num_piece": num_piece,
        "notes": notes,
    }
    for cle, val in (("date_naissance", date_naissance),
                     ("nationalite", nationalite),
                     ("num_passeport", num_passeport),
                     ("date_exp_passeport", date_exp_passeport)):
        if val is not None:
            donnees[cle] = val
    champs = [c for c in donnees if c in cols]
    set_clause = ", ".join(f"{c}=?" for c in champs)
    vals = [donnees[c] for c in champs] + [client_id]
    cur.execute(f"UPDATE clients SET {set_clause} WHERE id=?", vals)
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
#  RÉORGANISATION 2026 : fiche client enrichie, recherche, anti-doublons
# ===========================================================================
def enrichir_fiche_client():
    """Ajoute les 4 champs enrichis à la fiche client (sans perte de données).
    Idempotent : sans effet si les colonnes existent déjà."""
    conn = get_connexion()
    cur = conn.cursor()
    for col in ("date_naissance", "nationalite", "num_passeport",
                "date_exp_passeport"):
        _ajouter_colonne_si_absente(cur, "clients", col, "TEXT")
    conn.commit()
    conn.close()


def _norm(txt):
    """Minuscules + espaces réduits (pour comparer des textes)."""
    return " ".join((txt or "").strip().lower().split())


def _norm_tel(txt):
    """Ne garde que les chiffres d'un numéro de téléphone."""
    return "".join(c for c in (txt or "") if c.isdigit())


def rechercher_clients_avance(terme, limite=25):
    """Recherche un client par nom, prénom, téléphone, email, passeport ou code.
    (Le passeport n'est cherché que si la colonne existe.)"""
    conn = get_connexion()
    cols = {r["name"] for r in conn.execute("PRAGMA table_info(clients)").fetchall()}
    motif = f"%{(terme or '').strip()}%"
    champs = ["nom", "prenom", "telephone", "email", "code"]
    if "num_passeport" in cols:
        champs.append("num_passeport")
    where = " OR ".join(f"{c} LIKE ?" for c in champs)
    params = [motif] * len(champs) + [limite]
    lignes = conn.execute(
        f"SELECT * FROM clients WHERE {where} ORDER BY nom, prenom LIMIT ?",
        params).fetchall()
    conn.close()
    return lignes


def detecter_doublons(nom="", prenom="", telephone="", email="", num_passeport=""):
    """Repère un client DÉJÀ existant (§5), par ordre de fiabilité :
       1) passeport  2) téléphone  3) email  4) nom+prénom.
    Renvoie une liste de dicts {client, critere}. Liste vide = pas de doublon."""
    conn = get_connexion()
    cols = {r["name"] for r in conn.execute("PRAGMA table_info(clients)").fetchall()}
    clients = conn.execute("SELECT * FROM clients").fetchall()
    conn.close()

    np = _norm(num_passeport)
    tel = _norm_tel(telephone)
    em = _norm(email)
    nom_n, prenom_n = _norm(nom), _norm(prenom)
    a_passeport = "num_passeport" in cols

    trouves, deja = [], set()

    def _ajouter(c, critere):
        if c["id"] not in deja:
            deja.add(c["id"])
            trouves.append({"client": c, "critere": critere})

    if np and a_passeport:
        for c in clients:
            if _norm(c["num_passeport"]) == np:
                _ajouter(c, "numéro de passeport")
    if tel:
        for c in clients:
            if _norm_tel(c["telephone"]) == tel:
                _ajouter(c, "téléphone")
    if em:
        for c in clients:
            if _norm(c["email"]) == em:
                _ajouter(c, "email")
    if nom_n and prenom_n:
        for c in clients:
            if _norm(c["nom"]) == nom_n and _norm(c["prenom"]) == prenom_n:
                _ajouter(c, "nom + prénom")
    return trouves


def trouver_ou_creer_client(donnees_client, client_existant_id=None,
                            forcer_creation=False):
    """Cœur des Étapes 7-8-9, utilisé par tous les formulaires d'opération.

    - Si `client_existant_id` est fourni -> on rattache à ce client (Étape 7).
    - Sinon on cherche les doublons (Étape 9) :
        * doublon(s) trouvé(s) et `forcer_creation` = False
              -> on NE crée RIEN, on renvoie la liste des doublons pour que
                 l'UTILISATEUR décide (utiliser l'existant / créer quand même).
        * aucun doublon (ou forcer_creation = True)
              -> on crée la fiche + son code, et on renvoie son id (Étape 8).

    Renvoie un dict :
        {"client_id": <id>}                 -> rattaché ou créé
        {"doublons": [ {client,critere} ]}  -> décision requise
    """
    if client_existant_id:
        return {"client_id": int(client_existant_id)}

    d = dict(donnees_client or {})
    if not forcer_creation:
        doublons = detecter_doublons(
            nom=d.get("nom", ""), prenom=d.get("prenom", ""),
            telephone=d.get("telephone", ""), email=d.get("email", ""),
            num_passeport=d.get("num_passeport", ""))
        if doublons:
            return {"doublons": doublons}

    nid = creer_client(
        nom=d.get("nom", ""), prenom=d.get("prenom", ""),
        telephone=d.get("telephone", ""), email=d.get("email", ""),
        adresse=d.get("adresse", ""), type_piece=d.get("type_piece", ""),
        num_piece=d.get("num_piece", ""), notes=d.get("notes", ""),
        date_naissance=d.get("date_naissance", ""),
        nationalite=d.get("nationalite", ""),
        num_passeport=d.get("num_passeport", ""),
        date_exp_passeport=d.get("date_exp_passeport", ""))
    return {"client_id": nid}


# ===========================================================================
#  DOSSIERS
# ===========================================================================
def creer_dossier(client_id, titre="", statut="Ouvert", notes=""):
    conn = get_connexion()
    cur = conn.cursor()
    reference = generer_reference_dossier()
    cur.execute("""
        INSERT INTO dossiers (reference, client_id, titre, statut, notes, date_creation, cree_par)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (reference, client_id, titre, statut, notes, _maintenant(), _id_courant()))
    conn.commit()
    nouvel_id = cur.lastrowid
    conn.close()
    enregistrer_activite("Création", "Dossier", reference)
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
             gds, consolidateur, prix_achat, prix_vente, notes, date_creation, cree_par)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (dossier_id, type_billet, compagnie, pnr, num_billet, passager,
          ville_depart, ville_arrivee, date_depart, date_retour, classe,
          gds, consolidateur, prix_achat, prix_vente, notes, _maintenant(),
          _id_courant()))
    conn.commit()
    nouvel_id = cur.lastrowid
    conn.close()
    enregistrer_activite("Création", "Réservation",
                         f"{type_billet} {passager}".strip())
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
            (dossier_id, montant, mode, reference, date_paiement, notes, date_creation, cree_par)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (dossier_id, montant, mode, reference, date_paiement, notes,
          _maintenant(), _id_courant()))
    conn.commit()
    nouvel_id = cur.lastrowid
    conn.close()
    enregistrer_activite("Encaissement", "Paiement", f"{montant} ({mode})")
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


# --- RÉORGANISATION 2026 : paiements rattachés à une OPÉRATION ---------------
def migrer_paiements_operations():
    """Met la table `paiements` à niveau pour rattacher un paiement à une
    opération précise (billet/hôtel/assurance/visa) et au client, tout en
    gardant la compatibilité avec l'ancien rattachement au dossier.

    Concrètement : `dossier_id` devient FACULTATIF (peut être vide) et on
    ajoute `client_id`, `operation_type`, `operation_id`. Les 27 paiements
    existants sont RECOPIÉS tels quels (aucune perte), et leur `client_id`
    est retrouvé automatiquement via leur dossier. Idempotent."""
    conn = get_connexion()
    cur = conn.cursor()
    infos = {r["name"]: r for r in
             cur.execute("PRAGMA table_info(paiements)").fetchall()}
    a_colonnes = {"operation_type", "operation_id", "client_id"} <= set(infos)
    dossier_nullable = bool(infos.get("dossier_id")) and infos["dossier_id"]["notnull"] == 0
    if a_colonnes and dossier_nullable:
        conn.close()
        return False  # déjà à niveau

    cur.execute("PRAGMA foreign_keys=OFF")
    cur.execute("DROP TABLE IF EXISTS paiements_new")
    cur.execute("""
        CREATE TABLE paiements_new (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            dossier_id     INTEGER,
            client_id      INTEGER,
            operation_type TEXT,
            operation_id   INTEGER,
            montant        REAL NOT NULL,
            mode           TEXT,
            reference      TEXT,
            date_paiement  TEXT,
            notes          TEXT,
            date_creation  TEXT,
            cree_par       INTEGER,
            FOREIGN KEY (dossier_id) REFERENCES dossiers(id) ON DELETE CASCADE,
            FOREIGN KEY (client_id)  REFERENCES clients(id)  ON DELETE CASCADE
        )
    """)
    communes = [c for c in ("id", "dossier_id", "montant", "mode", "reference",
                            "date_paiement", "notes", "date_creation", "cree_par")
                if c in infos]
    cur.execute(f"INSERT INTO paiements_new ({', '.join(communes)}) "
                f"SELECT {', '.join(communes)} FROM paiements")
    # Retrouve le client via le dossier pour les paiements existants
    cur.execute("""
        UPDATE paiements_new SET client_id =
            (SELECT client_id FROM dossiers WHERE dossiers.id = paiements_new.dossier_id)
        WHERE client_id IS NULL AND dossier_id IS NOT NULL
    """)
    cur.execute("DROP TABLE paiements")
    cur.execute("ALTER TABLE paiements_new RENAME TO paiements")
    conn.commit()
    cur.execute("PRAGMA foreign_keys=ON")
    conn.close()
    return True


def creer_paiement_operation(client_id, operation_type, operation_id, montant,
                             mode="", reference="", date_paiement="", notes=""):
    """Enregistre un paiement rattaché à UNE opération précise (et au client).
    `dossier_id` reste vide (ce n'est plus le pivot dans le nouveau modèle)."""
    if not date_paiement:
        date_paiement = datetime.now().strftime("%Y-%m-%d")
    conn = get_connexion()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO paiements
            (dossier_id, client_id, operation_type, operation_id, montant,
             mode, reference, date_paiement, notes, date_creation, cree_par)
        VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (client_id, operation_type, operation_id, montant, mode, reference,
          date_paiement, notes, _maintenant(), _id_courant()))
    conn.commit()
    nid = cur.lastrowid
    conn.close()
    enregistrer_activite("Encaissement", "Paiement", f"{montant} ({mode})")
    return nid


def lister_tous_paiements(recherche=""):
    """Liste TOUS les paiements (module Paiements transversal), avec le nom du
    client. Filtrable par client / référence / mode."""
    conn = get_connexion()
    base = """
        SELECT p.*, c.nom AS client_nom, c.prenom AS client_prenom
        FROM paiements p
        LEFT JOIN clients c ON c.id = p.client_id
    """
    params = []
    if recherche:
        motif = f"%{recherche}%"
        base += (" WHERE c.nom LIKE ? OR c.prenom LIKE ? OR p.reference LIKE ? "
                 "OR p.mode LIKE ?")
        params += [motif, motif, motif, motif]
    base += " ORDER BY substr(p.date_paiement,1,10) DESC, p.id DESC"
    lignes = conn.execute(base, params).fetchall()
    conn.close()
    return lignes


def supprimer_paiement_operation(paiement_id):
    """Supprime un paiement (module transversal)."""
    conn = get_connexion()
    conn.execute("DELETE FROM paiements WHERE id=?", (paiement_id,))
    conn.commit()
    conn.close()
    enregistrer_activite("Suppression", "Paiement", f"#{paiement_id}")


# ===========================================================================
#  AVOIRS  (cagnotte du client : dépôts petit à petit, puis utilisation)
# ===========================================================================
def creer_depot_avoir(client_id, montant, mode="", date_mouvement="",
                      reference="", notes=""):
    """Enregistre un DÉPÔT : le client verse de l'argent dans sa cagnotte.
    La cagnotte (solde de l'avoir) augmente d'autant."""
    if not date_mouvement:
        date_mouvement = datetime.now().strftime("%Y-%m-%d")
    conn = get_connexion()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO avoirs
            (client_id, type, montant, mode, reference, dossier_id,
             notes, date_mouvement, date_creation, cree_par)
        VALUES (?, 'depot', ?, ?, ?, NULL, ?, ?, ?, ?)
    """, (client_id, montant, mode, reference, notes, date_mouvement,
          _maintenant(), _id_courant()))
    conn.commit()
    nouvel_id = cur.lastrowid
    conn.close()
    enregistrer_activite("Dépôt avoir", "Avoir", f"client #{client_id} : {montant}")
    return nouvel_id


def creer_utilisation_avoir(client_id, montant, dossier_id=None,
                            date_mouvement="", notes=""):
    """UTILISE l'avoir pour payer un dossier (voyage).

    Deux choses se passent :
      1) On retire le montant de la cagnotte (mouvement 'utilisation').
      2) Si un dossier est indiqué, on enregistre aussi un PAIEMENT sur ce
         dossier (mode « Avoir ») pour que le solde du dossier baisse.
    Ainsi l'argent de la cagnotte sert bien à payer le voyage, sans double saisie.
    """
    if not date_mouvement:
        date_mouvement = datetime.now().strftime("%Y-%m-%d")
    reference = ""
    # 1) Si on paie un dossier précis : créer le paiement correspondant
    if dossier_id:
        dossier = get_dossier(dossier_id)
        if dossier is not None:
            reference = dossier["reference"] or ""
        creer_paiement(dossier_id, montant, mode="Avoir",
                       reference="Avoir client",
                       date_paiement=date_mouvement,
                       notes=notes or "Payé avec l'avoir du client")
    # 2) Retirer le montant de la cagnotte
    conn = get_connexion()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO avoirs
            (client_id, type, montant, mode, reference, dossier_id,
             notes, date_mouvement, date_creation, cree_par)
        VALUES (?, 'utilisation', ?, '', ?, ?, ?, ?, ?, ?)
    """, (client_id, montant, reference, dossier_id, notes, date_mouvement,
          _maintenant(), _id_courant()))
    conn.commit()
    nouvel_id = cur.lastrowid
    conn.close()
    enregistrer_activite("Utilisation avoir", "Avoir",
                         f"client #{client_id} : {montant}")
    return nouvel_id


def lister_avoirs(client_id):
    """Liste tous les mouvements (dépôts + utilisations) d'un client,
    du plus récent au plus ancien."""
    conn = get_connexion()
    lignes = conn.execute("""
        SELECT * FROM avoirs WHERE client_id=?
        ORDER BY date_mouvement DESC, id DESC
    """, (client_id,)).fetchall()
    conn.close()
    return lignes


def get_solde_avoir(client_id):
    """Renvoie le solde de la cagnotte d'un client :
       somme des dépôts - somme des utilisations (jamais négatif en pratique)."""
    conn = get_connexion()
    depots = conn.execute(
        "SELECT COALESCE(SUM(montant),0) AS t FROM avoirs "
        "WHERE client_id=? AND type='depot'", (client_id,)).fetchone()["t"]
    utilises = conn.execute(
        "SELECT COALESCE(SUM(montant),0) AS t FROM avoirs "
        "WHERE client_id=? AND type='utilisation'", (client_id,)).fetchone()["t"]
    conn.close()
    return {"depots": depots, "utilises": utilises, "solde": depots - utilises}


def supprimer_avoir(avoir_id):
    """Supprime un mouvement d'avoir.
    NB : si c'était une 'utilisation' liée à un dossier, le paiement
    correspondant reste sur le dossier (à corriger à la main si besoin)."""
    conn = get_connexion()
    conn.execute("DELETE FROM avoirs WHERE id=?", (avoir_id,))
    conn.commit()
    conn.close()
    enregistrer_activite("Suppression", "Avoir", f"mouvement #{avoir_id}")


def lister_soldes_avoirs():
    """Renvoie, pour chaque client ayant au moins un mouvement d'avoir,
    son nom et le solde de sa cagnotte (utile pour une vue d'ensemble)."""
    conn = get_connexion()
    lignes = conn.execute("""
        SELECT c.id AS client_id, c.nom AS nom, c.prenom AS prenom,
               COALESCE(SUM(CASE WHEN a.type='depot' THEN a.montant ELSE 0 END), 0)
             - COALESCE(SUM(CASE WHEN a.type='utilisation' THEN a.montant ELSE 0 END), 0)
               AS solde
        FROM avoirs a
        JOIN clients c ON c.id = a.client_id
        GROUP BY c.id, c.nom, c.prenom
        HAVING solde <> 0
        ORDER BY c.nom, c.prenom
    """).fetchall()
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


# ===========================================================================
#  UTILISATEURS (comptes de connexion)
# ===========================================================================
def compter_utilisateurs():
    """Nombre total de comptes. Sert à savoir si c'est la 1re utilisation."""
    conn = get_connexion()
    n = conn.execute("SELECT COUNT(*) AS n FROM utilisateurs").fetchone()["n"]
    conn.close()
    return n


def creer_utilisateur(nom, prenom="", identifiant="", mot_de_passe="",
                      email="", role="agent", actif=1, doit_changer_mdp=0,
                      permissions=""):
    """Crée un compte utilisateur avec un mot de passe chiffré.
    `role` vaut 'admin' ou 'agent'. Lève une erreur si l'identifiant existe déjà.
    `doit_changer_mdp` = 1 oblige l'utilisateur à changer son mot de passe à
    sa première connexion (utile avec le mot de passe par défaut).
    `permissions` = liste de droits séparés par des virgules (pour un agent)."""
    identifiant = (identifiant or "").strip()
    if not identifiant:
        raise ValueError("L'identifiant de connexion est obligatoire.")
    if not mot_de_passe:
        raise ValueError("Le mot de passe est obligatoire.")
    permissions = _normaliser_permissions(permissions)
    sel, empreinte = auth.chiffrer_mot_de_passe(mot_de_passe)
    conn = get_connexion()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO utilisateurs
                (nom, prenom, identifiant, email, mdp_sel, mdp_hash,
                 role, actif, doit_changer_mdp, permissions, date_creation)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (nom, prenom, identifiant, email, sel, empreinte,
              role, 1 if actif else 0, 1 if doit_changer_mdp else 0,
              permissions, _maintenant()))
        conn.commit()
        nouvel_id = cur.lastrowid
    except sqlite3.IntegrityError:
        conn.close()
        raise ValueError(
            f"L'identifiant « {identifiant} » est déjà utilisé. "
            "Choisissez-en un autre.")
    conn.close()
    enregistrer_activite("Création", "Utilisateur",
                         f"{identifiant} ({role})")
    return nouvel_id


def modifier_utilisateur(utilisateur_id, nom, prenom="", identifiant="",
                         email="", role="agent", actif=1):
    """Modifie les informations d'un compte (SANS toucher au mot de passe)."""
    conn = get_connexion()
    try:
        conn.execute("""
            UPDATE utilisateurs SET
                nom=?, prenom=?, identifiant=?, email=?, role=?, actif=?
            WHERE id=?
        """, (nom, prenom, (identifiant or "").strip(), email, role,
              1 if actif else 0, utilisateur_id))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise ValueError(
            f"L'identifiant « {identifiant} » est déjà utilisé par un autre compte.")
    conn.close()
    enregistrer_activite("Modification", "Utilisateur", identifiant)


def _normaliser_permissions(permissions):
    """Transforme une liste OU une chaîne de permissions en texte propre
    « cle1,cle2,cle3 » (sans espaces ni doublons). Ne garde que les clés
    connues (voir auth.CLES_PERMISSIONS)."""
    if permissions is None:
        return ""
    if isinstance(permissions, (list, tuple, set)):
        elements = list(permissions)
    else:
        elements = str(permissions).split(",")
    valides = set(auth.CLES_PERMISSIONS)
    propres = []
    for e in elements:
        e = str(e).strip()
        if e and e in valides and e not in propres:
            propres.append(e)
    return ",".join(propres)


def definir_permissions(utilisateur_id, permissions):
    """Enregistre les permissions détaillées d'un compte (liste ou texte)."""
    texte = _normaliser_permissions(permissions)
    conn = get_connexion()
    conn.execute("UPDATE utilisateurs SET permissions=? WHERE id=?",
                 (texte, utilisateur_id))
    conn.commit()
    conn.close()
    enregistrer_activite("Modification", "Permissions",
                         f"compte #{utilisateur_id}")


def get_permissions(utilisateur_id):
    """Renvoie la liste des permissions (clés) d'un compte."""
    conn = get_connexion()
    ligne = conn.execute(
        "SELECT permissions FROM utilisateurs WHERE id=?",
        (utilisateur_id,)).fetchone()
    conn.close()
    if ligne is None or not ligne["permissions"]:
        return []
    return [p.strip() for p in ligne["permissions"].split(",") if p.strip()]


def changer_mot_de_passe(utilisateur_id, nouveau_mot_de_passe):
    """Remplace le mot de passe d'un compte par un nouveau (chiffré)."""
    if not nouveau_mot_de_passe:
        raise ValueError("Le nouveau mot de passe ne peut pas être vide.")
    sel, empreinte = auth.chiffrer_mot_de_passe(nouveau_mot_de_passe)
    conn = get_connexion()
    # On efface aussi l'obligation de changement (le mot de passe vient d'être changé)
    conn.execute("UPDATE utilisateurs SET mdp_sel=?, mdp_hash=?, "
                 "doit_changer_mdp=0 WHERE id=?",
                 (sel, empreinte, utilisateur_id))
    conn.commit()
    conn.close()
    enregistrer_activite("Modification", "Mot de passe",
                         f"compte #{utilisateur_id}")


def reinitialiser_mot_de_passe(utilisateur_id):
    """Remet le mot de passe du compte au mot de passe par défaut (Teranga99)
    et force l'utilisateur à en choisir un nouveau à sa prochaine connexion.
    Utile quand un agent a oublié son mot de passe."""
    sel, empreinte = auth.chiffrer_mot_de_passe(auth.MOT_DE_PASSE_DEFAUT)
    conn = get_connexion()
    conn.execute("UPDATE utilisateurs SET mdp_sel=?, mdp_hash=?, "
                 "doit_changer_mdp=1 WHERE id=?",
                 (sel, empreinte, utilisateur_id))
    conn.commit()
    conn.close()
    enregistrer_activite("Réinitialisation", "Mot de passe",
                         f"compte #{utilisateur_id}")


def definir_actif(utilisateur_id, actif):
    """Active (actif=1) ou désactive (actif=0) un compte."""
    conn = get_connexion()
    conn.execute("UPDATE utilisateurs SET actif=? WHERE id=?",
                 (1 if actif else 0, utilisateur_id))
    conn.commit()
    conn.close()
    enregistrer_activite("Modification", "Utilisateur",
                         f"compte #{utilisateur_id} "
                         f"{'activé' if actif else 'désactivé'}")


def supprimer_utilisateur(utilisateur_id):
    conn = get_connexion()
    conn.execute("DELETE FROM utilisateurs WHERE id=?", (utilisateur_id,))
    conn.commit()
    conn.close()
    enregistrer_activite("Suppression", "Utilisateur",
                         f"compte #{utilisateur_id}")


def lister_utilisateurs():
    conn = get_connexion()
    lignes = conn.execute(
        "SELECT * FROM utilisateurs ORDER BY role, nom, prenom").fetchall()
    conn.close()
    return lignes


def get_utilisateur(utilisateur_id):
    conn = get_connexion()
    ligne = conn.execute(
        "SELECT * FROM utilisateurs WHERE id=?", (utilisateur_id,)).fetchone()
    conn.close()
    return ligne


def get_utilisateur_par_identifiant(identifiant):
    conn = get_connexion()
    ligne = conn.execute(
        "SELECT * FROM utilisateurs WHERE identifiant=?",
        ((identifiant or "").strip(),)).fetchone()
    conn.close()
    return ligne


def compter_admins_actifs():
    """Nombre d'administrateurs encore actifs (pour ne pas tous les bloquer)."""
    conn = get_connexion()
    n = conn.execute(
        "SELECT COUNT(*) AS n FROM utilisateurs WHERE role='admin' AND actif=1"
    ).fetchone()["n"]
    conn.close()
    return n


_MAX_TENTATIVES = 5
_DUREE_BLOCAGE_MINUTES = 15


def authentifier(identifiant, mot_de_passe):
    """Vérifie l'identifiant + le mot de passe.

    Bloque le compte pendant quelques minutes après plusieurs mots de passe
    erronés d'affilée (protection contre les essais répétés / "brute force").

    Renvoie un dictionnaire :
      - {"ok": True, "utilisateur": <ligne>} si la connexion réussit
      - {"ok": False, "raison": "<message>"} sinon
    """
    utilisateur = get_utilisateur_par_identifiant(identifiant)
    if utilisateur is None:
        return {"ok": False, "raison": "Identifiant inconnu."}
    if not utilisateur["actif"]:
        return {"ok": False,
                "raison": "Ce compte est désactivé. Contactez l'administrateur."}
    bloque_jusqu_a = utilisateur["bloque_jusqu_a"]
    if bloque_jusqu_a:
        try:
            if datetime.now() < datetime.fromisoformat(bloque_jusqu_a):
                return {"ok": False,
                        "raison": f"Trop de mots de passe erronés. Réessayez "
                                  f"dans {_DUREE_BLOCAGE_MINUTES} minutes."}
        except ValueError:
            pass
    if not auth.verifier_mot_de_passe(mot_de_passe, utilisateur["mdp_sel"],
                                      utilisateur["mdp_hash"]):
        _enregistrer_echec_connexion(utilisateur["id"])
        return {"ok": False, "raison": "Mot de passe incorrect."}
    _reinitialiser_tentatives_connexion(utilisateur["id"])
    return {"ok": True, "utilisateur": utilisateur}


def _enregistrer_echec_connexion(utilisateur_id):
    """Compte un mot de passe erroné ; bloque le compte si trop de ratés."""
    conn = get_connexion()
    ligne = conn.execute(
        "SELECT tentatives_echouees FROM utilisateurs WHERE id=?",
        (utilisateur_id,)).fetchone()
    nb = (ligne["tentatives_echouees"] or 0) + 1
    if nb >= _MAX_TENTATIVES:
        from datetime import timedelta
        jusqu_a = (datetime.now() +
                   timedelta(minutes=_DUREE_BLOCAGE_MINUTES)).isoformat()
        conn.execute(
            "UPDATE utilisateurs SET tentatives_echouees=0, "
            "bloque_jusqu_a=? WHERE id=?", (jusqu_a, utilisateur_id))
    else:
        conn.execute(
            "UPDATE utilisateurs SET tentatives_echouees=? WHERE id=?",
            (nb, utilisateur_id))
    conn.commit()
    conn.close()


def _reinitialiser_tentatives_connexion(utilisateur_id):
    conn = get_connexion()
    conn.execute(
        "UPDATE utilisateurs SET tentatives_echouees=0, bloque_jusqu_a=NULL "
        "WHERE id=?", (utilisateur_id,))
    conn.commit()
    conn.close()


# ===========================================================================
#  JOURNAL DES ACTIVITÉS (traçabilité)
# ===========================================================================
def enregistrer_activite(action, objet, details=""):
    """Ajoute une ligne au journal des activités.
    L'utilisateur enregistré est celui actuellement connecté (voir auth.py).
    On protège l'appel par un try/except pour ne JAMAIS bloquer une opération
    métier si le journal rencontrait un souci."""
    try:
        conn = get_connexion()
        conn.execute("""
            INSERT INTO journal_activites
                (date_heure, utilisateur_id, utilisateur_nom, action, objet, details)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (_maintenant(), auth.id_courant(), auth.nom_courant(),
              action, objet, details))
        conn.commit()
        conn.close()
    except Exception:
        pass


def lister_activites(date_debut=None, date_fin=None, limite=500):
    """Liste les activités, de la plus récente à la plus ancienne.
    On peut filtrer par période (dates 'AAAA-MM-JJ' incluses)."""
    conn = get_connexion()
    base = "SELECT * FROM journal_activites"
    conditions = []
    params = []
    if date_debut:
        conditions.append("substr(date_heure, 1, 10) >= ?")
        params.append(date_debut)
    if date_fin:
        conditions.append("substr(date_heure, 1, 10) <= ?")
        params.append(date_fin)
    if conditions:
        base += " WHERE " + " AND ".join(conditions)
    base += " ORDER BY id DESC LIMIT ?"
    params.append(limite)
    lignes = conn.execute(base, params).fetchall()
    conn.close()
    return lignes


# Permet de tester ce fichier seul : python database.py
if __name__ == "__main__":
    initialiser_base()
    print("Base de données initialisée avec succès :", config.DB_PATH)
