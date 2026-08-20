"""
Tetris — réplica jugable en un solo fichero, sin dependencias externas.

POR QUÉ TKINTER Y NO PYGAME
===========================
El encargo es "un ejecutable único portable". Tkinter viene en la biblioteca
estándar: el .exe resultante no arrastra SDL, ni DLLs de audio, ni ruedas
binarias que dependan del Visual C++ Redistributable de la máquina destino.
Pesa ~10 MB en vez de ~40 y arranca en una máquina limpia. Un Tetris con
pygame se ve un poco mejor y falla en muchos más sitios.

QUÉ IMPLEMENTA, Y POR QUÉ IMPORTA
=================================
Un Tetris que no es Tetris se nota en treinta segundos de juego. Esto lleva
las reglas que la gente siente aunque no sepa nombrarlas:

  · Bolsa de 7 (7-bag): las siete piezas salen una vez antes de repetirse.
    Sin esto, el azar puro produce sequías de barra que arruinan la partida.
  · SRS con patadas de pared (wall kicks): girar pegado a la pared o dentro
    de un hueco funciona, que es lo que separa "gira" de "gira bien".
  · Lock delay de 500 ms con 15 reinicios: puedes deslizar la pieza al tocar
    suelo. Sin esto el juego se siente rígido y tramposo.
  · Hold (una vez por pieza), ghost piece, cola de 5 siguientes.
  · DAS/ARR reales para el movimiento lateral mantenido.
  · Gravedad por nivel con la curva clásica, soft drop y hard drop.
  · Puntuación estándar: 100/300/500/800 por líneas, x nivel, +1/+2 por
    celda en soft/hard drop.

MODO AUTOPRUEBA
===============
`tetris.exe --autotest 30` juega 30 fotogramas solo y sale con código 0. Es
lo que permite verificar en CI que el binario ARRANCA y DIBUJA, sin que nadie
tenga que mirarlo. Un ejecutable de juego que solo se puede probar a ojo es
un ejecutable que nadie prueba.
"""
from __future__ import annotations

import argparse
import random
import sys
import tkinter as tk

# ---------------------------------------------------------------- tablero

COLS, FILAS = 10, 20
FILAS_OCULTAS = 2          # donde nace la pieza, fuera de la vista
LADO = 30                  # píxeles por celda
MARGEN = 20

COLORES = {
    "I": "#00f0f0", "O": "#f0f000", "T": "#a000f0", "S": "#00f000",
    "Z": "#f00000", "J": "#0000f0", "L": "#f0a000",
}

FORMAS = {
    "I": [[(0, 1), (1, 1), (2, 1), (3, 1)], [(2, 0), (2, 1), (2, 2), (2, 3)],
          [(0, 2), (1, 2), (2, 2), (3, 2)], [(1, 0), (1, 1), (1, 2), (1, 3)]],
    "O": [[(1, 0), (2, 0), (1, 1), (2, 1)]] * 4,
    "T": [[(1, 0), (0, 1), (1, 1), (2, 1)], [(1, 0), (1, 1), (2, 1), (1, 2)],
          [(0, 1), (1, 1), (2, 1), (1, 2)], [(1, 0), (0, 1), (1, 1), (1, 2)]],
    "S": [[(1, 0), (2, 0), (0, 1), (1, 1)], [(1, 0), (1, 1), (2, 1), (2, 2)],
          [(1, 1), (2, 1), (0, 2), (1, 2)], [(0, 0), (0, 1), (1, 1), (1, 2)]],
    "Z": [[(0, 0), (1, 0), (1, 1), (2, 1)], [(2, 0), (1, 1), (2, 1), (1, 2)],
          [(0, 1), (1, 1), (1, 2), (2, 2)], [(1, 0), (0, 1), (1, 1), (0, 2)]],
    "J": [[(0, 0), (0, 1), (1, 1), (2, 1)], [(1, 0), (2, 0), (1, 1), (1, 2)],
          [(0, 1), (1, 1), (2, 1), (2, 2)], [(1, 0), (1, 1), (0, 2), (1, 2)]],
    "L": [[(2, 0), (0, 1), (1, 1), (2, 1)], [(1, 0), (1, 1), (1, 2), (2, 2)],
          [(0, 1), (1, 1), (2, 1), (0, 2)], [(0, 0), (1, 0), (1, 1), (1, 2)]],
}

