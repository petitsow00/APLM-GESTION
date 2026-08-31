@echo off
REM ====================================================================
REM  Lanceur DIAGNOSTIC : garde la fenetre noire ouverte pour afficher
REM  les messages d'erreur eventuels. A utiliser seulement si le
REM  logiciel ne demarre pas avec le lanceur normal.
REM ====================================================================
cd /d "%~dp0"
python main.py
echo.
echo ---------------------------------------------------------------
echo Le logiciel s'est ferme. Laissez cette fenetre ouverte pour lire
echo les messages ci-dessus en cas de probleme.
pause
