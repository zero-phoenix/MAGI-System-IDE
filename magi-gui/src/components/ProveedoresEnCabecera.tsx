/**
 * Los tres nodos del enjambre en la barra superior, con nombre y latencia.
 *
 * LO QUE HABÍA
 * ============
 *     prov-a 31/50   prov-b agotado   prov-c ok
 *
 * Tres etiquetas que no significan nada. No decían a qué proveedor
 * correspondía cada letra, ni qué era «31/50», ni por qué «prov-b» estaba
 * agotado. El usuario preguntó literalmente por qué no se entienden.
 *
 * Y encima estaban desactualizadas: el reparto real es MELCHIOR→gpt,
 * BALTHASAR→gemini, CASPER→command, así que ni siquiera había tres
 * proveedores anónimos a los que las letras pudieran referirse.
 *
 * Ahora cada pastilla dice el ROL, la FAMILIA que lo atiende y su latencia
 * medida, con color según el estado. Al pasar el ratón, la explicación entera.
 */
import { useEffect, useState } from "react";

type Nodo = { rol: string; familia: string; ms: number | null; sano: boolean };

const CORTO: Record<string, string> = {
  MELCHIOR: "MEL", BALTHASAR: "BAL", CASPER: "CAS",
};

const QUE_HACE: Record<string, string> = {
  MELCHIOR: "propone",
  BALTHASAR: "busca fallos",
  CASPER: "decide",
};

function color(n: Nodo) {
  if (!n.sano) return "#f87171";
  if (n.ms === null) return "var(--dim)";
  if (n.ms < 4000) return "#4ade80";
  if (n.ms < 12000) return "#fbbf24";
  return "#f87171";
}

export function ProveedoresEnCabecera({ fetchConfig }: {
  fetchConfig?: () => Promise<any>;
}) {
  const [nodos, setNodos] = useState<Nodo[]>([]);

  useEffect(() => {
    if (!fetchConfig) return;
    let vivo = true;
    const leer = async () => {
      try {
        const c = await fetchConfig();
        if (!vivo) return;
        const porId: Record<string, any> = {};
        for (const f of c.familias || []) porId[f.id] = f;
        const out: Nodo[] = Object.entries(c.enjambre?.reparto || {})
          .map(([rol, provId]) => {
            const f = porId[provId as string];
            const medidos = (f?.candidatos || [])
              .map((x: any) => x.latencia_ms)
              .filter((x: any) => typeof x === "number");
            return {
              rol,
              familia: c.enjambre?.familias?.[rol] || "?",
              ms: medidos.length ? Math.min(...medidos) : null,
              sano: !!f?.en_rotacion,
            };
          });
        setNodos(out);
      } catch { /* la cabecera nunca debe romper la app */ }
    };
    leer();
    // Cada 30 s: lo justo para que la latencia se vea viva sin castigar al
    // kernel con una consulta por segundo.
    const t = setInterval(leer, 30_000);
    return () => { vivo = false; clearInterval(t); };
  }, [fetchConfig]);

  if (!nodos.length) {
    return <span style={{ color: "var(--dim)" }} title="Aún no se ha medido ningún proveedor">
      enjambre · sondeando
    </span>;
  }

  return (
    <span style={{ display: "inline-flex", gap: "10px", marginRight: "10px" }}>
      {nodos.map((n) => (
        <span key={n.rol}
              title={`${n.rol} — el que ${QUE_HACE[n.rol] || "trabaja"}. `
                     + `Familia de modelo: ${n.familia}. `
                     + (n.ms !== null ? `Última latencia medida: ${n.ms} ms. `
                                      : "Todavía sin medir. ")
                     + (n.sano ? "En rotación."
                               : "FUERA de rotación: su cortacircuitos está abierto "
                                 + "tras varios fallos seguidos.")}>
          <span style={{ color: "var(--dim)" }}>{CORTO[n.rol] || n.rol}</span>{" "}
          <b style={{ color: color(n) }}>{n.familia}</b>
          {n.ms !== null && (
            <span style={{ color: "var(--dim)" }}> {(n.ms / 1000).toFixed(1)}s</span>
          )}
        </span>
      ))}
    </span>
  );
}

export default ProveedoresEnCabecera;
