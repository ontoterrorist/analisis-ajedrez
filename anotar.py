# -*- coding: utf-8 -*-
"""Inyecta comentarios en lenguaje natural, NAGs y variantes del motor
dentro de un PGN, dejandolo listo para abrir en ChessBase."""
import argparse, json, sys
import chess, chess.pgn

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pgn")
    ap.add_argument("comentarios", help="JSON: {'jugadas': {'<ply>': {...}}}")
    ap.add_argument("--juego", type=int, default=0)
    ap.add_argument("--out", required=True)
    ap.add_argument("--encoding", default="utf-8", help="utf-8 o latin-1 (ChessBase antiguo)")
    a = ap.parse_args()

    with open(a.comentarios, encoding="utf-8") as f:
        com = json.load(f)
    anot = {int(k): v for k, v in com.get("jugadas", {}).items()}

    with open(a.pgn, encoding="utf-8-sig", errors="replace") as f:
        for _ in range(a.juego):
            chess.pgn.read_game(f)
        game = chess.pgn.read_game(f)

    # Reconstruye la partida nodo a nodo para poder colgar variantes.
    nuevo = chess.pgn.Game()
    nuevo.headers.update(game.headers)
    for k, v in com.get("cabecera", {}).items():
        nuevo.headers[k] = v

    nodo = nuevo
    board = game.board()
    for i, mv in enumerate(game.mainline_moves(), start=1):
        nodo = nodo.add_main_variation(mv)
        d = anot.get(i)
        if d:
            if d.get("texto"):
                nodo.comment = d["texto"]
            if d.get("nag"):
                nodo.nags.add(int(d["nag"]))
            # variante alternativa, en SAN, desde la posicion ANTES de la jugada
            if d.get("variante"):
                vb = board.copy()
                vnodo = nodo.parent
                try:
                    for tok in d["variante"].split():
                        if tok[0].isdigit() or tok in ("...",):
                            continue
                        m = vb.parse_san(tok)
                        vnodo = vnodo.add_variation(m)
                        vb.push(m)
                    if d.get("texto_variante"):
                        vnodo.comment = d["texto_variante"]
                except ValueError as e:
                    print(f"  aviso: variante invalida en ply {i}: {e}", file=sys.stderr)
        board.push(mv)

    if com.get("resumen"):
        nuevo.comment = com["resumen"]

    with open(a.out, "w", encoding=a.encoding, errors="replace") as f:
        exporter = chess.pgn.FileExporter(f)
        nuevo.accept(exporter)
    print(f"-> {a.out}  ({len(anot)} jugadas comentadas)")

if __name__ == "__main__":
    main()
