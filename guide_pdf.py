# -*- coding: utf-8 -*-
"""
guide_pdf.py
-------------
Génère un GUIDE D'UTILISATION au format PDF pour APLM BUZNESS COMPANY :
installation, connexion, comptes, multi-postes (serveur/clients), sauvegardes,
dépannage.

Lancement :  python guide_pdf.py
Résultat  :  Guide-APLM.pdf (dans le dossier Téléchargements)

Police fpdf = latin-1 : on nettoie les caractères spéciaux (emojis, fleches...)
pour éviter toute erreur d'encodage.
"""

import os
from datetime import datetime
from fpdf import FPDF

try:
    import config
    LOGO = config.LOGO_PATH if os.path.exists(config.LOGO_PATH) else None
except Exception:
    LOGO = None

BLEU = (18, 52, 86)
BLEU2 = (31, 78, 121)
ACCENT = (46, 134, 222)
GRIS = (110, 110, 110)
VERT = (30, 132, 73)
ROUGE = (192, 57, 43)
FOND = (244, 246, 249)

# Remplacements pour rester compatible latin-1 (pas d'emojis, fleches, etc.)
_REMPLACEMENTS = {
    "→": "->", "←": "<-", "•": "-", "—": "-",
    "–": "-", "’": "'", "‘": "'", "“": '"',
    "”": '"', "…": "...", "œ": "oe", "Œ": "OE",
    "✅": "", "❌": "", "⚠": "", "⚙": "", "✓": "",
    "\U0001f310": "", "⭐": "", "\U0001f511": "", "\U0001f4be": "",
}


def _s(texte):
    if texte is None:
        return ""
    texte = str(texte)
    for k, v in _REMPLACEMENTS.items():
        texte = texte.replace(k, v)
    # Filet de securite : on force le latin-1 en remplacant l'inconnu
    return texte.encode("latin-1", "replace").decode("latin-1")


class Guide(FPDF):
    def header(self):
        if self.page_no() == 1:
            return
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*GRIS)
        self.cell(0, 6, _s("APLM BUZNESS COMPANY - Guide d'utilisation"),
                  align="R", ln=1)
        self.set_draw_color(*BLEU)
        self.set_line_width(0.2)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(2)

    def footer(self):
        if self.page_no() == 1:
            return
        self.set_y(-14)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*GRIS)
        self.cell(0, 6, _s("Page %d" % self.page_no()), align="C")

    # --- Briques de mise en page ---
    def _epw(self):
        """Largeur utile de la page (entre les marges)."""
        return self.w - self.l_margin - self.r_margin

    def titre1(self, numero, texte):
        if self.get_y() > self.h - 60:
            self.add_page()
        self.ln(2)
        self.set_x(self.l_margin)
        self.set_fill_color(*BLEU)
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 13)
        self.multi_cell(self._epw(), 10, _s("  %s  %s" % (numero, texte)), fill=True)
        self.ln(3)
        self.set_text_color(0, 0, 0)

    def titre2(self, texte):
        if self.get_y() > self.h - 45:
            self.add_page()
        self.ln(1)
        self.set_x(self.l_margin)
        self.set_text_color(*BLEU2)
        self.set_font("Helvetica", "B", 11)
        self.multi_cell(self._epw(), 7, _s(texte))
        self.set_text_color(0, 0, 0)

    def para(self, texte):
        self.set_x(self.l_margin)
        self.set_font("Helvetica", "", 10.5)
        self.set_text_color(30, 30, 30)
        self.multi_cell(self._epw(), 5.6, _s(texte))
        self.ln(1.5)

    def etape(self, numero, texte):
        self.set_x(self.l_margin)
        self.set_font("Helvetica", "B", 10.5)
        self.set_text_color(*ACCENT)
        largeur_num = 8
        self.cell(largeur_num, 5.6, _s(str(numero)))
        self.set_font("Helvetica", "", 10.5)
        self.set_text_color(30, 30, 30)
        self.multi_cell(self._epw() - largeur_num, 5.6, _s(texte))
        self.ln(0.8)

    def puce(self, texte):
        self.set_x(self.l_margin)
        self.set_font("Helvetica", "", 10.5)
        self.set_text_color(30, 30, 30)
        self.cell(5, 5.6, _s("-"))
        self.multi_cell(self._epw() - 5, 5.6, _s(texte))
        self.ln(0.4)

    def note(self, texte, couleur=VERT, titre="A SAVOIR"):
        self.ln(1)
        y0 = self.get_y()
        self.set_x(self.l_margin)
        self.set_font("Helvetica", "B", 9.5)
        self.set_text_color(*couleur)
        self.multi_cell(self._epw(), 5.4, _s(titre + " :"))
        self.set_x(self.l_margin)
        self.set_font("Helvetica", "", 10)
        self.set_text_color(40, 40, 40)
        self.multi_cell(self._epw(), 5.4, _s(texte))
        # petit trait vertical a gauche pour signaler l'encadre
        self.set_draw_color(*couleur)
        self.set_line_width(1.2)
        self.line(self.l_margin - 2, y0, self.l_margin - 2, self.get_y())
        self.set_line_width(0.2)
        self.ln(2)


