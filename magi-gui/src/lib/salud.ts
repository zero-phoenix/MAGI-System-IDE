/**
 * Lectura del historial de salud de proveedores (mejora 5.16 del plan).
 *
 * POR QUÉ UNA CHISPA Y NO UNA TABLA
 * ================================
 * `media_historica_ms` promedia 30 días de medias diarias, y cada día pesa lo
 * mismo: un candidato que pasó de 3 s a 9 s esta semana sigue mostrando «5 s»
 * durante semanas. La serie diaria (`historico`) enseña la pendiente; la
 * chispa la hace visible de un vistazo, que es lo que un panel debe a quien
 * solo quiere saber si hoy va peor que ayer.
 *
 * Este fichero es solo la aritmética, como funciones puras y testeables.
 * El componente pinta; aquí se decide qué merece pintarse.
 */

export interface DiaMedido {
  dia: string;      // "2026-08-16"
  media_ms: number;
  n: number;        // mediciones correctas de ese día
}

/** Puntos normalizados a [0,1] para una chispa SVG de ancho/alto dados. */
export function puntosChispa(
  serie: DiaMedido[], ancho: number, alto: number,
): string {
  if (serie.length === 0) return "";
  const ms = serie.map((d) => d.media_ms);
  const min = Math.min(...ms);
  const max = Math.max(...ms);
  const margen = max - min || 1;                    // serie plana: línea recta
  const paso = serie.length > 1 ? ancho / (serie.length - 1) : 0;
  return serie
    .map((d, i) => {
      const x = i * paso;
      // Y crece hacia abajo en SVG: normalizado 0 (más rápido) arriba,
      // 1 (más lento) abajo.
      const y = ((d.media_ms - min) / margen) * alto;
      return `${redondea(x)},${redondea(Math.max(0, Math.min(alto, y)))}`;
    })
    .join(" ");
}

function redondea(n: number): number {
  return Math.round(n * 10) / 10;
}

/** ¿La tendencia de los últimos días es peor que la de todos los anteriores? */
export function tendencia(serie: DiaMedido[]): "mejora" | "igual" | "empeora" | null {
  if (serie.length < 4) return null;              // con menos no hay pendiente que fiar
  const mitad = Math.floor(serie.length / 2);
  const primera = media(serie.slice(0, mitad));
  const ultima = media(serie.slice(mitad));
  if (primera === null || ultima === null) return null;
  const cambio = (ultima - primera) / primera;
  if (cambio <= -0.25) return "mejora";
  if (cambio >= 0.5) return "empeora";             // +50 % sostenido: se nota
  return "igual";
}

function media(serie: DiaMedido[]): number | null {
  if (serie.length === 0) return null;
  return serie.reduce((s, d) => s + d.media_ms, 0) / serie.length;
}

/**
 * Qué rotos enseñar primero. Los IMPOSIBLES (exigen cuenta o abren navegador)
 * no van a volver: enseñarlos mezclados con los caídos invita a esperarlos.
 */
export function clasificaRotos(
  motivos: Record<string, string>,
): { imposibles: [string, string][]; caidos: [string, string][] } {
  const imposibles: [string, string][] = [];
  const caidos: [string, string][] = [];
  for (const [proveedor, motivo] of Object.entries(motivos)) {
    if (/tu cuenta|navegador/i.test(motivo)) imposibles.push([proveedor, motivo]);
    else caidos.push([proveedor, motivo]);
  }
  return { imposibles, caidos };
}
