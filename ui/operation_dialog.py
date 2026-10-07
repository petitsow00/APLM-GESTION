# -*- coding: utf-8 -*-
"""
ui/operation_dialog.py
----------------------
Fenêtre RÉUTILISABLE pour créer/modifier une opération (billet, hôtel,
assurance, visa), avec le SÉLECTEUR DE CLIENT intelligent demandé au cahier
des charges :

    - « Client existant » : on recherche par nom/téléphone/email/passeport et
      on rattache l'opération au client trouvé (aucune nouvelle fiche).
    - « + Nouveau client » : on saisit le client ; avant de créer, on cherche
      les doublons (passeport/téléphone/email/nom+prénom) et, si on en trouve,
      on laisse l'UTILISATEUR décider (utiliser l'existant / créer quand même).

Après fermeture :
    self.resultat = {"client_id": <id>, "donnees": {champs de l'opération}}
    ou None si annulé.
"""

import tkinter as tk
from tkinter import ttk
import customtkinter as ctk

import database as db
import activites as act
from ui.helpers import COULEURS, erreur, info, CALENDRIER_DISPO

try:
    from tkcalendar import DateEntry
except Exception:
    CALENDRIER_DISPO = False

# Champs financiers qui déclenchent le recalcul automatique du total
FINANCE_KEYS = ("prix_client", "frais_service", "autres_frais", "reduction",
                "prix_fournisseur", "tva_taux")


def formater(montant):
    try:
        return f"{float(montant):,.0f}".replace(",", " ")
    except Exception:
        return str(montant)


