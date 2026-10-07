# -*- coding: utf-8 -*-
"""
pdf_comptabilite.py
--------------------
Génère les documents PDF de la COMPTABILITÉ (SYSCOHADA) :

  - generer_balance(...)        -> la balance comptable
  - generer_grand_livre(...)    -> le grand livre (mouvements d'un/des compte(s))
  - generer_journal(...)        -> un journal (écritures)
  - generer_etat_tresorerie(...)-> état de caisse ou de banque
  - generer_resultat(...)       -> compte de résultat
  - generer_bilan(...)          -> bilan

On réutilise le modèle de document (en-tête agence + pied de page) déjà défini
dans pdf_listes.py, et le formatage d'argent de pdf_receipt.py.

⚠️ Police fpdf = latin-1 : ne PAS utiliser le tiret long « — » (utiliser « - »).
"""

import os
from datetime import datetime

import config
import comptabilite as co
from i18n import t
from pdf_receipt import formater_montant
from pdf_listes import DocumentPDF, BLEU, GRIS
from utils import ouvrir_fichier


def _periode_txt(date_debut, date_fin):
    if date_debut and date_fin:
        return f"Periode : {date_debut}  ->  {date_fin}"
    if date_fin:
        return f"Jusqu'au {date_fin}"
    return "Toutes periodes"


def _nouveau_doc(titre, paysage=False):
    pdf = DocumentPDF(orientation="L" if paysage else "P", unit="mm", format="A4")
    pdf._sous_titre = titre
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.set_margins(12, 12, 12)
    pdf.add_page()
    return pdf


def _ligne_periode(pdf, date_debut, date_fin):
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 6, _periode_txt(date_debut, date_fin), ln=1)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*GRIS)
    pdf.cell(0, 5, "Genere le : " + datetime.now().strftime("%d/%m/%Y %H:%M"), ln=1)
    pdf.ln(2)


def _chemin(nom_fichier):
    return os.path.join(config.RECUS_DIR, nom_fichier.replace(" ", "_"))


# ===========================================================================
#  BALANCE
# ===========================================================================
def generer_balance(date_debut=None, date_fin=None, ouvrir=False):
    lignes = co.balance(date_debut, date_fin)
    pdf = _nouveau_doc(t("tab_balance").upper(), paysage=True)
    _ligne_periode(pdf, date_debut, date_fin)

    L = {"cpt": 24, "int": 95, "td": 38, "tc": 38, "sd": 38, "sc": 38}

    def entete():
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_fill_color(*BLEU)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(L["cpt"], 8, "  " + t("col_compte"), fill=True)
        pdf.cell(L["int"], 8, t("col_intitule"), fill=True)
        pdf.cell(L["td"], 8, t("col_debit"), fill=True, align="R")
        pdf.cell(L["tc"], 8, t("col_credit"), fill=True, align="R")
        pdf.cell(L["sd"], 8, t("col_solde_d"), fill=True, align="R")
        pdf.cell(L["sc"], 8, t("col_solde_c"), fill=True, align="R", ln=1)

    entete()
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 9)
    alt = False
    ttd = ttc = tsd = tsc = 0
    for b in lignes:
        if pdf.get_y() > pdf.h - 25:
            pdf.add_page(); entete()
            pdf.set_text_color(0, 0, 0); pdf.set_font("Helvetica", "", 9)
        pdf.set_fill_color(245, 245, 245) if alt else pdf.set_fill_color(255, 255, 255)
        alt = not alt
        pdf.cell(L["cpt"], 7, "  " + b["compte"], border="B", fill=True)
        pdf.cell(L["int"], 7, (b["intitule"] or "")[:60], border="B", fill=True)
        pdf.cell(L["td"], 7, formater_montant(b["total_debit"]), border="B", fill=True, align="R")
        pdf.cell(L["tc"], 7, formater_montant(b["total_credit"]), border="B", fill=True, align="R")
        pdf.cell(L["sd"], 7, formater_montant(b["solde_debiteur"]), border="B", fill=True, align="R")
        pdf.cell(L["sc"], 7, formater_montant(b["solde_crediteur"]), border="B", fill=True, align="R", ln=1)
        ttd += b["total_debit"]; ttc += b["total_credit"]
        tsd += b["solde_debiteur"]; tsc += b["solde_crediteur"]

    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*BLEU)
    pdf.cell(L["cpt"] + L["int"], 8, "  TOTAUX", border="T")
    pdf.cell(L["td"], 8, formater_montant(ttd), border="T", align="R")
    pdf.cell(L["tc"], 8, formater_montant(ttc), border="T", align="R")
    pdf.cell(L["sd"], 8, formater_montant(tsd), border="T", align="R")
    pdf.cell(L["sc"], 8, formater_montant(tsc), border="T", align="R", ln=1)

    chemin = _chemin(f"Balance_{date_debut or 'debut'}_{date_fin or 'fin'}.pdf")
    pdf.output(chemin)
    if ouvrir:
        ouvrir_fichier(chemin)
    return chemin


