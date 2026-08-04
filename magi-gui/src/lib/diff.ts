/**
 * Diff de líneas por subsecuencia común más larga (Plan MAGI 9.0 §7.3).
 *
 * QUÉ SUSTITUYE
 * =============
 * `DiffViewer.tsx` decidía si una línea era nueva así:
 *
 *     const isNew = !oldLines.includes(line) && line.trim() !== "";
 *
 * Eso no es un diff, y falla de cuatro formas que importan:
 *
 *   1. No muestra BORRADOS. Si el cambio quita treinta líneas, el panel de
 *      aprobación no enseña ninguna. Es justo lo que más urge revisar.
 *   2. Una línea MOVIDA no se marca, porque su texto sigue existiendo en
 *      alguna parte del original. Reordenar un fichero entero sale como "sin
 *      cambios".
 *   3. Una línea REPETIDA (`}`, `return`, una línea en blanco) nunca se marca
 *      aunque se hayan añadido veinte.
 *   4. Es O(n·m): `includes` recorre el original entero por cada línea nueva.
 *
 * Y encima recibía `originalCode=""`, así que en la práctica pintaba TODO de
 * verde. El usuario veía un panel que parecía una revisión y no lo era —
 * peor que no tener panel, porque invita a aprobar creyendo que has mirado.
 *
 * POR QUÉ LCS
 * ===========
 * La subsecuencia común más larga es lo que usan `diff`, `git` y todo lo
 * demás, y produce el alineamiento mínimo: lo que no está en la subsecuencia
 * común es exactamente lo que se añadió o se quitó. No hay heurística que
 * ajustar ni casos raros que parchear después.
 *
 * El coste es O(n·m) en memoria si se construye la tabla entera. Para el
 * tamaño de un fichero de código es irrelevante, pero un fichero grande
 * pegado en el panel podría hacerlo notar, así que hay un tope explícito que
 * DEGRADA A UNA COMPARACIÓN SIMPLE Y LO DICE, en vez de colgar la interfaz en
 * silencio.
 */

export type DiffOp = "igual" | "añadida" | "borrada";

export interface DiffLine {
  op: DiffOp;
  text: string;
  /** Número de línea en el original (1-indexado), null si es añadida. */
  oldNumber: number | null;
  /** Número de línea en el nuevo (1-indexado), null si es borrada. */
  newNumber: number | null;
}

export interface DiffResult {
  lines: DiffLine[];
  added: number;
  removed: number;
  /** Motivo si se degradó a una comparación menos precisa. Vacío si no. */
  degraded: string;
}

/**
 * Por encima de esto no se construye la tabla LCS.
 *
 * 4000x4000 son 16 millones de celdas: en JavaScript eso son segundos y
 * varios cientos de megas. Un panel de aprobación que se congela es un panel
 * que se cierra sin aprobar.
 */
export const MAX_LCS_LINES = 4000;

function splitLines(s: string): string[] {
  if (s === "") return [];
  return s.split("\n");
}

/**
 * Comparación de respaldo para ficheros enormes: alinea por posición.
 *
 * Es peor que LCS —una línea insertada al principio desplaza todo y hace que
 * el resto parezca cambiado— pero es honesta sobre ello: `degraded` explica
 * qué se perdió, así que nadie lee el resultado como si fuera exacto.
 */
function positionalDiff(oldLines: string[], newLines: string[]): DiffLine[] {
  const out: DiffLine[] = [];
  const n = Math.max(oldLines.length, newLines.length);
  for (let i = 0; i < n; i++) {
    const a = oldLines[i];
    const b = newLines[i];
    if (a !== undefined && b !== undefined && a === b) {
      out.push({ op: "igual", text: a, oldNumber: i + 1, newNumber: i + 1 });
    } else {
      if (a !== undefined) {
        out.push({ op: "borrada", text: a, oldNumber: i + 1, newNumber: null });
      }
      if (b !== undefined) {
        out.push({ op: "añadida", text: b, oldNumber: null, newNumber: i + 1 });
      }
    }
  }
  return out;
}

/** Recorta prefijo y sufijo comunes: la mayoría de cambios tocan poco. */
function trimCommon(a: string[], b: string[]) {
  let head = 0;
  while (head < a.length && head < b.length && a[head] === b[head]) head++;
  let tail = 0;
  while (
    tail < a.length - head &&
    tail < b.length - head &&
    a[a.length - 1 - tail] === b[b.length - 1 - tail]
  ) {
    tail++;
  }
  return { head, tail };
}

