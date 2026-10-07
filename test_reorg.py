# -*- coding: utf-8 -*-
"""
test_reorg.py
-------------
Teste TOUTE la couche de donnees de la reorganisation, sur une copie de travail
reconstruite a partir de la SAUVEGARDE (= vraie structure de production).

Il verifie les tests exiges au paragraphe 20 du cahier des charges :
  - aucune donnee perdue
  - migration des activites (billets / assurances)
  - client existant  (Etape 7)
  - detection de doublon (Etape 9)
  - nouveau client (Etape 8)
  - calculs (Etape 10)  +  TVA 18%
  - paiement partiel (Etape 11)
  - plusieurs operations pour un meme client

N'ecrit QUE sur aplm_travail.db. Ne touche jamais la vraie base.
"""

import os
import sqlite3

BACKUP = os.path.join(os.path.expanduser("~"), "Documents",
                      "SAUVEGARDE-AVANT-REORGANISATION-2026-09-11", "aplm.db")
COPIE = os.path.join(os.path.dirname(__file__), "data", "aplm_travail.db")

# --- 1) Reconstruire la copie de travail A PARTIR DE LA SAUVEGARDE ---
for suf in ("", "-wal", "-shm"):
    if os.path.exists(COPIE + suf):
        os.remove(COPIE + suf)
_src = sqlite3.connect(BACKUP)
_dst = sqlite3.connect(COPIE)
with _dst:
    _src.backup(_dst)
_dst.close()
_src.close()

# --- 2) Pointer l'application vers la copie AVANT d'importer database ---
import config
config.DB_PATH = COPIE
import database as db
import activites as act

OK, KO = 0, 0
def verifier(nom, condition, detail=""):
    global OK, KO
    if condition:
        OK += 1
        print(f"  [OK]  {nom}" + (f"  ({detail})" if detail else ""))
    else:
        KO += 1
        print(f"  [!!]  ECHEC : {nom}" + (f"  ({detail})" if detail else ""))

def compter(table):
    conn = db.get_connexion()
    n = conn.execute(f"SELECT COUNT(*) AS n FROM {table}").fetchone()["n"]
    conn.close()
    return n


print("=" * 68)
print("ETAT DE DEPART (copie reconstruite depuis la sauvegarde)")
avant = {t: compter(t) for t in ("clients", "dossiers", "reservations",
                                 "paiements", "ecritures")}
print("  ", avant)

print("=" * 68)
print("MIGRATIONS (creation tables + fiche client + paiements + recopie)")
act.initialiser()
nb_b, nb_a, nb_i = act.migrer_reservations_vers_activites()
# Idempotence : relancer ne doit RIEN recopier de plus
nb_b2, nb_a2, nb_i2 = act.migrer_reservations_vers_activites()

verifier("clients conserves (232)", compter("clients") == 232, compter("clients"))
verifier("reservations INTACTES (27)", compter("reservations") == 27)
verifier("dossiers INTACTS (29)", compter("dossiers") == 29)
verifier("paiements conserves (27)", compter("paiements") == 27)
verifier("ecritures comptables INTACTES (78)", compter("ecritures") == 78)
verifier("21 billets recopies", compter("billets") == 21, compter("billets"))
verifier("6 assurances recopiees", compter("assurances") == 6, compter("assurances"))
verifier("idempotence (2e recopie = 0)", (nb_b2, nb_a2) == (0, 0),
         f"{nb_b2},{nb_a2}")

print("=" * 68)
print("PAIEMENTS mis a niveau (rattachables a une operation)")
conn = db.get_connexion()
infos = {r["name"]: r for r in conn.execute("PRAGMA table_info(paiements)").fetchall()}
sans_client = conn.execute(
    "SELECT COUNT(*) AS n FROM paiements WHERE client_id IS NULL").fetchone()["n"]
conn.close()
verifier("colonnes operation ajoutees",
         {"operation_type", "operation_id", "client_id"} <= set(infos))
verifier("dossier_id devenu facultatif", infos["dossier_id"]["notnull"] == 0)
verifier("client retrouve pour les 27 paiements existants", sans_client == 0,
         f"{sans_client} sans client")

print("=" * 68)
print("ETAPE 10 - CALCULS (exemple du cahier des charges + TVA 18%)")
c = act.calc_totaux(prix_client=500000, frais_service=20000, autres_frais=0,
                    reduction=10000, prix_fournisseur=400000, tva_taux=18)