class OperationDialog(ctk.CTkToplevel):
    def __init__(self, parent, titre, champs, valeurs=None, client_fixe=None):
        super().__init__(parent)
        self.title(titre)
        self.resultat = None
        self._champs = champs
        self._widgets = {}
        self._valeurs = valeurs or {}
        # client_fixe = (id, "Nom Prénom") -> zone client verrouillée (modification)
        self._client_fixe = client_fixe
        self.client_id = client_fixe[0] if client_fixe else None

        self.configure(fg_color=COULEURS["fond"])
        self.geometry("620x760")

        ctk.CTkLabel(self, text=titre, font=ctk.CTkFont(size=19, weight="bold"),
                     text_color=COULEURS["primaire"]).pack(
                         anchor="w", padx=20, pady=(16, 8))

        zone = ctk.CTkScrollableFrame(self, fg_color=COULEURS["fond"])
        zone.pack(fill="both", expand=True, padx=14, pady=4)

        self._construire_zone_client(zone)
        self._construire_champs_operation(zone)

        # Bandeau des totaux calculés
        self.bandeau = ctk.CTkFrame(self, fg_color=COULEURS["primaire"])
        self.bandeau.pack(fill="x", padx=14, pady=(4, 4))
        self.lbl_totaux = ctk.CTkLabel(
            self.bandeau, text="", font=ctk.CTkFont(size=13, weight="bold"),
            text_color="white")
        self.lbl_totaux.pack(padx=14, pady=8, anchor="w")

        barre = ctk.CTkFrame(self, fg_color="transparent")
        barre.pack(fill="x", padx=20, pady=(4, 14))
        ctk.CTkButton(barre, text="Annuler", fg_color=COULEURS["gris"],
                      hover_color="#555", width=110,
                      command=self._annuler).pack(side="right", padx=(8, 0))
        ctk.CTkButton(barre, text="Enregistrer", fg_color=COULEURS["vert"],
                      hover_color="#166638", width=150,
                      command=self._valider).pack(side="right")

        self._maj_totaux()
        self.update_idletasks()
        self.transient(parent)
        self.grab_set()
        self.wait_window(self)

    # ------------------------------------------------------------------ #
    #  ZONE CLIENT
    # ------------------------------------------------------------------ #
    def _construire_zone_client(self, parent):
        cadre = ctk.CTkFrame(parent, fg_color=COULEURS["carte"], corner_radius=10)
        cadre.pack(fill="x", padx=6, pady=(4, 10))
        ctk.CTkLabel(cadre, text="👤  Client",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=COULEURS["primaire"]).pack(anchor="w", padx=12, pady=(10, 4))

        # Cas modification : client déjà fixé -> on l'affiche, non modifiable
        if self._client_fixe:
            ctk.CTkLabel(cadre, text=f"Opération de : {self._client_fixe[1]}",
                         font=ctk.CTkFont(size=13),
                         text_color=COULEURS["texte"]).pack(anchor="w", padx=12, pady=(0, 12))
            return

        self._mode_client = ctk.StringVar(value="existant")
        seg = ctk.CTkSegmentedButton(
            cadre, values=["Client existant", "+ Nouveau client"],
            command=self._changer_mode_client)
        seg.set("Client existant")
        seg.pack(fill="x", padx=12, pady=(0, 8))

        # --- Sous-cadre CLIENT EXISTANT ---
        self.cadre_existant = ctk.CTkFrame(cadre, fg_color="transparent")
        self.cadre_existant.pack(fill="x", padx=12, pady=(0, 10))
        self.recherche_var = ctk.StringVar()
        e = ctk.CTkEntry(self.cadre_existant,
                         placeholder_text="Rechercher : nom, téléphone, email, passeport…",
                         textvariable=self.recherche_var)
        e.pack(fill="x")
        e.bind("<KeyRelease>", lambda ev: self._rafraichir_resultats())

        self.tab_clients = ttk.Treeview(
            self.cadre_existant, columns=("code", "nom", "tel"),
            show="headings", selectmode="browse", height=4)
        for c, txt, w in (("code", "Code", 90), ("nom", "Nom", 220),
                          ("tel", "Téléphone", 120)):
            self.tab_clients.heading(c, text=txt)
            self.tab_clients.column(c, width=w, anchor="w")
        self.tab_clients.pack(fill="x", pady=(6, 4))
        self.tab_clients.bind("<<TreeviewSelect>>", self._selectionner_client)
        self.lbl_client = ctk.CTkLabel(self.cadre_existant,
                                       text="Aucun client sélectionné.",
                                       text_color=COULEURS["gris"])
        self.lbl_client.pack(anchor="w")

        # --- Sous-cadre NOUVEAU CLIENT (caché au départ) ---
        self.cadre_nouveau = ctk.CTkFrame(cadre, fg_color="transparent")
        self._champs_nouveau = {}
        for cle, lbl in (("nom", "Nom *"), ("prenom", "Prénom"),
                         ("telephone", "Téléphone"), ("email", "Email"),
                         ("num_passeport", "N° passeport"),
                         ("date_naissance", "Date de naissance"),
                         ("nationalite", "Nationalité"), ("adresse", "Adresse")):
            ctk.CTkLabel(self.cadre_nouveau, text=lbl,
                         font=ctk.CTkFont(size=11, weight="bold"),
                         anchor="w").pack(fill="x", padx=2, pady=(4, 0))
            w = ctk.CTkEntry(self.cadre_nouveau)
            w.pack(fill="x", padx=2)
            self._champs_nouveau[cle] = w

        self._rafraichir_resultats()

    def _changer_mode_client(self, valeur):
        if valeur == "Client existant":
            self.cadre_nouveau.pack_forget()
            self.cadre_existant.pack(fill="x", padx=12, pady=(0, 10))
            self._mode_client.set("existant")
        else:
            self.cadre_existant.pack_forget()
            self.cadre_nouveau.pack(fill="x", padx=12, pady=(0, 10))
            self._mode_client.set("nouveau")

    def _rafraichir_resultats(self):
        for l in self.tab_clients.get_children():
            self.tab_clients.delete(l)
        terme = self.recherche_var.get().strip()
        clients = (db.rechercher_clients_avance(terme) if terme
                   else db.lister_clients()[:20])
        for c in clients:
            nom = f'{c["nom"]} {c["prenom"] or ""}'.strip()
            self.tab_clients.insert("", "end", iid=str(c["id"]),
                                    values=(c["code"] or "", nom, c["telephone"] or ""))

    def _selectionner_client(self, _ev=None):
        sel = self.tab_clients.selection()
        if sel:
            self.client_id = int(sel[0])
            c = db.get_client(self.client_id)
            self.lbl_client.configure(
                text=f'✔ Client sélectionné : {c["nom"]} {c["prenom"] or ""} ({c["code"]})',
                text_color=COULEURS["vert"])

    # ------------------------------------------------------------------ #
    #  CHAMPS DE L'OPÉRATION
    # ------------------------------------------------------------------ #
    def _construire_champs_operation(self, parent):
        cadre = ctk.CTkFrame(parent, fg_color=COULEURS["carte"], corner_radius=10)
        cadre.pack(fill="x", padx=6, pady=(0, 10))
        ctk.CTkLabel(cadre, text="📝  Détails de l'opération",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=COULEURS["primaire"]).pack(anchor="w", padx=12, pady=(10, 4))

        for champ in self._champs:
            cle = champ["cle"]
            typ = champ.get("type", "texte")
            ctk.CTkLabel(cadre, text=champ.get("label", cle),
                         font=ctk.CTkFont(size=11, weight="bold"),
                         anchor="w").pack(fill="x", padx=12, pady=(6, 0))
            valeur = self._valeurs.get(cle, "")

            if typ == "zone":
                w = ctk.CTkTextbox(cadre, height=60)
                if valeur:
                    w.insert("1.0", str(valeur))
            elif typ == "liste":
                options = champ.get("options", [])
                var = ctk.StringVar(value=str(valeur) if valeur else
                                    (options[0] if options else ""))
                w = ctk.CTkOptionMenu(cadre, values=options, variable=var,
                                      fg_color=COULEURS["primaire"],
                                      button_color=COULEURS["primaire2"])
                w._var = var
            elif typ == "date" and CALENDRIER_DISPO:
                w = DateEntry(cadre, date_pattern="yyyy-mm-dd", width=18,
                              background=COULEURS["primaire"], foreground="white")
                if valeur:
                    try:
                        w.set_date(str(valeur))
                    except Exception:
                        w.delete(0, "end")
                else:
                    w.delete(0, "end")
            else:
                w = ctk.CTkEntry(cadre)
                if valeur not in ("", None):
                    w.insert(0, str(valeur))
                if cle in FINANCE_KEYS:
                    w.bind("<KeyRelease>", lambda ev: self._maj_totaux())

            w.pack(fill="x", padx=12, pady=(2, 2))
            self._widgets[cle] = (w, typ)

    # ------------------------------------------------------------------ #
    #  TOTAUX AUTOMATIQUES
    # ------------------------------------------------------------------ #
    def _nombre(self, cle):
        w_typ = self._widgets.get(cle)
        if not w_typ:
            return 0
        w, typ = w_typ
        try:
            txt = w.get().replace(" ", "").replace(",", ".")
            return float(txt) if txt else 0
        except Exception:
            return 0

    def _maj_totaux(self):
        t = act.calc_totaux(
            prix_client=self._nombre("prix_client"),
            frais_service=self._nombre("frais_service"),
            autres_frais=self._nombre("autres_frais"),
            reduction=self._nombre("reduction"),
            prix_fournisseur=self._nombre("prix_fournisseur"),
            tva_taux=self._nombre("tva_taux"))
        self.lbl_totaux.configure(
            text=(f"TOTAL CLIENT : {formater(t['total_client'])}   |   "
                  f"MARGE : {formater(t['marge'])}   |   "
                  f"TVA : {formater(t['montant_tva'])}"))

    # ------------------------------------------------------------------ #
    #  LECTURE / VALIDATION
    # ------------------------------------------------------------------ #
    def _lire(self, w, typ):
        if typ == "zone":
            return w.get("1.0", "end").strip()
        if typ == "liste":
            return w._var.get()
        if typ == "date" and CALENDRIER_DISPO:
            try:
                return w.get()
            except Exception:
                return ""
        return w.get().strip()

    def _resoudre_client(self):
        """Renvoie un client_id, ou None si l'utilisateur annule / erreur."""
        if self._client_fixe:
            return self._client_fixe[0]
        if self._mode_client.get() == "existant":
            if not self.client_id:
                erreur("Client", "Veuillez sélectionner un client existant, "
                       "ou choisir « + Nouveau client ».")
                return None
            return self.client_id
        # Mode nouveau client
        donnees = {c: w.get().strip() for c, w in self._champs_nouveau.items()}
        if not donnees.get("nom"):
            erreur("Client", "Le nom du nouveau client est obligatoire.")
            return None
        res = db.trouver_ou_creer_client(donnees)
        if "client_id" in res:
            return res["client_id"]
        # Doublon(s) détecté(s) -> l'utilisateur décide
        decision = _DialogueDoublon(self, res["doublons"], donnees).decision
        if decision is None:
            return None
        if decision == "__forcer__":
            return db.trouver_ou_creer_client(donnees, forcer_creation=True)["client_id"]
        return decision  # id du client existant choisi

    def _valider(self):
        client_id = self._resoudre_client()
        if client_id is None:
            return
        donnees = {}
        for cle, (w, typ) in self._widgets.items():
            valeur = self._lire(w, typ)
            if cle in FINANCE_KEYS:
                try:
                    valeur = float(str(valeur).replace(" ", "").replace(",", ".")) if valeur else 0
                except ValueError:
                    erreur("Erreur", f"« {valeur} » n'est pas un nombre valide.")
                    return
            donnees[cle] = valeur
        self.resultat = {"client_id": client_id, "donnees": donnees}
        self.grab_release()
        self.destroy()

    def _annuler(self):
        self.resultat = None
        self.grab_release()
        self.destroy()


