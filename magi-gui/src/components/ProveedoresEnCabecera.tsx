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

  const [error, setError] = useState(false);

  useEffect(() => {
    if (!fetchConfig) return;
    let vivo = true;
    let fallos = 0;
    let timer: ReturnType<typeof setTimeout>;

    const leer = async () => {
      try {
        const c = await fetchConfig();
        if (!vivo) return;
        fallos = 0;
        setError(false);
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
      } catch {
        // La cabecera nunca debe romper la app NI insistir contra un backend
        // que está fallando.
        //
        // La primera versión reintentaba cada 30 s pasara lo que pasara. Con
        // el handler `sys.config` roto —un nombre sin exportar— eso convirtió
        // un error puntual en una consulta fallida cada medio minuto, cada
        // una registrada como ERROR, cada una despertando a Naoko para
        // diagnosticarla. Sondear a ciegas es cómodo de escribir y caro de
        // sufrir.
        //
        // Ahora se espera cada vez más y se para a los cinco fallos. Si el
        // backend se recupera, el usuario tiene el botón «Releer» de la
        // pestaña Configuración.
        if (!vivo) return;
        fallos += 1;
        setError(true);
        if (fallos >= 5) return;
      }
      if (!vivo) return;
      // Espaciado creciente: 30 s, 60 s, 2 min, 4 min... Con todo en orden
      // basta con refrescar de vez en cuando; con algo roto, se aparta.
      timer = setTimeout(leer, 30_000 * Math.pow(2, fallos));
    };

    leer();
    return () => { vivo = false; clearTimeout(timer); };
    // `fetchConfig` FUERA de las dependencias. Este componente vive en la
    // cabecera, o sea que está montado SIEMPRE, y `useMagiSocket` devuelve una
    // función nueva en cada render: con ella aquí, el efecto se desmontaba y
    // se volvía a montar en cada render, relanzando el sondeo y programando un
    // `setTimeout` nuevo cada vez. Medido el 2026-08-20 sobre la app parada:
    // 97 % de un núcleo permanente, con el kernel a 0 %.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (error && !nodos.length) {
    return <span style={{ color: "#f87171" }}
                 title="El kernel no devolvió la configuración. Abre la pestaña Configuración y pulsa Releer.">
      enjambre · sin datos
    </span>;
  }
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
