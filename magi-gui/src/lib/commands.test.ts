import { describe, expect, it } from "vitest";
import { Command, filterCommands, fuzzyScore, moveSelection } from "./commands";

const cmd = (id: string, title: string, group = "General", keywords = ""): Command =>
  ({ id, title, group, keywords });

const CATALOGO = [
  cmd("cancel", "Parar solo esta tarea", "Ejecución", "cancelar detener"),
  cmd("stop", "Parar todo", "Ejecución", "emergencia kill"),
  cmd("health", "Medir salud del sistema", "Sistema", "metricas latencia"),
  cmd("bench", "Ejecutar banco de evaluación", "Sistema", "benchmark evaluar"),
  cmd("cost", "Ver coste en tokens", "Paneles", "gasto"),
];

describe("filtrado difuso", () => {
  it("encuentra por subsecuencia, no por subcadena", () => {
    // El motivo de existir de una paleta: escribir sin mirar.
    const r = filterCommands(CATALOGO, "pse");
    expect(r[0].command.id).toBe("cancel");   // Parar Solo Esta tarea
  });

  it("prefiere el principio de palabra", () => {
    // "ba" debe traer BAnco, no algo que contenga b...a por casualidad.
    const r = filterCommands(CATALOGO, "ba");
    expect(r[0].command.id).toBe("bench");
  });

  it("encuentra por sinónimo aunque no esté en el título", () => {
    const r = filterCommands(CATALOGO, "benchmark");
    expect(r[0].command.id).toBe("bench");
  });

  it("el título gana a los sinónimos", () => {
    // "Parar todo" contiene el término en el título; "cancelar" solo en los
    // sinónimos de otro. El primero debe ir antes.
    const r = filterCommands(CATALOGO, "parar");
    expect(r[0].command.title).toContain("Parar");
  });

  it("con consulta vacía devuelve el catálogo en su orden", () => {
    const r = filterCommands(CATALOGO, "");
    expect(r).toHaveLength(CATALOGO.length);
    expect(r.map((x) => x.command.id)).toEqual(CATALOGO.map((c) => c.id));
  });

  it("una consulta que no casa devuelve nada, no todo", () => {
    expect(filterCommands(CATALOGO, "zzzqx")).toHaveLength(0);
  });

  it("empata a favor de lo corto", () => {
    const dos = [cmd("a", "Coste"), cmd("b", "Coste de la sesión completa")];
    expect(filterCommands(dos, "coste")[0].command.id).toBe("a");
  });

  it("no distingue mayúsculas", () => {
    expect(filterCommands(CATALOGO, "SALUD")[0].command.id).toBe("health");
  });

  it("devuelve los índices para resaltar", () => {
    const r = fuzzyScore("sal", "Medir salud del sistema")!;
    expect(r.hits).toHaveLength(3);
    expect("Medir salud del sistema"[r.hits[0]].toLowerCase()).toBe("s");
  });

  it("no resalta sobre texto que el usuario no ve", () => {
    // Si casó solo por sinónimos, no hay nada que resaltar en el título.
    const r = filterCommands(CATALOGO, "benchmark");
    expect(r[0].hits).toEqual([]);
  });
});

describe("navegación", () => {
  it("envuelve por los dos extremos", () => {
    expect(moveSelection(0, -1, 5)).toBe(4);
    expect(moveSelection(4, 1, 5)).toBe(0);
  });

  it("con la lista vacía no devuelve un índice inválido", () => {
    // Sin esto, teclear algo que no casa y pulsar Enter revienta.
    expect(moveSelection(3, 1, 0)).toBe(0);
  });
});
