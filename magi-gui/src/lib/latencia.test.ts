/**
 * La lectura de los cuellos de botella.
 *
 * Lo que se prueba aquí no es que la tabla salga bonita, es que el panel diga
 * la verdad sobre lo que enseña. Tres afirmaciones, y las tres son decisiones
 * de diseño que se pueden discutir — por eso están fijadas:
 *
 *   1. Se ordena por p95, no por media. Lo primero que se ve es lo que más
 *      hace esperar.
 *   2. Una muestra pequeña se presenta como anécdota, no como percentil.
 *   3. «Lento» e «irregular» se distinguen, porque no se arreglan igual.
 */
import { describe, expect, it } from "vitest";
import {
  Estadistica, hayDatos, irregularidad, lectura, ms, ordenadas,
} from "./latencia";

const est = (p: Partial<Estadistica>): Estadistica => ({
  clave: "x", n: 100, mediana_ms: 1000, p95_ms: 2000, peor_ms: 3000,
  fiable: true, ...p,
});

describe("ms", () => {
  it("no enseña decimales por debajo del segundo", () => {
    expect(ms(30)).toBe("30 ms");
    expect(ms(999)).toBe("999 ms");
  });
  it("pasa a segundos y a minutos cuando toca", () => {
    expect(ms(1500)).toBe("1.5 s");
    expect(ms(95_000)).toBe("1 min 35 s");
  });
  it("no inventa un número cuando no hay medida", () => {
    expect(ms(null)).toBe("—");
    expect(ms(undefined)).toBe("—");
    expect(ms(NaN)).toBe("—");
  });
});

describe("ordenadas", () => {
  it("ordena por p95 y no por mediana", () => {
    // El primero tarda más de media; el segundo tiene la cola mala.
    const filas = [
      est({ clave: "estable", mediana_ms: 3000, p95_ms: 3100 }),
      est({ clave: "irregular", mediana_ms: 500, p95_ms: 20_000 }),
    ];
    expect(ordenadas(filas).map((f) => f.clave)).toEqual(["irregular", "estable"]);
  });

  it("descarta las filas sin medida en vez de pintarlas con guiones", () => {
    const filas = [est({ clave: "con" }), est({ clave: "sin", p95_ms: null })];
    expect(ordenadas(filas).map((f) => f.clave)).toEqual(["con"]);
  });

  it("recorta al top pedido", () => {
    const filas = Array.from({ length: 9 }, (_, i) =>
      est({ clave: `a${i}`, p95_ms: i * 100 }));
    expect(ordenadas(filas, 5)).toHaveLength(5);
    expect(ordenadas(filas, 5)[0].clave).toBe("a8");
  });

  it("no revienta sin datos", () => {
    expect(ordenadas(undefined)).toEqual([]);
    expect(ordenadas([])).toEqual([]);
  });
});

describe("irregularidad", () => {
  it("mide cuánto se aparta el p95 de la mediana", () => {
    expect(irregularidad(est({ mediana_ms: 1000, p95_ms: 10_000 }))).toBe(10);
    expect(irregularidad(est({ mediana_ms: 1000, p95_ms: 1100 }))).toBe(1.1);
  });
  it("devuelve null en vez de dividir por cero", () => {
    expect(irregularidad(est({ mediana_ms: 0 }))).toBeNull();
    expect(irregularidad(est({ p95_ms: null }))).toBeNull();
  });
});

describe("lectura", () => {
  it("distingue lento de irregular, porque no se arreglan igual", () => {
    const irregular = lectura(est({ mediana_ms: 500, p95_ms: 20_000 }));
    expect(irregular).toContain("Irregular");
    expect(irregular).toContain("se atasca");

    const estable = lectura(est({ mediana_ms: 3000, p95_ms: 3300 }));
    expect(estable).toContain("Estable");
    expect(estable).not.toContain("atasca");
  });

  it("una muestra pequeña se presenta como anécdota, no como percentil", () => {
    const texto = lectura(est({ n: 3, fiable: false }));
    expect(texto).toContain("3 medidas");
    expect(texto).toContain("no un percentil");
  });
});

describe("hayDatos", () => {
  it("false mientras el sistema no haya medido nada", () => {
    expect(hayDatos(undefined)).toBe(false);
    expect(hayDatos({})).toBe(false);
    expect(hayDatos({ agentes: [], familias: [], herramientas: [] })).toBe(false);
  });
  it("false si la consulta falló: mejor no enseñar sección que enseñarla vacía", () => {
    expect(hayDatos({ error: "no such table", agentes: [est({})] })).toBe(false);
  });
  it("true en cuanto hay una sola fila con medida", () => {
    expect(hayDatos({ herramientas: [est({})] })).toBe(true);
  });
});
