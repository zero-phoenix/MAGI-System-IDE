/**
 * Tests del diff (§7.3).
 *
 * Primeros tests de la interfaz: hasta aquí había 443 en Python y CERO en la
 * GUI, así que la regla "sin tests verdes no hay release" solo valía para la
 * mitad del sistema. Empiezan por el diff porque es la pieza que sostiene una
 * decisión del usuario — aprobar un cambio— y donde equivocarse no da error,
 * da una revisión que parece correcta.
 *
 * Cada uno de los cuatro primeros bloques corresponde a una forma concreta en
 * la que fallaba el `oldLines.includes(line)` anterior.
 */
import { describe, expect, it } from "vitest";
import { MAX_LCS_LINES, diffLines, diffSummary } from "./diff";

const texto = (...l: string[]) => l.join("\n");

describe("los cuatro fallos del diff anterior", () => {
  it("muestra los BORRADOS, que el anterior no mostraba nunca", () => {
    const d = diffLines(texto("a", "b", "c"), texto("a", "c"));
    const borradas = d.lines.filter((l) => l.op === "borrada");
    expect(borradas).toHaveLength(1);
    expect(borradas[0].text).toBe("b");
    expect(d.removed).toBe(1);
  });

  it("detecta una línea MOVIDA, que antes pasaba por sin cambios", () => {
    // "z" sigue existiendo en el original, así que `includes` decía que no
    // era nueva y el cambio salía invisible.
    const d = diffLines(texto("z", "a", "b"), texto("a", "b", "z"));
    expect(d.added + d.removed).toBeGreaterThan(0);
  });

  it("detecta líneas REPETIDAS añadidas", () => {
    // Añadir dos '}' cuando ya había uno: `includes` decía que ya existía.
    const d = diffLines(texto("f() {", "}"), texto("f() {", "}", "g() {", "}"));
    expect(d.added).toBe(2);
  });

  it("no recorre el original entero por cada línea", () => {
    // Prestacional, pero es un contrato: 3000 líneas con un cambio en medio
    // deben resolverse al instante gracias al recorte de prefijo y sufijo.
    const base = Array.from({ length: 3000 }, (_, i) => `línea ${i}`);
    const nuevo = [...base];
    nuevo[1500] = "línea 1500 MODIFICADA";
    const t0 = performance.now();
    const d = diffLines(base.join("\n"), nuevo.join("\n"));
    expect(performance.now() - t0).toBeLessThan(500);
    expect(d.added).toBe(1);
    expect(d.removed).toBe(1);
  });
});

describe("corrección del alineamiento", () => {
  it("dos textos iguales no tienen ningún cambio", () => {
    const d = diffLines(texto("a", "b"), texto("a", "b"));
    expect(d.added).toBe(0);
    expect(d.removed).toBe(0);
    expect(d.lines.every((l) => l.op === "igual")).toBe(true);
  });

  it("un original vacío es todo añadido", () => {
    const d = diffLines("", texto("a", "b"));
    expect(d.added).toBe(2);
    expect(d.removed).toBe(0);
  });

  it("un resultado vacío es todo borrado", () => {
    const d = diffLines(texto("a", "b"), "");
    expect(d.removed).toBe(2);
    expect(d.added).toBe(0);
  });

  it("dos vacíos no producen una línea fantasma", () => {
    // "".split("\n") devuelve [""] en JavaScript: sin tratarlo, un fichero
    // vacío aparece con una línea en blanco que nadie escribió.
    expect(diffLines("", "").lines).toHaveLength(0);
  });

  it("numera las líneas según el fichero al que pertenecen", () => {
    const d = diffLines(texto("a", "b", "c"), texto("a", "X", "c"));
    const borrada = d.lines.find((l) => l.op === "borrada")!;
    const añadida = d.lines.find((l) => l.op === "añadida")!;
    expect(borrada.oldNumber).toBe(2);
    expect(borrada.newNumber).toBeNull();
    expect(añadida.newNumber).toBe(2);
    expect(añadida.oldNumber).toBeNull();
  });

  it("mantiene la numeración correcta después de una inserción", () => {
    const d = diffLines(texto("a", "b"), texto("a", "NUEVA", "b"));
    const ultima = d.lines[d.lines.length - 1];
    expect(ultima.text).toBe("b");
    expect(ultima.oldNumber).toBe(2);
    expect(ultima.newNumber).toBe(3);
  });

  it("agrupa la sustitución como borrada y luego añadida", () => {
    // Se lee mejor que intercaladas, y es lo que hace `git`.
    const d = diffLines(texto("a", "viejo", "z"), texto("a", "nuevo", "z"));
    const ops = d.lines.map((l) => l.op);
    expect(ops).toEqual(["igual", "borrada", "añadida", "igual"]);
  });

  it("reconstruye el texto nuevo a partir del resultado", () => {
    // La comprobación que atrapa cualquier error de alineamiento: quedarse
    // con lo que no está borrado tiene que dar exactamente el fichero nuevo.
    const viejo = texto("uno", "dos", "tres", "cuatro");
    const nuevo = texto("uno", "TRES", "cuatro", "cinco");
    const d = diffLines(viejo, nuevo);
    const rehecho = d.lines
      .filter((l) => l.op !== "borrada")
      .map((l) => l.text)
      .join("\n");
    expect(rehecho).toBe(nuevo);
  });

  it("reconstruye también el texto original", () => {
    const viejo = texto("uno", "dos", "tres", "cuatro");
    const nuevo = texto("uno", "TRES", "cuatro", "cinco");
    const d = diffLines(viejo, nuevo);
    const rehecho = d.lines
      .filter((l) => l.op !== "añadida")
      .map((l) => l.text)
      .join("\n");
    expect(rehecho).toBe(viejo);
  });

  it("no se confunde con líneas en blanco repetidas", () => {
    const d = diffLines(texto("a", "", "", "b"), texto("a", "", "b"));
    expect(d.removed).toBe(1);
    expect(d.added).toBe(0);
  });
});

describe("degradación honesta en ficheros enormes", () => {
  it("no se degrada con un fichero grande y un cambio pequeño", () => {
    // El recorte de prefijo y sufijo deja una zona cambiada minúscula, así
    // que la tabla exacta sigue siendo viable aunque el fichero sea enorme.
    const base = Array.from({ length: MAX_LCS_LINES + 500 }, (_, i) => `l${i}`);
    const nuevo = [...base, "una línea más"];
    const d = diffLines(base.join("\n"), nuevo.join("\n"));
    expect(d.degraded).toBe("");
    expect(d.added).toBe(1);
  });

  it("se degrada y LO DICE cuando la zona cambiada es enorme", () => {
    const a = Array.from({ length: MAX_LCS_LINES + 10 }, (_, i) => `a${i}`);
    const b = Array.from({ length: MAX_LCS_LINES + 10 }, (_, i) => `b${i}`);
    const d = diffLines(a.join("\n"), b.join("\n"));
    expect(d.degraded).not.toBe("");
    expect(d.degraded).toContain("aproximada");
    // Degradado o no, sigue contando cambios: no puede quedarse en blanco.
    expect(d.added).toBeGreaterThan(0);
    expect(d.removed).toBeGreaterThan(0);
  });
});

describe("resumen", () => {
  it("dice sin cambios cuando no los hay", () => {
    expect(diffSummary(diffLines("a", "a"))).toBe("sin cambios");
  });

  it("cuenta añadidas y borradas", () => {
    expect(diffSummary(diffLines(texto("a", "b"), texto("a", "c", "d")))).toBe(
      "+2 −1",
    );
  });
});
