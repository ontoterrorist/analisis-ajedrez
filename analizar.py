# -*- coding: utf-8 -*-
"""Pasa Stockfish sobre una partida PGN y vuelca un informe JSON con
evaluaciones por jugada, perdida de centipeones y momentos criticos."""
import argparse, json, math, os, sys, io
import chess, chess.engine, chess.pgn

SF = os.environ.get("STOCKFISH") or os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages\Stockfish.Stockfish_Microsoft.Winget.Source_8wekyb3d8bbwe\stockfish\stockfish-windows-x86-64-universal.exe")

def winpct(cp):
    """Centipeones -> probabilidad de victoria (0-100). Curva tipo Lichess."""
    return 50 + 50 * (2 / (1 + math.exp(-0.00368208 * cp)) - 1)

def clasificar(dwp, wp_antes):
    """Clasifica segun caida de win% (no cp crudos: evita marcar 'error'
    en posiciones ya perdidas donde el cp se dispara sin significado)."""
    if dwp >= 20: return "error_grave", 4      # ?? 
    if dwp >= 10: return "error", 2            # ?
    if dwp >= 5:  return "imprecision", 6      # ?!
    return "ok", 0

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pgn")
    ap.add_argument("--juego", type=int, default=0, help="indice de partida (0 = la primera)")
    ap.add_argument("--depth", type=int, default=18)
    ap.add_argument("--threads", type=int, default=6)
    ap.add_argument("--hash", type=int, default=1024)
    ap.add_argument("--out", default="informe.json")
    a = ap.parse_args()

    with open(a.pgn, encoding="utf-8-sig", errors="replace") as f:
        for _ in range(a.juego):
            if chess.pgn.read_game(f) is None:
                sys.exit("No hay tantas partidas en el archivo.")
        game = chess.pgn.read_game(f)
    if game is None:
        sys.exit("No se pudo leer la partida.")

    eng = chess.engine.SimpleEngine.popen_uci(SF)
    eng.configure({"Threads": a.threads, "Hash": a.hash})

    board = game.board()
    movs = list(game.mainline_moves())
    lim = chess.engine.Limit(depth=a.depth)

    # Una evaluacion por posicion (N+1), no dos: el eval "despues de la jugada"
    # es el eval de la posicion siguiente.
    posiciones = []
    b = game.board()
    for i in range(len(movs) + 1):
        info = eng.analyse(b, lim)
        pv = info.get("pv", [])
        posiciones.append({
            "turno": b.turn,
            "cp_rel": info["score"].relative.score(mate_score=10000),
            "mate": info["score"].relative.mate(),
            "mejor_san": b.san(pv[0]) if pv else None,
            "pv_san": b.variation_san(pv[:6]) if pv else None,
            "fen": b.fen(),
        })
        print(f"  {i}/{len(movs)}", end="\r", file=sys.stderr)
        if i < len(movs):
            b.push(movs[i])

    jugadas = []
    b = game.board()
    for i, mv in enumerate(movs):
        mover = b.turn
        san = b.san(mv)
        # cp desde la perspectiva del que mueve, antes y despues
        cp_antes = posiciones[i]["cp_rel"]
        cp_desp  = -posiciones[i + 1]["cp_rel"]
        wp_antes, wp_desp = winpct(cp_antes), winpct(cp_desp)
        dwp = max(0.0, wp_antes - wp_desp)
        mejor = posiciones[i]["mejor_san"]
        fue_mejor = (mejor == san)
        if fue_mejor:
            dwp = 0.0
        etiqueta, nag = clasificar(dwp, wp_antes)
        jugadas.append({
            "ply": i + 1,
            "numero": i // 2 + 1,
            "color": "blancas" if mover == chess.WHITE else "negras",
            "san": san,
            "cp_antes_mover": cp_antes,
            "cp_despues_mover": cp_desp,
            "cp_perdidos": max(0, cp_antes - cp_desp) if not fue_mejor else 0,
            "winpct_perdido": round(dwp, 1),
            "mejor_jugada": mejor,
            "mejor_linea": posiciones[i]["pv_san"],
            "linea_tras_jugada": posiciones[i + 1]["pv_san"],
            "fue_la_mejor": fue_mejor,
            "etiqueta": etiqueta,
            "nag": nag,
            "fen_antes": posiciones[i]["fen"],
        })
        b.push(mv)
    eng.quit()

    criticos = sorted(jugadas, key=lambda j: -j["winpct_perdido"])[:10]
    informe = {
        "archivo": a.pgn, "indice": a.juego, "depth": a.depth,
        "cabecera": dict(game.headers),
        "jugadas": jugadas,
        "criticos": [{k: c[k] for k in ("ply","numero","color","san","etiqueta",
                      "winpct_perdido","cp_antes_mover","cp_despues_mover",
                      "mejor_jugada","mejor_linea")} for c in criticos],
        "acpl": {
            "blancas": round(sum(j["cp_perdidos"] for j in jugadas if j["color"]=="blancas")
                             / max(1, sum(1 for j in jugadas if j["color"]=="blancas"))),
            "negras": round(sum(j["cp_perdidos"] for j in jugadas if j["color"]=="negras")
                            / max(1, sum(1 for j in jugadas if j["color"]=="negras"))),
        },
    }
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(informe, f, ensure_ascii=False, indent=1)
    h = game.headers
    print(f"\n{h.get('White')} - {h.get('Black')} ({h.get('Result')}), {len(movs)} plies, depth {a.depth}")
    print(f"ACPL blancas {informe['acpl']['blancas']} | negras {informe['acpl']['negras']}")
    print(f"-> {a.out}")

if __name__ == "__main__":
    main()
