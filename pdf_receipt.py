# -*- coding: utf-8 -*-
"""
pdf_receipt.py
---------------
Génère un reçu PDF professionnel pour un dossier.

⚠️ RÈGLE ABSOLUE :
   Le reçu affiche UNIQUEMENT :
       - les informations de APLM BUZNESS COMPANY
       - les informations du client et du voyage
   Il n'affiche JAMAIS :
       - le consolidateur (Raya Travel / Bleujay / Travelgenex)
       - le GDS (Amadeus / Galileo / APG)
       - le prix d'achat interne
   -> Ces champs ne sont même pas lus dans ce fichier.
"""

import os
from datetime import datetime
from fpdf import FPDF

import config
import settings
import database as db
import i18n
from i18n import t
from utils import ouvrir_fichier


# --- Couleurs de la charte (bleu professionnel) ---------------------------
BLEU = (18, 52, 86)        # bleu foncé pour les titres
BLEU_CLAIR = (230, 238, 245)
GRIS = (110, 110, 110)


def formater_montant(valeur):
    """Transforme 1500000 -> '1 500 000 FCFA' (séparateur de milliers)."""
    try:
        valeur = float(valeur)
    except (TypeError, ValueError):
        valeur = 0
    entier = f"{valeur:,.0f}".replace(",", " ")
    return f"{entier} {settings.devise()}"


class RecuPDF(FPDF):
    """Modèle de reçu avec en-tête et pied de page automatiques."""

    def header(self):
        # --- Logo (s'il existe) ---
        y_depart = 12
        if os.path.exists(config.LOGO_PATH):
            try:
                self.image(config.LOGO_PATH, x=12, y=y_depart, w=28)
                decalage_x = 45
            except Exception:
                decalage_x = 12
        else:
            decalage_x = 12

        # --- Nom de la société (lu dans les Réglages de l'agence) ---
        self.set_xy(decalage_x, y_depart)
        self.set_text_color(*BLEU)
        self.set_font("Helvetica", "B", 20)
        self.cell(0, 9, settings.get("nom"), ln=1)

        # --- Coordonnées de la société ---
        self.set_x(decalage_x)
        self.set_text_color(*GRIS)
        self.set_font("Helvetica", "", 9)
        lignes_infos = []
        if settings.get("slogan"):
            lignes_infos.append(settings.get("slogan"))
        if settings.get("adresse"):
            lignes_infos.append(settings.get("adresse"))
        contact = []
        if settings.get("telephone"):
            contact.append("Tel: " + settings.get("telephone"))
        if settings.get("email"):
            contact.append(settings.get("email"))
        if contact:
            lignes_infos.append("   -   ".join(contact))
        for ligne in lignes_infos:
            self.set_x(decalage_x)
            self.cell(0, 5, ligne, ln=1)

        # --- Ligne de séparation ---
        self.ln(2)
        self.set_draw_color(*BLEU)
        self.set_line_width(0.6)
        y = self.get_y()
        self.line(12, y, 198, y)
        self.ln(6)

    def footer(self):
        self.set_y(-18)
        self.set_draw_color(*BLEU)
        self.set_line_width(0.3)
        self.line(12, self.get_y(), 198, self.get_y())
        self.ln(2)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*GRIS)
        self.cell(0, 5, t("recu_merci"), align="C", ln=1)
        self.cell(0, 5,
                  settings.get("nom") + "  -  " + t("recu_no") + " " + self._numero_recu,
                  align="C")


def _titre_section(pdf, texte):
    pdf.set_fill_color(*BLEU_CLAIR)
    pdf.set_text_color(*BLEU)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "  " + texte, ln=1, fill=True)
    pdf.ln(2)


def _designation_reservation(resa):
    """Construit une description LISIBLE du service, SANS info interne.
    On n'utilise que : type, compagnie, itinéraire, dates, passager."""
    parts = []
    if resa["type_billet"]:
        parts.append(resa["type_billet"])
    if resa["compagnie"]:
        parts.append(resa["compagnie"])
    trajet = ""
    if resa["ville_depart"] or resa["ville_arrivee"]:
        trajet = f'{resa["ville_depart"] or "?"} -> {resa["ville_arrivee"] or "?"}'
        parts.append(trajet)
    dates = []
    if resa["date_depart"]:
        dates.append(resa["date_depart"])
    if resa["date_retour"]:
        dates.append("- " + resa["date_retour"])
    if dates:
        parts.append("(" + " ".join(dates) + ")")
    if resa["passager"]:
        parts.append("Passager: " + resa["passager"])
    return "  |  ".join(parts) if parts else "Service"


