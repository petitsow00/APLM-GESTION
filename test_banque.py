# -*- coding: utf-8 -*-
"""
test_banque.py
--------------
Teste le module Banque (Etape 12) + le test anti-double-comptage du §20,
sur une copie reconstruite depuis la sauvegarde. N'ecrit que sur aplm_travail.db.
"""
import os
import sqlite3

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

act.initialiser()
bq.initialiser()

OK = KO = 0
def verifier(nom, cond, detail=""):
    global OK, KO
    if cond:
        OK += 1; print(f"  [OK]  {nom}" + (f"  ({detail})" if detail else ""))
    else:
        KO += 1; print(f"  [!!]  ECHEC : {nom}" + (f"  ({detail})" if detail else ""))


print("=" * 68)
print("ETAPE 12 - BANQUE : versements / retraits / solde")
compte = bq.creer_compte("Compte principal", banque="CBAO", numero="SN012",
                         solde_initial=0)
bq.creer_versement(compte, 590800, origine="Encaissement client",
                   motif="Depot recette")
bq.creer_retrait(compte, 100000, categorie="Dépense agence",
                 beneficiaire="Fournitures")
s = bq.solde_compte(compte)
verifier("total versements = 590 800", s["total_versements"] == 590800,
         s["total_versements"])
verifier("total retraits = 100 000", s["total_retraits"] == 100000,
         s["total_retraits"])
verifier("solde = 490 800", s["solde_actuel"] == 490800, s["solde_actuel"])

print("=" * 68)
print("ETAPE 12b - plusieurs comptes affiches separement")
compte2 = bq.creer_compte("Mobile Money", banque="Wave", solde_initial=25000)
bq.creer_versement(compte2, 10000, origine="Recettes")
soldes = {x["compte_nom"]: x["solde_actuel"] for x in bq.soldes_tous_comptes()}
verifier("2 comptes distincts", len(soldes) == 2, ",".join(soldes))
verifier("solde compte 2 = 35 000 (25 000 + 10 000)",
         soldes.get("Mobile Money") == 35000, soldes.get("Mobile Money"))

print("=" * 68)
print("TEST ANTI-DOUBLE-COMPTAGE (§20) : vente + paiement + depot bancaire")
# Un client neuf, une seule vente de 590 800
cli = db.creer_client(nom="ANTIDOUBLE", prenom="Test", telephone="778889900")
billet = act.creer_operation("billet", cli, {"passager": "Test ANTIDOUBLE",
                                             "prix_client": 590800})

def ca_client(client_id):
    """Chiffre d'affaires du client = somme des TOTAUX de ses operations
    (JAMAIS les paiements ni les mouvements bancaires)."""
    return sum(o["total_client"] for o in act.lister_operations_client(client_id))

ca_avant = ca_client(cli)
verifier("CA du client apres la vente = 590 800", ca_avant == 590800, ca_avant)

# Le client paie 590 800 (encaissement, PAS une nouvelle vente)
act.creer_paiement_operation("billet", billet, 590800, mode="Espèces")
# On depose ces 590 800 en banque (mouvement de tresorerie, PAS une vente)
bq.creer_versement(compte, 590800, origine="Encaissement client",
                   client_id=cli, motif="Depot du paiement client")

ca_apres = ca_client(cli)
verifier("CA INCHANGE apres paiement + depot = 590 800 (pas 1 181 600)",
         ca_apres == 590800, ca_apres)
t = act.totaux_operation("billet", billet)
verifier("operation soldee (reste 0)", t["reste_a_payer"] == 0)

print("=" * 68)
print(f"RESULTAT : {OK} test(s) OK, {KO} echec(s).")
print("=" * 68)