def generer(chemin_sortie):
    pdf = Guide(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=16)
    pdf.set_margins(16, 14, 16)

    # ===================== PAGE DE GARDE =====================
    pdf.add_page()
    pdf.set_fill_color(*BLEU)
    pdf.rect(0, 0, pdf.w, 90, style="F")
    if LOGO:
        try:
            pdf.image(LOGO, x=(pdf.w - 30) / 2, y=16, w=30)
        except Exception:
            pass
    pdf.set_y(52)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 26)
    pdf.cell(0, 12, _s("APLM BUZNESS COMPANY"), align="C", ln=1)
    pdf.set_font("Helvetica", "", 14)
    pdf.cell(0, 8, _s("Gestion Agence de Voyage"), align="C", ln=1)

    pdf.set_y(110)
    pdf.set_text_color(*BLEU)
    pdf.set_font("Helvetica", "B", 22)
    pdf.cell(0, 12, _s("Guide d'utilisation"), align="C", ln=1)
    pdf.set_font("Helvetica", "", 12)
    pdf.set_text_color(*GRIS)
    pdf.cell(0, 8, _s("Installation - Connexion - Multi-postes (serveur)"),
             align="C", ln=1)

    pdf.set_y(150)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(40, 40, 40)
    intro = ("Ce guide explique, pas a pas et simplement, comment installer et "
             "utiliser le logiciel : se connecter, gerer les comptes, et surtout "
             "faire fonctionner plusieurs ordinateurs ensemble sur les memes "
             "donnees (mode serveur / clients).")
    pdf.set_x(28)
    pdf.multi_cell(pdf.w - 56, 6, _s(intro), align="C")

    pdf.set_y(270)
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(*GRIS)
    pdf.cell(0, 6, _s("Document genere le " +
             datetime.now().strftime("%d/%m/%Y")), align="C")

    # ===================== 1. PRESENTATION =====================
    pdf.add_page()
    pdf.titre1("1.", "Que fait le logiciel ?")
    pdf.para("APLM BUZNESS COMPANY est un logiciel de gestion pour agence de "
             "voyage. Il permet de gerer les clients, les dossiers de voyage, les "
             "billets, les encaissements et les depenses, avec une comptabilite "
             "automatique conforme au SYSCOHADA / OHADA.")
    pdf.titre2("Les principales rubriques")
    pdf.puce("Tableau de bord : les chiffres cles (clients, chiffre d'affaires, benefice...).")
    pdf.puce("Clients : la liste et les fiches de vos clients.")
    pdf.puce("Dossiers : un dossier = un voyage (billets, prix, paiements).")
    pdf.puce("Depenses / Decaissements : les sorties d'argent (loyer, salaires, fournisseurs...).")
    pdf.puce("Historique clients / transactions : listes et exports PDF.")
    pdf.puce("Comptabilite : Grand Livre, Balance, Resultat, Bilan, Caisse/Banque, TVA (admin).")
    pdf.puce("Utilisateurs et Journal des activites : gestion des comptes et tracabilite (admin).")

    # ===================== 2. INSTALLATION =====================
    pdf.titre1("2.", "Installer le logiciel")
    pdf.etape(1, "Copiez le fichier APLM_Setup.exe sur l'ordinateur (cle USB ou telechargement).")
    pdf.etape(2, "Double-cliquez sur APLM_Setup.exe.")
    pdf.etape(3, "Si Windows affiche 'Windows a protege votre ordinateur' : cliquez "
                 "sur 'Informations complementaires' puis 'Executer quand meme'. "
                 "(C'est normal, le fichier n'est pas signe.)")
    pdf.etape(4, "Suivez l'installation (une icone est creee sur le Bureau).")
    pdf.note("Vos donnees sont rangees dans le dossier "
             "Documents\\APLM BUZNESS COMPANY. Une reinstallation ne les efface pas.")

    # ===================== 3. COMPTES ET CONNEXION =====================
    pdf.titre1("3.", "Se connecter (identifiant + mot de passe)")
    pdf.para("Chaque personne a son propre compte. Il existe deux types de comptes :")
    pdf.puce("Administrateur : acces a tout (comptabilite, utilisateurs, reglages, reseau).")
    pdf.puce("Agent : le travail quotidien (clients, dossiers, depenses), sans les ecrans d'administration.")
    pdf.titre2("Premiere connexion : changer le mot de passe")
    pdf.etape(1, "Sur l'ecran de connexion, saisissez votre identifiant et le mot de passe.")
    pdf.etape(2, "Le mot de passe par defaut d'un nouveau compte est : Teranga99")
    pdf.etape(3, "Un ecran vous demande alors de choisir VOTRE nouveau mot de passe personnel.")
    pdf.etape(4, "Une fois change, vous entrez dans le logiciel.")
    pdf.note("Le tout premier administrateur choisit lui-meme son mot de passe a la "
             "creation ; il n'a donc pas de changement force.", titre="NOTE")

    # ===================== 4. MULTI-POSTES (LE COEUR) =====================
    pdf.titre1("4.", "Plusieurs ordinateurs sur les memes donnees")
    pdf.para("Pour que plusieurs ordinateurs du bureau travaillent sur LES MEMES "
             "donnees, un ordinateur devient le SERVEUR (il detient la base) et les "
             "autres sont des CLIENTS (ils se connectent au serveur).")

    pdf.titre2("Schema")
    pdf.set_font("Courier", "", 9.5)
    pdf.set_text_color(*BLEU2)
    for ligne in [
        "        PC AGENT 1  ---\\",
        "        PC AGENT 2  -----> [ PC SERVEUR ] --- (base centrale)",
        "        PC AGENT 3  ---/",
    ]:
        pdf.cell(0, 5.4, _s(ligne), ln=1)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(2)

    pdf.titre2("A. Sur le PC SERVEUR (le principal - a faire une seule fois)")
    pdf.etape(1, "Ouvrez le logiciel et connectez-vous en tant qu'administrateur.")
    pdf.etape(2, "Allez dans le menu Reseau.")
    pdf.etape(3, "Choisissez le role : Serveur (ce PC partage la base).")
    pdf.etape(4, "Choisissez une Cle secrete partagee (par ex. un mot de passe simple "
                 "a retenir). La meme cle sera saisie sur tous les postes.")
    pdf.etape(5, "Notez l'Adresse IP affichee (ex : 192.168.1.10). C'est elle que les "
                 "agents utiliseront.")
    pdf.etape(6, "Cliquez sur Enregistrer, puis FERMEZ et ROUVREZ le logiciel.")
    pdf.etape(7, "Lancez une seule fois l'outil 'Autoriser le serveur (pare-feu)' "
                 "(present dans le menu Demarrer ou le dossier d'installation). "
                 "Cliquez 'Oui' a la demande d'autorisation.")
    pdf.note("Le PC serveur doit rester allume pendant que les autres travaillent. "
             "L'adresse IP est visible dans le menu Reseau.", titre="IMPORTANT")

    pdf.titre2("B. Sur chaque PC AGENT (client)")
    pdf.etape(1, "Installez et ouvrez le logiciel.")
    pdf.etape(2, "Sur l'ecran de connexion, cliquez sur le bouton "
                 "'Se connecter a un serveur'.")
    pdf.etape(3, "Saisissez l'Adresse IP du serveur et la Cle secrete (les memes que "
                 "sur le serveur).")
    pdf.etape(4, "Cliquez sur 'Tester' : un message vert confirme que le serveur "
                 "repond.")
    pdf.etape(5, "Cliquez sur 'Enregistrer et se connecter'. L'ecran se recharge.")
    pdf.etape(6, "Saisissez votre identifiant et votre mot de passe : vous voyez "
                 "alors les memes donnees que tout le monde.")
    pdf.note("Si le serveur est eteint ou l'adresse fausse, l'ecran affiche 'Serveur "
             "injoignable'. Verifiez que le PC serveur est allume, l'adresse IP et la "
             "cle, puis cliquez sur Reessayer.", couleur=ROUGE, titre="EN CAS DE PROBLEME")

    # ===================== 5. UTILISATEURS =====================
    pdf.titre1("5.", "Gerer les comptes (administrateur)")
    pdf.para("Dans le menu Utilisateurs, l'administrateur peut :")
    pdf.puce("Creer un nouveau compte (admin ou agent). Le mot de passe est Teranga99 par defaut.")
    pdf.puce("Reinitialiser le mot de passe d'un agent qui l'a oublie (il repasse a Teranga99).")
    pdf.puce("Activer / desactiver un compte, ou le supprimer.")
    pdf.para("Chaque nouvel utilisateur devra changer son mot de passe a sa premiere "
             "connexion.")

    # ===================== 6. SAUVEGARDES =====================
    pdf.titre1("6.", "Sauvegardes automatiques")
    pdf.para("Le logiciel copie tout seul la base de donnees une fois par jour, dans "
             "le dossier Documents\\APLM BUZNESS COMPANY\\Sauvegardes. Les 30 "
             "dernieres sauvegardes sont conservees.")
    pdf.note("En multi-postes, c'est le PC SERVEUR qui detient les donnees et fait les "
             "sauvegardes. Pensez a copier ce dossier de temps en temps sur une cle "
             "USB, par securite.", titre="CONSEIL")

    # ===================== 7. DEPANNAGE =====================
    pdf.titre1("7.", "Questions frequentes / depannage")
    pdf.titre2("J'ai oublie mon mot de passe")
    pdf.para("Demandez a l'administrateur : menu Utilisateurs -> Reinitialiser. Votre "
             "compte repasse a Teranga99, et vous choisirez un nouveau mot de passe a "
             "la prochaine connexion.")
    pdf.titre2("'Serveur injoignable' sur un poste agent")
    pdf.puce("Verifiez que le PC serveur est allume et le logiciel ouvert.")
    pdf.puce("Verifiez l'adresse IP et la cle (menu Reseau du serveur).")
    pdf.puce("Verifiez que l'outil pare-feu a bien ete lance sur le serveur.")
    pdf.titre2("Windows affiche 'Editeur inconnu'")
    pdf.para("C'est normal (le fichier n'est pas signe). Cliquez sur 'Informations "
             "complementaires' puis 'Executer quand meme'.")

    # ===================== AIDE-MEMOIRE =====================
    pdf.titre1("8.", "Aide-memoire a remplir")
    pdf.para("Notez ici vos informations importantes :")
    for libelle in ["Adresse IP du serveur : ______________________________",
                    "Cle secrete partagee  : ______________________________",
                    "Identifiant admin     : ______________________________",
                    "Port reseau           : 5000 (par defaut)"]:
        pdf.set_font("Helvetica", "", 11)
        pdf.set_text_color(30, 30, 30)
        pdf.cell(0, 9, _s("   " + libelle), ln=1)

    pdf.output(chemin_sortie)
    return chemin_sortie


if __name__ == "__main__":
    telechargements = os.path.join(os.path.expanduser("~"), "Downloads")
    if not os.path.isdir(telechargements):
        telechargements = os.path.expanduser("~")
    sortie = os.path.join(telechargements, "Guide-APLM.pdf")
    chemin = generer(sortie)
    print("Guide genere :", chemin)
