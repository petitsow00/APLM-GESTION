@echo off
chcp 65001 >nul
title APLM BUZNESS COMPANY - Gestion des utilisateurs
cd /d "%~dp0"
python gestion_utilisateurs.py
echo.
pause
