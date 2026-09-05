import { describe, expect, it } from "vitest";
import { enlazarRutas, rutaDeEnlace } from "./rutas";

describe("enlazarRutas", () => {
  it("enlaza la absoluta de Windows", () => {
    expect(enlazarRutas("creé C:\\works\\holamundo.py y funcionó"))
      .toBe("creé [C:\\works\\holamundo.py](open:C:\\works\\holamundo.py) y funcionó");
  });

  it("enlaza la relativa de dos segmentos con extensión", () => {
    expect(enlazarRutas("lee docs/BITACORA-OPTIMIZACION.md entera"))
      .toContain("[docs/BITACORA-OPTIMIZACION.md](open:docs/BITACORA-OPTIMIZACION.md)");
  });

  it("NO enlaza lo que no es un fichero", () => {
    expect(enlazarRutas("24/7 con TCP/IP el 3/9")).toBe("24/7 con TCP/IP el 3/9");
  });

  it("no toca el interior de las vallas de código", () => {
    const conValla = "texto docs/uno.md\n```\ndocs/dentro.md\n```";
    const out = enlazarRutas(conValla);
    expect(out).toContain("[docs/uno.md](open:docs/uno.md)");
    expect(out).not.toContain("[docs/dentro.md]");
  });

  it("devuelve el texto tal cual si está vacío", () => {
    expect(enlazarRutas("")).toBe("");
  });
});

describe("rutaDeEnlace", () => {
  it("extrae la ruta de un open:", () => {
    expect(rutaDeEnlace("open:src/vita/main.c")).toBe("src/vita/main.c");
  });
  it("null para cualquier otro href", () => {
    expect(rutaDeEnlace("https://x.com")).toBeNull();
  });
});
