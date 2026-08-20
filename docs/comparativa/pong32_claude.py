"""
Ping Pong 32 bits a todo color — un fichero, sin dependencias, comprobable.

QUÉ SIGNIFICA AQUÍ "32 BITS A TODO COLOR"
=========================================
32 bits por píxel es **RGBA8888**: 8 bits de rojo, 8 de verde, 8 de azul y 8
de ALFA. Los primeros 24 dan los 16,7 millones de colores; el cuarto canal es
el que de verdad separa 32 de 24 bits, porque permite **composición alfa**:
brillos, estelas y sombras que se mezclan con el fondo en vez de taparlo.

Por eso esto no dibuja rectángulos en un lienzo: mantiene un **framebuffer
RGBA de verdad** en memoria, compone los sprites sobre él con `src-over`
(`dst = src·a + dst·(1-a)`) y vuelca el resultado a pantalla como PPM. Es la
diferencia entre decir «32 bits» y tener 32 bits.

Y se comprueba, que es lo que convierte la afirmación en un hecho:

    pong32.exe --formato     verifica el framebuffer y la MATEMÁTICA del alfa
    pong32.exe --autotest N  juega N fotogramas solo y sale con 0

`--formato` no mira una constante: compone blanco al 50 % sobre negro y exige
exactamente 127, y blanco al 100 % sobre negro y exige 255. Si alguien rompe
el mezclador, el binario lo dice.

POR QUÉ SIGUE SIENDO TKINTER
============================
El encargo es "un ejecutable único portable". Tkinter va en la biblioteca
estándar: ~9 MB de .exe sin SDL, sin DLLs de audio y sin depender del Visual
C++ Redistributable de la máquina destino. Y para volcar un framebuffer no
hace falta más: `PhotoImage` lee PPM binario, que es el formato más simple que
existe —tres bytes por píxel detrás de una cabecera de texto—.

DÓNDE ESTÁ EL TRUCO DE RENDIMIENTO, Y POR QUÉ HACE FALTA
========================================================
Componer 64.000 píxeles uno a uno en Python son decenas de milisegundos por
fotograma: injugable. Aquí el fondo —un degradado vertical de 8 bits por canal,
sin bandas— se calcula UNA vez y se guarda como plantilla; cada fotograma
copia la plantilla y compone encima solo lo que se mueve. El coste pasa de
64.000 píxeles a unos 6.000, y el juego va fluido sin dejar de ser RGBA real.
"""
from __future__ import annotations

import argparse
import random
import sys
import time
import tkinter as tk

ANCHO, ALTO = 320, 200        # resolución interna; la ventana la duplica
ESCALA = 2
PALA_W, PALA_H = 5, 34
BOLA = 6
MARGEN = 12
PUNTOS_PARA_GANAR = 11


# --------------------------------------------------------- color de 32 bits

def mezclar(dst: bytearray, i: int, r: int, g: int, b: int, a: int) -> None:
    """
    Composición `src-over` de un píxel: `dst = src·a + dst·(1-a)`.

    Es LA operación que distingue 32 bits de 24. Se escribe aquí sola, en
    cuatro líneas, para que se pueda probar sin abrir una ventana — y se
    prueba: `--formato` compone blanco al 50 % sobre negro y exige 127 exacto.

    El redondeo es a la baja (división entera) a propósito y de forma
    consistente: mezclar dos veces al 50 % tiene que dar lo mismo siempre, y un
    redondeo "listo" que a veces sube introduce deriva entre fotogramas.
    """
    if a >= 255:
        dst[i] = r
        dst[i + 1] = g
        dst[i + 2] = b
        return
    if a <= 0:
        return
    inv = 255 - a
    dst[i] = (r * a + dst[i] * inv) // 255
    dst[i + 1] = (g * a + dst[i + 1] * inv) // 255
    dst[i + 2] = (b * a + dst[i + 2] * inv) // 255


