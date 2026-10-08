# -*- coding: utf-8 -*-
"""
pdf_engagement_visa.py
------------------------
Document « ENGAGEMENT — ASSISTANCE VISA », à faire signer par le client
avant le dépôt de son dossier.

RÈGLE ABSOLUE (demandée le 2026-10-08) : AUCUNE nouvelle saisie. Toutes les
données viennent du dossier visa déjà enregistré (voir activites.py). Si un
montant ou le mode de paiement des frais de visa n'a pas été renseigné, on
affiche « Non renseigné » — on n'invente jamais une valeur.

Correspondance avec les champs existants du dossier visa :
    - Frais d'assistance APLM            -> frais_service
      (le service facturé par l'agence)
    - Frais de visa                      -> prix_fournisseur
      (somme versée à l'ambassade / au centre, l'agence ne la garde pas)
    - Mode de paiement des frais de visa -> mode_paiement_visa
"""

import os
from datetime import datetime

import config
import database as db
import activites as act
from utils import ouvrir_fichier
from pdf_receipt import formater_montant
from pdf_listes import DocumentPDF, BLEU


MENTION_FRAIS = (
    "Je reconnais avoir ete informe(e) du montant des frais de visa "
    "applicables a ma demande. Ces frais sont distincts des frais "
    "d'assistance factures par APLM BUZNESS COMPANY Travel SARL. Les frais "
    "de visa sont payables selon les modalites prevues par l'autorite "
    "competente ou le centre de depot, notamment en ligne ou sur le lieu "
    "de depot."
)

MENTION_GARANTIE = (
    "APLM BUZNESS COMPANY Travel SARL ne garantit pas l'obtention du visa. "
    "La decision d'accorder ou de refuser le visa releve exclusivement de "
    "l'autorite competente."
)


def _montant_ou_non_renseigne(valeur):
    """N'invente jamais un montant : 0 / vide / absent -> "Non renseigné"."""
    if not valeur:
        return "Non renseigné"
    return formater_montant(valeur)  # inclut déjà la devise (ex: "20 000 FCFA")


def donnees_engagement(operation_id):
    """Rassemble, SANS RIEN SAISIR DE NOUVEAU, toutes les informations de
    l'engagement depuis le dossier visa + la fiche client. Utilisé à la fois
    pour l'aperçu (vérification par l'agent) et pour le PDF final."""
    o = act.get_operation("visa", operation_id)
    if o is None:
        raise ValueError("Dossier visa introuvable.")
    client = db.get_client(o["client_id"])
    if client is None:
        raise ValueError("Client introuvable.")
    return {
        "operation": o,
        "client": client,
        "nom_complet": f'{client["nom"]} {client["prenom"] or ""}'.strip(),
        "pays_destination": o["pays_destination"] or "Non renseigné",
        "type_visa": o["type_visa"] or "Non renseigné",
        "num_dossier": o["num_dossier"] or "Non renseigné",
        "frais_assistance_txt": _montant_ou_non_renseigne(o["frais_service"]),
        "frais_visa_txt": _montant_ou_non_renseigne(o["prix_fournisseur"]),
        "mode_paiement_txt": o["mode_paiement_visa"] or "Non renseigné",
    }


def generer_engagement_visa(operation_id, ouvrir=False):
    """Génère le PDF de l'engagement Assistance Visa et renvoie le chemin.
    L'enregistre aussi automatiquement dans les documents du dossier
    (rubrique 📎 Documents) pour qu'il reste accessible dans l'historique."""
    d = donnees_engagement(operation_id)
    o, client = d["operation"], d["client"]

    pdf = DocumentPDF(orientation="P", unit="mm", format="A4")
    pdf._sous_titre = "ENGAGEMENT - ASSISTANCE VISA"
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.set_margins(14, 14, 14)
    pdf.add_page()

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 6, "Date : " + datetime.now().strftime("%d/%m/%Y"), ln=1)
    pdf.ln(2)

    # --- Client ---
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*BLEU)
    pdf.cell(0, 7, "CLIENT", ln=1)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 6, f'Nom et prenom : {d["nom_complet"]}', ln=1)
    if client["telephone"]:
        pdf.cell(0, 6, f'Telephone : {client["telephone"]}', ln=1)
    if o["num_passeport"]:
        pdf.cell(0, 6, f'N. passeport : {o["num_passeport"]}', ln=1)
    pdf.ln(3)

    # --- Dossier visa ---
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*BLEU)
    pdf.cell(0, 7, "DOSSIER VISA", ln=1)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 6, f'Pays de destination : {d["pays_destination"]}', ln=1)
    pdf.cell(0, 6, f'Type de visa : {d["type_visa"]}', ln=1)
    pdf.cell(0, 6, f'N. de dossier : {d["num_dossier"]}', ln=1)
    pdf.ln(3)

    # --- Frais (partie explicitement demandée) ---
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*BLEU)
    pdf.cell(0, 7, "FRAIS", ln=1)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 6, f'Frais d\'assistance APLM : {d["frais_assistance_txt"]}', ln=1)
    pdf.cell(0, 6, f'Frais de visa : {d["frais_visa_txt"]}', ln=1)
    pdf.cell(0, 6,
             f'Mode de paiement des frais de visa : {d["mode_paiement_txt"]}', ln=1)
    pdf.ln(4)

    # --- Mentions légales (texte exact demandé, reproduit fidèlement) ---
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(0, 0, 0)
    pdf.multi_cell(0, 5, MENTION_FRAIS)
    pdf.ln(2)
    pdf.multi_cell(0, 5, MENTION_GARANTIE)
    pdf.ln(12)

    # --- Signature ---
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(90, 5, "Signature du client", ln=0)
    pdf.cell(0, 5, "Signature et cachet de l'agence", ln=1)
    pdf.ln(14)
    y = pdf.get_y()
    pdf.line(14, y, 90, y)
    pdf.line(120, y, 196, y)

    nom_fichier = f'Engagement_Visa_{o["num_dossier"] or operation_id}.pdf'.replace(" ", "_")
    chemin = os.path.join(config.RECUS_DIR, nom_fichier)
    pdf.output(chemin)

    # Historique : reste accessible dans les documents du dossier visa.
    import documents
    documents.enregistrer_document(
        chemin, categorie="Document visa",
        nom=f'Engagement Assistance Visa - {d["nom_complet"]}',
        operation_type="visa", operation_id=operation_id,
        client_id=o["client_id"])

    if ouvrir:
        ouvrir_fichier(chemin)
    return chemin
