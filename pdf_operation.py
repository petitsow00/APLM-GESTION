# -*- coding: utf-8 -*-
"""
pdf_operation.py
----------------
Génère un reçu PDF pour UNE opération séparée (billet / hôtel / assurance /
visa), dans le même style que le reçu existant.

⚠️ RÈGLE ABSOLUE (identique au reçu classique) :
    On n'affiche JAMAIS les infos internes : consolidateur, GDS, prix
    fournisseur (coût). Ces champs ne sont même pas lus ici.
"""

import os
from datetime import datetime

import config
import settings
import database as db
import activites as act
from utils import ouvrir_fichier
from pdf_receipt import RecuPDF, formater_montant, _titre_section, BLEU, GRIS


def _designation(activite, o):
    """Description LISIBLE de l'opération, sans aucune info interne."""
    parts = []
    if activite == "billet":
        for cle in ("type_billet", "compagnie"):
            if o[cle]:
                parts.append(o[cle])
        if o["ville_depart"] and o["ville_arrivee"]:
            parts.append(f'{o["ville_depart"]} -> {o["ville_arrivee"]}')
        elif o["ville_arrivee"]:
            parts.append("Destination: " + o["ville_arrivee"])
        dates = [d for d in (o["date_depart"], o["date_retour"]) if d]
        if dates:
            parts.append("(" + " - ".join(dates) + ")")
        if o["pnr"]:
            parts.append("PNR: " + o["pnr"])
        if o["num_billet"]:
            parts.append("N. billet: " + o["num_billet"])
    elif activite == "hotel":
        if o["nom_hotel"]:
            parts.append(o["nom_hotel"])
        lieu = " ".join(x for x in (o["ville"], o["pays"]) if x)
        if lieu:
            parts.append(lieu)
        dates = [d for d in (o["date_arrivee"], o["date_depart"]) if d]
        if dates:
            parts.append("(" + " - ".join(dates) + ")")
        if o["nb_nuits"]:
            parts.append(f'{o["nb_nuits"]} nuit(s)')
        if o["formule"]:
            parts.append(o["formule"])
    elif activite == "assurance":
        if o["compagnie_assurance"]:
            parts.append(o["compagnie_assurance"])
        if o["type_assurance"]:
            parts.append(o["type_assurance"])
        if o["destination"]:
            parts.append("Destination: " + o["destination"])
        dates = [d for d in (o["date_debut"], o["date_fin"]) if d]
        if dates:
            parts.append("(" + " - ".join(dates) + ")")
    elif activite == "visa":
        if o["pays_destination"]:
            parts.append("Pays: " + o["pays_destination"])
        if o["type_visa"]:
            parts.append(o["type_visa"])
        if o["motif"]:
            parts.append(o["motif"])
        if o["nb_entrees"]:
            parts.append(o["nb_entrees"])
    if o["passager"]:
        parts.append("Beneficiaire: " + o["passager"])
    return "  |  ".join(parts) if parts else "Service"


_LIBELLES = {"billet": "Billet d'avion", "hotel": "Hebergement hotelier",
             "assurance": "Assurance voyage", "visa": "Assistance visa"}


def generer_recu_operation(activite, operation_id, ouvrir=False):
    """Génère le PDF du reçu d'une opération et renvoie le chemin du fichier."""
    o = act.get_operation(activite, operation_id)
    if o is None:
        raise ValueError("Opération introuvable.")
    client = db.get_client(o["client_id"])
    totaux = act.totaux_operation(activite, operation_id)
    paiements = act.lister_paiements_operation(activite, operation_id)

    numero = o["reference"] or f"REC-{operation_id}"

    pdf = RecuPDF(orientation="P", unit="mm", format="A4")
    pdf._numero_recu = numero
    pdf.set_auto_page_break(auto=True, margin=22)
    pdf.set_margins(12, 12, 12)
    pdf.add_page()

    # Titre + numéro + date
    pdf.set_text_color(*BLEU)
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "RECU / FACTURE", ln=1)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(95, 6, f"No: {numero}", ln=0)
    pdf.cell(0, 6, "Date: " + datetime.now().strftime("%d/%m/%Y"), align="R", ln=1)
    pdf.ln(4)

    # Client
    _titre_section(pdf, "CLIENT")
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 6, f'{client["nom"]} {client["prenom"] or ""}'.strip(), ln=1)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*GRIS)
    for info in [x for x in ("Tel: " + (client["telephone"] or "") if client["telephone"] else "",
                             client["email"] or "", client["adresse"] or "") if x]:
        pdf.cell(0, 5, info, ln=1)
    pdf.ln(4)

    # Détail de l'opération
    _titre_section(pdf, _LIBELLES.get(activite, "Prestation").upper())
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(*BLEU)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(140, 8, "  Designation", fill=True)
    pdf.cell(46, 8, "Montant  ", fill=True, align="R", ln=1)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 9)
    x_avant, y_avant = pdf.get_x(), pdf.get_y()
    pdf.multi_cell(140, 6, "  " + _designation(activite, o), border="B",
                   align="L", max_line_height=6)
    hauteur = pdf.get_y() - y_avant
    pdf.set_xy(x_avant + 140, y_avant)
    pdf.cell(46, hauteur, formater_montant(totaux["total_client"]) + "  ",
             border="B", align="R", ln=1)
    pdf.ln(4)

    # Récapitulatif financier
    def ligne_total(libelle, valeur, gras=False, couleur=(0, 0, 0)):
        pdf.cell(120, 8, "", ln=0)
        pdf.set_font("Helvetica", "B" if gras else "", 11 if gras else 10)
        pdf.set_text_color(*couleur)
        pdf.cell(33, 8, libelle, border="T")
        pdf.cell(33, 8, formater_montant(valeur), border="T", align="R", ln=1)

    ligne_total("Total", totaux["total_client"])
    ligne_total("Paye", totaux["total_paye"])
    couleur = (180, 0, 0) if totaux["reste_a_payer"] > 0 else (0, 130, 0)
    ligne_total("Reste", totaux["reste_a_payer"], gras=True, couleur=couleur)
    pdf.ln(6)

    # Historique des paiements (facultatif)
    if paiements:
        pdf.set_text_color(0, 0, 0)
        _titre_section(pdf, "PAIEMENTS")
        pdf.set_font("Helvetica", "", 9)
        for p in paiements:
            pdf.cell(40, 6, (p["date_paiement"] or "")[:10])
            pdf.cell(60, 6, p["mode"] or "")
            pdf.cell(0, 6, formater_montant(p["montant"]), align="R", ln=1)

    pdf.ln(12)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 9)
    y = pdf.get_y()
    pdf.line(130, y, 190, y)
    pdf.set_xy(130, y + 1)
    pdf.cell(60, 5, "Signature et cachet", align="C")

    nom_fichier = f"Recu_{numero}.pdf".replace(" ", "_")
    chemin = os.path.join(config.RECUS_DIR, nom_fichier)
    pdf.output(chemin)
    if ouvrir:
        ouvrir_fichier(chemin)
    return chemin