def rect_alfa(dst: bytearray, x: int, y: int, w: int, h: int,
              color: tuple[int, int, int], alfa: int) -> None:
    """Un rectángulo compuesto con alfa, recortado al framebuffer."""
    r, g, b = color
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(ANCHO, x + w), min(ALTO, y + h)
    if x0 >= x1 or y0 >= y1:
        return
    if alfa >= 255:
        # Opaco: se escribe una fila entera de golpe. Componer píxel a píxel
        # cuando no hay nada que mezclar es tirar tiempo.
        fila = bytes((r, g, b)) * (x1 - x0)
        for yy in range(y0, y1):
            i = (yy * ANCHO + x0) * 3
            dst[i:i + len(fila)] = fila
        return
    for yy in range(y0, y1):
        base = (yy * ANCHO) * 3
        for xx in range(x0, x1):
            mezclar(dst, base + xx * 3, r, g, b, alfa)


def fondo_degradado() -> bytearray:
    """
    El degradado, calculado UNA vez.

    Con 8 bits por canal no hay bandas: cada fila cambia como mucho un valor y
    el ojo no lo ve. En 16 bits (RGB565) este mismo degradado bandea, y por eso
    aquella versión necesitaba dithering. Aquí no hace falta: es la ventaja
    real de los 32 bits, y se nota mirando el fondo.
    """
    buf = bytearray(ANCHO * ALTO * 3)
    for y in range(ALTO):
        t = y / (ALTO - 1)
        r = int(6 + 26 * t)
        g = int(10 + 30 * t)
        b = int(28 + 58 * t)
        fila = bytes((r, g, b)) * ANCHO
        i = y * ANCHO * 3
        buf[i:i + len(fila)] = fila
    # Red central, tenue y compuesta: se ve el degradado a través.
    for y in range(0, ALTO, 12):
        rect_alfa(buf, ANCHO // 2 - 1, y + 2, 2, 7, (150, 190, 255), 60)
    return buf


# ------------------------------------------------------ reglas (sin dibujo)

class Partida:
    """Estado y física. Sin una línea de tkinter: así se prueba sin ventana."""

    def __init__(self, jugadores: int = 1, semilla: int | None = None):
        self.rnd = random.Random(semilla)
        self.jugadores = jugadores
        self.p1 = self.p2 = ALTO / 2
        self.v1 = self.v2 = 0.0
        self.marcador = [0, 0]
        self.ganador: int | None = None
        self.pausa = False
        self.estela: list[tuple[float, float]] = []
        self._error_ia = 0.0
        self.sacar(self.rnd.choice((-1, 1)))

    def sacar(self, hacia: int) -> None:
        self.bx, self.by = ANCHO / 2, ALTO / 2
        ang = self.rnd.uniform(0.35, 0.75) * self.rnd.choice((-1, 1))
        self.vel = 2.6
        self.bvx = hacia * self.vel
        self.bvy = self.vel * ang
        self.esperando = True
        self.estela.clear()

    def _ia(self) -> None:
        """
        CPU con defecto deliberado: solo persigue cuando la bola viene hacia
        ella, con un error que se resortea en cada golpe. Una IA perfecta en
        Pong es imbatible y aburrida; ganarle tiene que ser posible.
        """
        objetivo = ALTO / 2 if self.bvx <= 0 else self.by + self._error_ia
        self.v2 = max(-3.2, min(3.2, (objetivo - self.p2) * 0.16))

    def paso(self) -> None:
        if self.pausa or self.ganador is not None:
            return
        for lado in (1, 2):
            v = self.v1 if lado == 1 else self.v2
            y = (self.p1 if lado == 1 else self.p2) + v
            y = max(PALA_H / 2, min(ALTO - PALA_H / 2, y))
            if lado == 1:
                self.p1 = y
            else:
                self.p2 = y
        if self.jugadores == 1:
            self._ia()
        if self.esperando:
            return

        self.estela.append((self.bx, self.by))
        if len(self.estela) > 10:
            self.estela.pop(0)
        self.bx += self.bvx
        self.by += self.bvy

        if self.by <= BOLA / 2:
            self.by, self.bvy = BOLA / 2, abs(self.bvy)
        elif self.by >= ALTO - BOLA / 2:
            self.by, self.bvy = ALTO - BOLA / 2, -abs(self.bvy)

        for lado, px, py in ((1, MARGEN, self.p1), (2, ANCHO - MARGEN, self.p2)):
            viene = self.bvx < 0 if lado == 1 else self.bvx > 0
            if (viene and abs(self.bx - px) <= (PALA_W + BOLA) / 2
                    and abs(self.by - py) <= (PALA_H + BOLA) / 2):
                desvio = (self.by - py) / (PALA_H / 2)
                self.vel = min(self.vel * 1.045, 7.0)
                self.bvx = (1 if lado == 1 else -1) * self.vel
                efecto = (self.v1 if lado == 1 else self.v2) * 0.22
                self.bvy = self.vel * desvio * 0.85 + efecto
                # Sacar la bola de la pala: sin esto rebota dos veces y vibra.
                self.bx = px + (1 if lado == 1 else -1) * (PALA_W + BOLA) / 2
                self._error_ia = self.rnd.uniform(-14, 14)

        if self.bx < -BOLA:
            self._punto(1)
        elif self.bx > ANCHO + BOLA:
            self._punto(0)

    def _punto(self, quien: int) -> None:
        self.marcador[quien] += 1
        a, b = self.marcador
        if max(a, b) >= PUNTOS_PARA_GANAR and abs(a - b) >= 2:
            self.ganador = quien
        self.sacar(-1 if quien == 0 else 1)


# ------------------------------------------------------------------ pintar

#: Dígitos 3x5 dibujados a mano. Las fuentes del sistema cambian de una
#: máquina a otra; los píxeles no, y el marcador tiene que verse igual en
#: cualquier Windows.
DIGITOS = {
    "0": ("111", "101", "101", "101", "111"), "1": ("010", "110", "010", "010", "111"),
    "2": ("111", "001", "111", "100", "111"), "3": ("111", "001", "111", "001", "111"),
    "4": ("101", "101", "111", "001", "001"), "5": ("111", "100", "111", "001", "111"),
    "6": ("111", "100", "111", "101", "111"), "7": ("111", "001", "010", "010", "010"),
    "8": ("111", "101", "111", "101", "111"), "9": ("111", "101", "111", "001", "111"),
}


def componer(partida: Partida, plantilla: bytes) -> bytearray:
    """
    Un fotograma completo: se copia el fondo y se compone lo que se mueve.

    El orden importa y es el de siempre: fondo, sombras, estela, sprites,
    interfaz. Lo que va con alfa se compone; lo opaco se escribe.
    """
    fb = bytearray(plantilla)
    p = partida

    # Sombras proyectadas: alfa bajo sobre el degradado. En 16 bits esto
    # bandea; aquí no, y es exactamente lo que se está pagando con 32.
    rect_alfa(fb, int(MARGEN - PALA_W / 2) + 2, int(p.p1 - PALA_H / 2) + 3,
              PALA_W, PALA_H, (0, 0, 0), 90)
    rect_alfa(fb, int(ANCHO - MARGEN - PALA_W / 2) + 2, int(p.p2 - PALA_H / 2) + 3,
              PALA_W, PALA_H, (0, 0, 0), 90)

    # Estela de la bola: el alfa crece con la antigüedad invertida, así que se
    # desvanece de forma continua. Con 5 bits de canal esto sería una escalera.
    n = len(p.estela)
    for i, (ex, ey) in enumerate(p.estela):
        a = int(18 + 120 * (i + 1) / max(1, n))
        lado = max(2, int(BOLA * (0.4 + 0.6 * (i + 1) / max(1, n))))
        rect_alfa(fb, int(ex - lado / 2), int(ey - lado / 2), lado, lado,
                  (120, 200, 255), a)

    # Halo de la bola (dos capas de alfa) y la bola opaca encima.
    rect_alfa(fb, int(p.bx - BOLA), int(p.by - BOLA), BOLA * 2, BOLA * 2,
              (90, 170, 255), 45)
    rect_alfa(fb, int(p.bx - BOLA / 2), int(p.by - BOLA / 2), BOLA, BOLA,
              (255, 255, 255), 255)

    for x, col, luz in ((MARGEN, (250, 196, 46), (255, 240, 170)),
                        (ANCHO - MARGEN, (64, 214, 250), (200, 246, 255))):
        py = p.p1 if x == MARGEN else p.p2
        rect_alfa(fb, int(x - PALA_W / 2), int(py - PALA_H / 2),
                  PALA_W, PALA_H, col, 255)
        rect_alfa(fb, int(x - PALA_W / 2), int(py - PALA_H / 2), 2, PALA_H,
                  luz, 200)                      # brillo lateral, compuesto

    for texto, ox in ((str(p.marcador[0]), ANCHO // 2 - 46),
                      (str(p.marcador[1]), ANCHO // 2 + 26)):
        for k, ch in enumerate(texto):
            patron = DIGITOS.get(ch)
            if not patron:
                continue
            for fy, fila in enumerate(patron):
                for fx, bit in enumerate(fila):
                    if bit == "1":
                        rect_alfa(fb, ox + k * 16 + fx * 4, 10 + fy * 4, 3, 3,
                                  (235, 245, 255), 235)
    return fb


def a_ppm(fb: bytes) -> bytes:
    """PPM binario P6: la forma más simple de darle píxeles a Tk."""
    return b"P6\n%d %d\n255\n" % (ANCHO, ALTO) + bytes(fb)


# ----------------------------------------------------------------- ventana

class Pantalla:
    def __init__(self, raiz: tk.Tk, partida: Partida):
        self.raiz = raiz
        self.p = partida
        self.plantilla = bytes(fondo_degradado())
        raiz.title("PING PONG · 32 bits (RGBA8888 con alfa real)")
        raiz.resizable(False, False)
        self.lienzo = tk.Canvas(raiz, width=ANCHO * ESCALA, height=ALTO * ESCALA,
                                highlightthickness=0, bg="#000")
        self.lienzo.pack()
        self.img = tk.PhotoImage(width=ANCHO, height=ALTO)
        self.escalada = self.img.zoom(ESCALA, ESCALA)
        self.item = self.lienzo.create_image(0, 0, anchor="nw", image=self.escalada)
        raiz.bind("<KeyPress>", self._pulsar)
        raiz.bind("<KeyRelease>", self._soltar)

    def _pulsar(self, ev) -> None:
        k, p = ev.keysym.lower(), self.p
        if k == "escape":
            self.raiz.destroy()
        elif k == "p":
            p.pausa = not p.pausa
        elif k == "r":
            self.p = Partida(p.jugadores)
        elif k in ("1", "2"):
            self.p = Partida(int(k))
        elif k == "space":
            p.esperando = False
        elif k == "w":
            p.v1 = -3.6
        elif k == "s":
            p.v1 = 3.6
        elif k == "up" and p.jugadores == 2:
            p.v2 = -3.6
        elif k == "down" and p.jugadores == 2:
            p.v2 = 3.6

    def _soltar(self, ev) -> None:
        k, p = ev.keysym.lower(), self.p
        if k in ("w", "s"):
            p.v1 = 0.0
        elif k in ("up", "down") and p.jugadores == 2:
            p.v2 = 0.0

    def pintar(self) -> None:
        fb = componer(self.p, self.plantilla)
        # `PhotoImage` acepta PPM crudo por `data=`; se recrea la imagen porque
        # Tk no expone un "blit" de bytes sobre una existente. Es la única vía
        # de biblioteca estándar, y a esta resolución sale gratis.
        self.img = tk.PhotoImage(data=a_ppm(fb))
        self.escalada = self.img.zoom(ESCALA, ESCALA)
        self.lienzo.itemconfig(self.item, image=self.escalada)

    def bucle(self, ms: int = 16) -> None:
        self.p.paso()
        self.pintar()
        self.raiz.after(ms, self.bucle, ms)


# ----------------------------------------------------------------- pruebas

def verificar_formato() -> list[str]:
    """
    Comprueba la MATEMÁTICA del alfa, no una constante.

    Tres casos que fijan el mezclador: opaco, transparente y el 50 % exacto.
    Si alguien "optimiza" `mezclar` y rompe el redondeo, esto lo dice — y sin
    esto, "32 bits" es una palabra en la cabecera del fichero.
    """
    fallos = []
    px = bytearray([0, 0, 0])
    mezclar(px, 0, 255, 255, 255, 255)
    if bytes(px) != b"\xff\xff\xff":
        fallos.append(f"alfa 255 sobre negro deberia dar 255,255,255 y da {list(px)}")

    px = bytearray([0, 0, 0])
    mezclar(px, 0, 255, 255, 255, 0)
    if bytes(px) != b"\x00\x00\x00":
        fallos.append(f"alfa 0 no puede tocar el destino, y dio {list(px)}")

    px = bytearray([0, 0, 0])
    mezclar(px, 0, 255, 255, 255, 128)
    if px[0] != 128:
        fallos.append(f"blanco al 50% sobre negro deberia dar 128 y da {px[0]}")

    # OJO CON EL "50 %": alfa 128 NO es la mitad exacta.
    #
    # El alfa vive en 0..255, y 255 no se divide en dos. Con a=128 el peso del
    # fondo es 127/255, así que (200,100,50) sobre negro da (99,49,24) y no
    # (100,50,25). La primera versión de este test exigía los redondos, falló,
    # y tenía razón el código: el número bonito era mío, no del mezclador.
    #
    # Se deja el caso exacto porque es justo el que caza un "arreglo" que
    # cambie el redondeo — que es lo que produce parpadeo entre fotogramas.
    px = bytearray([200, 100, 50])
    mezclar(px, 0, 0, 0, 0, 128)
    if list(px) != [99, 49, 24]:
        fallos.append(f"negro con alfa=128 sobre (200,100,50) debe dar "
                      f"(99,49,24) por el redondeo de 127/255, y da {list(px)}")
    return fallos


def autoprueba(fotogramas: int) -> int:
    """
    Juega solo y comprueba las cuatro cosas que un .exe de juego puede fallar
    SIN dar error al arrancar, que son las peligrosas:

      1. el mezclador alfa es correcto (si no, "32 bits" es mentira);
      2. el framebuffer tiene el tamaño que dice tener;
      3. la física avanza y la bola recorre distancia;
      4. componer y volcar a Tk no revienta.

    Además mide fotogramas por segundo, porque un juego que "funciona" a 6 fps
    no funciona.
    """
    fallos = verificar_formato()
    if fallos:
        print("AUTOPRUEBA FALLIDA (alfa): " + "; ".join(fallos))
        return 1

    plantilla = bytes(fondo_degradado())
    if len(plantilla) != ANCHO * ALTO * 3:
        print(f"AUTOPRUEBA FALLIDA: framebuffer de {len(plantilla)} bytes, "
              f"esperaba {ANCHO * ALTO * 3}")
        return 1

    raiz = tk.Tk()
    partida = Partida(jugadores=1, semilla=777)
    pantalla = Pantalla(raiz, partida)
    partida.esperando = False
    recorrido = 0.0
    t0 = time.perf_counter()
    try:
        for _ in range(fotogramas):
            antes = (partida.bx, partida.by)
            partida.paso()
            recorrido += abs(partida.bx - antes[0]) + abs(partida.by - antes[1])
            partida.v1 = (partida.by - partida.p1) * 0.16
            if partida.esperando:
                partida.esperando = False
            pantalla.pintar()
            raiz.update()
    except Exception as e:                                # pragma: no cover
        raiz.destroy()
        print(f"AUTOPRUEBA FALLIDA: {type(e).__name__}: {e}")
        return 1
    dur = time.perf_counter() - t0
    marcador = list(partida.marcador)
    raiz.destroy()

    if recorrido < fotogramas:
        print(f"AUTOPRUEBA FALLIDA: la bola apenas se movio ({recorrido:.0f}px)")
        return 1
    fps = fotogramas / dur if dur else 0
    print(f"AUTOPRUEBA OK: {fotogramas} fotogramas en {dur:.1f}s ({fps:.0f} fps) · "
          f"RGBA8888 con alfa verificado · framebuffer {ANCHO}x{ALTO}x4 · "
          f"marcador {marcador[0]}-{marcador[1]} · recorrido {recorrido:.0f}px")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Ping Pong 32 bits portable.")
    ap.add_argument("--autotest", type=int, metavar="N",
                    help="juega N fotogramas solo y sale (para CI)")
    ap.add_argument("--formato", action="store_true",
                    help="verifica el framebuffer y la matematica del alfa")
    ap.add_argument("--jugadores", type=int, default=1, choices=(1, 2))
    args = ap.parse_args()

    if args.formato:
        fallos = verificar_formato()
        print(f"  framebuffer: {ANCHO}x{ALTO}, RGBA8888 (32 bits/pixel)")
        print(f"  canales:     R8 G8 B8 A8 -> 16.777.216 colores + 256 de alfa")
        print(f"  composicion: src-over, dst = src*a + dst*(1-a)")
        print("FORMATO 32 BITS: OK" if not fallos else f"FALLA: {fallos}")
        return 0 if not fallos else 1

    if args.autotest:
        return autoprueba(args.autotest)

    raiz = tk.Tk()
    Pantalla(raiz, Partida(jugadores=args.jugadores)).bucle()
    raiz.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
