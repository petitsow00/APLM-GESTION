# -*- coding: utf-8 -*-
"""
documents.py
------------
ÉTAPE 16 : DOCUMENTS JOINTS.

Permet d'attacher un fichier (facture, reçu, billet, police d'assurance,
document visa, bordereau bancaire, justificatif...) à une opération et/ou à
un client. On stocke le CHEMIN du fichier (le fichier lui-même est copié dans
le dossier `documents/` de l'application par l'interface).

100 % additif : aucune donnée existante touchée.
"""

import os
import shutil
from datetime import datetime
import config
import database as db


# Catégories proposées (libres, mais pratiques pour trier)
CATEGORIES = ["Facture", "Reçu", "Billet", "Police d'assurance", "Document visa",
              "Bordereau bancaire", "Justificatif", "Passeport", "Autre"]

DOSSIER_DOCS = os.path.join(config.APP_HOME, "documents")


def initialiser():
    """Crée la table `documents` + le dossier de stockage (additif)."""
    os.makedirs(DOSSIER_DOCS, exist_ok=True)
    conn = db.get_connexion()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            operation_type TEXT,      -- billet / hotel / assurance / visa / paiement / banque / ''
            operation_id   INTEGER,
            client_id      INTEGER,
            categorie      TEXT,
            nom            TEXT,       -- nom lisible du document
            chemin         TEXT,       -- chemin du fichier sur le disque
            date_creation  TEXT,
            cree_par       INTEGER
        )
    """)
    conn.commit()
    conn.close()


def enregistrer_document(chemin_source, categorie="Autre", nom="",
                         operation_type="", operation_id=None, client_id=None,
                         copier=True):
    """Enregistre un document. Si `copier` est vrai, le fichier est COPIÉ dans
    le dossier `documents/` de l'application (l'original n'est pas déplacé)."""
    chemin_final = chemin_source
    if copier and chemin_source and os.path.exists(chemin_source):
        os.makedirs(DOSSIER_DOCS, exist_ok=True)
        base = os.path.basename(chemin_source)
        horodatage = datetime.now().strftime("%Y%m%d-%H%M%S")
        chemin_final = os.path.join(DOSSIER_DOCS, f"{horodatage}_{base}")
        try:
            shutil.copy2(chemin_source, chemin_final)
        except Exception:
            chemin_final = chemin_source  # à défaut, on garde le chemin d'origine
    if not nom:
        nom = os.path.basename(chemin_source) if chemin_source else categorie

    conn = db.get_connexion()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO documents
            (operation_type, operation_id, client_id, categorie, nom, chemin,
             date_creation, cree_par)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (operation_type, operation_id, client_id, categorie, nom, chemin_final,
          datetime.now().strftime("%Y-%m-%d %H:%M:%S"), db.auth.id_courant()))
    conn.commit()
    nid = cur.lastrowid
    conn.close()
    db.enregistrer_activite("Ajout", "Document", nom)
    return nid


def lister_documents(operation_type=None, operation_id=None, client_id=None):
    conn = db.get_connexion()
    base = "SELECT * FROM documents"
    cond, params = [], []
    if operation_type:
        cond.append("operation_type = ?"); params.append(operation_type)
    if operation_id is not None:
        cond.append("operation_id = ?"); params.append(operation_id)
    if client_id is not None:
        cond.append("client_id = ?"); params.append(client_id)
    if cond:
        base += " WHERE " + " AND ".join(cond)
    base += " ORDER BY date_creation DESC, id DESC"
    lignes = conn.execute(base, params).fetchall()
    conn.close()
    return lignes


def supprimer_document(document_id, effacer_fichier=False):
    conn = db.get_connexion()
    ligne = conn.execute("SELECT * FROM documents WHERE id=?",
                         (document_id,)).fetchone()
    conn.execute("DELETE FROM documents WHERE id=?", (document_id,))
    conn.commit()
    conn.close()
    if effacer_fichier and ligne and ligne["chemin"]:
        # On n'efface que si le fichier est bien dans NOTRE dossier documents
        try:
            if os.path.abspath(ligne["chemin"]).startswith(os.path.abspath(DOSSIER_DOCS)):
                os.remove(ligne["chemin"])
        except Exception:
            pass
    db.enregistrer_activite("Suppression", "Document", f"#{document_id}")
