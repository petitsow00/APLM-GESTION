# -*- coding: utf-8 -*-
"""
pdf_engagement_visa.py
------------------------
Document « ENGAGEMENT CLIENT - ASSISTANCE VISA », à faire signer par le
client avant le dépôt de son dossier (modèle complet du 2026-10-08).

RÈGLE ABSOLUE : AUCUNE nouvelle saisie. Toutes les données viennent du
dossier visa déjà enregistré + de la fiche client (voir activites.py /
database.py). Si une information n'a pas été renseignée, on affiche
« Non renseigné » — on n'invente jamais une valeur. Les emplacements "Fait à"
et les signatures restent à remplir à la main (aucun champ "ville" n'existe
dans le logiciel).

Correspondance avec les champs existants :
    - Nom / Prénom                        -> fiche client
    - Date de naissance                   -> fiche client (date_naissance)
    - Nationalité / N° de passeport        -> dossier visa, sinon fiche client
    - Pays de destination / Type de visa   -> dossier visa
    - Frais d'assistance APLM              -> frais_service
    - Frais de visa                        -> prix_fournisseur
    - Mode de paiement des frais de visa   -> mode_paiement_visa

⚠️ Police standard (Helvetica) : on n'utilise QUE des caractères latin-1
   (les guillemets « » et les accents français passent, mais pas les tirets
   longs — / – ni les cases ☐/☑, remplacés ici par des lignes dessinées et
   des cases [ ] / [X]).
"""

import os
from datetime import datetime

import config
import database as db
import activites as act
from utils import ouvrir_fichier
from pdf_receipt import formater_montant
from pdf_listes import DocumentPDF, BLEU


NOM_SOCIETE_LEGAL = "APLM BUZNESS COMPANY Travel SARL"

TXT_ASSISTANCE = (
    "Cette assistance peut notamment comprendre l'information sur les "
    "documents necessaires, l'organisation du dossier, l'aide au "
    "remplissage des formulaires et l'accompagnement dans les differentes "
    "demarches administratives liees a la demande."
)
TXT_FRAIS_DISTINCTS = (
    "Je reconnais que les frais d'assistance et les frais de visa sont "
    "deux frais distincts."
)
TXT_FRAIS_NATURE = (
    "Les frais de visa sont ceux applicables a ma demande auprès de "
    "l'autorite competente ou du centre de depot. Ils ne constituent pas "
    f"une remuneration supplementaire de {NOM_SOCIETE_LEGAL}."
)
TXT_FRAIS_NON_REMBOURSABLE = (
    "Je reconnais que, quelle que soit l'issue de ma demande, les frais "
    "de dossier ne sont pas remboursables."
)
TXT_ENGAGEMENT_1 = (
    "Je m'engage a fournir des informations exactes, completes et "
    "sinceres ainsi que des documents authentiques."
)
TXT_ENGAGEMENT_2 = (
    "Je reconnais etre responsable de l'exactitude et de l'authenticite "
    "des documents remis pour constituer mon dossier."
)
TXT_ENGAGEMENT_3 = (
    "Je m'engage egalement a fournir dans les delais les documents "
    "complementaires qui pourraient etre demandes et a respecter les "
    "rendez-vous et procedures qui me seront communiques."
)
TXT_GARANTIE_1 = (
    f"Je reconnais expressement que {NOM_SOCIETE_LEGAL} ne garantit pas "
    "l'obtention du visa."
)
TXT_GARANTIE_2 = (
    "La decision d'accorder, de refuser ou de demander des informations "
    "ou documents complementaires releve exclusivement de l'ambassade, "
    "du consulat, du centre de visa ou de toute autre autorite competente."
)
TXT_GARANTIE_3 = (
    "En consequence, un refus de visa, un retard de traitement ou une "
    "demande de documents complementaires ne peut etre considere comme "
    "une garantie non respectee par l'agence lorsque celle-ci a "
    "correctement execute la prestation d'assistance convenue."
)
TXT_DECLARATION_1 = (
    "Je declare avoir ete informe(e) des conditions de la prestation "
    "d'assistance visa et avoir compris que l'agence intervient "
    "uniquement dans le cadre de l'accompagnement administratif de ma "
    "demande."
)
TXT_DECLARATION_2 = "Je reconnais avoir pris connaissance du present engagement et l'accepte."


def _ou_non_renseigne(valeur):
    valeur = (valeur or "").strip() if isinstance(valeur, str) else valeur
    return valeur if valeur else "Non renseigné"


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

    def champ_client_ou_dossier(cle):
        """Priorité au dossier visa (propre à cette demande), sinon la
        fiche client générale."""
        try:
            val_dossier = o[cle]
        except Exception:
            val_dossier = None
        if val_dossier:
            return val_dossier
        try:
            return client[cle]
        except Exception:
            return None

    mode = (o["mode_paiement_visa"] or "").strip()
    return {
        "operation": o,
        "client": client,
        "nom": _ou_non_renseigne(client["nom"]),
        "prenom": _ou_non_renseigne(client["prenom"]),
        "nom_complet": f'{client["nom"]} {client["prenom"] or ""}'.strip(),
        "date_naissance": _ou_non_renseigne(client["date_naissance"]
                                            if "date_naissance" in client.keys() else None),
        "nationalite": _ou_non_renseigne(champ_client_ou_dossier("nationalite")),
        "num_passeport": _ou_non_renseigne(champ_client_ou_dossier("num_passeport")),
        "pays_destination": _ou_non_renseigne(o["pays_destination"]),
        "type_visa": _ou_non_renseigne(o["type_visa"]),
        "num_dossier": _ou_non_renseigne(o["num_dossier"]),
        "frais_assistance_txt": _montant_ou_non_renseigne(o["frais_service"]),
        "frais_visa_txt": _montant_ou_non_renseigne(o["prix_fournisseur"]),
        "mode_paiement_txt": mode or "Non renseigné",
        "case_en_ligne": "[X]" if mode == "Paiement en ligne" else "[ ]",
        "case_lieu_depot": "[X]" if mode == "Paiement sur le lieu de dépôt" else "[ ]",
        "case_a_confirmer": "[X]" if mode == "À confirmer" else "[ ]",
    }


