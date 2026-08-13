/**
 * ¿Es un debate o es teatro? Dos números que lo dicen.
 *
 * LO QUE NO SE MEDÍA
 * ==================
 * MAGI monta un debate dialéctico entre tres inteligencias y hasta hoy no
 * había forma de saber si servía de algo. Faltaban dos respuestas concretas:
 *
 *   · ¿BALTHASAR aporta algo distinto de MELCHIOR, o le da la razón con otras
 *     palabras? Si la antítesis converge con la tesis, el enjambre está
 *     pagando tres llamadas por el trabajo de una.
 *
 *   · ¿la ronda 2 cambió algo respecto de la 1? Porque si no, las rondas de
 *     más son latencia y cuota a cambio de nada, y conviene saberlo antes de
 *     recomendarlas.
 *
 * Sin estos números, «tres cabezas piensan mejor que una» es una creencia. Con
 * ellos es una afirmación comprobable, que puede salir que no — y saber que no
 * también vale.
 *
 * POR QUÉ JACCARD Y NO ALGO MÁS FINO
 * ==================================
 * Se compara el vocabulario significativo de dos textos: palabras compartidas
 * entre palabras totales. Es tosco a propósito.
 *
 * Un método bueno de verdad —embeddings— exigiría un modelo, y §I.3 prohíbe
 * los modelos locales; pedírselo a un proveedor gratuito significaría gastar
 * cuota del usuario para adornar un gráfico. Jaccard corre en el navegador, en
 * microsegundos, sin red y sin dependencias.
 *
 * No distingue «el mutex es mejor» de «el mutex es peor» —comparten
 * vocabulario— y por eso el número se presenta como SEÑAL, no como veredicto:
 * sirve para detectar el caso extremo (dos textos casi idénticos), que es
 * justo el que importa y el único que se puede afirmar con honestidad.
 *
 * Todo son funciones puras y sin estado: se prueban sin montar nada.
 */

import type { Ronda } from "./rondas";

/**
 * Palabras vacías de los cuatro idiomas admitidos por el sistema.
 *
 * Sin quitarlas, dos textos cualesquiera en español comparten «de», «la»,
 * «que» y «para», y la divergencia sale artificialmente baja: parecería que
 * los agentes están de acuerdo cuando solo comparten gramática.
 */
const VACIAS = new Set([
  // es
  "el", "la", "los", "las", "un", "una", "de", "del", "que", "y", "o", "a",
  "en", "por", "para", "con", "sin", "es", "son", "se", "su", "sus", "al",
  "lo", "como", "mas", "más", "pero", "no", "si", "este", "esta", "esto",
  "ese", "esa", "hay", "ha", "han", "ser", "esta", "esta", "muy", "ya",
  // en
  "the", "of", "and", "to", "in", "is", "are", "for", "with", "that", "this",
  "it", "as", "be", "on", "or", "an", "at", "by", "from", "not", "but",
  // pt / it
  "os", "as", "um", "uma", "do", "da", "dos", "das", "nao", "não", "com",
  "il", "lo", "gli", "di", "che", "per", "con", "una", "e", "non", "sono",
]);

/** Palabras significativas, normalizadas y sin duplicados. */
export function vocabulario(texto: string | undefined): Set<string> {
  if (!texto) return new Set();
  const limpio = texto
    // Los bloques de código se quitan: dos agentes que citan el mismo
    // fragmento compartirían decenas de palabras idénticas y la divergencia
    // se desplomaría sin que hubieran estado de acuerdo en nada.
    .replace(/```[\s\S]*?```/g, " ")
    .toLowerCase()
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "");
  const palabras = limpio.match(/[a-z0-9]{3,}/g) || [];
  return new Set(palabras.filter((p) => !VACIAS.has(p)));
}

/**
 * Divergencia entre dos textos: 0 = idénticos, 1 = sin nada en común.
 *
 * `null` cuando alguno no tiene vocabulario suficiente. Devolver 0 ahí diría
 * «coinciden del todo», que es una afirmación fuerte sobre un texto vacío.
 */
export function divergencia(a: string | undefined, b: string | undefined): number | null {
  const va = vocabulario(a);
  const vb = vocabulario(b);
  if (va.size < 3 || vb.size < 3) return null;

  let comunes = 0;
  va.forEach((p) => {
    if (vb.has(p)) comunes += 1;
  });
  const union = va.size + vb.size - comunes;
  if (union === 0) return null;
  return 1 - comunes / union;
}

export interface CalidadRonda {
  ronda: number;
  /** Entre la tesis de MELCHIOR y la antítesis de BALTHASAR. */
  divergenciaTesisAntitesis: number | null;
  /** Entre la conclusión de esta ronda y la de la anterior. */
  cambioRespectoAnterior: number | null;
  /** Lectura en castellano, para quien no quiera interpretar un número. */
  lectura: string;
}