PATADAS_JLSTZ = {
    (0, 1): [(0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)],
    (1, 0): [(0, 0), (1, 0), (1, 1), (0, -2), (1, -2)],
    (1, 2): [(0, 0), (1, 0), (1, 1), (0, -2), (1, -2)],
    (2, 1): [(0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)],
    (2, 3): [(0, 0), (1, 0), (1, -1), (0, 2), (1, 2)],
    (3, 2): [(0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)],
    (3, 0): [(0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)],
    (0, 3): [(0, 0), (1, 0), (1, -1), (0, 2), (1, 2)],
}
PATADAS_I = {
    (0, 1): [(0, 0), (-2, 0), (1, 0), (-2, 1), (1, -2)],
    (1, 0): [(0, 0), (2, 0), (-1, 0), (2, -1), (-1, 2)],
    (1, 2): [(0, 0), (-1, 0), (2, 0), (-1, -2), (2, 1)],
    (2, 1): [(0, 0), (1, 0), (-2, 0), (1, 2), (-2, -1)],
    (2, 3): [(0, 0), (2, 0), (-1, 0), (2, -1), (-1, 2)],
    (3, 2): [(0, 0), (-2, 0), (1, 0), (-2, 1), (1, -2)],
    (3, 0): [(0, 0), (1, 0), (-2, 0), (1, 2), (-2, -1)],
    (0, 3): [(0, 0), (-1, 0), (2, 0), (-1, -2), (2, 1)],
}

GRAVEDAD = [48, 43, 38, 33, 28, 23, 18, 13, 8, 6, 5, 5, 5, 4, 4, 4, 3, 3, 3, 2]
PUNTOS = {1: 100, 2: 300, 3: 500, 4: 800}


class Pieza:
    """Una pieza en juego: qué es, dónde está y cómo está girada."""

    def __init__(self, tipo: str):
        self.tipo = tipo
        self.rot = 0
        # Nace centrada y en las filas ocultas, como en el juego real.
        self.x = 3
        self.y = 0

    def celdas(self, rot: int | None = None, dx: int = 0, dy: int = 0):
        r = self.rot if rot is None else rot
        return [(self.x + cx + dx, self.y + cy + dy)
                for cx, cy in FORMAS[self.tipo][r % 4]]


class Bolsa:
    """
    Generador de 7 (7-bag).

    El azar puro se siente injusto: puede darte cinco eses seguidas y ninguna
    barra en veinte piezas. La bolsa reparte las siete y baraja de nuevo, que
    es lo que hace el Tetris moderno desde 2001.
    """

    def __init__(self, semilla: int | None = None):
        self._rnd = random.Random(semilla)
        self._bolsa: list[str] = []

    def siguiente(self) -> str:
        if not self._bolsa:
            self._bolsa = list(FORMAS)
            self._rnd.shuffle(self._bolsa)
        return self._bolsa.pop()