# ===========================================================================
#  GRAND LIVRE
# ===========================================================================
def generer_grand_livre(compte=None, date_debut=None, date_fin=None,
                        journal_code=None, ouvrir=False):
    lignes = co.grand_livre(compte, date_debut, date_fin, journal_code)
    titre = t("tab_grand_livre").upper()
    if compte:
        titre += f" - {compte} {co.intitule_compte(compte)}"
    pdf = _nouveau_doc(titre, paysage=True)
    _ligne_periode(pdf, date_debut, date_fin)

    L = {"date": 24, "piece": 34, "jr": 20, "lib": 95, "d": 34, "c": 34, "s": 34}

    def entete():
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_fill_color(*BLEU); pdf.set_text_color(255, 255, 255)
        pdf.cell(L["date"], 8, "  " + t("recu_date"), fill=True)
        pdf.cell(L["piece"], 8, t("col_piece"), fill=True)
        pdf.cell(L["jr"], 8, t("col_journal_c"), fill=True)
        pdf.cell(L["lib"], 8, t("col_libelle"), fill=True)
        pdf.cell(L["d"], 8, t("col_debit"), fill=True, align="R")
        pdf.cell(L["c"], 8, t("col_credit"), fill=True, align="R")
        pdf.cell(L["s"], 8, t("col_solde"), fill=True, align="R", ln=1)

    entete()
    pdf.set_text_color(0, 0, 0); pdf.set_font("Helvetica", "", 8)
    alt = False
    compte_courant = None
    for l in lignes:
        # Titre de compte quand on change de compte (mode "tous les comptes")
        if l["compte"] != compte_courant:
            compte_courant = l["compte"]
            if not compte:
                pdf.ln(1)
                pdf.set_font("Helvetica", "B", 9)
                pdf.set_text_color(*BLEU)
                pdf.cell(0, 7, f"{l['compte']} - {l['intitule']}", ln=1)
                pdf.set_text_color(0, 0, 0); pdf.set_font("Helvetica", "", 8)
        if pdf.get_y() > pdf.h - 25:
            pdf.add_page(); entete()
            pdf.set_text_color(0, 0, 0); pdf.set_font("Helvetica", "", 8)
        pdf.set_fill_color(245, 245, 245) if alt else pdf.set_fill_color(255, 255, 255)
        alt = not alt
        pdf.cell(L["date"], 7, "  " + (l["date"] or ""), border="B", fill=True)
        pdf.cell(L["piece"], 7, (l["num_piece"] or "")[:20], border="B", fill=True)
        pdf.cell(L["jr"], 7, l["journal"] or "", border="B", fill=True)
        pdf.cell(L["lib"], 7, (l["libelle"] or "")[:60], border="B", fill=True)
        pdf.cell(L["d"], 7, formater_montant(l["debit"]) if l["debit"] else "", border="B", fill=True, align="R")
        pdf.cell(L["c"], 7, formater_montant(l["credit"]) if l["credit"] else "", border="B", fill=True, align="R")
        pdf.cell(L["s"], 7, formater_montant(l["solde"]), border="B", fill=True, align="R", ln=1)

    if not lignes:
        pdf.cell(0, 8, "  (Aucun mouvement)", ln=1)

    chemin = _chemin(f"GrandLivre_{compte or 'tous'}_{date_debut or ''}_{date_fin or ''}.pdf")
    pdf.output(chemin)
    if ouvrir:
        ouvrir_fichier(chemin)
    return chemin


