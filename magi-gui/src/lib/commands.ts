/**
 * Paleta de comandos: filtrado difuso y catálogo (Plan MAGI 9.0 §7.3).
 *
 * POR QUÉ IMPORTA MÁS DE LO QUE PARECE
 * ====================================
 * A estas alturas el sistema tiene diez pestañas y una docena de acciones
 * repartidas entre ellas: parar una tarea, parar todo, medir salud, correr el
 * banco, pedir una auto-mejora, clonar, cambiar de motor, abrir el diff…
 *
 * Una capacidad que existe pero que hay que ir a buscar a la cuarta pestaña
 * es, en la práctica, una capacidad que no se usa. Es una versión más suave
 * del mismo problema que ya apareció tres veces en este proyecto: la pieza
 * construida y el camino que no lleva a ella.
 *
 * EL FILTRADO
 * ===========
 * Subsecuencia, no subcadena: escribir "psl" debe encontrar "Parar SoLo esta
 * tarea". Es lo que hace que la paleta se pueda usar sin mirar — que es el
 * único motivo por el que una paleta gana a un menú.
 *
 * Y puntúa: coincidir al principio de una palabra vale más que en medio,
 * porque "ba" debe traer "BAnco" antes que "auto-mejora medible" (que también
 * contiene b...a). Sin puntuación, el orden lo decide el azar del catálogo.
 */

export interface Command {
  id: string;
  /** Lo que se ve. */
  title: string;
  /** Dónde vive, para que el usuario aprenda la interfaz en vez de depender
   *  de la paleta. */
  group: string;
  /** Sinónimos: cómo lo llamaría alguien que no sabe cómo lo llamamos aquí. */
  keywords?: string;
  /** Marca las acciones que tocan la máquina o gastan cuota. */
  dangerous?: boolean;
}

export interface Scored {
  command: Command;
  score: number;
  /** Índices de `title` que casaron, para poder resaltarlos. */
  hits: number[];
}

/**
 * Puntúa una consulta contra un texto por subsecuencia.
 *
 * Devuelve null si no casa. Puntúa más alto cuando los caracteres van
 * seguidos y cuando caen al principio de una palabra.
 */
export function fuzzyScore(query: string, text: string): { score: number; hits: number[] } | null {
  const q = query.trim().toLowerCase();
  if (!q) return { score: 0, hits: [] };
  const t = text.toLowerCase();

  const hits: number[] = [];
  let score = 0;
  let desde = 0;
  let anterior = -2;

  for (const ch of q) {
    const i = t.indexOf(ch, desde);
    if (i === -1) return null;
    hits.push(i);

    // Contiguo con el anterior: el usuario está escribiendo la palabra.
    if (i === anterior + 1) score += 6;
    // Principio de palabra: "ba" para "banco" vale más que la b de "sobra".
    if (i === 0 || /[\s\-_/·]/.test(t[i - 1])) score += 10;
    // Cuanto más lejos haya que saltar, peor.
    score -= Math.min(i - desde, 6);

    anterior = i;
    desde = i + 1;
  }
  // Empatar a favor de lo corto: "Coste" antes que "Estado de Motores IA".
  score -= text.length * 0.05;
  return { score, hits };
}

/**
 * Filtra y ordena el catálogo.
 *
 * Con la consulta vacía devuelve TODO en el orden del catálogo, que es el
 * orden en que se pensó: la paleta recién abierta debe ser un índice, no una
 * lista arbitraria.
 */
export function filterCommands(commands: Command[], query: string): Scored[] {
  if (!query.trim()) {
    return commands.map((command) => ({ command, score: 0, hits: [] }));
  }
  const out: Scored[] = [];
  for (const command of commands) {
    // Se busca sobre título + grupo + sinónimos, pero los índices resaltados
    // son solo los del título: resaltar en un texto que no se ve confunde.
    const enTitulo = fuzzyScore(query, command.title);
    const ampliado = fuzzyScore(
      query, `${command.title} ${command.group} ${command.keywords ?? ""}`);
    if (!enTitulo && !ampliado) continue;
    out.push({
      command,
      // Casar en el título vale bastante más que casar en los sinónimos.
      score: (enTitulo?.score ?? -Infinity) > -Infinity
        ? enTitulo!.score + 25
        : ampliado!.score,
      hits: enTitulo?.hits ?? [],
    });
  }
  return out.sort((a, b) => b.score - a.score);
}

/** Mueve la selección sin salirse, envolviendo por los extremos. */
export function moveSelection(actual: number, delta: number, total: number): number {
  if (total <= 0) return 0;
  return (((actual + delta) % total) + total) % total;
}
