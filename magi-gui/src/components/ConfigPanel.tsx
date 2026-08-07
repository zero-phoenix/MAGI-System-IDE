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

type Candidato = { proveedor: string; modelo: string; latencia_ms: number | null };
type Familia = {
  id: string; familia: string; prioridad: number; verificada: boolean;
  disponible: boolean | null; en_rotacion: boolean;
  llamadas: number; tokens_in: number; tokens_out: number;
  candidatos: Candidato[];
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
                  {f.candidatos.map((c, i) => (
                    <div key={i} style={{ color: c.latencia_ms ? "#cfe0e4" : "var(--dim)" }}>
                      {c.proveedor} · {c.modelo}
                      {c.latencia_ms ? ` · ${c.latencia_ms} ms` : " · sin medir"}
                    </div>
                  ))}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

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