def generer_recu(dossier_id, ouvrir=False):
    """Génère le PDF du reçu pour un dossier et renvoie le chemin du fichier."""
    dossier = db.get_dossier(dossier_id)
    if dossier is None:
        raise ValueError("Dossier introuvable.")

    reservations = db.lister_reservations(dossier_id)
    solde = db.get_solde_dossier(dossier_id)

    numero_recu = dossier["reference"] or f"REC-{dossier_id}"

    pdf = RecuPDF(orientation="P", unit="mm", format="A4")
    pdf._numero_recu = numero_recu
    pdf.set_auto_page_break(auto=True, margin=22)
    pdf.set_margins(12, 12, 12)
    pdf.add_page()

    # ----- Titre du document + numéro + date -----
    pdf.set_text_color(*BLEU)
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, t("recu_titre"), ln=1)

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(0, 0, 0)
    date_jour = datetime.now().strftime("%d/%m/%Y")
    pdf.cell(95, 6, f'{t("recu_no")}: {numero_recu}', ln=0)
    pdf.cell(0, 6, f'{t("recu_date")}: {date_jour}', align="R", ln=1)
    pdf.ln(4)

    # ----- Bloc CLIENT -----
    _titre_section(pdf, t("recu_client"))
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "B", 11)
    nom_complet = f'{dossier["client_nom"]} {dossier["client_prenom"] or ""}'.strip()
    pdf.cell(0, 6, nom_complet, ln=1)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*GRIS)
    infos_client = []
    if dossier["client_telephone"]:
        infos_client.append("Tel: " + dossier["client_telephone"])
    if dossier["client_email"]:
        infos_client.append(dossier["client_email"])
    if dossier["client_adresse"]:
        infos_client.append(dossier["client_adresse"])
    for info in infos_client:
        pdf.cell(0, 5, info, ln=1)
    pdf.ln(4)

    # ----- Tableau des SERVICES (sans aucune info interne) -----
    _titre_section(pdf, t("lbl_reservations"))
    # En-tête du tableau
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(*BLEU)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(140, 8, "  " + t("recu_designation"), border=0, fill=True)
    pdf.cell(46, 8, t("recu_montant") + "  ", border=0, fill=True, align="R", ln=1)

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 9)
    alterne = False
    if reservations:
        for resa in reservations:
            designation = _designation_reservation(resa)
            montant = formater_montant(resa["prix_vente"])
            # Fond alterné pour la lisibilité
            if alterne:
                pdf.set_fill_color(245, 245, 245)
            else:
                pdf.set_fill_color(255, 255, 255)
            alterne = not alterne

            # Cellule multi-lignes pour la désignation
            x_avant = pdf.get_x()
            y_avant = pdf.get_y()
            pdf.multi_cell(140, 6, "  " + designation, border="B", fill=True,
                           align="L", max_line_height=6)
            hauteur = pdf.get_y() - y_avant
            # Montant aligné à droite, même hauteur
            pdf.set_xy(x_avant + 140, y_avant)
            pdf.cell(46, hauteur, montant + "  ", border="B", fill=True, align="R", ln=1)
    else:
        pdf.cell(0, 7, "  (Aucun service enregistré)", border="B", ln=1)
    pdf.ln(4)

    # ----- Récapitulatif financier -----
    largeur_gauche = 120
    largeur_droite = 66
    pdf.set_font("Helvetica", "", 10)

    def ligne_total(libelle, valeur, gras=False, couleur=(0, 0, 0)):
        pdf.cell(largeur_gauche, 8, "", ln=0)  # espace vide à gauche
        if gras:
            pdf.set_font("Helvetica", "B", 11)
        else:
            pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*couleur)
        pdf.cell(largeur_droite * 0.5, 8, libelle, border="T")
        pdf.cell(largeur_droite * 0.5, 8, formater_montant(valeur),
                 border="T", align="R", ln=1)

    ligne_total(t("lbl_total_vente"), solde["total_vente"])
    ligne_total(t("lbl_total_paye"), solde["total_paye"])
    couleur_solde = (180, 0, 0) if solde["solde"] > 0 else (0, 130, 0)
    ligne_total(t("lbl_solde"), solde["solde"], gras=True, couleur=couleur_solde)

    pdf.ln(16)

    # ----- Zone signature -----
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 9)
    y = pdf.get_y()
    pdf.line(130, y, 190, y)
    pdf.set_xy(130, y + 1)
    pdf.cell(60, 5, t("recu_signature"), align="C")

    # ----- Sauvegarde du fichier -----
    nom_fichier = f"Recu_{numero_recu}.pdf".replace(" ", "_")
    chemin = os.path.join(config.RECUS_DIR, nom_fichier)
    pdf.output(chemin)

    if ouvrir:
        ouvrir_fichier(chemin)   # ouvre le PDF (Windows / macOS / Linux)

    return chemin
