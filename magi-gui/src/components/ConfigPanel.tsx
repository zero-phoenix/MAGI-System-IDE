/**
 * Panel de Configuración.
 *
 * EL FALLO QUE CIERRA
 * ===================
 * "Configuración" estaba en la lista PESTAÑAS de App.tsx, se pintaba en la
 * barra, se podía pulsar... y no existía ningún bloque que la renderizara. El
 * usuario hacía clic y el panel se quedaba en blanco. No era un panel roto:
 * era un panel que nunca se escribió.
 *
 * Todo lo que se ve aquí se lee del sistema en marcha (`sys.config`), no de
 * una copia en el frontend. Una pantalla de configuración que enseñe valores
 * escritos a mano miente en cuanto algo cambia, y este proyecto lleva media
 * docena de sesiones desmontando exactamente esa clase de mentira.
 */
import { useCallback, useEffect, useState } from "react";
import { clasificaRotos, puntosChispa, tendencia } from "../lib/salud";
import {
  Estadistica, Telemetria, hayDatos, lectura, ms, ordenadas,
} from "../lib/latencia";

type Candidato = { proveedor: string; modelo: string; latencia_ms: number | null };
type Familia = {
  id: string; familia: string; prioridad: number; verificada: boolean;
  disponible: boolean | null; en_rotacion: boolean;
  llamadas: number; tokens_in: number; tokens_out: number;
  candidatos: Candidato[];
  descartados?: Record<string, string>;
};
type Config = {
  enjambre: { reparto: Record<string, string>; familias: Record<string, string>;
              diversidad: string; nota: string };
  familias: Familia[];
  inferencia: { hedge_after_s: number; hedge_max: number;
                cache_entradas: number; familias_verificadas: string[] };
  herramientas: Record<string, string[]>;
  dominios: string[];
  rutas: Record<string, any>;
  cortafuegos: Record<string, any>;
  violaciones: { source: string; detail: string }[];
  telemetria?: Telemetria;
  sonda?: {
    ventana_dias: number;
    familias: {
      familia: string; mejor_ms: number | null; vivos: number; total: number;
      candidatos: {
        proveedor: string; modelo: string;
        media_historica_ms: number | null; ultima_ms: number | null;
        tasa_exito: number | null; vivo: boolean; medido: boolean;
        historico?: { dia: string; media_ms: number; n: number }[];
      }[];
    }[];
  };
  catalogo?: {
    rotos_motivos?: Record<string, string>;
    rotos_imposibles?: string[];
    rotos_caidos?: string[];
  };
};

const DIVERSIDAD: Record<string, { txt: string; color: string }> = {
  full: { txt: "completa — cada nodo en una familia distinta", color: "#4ade80" },
  partial: { txt: "parcial — dos nodos comparten familia", color: "#fbbf24" },
  degraded: { txt: "degradada — una sola familia disponible", color: "#f87171" },
  none: { txt: "sin proveedores sanos", color: "#f87171" },
};

const caja: React.CSSProperties = {
  background: "#050a0b", border: "1px solid var(--dim)",
  padding: "14px", marginBottom: "14px",
};
const titulo: React.CSSProperties = {
  color: "var(--acc)", fontSize: "13px", letterSpacing: "1px",
  textTransform: "uppercase", marginBottom: "10px",
};
const th: React.CSSProperties = {
  padding: "6px 8px", borderBottom: "1px solid var(--dim)",
  textAlign: "left", color: "var(--dim)", fontWeight: 400,
};
const td: React.CSSProperties = { padding: "6px 8px", borderBottom: "1px solid #10191b" };

function Pastilla({ ok, si, no }: { ok: boolean; si: string; no: string }) {
  return (
    <span style={{
      padding: "1px 7px", fontSize: "10px", borderRadius: "2px",
      background: ok ? "#0d2b17" : "#2b0d0d",
      color: ok ? "#4ade80" : "#f87171",
      border: `1px solid ${ok ? "#1f6b3a" : "#6b1f1f"}`,
    }}>{ok ? si : no}</span>
  );
}

