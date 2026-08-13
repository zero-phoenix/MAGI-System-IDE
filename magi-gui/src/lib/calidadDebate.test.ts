/**
 * ¿Es un debate o es teatro?
 *
 * Estos tests no comprueban que el número sea «correcto» —Jaccard es tosco a
 * propósito y no hay un valor verdadero que exigir—, sino que **detecta el
 * caso extremo**, que es el único que se puede afirmar con honestidad: dos
 * textos casi idénticos, o una ronda que concluye lo mismo que la anterior.
 */
import { describe, expect, it } from "vitest";

import {
  UMBRAL_ECO,
  UMBRAL_SIN_CAMBIO,
  avisoDelDebate,
  calidadDelDebate,
  divergencia,
  vocabulario,
} from "./calidadDebate";
import type { Ronda } from "./rondas";

function ronda(
  numero: number,
  melchior: string,
  balthasar: string,
  conclusion: string | null,
): Ronda {
  return {
    numero,
    cerrada: conclusion !== null,
    conclusion,
    nodos: [
      { agente: "MELCHIOR", papel: "tesis", estado: "hecho", texto: melchior },
      { agente: "BALTHASAR", papel: "antítesis", estado: "hecho", texto: balthasar },
      { agente: "CASPER", papel: "síntesis", estado: "hecho", texto: conclusion ?? "" },
    ],
  };
}

describe("vocabulario", () => {
  it("quita las palabras vacías, o todo se parecería a todo", () => {
    // Sin esto, dos textos cualesquiera en español comparten «de», «la» y
    // «que», y la divergencia sale baja aunque no tengan nada que ver.
    const v = vocabulario("El mutex de la sección crítica que protege");
    expect(v.has("de")).toBe(false);
    expect(v.has("que")).toBe(false);
    expect(v.has("mutex")).toBe(true);
  });

  it("ignora los bloques de código", () => {
    // Dos agentes que citan el mismo fragmento compartirían decenas de
    // palabras idénticas y parecerían de acuerdo sin haberlo estado.
    const v = vocabulario("Propongo esto:\n```python\nsemaforo = Semaphore(3)\n```");
    expect(v.has("semaphore")).toBe(false);
    expect(v.has("propongo")).toBe(true);
  });

  it("no distingue mayúsculas ni acentos", () => {
    expect(vocabulario("SECCIÓN")).toEqual(vocabulario("seccion"));
  });
});

describe("divergencia", () => {
  it("dos textos idénticos divergen 0", () => {
    const t = "el mutex protege la seccion critica entre hilos concurrentes";
    expect(divergencia(t, t)).toBe(0);
  });

  it("dos textos sin nada en común divergen 1", () => {
    expect(
      divergencia(
        "mutex semaforo concurrencia hilos bloqueo",
        "receta bizcocho horno harina azucar",
      ),
    ).toBe(1);
  });

  it("devuelve null si no hay material, en vez de fingir un 0", () => {
    // Un 0 diría «coinciden del todo», que es una afirmación fuerte sobre un
    // texto vacío. «No lo sé» es la respuesta honesta.
    expect(divergencia("", "algo con palabras suficientes aqui")).toBeNull();
    expect(divergencia(undefined, undefined)).toBeNull();
    expect(divergencia("dos palabras", "tres palabras cortas")).toBeNull();
  });

  it("es simétrica", () => {
    const a = "el mutex garantiza exclusion mutua entre hilos";
    const b = "el semaforo lleva un contador de recursos disponibles";
    expect(divergencia(a, b)).toBe(divergencia(b, a));
  });
});

describe("calidadDelDebate", () => {
  it("detecta que BALTHASAR está repitiendo a MELCHIOR", () => {
    // EL CASO QUE IMPORTA. Si la antítesis converge con la tesis, el enjambre
    // paga tres llamadas por el trabajo de una y nadie se entera.
    const r = ronda(
      1,
      "Propongo usar un mutex para proteger la seccion critica de los hilos",
      "Coincido: usar un mutex protege la seccion critica de los hilos",
      "Aprobado el mutex",
    );
    const [c] = calidadDelDebate([r]);
    expect(c.divergenciaTesisAntitesis).toBeLessThan(UMBRAL_ECO);
    expect(c.lectura).toContain("no está refutando");
  });

  it("un debate de verdad diverge", () => {
    const r = ronda(
      1,
      "Propongo un mutex porque garantiza exclusion mutua barata y simple",
      "Objeto: bajo contencion alta conviene un semaforo con contador de permisos",
      "Se adopta el semaforo",
    );
    const [c] = calidadDelDebate([r]);
    expect(c.divergenciaTesisAntitesis).toBeGreaterThan(UMBRAL_ECO);
  });

  it("detecta que la segunda ronda no aportó nada", () => {
    // Si la ronda 2 concluye lo mismo que la 1, las rondas de más son latencia
    // y cuota a cambio de nada. Conviene saberlo antes de recomendarlas.
    const conclusion = "Se adopta el semaforo con tres permisos concurrentes";
    const rondas = [
      ronda(1, "propongo mutex exclusion mutua simple", "objeto semaforo contador permisos", conclusion),
      ronda(2, "insisto mutex exclusion", "reitero semaforo contador", conclusion),
    ];
    const c = calidadDelDebate(rondas);
    expect(c[1].cambioRespectoAnterior).toBeLessThan(UMBRAL_SIN_CAMBIO);
  });

  it("la primera ronda no tiene con qué compararse", () => {
    const c = calidadDelDebate([ronda(1, "a b c d e f", "g h i j k l", "m n o p")]);
    expect(c[0].cambioRespectoAnterior).toBeNull();
  });

  it("una ronda a medias no revienta ni miente", () => {
    const aMedias: Ronda = {
      numero: 1,
      cerrada: false,
      conclusion: null,
      nodos: [{ agente: "MELCHIOR", papel: "tesis", estado: "hecho", texto: "propongo algo" }],
    };
    const [c] = calidadDelDebate([aMedias]);
    expect(c.divergenciaTesisAntitesis).toBeNull();
    expect(c.lectura).toContain("sin material");
  });
});

describe("avisoDelDebate", () => {
  it("calla cuando el debate va bien", () => {
    // Un aviso que aparece siempre es ruido y se deja de leer a la tercera
    // vez — y entonces tampoco se lee el que sí importa.
    const r = ronda(
      1,
      "Propongo un mutex porque garantiza exclusion mutua barata y simple",
      "Objeto: bajo contencion alta conviene un semaforo con contador de permisos",
      "Se adopta el semaforo",
    );
    expect(avisoDelDebate([r])).toBeNull();
  });

  it("avisa, con el número de ronda, cuando la antítesis es un eco", () => {
    const r = ronda(
      3,
      "Propongo usar un mutex para proteger la seccion critica de los hilos",
      "Coincido: usar un mutex protege la seccion critica de los hilos",
      "Aprobado",
    );
    const aviso = avisoDelDebate([r]);
    expect(aviso).toContain("Ronda 3");
    expect(aviso).toContain("BALTHASAR");
  });

  it("sin rondas no dice nada", () => {
    expect(avisoDelDebate([])).toBeNull();
  });
});
