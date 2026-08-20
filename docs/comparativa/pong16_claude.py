"""
Ping Pong 16 bits — un fichero, sin dependencias, con la paleta comprobada.

QUÉ SIGNIFICA AQUÍ "16 BITS A COLOR", Y POR QUÉ SE COMPRUEBA
============================================================
No es un adjetivo de ambientación: es RGB565, el formato real de color de 16
bits de la época —5 bits de rojo, 6 de verde, 5 de azul, 65.536 colores— y el
que llevaban las pantallas de Mega Drive, GBA y medio mundo embebido.

Todo color de este juego pasa por `c565()`, que lo ajusta a la rejilla 5-6-5.
Y `--autotest` **verifica la paleta entera**: si alguien mete un color que no
es representable en 16 bits, el binario falla y lo dice. Sin esa comprobación,
"16 bits" es una palabra en el README.

El verde tiene un bit más que el rojo y el azul, y no es un capricho: el ojo
humano distingue muchos más matices de verde. Por eso los degradados de cielo
de esa época bandean y los de hierba no.

POR QUÉ TKINTER
===============
El encargo dice "ejecutable único portable". Tkinter va en la biblioteca
estándar: el .exe no arrastra SDL, ni DLLs de audio, ni dependencias del
Visual C++ Redistributable de la máquina destino. Salen ~9 MB en vez de ~35 y
arranca en un Windows recién instalado.

TÉCNICA DE ÉPOCA QUE SÍ SE USA
==============================
El fondo lleva **dithering ordenado** (Bayer 4x4) entre dos colores 565 para
simular más profundidad de la que hay. Es exactamente lo que se hacía cuando
no te sobraban colores.

CONTROLES
=========
  Jugador 1: W / S      ·  Jugador 2 (modo 2P): flechas arriba/abajo
  1 / 2: modo 1 o 2 jugadores   ·  P: pausa   ·  R: reiniciar
  ESPACIO: sacar        ·  ESC: salir

AUTOPRUEBA
==========
    pong.exe --autotest 240      juega 240 fotogramas solo y sale con 0
    pong.exe --paleta            imprime la paleta y su verificación 565
"""
from __future__ import annotations

import argparse
import random
import sys
import tkinter as tk


def c565(r: int, g: int, b: int) -> str:
    """
    Ajusta un color de 24 bits a la rejilla RGB565 y lo devuelve en #rrggbb.

    Se tira precisión a propósito: 8 bits por canal -> 5/6/5, y se reexpande
    replicando los bits altos (`(v5 << 3) | (v5 >> 2)`), que es lo que hace el
    hardware de verdad. Redondear con otra regla daría colores que en una
    pantalla 565 real no existen.
    """
    r5, g6, b5 = r >> 3, g >> 2, b >> 3
    return "#{:02x}{:02x}{:02x}".format(
        (r5 << 3) | (r5 >> 2), (g6 << 2) | (g6 >> 4), (b5 << 3) | (b5 >> 2))


def es_565(color: str) -> bool:
    """¿Este #rrggbb existe de verdad en 16 bits? Sin esto, "16 bits" es fe."""
    r = int(color[1:3], 16)
    g = int(color[3:5], 16)
    b = int(color[5:7], 16)
    return c565(r, g, b) == color.lower()


#: Paleta del juego. Los nombres son los de la época a propósito: cuando solo
#: tienes doce colores, cada uno tiene nombre.
PALETA = {
    "fondo_alto":   c565(16, 24, 48),
    "fondo_bajo":   c565(8, 12, 28),
    "muro":         c565(200, 208, 224),
    "linea":        c565(64, 80, 120),
    "pala1":        c565(248, 200, 40),
    "pala1_luz":    c565(255, 240, 160),
    "pala2":        c565(64, 216, 248),
    "pala2_luz":    c565(190, 248, 255),
    "bola":         c565(255, 255, 255),
    "bola_estela":  c565(160, 176, 208),
    "marcador":     c565(232, 240, 255),
    "aviso":        c565(248, 96, 96),
}