# ===========================================================================
#  JOURNAL
# ===========================================================================
def generer_journal(journal_code, date_debut=None, date_fin=None, ouvrir=False):
    ecritures = co.lister_ecritures(journal_code, date_debut, date_fin)
    titre = f"JOURNAL {journal_code} - {co.libelle_journal(journal_code)}"
    pdf = _nouveau_doc(titre, paysage=True)
    _ligne_periode(pdf, date_debut, date_fin)

    L = {"date": 24, "piece": 32, "cpt": 22, "lib": 105, "d": 40, "c": 40}

    def entete():
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_fill_color(*BLEU); pdf.set_text_color(255, 255, 255)
        pdf.cell(L["date"], 8, "  " + t("recu_date"), fill=True)
        pdf.cell(L["piece"], 8, t("col_piece"), fill=True)
        pdf.cell(L["cpt"], 8, t("col_compte"), fill=True)
        pdf.cell(L["lib"], 8, t("col_libelle"), fill=True)
        pdf.cell(L["d"], 8, t("col_debit"), fill=True, align="R")
        pdf.cell(L["c"], 8, t("col_credit"), fill=True, align="R", ln=1)

    entete()
    pdf.set_text_color(0, 0, 0); pdf.set_font("Helvetica", "", 8)
    ttd = ttc = 0
    for e in ecritures:
        if pdf.get_y() > pdf.h - 25:
            pdf.add_page(); entete()
            pdf.set_text_color(0, 0, 0); pdf.set_font("Helvetica", "", 8)
        for i, l in enumerate(co.lignes_de_ecriture(e["id"])):
            pdf.cell(L["date"], 6, "  " + (e["date_ecriture"] or "") if i == 0 else "", border=0)
            pdf.cell(L["piece"], 6, (e["num_piece"] or "") if i == 0 else "", border=0)
            pdf.cell(L["cpt"], 6, l["compte"] or "", border=0)
            pdf.cell(L["lib"], 6, (l["libelle"] or "")[:65], border=0)
            pdf.cell(L["d"], 6, formater_montant(l["debit"]) if l["debit"] else "", border=0, align="R")
            pdf.cell(L["c"], 6, formater_montant(l["credit"]) if l["credit"] else "", border=0, align="R", ln=1)
            ttd += l["debit"] or 0; ttc += l["credit"] or 0
        pdf.set_draw_color(210, 210, 210)
        y = pdf.get_y()
        pdf.line(pdf.l_margin, y, pdf.w - pdf.r_margin, y)

    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 9); pdf.set_text_color(*BLEU)
    pdf.cell(L["date"] + L["piece"] + L["cpt"] + L["lib"], 8, "  TOTAUX", border="T")
    pdf.cell(L["d"], 8, formater_montant(ttd), border="T", align="R")
    pdf.cell(L["c"], 8, formater_montant(ttc), border="T", align="R", ln=1)

    chemin = _chemin(f"Journal_{journal_code}_{date_debut or ''}_{date_fin or ''}.pdf")
    pdf.output(chemin)
    if ouvrir:
        ouvrir_fichier(chemin)
    return chemin


# ===========================================================================
#  ÉTAT DE TRÉSORERIE (caisse / banque)
# ===========================================================================
def generer_etat_tresorerie(compte, date_debut=None, date_fin=None,
                            solde_initial=0, ouvrir=False):
    etat = co.etat_tresorerie(compte, date_debut, date_fin, solde_initial)
    intitule = co.intitule_compte(compte)
    pdf = _nouveau_doc(f"ETAT DE TRESORERIE - {compte} {intitule}".upper())
    _ligne_periode(pdf, date_debut, date_fin)

    def ligne(libelle, valeur, gras=False, couleur=(0, 0, 0)):
        pdf.set_font("Helvetica", "B" if gras else "", 11)
        pdf.set_text_color(80, 80, 80)
        pdf.cell(110, 9, libelle, border="B")
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(*couleur)
        pdf.cell(60, 9, formater_montant(valeur), border="B", align="R", ln=1)

    pdf.ln(4)
    ligne("Solde initial", etat["solde_initial"])
    ligne("Total encaissements (entrees)", etat["entrees"], couleur=(0, 130, 0))
    ligne("Total decaissements (sorties)", etat["sorties"], couleur=(180, 0, 0))
    pdf.ln(2)
    ligne("SOLDE FINAL", etat["solde_final"], gras=True, couleur=BLEU)

    chemin = _chemin(f"Tresorerie_{compte}_{date_debut or ''}_{date_fin or ''}.pdf")
    pdf.output(chemin)
    if ouvrir:
        ouvrir_fichier(chemin)
    return chemin


