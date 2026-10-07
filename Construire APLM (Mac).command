#!/bin/bash
# ============================================================
#  CONSTRUIRE APLM.app (equivalent Mac de APLM_Setup)
#  A EXECUTER SUR LE MAC (pas sur Windows).
#
#  Ce fichier fabrique une vraie application double-cliquable
#  "APLM.app" et la copie sur le Bureau.
#  A ne faire QU'UNE SEULE FOIS.
# ============================================================

cd "$(dirname "$0")"

PY="python3"
if ! command -v "$PY" >/dev/null 2>&1; then
    echo "Python 3 n'est pas installe."
    echo "Installez-le depuis https://www.python.org/downloads/ (version 3.12),"
    echo "puis relancez ce fichier."
    read -n 1 -s -r -p "Appuyez sur une touche pour fermer..."
    exit 1
fi

echo "============================================================"
echo " Etape 1/2 : installation des composants (quelques minutes)"
echo "============================================================"
"$PY" -m pip install --user -r requirements.txt
"$PY" -m pip install --user pyinstaller

echo
echo "============================================================"
echo " Etape 2/2 : construction de APLM.app"
echo "============================================================"
"$PY" -m PyInstaller "APLM-mac.spec" --noconfirm --clean

echo
if [ -d "dist/APLM.app" ]; then
    echo "TERMINE : APLM.app a ete cree dans le dossier 'dist'."
    if cp -R "dist/APLM.app" "$HOME/Desktop/" 2>/dev/null; then
        echo "Une copie a ete placee sur votre BUREAU : APLM.app"
    fi
    echo
    echo "Vous pouvez maintenant double-cliquer sur APLM.app pour lancer le logiciel."
    echo "(Au 1er lancement : clic droit sur APLM.app -> Ouvrir -> Ouvrir.)"
    open dist 2>/dev/null
else
    echo "La construction a echoue. Lisez les messages ci-dessus pour comprendre."
fi

echo
read -n 1 -s -r -p "Appuyez sur une touche pour fermer cette fenetre..."
