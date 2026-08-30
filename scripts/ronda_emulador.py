#!/usr/bin/env python3
"""ronda_emulador — la Ronda 2 de YabauseVita como procedimiento ejecutable.

Ingeniería inversa de la metodología de la ronda 1: lo que el supervisor
hacía a mano (lanzar, esperar, capturar, pulsar, juzgar) queda aquí como
protocolo determinista que el enjambre —o cualquiera— puede correr y cuyo
veredicto llega en el formato R9: imagen + movimiento + dos FPS + errores.

LOS CUATRO EXPERIMENTOS DE LA RONDA 2 (bitácora, «pendiente»)
=============================================================
  1. nights   — NiGHTS ≥ 3 min con BIOS por región: ¿llega al título?
                (veredicto: imagen con movimiento sostenido tras la espera)
  2. input    — en el título, pulsar START (ENTER): ¿la pantalla cambia?
                (veredicto: diff % tras la pulsación ≥ umbral)
  3. dynarec  — cpu_mode=2 (SH2DynARM), 90 s: ¿sigue colgado al primer frame?
                (veredicto: ventanas de log ≥ 1 = avance; 0 = hang)
  4. perfil   — cpu_mode=0 por juego: reparto msh2/ssh2/scsp_th/vdp por ventana
                (el blanco de optimización ya tiene nombre: los SH2)

USO
===
    python scripts/ronda_emulador.py --repo C:\\...\\yabausevita-zp [--solo nights]

Sin dependencias fuera del harness: importa tools/vita3k_ctl.py del repo
del emulador. El veredicto sale por stdout como un JSON por experimento.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path

GAMES = {
    "nights": "ux0:data/yabause/roms/NiGHTS into Dreams... (USA) (with 3D Control Pad) (RE).chd",
    "sonicr": "ux0:data/yabause/roms/Sonic R (Europe).chd",
    "panzer": "ux0:data/yabause/roms/Panzer Dragoon (Europe) (EnFrDeEsIt).chd",
}


def cargar_harness(repo: Path):
    spec = importlib.util.spec_from_file_location(
        "vita3k_ctl", repo / "tools" / "vita3k_ctl.py")
    ctl = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ctl)
    return ctl


def correr_y_ver(ctl, rom: str, segundos: float, tag: str,
                 cpu_mode: int = 0, monitor_s: float = 15.0):
    """Corrida con ojos (R9): launch → espera → capturas → veredicto."""
    ctl.set_config({"rom_path": rom, "autostart": 1, "cpu_mode": cpu_mode,
                    "show_fps": 1, "auto_bios": 1, "bios_path": ""})
    off = ctl.log_size()
    boot = ctl.launch(ctl.APP_DIR)
    time.sleep(segundos)
    vision = ctl.monitor(seconds=monitor_s, interval=3, tag=tag)
    txt = ctl.read_new_text(off)
    ctl.kill()
    wins = ctl.parse_windows(txt)
    s = ctl.summarize(wins)
    return {
        "boot": boot,
        "vision": {k: vision[k] for k in
                   ("has_image", "has_motion", "black_pct_mediana",
                    "diff_pct_mediana")},
        "fps_rom_log": s.get("fps_median"),
        "fps_rom_min": s.get("fps_min"),
        "drawn_avg": s.get("drawn_avg"),
        "presented": s.get("presented_avg"),
        "emu": {k.replace("emu_", "").replace("_avg_us", ""): round(v)
                for k, v in s.items() if k.startswith("emu_")},
        "errors": ctl.scan_errors(txt),
    }


def exp_nights(ctl) -> dict:
    """1. NiGHTS con espera larga: la 5ª ventana de captura vale más que las
    cuatro primeras juntas — el boot de NiGHTS a 40 FPS tarda."""
    r = correr_y_ver(ctl, GAMES["nights"], segundos=185, tag="r2-nights")
    return {"experimento": "nights_titulo", **r,
            "veredicto": "LLEGA AL TITULO" if r["vision"]["has_motion"]
            else "NO LLEGA (sin movimiento tras 3 min)"}


def exp_input(ctl) -> dict:
    """2. Input. OJO con el diseño (v5.11.0 se equivocó aquí): medir diff
    antes/después en un attract QUE YA SE MUEVE no aísla la pulsación — el
    delta salió negativo con el juego vivo y el veredicto mintió. Protocolo
    corregido: capturas a 1 s, se mide el PICO de transición (un cambio de
    escena es un salto en UNA captura), y se compara contra un CONTROL de
    6 s sin pulsar: el input cruza si el pico tras la pulsación supera
    holgadamente el máximo que da el juego solo."""
    ctl.set_config({"rom_path": GAMES["sonicr"], "autostart": 1, "cpu_mode": 0,
                    "show_fps": 1, "auto_bios": 1, "bios_path": ""})
    off = ctl.log_size()
    ctl.launch(ctl.APP_DIR)
    time.sleep(70)  # attract con imagen

    control = ctl.monitor(seconds=6, interval=1, tag="r2-input-control")
    ctl.press_key("ENTER", hold=0.3)
    tras = ctl.monitor(seconds=6, interval=1, tag="r2-input-tras")
    txt = ctl.read_new_text(off)
    ctl.kill()

    pico_control = max(control.get("diffs_por_captura") or [0])
    pico_tras = max(tras.get("diffs_por_captura") or [0])
    cruzo = pico_tras >= max(8.0, 2.0 * pico_control)
    return {"experimento": "input_al_juego",
            "pico_diff_control_pct": round(pico_control, 2),
            "pico_diff_tras_pct": round(pico_tras, 2),
            "imagen_previa": control["has_image"],
            "errors": ctl.scan_errors(txt),
            "veredicto": "EL INPUT CRUZA" if cruzo else
            "INCONCLUSO (sin imagen previa)" if not control["has_image"] else
            "EL INPUT NO CRUZA (picos parejos)"}


def exp_dynarec(ctl) -> dict:
    """3. Dynarec: 90 s con cpu_mode=2. Ventanas de log > 0 significa que el
    primer frame completó — el hang conocido nunca escribió ni una."""
    ctl.set_config({"rom_path": GAMES["nights"], "autostart": 1, "cpu_mode": 2,
                    "show_fps": 1, "auto_bios": 1, "bios_path": ""})
    off = ctl.log_size()
    boot = ctl.launch(ctl.APP_DIR)
    time.sleep(90)
    txt = ctl.read_new_text(off)
    ctl.kill()
    wins = ctl.parse_windows(txt)
    return {"experimento": "dynarec_cpu_mode_2", "boot": boot,
            "ventanas_log": len(wins),
            "fps": [w.get("fps") for w in wins][:6],
            "errors": ctl.scan_errors(txt),
            "veredicto": "AVANZA" if wins else
            "HANG EN EL PRIMER FRAME (cache JIT OK, ejecucion rota)"}


def exp_perfil(ctl) -> dict:
    """4. Perfil SH2 por juego (cpu_mode=0): la mesa donde se sienta la
    Ronda 3. msh2+ssh2 dominando = la optimización va por los SH2."""
    out = []
    for clave in ("sonicr", "panzer", "nights"):
        r = correr_y_ver(ctl, GAMES[clave], segundos=60, tag=f"r2-perfil-{clave}")
        emu = r["emu"]
        total = sum(v for k, v in emu.items()
                    if k not in ("scsp_th",)) or 1  # scsp_th va en paralelo
        sh2 = round(100 * (emu.get("msh2", 0) + emu.get("ssh2", 0)) / total, 1)
        out.append({"juego": clave, "fps": r["fps_rom_log"],
                    "vision_ok": r["vision"]["has_image"] and r["vision"]["has_motion"],
                    "sh2_pct_hilo_principal": sh2, "emu": emu})
    return {"experimento": "perfil_sh2", "juegos": out,
            "veredicto": "SH2-BOUND confirmado" if
            all(j["sh2_pct_hilo_principal"] > 50 for j in out[:2]) else
            "reparto mixto — revisar por juego"}


EXPERIMENTOS = {"nights": exp_nights, "input": exp_input,
                "dynarec": exp_dynarec, "perfil": exp_perfil}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", required=True,
                    help="ruta del repo del emulador (con tools/vita3k_ctl.py)")
    ap.add_argument("--solo", choices=EXPERIMENTOS, default=None,
                    help="ejecutar un solo experimento")
    args = ap.parse_args()

    repo = Path(args.repo).resolve()
    ctl = cargar_harness(repo)

    nombres = [args.solo] if args.solo else list(EXPERIMENTOS)
    resultados = {}
    for nombre in nombres:
        print(f"── experimento: {nombre} ──", flush=True)
        try:
            resultados[nombre] = EXPERIMENTOS[nombre](ctl)
        except Exception as exc:  # el protocolo no muere entero por un trozo
            resultados[nombre] = {"experimento": nombre,
                                  "error": f"{type(exc).__name__}: {exc}"}
        print(json.dumps(resultados[nombre], ensure_ascii=False, indent=1),
              flush=True)

    print("=== VEREDICTO R2 (R9: imagen + movimiento + dos FPS + errores) ===")
    print(json.dumps(resultados, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
