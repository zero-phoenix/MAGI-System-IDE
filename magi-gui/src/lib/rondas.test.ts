/**
 * El debate agrupado en rondas.
 *
 * Lo que se prueba no es que el diagrama quede bonito: es que conteste a las
 * tres preguntas que se le hacen a un gráfico de un debate y que la versión
 * plana no podía contestar —en qué ronda vamos, qué se decidió en cada una, y
 * qué falta para cerrar la actual.
 */
import { describe, expect, it } from "vitest";
import {
  MensajeAgente, agruparEnRondas, conclusionDe, primeraFrase, tituloDelDebate,
} from "./rondas";

const mel = (c = "Propongo el enfoque A."): MensajeAgente =>
  ({ agent: "MELCHIOR", role: "propone", content: c, family: "gpt" });
const bal = (c = "Falla con entrada vacía."): MensajeAgente =>
  ({ agent: "BALTHASAR", role: "critica", content: c, family: "gemini" });
const cas = (dec = "APPROVED", c = "Síntesis lista."): MensajeAgente =>
  ({ agent: "CASPER", role: "arbitro", content: c, stats: `Decisión: ${dec}`,
     family: "command" });

describe("agruparEnRondas", () => {
  it("una ronda va de Melchior a Casper", () => {
    const r = agruparEnRondas([mel(), bal(), cas()]);
    expect(r).toHaveLength(1);
    expect(r[0].numero).toBe(1);
    expect(r[0].cerrada).toBe(true);
    expect(r[0].nodos.map((n) => n.agente))
      .toEqual(["MELCHIOR", "BALTHASAR", "CASPER"]);
  });

  it("cada intervención de Melchior abre una ronda nueva", () => {
    const r = agruparEnRondas([mel(), bal(), cas(), mel(), bal(), cas()]);
    expect(r).toHaveLength(2);
    expect(r[1].numero).toBe(2);
  });

  it("una ronda a medias marca quién va y quién falta", () => {
    // Sin esta distinción, una ronda en curso parece una ronda rota.
    const r = agruparEnRondas([mel(), bal()]);
    expect(r[0].cerrada).toBe(false);
    expect(r[0].nodos.map((n) => n.estado))
      .toEqual(["hecho", "hecho", "en curso"]);
  });

  it("con solo la tesis, el crítico está en curso y el árbitro pendiente", () => {
    const r = agruparEnRondas([mel()]);
    expect(r[0].nodos.map((n) => n.estado))
      .toEqual(["hecho", "en curso", "pendiente"]);
  });

  it("lo que llega antes del primer Melchior no se cuela en la ronda 1", () => {
    const ruido: MensajeAgente = { agent: "SISTEMA", content: "arrancando" };
    const r = agruparEnRondas([ruido, mel(), bal(), cas()]);
    expect(r).toHaveLength(1);
    expect(r[0].nodos.filter((n) => n.estado === "hecho")).toHaveLength(3);
  });

  it("sin mensajes no inventa una ronda vacía", () => {
    expect(agruparEnRondas([])).toEqual([]);
    expect(agruparEnRondas(undefined as any)).toEqual([]);
  });
});

describe("conclusionDe", () => {
  it("lee el veredicto del dato estructurado antes que del texto", () => {
    // `stats` viene del backend; el contenido es prosa donde la palabra puede
    // aparecer citando otra cosa. El orden no es indiferente.
    const m = cas("APPROVED", "En la ronda previa hubo un REJECTED por rutas.");
    expect(conclusionDe(m)).toBe("aprobada");
  });

  it("cae al texto cuando no hay stats", () => {
    const m: MensajeAgente = {
      agent: "CASPER", content: "Listo.\n\nDECISIÓN: NECESITA REVISIÓN" };
    expect(conclusionDe(m)).toBe("necesita revisión");
  });

  it("traduce los códigos internos a algo legible", () => {
    expect(conclusionDe(cas("REJECTED_NEEDS_WORK"))).toBe("necesita revisión");
    expect(conclusionDe(cas("APPROVED"))).toBe("aprobada");
  });

  it("sin Casper todavía, no hay conclusión que enseñar", () => {
    expect(conclusionDe(undefined)).toBeNull();
    expect(agruparEnRondas([mel(), bal()])[0].conclusion).toBeNull();
  });
});

describe("primeraFrase", () => {
  it("resume en prosa y deja fuera el código", () => {
    // Una caja del diagrama que diga «```python» no resume nada.
    const t = "Integro ambas posiciones.\n\n```python\nprint('x')\n```";
    expect(primeraFrase(t)).toBe("Integro ambas posiciones.");
  });

  it("si solo hay código, lo dice callándose en vez de enseñar un trozo", () => {
    expect(primeraFrase("```python\nprint('x')\n```")).toBe("");
  });

  it("recorta lo largo con puntos suspensivos", () => {
    const largo = "a".repeat(200);
    const r = primeraFrase(largo, 40);
    expect(r).toHaveLength(40);
    expect(r.endsWith("…")).toBe(true);
  });

  it("no revienta sin texto", () => {
    expect(primeraFrase(undefined)).toBe("");
    expect(primeraFrase("")).toBe("");
  });
});

describe("tituloDelDebate", () => {
  it("dice en qué ronda vamos y a quién se espera", () => {
    const r = agruparEnRondas([mel(), bal(), cas(), mel(), bal()]);
    expect(tituloDelDebate(r)).toBe("Ronda 2 de 2 · en curso (CASPER)");
  });

  it("con el debate cerrado dice cuántas rondas costó", () => {
    expect(tituloDelDebate(agruparEnRondas([mel(), bal(), cas()])))
      .toBe("1 ronda · cerrada");
    expect(tituloDelDebate(agruparEnRondas([mel(), bal(), cas(), mel(), bal(), cas()])))
      .toBe("2 rondas · cerrada");
  });

  it("sin rondas lo dice, en vez de enseñar un cero", () => {
    expect(tituloDelDebate([])).toBe("Sin rondas todavía");
  });
});
