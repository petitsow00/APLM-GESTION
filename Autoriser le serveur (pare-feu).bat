@echo off
chcp 65001 >nul
title APLM BUZNESS COMPANY - Autoriser le serveur dans le pare-feu

REM ============================================================
REM  Ce petit outil autorise le PC SERVEUR a etre joignable par
REM  les autres postes du bureau (port reseau 5000 par defaut).
REM  A lancer UNE SEULE FOIS sur le PC serveur.
REM ============================================================

REM --- Demande automatiquement les droits administrateur ---
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Demande des droits administrateur...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

set PORT=5000

echo.
echo Autorisation du port %PORT% (TCP) dans le pare-feu Windows...
netsh advfirewall firewall delete rule name="APLM BUZNESS COMPANY - Serveur" >nul 2>&1
netsh advfirewall firewall add rule name="APLM BUZNESS COMPANY - Serveur" dir=in action=allow protocol=TCP localport=%PORT% profile=private,domain

echo.
echo ============================================================
echo  Termine. Le PC serveur est maintenant joignable sur le
echo  port %PORT% par les autres postes du bureau.
echo.
echo  (Si vous avez change le port dans les Reglages Reseau,
echo   modifiez la valeur PORT au debut de ce fichier.)
echo ============================================================
echo.
pause