# ===========================================================================
#  COMPTE DE RÉSULTAT
# ===========================================================================
def generer_resultat(date_debut=None, date_fin=None, ouvrir=False):
    r = co.compte_de_resultat(date_debut, date_fin)
    pdf = _nouveau_doc(t("tab_resultat").upper())
    _ligne_periode(pdf, date_debut, date_fin)

    def bloc(titre, elements, total_libelle, total, couleur_total=BLEU):
        pdf.set_font("Helvetica", "B", 11); pdf.set_text_color(*BLEU)
        pdf.cell(0, 8, titre, ln=1)
        pdf.set_font("Helvetica", "", 10); pdf.set_text_color(0, 0, 0)
        for e in elements:
            pdf.cell(28, 7, "  " + e["compte"], border="B")
            pdf.cell(102, 7, (e["intitule"] or "")[:60], border="B")
            pdf.cell(40, 7, formater_montant(e["montant"]), border="B", align="R", ln=1)
        if not elements:
            pdf.cell(0, 7, "  (Aucun)", ln=1)
        pdf.set_font("Helvetica", "B", 10); pdf.set_text_color(*couleur_total)
        pdf.cell(130, 8, total_libelle, border="T")
        pdf.cell(40, 8, formater_montant(total), border="T", align="R", ln=1)
        pdf.ln(4)

    bloc(t("res_produits"), r["produits"], t("res_total_produits"), r["total_produits"])
    bloc(t("res_charges"), r["charges"], t("res_total_charges"), r["total_charges"])

    couleur = (0, 130, 0) if r["resultat"] >= 0 else (180, 0, 0)
    pdf.set_font("Helvetica", "B", 13); pdf.set_text_color(*couleur)
    pdf.cell(130, 11, t("res_resultat"), border="T")
    pdf.cell(40, 11, formater_montant(r["resultat"]), border="T", align="R", ln=1)

    chemin = _chemin(f"Resultat_{date_debut or ''}_{date_fin or ''}.pdf")
    pdf.output(chemin)
    if ouvrir:
        ouvrir_fichier(chemin)
    return chemin


# ===========================================================================
#  BILAN
# ===========================================================================
def generer_bilan(date_debut=None, date_fin=None, ouvrir=False):
    b = co.bilan(date_debut, date_fin)
    pdf = _nouveau_doc(t("tab_bilan").upper())
    _ligne_periode(pdf, date_debut, date_fin)

    def bloc(titre, elements, total_libelle, total):
        pdf.set_font("Helvetica", "B", 11); pdf.set_text_color(*BLEU)
        pdf.cell(0, 8, titre, ln=1)
        pdf.set_font("Helvetica", "", 10); pdf.set_text_color(0, 0, 0)
        for e in elements:
            pdf.cell(28, 7, "  " + e["compte"], border="B")
            pdf.cell(102, 7, (e["intitule"] or "")[:60], border="B")
            pdf.cell(40, 7, formater_montant(e["montant"]), border="B", align="R", ln=1)
        if not elements:
            pdf.cell(0, 7, "  (Aucun)", ln=1)
        pdf.set_font("Helvetica", "B", 11); pdf.set_text_color(*BLEU)
        pdf.cell(130, 8, total_libelle, border="T")
        pdf.cell(40, 8, formater_montant(total), border="T", align="R", ln=1)
        pdf.ln(6)

    bloc(t("bilan_actif"), b["actif"], t("bilan_total_actif"), b["total_actif"])
    bloc(t("bilan_passif"), b["passif"], t("bilan_total_passif"), b["total_passif"])

    chemin = _chemin(f"Bilan_{date_debut or ''}_{date_fin or ''}.pdf")
    pdf.output(chemin)
    if ouvrir:
        ouvrir_fichier(chemin)
    return chemin
