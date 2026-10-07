# -*- coding: utf-8 -*-
"""
comptabilite.py
----------------
MODULE COMPTABILITÉ (SYSCOHADA révisé / OHADA) du logiciel APLM BUZNESS COMPANY.

Idée directrice — AUCUNE DOUBLE SAISIE :
    La comptabilité NE réinvente rien. Elle se construit AUTOMATIQUEMENT à
    partir des données déjà présentes dans le logiciel :
        - les VENTES        = réservations/billets (prix de vente, prix d'achat)
        - les ENCAISSEMENTS = paiements reçus des clients
        - les DÉCAISSEMENTS = dépenses (nouvelle rubrique, voir table `depenses`)

Comment ça marche :
    1) On tient un vrai PLAN COMPTABLE SYSCOHADA (comptes 401, 411, 521, 571,
       601, 701, ...), rangé dans la table `plan_comptable`.
    2) Chaque opération réelle produit une ÉCRITURE en PARTIE DOUBLE
       (Débit = Crédit), rangée dans `ecritures` + `lignes_ecriture`.
    3) Les écritures « automatiques » sont RECONSTRUITES à la demande
       (fonction `regenerer_ecritures_auto`) : on efface les anciennes
       écritures automatiques et on les recrée d'après les données à jour.
       Les écritures saisies à la main (journal OD) sont conservées.
    4) À partir des écritures, on calcule le GRAND LIVRE, la BALANCE,
       le COMPTE DE RÉSULTAT, le BILAN, la CAISSE, la BANQUE, etc.

RÈGLE D'OR : une écriture déséquilibrée (Débit ≠ Crédit) est REFUSÉE.
"""

from datetime import datetime
import database as db


# ===========================================================================
#  PLAN COMPTABLE SYSCOHADA (adapté à une agence de voyage)
# ===========================================================================
# Chaque compte : (numéro, intitulé, classe, nature)
#   classe : 1 à 7 (référentiel SYSCOHADA)
#   nature : 'actif', 'passif', 'charge', 'produit', 'tiers', 'tresorerie'
# NB : les numéros sont ceux du SYSCOHADA révisé (non inventés).
PLAN_COMPTABLE_DEFAUT = [
    # --- Classe 1 : Ressources durables (capitaux propres) ---
    ("101", "Capital social", 1, "passif"),
    ("11",  "Report à nouveau", 1, "passif"),
    ("130", "Résultat de l'exercice", 1, "passif"),

    # --- Classe 2 : Immobilisations (actif) ---
    ("2441", "Matériel de bureau", 2, "actif"),
    ("2444", "Matériel informatique", 2, "actif"),
    ("2844", "Amortissements du matériel", 2, "actif"),

    # --- Classe 4 : Tiers ---
    ("401", "Fournisseurs", 4, "tiers"),
    ("411", "Clients", 4, "tiers"),
    ("421", "Personnel (salaires à payer)", 4, "tiers"),
    ("4431", "État, TVA facturée (collectée)", 4, "tiers"),
    ("4452", "État, TVA récupérable (déductible)", 4, "tiers"),
    ("4441", "État, TVA due", 4, "tiers"),
    ("447", "État, impôts et taxes", 4, "tiers"),

    # --- Classe 5 : Trésorerie (actif) ---
    ("521", "Banque", 5, "tresorerie"),
    ("531", "Chèques postaux", 5, "tresorerie"),
    ("571", "Caisse", 5, "tresorerie"),
    ("585", "Virements internes", 5, "tresorerie"),

    # --- Classe 6 : Charges ---
    ("601", "Achats de billets et de voyages", 6, "charge"),
    ("605", "Autres achats", 6, "charge"),
    ("622", "Locations et charges locatives (loyer)", 6, "charge"),
    ("627", "Publicité et relations publiques", 6, "charge"),
    ("628", "Frais de télécommunications", 6, "charge"),
    ("631", "Frais bancaires", 6, "charge"),
    ("641", "Impôts et taxes", 6, "charge"),
    ("661", "Rémunérations du personnel (salaires)", 6, "charge"),
    ("681", "Dotations aux amortissements", 6, "charge"),
    ("658", "Autres charges diverses", 6, "charge"),

    # --- Classe 7 : Produits ---
    ("701", "Ventes de billets et de voyages", 7, "produit"),
    ("706", "Services vendus (commissions, prestations)", 7, "produit"),
    ("707", "Produits accessoires", 7, "produit"),
    ("771", "Revenus financiers", 7, "produit"),
]

# --- Journaux comptables (au minimum : VT, AC, CA, BQ, OD) ---
JOURNAUX_DEFAUT = [
    ("VT", "Journal des ventes", "vente"),
    ("AC", "Journal des achats", "achat"),
    ("CA", "Journal de caisse", "caisse"),
    ("BQ", "Journal de banque", "banque"),
    ("OD", "Journal des opérations diverses", "od"),
]