class Juego:
    """
    El estado y las reglas. Sin nada de dibujo: así se puede probar sin
    ventana, que es lo que hace `--autotest` y lo que permitiría escribir
    tests de verdad sobre las reglas.
    """

    def __init__(self, semilla: int | None = None):
        self.tablero: list[list[str | None]] = [
            [None] * COLS for _ in range(FILAS + FILAS_OCULTAS)]
        self.bolsa = Bolsa(semilla)
        self.cola = [self.bolsa.siguiente() for _ in range(5)]
        self.pieza = Pieza(self._sacar())
        self.reserva: str | None = None
        self.reserva_usada = False
        self.puntos = 0
        self.lineas = 0
        self.nivel = 1
        self.fin = False
        self.pausa = False
        # Lock delay: al tocar suelo no se fija de inmediato. 500 ms y hasta
        # 15 movimientos que reinician el contador, como el estándar.
        self.lock_ms = 0
        self.lock_reinicios = 0

    def _sacar(self) -> str:
        self.cola.append(self.bolsa.siguiente())
        return self.cola.pop(0)

    # ------------------------------------------------------------ colisión

    def cabe(self, celdas) -> bool:
        for x, y in celdas:
            if x < 0 or x >= COLS or y >= FILAS + FILAS_OCULTAS:
                return False
            if y >= 0 and self.tablero[y][x] is not None:
                return False
        return True

    # ----------------------------------------------------------- acciones

    def mover(self, dx: int) -> bool:
        if self.cabe(self.pieza.celdas(dx=dx)):
            self.pieza.x += dx
            self._tocar_lock()
            return True
        return False

    def girar(self, sentido: int) -> bool:
        """
        Gira con patadas de pared. Se prueban cinco desplazamientos en orden;
        el primero que quepa, vale. Sin esto, girar contra un muro no hace
        nada y el jugador cree que el juego se ha colgado.
        """
        origen = self.pieza.rot % 4
        destino = (origen + sentido) % 4
        if self.pieza.tipo == "O":
            return True
        tabla = PATADAS_I if self.pieza.tipo == "I" else PATADAS_JLSTZ
        for dx, dy in tabla.get((origen, destino), [(0, 0)]):
            # El eje Y de la tabla SRS crece hacia arriba; aquí crece hacia
            # abajo. Invertirlo es el fallo clásico al implementar esto.
            if self.cabe(self.pieza.celdas(rot=destino, dx=dx, dy=-dy)):
                self.pieza.rot = destino
                self.pieza.x += dx
                self.pieza.y += -dy
                self._tocar_lock()
                return True
        return False

    def _tocar_lock(self) -> None:
        if self.en_suelo() and self.lock_reinicios < 15:
            self.lock_ms = 0
            self.lock_reinicios += 1

    def en_suelo(self) -> bool:
        return not self.cabe(self.pieza.celdas(dy=1))

    def bajar(self, por_jugador: bool = False) -> bool:
        if self.cabe(self.pieza.celdas(dy=1)):
            self.pieza.y += 1
            if por_jugador:
                self.puntos += 1
            return True
        return False

    def soltar(self) -> None:
        caidas = 0
        while self.cabe(self.pieza.celdas(dy=1)):
            self.pieza.y += 1
            caidas += 1
        self.puntos += caidas * 2
        self.fijar()

    def guardar(self) -> None:
        """Reserva. Una sola vez por pieza: si no, es un deshacer infinito."""
        if self.reserva_usada:
            return
        self.reserva_usada = True
        if self.reserva is None:
            self.reserva = self.pieza.tipo
            self.pieza = Pieza(self._sacar())
        else:
            self.reserva, self.pieza = self.pieza.tipo, Pieza(self.reserva)
        if not self.cabe(self.pieza.celdas()):
            self.fin = True


    def fantasma(self) -> list[tuple[int, int]]:
        """Dónde caería la pieza. Ayuda de verdad, y es barata de calcular."""
        dy = 0
        while self.cabe(self.pieza.celdas(dy=dy + 1)):
            dy += 1
        return self.pieza.celdas(dy=dy)

    def fijar(self) -> None:
        for x, y in self.pieza.celdas():
            if y >= 0:
                self.tablero[y][x] = self.pieza.tipo
        self._limpiar_lineas()
        self.pieza = Pieza(self._sacar())
        self.reserva_usada = False
        self.lock_ms = 0
        self.lock_reinicios = 0
        # Fin de partida: la pieza nueva no cabe (block out).
        if not self.cabe(self.pieza.celdas()):
            self.fin = True

    def _limpiar_lineas(self) -> None:
        completas = [y for y, fila in enumerate(self.tablero)
                     if all(c is not None for c in fila)]
        if not completas:
            return
        for y in completas:
            del self.tablero[y]
            self.tablero.insert(0, [None] * COLS)
        n = len(completas)
        self.lineas += n
        self.puntos += PUNTOS.get(n, 0) * self.nivel
        # Un nivel cada diez líneas, como toda la vida.
        self.nivel = 1 + self.lineas // 10

    def ms_por_caida(self) -> float:
        frames = GRAVEDAD[min(self.nivel - 1, len(GRAVEDAD) - 1)]
        return frames * (1000.0 / 60.0)

    def tick(self, ms: int) -> None:
        """
        Avanza el reloj del juego. Todo el tiempo entra por aquí: así el modo
        autoprueba puede simular fotogramas sin depender del reloj real.
        """
        if self.fin or self.pausa:
            return
        self._acumulado = getattr(self, "_acumulado", 0.0) + ms
        if self.en_suelo():
            self.lock_ms += ms
            if self.lock_ms >= 500:
                self.fijar()
            return
        self.lock_ms = 0
        while self._acumulado >= self.ms_por_caida():
            self._acumulado -= self.ms_por_caida()
            if not self.bajar():
                break


