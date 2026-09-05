/**
 * Rutas de archivo clicables en el flujo (deconstrucción, principio #7).
 *
 * «Cada artefacto es una referencia clicable»: un mensaje que nombra un
 * fichero debe poder abrirlo. Estas dos funciones deciden QUÉ se enlaza —
 * el cómo renderizarlo vive en el componente.
 *
 * Conservador a propósito: solo rutas absolutas de Windows o relativas con
 * extensión de archivo. «24/7», «TCP/IP» o una fecha no son ficheros, y un
 * enlace falso enseña a no hacer clic en los verdaderos.
 */

/** Ruta absoluta de Windows: C:\algo\algo.ext */
const RE_ABSOLUTA = /[A-Za-z]:\\[\w\\.-]+/g;

/** Relativa con extensión: docs/BITACORA.md, src/vita/main.c (>= 2 segmentos) */
const RE_RELATIVA = /(?:[\w.-]+\/)+[\w.-]+\.\w{2,4}/g;

/** ¿Este texto es una valla de código? Dentro no se toca nada. */
const RE_VALLA = /(```[\s\S]*?```)/;

/** Convierte las rutas del texto en enlaces markdown [ruta](open:ruta). */
export function enlazarRutas(texto: string): string {
  if (!texto) return texto;
  return texto
    .split(RE_VALLA)
    .map((parte) => parte.startsWith("```")
      ? parte
      : parte
          .replace(RE_ABSOLUTA, (r) => `[${r}](open:${r})`)
          .replace(RE_RELATIVA, (r) => `[${r}](open:${r})`))
    .join("");
}

/** Extrae la ruta de un href open:... (null si no lo es). */
export function rutaDeEnlace(href: string): string | null {
  return href?.startsWith("open:") ? href.slice(5) : null;
}
