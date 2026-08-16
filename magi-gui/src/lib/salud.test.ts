import { describe, expect, it } from "vitest";

import { clasificaRotos, puntosChispa, tendencia } from "./salud";

describe("puntosChispa", () => {
  it("una serie vacía no tiene puntos", () => {
    expect(puntosChispa([], 90, 22)).toBe("");
  });

  it("un solo punto va al inicio, centrado verticalmente", () => {
    // Sin rango que recorrer, la chispa es una línea plana.
    expect(puntosChispa([{ dia: "d", media_ms: 5, n: 1 }], 90, 22)).toBe("0,0");
  });

  it("el día más lento queda abajo y el más rápido arriba", () => {
    const pts = puntosChispa(
      [{ dia: "a", media_ms: 100, n: 1 }, { dia: "b", media_ms: 300, n: 1 }],
      90, 22,
    );
    const [rapido, lento] = pts.split(" ");
    expect(Number(rapido.split(",")[1])).toBe(0);   // 100 ms: arriba
    expect(Number(lento.split(",")[1])).toBe(22);   // 300 ms: abajo
  });

  it("una serie plana no divide entre cero", () => {
    const pts = puntosChispa(
      [{ dia: "a", media_ms: 200, n: 1 }, { dia: "b", media_ms: 200, n: 1 }],
      90, 22,
    );
    expect(pts).toBeTruthy();
  });
});

describe("tendencia", () => {
  it("con menos de 4 días no hay pendiente que fiar", () => {
    expect(tendencia([{ dia: "a", media_ms: 1, n: 1 }])).toBeNull();
  });

  it("pasar de 2 s a 9 s es empeorar", () => {
    const serie = [
      { dia: "1", media_ms: 2000, n: 4 },
      { dia: "2", media_ms: 2100, n: 4 },
      { dia: "3", media_ms: 9000, n: 4 },
      { dia: "4", media_ms: 9500, n: 4 },
    ];
    expect(tendencia(serie)).toBe("empeora");
  });

  it("pasar de 8 s a 3 s es mejorar", () => {
    const serie = [
      { dia: "1", media_ms: 8000, n: 4 },
      { dia: "2", media_ms: 8200, n: 4 },
      { dia: "3", media_ms: 3100, n: 4 },
      { dia: "4", media_ms: 2900, n: 4 },
    ];
    expect(tendencia(serie)).toBe("mejora");
  });

  it("un 10 % de ruido no es una tendencia", () => {
    const serie = [
      { dia: "1", media_ms: 3000, n: 4 },
      { dia: "2", media_ms: 3050, n: 4 },
      { dia: "3", media_ms: 3100, n: 4 },
      { dia: "4", media_ms: 3150, n: 4 },
    ];
    expect(tendencia(serie)).toBe("igual");
  });
});

describe("clasificaRotos", () => {
  it("separa los que exigen tu cuenta de los caídos", () => {
    const { imposibles, caidos } = clasificaRotos({
      Claude: "DESCARTADO: exige tu cuenta (cookies).",
      Pi: "DESCARTADO: abre navegador.",
      Groq: "HTTP 402 (medido 13-ago).",
      WeWordle: "HTTP 429 (medido 13-ago).",
    });
    expect(imposibles.map(([p]) => p)).toEqual(["Claude", "Pi"]);
    expect(caidos.map(([p]) => p)).toEqual(["Groq", "WeWordle"]);
  });

  it("sin motivos no hay nada que separar", () => {
    const { imposibles, caidos } = clasificaRotos({});
    expect(imposibles).toEqual([]);
    expect(caidos).toEqual([]);
  });
});