# =========================================================================== #
#  Petit dialogue : un doublon a été trouvé, l'utilisateur décide
# =========================================================================== #
class _DialogueDoublon(ctk.CTkToplevel):
    def __init__(self, parent, doublons, donnees):
        super().__init__(parent)
        self.title("Client déjà existant ?")
        self.decision = None
        self.configure(fg_color=COULEURS["fond"])
        self.geometry("560x460")

        ctk.CTkLabel(self, text="⚠️  Un client correspondant existe déjà",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=COULEURS["rouge"]).pack(anchor="w", padx=18, pady=(16, 4))
        ctk.CTkLabel(self, text=f'Vous saisissez : {donnees.get("nom","")} '
                     f'{donnees.get("prenom","")}  ·  {donnees.get("telephone","")}',
                     text_color=COULEURS["gris"]).pack(anchor="w", padx=18)

        zone = ctk.CTkScrollableFrame(self, fg_color=COULEURS["carte"], height=240)
        zone.pack(fill="both", expand=True, padx=18, pady=10)
        for d in doublons:
            c = d["client"]
            ligne = ctk.CTkFrame(zone, fg_color=COULEURS["fond"], corner_radius=8)
            ligne.pack(fill="x", padx=6, pady=5)
            ctk.CTkLabel(ligne,
                         text=f'{c["nom"]} {c["prenom"] or ""}  ({c["code"] or ""})\n'
                              f'📞 {c["telephone"] or "—"}   ✉ {c["email"] or "—"}\n'
                              f'Correspondance : {d["critere"]}',
                         justify="left", anchor="w").pack(side="left", padx=10, pady=8)
            ctk.CTkButton(ligne, text="Utiliser cette fiche",
                          fg_color=COULEURS["vert"], hover_color="#166638", width=150,
                          command=lambda cid=c["id"]: self._choisir(cid)).pack(
                              side="right", padx=10)

        barre = ctk.CTkFrame(self, fg_color="transparent")
        barre.pack(fill="x", padx=18, pady=(0, 16))
        ctk.CTkButton(barre, text="Annuler", fg_color=COULEURS["gris"],
                      hover_color="#555", width=120,
                      command=self._annuler).pack(side="right", padx=(8, 0))
        ctk.CTkButton(barre, text="Créer quand même un nouveau client",
                      fg_color=COULEURS["accent"], width=260,
                      command=self._forcer).pack(side="right")

        self.transient(parent)
        self.grab_set()
        self.wait_window(self)

    def _choisir(self, cid):
        self.decision = cid
        self.grab_release(); self.destroy()

    def _forcer(self):
        self.decision = "__forcer__"
        self.grab_release(); self.destroy()

    def _annuler(self):
        self.decision = None
        self.grab_release(); self.destroy()