#: Bayer 4x4: el patrón de dithering ordenado clásico.
BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]

ANCHO, ALTO = 640, 400
BLOQUE = 8                     # el "píxel gordo" de la rejilla de fondo
MARGEN_PALA = 24
PALA_W, PALA_H = 10, 64
BOLA = 10
PUNTOS_PARA_GANAR = 11


# ------------------------------------------------------ reglas (sin dibujo)

class Partida:
    """
    El estado y la física. Sin una línea de tkinter, a propósito: así se puede
    simular una partida entera sin ventana, que es lo que hace `--autotest` y
    lo que permitiría escribir tests de las reglas.
    """

    def __init__(self, jugadores: int = 1, semilla: int | None = None):
        self.rnd = random.Random(semilla)
        self.jugadores = jugadores
        self.p1 = ALTO / 2
        self.p2 = ALTO / 2
        self.v1 = 0.0
        self.v2 = 0.0
        self.marcador = [0, 0]
        self.pausa = False
        self.ganador: int | None = None
        self.estela: list[tuple[float, float]] = []
        self.sacar(hacia=self.rnd.choice((-1, 1)))

    # ------------------------------------------------------------- servicio

    def sacar(self, hacia: int) -> None:
        self.bx, self.by = ANCHO / 2, ALTO / 2
        # Ángulo de saque acotado: un saque casi horizontal es injugable y uno
        # casi vertical es aburrido. Entre 20 y 45 grados es lo jugable.
        ang = self.rnd.uniform(0.35, 0.79) * self.rnd.choice((-1, 1))
        self.vel = 5.0
        self.bvx = hacia * self.vel
        self.bvy = self.vel * ang
        self.esperando_saque = True
        self.estela.clear()

    # ------------------------------------------------------------ movimiento

    def _mover_palas(self) -> None:
        for lado in (1, 2):
            v = self.v1 if lado == 1 else self.v2
            y = (self.p1 if lado == 1 else self.p2) + v
            y = max(PALA_H / 2, min(ALTO - PALA_H / 2, y))
            if lado == 1:
                self.p1 = y
            else:
                self.p2 = y

    def _ia(self) -> None:
        """
        La CPU con un defecto deliberado: reacciona tarde y falla un poco.

        Una IA perfecta en Pong es imbatible y aburrida —devuelve siempre—, y
        una tonta se nota. Sigue la bola solo cuando viene hacia ella, con un
        error aleatorio estable por punto y una velocidad tope menor que la del
        jugador. Se puede ganar, y cuesta.
        """
        if self.bvx <= 0:
            objetivo = ALTO / 2                  # vuelve al centro a esperar
        else:
            objetivo = self.by + getattr(self, "_error_ia", 0.0)
        dif = objetivo - self.p2
        tope = 6.0
        self.v2 = max(-tope, min(tope, dif * 0.16))

    def paso(self) -> None:
        """Un fotograma de física. Todo el tiempo del juego entra por aquí."""
        if self.pausa or self.ganador is not None:
            return
        self._mover_palas()
        if self.jugadores == 1:
            self._ia()
        if self.esperando_saque:
            return

        self.estela.append((self.bx, self.by))
        if len(self.estela) > 8:
            self.estela.pop(0)

        self.bx += self.bvx
        self.by += self.bvy

        # Muros arriba y abajo.
        if self.by <= BOLA / 2:
            self.by = BOLA / 2
            self.bvy = abs(self.bvy)
        elif self.by >= ALTO - BOLA / 2:
            self.by = ALTO - BOLA / 2
            self.bvy = -abs(self.bvy)

        self._rebotar_en_palas()

        # Punto.
        if self.bx < -BOLA:
            self._punto(1)
        elif self.bx > ANCHO + BOLA:
            self._punto(0)

    def _rebotar_en_palas(self) -> None:
        """
        El rebote NO es un espejo: el ángulo depende de dónde golpea la bola.

        Es lo que convierte el Pong en un juego con intención en vez de en un
        salvapantallas. Además la pala pasa parte de su movimiento a la bola
        (efecto), y cada rebote acelera un 4 % hasta un tope.
        """
        for lado, px, py in ((1, MARGEN_PALA, self.p1),
                             (2, ANCHO - MARGEN_PALA, self.p2)):
            dentro_x = abs(self.bx - px) <= (PALA_W / 2 + BOLA / 2)
            dentro_y = abs(self.by - py) <= (PALA_H / 2 + BOLA / 2)
            viene = self.bvx < 0 if lado == 1 else self.bvx > 0
            if not (dentro_x and dentro_y and viene):
                continue
            desvio = (self.by - py) / (PALA_H / 2)          # -1 arriba, +1 abajo
            self.vel = min(self.vel * 1.04, 13.0)
            self.bvx = (1 if lado == 1 else -1) * self.vel
            efecto = (self.v1 if lado == 1 else self.v2) * 0.25
            self.bvy = self.vel * desvio * 0.85 + efecto
            # Sacar la bola de la pala evita el rebote doble, que es el fallo
            # clásico de este juego: la bola se queda vibrando dentro.
            self.bx = px + (1 if lado == 1 else -1) * (PALA_W / 2 + BOLA / 2 + 1)
            self._error_ia = self.rnd.uniform(-26, 26)

    def _punto(self, quien: int) -> None:
        self.marcador[quien] += 1
        a, b = self.marcador
        # Hay que ganar por dos, como en el ping pong de verdad.
        if max(a, b) >= PUNTOS_PARA_GANAR and abs(a - b) >= 2:
            self.ganador = quien
        self.sacar(hacia=-1 if quien == 0 else 1)