export function diffLines(original: string, updated: string): DiffResult {
  const oldLines = splitLines(original ?? "");
  const newLines = splitLines(updated ?? "");

  // Recortar lo común por los extremos hace que la tabla LCS solo cubra la
  // parte que de verdad cambió, que en un cambio normal es una fracción.
  const { head, tail } = trimCommon(oldLines, newLines);
  const oldMid = oldLines.slice(head, oldLines.length - tail);
  const newMid = newLines.slice(head, newLines.length - tail);

  let midOps: DiffLine[];
  let degraded = "";

  if (oldMid.length > MAX_LCS_LINES || newMid.length > MAX_LCS_LINES) {
    degraded =
      `comparación aproximada: la parte cambiada supera ${MAX_LCS_LINES} ` +
      `líneas y la tabla exacta bloquearía la interfaz. Los bloques movidos ` +
      `pueden aparecer como borrado + añadido.`;
    midOps = positionalDiff(oldMid, newMid).map((l) => ({
      ...l,
      oldNumber: l.oldNumber === null ? null : l.oldNumber + head,
      newNumber: l.newNumber === null ? null : l.newNumber + head,
    }));
  } else {
    midOps = lcsDiff(oldMid, newMid, head);
  }

  const lines: DiffLine[] = [];
  for (let i = 0; i < head; i++) {
    lines.push({
      op: "igual", text: oldLines[i], oldNumber: i + 1, newNumber: i + 1,
    });
  }
  lines.push(...midOps);
  for (let i = 0; i < tail; i++) {
    const oi = oldLines.length - tail + i;
    const ni = newLines.length - tail + i;
    lines.push({
      op: "igual", text: oldLines[oi], oldNumber: oi + 1, newNumber: ni + 1,
    });
  }

  return {
    lines,
    added: lines.filter((l) => l.op === "añadida").length,
    removed: lines.filter((l) => l.op === "borrada").length,
    degraded,
  };
}

/** LCS clásico con tabla de programación dinámica. `offset` reubica los números. */
function lcsDiff(a: string[], b: string[], offset: number): DiffLine[] {
  const n = a.length;
  const m = b.length;

  // Casos degenerados: sin ellos la tabla de abajo funciona igual, pero
  // atajarlos evita reservar memoria para nada.
  if (n === 0) {
    return b.map((text, j) => ({
      op: "añadida" as DiffOp, text, oldNumber: null, newNumber: offset + j + 1,
    }));
  }
  if (m === 0) {
    return a.map((text, i) => ({
      op: "borrada" as DiffOp, text, oldNumber: offset + i + 1, newNumber: null,
    }));
  }

  // tabla[i][j] = longitud de la LCS de a[i:] y b[j:]
  const tabla: Uint32Array[] = Array.from(
    { length: n + 1 }, () => new Uint32Array(m + 1));
  for (let i = n - 1; i >= 0; i--) {
    for (let j = m - 1; j >= 0; j--) {
      tabla[i][j] = a[i] === b[j]
        ? tabla[i + 1][j + 1] + 1
        : Math.max(tabla[i + 1][j], tabla[i][j + 1]);
    }
  }

  const out: DiffLine[] = [];
  let i = 0;
  let j = 0;
  while (i < n && j < m) {
    if (a[i] === b[j]) {
      out.push({
        op: "igual", text: a[i],
        oldNumber: offset + i + 1, newNumber: offset + j + 1,
      });
      i++; j++;
    } else if (tabla[i + 1][j] >= tabla[i][j + 1]) {
      // Borrado antes que añadido cuando empatan: agrupa las líneas
      // sustituidas (borrada seguida de añadida) en vez de intercalarlas,
      // que es como se lee un cambio.
      out.push({
        op: "borrada", text: a[i], oldNumber: offset + i + 1, newNumber: null,
      });
      i++;
    } else {
      out.push({
        op: "añadida", text: b[j], oldNumber: null, newNumber: offset + j + 1,
      });
      j++;
    }
  }
  while (i < n) {
    out.push({
      op: "borrada", text: a[i], oldNumber: offset + i + 1, newNumber: null,
    });
    i++;
  }
  while (j < m) {
    out.push({
      op: "añadida", text: b[j], oldNumber: null, newNumber: offset + j + 1,
    });
    j++;
  }
  return out;
}

/** Resumen corto para cabeceras: "+12 −3". */
export function diffSummary(d: DiffResult): string {
  if (!d.added && !d.removed) return "sin cambios";
  return `+${d.added} −${d.removed}`;
}