def generer_engagement_visa(operation_id, ouvrir=False):
    """Génère le PDF de l'engagement Assistance Visa et renvoie le chemin.
    L'enregistre aussi automatiquement dans les documents du dossier
    (rubrique 📎 Documents) pour qu'il reste accessible dans l'historique."""
    d = donnees_engagement(operation_id)
    o = d["operation"]

    pdf = DocumentPDF(orientation="P", unit="mm", format="A4")
    pdf._sous_titre = "ENGAGEMENT CLIENT - ASSISTANCE VISA"
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.set_margins(14, 14, 14)
    pdf.add_page()

    def section(titre):
        pdf.ln(2)
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(*BLEU)
        pdf.cell(0, 7, titre, ln=1)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(0, 0, 0)

    def ligne(texte):
        pdf.cell(0, 6, texte, ln=1)

    def paragraphe(texte):
        pdf.multi_cell(0, 5.2, texte)
        pdf.ln(1)

    def separateur():
        pdf.ln(2)
        pdf.set_draw_color(*BLEU)
        pdf.set_line_width(0.3)
        y = pdf.get_y()
        pdf.line(pdf.l_margin, y, pdf.w - pdf.r_margin, y)
        pdf.ln(3)

    # --- En-tête société (nom légal exact, en plus de l'en-tête agence) ---
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 6, NOM_SOCIETE_LEGAL, ln=1)
    pdf.ln(2)

    # --- Identification du client ---
    section("IDENTIFICATION DU CLIENT")
    ligne(f'Nom : {d["nom"]}')
    ligne(f'Prénom : {d["prenom"]}')
    ligne(f'Date de naissance : {d["date_naissance"]}')
    ligne(f'Nationalité : {d["nationalite"]}')
    ligne(f'N° de passeport : {d["num_passeport"]}')
    ligne(f'Pays de destination : {d["pays_destination"]}')
    ligne(f'Type de visa : {d["type_visa"]}')
    separateur()

    # --- Objet de l'engagement ---
    section("OBJET DE L'ENGAGEMENT")
    paragraphe(
        f'Je soussigné(e), {d["nom_complet"]}, sollicite auprès de '
        f'{NOM_SOCIETE_LEGAL} une prestation d\'assistance dans le cadre '
        f'de ma demande de visa pour {d["pays_destination"]}.')
    paragraphe(TXT_ASSISTANCE)

    # --- Frais ---
    section("FRAIS")
    ligne(f'Frais d\'assistance APLM : {d["frais_assistance_txt"]}')
    ligne(f'Frais de visa : {d["frais_visa_txt"]}')
    pdf.ln(1)
    ligne("Mode de paiement des frais de visa :")
    ligne(f'   {d["case_en_ligne"]}  Paiement en ligne')
    ligne(f'   {d["case_lieu_depot"]}  Paiement sur le lieu de dépôt')
    ligne(f'   {d["case_a_confirmer"]}  À confirmer')
    pdf.ln(1)
    paragraphe(TXT_FRAIS_DISTINCTS)
    paragraphe(TXT_FRAIS_NATURE)
    paragraphe(TXT_FRAIS_NON_REMBOURSABLE)

    # --- Engagement du client ---
    section("ENGAGEMENT DU CLIENT")
    paragraphe(TXT_ENGAGEMENT_1)
    paragraphe(TXT_ENGAGEMENT_2)
    paragraphe(TXT_ENGAGEMENT_3)

    # --- Absence de garantie d'obtention du visa ---
    section("ABSENCE DE GARANTIE D'OBTENTION DU VISA")
    paragraphe(TXT_GARANTIE_1)
    paragraphe(TXT_GARANTIE_2)
    paragraphe(TXT_GARANTIE_3)

    # --- Déclaration du client ---
    section("DÉCLARATION DU CLIENT")
    paragraphe(TXT_DECLARATION_1)
    paragraphe(TXT_DECLARATION_2)

    # --- Fait à / Le (ville à remplir à la main : aucun champ "ville"
    #     n'existe dans le logiciel -> on n'invente rien) ---
    pdf.ln(3)
    pdf.cell(95, 6, "Fait à : ______________________", ln=0)
    pdf.cell(0, 6, "Le : " + datetime.now().strftime("%d/%m/%Y"), ln=1)
    pdf.ln(6)

    # --- Signature du client ---
    section("SIGNATURE DU CLIENT")
    ligne('Mention : « Lu et approuvé »')
    pdf.ln(10)
    y = pdf.get_y()
    pdf.cell(90, 5, "Signature :", ln=0)
    pdf.line(40, y + 5, 90, y + 5)
    pdf.ln(12)

    separateur()

    # --- Partie agence ---
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 6, NOM_SOCIETE_LEGAL, ln=1)
    pdf.set_font("Helvetica", "", 10)
    pdf.ln(2)
    ligne("Nom / Responsable : __________________________")
    pdf.ln(8)
    y = pdf.get_y()
    pdf.cell(0, 5, "Signature et cachet :", ln=1)
    pdf.ln(10)

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
