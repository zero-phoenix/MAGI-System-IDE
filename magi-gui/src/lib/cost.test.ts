/**
 * Agregación del gasto (§7.3).
 *
 * El panel de coste llevaba sin datos porque nadie llamaba a `record_usage`.
 * Estos tests cubren la aritmética y —sobre todo— las observaciones, que son
 * la parte que convierte una tabla de números en algo que sirve para decidir.
 */
import { describe, expect, it } from "vitest";
import { UsageEntry, formatSeconds, formatTokens, summarize } from "./cost";

let n = 0;
const uso = (p: Partial<UsageEntry>): UsageEntry => ({
  id: `u${n++}`, task_id: "t1", agent: "MELCHIOR", family: "deepseek",
  tokens_in: 100, tokens_out: 200, elapsed_s: 5, iterations: 1, tool_calls: 0,
  ...p,
});

describe("agregación", () => {
  it("sin datos no inventa nada", () => {
    const s = summarize([]);
    expect(s.calls).toBe(0);
    expect(s.tokens).toBe(0);
    expect(s.byAgent).toEqual([]);
  });

  it("suma tokens, tiempo y llamadas", () => {
    const s = summarize([uso({}), uso({ tokens_in: 50, tokens_out: 25, elapsed_s: 3 })]);
    expect(s.calls).toBe(2);
    expect(s.tokensIn).toBe(150);
    expect(s.tokensOut).toBe(225);
    expect(s.tokens).toBe(375);
    expect(s.seconds).toBe(8);
  });

  it("filtra por tarea", () => {
    const s = summarize([uso({ task_id: "t1" }), uso({ task_id: "t2" })], "t1");
    expect(s.calls).toBe(1);
  });

  it("agrupa por agente y ordena por tokens", () => {
    const s = summarize([
      uso({ agent: "MELCHIOR", tokens_out: 1000 }),
      uso({ agent: "CASPER", tokens_out: 10 }),
      uso({ agent: "BALTHASAR", tokens_out: 500 }),
    ]);
    expect(s.byAgent.map((a) => a.agent)).toEqual(["MELCHIOR", "BALTHASAR", "CASPER"]);
    expect(s.byAgent[0].share).toBeGreaterThan(s.byAgent[2].share);
  });

  it("separa a un agente que se degradó a otra familia", () => {
    // Si un nodo cambia de familia a mitad de tarea, mezclarlo bajo el mismo
    // agente esconde justo el dato que explica ese tramo.
    const s = summarize([
      uso({ agent: "BALTHASAR", family: "claude" }),
      uso({ agent: "BALTHASAR", family: "qwen" }),
    ]);
    expect(s.byAgent).toHaveLength(2);
    expect(s.byAgent.map((a) => a.family).sort()).toEqual(["claude", "qwen"]);
  });

  it("las cuotas suman uno", () => {
    const s = summarize([uso({ agent: "A" }), uso({ agent: "B" }), uso({ agent: "C" })]);
    expect(s.byAgent.reduce((t, a) => t + a.share, 0)).toBeCloseTo(1);
  });
});

describe("observaciones que cambian una decisión", () => {
  it("avisa de que los tres nodos comparten familia", () => {
    // El fallo original de v5.0.28: diversidad ficticia. Si se repite, el
    // panel de coste es el sitio donde se ve.
    const s = summarize([
      uso({ agent: "MELCHIOR", family: "gpt-4o-mini" }),
      uso({ agent: "BALTHASAR", family: "gpt-4o-mini" }),
      uso({ agent: "CASPER", family: "gpt-4o-mini" }),
    ]);
    expect(s.notes.join(" ")).toContain("MISMA familia");
  });

  it("no avisa cuando la diversidad es real", () => {
    const s = summarize([
      uso({ agent: "MELCHIOR", family: "deepseek" }),
      uso({ agent: "BALTHASAR", family: "claude" }),
      uso({ agent: "CASPER", family: "qwen" }),
    ]);
    expect(s.notes.join(" ")).not.toContain("MISMA familia");
  });

  it("avisa si un solo nodo concentra el gasto", () => {
    const s = summarize([
      uso({ agent: "MELCHIOR", family: "deepseek", tokens_out: 10000 }),
      uso({ agent: "CASPER", family: "qwen", tokens_out: 100 }),
    ]);
    expect(s.notes.join(" ")).toContain("concentra");
  });

  it("señala al proveedor degradado por latencia", () => {
    const s = summarize([
      uso({ agent: "BALTHASAR", family: "claude", elapsed_s: 40 }),
      uso({ agent: "CASPER", family: "qwen", elapsed_s: 4 }),
    ]);
    expect(s.notes.join(" ")).toContain("degradado");
  });

  it("distingue 'cero tokens' de 'sin llamadas'", () => {
    // Los proveedores gratuitos a menudo no devuelven conteo de uso. Enseñar
    // 0 sin decirlo haría creer que la tarea fue gratis.
    const s = summarize([uso({ tokens_in: 0, tokens_out: 0, elapsed_s: 12 })]);
    expect(s.notes.join(" ")).toContain("no devuelve conteo");
    expect(s.seconds).toBe(12);
  });
});

describe("formato", () => {
  it("abrevia los números largos", () => {
    expect(formatTokens(999)).toBe("999");
    expect(formatTokens(12480)).toBe("12.5k");
    expect(formatTokens(2_500_000)).toBe("2.50M");
  });

  it("pasa a minutos cuando toca", () => {
    expect(formatSeconds(45.2)).toBe("45.2s");
    expect(formatSeconds(125)).toBe("2m 5s");
  });
});