/**
 * Tabla de un grupo (agentes, familias o herramientas) ordenada por p95.
 *
 * La columna «mediana» va antes que «p95» a propósito: leídas en ese orden,
 * las dos juntas cuentan la historia sin necesidad de explicarla — «suele
 * tardar esto, y cuando va mal, esto otro».
 */
function TablaLatencia({ que, filas }: { que: string; filas: Estadistica[] }) {
  if (!filas.length) return null;
  return (
    <div style={{ marginBottom: "14px" }}>
      <div style={{ fontSize: "11px", color: "var(--dim)", marginBottom: "4px",
                    textTransform: "uppercase", letterSpacing: "1px" }}>
        {que}
      </div>
      <table style={{ width: "100%", fontSize: "12px", borderCollapse: "collapse" }}>
        <thead>
          <tr>
            <th style={th}>{que}</th>
            <th style={th}>medidas</th>
            <th style={th}>mediana</th>
            <th style={th}>p95</th>
            <th style={th}>peor</th>
          </tr>
        </thead>
        <tbody>
          {filas.map((f) => (
            <tr key={f.clave}>
              <td style={td}>
                {f.clave}
                {!f.fiable && (
                  <span style={{ color: "#fbbf24", marginLeft: 6, fontSize: "10px" }}>
                    pocas medidas
                  </span>
                )}
                <div style={{ fontSize: "11px", color: "var(--dim)", marginTop: 2 }}>
                  {lectura(f)}
                </div>
              </td>
              <td style={td}>{f.n}</td>
              <td style={td}>{ms(f.mediana_ms)}</td>
              <td style={{ ...td, color: "var(--acc)" }}>{ms(f.p95_ms)}</td>
              <td style={{ ...td, color: "var(--dim)" }}>{ms(f.peor_ms)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/**
 * Dónde se va el tiempo. Ordenado por p95, no por media.
 *
 * Los datos ya estaban en la base desde que existe la telemetría: cada turno y
 * cada uso de herramienta se guardan con su duración. Lo único que faltaba era
 * leerlos — es el mismo patrón que ya apareció con la contabilidad de tokens y
 * con el panel de salud: la pieza construida y el cable que no está.
 */
function TiempoPerdido({ tel }: { tel?: Telemetria }) {
  const cuellos = tel?.cuellos;
  const avisos = tel?.avisos_lentitud ?? [];
  if (!hayDatos(cuellos) && !avisos.length) return null;

  return (
    <div style={caja}>
      <div style={titulo}>Dónde se va el tiempo</div>

      {avisos.length > 0 && (
        <div style={{ border: "1px solid #fbbf24", padding: "8px 10px",
                      marginBottom: "12px", fontSize: "12px" }}>
          <div style={{ color: "#fbbf24", marginBottom: 4 }}>
            Se han salido de su propio comportamiento
          </div>
          {avisos.map((a) => (
            <div key={a.herramienta} style={{ marginBottom: 3 }}>
              <b>{a.herramienta}</b>: {ms(a.ultima_ms)} en su última ejecución,
              {" "}{a.veces_el_p95}× su p95 habitual ({ms(a.p95_historico_ms)}
              {" "}sobre {a.muestras} medidas).
            </div>
          ))}
          <div style={{ color: "var(--dim)", fontSize: "11px", marginTop: 5 }}>
            Cada herramienta se compara consigo misma, no con un umbral común:
            que <i>run_tests</i> tarde 40 s es normal y que <i>read_file</i>
            {" "}tarde 4 s no lo es.
          </div>
        </div>
      )}

      <TablaLatencia que="agente" filas={ordenadas(cuellos?.agentes)} />
      <TablaLatencia que="familia" filas={ordenadas(cuellos?.familias)} />
      <TablaLatencia que="herramienta" filas={ordenadas(cuellos?.herramientas)} />

      <div style={{ fontSize: "11px", color: "var(--dim)" }}>
        Se ordena por p95 y no por la media. Una media no distingue «siempre
        tarda 4 s» de «suele tardar 1 s y una de cada diez veces tarda 30»: son
        el mismo número y problemas distintos. El p95 dice cuánto tarda cuando
        va mal; la columna «peor», cuánto puede llegar a tardar.
      </div>
    </div>
  );
}

export function ConfigPanel({ fetchConfig }: { fetchConfig: () => Promise<any> }) {
  const [cfg, setCfg] = useState<Config | null>(null);
  const [error, setError] = useState("");
  const [cargando, setCargando] = useState(false);

  const cargar = useCallback(async () => {
    setCargando(true);
    setError("");
    try {
      setCfg(await fetchConfig());
    } catch (e: any) {
      setError(e?.message || "no se pudo leer la configuración");
    } finally {
      setCargando(false);
    }
  }, [fetchConfig]);

  useEffect(() => { cargar(); }, [cargar]);

  if (error) {
    return (
      <div style={{ ...caja, color: "#f87171", margin: "20px" }}>
        No se pudo leer la configuración: {error}
        <div style={{ marginTop: "10px" }}>
          <button className="bt go" onClick={cargar}>Reintentar</button>
        </div>
      </div>
    );
  }
  if (!cfg) {
    return <div style={{ padding: "24px", color: "var(--dim)" }}>
      Leyendo la configuración del sistema…
    </div>;
  }

  const div = DIVERSIDAD[cfg.enjambre.diversidad] ??
              { txt: cfg.enjambre.diversidad, color: "var(--dim)" };
  const fuego = cfg.cortafuegos || {};
  const capas = ["popen", "webbrowser", "cdp", "nodriver"];

  return (
    <div style={{ flex: 1, overflowY: "auto", padding: "18px", color: "#cfe0e4",
                  userSelect: "text", WebkitUserSelect: "text" }}>
      <div style={{ display: "flex", alignItems: "center", gap: "12px",
                    marginBottom: "16px" }}>
        <h2 style={{ color: "var(--acc)", margin: 0 }}>Configuración del sistema</h2>
        <button className="bt" onClick={cargar} disabled={cargando}>
          {cargando ? "Leyendo…" : "Releer"}
        </button>
        <span style={{ color: "var(--dim)", fontSize: "11px" }}>
          Todo lo de abajo se lee del sistema en marcha, no de una copia.
        </span>
      </div>

      {/* ---------------------------------------------------- enjambre */}
      <div style={caja}>
        <div style={titulo}>Reparto del enjambre</div>
        <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
          {Object.entries(cfg.enjambre.reparto).map(([rol, prov]) => (
            <div key={rol} style={{ flex: "1 1 200px", border: "1px solid var(--gr)",
                                    padding: "10px", background: "#020506" }}>
              <div style={{ color: "var(--acc)", fontWeight: 700 }}>{rol}</div>
              <div style={{ fontSize: "12px" }}>{prov}</div>
              <div style={{ fontSize: "11px", color: "var(--dim)" }}>
                familia {cfg.enjambre.familias[rol]}
              </div>
            </div>
          ))}
        </div>
        <div style={{ marginTop: "10px", fontSize: "12px", color: div.color }}>
          Diversidad: {div.txt}
        </div>
        {cfg.enjambre.nota && (
          <div style={{ fontSize: "11px", color: "var(--dim)" }}>{cfg.enjambre.nota}</div>
        )}
      </div>

      {/* --------------------------------------------------- inferencia */}
      <div style={caja}>
        <div style={titulo}>Inferencia</div>
        <table style={{ width: "100%", fontSize: "12px", borderCollapse: "collapse" }}>
          <tbody>
            <tr><td style={td}>Petición cubierta a partir de</td>
                <td style={td}>{cfg.inferencia.hedge_after_s} s</td></tr>
            <tr><td style={td}>Llamadas simultáneas por familia</td>
                <td style={td}>{cfg.inferencia.hedge_max}</td></tr>
            <tr><td style={td}>Respuestas en caché</td>
                <td style={td}>{cfg.inferencia.cache_entradas}</td></tr>
            <tr><td style={td}>Familias verificadas</td>
                <td style={td}>{cfg.inferencia.familias_verificadas.join(", ")}</td></tr>
          </tbody>
        </table>
        <div style={{ fontSize: "11px", color: "var(--dim)", marginTop: "8px" }}>
          Si un candidato no contesta en {cfg.inferencia.hedge_after_s} s se lanza
          el siguiente en paralelo y gana el que responda antes. Misma respuesta,
          sin pagar la cola de latencia.
        </div>
      </div>

      {/* ------------------------------------------ §3.2 dónde se va el tiempo */}
      <TiempoPerdido tel={cfg.telemetria} />

      {/* ---------------------------------------------------- proveedores */}
      <div style={caja}>
        <div style={titulo}>Proveedores y latencia medida</div>
        <table style={{ width: "100%", fontSize: "12px", borderCollapse: "collapse" }}>
          <thead>
            <tr>
              <th style={th}>Familia</th><th style={th}>Estado</th>
              <th style={th}>Prio</th><th style={th}>Llamadas</th>
              <th style={th}>Candidatos (proveedor · modelo · latencia)</th>
            </tr>
          </thead>
          <tbody>
            {cfg.familias.map((f) => (
              <tr key={f.id}>
                <td style={{ ...td, color: "var(--acc)" }}>{f.familia}</td>
                <td style={td}>
                  <div style={{ display: "flex", gap: "4px", flexWrap: "wrap" }}>
                    <Pastilla ok={f.verificada} si="verificada" no="sin verificar" />
                    <Pastilla ok={f.en_rotacion} si="en rotación" no="cortacircuitos" />
                  </div>
                </td>
                <td style={td}>{f.prioridad}</td>
                <td style={td}>{f.llamadas}</td>
                <td style={td}>
                  {f.candidatos.map((c, i) => {
                    const motivo = f.descartados?.[c.proveedor];
                    return (
                      <div key={i} title={motivo || undefined}
                           style={{
                             color: motivo ? "#6b7a7d"
                                           : (c.latencia_ms ? "#cfe0e4" : "var(--dim)"),
                             textDecoration: motivo ? "line-through" : "none",
                           }}>
                        {c.proveedor} · {c.modelo}
                        {motivo
                          ? <span style={{ textDecoration: "none", color: "#fbbf24" }}>
                              {"  — "}{motivo}
                            </span>
                          : (c.latencia_ms ? ` · ${c.latencia_ms} ms` : " · sin medir")}
                      </div>
                    );
                  })}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* ------------------------------------------- salud por día (sonda) */}
      {cfg.sonda && cfg.sonda.familias.length > 0 && (
        <div style={caja}>
          <div style={titulo}>
            Salud por día — la pendiente, no la media
          </div>
          <table style={{ width: "100%", fontSize: "12px", borderCollapse: "collapse" }}>
            <thead>
              <tr>
                <th style={th}>Familia</th><th style={th}>Candidato</th>
                <th style={th}>14 días</th><th style={th}>Media hist.</th>
                <th style={th}>Última</th><th style={th}>Tendencia</th>
              </tr>
            </thead>
            <tbody>
              {cfg.sonda.familias.map((f) =>
                f.candidatos.map((c, i) => {
                  const serie = c.historico || [];
                  const tnd = tendencia(serie);
                  return (
                    <tr key={`${f.familia}-${i}`}>
                      {i === 0 && (
                        <td rowSpan={f.candidatos.length}
                            style={{ ...td, color: "var(--acc)", verticalAlign: "top" }}>
                          {f.familia}
                          <div style={{ color: "var(--dim)", fontSize: "11px" }}>
                            {f.vivos}/{f.total} vivos
                          </div>
                        </td>
                      )}
                      <td style={td}>
                        {c.proveedor} · {c.modelo}
                        {!c.vivo && <span style={{ color: "#f87171" }}> ✗</span>}
                      </td>
                      <td style={td}>
                        {serie.length >= 2 ? (
                          <svg width="90" height="22" aria-label="latencia diaria">
                            <polyline points={puntosChispa(serie, 90, 22)}
                                      fill="none" stroke="var(--acc)" strokeWidth="1.5" />
                          </svg>
                        ) : (
                          <span style={{ color: "var(--dim)" }}>sin serie</span>
                        )}
                      </td>
                      <td style={td}>{c.media_historica_ms
                        ? `${c.media_historica_ms} ms` : "—"}</td>
                      <td style={td}>{c.ultima_ms ? `${c.ultima_ms} ms` : "—"}</td>
                      <td style={{ ...td, color:
                        tnd === "empeora" ? "#f87171" :
                        tnd === "mejora" ? "#4ade80" : "var(--dim)" }}>
                        {tnd ?? "—"}
                      </td>
                    </tr>
                  );
                }),
              )}
            </tbody>
          </table>
          <div style={{ color: "var(--dim)", fontSize: "11px", marginTop: 5 }}>
            La chispa es la latencia media de cada día con datos (más alto =
            más lento). Una media histórica de 30 días esconde que algo pasó
            de 3 s a 9 s esta semana; la pendiente no.
          </div>
        </div>
      )}

      {/* ------------------------------------------- rotos, con su motivo */}
      {cfg.catalogo?.rotos_motivos &&
        Object.keys(cfg.catalogo.rotos_motivos).length > 0 && (() => {
        const { imposibles, caidos } = clasificaRotos(cfg.catalogo.rotos_motivos);
        return (
          <div style={caja}>
            <div style={titulo}>Por qué faltan proveedores</div>
            {imposibles.length > 0 && (
              <div style={{ marginBottom: "8px" }}>
                <div style={{ color: "#f87171", fontSize: "12px", marginBottom: "4px" }}>
                  No van a volver — exigen tu cuenta o abren navegador:
                </div>
                {imposibles.map(([p_, m]) => (
                  <div key={p_} style={{ fontSize: "11px", color: "var(--dim)" }}>
                    <span style={{ color: "#cfe0e4" }}>{p_}</span> — {m}
                  </div>
                ))}
              </div>
            )}
            {caidos.length > 0 && (
              <div>
                <div style={{ color: "#fbbf24", fontSize: "12px", marginBottom: "4px" }}>
                  Caídos ahora, pueden volver:
                </div>
                {caidos.map(([p_, m]) => (
                  <div key={p_} style={{ fontSize: "11px", color: "var(--dim)" }}>
                    <span style={{ color: "#cfe0e4" }}>{p_}</span> — {m}
                  </div>
                ))}
              </div>
            )}
          </div>
        );
      })()}

      {/* ---------------------------------------------------- cortafuegos */}
      <div style={caja}>
        <div style={titulo}>Cortafuegos de navegador (§I.3)</div>
        <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", marginBottom: "8px" }}>
          {capas.map((c) => (
            <Pastilla key={c} ok={!!fuego[c]} si={`${c} ✓`} no={`${c} ✗`} />
          ))}
        </div>
        <div style={{ fontSize: "12px" }}>
          Intentos bloqueados: <b>{fuego.violations ?? 0}</b>
        </div>
        {cfg.violaciones?.length > 0 && (
          <ul style={{ fontSize: "11px", color: "var(--dim)", marginTop: "6px" }}>
            {cfg.violaciones.map((v, i) => <li key={i}>{v.source} — {v.detail}</li>)}
          </ul>
        )}
      </div>

      {/* --------------------------------------------------- herramientas */}
      <div style={caja}>
        <div style={titulo}>Herramientas por rol</div>
        <div style={{ fontSize: "11px", color: "var(--dim)", marginBottom: "8px" }}>
          El catálogo se acota al dominio de la tarea. Dominios: {cfg.dominios.join(", ")}.
        </div>
        {Object.entries(cfg.herramientas).map(([rol, lista]) => (
          <div key={rol} style={{ marginBottom: "8px" }}>
            <div style={{ color: "var(--acc)", fontSize: "12px" }}>
              {rol} <span style={{ color: "var(--dim)" }}>({lista.length})</span>
            </div>
            <div style={{ fontSize: "11px", color: "#9fb3b8", lineHeight: 1.6 }}>
              {lista.join(" · ")}
            </div>
          </div>
        ))}
      </div>

      {/* --------------------------------------------------------- rutas */}
      <div style={caja}>
        <div style={titulo}>Rutas</div>
        <table style={{ width: "100%", fontSize: "12px", borderCollapse: "collapse" }}>
          <tbody>
            {Object.entries(cfg.rutas).map(([k, v]) => (
              <tr key={k}>
                <td style={{ ...td, color: "var(--dim)", width: "160px" }}>{k}</td>
                <td style={{ ...td, wordBreak: "break-all" }}>{String(v)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default ConfigPanel;