# --- Comptes « pivots » utilisés par la génération automatique ---
C_CLIENT      = "411"   # créances clients
C_FOURNISSEUR = "401"   # dettes fournisseurs
C_CAISSE      = "571"   # espèces
C_BANQUE      = "521"   # banque / mobile money / virement / chèque / carte
C_VENTE       = "701"   # ventes de billets et voyages
C_ACHAT       = "601"   # achats de billets et voyages
C_SERVICE     = "706"   # services vendus (frais de service / commission)
C_TVA_COLLECTEE = "4431"  # TVA facturée (collectée) sur les frais de service

# Tables des 4 activités (réorganisation 2026) lues par la génération auto.
_ACTIVITES_TABLES = {
    "billet": "billets", "hotel": "hotels",
    "assurance": "assurances", "visa": "visas",
}

# Modes de paiement considérés comme « espèces » (journal caisse).
# Tout le reste (virement, mobile money, carte, chèque) passe en banque.
MODES_ESPECES = ("espèces", "especes", "espece", "cash", "liquide")


# ===========================================================================
#  INITIALISATION (création des tables + données de départ)
# ===========================================================================
def initialiser_comptabilite():
    """Crée les tables comptables si besoin et charge le plan comptable +
    les journaux par défaut au tout premier lancement. Sans effet si déjà fait."""
    conn = db.get_connexion()
    cur = conn.cursor()

    # --- Exercices comptables ---
    cur.execute("""
        CREATE TABLE IF NOT EXISTS exercices (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            libelle       TEXT,
            date_debut    TEXT,
            date_fin      TEXT,
            cloture       INTEGER NOT NULL DEFAULT 0,
            date_creation TEXT
        )
    """)

    # --- Plan comptable ---
    cur.execute("""
        CREATE TABLE IF NOT EXISTS plan_comptable (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            numero   TEXT NOT NULL UNIQUE,
            intitule TEXT NOT NULL,
            classe   INTEGER,
            nature   TEXT
        )
    """)

    # --- Journaux ---
    cur.execute("""
        CREATE TABLE IF NOT EXISTS journaux (
            code    TEXT PRIMARY KEY,
            libelle TEXT,
            type    TEXT
        )
    """)

    # --- Écritures (l'en-tête) ---
    # source_type : 'vente' / 'achat' / 'encaissement' / 'decaissement' -> auto
    #               'manuel' -> saisie à la main (journal OD), jamais effacée
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ecritures (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            exercice_id   INTEGER,
            date_ecriture TEXT,
            journal_code  TEXT,
            num_piece     TEXT,
            libelle       TEXT,
            reference     TEXT,
            source_type   TEXT,
            source_id     INTEGER,
            validee       INTEGER NOT NULL DEFAULT 1,
            date_creation TEXT,
            cree_par      INTEGER
        )
    """)

    # --- Lignes d'écriture (le détail Débit / Crédit) ---
    cur.execute("""
        CREATE TABLE IF NOT EXISTS lignes_ecriture (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            ecriture_id INTEGER NOT NULL,
            compte      TEXT,
            libelle     TEXT,
            debit       REAL DEFAULT 0,
            credit      REAL DEFAULT 0,
            client_id   INTEGER,
            fournisseur TEXT,
            dossier_id  INTEGER,
            FOREIGN KEY (ecriture_id) REFERENCES ecritures(id) ON DELETE CASCADE
        )
    """)

    # --- Dépenses / Décaissements (nouvelle donnée : sorties d'argent) ---
    cur.execute("""
        CREATE TABLE IF NOT EXISTS depenses (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            date_depense  TEXT,
            beneficiaire  TEXT,
            dossier_id    INTEGER,
            motif         TEXT,
            montant       REAL NOT NULL DEFAULT 0,
            mode          TEXT,
            reference     TEXT,
            compte_charge TEXT,
            libelle       TEXT,
            date_creation TEXT,
            cree_par      INTEGER
        )
    """)

    conn.commit()

    # --- Chargement du plan comptable par défaut (si vide) ---
    n = cur.execute("SELECT COUNT(*) AS n FROM plan_comptable").fetchone()["n"]
    if n == 0:
        cur.executemany(
            "INSERT INTO plan_comptable (numero, intitule, classe, nature) "
            "VALUES (?, ?, ?, ?)", PLAN_COMPTABLE_DEFAUT)

    # --- Chargement des journaux par défaut (si vide) ---
    nj = cur.execute("SELECT COUNT(*) AS n FROM journaux").fetchone()["n"]
    if nj == 0:
        cur.executemany(
            "INSERT INTO journaux (code, libelle, type) VALUES (?, ?, ?)",
            JOURNAUX_DEFAUT)

    conn.commit()
    conn.close()


# ===========================================================================
#  PETITS OUTILS
# ===========================================================================
def _maintenant():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _journal_tresorerie(mode):
    """Renvoie le code du journal (CA=caisse ou BQ=banque) selon le mode."""
    if (mode or "").strip().lower() in MODES_ESPECES:
        return "CA"
    return "BQ"


def _compte_tresorerie(mode):
    """Renvoie le compte de trésorerie (571 caisse ou 521 banque) selon le mode."""
    if (mode or "").strip().lower() in MODES_ESPECES:
        return C_CAISSE
    return C_BANQUE


def _table_existe(cur, nom):
    """Vrai si la table existe (pour ne pas planter si les activités ne sont
    pas encore créées sur une très vieille base)."""
    return cur.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (nom,)).fetchone() is not None


def _fournisseur_operation(activite, o):
    """Nom du fournisseur (pour le crédit 401), selon l'activité.
    Reste INTERNE : n'apparaît jamais sur un reçu client."""
    cles = o.keys()
    if activite == "billet" and "consolidateur" in cles and o["consolidateur"]:
        return o["consolidateur"]
    if activite == "assurance" and "compagnie_assurance" in cles and o["compagnie_assurance"]:
        return o["compagnie_assurance"]
    if activite == "hotel" and "nom_hotel" in cles and o["nom_hotel"]:
        return o["nom_hotel"]
    if activite == "visa" and "ambassade" in cles and o["ambassade"]:
        return o["ambassade"]
    return "Fournisseur"


