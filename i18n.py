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

    # --- Avoir (cagnotte client) ---
    "menu_avoir":       {"fr": "Avoir", "en": "Store credit"},
    "avoir_titre":      {"fr": "Avoirs des clients (cagnotte)",
                          "en": "Client store credit"},
    "avoir_intro":      {"fr": "Enregistrez ici l'argent qu'un client verse "
                               "petit à petit, jusqu'à réunir la somme pour "
                               "payer son voyage. Choisissez un client pour "
                               "voir sa cagnotte.",
                          "en": "Record here the money a client deposits little "
                               "by little, until they have enough to pay for "
                               "their trip. Pick a client to see their credit."},
    "avoir_solde":      {"fr": "Solde de la cagnotte", "en": "Credit balance"},
    "avoir_depots":     {"fr": "Total déposé", "en": "Total deposited"},
    "avoir_utilises":   {"fr": "Total utilisé", "en": "Total used"},
    "avoir_depot":      {"fr": "Dépôt", "en": "Deposit"},
    "avoir_utilisation":{"fr": "Utilisation", "en": "Use"},
    "avoir_ajouter_depot": {"fr": "Ajouter un dépôt", "en": "Add a deposit"},
    "avoir_utiliser":   {"fr": "Utiliser l'avoir pour payer un dossier",
                          "en": "Use credit to pay a file"},
    "avoir_choisir_client": {"fr": "Client", "en": "Client"},
    "avoir_aucun_client": {"fr": "Aucun client. Créez d'abord un client.",
                            "en": "No client yet. Create a client first."},
    "avoir_aucun_dossier": {"fr": "Ce client n'a aucun dossier à payer.",
                             "en": "This client has no file to pay."},
    "avoir_choisir_dossier": {"fr": "Dossier à payer", "en": "File to pay"},
    "avoir_montant_trop_grand": {"fr": "Le montant dépasse le solde disponible "
                                       "de la cagnotte.",
                                  "en": "Amount is greater than the available "
                                       "credit balance."},
    "avoir_depot_ok":   {"fr": "Dépôt enregistré.", "en": "Deposit saved."},
    "avoir_utilisation_ok": {"fr": "Avoir utilisé pour payer le dossier.",
                              "en": "Credit used to pay the file."},
    "col_type":         {"fr": "Type", "en": "Type"},

    # --- Permissions détaillées (par agent) ---
    "perm_titre":       {"fr": "Permissions (pour un agent)",
                          "en": "Permissions (for an agent)"},
    "perm_note_admin":  {"fr": "Un administrateur a automatiquement toutes "
                               "les permissions.",
                          "en": "An administrator automatically has all "
                               "permissions."},
    "perm_gerer_clients": {"fr": "Gérer les clients (créer / modifier)",
                            "en": "Manage clients (create / edit)"},
    "perm_gerer_dossiers": {"fr": "Gérer les dossiers et réservations",
                             "en": "Manage files and bookings"},
    "perm_encaisser_paiements": {"fr": "Encaisser des paiements",
                                  "en": "Record payments"},
    "perm_generer_recus": {"fr": "Générer les reçus PDF",
                            "en": "Generate PDF receipts"},
    "perm_gerer_avoirs": {"fr": "Gérer les avoirs (cagnotte)",
                           "en": "Manage store credit"},
    "perm_gerer_depenses": {"fr": "Gérer les dépenses",
                             "en": "Manage expenses"},
    "perm_voir_finances": {"fr": "Voir les finances (bénéfices, transactions)",
                            "en": "See finances (profit, transactions)"},
    "perm_voir_comptabilite": {"fr": "Voir la comptabilité",
                                "en": "See accounting"},
    "perm_supprimer":   {"fr": "Supprimer des éléments (clients, dossiers...)",
                          "en": "Delete items (clients, files...)"},
    "msg_permission_refusee": {"fr": "Vous n'avez pas la permission de faire "
                                     "cette action.",
                                "en": "You do not have permission to do this."},

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

    # --- Connexion / Multi-utilisateurs ---
    "menu_utilisateurs": {"fr": "Utilisateurs", "en": "Users"},
    "menu_journal":      {"fr": "Journal des activités", "en": "Activity log"},
    "btn_deconnexion":   {"fr": "Déconnexion", "en": "Log out"},
    "lbl_connecte":      {"fr": "Connecté", "en": "Signed in"},

    "login_titre":       {"fr": "Connexion", "en": "Sign in"},
    "login_intro":       {"fr": "Veuillez vous connecter pour accéder au logiciel.",
                          "en": "Please sign in to access the software."},
    "login_bouton":      {"fr": "Se connecter", "en": "Sign in"},
    "login_echec":       {"fr": "Connexion impossible", "en": "Sign-in failed"},

    "firstrun_titre":    {"fr": "Bienvenue — Première utilisation",
                          "en": "Welcome — First use"},
    "firstrun_intro":    {"fr": "Créez le compte ADMINISTRATEUR de l'agence. "
                                "C'est le compte principal qui pourra ensuite "
                                "créer les comptes des agents.",
                          "en": "Create the agency ADMINISTRATOR account. "
                                "This main account will then be able to "
                                "create the agents' accounts."},
    "firstrun_creer":    {"fr": "Créer l'administrateur", "en": "Create administrator"},

    "champ_identifiant": {"fr": "Identifiant de connexion", "en": "Login username"},
    "champ_mdp":         {"fr": "Mot de passe", "en": "Password"},
    "champ_mdp_confirm": {"fr": "Confirmer le mot de passe", "en": "Confirm password"},
    "champ_role":        {"fr": "Rôle", "en": "Role"},
    "champ_actif":       {"fr": "Compte actif", "en": "Active account"},
    "role_admin":        {"fr": "Administrateur", "en": "Administrator"},
    "role_agent":        {"fr": "Agent", "en": "Agent"},

    # --- Écran Utilisateurs (admin) ---
    "users_titre":       {"fr": "Gestion des utilisateurs", "en": "User management"},
    "users_intro":       {"fr": "Créez et gérez les comptes des agents. "
                                "Seul l'administrateur voit cet écran.",
                          "en": "Create and manage agent accounts. "
                                "Only the administrator sees this screen."},
    "btn_nouvel_utilisateur": {"fr": "Nouvel utilisateur", "en": "New user"},
    "btn_changer_mdp":   {"fr": "Changer le mot de passe", "en": "Change password"},
    "btn_reinit_mdp":    {"fr": "Réinitialiser (mot de passe oublié)",
                          "en": "Reset (forgot password)"},
    "msg_reinit_ok":     {"fr": "Mot de passe réinitialisé à « {mdp} ». "
                                "L'utilisateur devra le changer à sa prochaine connexion.",
                          "en": "Password reset to \"{mdp}\". The user will have to "
                                "change it at next login."},
    "btn_activer":       {"fr": "Activer", "en": "Enable"},
    "btn_desactiver":    {"fr": "Désactiver", "en": "Disable"},
    "col_role":          {"fr": "Rôle", "en": "Role"},
    "col_statut":        {"fr": "Statut", "en": "Status"},
    "statut_actif":      {"fr": "Actif", "en": "Active"},
    "statut_inactif":    {"fr": "Inactif", "en": "Inactive"},
    "titre_nouvel_utilisateur": {"fr": "Nouvel utilisateur", "en": "New user"},
    "titre_modifier_utilisateur": {"fr": "Modifier l'utilisateur", "en": "Edit user"},
    "titre_changer_mdp": {"fr": "Changer le mot de passe", "en": "Change password"},
    "champ_nouveau_mdp": {"fr": "Nouveau mot de passe", "en": "New password"},

    # --- Écran Journal des activités (admin) ---
    "journal_titre":     {"fr": "Journal des activités", "en": "Activity log"},
    "journal_intro":     {"fr": "Historique des actions effectuées dans le logiciel "
                                "(qui a fait quoi, et quand).",
                          "en": "History of actions performed in the software "
                                "(who did what, and when)."},
    "col_date_heure":    {"fr": "Date et heure", "en": "Date & time"},
    "col_utilisateur":   {"fr": "Utilisateur", "en": "User"},
    "col_action":        {"fr": "Action", "en": "Action"},
    "col_objet":         {"fr": "Objet", "en": "Object"},
    "col_details":       {"fr": "Détails", "en": "Details"},

    # --- Messages multi-utilisateurs ---
    "msg_champs_requis": {"fr": "Veuillez remplir tous les champs obligatoires.",
                          "en": "Please fill in all required fields."},
    "msg_mdp_differents": {"fr": "Les deux mots de passe ne sont pas identiques.",
                           "en": "The two passwords do not match."},
    "msg_mdp_court":     {"fr": "Le mot de passe doit contenir au moins 4 caractères.",
                          "en": "The password must be at least 4 characters long."},
    "msg_utilisateur_cree": {"fr": "Compte créé avec succès.", "en": "Account created successfully."},
    "msg_mdp_change":    {"fr": "Mot de passe modifié avec succès.", "en": "Password changed successfully."},
    "msg_dernier_admin": {"fr": "Impossible : il doit rester au moins un "
                                "administrateur actif.",
                          "en": "Not allowed: at least one active administrator "
                                "must remain."},
    "msg_pas_soi_meme":  {"fr": "Vous ne pouvez pas désactiver votre propre compte.",
                          "en": "You cannot disable your own account."},
    "msg_acces_refuse":  {"fr": "Accès réservé à l'administrateur.",
                          "en": "Access restricted to the administrator."},

    # === COMPTABILITÉ ======================================================
    "menu_comptabilite": {"fr": "Comptabilité", "en": "Accounting"},
    "menu_depenses":     {"fr": "Dépenses / Décaissements", "en": "Expenses / Payouts"},
    "compta_titre":      {"fr": "Comptabilité SYSCOHADA / OHADA", "en": "SYSCOHADA / OHADA accounting"},
    "compta_intro":      {"fr": "La comptabilité se met à jour automatiquement à partir "
                                "de vos ventes, encaissements et dépenses. Aucune double saisie.",
                          "en": "Accounting updates automatically from your sales, "
                                "collections and expenses. No double entry."},
    "btn_maj_compta":    {"fr": "Mettre à jour la comptabilité", "en": "Update accounting"},
    "msg_compta_maj":    {"fr": "Comptabilité mise à jour :", "en": "Accounting updated:"},
    "msg_compta_ecritures": {"fr": "écritures générées.", "en": "entries generated."},

    # --- Onglets ---
    "tab_tdb":           {"fr": "Tableau de bord", "en": "Dashboard"},
    "tab_journal":       {"fr": "Journaux", "en": "Journals"},
    "tab_grand_livre":   {"fr": "Grand Livre", "en": "General ledger"},
    "tab_balance":       {"fr": "Balance", "en": "Trial balance"},
    "tab_caisse":        {"fr": "Caisse / Banque", "en": "Cash / Bank"},
    "tab_resultat":      {"fr": "Compte de résultat", "en": "Income statement"},
    "tab_bilan":         {"fr": "Bilan", "en": "Balance sheet"},
    "tab_tva":           {"fr": "TVA", "en": "VAT"},
    "tab_plan":          {"fr": "Plan comptable", "en": "Chart of accounts"},
    "tab_ecritures":     {"fr": "Écritures (OD)", "en": "Entries (misc.)"},
    "tab_exercices":     {"fr": "Exercices", "en": "Fiscal years"},

    # --- Colonnes comptables ---
    "col_compte":        {"fr": "N° compte", "en": "Account"},
    "col_intitule":      {"fr": "Intitulé", "en": "Label"},
    "col_debit":         {"fr": "Débit", "en": "Debit"},
    "col_credit":        {"fr": "Crédit", "en": "Credit"},
    "col_solde":         {"fr": "Solde", "en": "Balance"},
    "col_piece":         {"fr": "N° pièce", "en": "Voucher"},
    "col_journal_c":     {"fr": "Journal", "en": "Journal"},
    "col_libelle":       {"fr": "Libellé", "en": "Description"},
    "col_classe":        {"fr": "Classe", "en": "Class"},
    "col_solde_d":       {"fr": "Solde débiteur", "en": "Debit balance"},
    "col_solde_c":       {"fr": "Solde créditeur", "en": "Credit balance"},
    "col_nature":        {"fr": "Nature", "en": "Type"},

    # --- Tableau de bord comptable ---
    "tdb_ca":            {"fr": "Chiffre d'affaires", "en": "Revenue"},
    "tdb_produits":      {"fr": "Total produits", "en": "Total income"},
    "tdb_charges":       {"fr": "Total charges", "en": "Total expenses"},
    "tdb_resultat":      {"fr": "Résultat (bénéfice)", "en": "Result (profit)"},
    "tdb_caisse":        {"fr": "Solde caisse", "en": "Cash balance"},
    "tdb_banque":        {"fr": "Solde banque", "en": "Bank balance"},
    "tdb_creances":      {"fr": "Créances clients", "en": "Receivables"},
    "tdb_dettes":        {"fr": "Dettes fournisseurs", "en": "Payables"},

    # --- Résultat / Bilan / TVA ---
    "res_charges":       {"fr": "CHARGES (classe 6)", "en": "EXPENSES (class 6)"},
    "res_produits":      {"fr": "PRODUITS (classe 7)", "en": "INCOME (class 7)"},
    "res_total_charges": {"fr": "Total charges", "en": "Total expenses"},
    "res_total_produits":{"fr": "Total produits", "en": "Total income"},
    "res_resultat":      {"fr": "RÉSULTAT NET", "en": "NET RESULT"},
    "bilan_actif":       {"fr": "ACTIF", "en": "ASSETS"},
    "bilan_passif":      {"fr": "PASSIF", "en": "LIABILITIES"},
    "bilan_total_actif": {"fr": "Total actif", "en": "Total assets"},
    "bilan_total_passif":{"fr": "Total passif", "en": "Total liabilities"},
    "tva_collectee":     {"fr": "TVA collectée", "en": "VAT collected"},
    "tva_deductible":    {"fr": "TVA déductible", "en": "Deductible VAT"},
    "tva_a_payer":       {"fr": "TVA à payer", "en": "VAT payable"},
    "tva_credit":        {"fr": "Crédit de TVA", "en": "VAT credit"},
    "tva_note":          {"fr": "Aucun taux n'est appliqué automatiquement "
                                "(paramétrable selon la réglementation).",
                          "en": "No rate is applied automatically "
                                "(configurable per regulation)."},

    # --- Dépenses / Décaissements ---
    "dep_titre":         {"fr": "Dépenses / Décaissements", "en": "Expenses / Payouts"},
    "dep_intro":         {"fr": "Enregistrez ici les sorties d'argent (loyer, salaires, "
                                "paiement fournisseurs, frais divers...).",
                          "en": "Record money going out here (rent, salaries, "
                                "supplier payments, misc. costs...)."},
    "champ_beneficiaire":{"fr": "Bénéficiaire / Fournisseur", "en": "Payee / Supplier"},
    "champ_motif":       {"fr": "Motif", "en": "Reason"},
    "champ_compte_charge":{"fr": "Compte comptable", "en": "Account"},
    "champ_date_depense":{"fr": "Date", "en": "Date"},
    "col_beneficiaire":  {"fr": "Bénéficiaire", "en": "Payee"},
    "col_motif":         {"fr": "Motif", "en": "Reason"},

    # --- Exercices ---
    "exo_titre":         {"fr": "Exercices comptables", "en": "Fiscal years"},
    "champ_libelle":     {"fr": "Libellé (ex: Exercice 2026)", "en": "Label (e.g. 2026)"},
    "col_cloture":       {"fr": "État", "en": "Status"},
    "exo_ouvert":        {"fr": "Ouvert", "en": "Open"},
    "exo_cloture":       {"fr": "Clôturé", "en": "Closed"},
    "btn_nouvel_exercice":{"fr": "Nouvel exercice", "en": "New fiscal year"},
    "btn_cloturer":      {"fr": "Clôturer", "en": "Close"},
    "btn_rouvrir":       {"fr": "Rouvrir", "en": "Reopen"},
    "btn_nouvelle_ecriture": {"fr": "Nouvelle écriture (OD)", "en": "New entry (misc.)"},
    "msg_exo_cloture":   {"fr": "Exercice clôturé (lecture seule).", "en": "Fiscal year closed (read-only)."},
    "tous_les_comptes":  {"fr": "Tous les comptes", "en": "All accounts"},
    "tous_journaux":     {"fr": "Tous les journaux", "en": "All journals"},

    # --- Mot de passe par défaut + changement obligatoire ---
    "mdp_defaut_info":   {"fr": "Ce compte sera créé avec le mot de passe par "
                                "défaut « {mdp} ». L'utilisateur devra le changer "
                                "à sa première connexion.",
                          "en": "This account will be created with the default "
                                "password \"{mdp}\". The user will have to change "
                                "it at first login."},
    "chg_titre":         {"fr": "Changement de mot de passe obligatoire",
                          "en": "Password change required"},
    "chg_intro":         {"fr": "Pour votre sécurité, veuillez choisir un nouveau "
                                "mot de passe personnel avant d'accéder au logiciel.",
                          "en": "For your security, please choose a new personal "
                                "password before accessing the software."},
    "chg_valider":       {"fr": "Changer et continuer", "en": "Change and continue"},
    "msg_mdp_egal_defaut": {"fr": "Choisissez un mot de passe DIFFÉRENT du mot de "
                                  "passe par défaut.",
                            "en": "Choose a password DIFFERENT from the default one."},
    "msg_chg_obligatoire": {"fr": "Vous devez changer votre mot de passe pour "
                                  "continuer.",
                            "en": "You must change your password to continue."},
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
