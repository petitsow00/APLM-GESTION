# -*- coding: utf-8 -*-
"""
recherche.py
------------
§18 : RECHERCHE GLOBALE.

Une seule fonction `rechercher(terme)` cherche partout à la fois :
    clients, billets (PNR / n° billet), hôtels (n° réservation),
    assurances (n° police), visas (n° dossier), paiements (référence),
    banque (référence bancaire).

Renvoie un dictionnaire de résultats regroupés par catégorie, prêt à afficher.
Quand un client est trouvé, l'interface pourra ouvrir directement sa fiche.
"""

import database as db
import activites as act


def _like(terme):
    return f"%{(terme or '').strip()}%"


def rechercher(terme):
    terme = (terme or "").strip()
    if not terme:
        return {"clients": [], "billets": [], "hotels": [], "assurances": [],
                "visas": [], "paiements": [], "banque": []}
    motif = _like(terme)
    conn = db.get_connexion()

    def q(sql, params=()):
        try:
            return conn.execute(sql, params).fetchall()
        except Exception:
            return []

    # --- Clients (nom/prénom/tél/email/passeport/code) ---
    clients = db.rechercher_clients_avance(terme)

    # --- Billets : PNR, n° billet, référence, passager ---
    billets = q("""
        SELECT b.*, c.nom AS client_nom, c.prenom AS client_prenom
        FROM billets b JOIN clients c ON c.id = b.client_id
        WHERE b.pnr LIKE ? OR b.num_billet LIKE ? OR b.reference LIKE ?
           OR b.passager LIKE ?
        ORDER BY b.id DESC
    """, (motif, motif, motif, motif))

    # --- Hôtels : n° réservation, nom hôtel, référence ---
    hotels = q("""
        SELECT h.*, c.nom AS client_nom, c.prenom AS client_prenom
        FROM hotels h JOIN clients c ON c.id = h.client_id
        WHERE h.num_reservation LIKE ? OR h.nom_hotel LIKE ? OR h.reference LIKE ?
        ORDER BY h.id DESC
    """, (motif, motif, motif))

    # --- Assurances : n° police, compagnie, référence ---
    assurances = q("""
        SELECT a.*, c.nom AS client_nom, c.prenom AS client_prenom
        FROM assurances a JOIN clients c ON c.id = a.client_id
        WHERE a.num_police LIKE ? OR a.compagnie_assurance LIKE ? OR a.reference LIKE ?
        ORDER BY a.id DESC
    """, (motif, motif, motif))

    # --- Visas : n° dossier, pays, référence ---
    visas = q("""
        SELECT v.*, c.nom AS client_nom, c.prenom AS client_prenom
        FROM visas v JOIN clients c ON c.id = v.client_id
        WHERE v.num_dossier LIKE ? OR v.pays_destination LIKE ? OR v.reference LIKE ?
        ORDER BY v.id DESC
    """, (motif, motif, motif))

    # --- Paiements : référence ---
    paiements = q("""
        SELECT p.*, c.nom AS client_nom, c.prenom AS client_prenom
        FROM paiements p LEFT JOIN clients c ON c.id = p.client_id
        WHERE p.reference LIKE ?
        ORDER BY p.id DESC
    """, (motif,))

    # --- Banque : référence bancaire, pièce, motif ---
    banque = q("""
        SELECT m.*, cb.nom AS compte_nom
        FROM mouvements_bancaires m JOIN comptes_bancaires cb ON cb.id = m.compte_id
        WHERE m.reference_bancaire LIKE ? OR m.piece_reference LIKE ?
           OR m.motif LIKE ?
        ORDER BY m.id DESC
    """, (motif, motif, motif))

    conn.close()
    return {
        "clients": clients, "billets": billets, "hotels": hotels,
        "assurances": assurances, "visas": visas, "paiements": paiements,
        "banque": banque,
    }


def compter(resultats):
    """Nombre total de résultats trouvés (toutes catégories)."""
    return sum(len(v) for v in resultats.values())