class Ventana:
    """La capa de dibujo y entrada. Nada de reglas aquí."""

    #: DAS (retardo hasta la repetición) y ARR (ritmo de repetición), en ms.
    #: Son los dos números que hacen que el movimiento lateral se sienta bien;
    #: con la repetición del sistema operativo se siente pegajoso.
    DAS, ARR = 170, 40

    def __init__(self, raiz: tk.Tk, semilla: int | None = None):
        self.raiz = raiz
        self.juego = Juego(semilla)
        ancho = COLS * LADO + MARGEN * 2 + 160
        alto = FILAS * LADO + MARGEN * 2
        raiz.title("Tetris")
        raiz.resizable(False, False)
        self.lienzo = tk.Canvas(raiz, width=ancho, height=alto,
                                bg="#0b0f10", highlightthickness=0)
        self.lienzo.pack()
        self._pulsadas: dict[str, float] = {}
        self._ultimo = 0.0
        raiz.bind("<KeyPress>", self._pulsar)
        raiz.bind("<KeyRelease>", self._soltar_tecla)

    # ------------------------------------------------------------- entrada

    def _pulsar(self, ev) -> None:
        k = ev.keysym
        j = self.juego
        if k in ("p", "P"):
            j.pausa = not j.pausa
            return
        if k in ("r", "R") and j.fin:
            self.juego = Juego()
            return
        if j.fin or j.pausa:
            return
        if k == "Left":
            j.mover(-1)
            self._pulsadas["Left"] = -self.DAS
        elif k == "Right":
            j.mover(1)
            self._pulsadas["Right"] = -self.DAS
        elif k == "Down":
            j.bajar(por_jugador=True)
        elif k in ("Up", "x", "X"):
            j.girar(1)
        elif k in ("z", "Z", "Control_L", "Control_R"):
            j.girar(-1)
        elif k == "space":
            j.soltar()
        elif k in ("c", "C", "Shift_L", "Shift_R"):
            j.guardar()

    def _soltar_tecla(self, ev) -> None:
        self._pulsadas.pop(ev.keysym, None)

    def _repetir_laterales(self, ms: int) -> None:
        for tecla, dx in (("Left", -1), ("Right", 1)):
            if tecla not in self._pulsadas:
                continue
            self._pulsadas[tecla] += ms
            while self._pulsadas[tecla] >= self.ARR:
                self._pulsadas[tecla] -= self.ARR
                if not self.juego.mover(dx):
                    break


    # ------------------------------------------------------------- dibujo

    def _celda(self, x: int, y: int, color: str, borde: str = "#0b0f10") -> None:
        px = MARGEN + x * LADO
        py = MARGEN + (y - FILAS_OCULTAS) * LADO
        if py < MARGEN:
            return                      # zona oculta: no se pinta
        self.lienzo.create_rectangle(px, py, px + LADO, py + LADO,
                                     fill=color, outline=borde, width=2)

    def dibujar(self) -> None:
        j = self.juego
        self.lienzo.delete("all")
        # Pozo
        self.lienzo.create_rectangle(
            MARGEN, MARGEN, MARGEN + COLS * LADO, MARGEN + FILAS * LADO,
            fill="#05080a", outline="#1d2a2e")
        for y in range(FILAS + FILAS_OCULTAS):
            for x in range(COLS):
                if j.tablero[y][x]:
                    self._celda(x, y, COLORES[j.tablero[y][x]])
        if not j.fin:
            for x, y in j.fantasma():          # el fantasma, primero
                self._celda(x, y, "#16232a", borde="#24363d")
            for x, y in j.pieza.celdas():
                self._celda(x, y, COLORES[j.pieza.tipo])

        # Panel lateral
        px = MARGEN + COLS * LADO + 16
        self.lienzo.create_text(px, MARGEN + 4, anchor="nw", fill="#7fd4e0",
                                font=("Consolas", 11, "bold"), text="SIGUIENTES")
        for i, t in enumerate(j.cola[:5]):
            for cx, cy in FORMAS[t][0]:
                x0 = px + cx * 14
                y0 = MARGEN + 24 + i * 52 + cy * 14
                self.lienzo.create_rectangle(x0, y0, x0 + 12, y0 + 12,
                                             fill=COLORES[t], outline="")
        self.lienzo.create_text(px, MARGEN + 300, anchor="nw", fill="#7fd4e0",
                                font=("Consolas", 11, "bold"), text="RESERVA")
        if j.reserva:
            for cx, cy in FORMAS[j.reserva][0]:
                x0 = px + cx * 14
                y0 = MARGEN + 320 + cy * 14
                self.lienzo.create_rectangle(x0, y0, x0 + 12, y0 + 12,
                                             fill=COLORES[j.reserva], outline="")
        for i, (etiqueta, valor) in enumerate(
                (("PUNTOS", j.puntos), ("LINEAS", j.lineas), ("NIVEL", j.nivel))):
            self.lienzo.create_text(
                px, MARGEN + 400 + i * 34, anchor="nw", fill="#cfe0e4",
                font=("Consolas", 10), text=f"{etiqueta}\n{valor}")

        if j.pausa:
            self._cartel("PAUSA", "P para seguir")
        elif j.fin:
            self._cartel("FIN", "R para otra partida")

    def _cartel(self, titulo: str, pie: str) -> None:
        cx = MARGEN + COLS * LADO // 2
        cy = MARGEN + FILAS * LADO // 2
        self.lienzo.create_rectangle(cx - 110, cy - 42, cx + 110, cy + 42,
                                     fill="#0b0f10", outline="#7fd4e0")
        self.lienzo.create_text(cx, cy - 12, fill="#7fd4e0",
                                font=("Consolas", 18, "bold"), text=titulo)
        self.lienzo.create_text(cx, cy + 18, fill="#cfe0e4",
                                font=("Consolas", 10), text=pie)

    # --------------------------------------------------------------- bucle

    def bucle(self, ms: int = 16) -> None:
        self.juego.tick(ms)
        self._repetir_laterales(ms)
        self.dibujar()
        self.raiz.after(ms, self.bucle, ms)