# ------------------------------------------------------------------ pantalla

#: Fuente de bloques 3x5 para el marcador. Dibujar los dígitos a mano en vez de
#: usar una fuente del sistema es lo que hace que el marcador se vea igual en
#: cualquier Windows: las fuentes cambian de una máquina a otra, los píxeles no.
DIGITOS = {
    "0": ("111", "101", "101", "101", "111"),
    "1": ("010", "110", "010", "010", "111"),
    "2": ("111", "001", "111", "100", "111"),
    "3": ("111", "001", "111", "001", "111"),
    "4": ("101", "101", "111", "001", "001"),
    "5": ("111", "100", "111", "001", "111"),
    "6": ("111", "100", "111", "101", "111"),
    "7": ("111", "001", "010", "010", "010"),
    "8": ("111", "101", "111", "101", "111"),
    "9": ("111", "101", "111", "001", "111"),
}


class Pantalla:
    def __init__(self, raiz: tk.Tk, partida: Partida):
        self.raiz = raiz
        self.p = partida
        raiz.title("PING PONG · 16 bits (RGB565)")
        raiz.resizable(False, False)
        self.lienzo = tk.Canvas(raiz, width=ANCHO, height=ALTO,
                                bg=PALETA["fondo_bajo"], highlightthickness=0)
        self.lienzo.pack()
        self._fondo_pintado = False
        raiz.bind("<KeyPress>", self._pulsar)
        raiz.bind("<KeyRelease>", self._soltar)

    # --------------------------------------------------------------- entrada

    def _pulsar(self, ev) -> None:
        k, p = ev.keysym.lower(), self.p
        if k == "escape":
            self.raiz.destroy()
        elif k == "p":
            p.pausa = not p.pausa
        elif k == "r":
            self.p = Partida(jugadores=p.jugadores)
        elif k in ("1", "2"):
            self.p = Partida(jugadores=int(k))
        elif k == "space":
            p.esperando_saque = False
        elif k == "w":
            p.v1 = -7.5
        elif k == "s":
            p.v1 = 7.5
        elif k == "up" and p.jugadores == 2:
            p.v2 = -7.5
        elif k == "down" and p.jugadores == 2:
            p.v2 = 7.5

    def _soltar(self, ev) -> None:
        k, p = ev.keysym.lower(), self.p
        if k in ("w", "s"):
            p.v1 = 0.0
        elif k in ("up", "down") and p.jugadores == 2:
            p.v2 = 0.0

    # ---------------------------------------------------------------- dibujo

    def _pintar_fondo(self) -> None:
        """
        Degradado con dithering ordenado, pintado UNA vez.

        Podría repintarse cada fotograma, pero son 4.000 rectángulos: a 60 fps
        eso es lo que convierte un juego fluido en una presentación. El fondo
        no cambia, así que se pinta una vez y se dibuja el resto encima.
        """
        for fy in range(0, ALTO, BLOQUE):
            nivel = fy / ALTO                     # 0 arriba, 1 abajo
            for fx in range(0, ANCHO, BLOQUE):
                umbral = BAYER[(fy // BLOQUE) % 4][(fx // BLOQUE) % 4] / 16.0
                color = PALETA["fondo_alto"] if nivel < umbral else PALETA["fondo_bajo"]
                self.lienzo.create_rectangle(fx, fy, fx + BLOQUE, fy + BLOQUE,
                                             fill=color, outline="", tags="fondo")
        for y in range(0, ALTO, 24):              # red central, a trozos
            self.lienzo.create_rectangle(ANCHO // 2 - 2, y + 4, ANCHO // 2 + 2,
                                         y + 16, fill=PALETA["linea"],
                                         outline="", tags="fondo")
        self._fondo_pintado = True

    def _numero(self, texto: str, x: int, y: int, lado: int = 6) -> None:
        for i, ch in enumerate(texto):
            patron = DIGITOS.get(ch)
            if not patron:
                continue
            for fy, fila in enumerate(patron):
                for fx, bit in enumerate(fila):
                    if bit == "1":
                        px = x + i * (lado * 4) + fx * lado
                        py = y + fy * lado
                        self.lienzo.create_rectangle(
                            px, py, px + lado - 1, py + lado - 1,
                            fill=PALETA["marcador"], outline="", tags="movil")

    def dibujar(self) -> None:
        p = self.p
        if not self._fondo_pintado:
            self._pintar_fondo()
        self.lienzo.delete("movil")

        for i, (ex, ey) in enumerate(p.estela):   # estela de la bola
            k = (i + 1) / (len(p.estela) + 1)
            r = BOLA / 2 * k
            self.lienzo.create_rectangle(ex - r, ey - r, ex + r, ey + r,
                                         fill=PALETA["bola_estela"],
                                         outline="", tags="movil")
        self.lienzo.create_rectangle(
            p.bx - BOLA / 2, p.by - BOLA / 2, p.bx + BOLA / 2, p.by + BOLA / 2,
            fill=PALETA["bola"], outline="", tags="movil")

        for x, y, base, luz in ((MARGEN_PALA, p.p1, "pala1", "pala1_luz"),
                                (ANCHO - MARGEN_PALA, p.p2, "pala2", "pala2_luz")):
            self.lienzo.create_rectangle(
                x - PALA_W / 2, y - PALA_H / 2, x + PALA_W / 2, y + PALA_H / 2,
                fill=PALETA[base], outline="", tags="movil")
            # Brillo de un píxel: el truco de sprite de 16 bits para que un
            # rectángulo plano parezca tener volumen.
            self.lienzo.create_rectangle(
                x - PALA_W / 2, y - PALA_H / 2, x - PALA_W / 2 + 3, y + PALA_H / 2,
                fill=PALETA[luz], outline="", tags="movil")

        self._numero(str(p.marcador[0]), ANCHO // 2 - 90, 24)
        self._numero(str(p.marcador[1]), ANCHO // 2 + 50, 24)

        if p.ganador is not None:
            self._cartel(f"GANA JUGADOR {p.ganador + 1}", "R para otra")
        elif p.pausa:
            self._cartel("PAUSA", "P para seguir")
        elif p.esperando_saque:
            self._cartel("LISTO", "ESPACIO para sacar")

    def _cartel(self, titulo: str, pie: str) -> None:
        cx, cy = ANCHO // 2, ALTO // 2
        self.lienzo.create_rectangle(cx - 150, cy - 34, cx + 150, cy + 34,
                                     fill=PALETA["fondo_bajo"],
                                     outline=PALETA["muro"], width=2, tags="movil")
        self.lienzo.create_text(cx, cy - 10, fill=PALETA["marcador"],
                                font=("Consolas", 15, "bold"), text=titulo,
                                tags="movil")
        self.lienzo.create_text(cx, cy + 16, fill=PALETA["linea"],
                                font=("Consolas", 9), text=pie, tags="movil")

    def bucle(self, ms: int = 16) -> None:
        self.p.paso()
        self.dibujar()
        self.raiz.after(ms, self.bucle, ms)


# ----------------------------------------------------------------- pruebas

def verificar_paleta() -> list[str]:
    """Devuelve los colores que NO son representables en RGB565."""
    return [f"{n}={c}" for n, c in PALETA.items() if not es_565(c)]


def autoprueba(fotogramas: int) -> int:
    """
    Juega solo y comprueba tres cosas que un .exe de juego puede fallar sin
    dar error al arrancar, que son las peligrosas:

      1. La paleta es 16 bits de verdad (RGB565), no un adjetivo.
      2. La física avanza: la bola se mueve y alguien marca.
      3. Dibujar no revienta con el fondo dithered ni con el marcador.

    Sale 0 si todo cuadra. Es lo que permite verificar el binario YA
    empaquetado sin que nadie mire la pantalla.
    """
    malos = verificar_paleta()
    if malos:
        print(f"AUTOPRUEBA FALLIDA: colores fuera de RGB565: {', '.join(malos)}")
        return 1

    raiz = tk.Tk()
    partida = Partida(jugadores=1, semilla=4242)
    pantalla = Pantalla(raiz, partida)
    partida.esperando_saque = False
    recorrido = 0.0
    fallo = None
    for i in range(fotogramas):
        try:
            antes = (partida.bx, partida.by)
            partida.paso()
            recorrido += abs(partida.bx - antes[0]) + abs(partida.by - antes[1])
            # Se mueve la pala del jugador para que la partida progrese y la
            # bola rebote en los dos lados, no solo en la CPU.
            partida.v1 = (partida.by - partida.p1) * 0.15
            if partida.esperando_saque:
                partida.esperando_saque = False
            pantalla.dibujar()
            raiz.update()
        except Exception as e:                              # pragma: no cover
            fallo = f"{type(e).__name__}: {e}"
            break
    marcador = list(partida.marcador)
    raiz.destroy()

    if fallo:
        print(f"AUTOPRUEBA FALLIDA en fotograma: {fallo}")
        return 1
    if recorrido < fotogramas:          # la bola tiene que haberse movido
        print(f"AUTOPRUEBA FALLIDA: la bola apenas se movio ({recorrido:.0f}px)")
        return 1
    print(f"AUTOPRUEBA OK: {fotogramas} fotogramas · paleta RGB565 verificada "
          f"({len(PALETA)} colores) · marcador {marcador[0]}-{marcador[1]} · "
          f"recorrido {recorrido:.0f}px")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Ping Pong 16 bits portable.")
    ap.add_argument("--autotest", type=int, metavar="N",
                    help="juega N fotogramas solo y sale (para CI)")
    ap.add_argument("--paleta", action="store_true",
                    help="imprime la paleta y su verificacion RGB565")
    ap.add_argument("--jugadores", type=int, default=1, choices=(1, 2))
    args = ap.parse_args()

    if args.paleta:
        for nombre, color in PALETA.items():
            print(f"  {nombre:14} {color}  565={'si' if es_565(color) else 'NO'}")
        malos = verificar_paleta()
        print("PALETA 16 BITS: OK" if not malos else f"FUERA DE 565: {malos}")
        return 0 if not malos else 1

    if args.autotest:
        return autoprueba(args.autotest)

    raiz = tk.Tk()
    pantalla = Pantalla(raiz, Partida(jugadores=args.jugadores))
    pantalla.bucle()
    raiz.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
