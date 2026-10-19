# Análisis de ajedrez

Scripts para analizar partidas con Stockfish y devolver un PGN comentado que se abre en ChessBase.

- `analizar.py`: pasa Stockfish por un PGN y escribe un informe JSON (evaluación por jugada, centipeones perdidos, caída de win%, ACPL).
- `anotar.py`: mete prosa, NAGs y variantes del motor en el PGN (`--encoding latin-1` si ChessBase no lee UTF-8).
- `tablero-siempre-activo.bat`: deja el tablero de `tintins-chess-analysis` encendido en http://127.0.0.1:8765, aparte del servidor MCP.
- `informe_granda.json`, `com_granda.json`: ejemplo de informe y de comentarios.

Flujo: `analizar.py` → se escribe la prosa sobre los datos → `anotar.py`.

Requisitos: `py -m pip install chess` y Stockfish (por defecto la ruta de winget; otra ruta con la variable `STOCKFISH`).
