# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = []
binaries = []
# Modules internes de l'application (par sécurité, pour qu'ils soient
# TOUJOURS embarqués dans le .exe, y compris ceux importés "à la demande").
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
    # --- Réorganisation 2026 : nouveaux modules ---
    'activites', 'banque', 'documents', 'recherche', 'rapports',
    'pdf_operation',
    'ui.activite_view', 'ui.operation_dialog', 'ui.documents_dialog',
    'ui.paiements_view', 'ui.banque_view', 'ui.rapports_view',
    'ui.recherche_view',
]
tmp_ret = collect_all('customtkinter')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('tkcalendar')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('babel')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('fpdf2')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('darkdetect')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('cryptography')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


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
    upx=True,
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
    upx=True,
    upx_exclude=[],
    name='APLM',
)
