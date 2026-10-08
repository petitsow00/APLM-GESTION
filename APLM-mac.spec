# -*- mode: python ; coding: utf-8 -*-
# ============================================================
#  Recette PyInstaller pour construire APLM.app SUR macOS.
#  (A utiliser via le fichier "Construire APLM (Mac).command".)
# ============================================================
from PyInstaller.utils.hooks import collect_all

datas = []
binaries = []
hiddenimports = [
    'auth', 'reseau', 'db_client', 'db_serveur', 'tls', 'sauvegarde',
    'comptabilite', 'pdf_comptabilite', 'pdf_listes', 'pdf_receipt',
    'database', 'settings', 'config', 'i18n', 'utils',
    'ui.app', 'ui.dashboard_view', 'ui.clients_view', 'ui.dossiers_view',
    'ui.parametres_view', 'ui.historique_clients_view',
    'ui.historique_transactions_view', 'ui.login_view',
    'ui.utilisateurs_view', 'ui.journal_view', 'ui.depenses_view',
    'ui.comptabilite_view', 'ui.reseau_view', 'ui.helpers',
    'ui.avoirs_view',
    # --- Réorganisation 2026 : nouveaux modules (alignés sur APLM.spec,
    # la recette Windows - manquaient ici, ce qui aurait fait planter ou
    # manquer des écrans entiers une fois l'app Mac construite). ---
    'activites', 'banque', 'documents', 'recherche', 'rapports',
    'pdf_operation', 'pdf_engagement_visa',
    'ui.activite_view', 'ui.operation_dialog', 'ui.documents_dialog',
    'ui.paiements_view', 'ui.banque_view', 'ui.rapports_view',
    'ui.recherche_view',
]
for _pkg in ('customtkinter', 'tkcalendar', 'babel', 'fpdf2', 'darkdetect',
             'cryptography'):
    d, b, h = collect_all(_pkg)
    datas += d
    binaries += b
    hiddenimports += h


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='APLM',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='APLM',
)

# Le point important pour Mac : creer un vrai APLM.app double-cliquable.
app = BUNDLE(
    coll,
    name='APLM.app',
    icon=None,
    bundle_identifier='com.aplm.gestionvoyage',
    info_plist={
        'NSHighResolutionCapable': 'True',
        'LSMinimumSystemVersion': '10.13',
        'CFBundleDisplayName': 'APLM BUZNESS COMPANY',
        'CFBundleName': 'APLM',
    },
)
