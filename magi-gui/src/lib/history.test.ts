import { describe, expect, it } from "vitest";
import { MAX_TERMINAL_CHARS, appendBounded, tail } from "./history";

describe("terminal acotado", () => {
  it("no toca nada mientras cabe", () => {
    expect(appendBounded("hola", "mundo")).toBe("holamundo\n");
  });

  it("recorta por el principio al pasarse", () => {
    const largo = "x".repeat(500);
    const r = appendBounded(largo, "nuevo", 100);
    expect(r.length).toBeLessThan(300);
    expect(r).toContain("nuevo");
  });

  it("dice cuánto tiró, en vez de acortar en silencio", () => {
    // Un historial que se acorta sin avisar hace dudar de si faltó salida o
    // es que nunca se produjo.
    const r = appendBounded("linea\n".repeat(100), "final", 50);
    expect(r).toContain("descartados");
  });

  it("corta en un salto de línea, no a mitad de línea", () => {
    const r = appendBounded("aaaa\nbbbb\ncccc\ndddd\n", "eeee", 20);
    const cuerpo = r.split("\n").slice(1).join("\n");
    expect(cuerpo.startsWith("aaa")).toBe(false);
  });

  it("aguanta el caso que lo motivó sin dispararse", () => {
    // 4000 anexiones daban 4,9 MB y 2,7 ms de escaneo por repintado.
    let t = "";
    for (let i = 0; i < 4000; i++) t = appendBounded(t, "salida de herramienta ".repeat(20));
    expect(t.length).toBeLessThanOrEqual(MAX_TERMINAL_CHARS + 200);
  });

  it("un solo texto mayor que el tope no revienta", () => {
    const r = appendBounded("", "y".repeat(5000), 100);
    expect(r.length).toBeLessThan(5200);
    expect(typeof r).toBe("string");
  });
});

describe("cola de la lista", () => {
  it("devuelve todo si cabe", () => {
    const { visible, hidden } = tail([1, 2, 3], 10);
    expect(visible).toEqual([1, 2, 3]);
    expect(hidden).toBe(0);
  });

  it("se queda con los ÚLTIMOS, que son los que interesan", () => {
    const { visible, hidden } = tail([1, 2, 3, 4, 5], 2);
    expect(visible).toEqual([4, 5]);
    expect(hidden).toBe(3);
  });

  it("no muta el array de entrada", () => {
    const original = [1, 2, 3, 4];
    tail(original, 2);
    expect(original).toEqual([1, 2, 3, 4]);
  });

  it("con lista vacía no inventa nada", () => {
    expect(tail([], 5)).toEqual({ visible: [], hidden: 0 });
  });
});

describe("regresión: no perder lo recién añadido", () => {
  it("conserva el texto nuevo aunque lo anterior no tenga saltos de línea", () => {
    // Mi primera versión buscaba el salto de línea sobre la cadena ENTERA, así
    // que el único que encontraba era el que acababa de añadir: se tiraba el
    // texto nuevo y quedaba solo el aviso. En un terminal, la última línea es
    // justo la que hace falta ver.
    const sinSaltos = "x".repeat(500);
    const r = appendBounded(sinSaltos, "LA LINEA QUE IMPORTA", 100);
    expect(r).toContain("LA LINEA QUE IMPORTA");
  });

  it("conserva el texto nuevo con muchas anexiones seguidas", () => {
    let t = "";
    for (let i = 0; i < 500; i++) t = appendBounded(t, `linea ${i}`, 300);
    expect(t).toContain("linea 499");
    expect(t.length).toBeLessThanOrEqual(400);
  });
});
