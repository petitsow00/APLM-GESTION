# -*- coding: utf-8 -*-
"""
test_compta.py
--------------
Teste la RESYNCHRONISATION comptable (Etape 13) sur une copie reconstruite
depuis la sauvegarde. Ne touche jamais la vraie base.
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
import comptabilite as co

OK = KO = 0
def verifier(nom, cond, detail=""):
    global OK, KO
    if cond:
        OK += 1; print(f"  [OK]  {nom}" + (f"  ({detail})" if detail else ""))
    else:
        KO += 1; print(f"  [!!]  ECHEC : {nom}" + (f"  ({detail})" if detail else ""))

def somme(sql, *p):
    conn = db.get_connexion()
    v = conn.execute(sql, p).fetchone()[0] or 0
    conn.close()
    return round(v, 2)

# --- Migrations ---
act.initialiser()
co.initialiser_comptabilite()
act.migrer_reservations_vers_activites()

print("=" * 68)
print("Une ECRITURE MANUELLE (journal OD) doit SURVIVRE a la regeneration")
eid_manuel = co.creer_ecriture("2026-01-15", "OD", "Test manuel loyer",
                               [{"compte": "622", "debit": 50000, "credit": 0},
                                {"compte": "571", "debit": 0, "credit": 50000}])

# --- Une nouvelle operation avec frais de service + TVA 18% ---
cli = db.creer_client(nom="COMPTA", prenom="Test")
billet = act.creer_operation("billet", cli, {
    "passager": "Test COMPTA", "prix_fournisseur": 400000, "prix_client": 500000,
    "frais_service": 20000, "reduction": 10000, "tva_taux": 18,
    "consolidateur": "Raya Travel"})

print("=" * 68)
print("REGENERATION des ecritures automatiques")
co.regenerer_ecritures_auto()

# 1) Comptabilite EQUILIBREE (debit total == credit total)
td = somme("SELECT SUM(debit) FROM lignes_ecriture")
tc = somme("SELECT SUM(credit) FROM lignes_ecriture")
verifier("comptabilite equilibree (total debit == total credit)", td == tc,
         f"D={td} C={tc}")

# 2) Ecriture manuelle conservee
conn = db.get_connexion()
manuel_present = conn.execute(
    "SELECT COUNT(*) FROM ecritures WHERE id=? AND source_type='manuel'",
    (eid_manuel,)).fetchone()[0]
conn.close()
verifier("ecriture manuelle OD conservee", manuel_present == 1)

# 3) PAS de double comptage : 1 ecriture 'vente' par operation (total != 0)
nb_ventes = somme("SELECT COUNT(*) FROM ecritures WHERE source_type='vente'")
nb_ops = 0
for a, table in (("billet", "billets"), ("assurance", "assurances"),
                 ("hotel", "hotels"), ("visa", "visas")):
    for o in act.lister_operations(a):
        t = act.calc_totaux(o["prix_client"], o["frais_service"], o["autres_frais"],
                            o["reduction"], o["prix_fournisseur"], o["tva_taux"])
        if t["total_client"] != 0:
            nb_ops += 1
verifier("1 ecriture de vente par operation (pas de doublon)",
         nb_ventes == nb_ops, f"{nb_ventes} ventes / {nb_ops} operations")

# 4) CA historique inchange : credits 701+706 == somme des totaux clients
credits_ventes = somme(
    "SELECT SUM(credit) FROM lignes_ecriture WHERE compte IN ('701','706')")
total_ops = 0
for a, table in (("billet", "billets"), ("assurance", "assurances"),
                 ("hotel", "hotels"), ("visa", "visas")):
    for o in act.lister_operations(a):
        t = act.calc_totaux(o["prix_client"], o["frais_service"], o["autres_frais"],
                            o["reduction"], o["prix_fournisseur"], o["tva_taux"])
        total_ops += t["total_client"] - t["montant_tva"]  # 701+706 = total - TVA
verifier("ventes (701+706) = somme des totaux clients HT-service",
         round(credits_ventes, 2) == round(total_ops, 2),
         f"{credits_ventes} vs {round(total_ops,2)}")

# 5) TVA collectee (4431) = 3 600 pour la nouvelle operation
tva_collectee = somme("SELECT SUM(credit) FROM lignes_ecriture WHERE compte='4431'")
verifier("TVA collectee (4431) = 3 600", tva_collectee == 3600, tva_collectee)
etat = co.etat_tva()
verifier("etat_tva : TVA collectee = 3 600",
         round(etat["tva_collectee"], 2) == 3600, etat["tva_collectee"])

# 6) Le detail de la nouvelle vente est correct (411=510000 ; 701=490000 ; 706=16400 ; 4431=3600)
conn = db.get_connexion()
lg = conn.execute("""
    SELECT l.compte, l.debit, l.credit FROM lignes_ecriture l
    JOIN ecritures e ON e.id=l.ecriture_id
    WHERE e.source_type='vente' AND e.reference=?
""", (act.get_operation("billet", billet)["reference"],)).fetchall()
conn.close()
d = {r["compte"]: (r["debit"], r["credit"]) for r in lg}
verifier("vente : 411 debit = 510 000", d.get("411", (0, 0))[0] == 510000)
verifier("vente : 701 credit = 490 000", d.get("701", (0, 0))[1] == 490000)
verifier("vente : 706 credit = 16 400", d.get("706", (0, 0))[1] == 16400)
verifier("vente : 4431 credit = 3 600", d.get("4431", (0, 0))[1] == 3600)

# 7) Donnees toujours intactes
verifier("reservations toujours intactes (27)",
         somme("SELECT COUNT(*) FROM reservations") == 27)

print("=" * 68)
print(f"RESULTAT : {OK} test(s) OK, {KO} echec(s).")
print("=" * 68)
