# -*- coding: utf-8 -*-
"""
rapports.py
-----------
ÉTAPE 14 (Rapports) + ÉTAPE 15 (Tableau de bord).

Ces chiffres se calculent DIRECTEMENT à partir des vraies données (opérations,
paiements, banque). Ils fonctionnent indépendamment de l'écran comptable.

RÈGLE ANTI-DOUBLE-COMPTAGE (§13) :
    - Chiffre d'affaires  = somme des TOTAUX des opérations (billets/hôtels/...)
    - Encaissements       = somme des PAIEMENTS reçus  (ce n'est PAS du CA en plus)
    - Mouvements bancaires = trésorerie  (ce n'est NI du CA NI un encaissement en plus)
"""

from datetime import datetime, timedelta
import database as db
import activites as act
import banque as bq


# Statuts d'un dossier visa considérés « en cours » (ni clos, ni refusé/annulé)
_VISA_TERMINE = {"visa accordé", "visa refusé", "dossier annulé", "annulé",
                 "accordé", "refusé", "terminé"}


def _dans_periode(date_op, date_debut, date_fin):
    if date_debut and date_op < date_debut:
        return False
    if date_fin and date_op > date_fin:
        return False
    return True


def _iter_operations(date_debut=None, date_fin=None, activite=None, statut=None):
    """Parcourt les opérations (avec totaux calculés), filtrées par période /
    activité / statut. Rend des tuples (activite, ligne, totaux)."""
    activites = [activite] if activite else list(act.ACTIVITES)
    for a in activites:
        for o in act.lister_operations(a):
            date_op = (o["date_creation"] or "")[:10]
            if not _dans_periode(date_op, date_debut, date_fin):
                continue
            if statut and (o["statut"] or "") != statut:
                continue
            paye = act.get_total_paye_operation(a, o["id"])
            t = act.calc_totaux(o["prix_client"], o["frais_service"],
                                o["autres_frais"], o["reduction"],
                                o["prix_fournisseur"], o["tva_taux"], paye)
            yield a, o, t


def _encaissements_periode(date_debut=None, date_fin=None):
    conn = db.get_connexion()
    base = "SELECT COALESCE(SUM(montant),0) AS t FROM paiements"
    cond, params = [], []
    if date_debut:
        cond.append("substr(date_paiement,1,10) >= ?"); params.append(date_debut)
    if date_fin:
        cond.append("substr(date_paiement,1,10) <= ?"); params.append(date_fin)
    if cond:
        base += " WHERE " + " AND ".join(cond)
    v = conn.execute(base, params).fetchone()["t"] or 0
    conn.close()
    return v


def _mouvements_banque_periode(date_debut=None, date_fin=None):
    versements = retraits = 0
    for m in bq.lister_mouvements(date_debut=date_debut, date_fin=date_fin):
        if m["type"] == "versement":
            versements += m["montant"] or 0
        else:
            retraits += m["montant"] or 0
    solde = sum((s["solde_actuel"] or 0) for s in bq.soldes_tous_comptes())
    return versements, retraits, solde


def rapport(date_debut=None, date_fin=None, activite=None, statut=None):
    """Rapport d'une période (jour / semaine / mois / personnalisé)."""
    compteur = {a: 0 for a in act.ACTIVITES}
    ca = couts = marge = reste = tva = 0
    for a, o, t in _iter_operations(date_debut, date_fin, activite, statut):
        compteur[a] += 1
        ca += t["total_client"]
        couts += float(o["prix_fournisseur"] or 0)
        marge += t["marge"]
        reste += t["reste_a_payer"]
        tva += t["montant_tva"]

    encaisse = _encaissements_periode(date_debut, date_fin)
    versements, retraits, solde_banque = _mouvements_banque_periode(date_debut, date_fin)

    return {
        "date_debut": date_debut, "date_fin": date_fin,
        "nb_billets": compteur["billet"], "nb_hotels": compteur["hotel"],
        "nb_assurances": compteur["assurance"], "nb_visas": compteur["visa"],
        "nb_operations": sum(compteur.values()),
        "chiffre_affaires": round(ca, 2),
        "couts_fournisseurs": round(couts, 2),
        "marge": round(marge, 2),
        "tva": round(tva, 2),
        "encaissements": round(encaisse, 2),
        "creances": round(reste, 2),          # reste à payer sur les opérations
        "versements_bancaires": round(versements, 2),
        "retraits_bancaires": round(retraits, 2),
        "solde_bancaire": round(solde_banque, 2),
    }


def _bornes():
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    lundi = (now - timedelta(days=now.weekday())).strftime("%Y-%m-%d")
    prem_mois = now.strftime("%Y-%m-01")
    return today, lundi, prem_mois


def creances_globales():
    """Total du reste à payer sur TOUTES les opérations (toutes périodes)."""
    total = 0
    for a, o, t in _iter_operations():
        total += t["reste_a_payer"]
    return round(total, 2)


def paiements_en_attente():
    """Nombre d'opérations avec un reste à payer > 0."""
    n = 0
    for a, o, t in _iter_operations():
        if t["reste_a_payer"] > 0:
            n += 1
    return n


def dossiers_visa_en_cours():
    """Nombre de dossiers visa non terminés (ni accordé, ni refusé, ni annulé)."""
    n = 0
    for v in act.lister_operations("visa"):
        if (v["statut"] or "").strip().lower() not in _VISA_TERMINE:
            n += 1
    return n


def tableau_de_bord():
    """ÉTAPE 15 : chiffres clés RÉELS pour le tableau de bord."""
    today, lundi, prem_mois = _bornes()
    r_jour = rapport(today, today)
    r_sem = rapport(lundi, today)
    r_mois = rapport(prem_mois, today)
    _, _, solde_banque = _mouvements_banque_periode()

    # Comptes globaux (toutes périodes)
    nb = {a: len(act.lister_operations(a)) for a in act.ACTIVITES}

    return {
        "ca_jour": r_jour["chiffre_affaires"],
        "ca_semaine": r_sem["chiffre_affaires"],
        "ca_mois": r_mois["chiffre_affaires"],
        "encaissements_mois": r_mois["encaissements"],
        "marge_mois": r_mois["marge"],
        "creances": creances_globales(),
        "nb_billets": nb["billet"], "nb_hotels": nb["hotel"],
        "nb_assurances": nb["assurance"], "nb_visas": nb["visa"],
        "paiements_en_attente": paiements_en_attente(),
        "dossiers_visa_en_cours": dossiers_visa_en_cours(),
        "versements_mois": r_mois["versements_bancaires"],
        "retraits_mois": r_mois["retraits_bancaires"],
        "solde_bancaire": solde_banque,
    }