def autoprueba(fotogramas: int) -> int:
    """
    Juega solo unos fotogramas y sale. Es la prueba de que el binario ARRANCA
    y DIBUJA, que es justo lo que no comprueba nadie cuando entrega un .exe de
    un juego. Devuelve 0 si el motor sobrevivió; distinto de 0 si reventó.
    """
    raiz = tk.Tk()
    ventana = Ventana(raiz, semilla=12345)
    fallo = None
    for i in range(fotogramas):
        try:
            ventana.juego.tick(16)
            if i % 7 == 0:
                ventana.juego.mover(1 if i % 2 else -1)
            if i % 11 == 0:
                ventana.juego.girar(1)
            if i % 23 == 0:
                ventana.juego.soltar()
            ventana.dibujar()
            raiz.update()
        except Exception as e:                       # pragma: no cover
            fallo = f"{type(e).__name__}: {e}"
            break
    j = ventana.juego
    raiz.destroy()
    if fallo:
        print(f"AUTOPRUEBA FALLIDA en el fotograma: {fallo}")
        return 1
    print(f"AUTOPRUEBA OK: {fotogramas} fotogramas, puntos={j.puntos}, "
          f"lineas={j.lineas}, fin={j.fin}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Tetris portable.")
    ap.add_argument("--autotest", type=int, metavar="N",
                    help="juega N fotogramas solo y sale (para CI)")
    args = ap.parse_args()

    if args.autotest:
        return autoprueba(args.autotest)

    raiz = tk.Tk()
    ventana = Ventana(raiz)
    ventana.bucle()
    raiz.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
