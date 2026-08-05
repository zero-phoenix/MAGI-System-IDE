/**
 * Lectura del panel de salud (Plan MAGI 9.0 §3.4, §7.3).
 *
 * POR QUÉ NO EXISTÍA
 * ==================
 * No faltaba el backend. `MetricsCollector` estaba construido, enganchado al
 * bus en el arranque del kernel y con su handler `obs.metrics` registrado. Lo
 * que faltaba era que alguien lo llamara: una auditoría de qué handlers RPC
 * tienen forma de invocarse desde la interfaz encontró TRES capacidades
 * completas e inalcanzables — `obs.metrics`, `naoko.self_improve` y
 * `eval.run`.
 *
 * Es el mismo patrón que ya apareció con la contabilidad de tokens, con la
 * cancelación y con el diff: la pieza construida y el cable que falta. Aquí
 * el cable era un botón.
 *
 * QUÉ APORTA ESTE FICHERO
 * =======================
 * La aritmética de convertir el snapshot en un diagnóstico, como función
 * pura. Un panel que enseña p50 y p95 sin decir qué significan deja el
 * trabajo a medias: lo útil es "este proveedor está degradado" y "esta
 * herramienta falla una de cada tres veces".
 */

export interface ProviderStat {
  n: number; p50: number; p95: number; p99: number; mean: number;
  ok: number; fail: number; total: number; failure_rate: number;
}

export interface ToolStat {
  ok: number; fail: number; total: number; failure_rate: number;
}

export interface HealthSnapshot {
  providers?: Record<string, ProviderStat>;
  tools?: Record<string, ToolStat>;
  agents?: Record<string, unknown>;
  tasks_tracked?: number;
  total_tokens?: number;
  alerts?: Array<{ kind: string; subject: string; detail: string; severity: string }>;
}

/** Por encima de esto, la espera se nota y arruina la sesión aunque no falle. */
export const SLOW_P95_MS = 25_000;

/** Una herramienta que falla más de esto no es mala suerte. */
export const HIGH_FAILURE_RATE = 0.25;

export interface Diagnosis {
  severity: "ok" | "aviso" | "grave";
  text: string;
}

/**
 * Qué está mal, dicho en lenguaje que sirva para decidir.
 *
 * §3.4 lo llama "degradación visible": un proveedor a 25 s o una herramienta
 * fallando el 40 % no lanzan ninguna excepción, así que no aparecen en ningún
 * log de errores, y aun así arruinan la experiencia. Solo se ven si alguien
 * los mira.
 */
export function diagnose(s: HealthSnapshot): Diagnosis[] {
  const out: Diagnosis[] = [];

  for (const [nombre, p] of Object.entries(s.providers ?? {})) {
    if (!p || !p.total) continue;
    if (p.failure_rate >= 0.5) {
      out.push({
        severity: "grave",
        text: `${nombre} falla el ${Math.round(p.failure_rate * 100)}% de las ` +
              `veces (${p.fail}/${p.total}). El cortacircuitos debería estar ` +
              `apartándolo.`,
      });
    } else if (p.p95 >= SLOW_P95_MS) {
      out.push({
        severity: "aviso",
        text: `${nombre}: p95 de ${(p.p95 / 1000).toFixed(1)}s. No da error, ` +
              `pero una de cada veinte peticiones te hace esperar eso.`,
      });
    }
  }

  for (const [nombre, t] of Object.entries(s.tools ?? {})) {
    if (!t || t.total < 3) continue;    // con dos intentos no hay tendencia
    if (t.failure_rate >= HIGH_FAILURE_RATE) {
      out.push({
        severity: t.failure_rate >= 0.5 ? "grave" : "aviso",
        text: `La herramienta ${nombre} falla ${t.fail} de ${t.total} veces. ` +
              `Los agentes la seguirán intentando y gastando turnos.`,
      });
    }
  }

  for (const a of s.alerts ?? []) {
    out.push({
      severity: a.severity === "critical" ? "grave" : "aviso",
      text: `${a.subject}: ${a.detail}`,
    });
  }

  if (!out.length) {
    const n = Object.keys(s.providers ?? {}).length;
    out.push({
      severity: "ok",
      text: n
        ? `Sin degradación detectada en ${n} proveedor(es).`
        : "Todavía no hay medidas: haz una petición y vuelve.",
    });
  }
  return out;
}

/**
 * El proveedor más lento, que es el que marca la experiencia.
 *
 * La media engaña con los proveedores gratuitos: uno que responde en 2 s
 * nueve veces y en 40 s la décima tiene una media aceptable y una décima
 * llamada insufrible. Por eso se ordena por p95 y no por `mean`.
 */
export function slowest(s: HealthSnapshot): [string, ProviderStat] | null {
  const filas = Object.entries(s.providers ?? {}).filter(([, p]) => p?.n);
  if (!filas.length) return null;
  return filas.sort((a, b) => b[1].p95 - a[1].p95)[0];
}

export function formatMs(ms: number): string {
  if (!Number.isFinite(ms)) return "—";
  return ms < 1000 ? `${Math.round(ms)}ms` : `${(ms / 1000).toFixed(1)}s`;
}
