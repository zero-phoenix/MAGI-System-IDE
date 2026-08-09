/**
 * Lectura de los cuellos de botella (§3.2 del plan de mejora).
 *
 * POR QUÉ ESTO NO ES UNA TABLA MÁS
 * ================================
 * La telemetría llevaba tiempo guardando la duración de cada turno y de cada
 * uso de herramienta. Nadie las leía. El panel enseñaba una latencia media por
 * proveedor, y una media no distingue dos situaciones que no se parecen en
 * nada:
 *
 *     A: siempre tarda 4 s                 media = 4 s
 *     B: suele tardar 1 s, y una de cada   media = 4 s
 *        diez veces tarda 30 s
 *
 * A es un límite del proveedor: se acepta o se cambia. B es la cola de la
 * distribución, y es la que el usuario recuerda, porque es la vez que se quedó
 * mirando la pantalla sin saber si el sistema seguía vivo. La media las declara
 * iguales; el p95 las separa.
 *
 * Este fichero es solo la aritmética de presentar eso, como funciones puras y
 * testeables. El componente pinta; aquí se decide qué merece pintarse.
 */

export interface Estadistica {
  clave: string;
  n: number;
  mediana_ms: number | null;
  p95_ms: number | null;
  peor_ms: number;
  /** false cuando hay tan pocas muestras que el «p95» es el peor valor visto. */
  fiable: boolean;
}

export interface AvisoLentitud {
  herramienta: string;
  ultima_ms: number;
  p95_historico_ms: number;
  mediana_ms: number | null;
  veces_el_p95: number | null;
  muestras: number;
}

export interface Cuellos {
  agentes?: Estadistica[];
  familias?: Estadistica[];
  herramientas?: Estadistica[];
  muestra_fiable_desde?: number;
  error?: string;
}

export interface Telemetria {
  cuellos?: Cuellos;
  avisos_lentitud?: AvisoLentitud[];
  [k: string]: unknown;
}

/** ms legibles. Por debajo del segundo, los decimales sobran. */
export function ms(v: number | null | undefined): string {
  if (v === null || v === undefined || !Number.isFinite(v)) return "—";
  if (v < 1000) return `${Math.round(v)} ms`;
  if (v < 60_000) return `${(v / 1000).toFixed(1)} s`;
  return `${Math.floor(v / 60_000)} min ${Math.round((v % 60_000) / 1000)} s`;
}

/**
 * Cuánto se aparta el p95 de la mediana, en veces.
 *
 * Es el número que dice si el problema es «lento» o «irregular», y son cosas
 * distintas con soluciones distintas. Un p95 igual a la mediana significa que
 * el componente tarda siempre lo mismo: molesto, pero predecible, y se arregla
 * cambiando de proveedor o de enfoque. Un p95 diez veces la mediana significa
 * que casi siempre va bien y de vez en cuando se atasca — eso no se arregla
 * cambiando de proveedor, se arregla encontrando qué pasa en esa décima vez.
 */
export function irregularidad(e: Estadistica): number | null {
  if (!e.mediana_ms || !e.p95_ms) return null;
  return Math.round((e.p95_ms / e.mediana_ms) * 10) / 10;
}

/** Umbral a partir del cual la irregularidad deja de ser ruido de medición. */
export const IRREGULAR_DESDE = 3;

/**
 * Una línea que explique la fila sin obligar a interpretar cuatro números.
 *
 * Un panel que enseña p50, p95 y peor sin decir qué significan deja el trabajo
 * a medias: lo útil no es el número, es la frase que permite decidir qué mirar
 * después.
 */
export function lectura(e: Estadistica): string {
  if (!e.fiable) {
    return `Solo ${e.n} medidas: esto es lo peor visto, no un percentil. ` +
           `Trátalo como una anécdota hasta que haya más.`;
  }
  const irr = irregularidad(e);
  if (irr !== null && irr >= IRREGULAR_DESDE) {
    return `Irregular: casi siempre ${ms(e.mediana_ms)}, pero una de cada ` +
           `veinte veces ${ms(e.p95_ms)} — ${irr}× su mediana. El problema no ` +
           `es que sea lento, es que a veces se atasca.`;
  }
  return `Estable en torno a ${ms(e.mediana_ms)}; cuando va mal, ${ms(e.p95_ms)}. ` +
         `Tarda siempre parecido, así que el margen está en cambiar de enfoque, ` +
         `no en buscar un atasco.`;
}

/**
 * Filas que merecen enseñarse, de peor a mejor.
 *
 * Se descartan las que no tienen p95: sin medida no hay nada que decir, y una
 * fila con guiones ocupa el mismo sitio que una con información.
 */
export function ordenadas(filas: Estadistica[] | undefined, top = 5): Estadistica[] {
  return (filas ?? [])
    .filter((f) => f && typeof f.p95_ms === "number")
    .sort((a, b) => (b.p95_ms ?? 0) - (a.p95_ms ?? 0))
    .slice(0, top);
}

/** ¿Hay algo que enseñar, o el sistema todavía no ha medido nada? */
export function hayDatos(c: Cuellos | undefined): boolean {
  if (!c || c.error) return false;
  return ordenadas(c.agentes).length > 0 ||
         ordenadas(c.familias).length > 0 ||
         ordenadas(c.herramientas).length > 0;
}
