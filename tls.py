# -*- coding: utf-8 -*-
"""
tls.py
-------
Chiffrement des échanges réseau (HTTPS) entre le serveur et les postes agents.

Avant : les données (y compris les mots de passe envoyés à la connexion)
circulaient en clair (HTTP) sur le réseau local — n'importe qui écoutant le
Wi-Fi/réseau aurait pu les lire.

Maintenant : le serveur utilise un certificat "auto-signé" (créé par le
logiciel lui-même, comme un cadenas fait maison) pour chiffrer la
communication. C'est suffisant pour un réseau local de confiance (le bureau),
mais ce n'est PAS un certificat reconnu officiellement (comme pour un vrai
site internet) : il ne faut jamais exposer ce serveur sur Internet.

Le certificat est généré une seule fois, au premier démarrage du serveur,
puis réutilisé (il ne change pas à chaque redémarrage).
"""

import os
import datetime
import config

CERT_PATH = os.path.join(config.DATA_DIR, "serveur_cert.pem")
CLE_PATH = os.path.join(config.DATA_DIR, "serveur_cle.pem")


def obtenir_certificat():
    """Renvoie (chemin_certificat, chemin_cle_privee), en les créant si besoin."""
    if not (os.path.exists(CERT_PATH) and os.path.exists(CLE_PATH)):
        _generer_certificat()
    return CERT_PATH, CLE_PATH


def _generer_certificat():
    """Crée un certificat auto-signé valable 10 ans (clé RSA 2048 bits)."""
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID

    cle = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    sujet = x509.Name(
        [x509.NameAttribute(NameOID.COMMON_NAME, "APLM-Serveur-Local")])
    maintenant = datetime.datetime.now(datetime.timezone.utc)
    certificat = (
        x509.CertificateBuilder()
        .subject_name(sujet)
        .issuer_name(sujet)
        .public_key(cle.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(maintenant - datetime.timedelta(days=1))
        .not_valid_after(maintenant + datetime.timedelta(days=3650))
        .add_extension(
            x509.SubjectAlternativeName([x509.DNSName("localhost")]),
            critical=False)
        .sign(cle, hashes.SHA256())
    )

    os.makedirs(config.DATA_DIR, exist_ok=True)
    with open(CLE_PATH, "wb") as f:
        f.write(cle.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()))
    with open(CERT_PATH, "wb") as f:
        f.write(certificat.public_bytes(serialization.Encoding.PEM))
