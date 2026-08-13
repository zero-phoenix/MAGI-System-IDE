/**
 * El debate, agrupado en rondas y con la conclusión de cada una.
 *
 * POR QUÉ EXISTE
 * ==============
 * El gráfico HDC pintaba una cadena plana: un nodo por mensaje, uno detrás de
 * otro, todos iguales. Con eso no se podía contestar a lo único que se le
 * pregunta a un diagrama de un debate:
 *
 *   · ¿en qué ronda vamos?
 *   · ¿qué se decidió en cada una?
 *   · ¿qué falta para que termine la actual?
 *
 * Y como cada variante de Melchior publicaba su propio mensaje, una ronda
 * podía aparecer con cinco cajas de las que tres eran el mismo agente. La
 * cadena crecía y contaba cada vez menos.
 *
 * Aquí se agrupa. Una ronda empieza cuando habla MELCHIOR y se cierra cuando
 * responde CASPER; su conclusión es el veredicto de Casper, porque es quien
 * arbitra. Lo demás es detalle, y el detalle se pliega.
 *
 * Todo son funciones puras: el componente pinta, aquí se decide qué contar.
 */

export interface MensajeAgente {
  agent: string;
  role?: string;
  content?: string;
  stats?: string;
  provider?: string;
  family?: string;
}

export type EstadoNodo = "hecho" | "en curso" | "pendiente";

export interface NodoRonda {
  agente: string;
  papel: string;
  estado: EstadoNodo;
  familia?: string;
  resumen?: string;
  /**
   * El mensaje ENTERO, no solo su primera frase.
   *
   * La caja del gráfico pinta `resumen`, pero medir si BALTHASAR aporta algo
   * distinto de MELCHIOR (ver `calidadDebate.ts`) necesita el texto completo:
   * comparar dos primeras frases diría más sobre cómo empiezan a escribir que
   * sobre si están de acuerdo.
   */
  texto?: string;
}

export interface Ronda {
  numero: number;
  cerrada: boolean;
  nodos: NodoRonda[];
  /** Veredicto de Casper, o null mientras no haya cerrado. */
  conclusion: string | null;
}

/** El orden del debate. Es también el que decide cuándo empieza una ronda. */
export const SECUENCIA = ["MELCHIOR", "BALTHASAR", "CASPER"] as const;

const PAPEL: Record<string, string> = {
  MELCHIOR: "tesis",
  BALTHASAR: "antítesis",
  CASPER: "síntesis",
};

/**
 * Primera frase con contenido de un mensaje, para el resumen de la caja.
 *
 * Se salta encabezados markdown y bloques de código: una caja que dice
 * «```python» no resume nada. Si no hay prosa, se dice que no la hay en vez de
 * enseñar un fragmento arbitrario.
 */
export function primeraFrase(texto: string | undefined, max = 90): string {
  if (!texto) return "";
  const limpio = texto
    .replace(/```[\s\S]*?```/g, " ")     // bloques de código fuera
    .replace(/^#{1,6}\s+/gm, "")         // encabezados
    .replace(/[*_`>|-]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
  if (!limpio) return "";
  const corte = limpio.search(/[.;:]\s/);
  const frase = corte > 20 ? limpio.slice(0, corte + 1) : limpio;
  return frase.length > max ? frase.slice(0, max - 1).trimEnd() + "…" : frase;
}

/**
 * El veredicto de una ronda, leído del mensaje de Casper.
 *
 * Se mira primero `stats` —donde el backend pone «Decisión: X»— y solo si no
 * está se busca en el texto. El orden importa: `stats` es un dato estructurado
 * y el texto es prosa donde la palabra puede aparecer citando otra cosa.
 */
export function conclusionDe(msg: MensajeAgente | undefined): string | null {
  if (!msg) return null;
  const s = msg.stats || "";
  const m = /Decisi[óo]n:\s*(.+)/i.exec(s);
  if (m) return normalizaVeredicto(m[1].trim());
  const t = (msg.content || "").slice(-400);
  const m2 = /DECISI[ÓO]N\s*:\s*(.+)/i.exec(t);
  return m2 ? normalizaVeredicto(m2[1].trim()) : null;
}

function normalizaVeredicto(v: string): string {
  const u = v.toUpperCase();
  if (u.includes("REJECT") || u.includes("REVIS") || u.includes("RECHAZ")) {
    return "necesita revisión";
  }
  if (u.includes("APPROV") || u.includes("APROB")) return "aprobada";
  return v;
}

/**
 * Agrupa los mensajes en rondas.
 *
 * Una ronda nueva empieza cada vez que habla MELCHIOR, porque él abre el ciclo
 * dialéctico. Los mensajes que llegan antes del primer Melchior —avisos del
 * sistema, saludos— no pertenecen a ninguna ronda y no se cuelan en la
 * primera.
 */
export function agruparEnRondas(mensajes: MensajeAgente[]): Ronda[] {
  const rondas: Ronda[] = [];
  let actual: MensajeAgente[] | null = null;

  const cerrar = () => {
    if (!actual) return;
    rondas.push(construir(rondas.length + 1, actual));
    actual = null;
  };

  for (const m of mensajes ?? []) {
    if (m.agent === "MELCHIOR") {
      cerrar();
      actual = [m];
    } else if (actual && SECUENCIA.includes(m.agent as any)) {
      actual.push(m);
    }
  }
  cerrar();
  return rondas;
}

function construir(numero: number, mensajes: MensajeAgente[]): Ronda {
  const porAgente = new Map(mensajes.map((m) => [m.agent, m]));
  const casper = porAgente.get("CASPER");

  // «En curso» es el siguiente que no ha hablado; los de después, pendientes.
  // Sin esa distinción, una ronda a medias parece una ronda rota.
  let vistoHueco = false;
  const nodos: NodoRonda[] = SECUENCIA.map((agente) => {
    const msg = porAgente.get(agente);
    let estado: EstadoNodo;
    if (msg) {
      estado = "hecho";
    } else if (!vistoHueco) {
      estado = "en curso";
      vistoHueco = true;
    } else {
      estado = "pendiente";
    }
    return {
      agente,
      papel: PAPEL[agente] ?? "",
      estado,
      familia: msg?.family,
      resumen: primeraFrase(msg?.content),
      texto: msg?.content,
    };
  });

  return {
    numero,
    cerrada: Boolean(casper),
    nodos,
    conclusion: conclusionDe(casper),
  };
}

/** «Ronda 2 de 2 · en curso» — el encabezado del gráfico. */
export function tituloDelDebate(rondas: Ronda[]): string {
  if (!rondas.length) return "Sin rondas todavía";
  const ultima = rondas[rondas.length - 1];
  const total = rondas.length;
  if (ultima.cerrada) {
    return `${total} ronda${total > 1 ? "s" : ""} · cerrada`;
  }
  const faltan = ultima.nodos.filter((n) => n.estado !== "hecho");
  const quien = faltan.length ? faltan[0].agente : "";
  return `Ronda ${ultima.numero} de ${total} · en curso${quien ? ` (${quien})` : ""}`;
}
