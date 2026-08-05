import { describe, expect, it } from "vitest";
import { HealthSnapshot, diagnose, formatMs, slowest } from "./health";

const snap = (p: HealthSnapshot): HealthSnapshot => p;

describe("diagnóstico de salud", () => {
  it("sin medidas no finge que todo va bien", () => {
    const d = diagnose(snap({}));
    expect(d[0].severity).toBe("ok");
    expect(d[0].text).toContain("Todavía no hay medidas");
  });

  it("detecta el proveedor LENTO, que no da ningún error", () => {
    // §3.4: la degradación silenciosa no aparece en ningún log.
    const d = diagnose(snap({ providers: { lento: {
      n: 20, p50: 3000, p95: 31000, p99: 40000, mean: 6000,
      ok: 20, fail: 0, total: 20, failure_rate: 0 } } }));
    expect(d.some((x) => x.text.includes("31.0s"))).toBe(true);
    expect(d[0].severity).toBe("aviso");
  });

  it("un proveedor rápido y sano no genera ruido", () => {
    const d = diagnose(snap({ providers: { sano: {
      n: 20, p50: 900, p95: 2100, p99: 2500, mean: 1100,
      ok: 20, fail: 0, total: 20, failure_rate: 0 } } }));
    expect(d[0].severity).toBe("ok");
  });

  it("el proveedor que falla la mitad es grave, no aviso", () => {
    const d = diagnose(snap({ providers: { roto: {
      n: 10, p50: 800, p95: 900, p99: 900, mean: 800,
      ok: 4, fail: 6, total: 10, failure_rate: 0.6 } } }));
    expect(d[0].severity).toBe("grave");
    expect(d[0].text).toContain("60%");
  });

  it("no saca conclusiones de dos intentos", () => {
    // Una herramienta que falló 1 de 2 veces no tiene tendencia.
    const d = diagnose(snap({ tools: {
      nueva: { ok: 1, fail: 1, total: 2, failure_rate: 0.5 } } }));
    expect(d[0].severity).toBe("ok");
  });

  it("sí la saca con muestra suficiente", () => {
    const d = diagnose(snap({ tools: {
      floja: { ok: 6, fail: 4, total: 10, failure_rate: 0.4 } } }));
    expect(d.some((x) => x.text.includes("floja"))).toBe(true);
  });

  it("incorpora las alertas del bus", () => {
    const d = diagnose(snap({ alerts: [
      { kind: "drift", subject: "g4f-qwen", severity: "critical",
        detail: "cambió de comportamiento" }] }));
    expect(d[0].severity).toBe("grave");
    expect(d[0].text).toContain("g4f-qwen");
  });
});

describe("el más lento", () => {
  it("ordena por p95 y no por la media", () => {
    // Un proveedor que responde en 2s nueve veces y en 40s la décima tiene
    // buena media y una décima llamada insufrible.
    const s = snap({ providers: {
      irregular: { n: 10, p50: 2000, p95: 40000, p99: 41000, mean: 5800,
                   ok: 10, fail: 0, total: 10, failure_rate: 0 },
      constante: { n: 10, p50: 7000, p95: 7500, p99: 7600, mean: 7000,
                   ok: 10, fail: 0, total: 10, failure_rate: 0 } } });
    expect(slowest(s)![0]).toBe("irregular");
  });

  it("sin proveedores devuelve null en vez de reventar", () => {
    expect(slowest(snap({}))).toBeNull();
  });
});

describe("formato", () => {
  it("pasa a segundos cuando toca", () => {
    expect(formatMs(850)).toBe("850ms");
    expect(formatMs(31000)).toBe("31.0s");
  });
  it("no imprime NaN", () => {
    expect(formatMs(NaN)).toBe("—");
  });
});
