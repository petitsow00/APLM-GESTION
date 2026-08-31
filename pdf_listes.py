# -*- coding: utf-8 -*-
"""
pdf_listes.py
--------------
Génère deux documents PDF professionnels pour APLM BUZNESS COMPANY :

  1) generer_liste_clients(...)            -> la liste complète des clients
  2) generer_historique_transactions(...)  -> les transactions d'une période

⚠️ Ce fichier est SÉPARÉ de pdf_receipt.py (les reçus). On ne modifie donc
   PAS le comportement des reçus existants. Comme il s'agit de documents de
   gestion INTERNES à l'agence, l'historique peut afficher le prix d'achat et
   le bénéfice (ce que le reçu client, lui, n'affiche jamais).
"""

import os
from datetime import datetime
from fpdf import FPDF

import config
import settings
import database as db
from i18n import t
from pdf_receipt import formater_montant   # on réutilise le même formatage d'argent
from utils import ouvrir_fichier


# --- Mêmes couleurs que le reçu (charte bleu professionnel) ---------------
BLEU = (18, 52, 86)
BLEU_CLAIR = (230, 238, 245)
GRIS = (110, 110, 110)


class DocumentPDF(FPDF):
    """Modèle de document (liste/historique) avec en-tête et pied de page.

    self._sous_titre : titre du document affiché dans l'en-tête
                       (ex : « LISTE DES CLIENTS »).
    """

    _sous_titre = ""

    def header(self):
        y_depart = 12
        # --- Logo (s'il existe) ---
        if os.path.exists(config.LOGO_PATH):
            try:
                self.image(config.LOGO_PATH, x=12, y=y_depart, w=26)
                decalage_x = 43
            except Exception:
                decalage_x = 12
        else:
            decalage_x = 12

        # --- Nom de la société (lu dans les Réglages) ---
        self.set_xy(decalage_x, y_depart)
        self.set_text_color(*BLEU)
        self.set_font("Helvetica", "B", 18)
        self.cell(0, 9, settings.get("nom"), ln=1)

        # --- Coordonnées ---
        self.set_x(decalage_x)
        self.set_text_color(*GRIS)
        self.set_font("Helvetica", "", 9)
        contact = []
        if settings.get("adresse"):
            contact.append(settings.get("adresse"))
        if settings.get("telephone"):
            contact.append("Tel: " + settings.get("telephone"))
        if settings.get("email"):
            contact.append(settings.get("email"))
        if contact:
            self.set_x(decalage_x)
            self.cell(0, 5, "   -   ".join(contact), ln=1)

        # --- Titre du document ---
        self.ln(3)
        self.set_text_color(*BLEU)
        self.set_font("Helvetica", "B", 14)
        self.cell(0, 8, self._sous_titre, ln=1)

        # --- Ligne de séparation ---
        self.set_draw_color(*BLEU)
        self.set_line_width(0.6)
        y = self.get_y()
        self.line(self.l_margin, y, self.w - self.r_margin, y)
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_draw_color(*BLEU)
        self.set_line_width(0.3)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(2)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*GRIS)
        self.cell(0, 5, f"{settings.get('nom')}   -   Page {self.page_no()}",
                  align="C")


def _ligne_date_generation(pdf):
    """Écrit « Date de génération : JJ/MM/AAAA » sous le titre."""
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(0, 0, 0)
    date_jour = datetime.now().strftime("%d/%m/%Y")
    pdf.cell(0, 6, f"{t('recu_date')} de génération : {date_jour}", ln=1)
    pdf.ln(2)


# ===========================================================================
#  1) LISTE COMPLÈTE DES CLIENTS
# ===========================================================================
def generer_liste_clients(ouvrir=False):
    """Génère le PDF de la liste complète des clients et renvoie le chemin."""
    clients = db.lister_clients()

    pdf = DocumentPDF(orientation="P", unit="mm", format="A4")
    pdf._sous_titre = t("pdf_liste_clients_titre")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.set_margins(12, 12, 12)
    pdf.add_page()

    _ligne_date_generation(pdf)

    # Largeurs des colonnes (total = 186 mm sur A4 portrait avec marges de 12)
    largeurs = {"num": 12, "nom": 60, "tel": 38, "email": 46, "date": 30}

    def entete_tableau():
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_fill_color(*BLEU)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(largeurs["num"],   8, "  " + t("col_num"), fill=True)
        pdf.cell(largeurs["nom"],   8, t("col_nom_prenom"), fill=True)
        pdf.cell(largeurs["tel"],   8, t("champ_telephone"), fill=True)
        pdf.cell(largeurs["email"], 8, t("champ_email"), fill=True)
        pdf.cell(largeurs["date"],  8, t("col_date_enreg"), fill=True, ln=1)

    entete_tableau()

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 9)
    alterne = False
    for i, c in enumerate(clients, start=1):
        # Nouvelle page -> on réaffiche l'en-tête du tableau
        if pdf.get_y() > pdf.h - 25:
            pdf.add_page()
            entete_tableau()
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Helvetica", "", 9)

        pdf.set_fill_color(245, 245, 245) if alterne else pdf.set_fill_color(255, 255, 255)
        alterne = not alterne

        nom_complet = f'{c["nom"]} {c["prenom"] or ""}'.strip()
        date_enr = (c["date_creation"] or "")[:10]

        pdf.cell(largeurs["num"],   7, "  " + str(i), border="B", fill=True)
        pdf.cell(largeurs["nom"],   7, nom_complet[:38], border="B", fill=True)
        pdf.cell(largeurs["tel"],   7, (c["telephone"] or "")[:22], border="B", fill=True)
        pdf.cell(largeurs["email"], 7, (c["email"] or "")[:30], border="B", fill=True)
        pdf.cell(largeurs["date"],  7, date_enr, border="B", fill=True, ln=1)

    if not clients:
        pdf.cell(0, 8, "  (Aucun client enregistré)", ln=1)

    # Total
    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*BLEU)
    pdf.cell(0, 7, f"{t('dash_clients')} : {len(clients)}", ln=1)

    nom_fichier = "Liste_clients_" + datetime.now().strftime("%Y-%m-%d") + ".pdf"
    chemin = os.path.join(config.RECUS_DIR, nom_fichier)
    pdf.output(chemin)

    if ouvrir:
        ouvrir_fichier(chemin)
    return chemin


