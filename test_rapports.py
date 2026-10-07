# -*- coding: utf-8 -*-
"""
test_rapports.py
----------------
Teste Documents (Et.16), Recherche globale (§18) et Rapports/Tableau de bord
(Et.14-15) sur une copie reconstruite depuis la sauvegarde.

Methode : on mesure l'ECART (avant/apres ajout) pour ne pas dependre des
vraies donnees deja datees d'aujourd'hui.
"""
import os
import sqlite3
from datetime import datetime

BACKUP = os.path.join(os.path.expanduser("~"), "Documents",
                      "SAUVEGARDE-AVANT-REORGANISATION-2026-09-11", "aplm.db")
COPIE = os.path.join(os.path.dirname(__file__), "data", "aplm_travail.db")

for suf in ("", "-wal", "-shm"):
    if os.path.exists(COPIE + suf):
        os.remove(COPIE + suf)
_s = sqlite3.connect(BACKUP); _d = sqlite3.connect(COPIE)
with _d:
    _s.backup(_d)
_d.close(); _s.close()

import config
config.DB_PATH = COPIE
import database as db
import activites as act
import banque as bq
import documents as docs
import recherche as rech
import rapports as rap

act.initialiser(); bq.initialiser(); docs.initialiser()
act.migrer_reservations_vers_activites()

OK = KO = 0
def verifier(nom, cond, detail=""):
    global OK, KO
    if cond:
        OK += 1; print(f"  [OK]  {nom}" + (f"  ({detail})" if detail else ""))
    else:
        KO += 1; print(f"  [!!]  ECHEC : {nom}" + (f"  ({detail})" if detail else ""))

today = datetime.now().strftime("%Y-%m-%d")

# --- MESURE DE REFERENCE (avant d'ajouter quoi que ce soit) ---
base = rap.rapport(today, today)
base_tb = rap.tableau_de_bord()

# --- Donnees de test datees AUJOURD'HUI ---
cli = db.creer_client(nom="RAPPORT", prenom="Test", telephone="771234567")
billet = act.creer_operation("billet", cli, {
    "passager": "Test RAPPORT", "pnr": "ZZPNR9", "compagnie": "AF",
    "prix_fournisseur": 400000, "prix_client": 500000,
    "frais_service": 20000, "reduction": 10000, "tva_taux": 18})
act.creer_paiement_operation("billet", billet, 300000, mode="Espèces")
compte = bq.creer_compte("Caisse test", solde_initial=0)
bq.creer_versement(compte, 300000, origine="Encaissement client", client_id=cli)

print("=" * 68)
print("§18 - RECHERCHE GLOBALE")
r = rech.rechercher("ZZPNR9")
verifier("billet trouve par PNR", len(r["billets"]) == 1,
         r["billets"][0]["pnr"] if r["billets"] else "")
r2 = rech.rechercher("RAPPORT")
verifier("client trouve par nom", any(c["nom"] == "RAPPORT" for c in r2["clients"]))
verifier("compteur global > 0", rech.compter(r2) > 0, rech.compter(r2))

print("=" * 68)
print("ETAPE 16 - DOCUMENTS")
tmp = os.path.join(config.DATA_DIR, "piece_test.txt")
with open(tmp, "w", encoding="utf-8") as f:
    f.write("justificatif de test")
docs.enregistrer_document(tmp, categorie="Facture", nom="Facture test",
                          operation_type="billet", operation_id=billet, client_id=cli)
liste = docs.lister_documents(operation_type="billet", operation_id=billet)
verifier("document rattache a l'operation", len(liste) == 1)
verifier("fichier copie dans le dossier documents",
         bool(liste) and os.path.exists(liste[0]["chemin"]))

print("=" * 68)
print("ETAPE 14 - RAPPORT DU JOUR (mesure de l'ECART apres ajout)")
rj = rap.rapport(today, today)
verifier("+1 billet aujourd'hui", rj["nb_billets"] - base["nb_billets"] == 1)
verifier("CA +510 000", rj["chiffre_affaires"] - base["chiffre_affaires"] == 510000,
         rj["chiffre_affaires"] - base["chiffre_affaires"])
verifier("encaissements +300 000",
         rj["encaissements"] - base["encaissements"] == 300000)
verifier("creances +210 000", rj["creances"] - base["creances"] == 210000)
verifier("marge +110 000", rj["marge"] - base["marge"] == 110000)
verifier("versements banque +300 000",
         rj["versements_bancaires"] - base["versements_bancaires"] == 300000)

print("=" * 68)
print("ETAPE 15 - TABLEAU DE BORD (donnees reelles)")
tb = rap.tableau_de_bord()
verifier("CA du jour +510 000", tb["ca_jour"] - base_tb["ca_jour"] == 510000,
         tb["ca_jour"] - base_tb["ca_jour"])
verifier("nb billets global +1", tb["nb_billets"] - base_tb["nb_billets"] == 1,
         tb["nb_billets"])
verifier("nb assurances global = 6", tb["nb_assurances"] == 6, tb["nb_assurances"])
verifier("paiements en attente >= 1", tb["paiements_en_attente"] >= 1,
         tb["paiements_en_attente"])
verifier("solde bancaire = 300 000", tb["solde_bancaire"] == 300000,
         tb["solde_bancaire"])

print("=" * 68)
print(f"RESULTAT : {OK} test(s) OK, {KO} echec(s).")
print("=" * 68)