/**
 * Umbral por debajo del cual dos textos son «lo mismo con otras palabras».
 *
 * ESTE NÚMERO LO PUSE A OJO Y ESTABA MAL.
 * =======================================
 * Empezó en 0,25 porque «una cuarta parte distinto suena a poco». Al escribir
 * los tests con ejemplos concretos salió esto:
 *
 *   paráfrasis casi literal («propongo usar un mutex…» / «coincido: usar un
 *   mutex…»)                                             -> 0,44
 *   desacuerdo real («mutex, exclusión mutua barata» /
 *   «semáforo con contador bajo contención alta»)        -> 1,00
 *
 * Con 0,25 no se detectaba NI el eco más descarado. La causa es que Jaccard no
 * lematiza: «proteger» y «protege» cuentan como palabras distintas, así que
 * dos frases que dicen lo mismo nunca bajan mucho de 0,4.
 *
 * 0,55 separa los dos casos medidos con holgura por ambos lados.
 *
 * HONESTAMENTE: está calibrado sobre dos ejemplos escritos a mano, que es poca
 * evidencia. Cuando haya debates reales guardados conviene recalibrarlo con
 * ellos — y hasta entonces esto detecta el caso descarado y poco más, que es
 * justo lo que promete y nada más.
 */
export const UMBRAL_ECO = 0.55;

/**
 * Umbral por debajo del cual una ronda no ha cambiado nada.
 *
 * Más bajo que el anterior a propósito: comparar dos CONCLUSIONES sobre el
 * mismo asunto es más exigente que comparar dos posturas. Si la conclusión de
 * la ronda 2 comparte más de dos tercios del vocabulario con la de la ronda 1,
 * la ronda no ha aportado.
 */
export const UMBRAL_SIN_CAMBIO = 0.35;

function textoDe(r: Ronda, agente: string): string | undefined {
  return r.nodos.find((n) => n.agente === agente)?.texto;
}

/**
 * Calidad de cada ronda del debate.
 *
 * La lectura en texto no es adorno: un `0.18` no le dice nada a nadie a las
 * dos de la mañana, y «BALTHASAR repite a MELCHIOR» sí.
 */
export function calidadDelDebate(rondas: Ronda[]): CalidadRonda[] {
  return rondas.map((r, i) => {
    const div = divergencia(textoDe(r, "MELCHIOR"), textoDe(r, "BALTHASAR"));
    const previa = i > 0 ? rondas[i - 1].conclusion ?? undefined : undefined;
    const cambio = i > 0 ? divergencia(r.conclusion ?? undefined, previa) : null;

    let lectura: string;
    if (div === null) {
      lectura = "aún sin material suficiente para juzgar";
    } else if (div < UMBRAL_ECO) {
      lectura = "BALTHASAR apenas se separa de MELCHIOR: la antítesis no está refutando";
    } else if (cambio !== null && cambio < UMBRAL_SIN_CAMBIO) {
      lectura = "esta ronda concluye casi lo mismo que la anterior: no está aportando";
    } else {
      lectura = "el debate diverge de verdad";
    }

    return {
      ronda: r.numero,
      divergenciaTesisAntitesis: div,
      cambioRespectoAnterior: cambio,
      lectura,
    };
  });
}

/**
 * Una frase para el gráfico. `null` si no hay nada que valga la pena decir.
 *
 * Solo habla cuando hay un problema. Un aviso que aparece siempre —«el debate
 * va bien»— es ruido y se deja de leer a la tercera vez, y entonces tampoco se
 * lee el que sí importa.
 */
export function avisoDelDebate(rondas: Ronda[]): string | null {
  const calidad = calidadDelDebate(rondas).filter(
    (c) => c.divergenciaTesisAntitesis !== null,
  );
  if (!calidad.length) return null;

  const ecos = calidad.filter(
    (c) => (c.divergenciaTesisAntitesis ?? 1) < UMBRAL_ECO,
  );
  if (ecos.length) {
    const cuales = ecos.map((c) => c.ronda).join(", ");
    return `Ronda ${cuales}: BALTHASAR apenas se separa de MELCHIOR. La antítesis no está refutando.`;
  }

  const estancadas = calidad.filter(
    (c) => c.cambioRespectoAnterior !== null &&
      c.cambioRespectoAnterior < UMBRAL_SIN_CAMBIO,
  );
  if (estancadas.length) {
    const cuales = estancadas.map((c) => c.ronda).join(", ");
    return `Ronda ${cuales}: concluye casi lo mismo que la anterior. Otra ronda cuesta latencia y no aporta.`;
  }
  return null;
}