# ===========================================================================
#  PLAN COMPTABLE (lecture / ajout)
# ===========================================================================
def lister_comptes(classe=None):
    conn = db.get_connexion()
    if classe:
        lignes = conn.execute(
            "SELECT * FROM plan_comptable WHERE classe=? ORDER BY numero",
            (classe,)).fetchall()
    else:
        lignes = conn.execute(
            "SELECT * FROM plan_comptable ORDER BY numero").fetchall()
    conn.close()
    return lignes


def get_compte(numero):
    conn = db.get_connexion()
    ligne = conn.execute(
        "SELECT * FROM plan_comptable WHERE numero=?", (numero,)).fetchone()
    conn.close()
    return ligne


def intitule_compte(numero):
    c = get_compte(numero)
    return c["intitule"] if c else ""


def ajouter_compte(numero, intitule, classe, nature="autre"):
    conn = db.get_connexion()
    try:
        conn.execute(
            "INSERT INTO plan_comptable (numero, intitule, classe, nature) "
            "VALUES (?, ?, ?, ?)", (numero.strip(), intitule, classe, nature))
        conn.commit()
    except Exception:
        conn.close()
        raise ValueError(f"Le compte {numero} existe déjà.")
    conn.close()
    db.enregistrer_activite("Création", "Compte", f"{numero} {intitule}")


def lister_journaux():
    conn = db.get_connexion()
    lignes = conn.execute("SELECT * FROM journaux ORDER BY code").fetchall()
    conn.close()
    return lignes


def libelle_journal(code):
    conn = db.get_connexion()
    ligne = conn.execute(
        "SELECT libelle FROM journaux WHERE code=?", (code,)).fetchone()
    conn.close()
    return ligne["libelle"] if ligne else code


# ===========================================================================
#  EXERCICES COMPTABLES
# ===========================================================================
def creer_exercice(libelle, date_debut, date_fin):
    conn = db.get_connexion()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO exercices (libelle, date_debut, date_fin, cloture, date_creation)
        VALUES (?, ?, ?, 0, ?)
    """, (libelle, date_debut, date_fin, _maintenant()))
    conn.commit()
    nid = cur.lastrowid
    conn.close()
    db.enregistrer_activite("Création", "Exercice", libelle)
    return nid


def lister_exercices():
    conn = db.get_connexion()
    lignes = conn.execute(
        "SELECT * FROM exercices ORDER BY date_debut DESC, id DESC").fetchall()
    conn.close()
    return lignes


def cloturer_exercice(exercice_id, cloture=1):
    conn = db.get_connexion()
    conn.execute("UPDATE exercices SET cloture=? WHERE id=?",
                 (1 if cloture else 0, exercice_id))
    conn.commit()
    conn.close()
    db.enregistrer_activite(
        "Clôture" if cloture else "Réouverture", "Exercice", f"#{exercice_id}")


def exercice_courant():
    """Renvoie l'exercice NON clôturé le plus récent, ou None."""
    conn = db.get_connexion()
    ligne = conn.execute(
        "SELECT * FROM exercices WHERE cloture=0 "
        "ORDER BY date_debut DESC, id DESC LIMIT 1").fetchone()
    conn.close()
    return ligne


