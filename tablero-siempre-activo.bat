@echo off
REM Tablero de ajedrez siempre activo.
REM Sirve el tablero en http://127.0.0.1:8765 en un proceso propio, independiente del MCP:
REM no se muere cuando Claude Code reinicia su servidor MCP ni cuando cierras la pestana.
REM Los procesos MCP detectan que el puerto ya esta ocupado y le pasan las partidas a este.
setlocal
set CHESS_WEB_OPEN=0
set CHESS_SESSION_TTL=0
cd /d "%USERPROFILE%\Documents\tintins-chess-analysis"
".venv\Scripts\python.exe" scripts\run_web.py --serve