# ===========================================================================
#  2) HISTORIQUE DES TRANSACTIONS D'UNE PÉRIODE
# ===========================================================================
def generer_historique_transactions(date_debut, date_fin, ouvrir=False):
    """Génère le PDF de l'historique des transactions entre deux dates."""
    transactions = db.lister_transactions_periode(date_debut, date_fin)
    totaux = db.totaux_transactions_periode(date_debut, date_fin)

    # Format paysage : beaucoup de colonnes
    pdf = DocumentPDF(orientation="L", unit="mm", format="A4")
    pdf._sous_titre = t("pdf_transac_titre")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.set_margins(12, 12, 12)
    pdf.add_page()

    # Période
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 6, f"{t('lbl_periode')} : {date_debut}  ->  {date_fin}", ln=1)
    _ligne_date_generation(pdf)

    # Largeurs (total = 273 mm sur A4 paysage avec marges de 12)
    largeurs = {
        "date": 24, "client": 50, "ref": 34, "type": 30,
        "montant": 30, "mode": 30, "achat": 25, "vente": 25, "benef": 25,
    }

    def entete_tableau():
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_fill_color(*BLEU)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(largeurs["date"],    8, "  " + t("recu_date"), fill=True)
        pdf.cell(largeurs["client"],  8, t("champ_client"), fill=True)
        pdf.cell(largeurs["ref"],     8, t("champ_reference"), fill=True)
        pdf.cell(largeurs["type"],    8, t("col_type_op"), fill=True)
        pdf.cell(largeurs["montant"], 8, t("champ_montant"), fill=True, align="R")
        pdf.cell(largeurs["mode"],    8, t("champ_mode"), fill=True)
        pdf.cell(largeurs["achat"],   8, t("champ_prix_achat"), fill=True, align="R")
        pdf.cell(largeurs["vente"],   8, t("champ_prix_vente"), fill=True, align="R")
        pdf.cell(largeurs["benef"],   8, t("col_benefice"), fill=True, align="R", ln=1)

    entete_tableau()

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 8)
    alterne = False

    def montant_ou_vide(valeur):
        return formater_montant(valeur) if valeur is not None else "-"

    for tr in transactions:
        if pdf.get_y() > pdf.h - 25:
            pdf.add_page()
            entete_tableau()
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Helvetica", "", 8)

        pdf.set_fill_color(245, 245, 245) if alterne else pdf.set_fill_color(255, 255, 255)
        alterne = not alterne

        # Traduit le type d'opération
        type_txt = t("type_vente") if tr["type"] == "Vente" else t("type_encaissement")

        pdf.cell(largeurs["date"],    7, "  " + (tr["date"] or ""), border="B", fill=True)
        pdf.cell(largeurs["client"],  7, (tr["client"] or "")[:32], border="B", fill=True)
        pdf.cell(largeurs["ref"],     7, (tr["reference"] or "")[:20], border="B", fill=True)
        pdf.cell(largeurs["type"],    7, type_txt, border="B", fill=True)
        pdf.cell(largeurs["montant"], 7, formater_montant(tr["montant"]), border="B", fill=True, align="R")
        pdf.cell(largeurs["mode"],    7, (tr["mode"] or "")[:18], border="B", fill=True)
        pdf.cell(largeurs["achat"],   7, montant_ou_vide(tr["prix_achat"]), border="B", fill=True, align="R")
        pdf.cell(largeurs["vente"],   7, montant_ou_vide(tr["prix_vente"]), border="B", fill=True, align="R")
        pdf.cell(largeurs["benef"],   7, montant_ou_vide(tr["benefice"]), border="B", fill=True, align="R", ln=1)

    if not transactions:
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(0, 8, "  " + t("msg_aucune_transac"), ln=1)

    # ----- Totaux de la période -----
    pdf.ln(6)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*BLEU)
    pdf.cell(0, 7, t("lbl_periode") + " - Totaux", ln=1)
    pdf.ln(1)

    def ligne_total(libelle, valeur, couleur=(0, 0, 0)):
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(80, 80, 80)
        pdf.cell(70, 7, libelle, border="T")
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*couleur)
        pdf.cell(50, 7, formater_montant(valeur), border="T", align="R", ln=1)

    ligne_total(t("lbl_total_ventes"),   totaux["total_ventes"])
    ligne_total(t("lbl_total_encaisse"), totaux["total_encaisse"])
    ligne_total(t("lbl_total_achats"),   totaux["total_achats"])
    couleur_benef = (0, 130, 0) if totaux["total_benefice"] >= 0 else (180, 0, 0)
    ligne_total(t("lbl_total_benefice"), totaux["total_benefice"], couleur_benef)
    couleur_rest = (180, 0, 0) if totaux["total_restant"] > 0 else (0, 130, 0)
    ligne_total(t("lbl_total_restant"),  totaux["total_restant"], couleur_rest)

    nom_fichier = f"Transactions_{date_debut}_a_{date_fin}.pdf".replace(" ", "_")
    chemin = os.path.join(config.RECUS_DIR, nom_fichier)
    pdf.output(chemin)

    if ouvrir:
        ouvrir_fichier(chemin)
    return chemin