def _exercice_de_date(date_op):
    """Trouve l'exercice qui contient la date donnée (ou None)."""
    conn = db.get_connexion()
    ligne = conn.execute("""
        SELECT * FROM exercices
        WHERE (date_debut IS NULL OR date_debut = '' OR date_debut <= ?)
          AND (date_fin   IS NULL OR date_fin   = '' OR date_fin   >= ?)
        ORDER BY id DESC LIMIT 1
    """, (date_op, date_op)).fetchone()
    conn.close()
    return ligne["id"] if ligne else None


# ===========================================================================
#  DÉPENSES / DÉCAISSEMENTS
# ===========================================================================
def creer_depense(date_depense, beneficiaire="", montant=0, mode="Espèces",
                  motif="", reference="", compte_charge="605", libelle="",
                  dossier_id=None):
    if not date_depense:
        date_depense = datetime.now().strftime("%Y-%m-%d")
    conn = db.get_connexion()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO depenses
            (date_depense, beneficiaire, dossier_id, motif, montant, mode,
             reference, compte_charge, libelle, date_creation, cree_par)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (date_depense, beneficiaire, dossier_id, motif, montant, mode,
          reference, compte_charge, libelle, _maintenant(), db.auth.id_courant()))
    conn.commit()
    nid = cur.lastrowid
    conn.close()
    db.enregistrer_activite("Décaissement", "Dépense",
                            f"{montant} {beneficiaire}".strip())
    return nid


def supprimer_depense(depense_id):
    conn = db.get_connexion()
    conn.execute("DELETE FROM depenses WHERE id=?", (depense_id,))
    conn.commit()
    conn.close()
    db.enregistrer_activite("Suppression", "Dépense", f"#{depense_id}")


def lister_depenses(date_debut=None, date_fin=None):
    conn = db.get_connexion()
    base = "SELECT * FROM depenses"
    cond, params = [], []
    if date_debut:
        cond.append("substr(date_depense,1,10) >= ?"); params.append(date_debut)
    if date_fin:
        cond.append("substr(date_depense,1,10) <= ?"); params.append(date_fin)
    if cond:
        base += " WHERE " + " AND ".join(cond)
    base += " ORDER BY date_depense, id"
    lignes = conn.execute(base, params).fetchall()
    conn.close()
    return lignes


# ===========================================================================
#  ÉCRITURES COMPTABLES (partie double)
# ===========================================================================
def creer_ecriture(date_ecriture, journal_code, libelle, lignes,
                   reference="", num_piece="", source_type="manuel",
                   source_id=None, exercice_id=None):
    """Crée une écriture équilibrée.

    `lignes` : liste de dictionnaires, ex :
        {"compte": "411", "libelle": "...", "debit": 1000, "credit": 0,
         "client_id": 3, "fournisseur": "", "dossier_id": 7}

    RÈGLE : total débit == total crédit, sinon on lève une erreur.
    """
    total_debit = round(sum(float(l.get("debit") or 0) for l in lignes), 2)
    total_credit = round(sum(float(l.get("credit") or 0) for l in lignes), 2)
    if total_debit != total_credit:
        raise ValueError(
            f"Écriture déséquilibrée : total débit ({total_debit}) "
            f"≠ total crédit ({total_credit}). L'écriture est refusée.")
    if total_debit == 0:
        raise ValueError("Écriture vide : aucun montant saisi.")

    if exercice_id is None:
        exercice_id = _exercice_de_date((date_ecriture or "")[:10])

    conn = db.get_connexion()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO ecritures
            (exercice_id, date_ecriture, journal_code, num_piece, libelle,
             reference, source_type, source_id, validee, date_creation, cree_par)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
    """, (exercice_id, date_ecriture, journal_code, num_piece, libelle,
          reference, source_type, source_id, _maintenant(), db.auth.id_courant()))
    ecriture_id = cur.lastrowid
    for l in lignes:
        cur.execute("""
            INSERT INTO lignes_ecriture
                (ecriture_id, compte, libelle, debit, credit,
                 client_id, fournisseur, dossier_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (ecriture_id, l.get("compte"), l.get("libelle", libelle),
              float(l.get("debit") or 0), float(l.get("credit") or 0),
              l.get("client_id"), l.get("fournisseur"), l.get("dossier_id")))
    conn.commit()
    conn.close()
    if source_type == "manuel":
        db.enregistrer_activite("Écriture", "Comptabilité",
                                f"{journal_code} {libelle}")
    return ecriture_id


def supprimer_ecriture(ecriture_id):
    conn = db.get_connexion()
    conn.execute("DELETE FROM ecritures WHERE id=?", (ecriture_id,))
    conn.commit()
    conn.close()


