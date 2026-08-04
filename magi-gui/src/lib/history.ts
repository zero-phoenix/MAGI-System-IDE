/**
 * Acotado de historiales que crecen sin fin (Plan MAGI 9.0 §7.3).
 *
 * QUÉ DICE LA MEDICIÓN, QUE NO ES LO QUE DECÍA EL PLAN
 * ====================================================
 * §7.3 apuntaba a la "virtualización de lista" porque "los historiales largos
 * hunden el render". Al medirlo, el reparto real del coste es otro:
 *
 *     4000 anexiones al terminal      →  4,9 MB de cadena en memoria
 *     200 repintados × 2 `.includes()`→  532 ms  (2,7 ms POR REPINTADO)
 *     50 repintados × 800 mensajes    →    3 ms  (el `.map` es gratis)
 *
 * El `.map` de mensajes no era el problema. El problema es que
 * `terminalOutput` es UNA CADENA que se concatena sin límite, y que App.tsx
 * la recorre entera dos veces en cada repintado buscando la frase
 * "Esperando aprobación interactiva del usuario" — con un `useEffect` que
 * depende de `terminalOutput`, o sea que se dispara en cada línea nueva.
 *
 * Cada línea de salida de una herramienta costaba ~2,7 ms de puro escaneo de
 * cadena antes de tocar el DOM. Con la salida de un `grep` son cientos de
 * líneas seguidas.
 *
 * Así que se acota la cadena y se sustituyen los escaneos por una bandera que
 * se pone cuando llega el evento. Virtualizar la lista sin esto habría sido
 * optimizar lo que no dolía.
 */

/** Tope del terminal. ~200k caracteres son unas 2500 líneas: sobra para
 *  desplazarse hacia atrás y no llega a pesar. */
export const MAX_TERMINAL_CHARS = 200_000;

/** Cuántos mensajes se pintan. Cada uno arrastra un ReactMarkdown, que es lo
 *  caro de verdad en la lista — no el `.map`. */
export const MAX_RENDERED_MESSAGES = 120;

/**
 * Añade texto al terminal recortando por el principio.
 *
 * Recorta en un salto de línea y no a mitad de palabra, y deja constancia de
 * lo que se tiró: un historial que se acorta en silencio hace dudar de si
 * faltó salida o es que nunca se produjo.
 */
export function appendBounded(
  current: string,
  text: string,
  max: number = MAX_TERMINAL_CHARS,
): string {
  const nuevo = text + "\n";
  const combinado = current + nuevo;
  if (combinado.length <= max) return combinado;

  // El corte NUNCA puede comerse lo recién añadido. La primera versión hacía
  // `indexOf("\n", exceso)` sobre la cadena entera, y si lo anterior no tenía
  // saltos de línea el único que encontraba era el que acababa de añadir: se
  // tiraba el texto nuevo y quedaba solo el aviso. En un terminal, la última
  // línea es justo la que hace falta ver.
  const corteMax = Math.max(0, combinado.length - max);
  const limite = combinado.length - nuevo.length;   // no pasar de aquí
  const busqueda = Math.min(corteMax, limite);

  let inicio = combinado.indexOf("\n", busqueda);
  inicio = inicio === -1 || inicio >= limite ? busqueda : inicio + 1;

  const descartados = inicio;
  const resto = combinado.slice(inicio);
  if (!descartados) return resto;
  return `[… ${descartados.toLocaleString()} caracteres anteriores descartados …]\n${resto}`;
}

/**
 * Últimos N elementos, con la cuenta de los ocultos.
 *
 * No es virtualización con ventana de scroll: es el 90 % del beneficio con el
 * 5 % de la complejidad y sin añadir una dependencia. Lo que hundía el render
 * era montar cientos de ReactMarkdown, y eso se arregla no montándolos.
 */
export function tail<T>(items: T[], max: number = MAX_RENDERED_MESSAGES): {
  visible: T[];
  hidden: number;
} {
  if (items.length <= max) return { visible: items, hidden: 0 };
  return { visible: items.slice(-max), hidden: items.length - max };
}
