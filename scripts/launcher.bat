@echo off
title Stack SQL + VS Code

:: Intenta abrir con Windows Terminal; si no está instalado, usa cmd normal
where wt >nul 2>&1
if %ERRORLEVEL% == 0 (
    start "" wt wsl.exe -- bash -ic "cd ~/dev/stack-sql-vscode && bash scripts/menu.sh"
) else (
    start "" wsl.exe -- bash -ic "cd ~/dev/stack-sql-vscode && bash scripts/menu.sh"
)