def lister_ecritures(journal_code=None, date_debut=None, date_fin=None):
    """Liste les écritures (en-têtes) avec leur total, filtrables."""
    conn = db.get_connexion()
    base = """
        SELECT e.*,
               (SELECT COALESCE(SUM(debit),0) FROM lignes_ecriture
                WHERE ecriture_id = e.id) AS total
        FROM ecritures e
    """
    cond, params = [], []
    if journal_code:
        cond.append("e.journal_code = ?"); params.append(journal_code)
    if date_debut:
        cond.append("substr(e.date_ecriture,1,10) >= ?"); params.append(date_debut)
    if date_fin:
        cond.append("substr(e.date_ecriture,1,10) <= ?"); params.append(date_fin)
    if cond:
        base += " WHERE " + " AND ".join(cond)
    base += " ORDER BY substr(e.date_ecriture,1,10), e.id"
    lignes = conn.execute(base, params).fetchall()
    conn.close()
    return lignes


def lignes_de_ecriture(ecriture_id):
    conn = db.get_connexion()
    lignes = conn.execute(
        "SELECT * FROM lignes_ecriture WHERE ecriture_id=? ORDER BY id",
        (ecriture_id,)).fetchall()
    conn.close()
    return lignes


def _prochain_num_piece(cur, journal_code, annee):
    """Fabrique un numéro de pièce unique du type VT-2026-0001."""
    prefixe = f"{journal_code}-{annee}-"
    n = cur.execute(
        "SELECT COUNT(*) AS n FROM ecritures WHERE num_piece LIKE ?",
        (prefixe + "%",)).fetchone()["n"]
    return f"{prefixe}{n + 1:04d}"


# ===========================================================================
#  GÉNÉRATION AUTOMATIQUE DES ÉCRITURES (depuis les données existantes)
# ===========================================================================
def regenerer_ecritures_auto():
    """Reconstruit TOUTES les écritures automatiques à partir des données
    réelles (ventes, encaissements, décaissements). Les écritures manuelles
    (journal OD) ne sont PAS touchées.

    Cette approche garantit qu'il n'y a JAMAIS de double saisie : la
    comptabilité reflète toujours exactement les opérations enregistrées.
    """
    conn = db.get_connexion()
    cur = conn.cursor()

    # 1) On efface les anciennes écritures AUTOMATIQUES uniquement
    cur.execute("""
        DELETE FROM ecritures
        WHERE source_type IN ('vente', 'achat', 'encaissement', 'decaissement')
    """)
    conn.commit()

    nb = 0

    # 2) VENTES + ACHATS (à partir des 4 ACTIVITÉS séparées) --------------
    # NB : on lit désormais billets/hotels/assurances/visas (et PLUS la table
    #      reservations, gardée en archive) -> aucune vente comptée deux fois.
    import activites as act
    for activite, table in _ACTIVITES_TABLES.items():
        if not _table_existe(cur, table):
            continue
        for o in cur.execute(f"SELECT * FROM {table}").fetchall():
            date_op = (o["date_creation"] or "")[:10]
            annee = date_op[:4] or datetime.now().strftime("%Y")
            libelle_base = f'{act.ACTIVITES[activite][1]} {o["passager"] or ""}'.strip()
            ref = o["reference"] or ""
            client_id = o["client_id"]

            calc = act.calc_totaux(o["prix_client"], o["frais_service"],
                                   o["autres_frais"], o["reduction"],
                                   o["prix_fournisseur"], o["tva_taux"])
            total_client = calc["total_client"]
            tva = calc["montant_tva"]              # TVA sur les frais de service
            frais = float(o["frais_service"] or 0)
            service_net = round(frais - tva, 2)    # part service hors TVA
            vente_princ = round(total_client - frais, 2)  # part billet/voyage

            # --- VENTE : Débit 411 Client / Crédit 701 (+ 706 service + 4431 TVA) ---
            if total_client != 0:
                lignes = [{"compte": C_CLIENT, "debit": total_client, "credit": 0,
                           "client_id": client_id}]
                if vente_princ != 0:
                    lignes.append({"compte": C_VENTE, "debit": 0, "credit": vente_princ})
                if service_net != 0:
                    lignes.append({"compte": C_SERVICE, "debit": 0, "credit": service_net})
                if tva != 0:
                    lignes.append({"compte": C_TVA_COLLECTEE, "debit": 0, "credit": tva})
                num = _prochain_num_piece(cur, "VT", annee)
                _ecrire_auto(cur, date_op, "VT", num,
                             f"Vente {libelle_base} ({ref})", ref, "vente",
                             o["id"], lignes)
                nb += 1

            # --- ACHAT : Débit 601 Achats / Crédit 401 Fournisseur ---
            if (o["prix_fournisseur"] or 0) > 0:
                fournisseur = _fournisseur_operation(activite, o)
                num = _prochain_num_piece(cur, "AC", annee)
                _ecrire_auto(cur, date_op, "AC", num,
                             f"Achat {libelle_base} ({ref})", ref, "achat",
                             o["id"], [
                                 {"compte": C_ACHAT, "debit": o["prix_fournisseur"],
                                  "credit": 0},
                                 {"compte": C_FOURNISSEUR, "debit": 0,
                                  "credit": o["prix_fournisseur"],
                                  "fournisseur": fournisseur},
                             ])
                nb += 1

    # 3) ENCAISSEMENTS (paiements clients) --------------------------------
    # LEFT JOIN : on prend AUSSI les paiements rattachés à une opération
    # (dossier_id vide). Le client vient de paiements.client_id.
    paiements = cur.execute("""
        SELECT p.*, d.reference AS dossier_ref
        FROM paiements p
        LEFT JOIN dossiers d ON d.id = p.dossier_id
    """).fetchall()
    for p in paiements:
        if (p["montant"] or 0) == 0:
            continue
        date_op = (p["date_paiement"] or p["date_creation"] or "")[:10]
        annee = date_op[:4] or datetime.now().strftime("%Y")
        jrn = _journal_tresorerie(p["mode"])
        compte_treso = _compte_tresorerie(p["mode"])
        ref = p["dossier_ref"] or ""
        client_id = p["client_id"] if "client_id" in p.keys() else None
        num = _prochain_num_piece(cur, jrn, annee)
        # Débit trésorerie (571/521) / Crédit 411 Client
        _ecrire_auto(cur, date_op, jrn, num,
                     f"Encaissement {ref} ({p['mode'] or ''})".strip(),
                     ref, "encaissement", p["id"], [
                         {"compte": compte_treso, "debit": p["montant"], "credit": 0,
                          "dossier_id": p["dossier_id"]},
                         {"compte": C_CLIENT, "debit": 0, "credit": p["montant"],
                          "client_id": client_id, "dossier_id": p["dossier_id"]},
                     ])
        nb += 1

    # 4) DÉCAISSEMENTS (dépenses) -----------------------------------------
    depenses = cur.execute("SELECT * FROM depenses").fetchall()
    for d in depenses:
        if (d["montant"] or 0) == 0:
            continue
        date_op = (d["date_depense"] or "")[:10]
        annee = date_op[:4] or datetime.now().strftime("%Y")
        jrn = _journal_tresorerie(d["mode"])
        compte_treso = _compte_tresorerie(d["mode"])
        compte_charge = d["compte_charge"] or "605"
        num = _prochain_num_piece(cur, jrn, annee)
        # Débit compte de charge (6xx / ou 401) / Crédit trésorerie (571/521)
        _ecrire_auto(cur, date_op, jrn, num,
                     f"Dépense {d['motif'] or ''} {d['beneficiaire'] or ''}".strip(),
                     d["reference"] or "", "decaissement", d["id"], [
                         {"compte": compte_charge, "debit": d["montant"], "credit": 0,
                          "fournisseur": d["beneficiaire"], "dossier_id": d["dossier_id"]},
                         {"compte": compte_treso, "debit": 0, "credit": d["montant"]},
                     ])
        nb += 1

    conn.commit()
    conn.close()
    return nb


