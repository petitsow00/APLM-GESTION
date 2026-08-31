# -*- coding: utf-8 -*-
"""
i18n.py
--------
Gère les traductions Français / Anglais de l'interface.

Fonctionnement très simple :
  - TEXTES contient tous les libellés dans les deux langues.
  - On appelle t("clé") pour obtenir le texte dans la langue active.
  - definir_langue("en") ou definir_langue("fr") change la langue.
"""

import config

# Langue actuellement active (au démarrage = celle de config)
_langue_active = config.LANGUE_DEFAUT

TEXTES = {
    # --- Général / navigation ---
    "app_titre":        {"fr": "Gestion Agence de Voyages",
                          "en": "Travel Agency Manager"},
    "menu_dashboard":   {"fr": "Tableau de bord", "en": "Dashboard"},
    "menu_clients":     {"fr": "Clients", "en": "Clients"},
    "menu_dossiers":    {"fr": "Dossiers", "en": "Files"},
    "menu_paiements":   {"fr": "Paiements", "en": "Payments"},
    "menu_parametres":  {"fr": "Réglages", "en": "Settings"},
    "menu_langue":      {"fr": "Langue", "en": "Language"},
    "menu_quitter":     {"fr": "Quitter", "en": "Quit"},

    # --- Écran Réglages ---
    "param_titre":      {"fr": "Réglages de l'agence", "en": "Agency settings"},
    "param_intro":      {"fr": "Renseignez ici les informations de votre agence. "
                               "Elles apparaîtront sur les reçus.",
                          "en": "Enter your agency information here. "
                               "It will appear on the receipts."},
    "champ_nom_agence": {"fr": "Nom de l'agence", "en": "Agency name"},
    "champ_slogan":     {"fr": "Slogan / activité", "en": "Slogan / activity"},
    "champ_site":       {"fr": "Site web", "en": "Website"},
    "champ_rccm":       {"fr": "RCCM / N° registre", "en": "Business reg. No."},
    "champ_devise":     {"fr": "Monnaie", "en": "Currency"},
    "param_logo":       {"fr": "Logo (apparaît sur les reçus)", "en": "Logo (shown on receipts)"},
    "param_choisir_logo": {"fr": "Choisir une image...", "en": "Choose an image..."},
    "param_logo_actuel": {"fr": "Logo actuel : présent", "en": "Current logo: set"},
    "param_logo_absent": {"fr": "Aucun logo pour l'instant", "en": "No logo yet"},
    "param_logo_ok":    {"fr": "Logo enregistré.", "en": "Logo saved."},
    "msg_param_ok":     {"fr": "Réglages enregistrés avec succès.", "en": "Settings saved successfully."},
    "msg_nom_requis":   {"fr": "Veuillez d'abord renseigner le nom de l'agence "
                               "dans l'écran Réglages avant de générer un reçu.",
                          "en": "Please set the agency name in Settings "
                               "before generating a receipt."},

    # --- Boutons communs ---
    "btn_ajouter":      {"fr": "Ajouter", "en": "Add"},
    "btn_modifier":     {"fr": "Modifier", "en": "Edit"},
    "btn_supprimer":    {"fr": "Supprimer", "en": "Delete"},
    "btn_enregistrer":  {"fr": "Enregistrer", "en": "Save"},
    "btn_annuler":      {"fr": "Annuler", "en": "Cancel"},
    "btn_rechercher":   {"fr": "Rechercher", "en": "Search"},
    "btn_actualiser":   {"fr": "Actualiser", "en": "Refresh"},
    "btn_recu_pdf":     {"fr": "Générer reçu PDF", "en": "Generate PDF receipt"},
    "btn_ouvrir":       {"fr": "Ouvrir", "en": "Open"},
    "btn_retour":       {"fr": "Retour", "en": "Back"},

    # --- Champs clients ---
    "col_code":         {"fr": "Code", "en": "Code"},
    "champ_nom":        {"fr": "Nom", "en": "Last name"},
    "champ_prenom":     {"fr": "Prénom", "en": "First name"},
    "champ_telephone":  {"fr": "Téléphone", "en": "Phone"},
    "champ_email":      {"fr": "E-mail", "en": "Email"},
    "champ_adresse":    {"fr": "Adresse", "en": "Address"},
    "champ_type_piece": {"fr": "Type de pièce", "en": "ID type"},
    "champ_num_piece":  {"fr": "N° de pièce", "en": "ID number"},
    "champ_notes":      {"fr": "Notes", "en": "Notes"},

    # --- Champs dossiers / réservations ---
    "champ_reference":  {"fr": "Référence", "en": "Reference"},
    "champ_client":     {"fr": "Client", "en": "Client"},
    "champ_titre":      {"fr": "Titre du dossier", "en": "File title"},
    "champ_statut":     {"fr": "Statut", "en": "Status"},
    "champ_type_billet":{"fr": "Type", "en": "Type"},
    "champ_compagnie":  {"fr": "Compagnie", "en": "Airline"},
    "champ_pnr":        {"fr": "PNR", "en": "PNR"},
    "champ_num_billet": {"fr": "N° billet", "en": "Ticket No."},
    "champ_passager":   {"fr": "Passager", "en": "Passenger"},
    "champ_depart":     {"fr": "Départ (ville)", "en": "From (city)"},
    "champ_arrivee":    {"fr": "Arrivée (ville)", "en": "To (city)"},
    "champ_date_depart":{"fr": "Date départ", "en": "Departure date"},
    "champ_date_retour":{"fr": "Date retour", "en": "Return date"},
    "champ_classe":     {"fr": "Classe", "en": "Class"},
    "champ_gds":        {"fr": "GDS (interne)", "en": "GDS (internal)"},
    "champ_consolidateur": {"fr": "Consolidateur (interne)", "en": "Consolidator (internal)"},
    "champ_prix_achat": {"fr": "Prix d'achat (interne)", "en": "Cost price (internal)"},
    "champ_prix_vente": {"fr": "Prix de vente", "en": "Sale price"},

    # --- Champs paiements ---
    "champ_montant":    {"fr": "Montant", "en": "Amount"},
    "champ_mode":       {"fr": "Mode de paiement", "en": "Payment method"},
    "champ_date_paiement": {"fr": "Date paiement", "en": "Payment date"},

    # --- Soldes / résumés ---
    "lbl_total_vente":  {"fr": "Total à payer", "en": "Total due"},
    "lbl_total_paye":   {"fr": "Total payé", "en": "Total paid"},
    "lbl_solde":        {"fr": "Solde restant", "en": "Balance"},
    "lbl_reservations": {"fr": "Réservations / Billets", "en": "Bookings / Tickets"},
    "lbl_paiements":    {"fr": "Paiements", "en": "Payments"},

    # --- Tableau de bord ---
    "dash_clients":     {"fr": "Clients", "en": "Clients"},
    "dash_dossiers":    {"fr": "Dossiers", "en": "Files"},
    "dash_ca":          {"fr": "Chiffre d'affaires", "en": "Revenue"},
    "dash_encaisse":    {"fr": "Encaissé", "en": "Collected"},
    "dash_solde":       {"fr": "Reste à encaisser", "en": "Outstanding"},
    "dash_benefice":    {"fr": "Bénéfice", "en": "Profit"},
    "dash_bienvenue":   {"fr": "Bienvenue", "en": "Welcome"},

    # --- Historique clients (liste PDF) ---
    "menu_hist_clients":  {"fr": "Historique clients", "en": "Client history"},
    "hist_clients_titre": {"fr": "Historique clients", "en": "Client history"},
    "hist_clients_intro": {"fr": "Générez la liste complète de tous les clients "
                                 "enregistrés dans un document PDF professionnel.",
                           "en": "Generate the full list of all registered clients "
                                 "as a professional PDF document."},
    "btn_liste_clients_pdf": {"fr": "Générer la liste des clients PDF",
                              "en": "Generate clients list PDF"},
    "pdf_liste_clients_titre": {"fr": "LISTE DES CLIENTS", "en": "CLIENTS LIST"},
    "col_num":            {"fr": "N°", "en": "No."},
    "col_nom_prenom":     {"fr": "Nom et prénom", "en": "Full name"},
    "col_date_enreg":     {"fr": "Date d'enregistrement", "en": "Registration date"},

    # --- Historique transactions (période + PDF) ---
    "menu_hist_transac":  {"fr": "Historique transactions", "en": "Transaction history"},
    "hist_transac_titre": {"fr": "Historique des transactions", "en": "Transaction history"},
    "hist_transac_intro": {"fr": "Choisissez une période, affichez les transactions, "
                                 "puis générez le PDF.",
                           "en": "Choose a period, display the transactions, "
                                 "then generate the PDF."},
    "champ_date_debut":   {"fr": "Date de début", "en": "Start date"},
    "champ_date_fin":     {"fr": "Date de fin", "en": "End date"},
    "btn_afficher":       {"fr": "Afficher", "en": "Show"},
    "btn_generer_pdf":    {"fr": "Générer PDF", "en": "Generate PDF"},
    "pdf_transac_titre":  {"fr": "HISTORIQUE DES TRANSACTIONS", "en": "TRANSACTION HISTORY"},
    "col_type_op":        {"fr": "Type d'opération", "en": "Operation type"},
    "col_benefice":       {"fr": "Bénéfice", "en": "Profit"},
    "type_vente":         {"fr": "Vente", "en": "Sale"},
    "type_encaissement":  {"fr": "Encaissement", "en": "Payment"},
    "lbl_periode":        {"fr": "Période", "en": "Period"},
    "lbl_total_ventes":   {"fr": "Total des ventes", "en": "Total sales"},
    "lbl_total_encaisse": {"fr": "Total des encaissements", "en": "Total collected"},
    "lbl_total_achats":   {"fr": "Total des coûts d'achat", "en": "Total purchase cost"},
    "lbl_total_benefice": {"fr": "Total des bénéfices", "en": "Total profit"},
    "lbl_total_restant":  {"fr": "Total restant à payer", "en": "Total outstanding"},
    "msg_aucune_transac": {"fr": "Aucune transaction sur cette période.",
                           "en": "No transaction in this period."},
    "msg_dates_invalides": {"fr": "Veuillez saisir des dates valides "
                                  "(la date de début doit précéder la date de fin).",
                            "en": "Please enter valid dates "
                                  "(start date must be before end date)."},
    "msg_pdf_genere":     {"fr": "PDF généré :", "en": "PDF generated:"},
    "msg_aucun_client":   {"fr": "Aucun client à imprimer.", "en": "No client to print."},

    # --- Messages ---
    "msg_champ_requis": {"fr": "Le nom est obligatoire.", "en": "Name is required."},
    "msg_confirmer_suppr": {"fr": "Confirmer la suppression ?", "en": "Confirm deletion?"},
    "msg_enregistre":   {"fr": "Enregistré avec succès.", "en": "Saved successfully."},
    "msg_selectionner": {"fr": "Veuillez sélectionner un élément.", "en": "Please select an item."},
    "msg_recu_genere":  {"fr": "Reçu généré :", "en": "Receipt generated:"},
    "msg_montant_invalide": {"fr": "Montant invalide.", "en": "Invalid amount."},

    # --- Reçu PDF ---
    "recu_titre":       {"fr": "REÇU DE PAIEMENT", "en": "PAYMENT RECEIPT"},
    "recu_no":          {"fr": "Reçu N°", "en": "Receipt No."},
    "recu_date":        {"fr": "Date", "en": "Date"},
    "recu_client":      {"fr": "Client", "en": "Client"},
    "recu_designation": {"fr": "Désignation", "en": "Description"},
    "recu_montant":     {"fr": "Montant", "en": "Amount"},
    "recu_merci":       {"fr": "Merci de votre confiance.", "en": "Thank you for your trust."},
    "recu_signature":   {"fr": "Signature & Cachet", "en": "Signature & Stamp"},
}


def definir_langue(code):
    """Change la langue active ('fr' ou 'en')."""
    global _langue_active
    if code in ("fr", "en"):
        _langue_active = code


def langue_active():
    return _langue_active


def t(cle):
    """Renvoie le texte correspondant à la clé, dans la langue active.
    Si la clé n'existe pas, renvoie la clé elle-même (pour repérer les oublis)."""
    entree = TEXTES.get(cle)
    if not entree:
        return cle
    return entree.get(_langue_active, entree.get("fr", cle))