verifier("total_client = 510 000", c["total_client"] == 510000, c["total_client"])
verifier("marge = 110 000", c["marge"] == 110000, c["marge"])
verifier("TVA 18% sur frais service (20 000) = 3 600",
         c["montant_tva"] == 3600, c["montant_tva"])

print("=" * 68)
print("ETAPE 7 - CLIENT EXISTANT (ne cree PAS de nouvelle fiche)")
conn = db.get_connexion()
ref = conn.execute("SELECT * FROM clients ORDER BY id LIMIT 1").fetchone()
conn.close()
n0 = compter("clients")
res7 = db.trouver_ou_creer_client({}, client_existant_id=ref["id"])
verifier("rattache au client existant", res7.get("client_id") == ref["id"])
verifier("aucune fiche creee", compter("clients") == n0)

print("=" * 68)
print("ETAPE 9 - DETECTION DE DOUBLON (re-saisie d'un client existant)")
res9 = db.trouver_ou_creer_client({"nom": ref["nom"], "prenom": ref["prenom"] or "",
                                   "telephone": ref["telephone"] or ""})
verifier("doublon detecte -> decision a l'utilisateur", "doublons" in res9,
         res9.get("doublons", [{}])[0].get("critere", "") if "doublons" in res9 else "")
verifier("aucune fiche creee tant que non confirme", compter("clients") == n0)

print("=" * 68)
print("ETAPE 8 - NOUVEAU CLIENT (cree la fiche + code + rattachement)")
res8 = db.trouver_ou_creer_client({"nom": "TESTREORG", "prenom": "Nouveau",
                                   "telephone": "770000001",
                                   "num_passeport": "PASS-TEST-001"})
verifier("nouvelle fiche creee", "client_id" in res8)
verifier("compte clients +1", compter("clients") == n0 + 1)
nouveau_id = res8.get("client_id")
cli = db.get_client(nouveau_id)
verifier("code client genere", bool(cli["code"]), cli["code"])
verifier("passeport bien enregistre", cli["num_passeport"] == "PASS-TEST-001")

print("=" * 68)
print("ETAPE 20 - PLUSIEURS OPERATIONS POUR LE MEME CLIENT")
b1 = act.creer_operation("billet", nouveau_id,
                         {"passager": "Nouveau TESTREORG", "compagnie": "AF",
                          "ville_depart": "DKR", "ville_arrivee": "CDG",
                          "prix_fournisseur": 400000, "prix_client": 500000,
                          "frais_service": 20000, "reduction": 10000,
                          "tva_taux": 18})
act.creer_operation("billet", nouveau_id, {"passager": "Nouveau TESTREORG",
                                           "prix_client": 300000})
act.creer_operation("hotel", nouveau_id, {"nom_hotel": "Hotel Test",
                                          "ville": "Paris", "nb_nuits": 3,
                                          "prix_client": 150000})
act.creer_operation("visa", nouveau_id, {"pays_destination": "France",
                                         "type_visa": "Tourisme",
                                         "prix_client": 75000})
histo = act.lister_operations_client(nouveau_id)
verifier("4 operations rattachees au meme client", len(histo) == 4, len(histo))
activites_vues = sorted({h["activite"] for h in histo})
verifier("activites variees (billet/hotel/visa)",
         set(["billet", "hotel", "visa"]) <= set(activites_vues),
         ",".join(activites_vues))

print("=" * 68)
print("ETAPE 11 - PAIEMENT PARTIEL (billet a 510 000)")
t0 = act.totaux_operation("billet", b1)
verifier("total du billet = 510 000", t0["total_client"] == 510000, t0["total_client"])
verifier("reste initial = 510 000", t0["reste_a_payer"] == 510000)
act.creer_paiement_operation("billet", b1, 300000, mode="Especes")
t1 = act.totaux_operation("billet", b1)
verifier("apres 300 000 -> reste 210 000", t1["reste_a_payer"] == 210000,
         t1["reste_a_payer"])
act.creer_paiement_operation("billet", b1, 210000, mode="Virement")
t2 = act.totaux_operation("billet", b1)
verifier("apres solde -> reste 0", t2["reste_a_payer"] == 0)
verifier("marge inchangee = 110 000", t2["marge"] == 110000, t2["marge"])

print("=" * 68)
print(f"RESULTAT : {OK} test(s) OK, {KO} echec(s).")
print("La vraie base n'a PAS ete touchee (tout s'est fait sur aplm_travail.db).")
print("=" * 68)