def _ecrire_auto(cur, date_op, journal_code, num_piece, libelle, reference,
                 source_type, source_id, lignes):
    """Insère une écriture automatique (déjà équilibrée par construction)."""
    exercice_id = None  # calculé plus tard par les rapports si besoin
    cur.execute("""
        INSERT INTO ecritures
            (exercice_id, date_ecriture, journal_code, num_piece, libelle,
             reference, source_type, source_id, validee, date_creation, cree_par)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
    """, (exercice_id, date_op, journal_code, num_piece, libelle, reference,
          source_type, source_id, _maintenant(), db.auth.id_courant()))
    eid = cur.lastrowid
    for l in lignes:
        cur.execute("""
            INSERT INTO lignes_ecriture
                (ecriture_id, compte, libelle, debit, credit,
                 client_id, fournisseur, dossier_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (eid, l["compte"], l.get("libelle", libelle),
              float(l.get("debit") or 0), float(l.get("credit") or 0),
              l.get("client_id"), l.get("fournisseur"), l.get("dossier_id")))


# ===========================================================================
#  GRAND LIVRE
# ===========================================================================
def grand_livre(compte=None, date_debut=None, date_fin=None, journal_code=None):
    """Renvoie les mouvements d'un (ou tous les) compte(s), avec solde progressif.

    Renvoie une liste de dictionnaires triés par compte puis par date :
        {compte, intitule, date, num_piece, journal, libelle, debit, credit, solde}
    """
    conn = db.get_connexion()
    base = """
        SELECT l.compte AS compte, e.date_ecriture AS date, e.num_piece AS num_piece,
               e.journal_code AS journal, l.libelle AS libelle,
               l.debit AS debit, l.credit AS credit
        FROM lignes_ecriture l
        JOIN ecritures e ON e.id = l.ecriture_id
    """
    cond, params = [], []
    if compte:
        cond.append("l.compte = ?"); params.append(compte)
    if journal_code:
        cond.append("e.journal_code = ?"); params.append(journal_code)
    if date_debut:
        cond.append("substr(e.date_ecriture,1,10) >= ?"); params.append(date_debut)
    if date_fin:
        cond.append("substr(e.date_ecriture,1,10) <= ?"); params.append(date_fin)
    if cond:
        base += " WHERE " + " AND ".join(cond)
    base += " ORDER BY l.compte, substr(e.date_ecriture,1,10), e.id"
    lignes = conn.execute(base, params).fetchall()
    conn.close()

    resultat = []
    solde = 0
    compte_courant = None
    for l in lignes:
        if l["compte"] != compte_courant:
            compte_courant = l["compte"]
            solde = 0
        solde += (l["debit"] or 0) - (l["credit"] or 0)
        resultat.append({
            "compte": l["compte"],
            "intitule": intitule_compte(l["compte"]),
            "date": l["date"] or "",
            "num_piece": l["num_piece"] or "",
            "journal": l["journal"] or "",
            "libelle": l["libelle"] or "",
            "debit": l["debit"] or 0,
            "credit": l["credit"] or 0,
            "solde": solde,
        })
    return resultat


# ===========================================================================
#  BALANCE
# ===========================================================================
def balance(date_debut=None, date_fin=None):
    """Renvoie la balance comptable : par compte, total débit / crédit et solde.

    Liste de dictionnaires :
        {compte, intitule, classe, total_debit, total_credit,
         solde_debiteur, solde_crediteur}
    """
    conn = db.get_connexion()
    base = """
        SELECT l.compte AS compte,
               COALESCE(SUM(l.debit),0)  AS td,
               COALESCE(SUM(l.credit),0) AS tc
        FROM lignes_ecriture l
        JOIN ecritures e ON e.id = l.ecriture_id
    """
    cond, params = [], []
    if date_debut:
        cond.append("substr(e.date_ecriture,1,10) >= ?"); params.append(date_debut)
    if date_fin:
        cond.append("substr(e.date_ecriture,1,10) <= ?"); params.append(date_fin)
    if cond:
        base += " WHERE " + " AND ".join(cond)
    base += " GROUP BY l.compte ORDER BY l.compte"
    lignes = conn.execute(base, params).fetchall()
    conn.close()

    resultat = []
    for l in lignes:
        c = get_compte(l["compte"])
        solde = (l["td"] or 0) - (l["tc"] or 0)
        resultat.append({
            "compte": l["compte"],
            "intitule": c["intitule"] if c else "",
            "classe": c["classe"] if c else None,
            "total_debit": l["td"] or 0,
            "total_credit": l["tc"] or 0,
            "solde_debiteur": solde if solde > 0 else 0,
            "solde_crediteur": -solde if solde < 0 else 0,
        })
    return resultat


# ===========================================================================
#  ÉTAT DE CAISSE / BANQUE (trésorerie)
# ===========================================================================
def etat_tresorerie(compte, date_debut=None, date_fin=None, solde_initial=0):
    """État d'un compte de trésorerie (571 caisse ou 521 banque) :
       solde initial + encaissements (débits) - décaissements (crédits)."""
    conn = db.get_connexion()
    base = """
        SELECT COALESCE(SUM(l.debit),0) AS entrees,
               COALESCE(SUM(l.credit),0) AS sorties
        FROM lignes_ecriture l
        JOIN ecritures e ON e.id = l.ecriture_id
        WHERE l.compte = ?
    """
    params = [compte]
    if date_debut:
        base += " AND substr(e.date_ecriture,1,10) >= ?"; params.append(date_debut)
    if date_fin:
        base += " AND substr(e.date_ecriture,1,10) <= ?"; params.append(date_fin)
    r = conn.execute(base, params).fetchone()
    conn.close()
    entrees = r["entrees"] or 0
    sorties = r["sorties"] or 0
    return {
        "solde_initial": solde_initial,
        "entrees": entrees,
        "sorties": sorties,
        "solde_final": solde_initial + entrees - sorties,
    }


# ===========================================================================
#  COMPTE DE RÉSULTAT & BILAN (simplifiés SYSCOHADA)
# ===========================================================================
def compte_de_resultat(date_debut=None, date_fin=None):
    """Produits (classe 7) - Charges (classe 6) = Résultat.
    Renvoie {charges: [...], produits: [...], total_charges, total_produits,
             resultat}."""
    lignes = balance(date_debut, date_fin)
    charges, produits = [], []
    total_charges = total_produits = 0
    for b in lignes:
        if b["classe"] == 6:
            montant = b["total_debit"] - b["total_credit"]
            charges.append({"compte": b["compte"], "intitule": b["intitule"],
                            "montant": montant})
            total_charges += montant
        elif b["classe"] == 7:
            montant = b["total_credit"] - b["total_debit"]
            produits.append({"compte": b["compte"], "intitule": b["intitule"],
                             "montant": montant})
            total_produits += montant
    return {
        "charges": charges,
        "produits": produits,
        "total_charges": total_charges,
        "total_produits": total_produits,
        "resultat": total_produits - total_charges,
    }


def bilan(date_debut=None, date_fin=None):
    """Bilan simplifié : Actif (classes 2,3,5 + comptes de tiers débiteurs)
    et Passif (classe 1 + tiers créditeurs + résultat).
    Renvoie {actif: [...], passif: [...], total_actif, total_passif}."""
    lignes = balance(date_debut, date_fin)
    actif, passif = [], []
    total_actif = total_passif = 0
    for b in lignes:
        classe = b["classe"]
        solde_d = b["solde_debiteur"]
        solde_c = b["solde_crediteur"]
        if classe in (2, 3, 5):
            if solde_d or solde_c:
                montant = solde_d - solde_c
                actif.append({"compte": b["compte"], "intitule": b["intitule"],
                              "montant": montant})
                total_actif += montant
        elif classe == 1:
            montant = solde_c - solde_d
            passif.append({"compte": b["compte"], "intitule": b["intitule"],
                           "montant": montant})
            total_passif += montant
        elif classe == 4:
            # Tiers : débiteur -> actif (créances) ; créditeur -> passif (dettes)
            if solde_d > 0:
                actif.append({"compte": b["compte"], "intitule": b["intitule"],
                              "montant": solde_d})
                total_actif += solde_d
            elif solde_c > 0:
                passif.append({"compte": b["compte"], "intitule": b["intitule"],
                               "montant": solde_c})
                total_passif += solde_c
        # classes 6 et 7 -> vont dans le résultat (ci-dessous)

    # Résultat de l'exercice -> au passif (bénéfice) ou en négatif (perte)
    res = compte_de_resultat(date_debut, date_fin)
    passif.append({"compte": "130", "intitule": "Résultat de l'exercice",
                   "montant": res["resultat"]})
    total_passif += res["resultat"]

    return {
        "actif": actif,
        "passif": passif,
        "total_actif": total_actif,
        "total_passif": total_passif,
        "resultat": res["resultat"],
    }


# ===========================================================================
#  TVA (informative — aucun taux appliqué automatiquement)
# ===========================================================================
def etat_tva(date_debut=None, date_fin=None):
    """État de TVA calculé à partir des écritures sur les comptes de TVA.
    Tant qu'aucune écriture de TVA n'est saisie, tout est à 0 (normal :
    on n'invente aucun taux)."""
    lignes = balance(date_debut, date_fin)
    collectee = deductible = 0
    for b in lignes:
        if b["compte"] == "4431":      # TVA facturée (collectée) -> créditeur
            collectee = b["total_credit"] - b["total_debit"]
        elif b["compte"] == "4452":    # TVA récupérable (déductible) -> débiteur
            deductible = b["total_debit"] - b["total_credit"]
    a_payer = collectee - deductible
    return {
        "tva_collectee": collectee,
        "tva_deductible": deductible,
        "tva_a_payer": a_payer if a_payer > 0 else 0,
        "credit_tva": -a_payer if a_payer < 0 else 0,
    }


# ===========================================================================
#  TABLEAU DE BORD COMPTABLE
# ===========================================================================
def tableau_de_bord(date_debut=None, date_fin=None):
    """Chiffres clés comptables pour une période."""
    res = compte_de_resultat(date_debut, date_fin)
    caisse = etat_tresorerie(C_CAISSE, date_debut, date_fin)
    banque = etat_tresorerie(C_BANQUE, date_debut, date_fin)

    # Créances clients (411 débiteur) et dettes fournisseurs (401 créditeur)
    creances = dettes = 0
    for b in balance(date_debut, date_fin):
        if b["compte"] == C_CLIENT:
            creances = b["solde_debiteur"]
        elif b["compte"] == C_FOURNISSEUR:
            dettes = b["solde_crediteur"]

    # Chiffre d'affaires = ventes (701) + services (706)
    ca = 0
    for p in res["produits"]:
        if p["compte"] in ("701", "706", "707"):
            ca += p["montant"]

    return {
        "chiffre_affaires": ca,
        "total_produits": res["total_produits"],
        "total_charges": res["total_charges"],
        "resultat": res["resultat"],
        "solde_caisse": caisse["solde_final"],
        "solde_banque": banque["solde_final"],
        "creances_clients": creances,
        "dettes_fournisseurs": dettes,
    }
