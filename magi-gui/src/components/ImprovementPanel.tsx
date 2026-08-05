/**
 * Ciclo de mejora de Naoko (rol creativo + rondas del enjambre).
 *
 * LO QUE ESTE PANEL TIENE QUE DEJAR CLARO
 * =======================================
 * Naoko repara sola y sin preguntar. Pero MEJORAR es otra cosa: cambia hacia
 * dónde va el sistema, y ese criterio es del usuario. Por eso el ciclo tiene
 * cuatro compuertas —desarrollar el plan, pasarlo al enjambre, aprobar el plan
 * final, publicar— y este panel existe para que se vean.
 *
 * La pregunta pendiente va ARRIBA y en grande. Un panel donde hay que buscar
 * qué se está preguntando acaba con el usuario pulsando «sí» sin leer, que es
 * la peor forma posible de tener compuertas.
 */
import { useEffect, useState } from "react";
import { useMagiStore } from "../store";

const ETAPAS: Record<string, string> = {
  idea: "Idea propuesta",
  plan_borrador: "Plan redactado",
  ronda: "Circulando por el enjambre",
  plan_final: "Plan hiperperfeccionado",
  ejecutando: "Aplicándose",
  esperando_publicacion: "Aplicada, sin publicar",
  publicado: "Publicada",
  descartada: "Descartada",
};

interface Props {
  listImprovements: () => Promise<any>;
  proposeImprovement: (t: string, r: string) => Promise<any>;
  decideImprovement: (id: string, approve: boolean) => Promise<any>;
}

export default function ImprovementPanel(
  { listImprovements, proposeImprovement, decideImprovement }: Props,
) {
  const enVivo = useMagiStore((s) => s.improvement);
  const [lista, setLista] = useState<any[]>([]);
  const [titulo, setTitulo] = useState("");
  const [motivo, setMotivo] = useState("");
  const [error, setError] = useState("");
  const [ocupado, setOcupado] = useState(false);

  const recargar = async () => {
    try {
      setLista((await listImprovements())?.all ?? []);
      setError("");
    } catch (e: any) {
      setError(e?.message || String(e));
    }
  };

  useEffect(() => { recargar(); }, []);
  // Cuando Naoko publica una transición, la lista de al lado queda vieja.
  useEffect(() => { if (enVivo) recargar(); }, [enVivo?.stage, enVivo?.improvement_id]);

  const decidir = async (id: string, aprueba: boolean) => {
    setOcupado(true); setError("");
    try {
      await decideImprovement(id, aprueba);
      await recargar();
    } catch (e: any) {
      setError(e?.message || String(e));
    } finally {
      setOcupado(false);
    }
  };

  const proponer = async () => {
    if (!titulo.trim()) return;
    setOcupado(true); setError("");
    try {
      await proposeImprovement(titulo.trim(), motivo.trim());
      setTitulo(""); setMotivo("");
      await recargar();
    } catch (e: any) {
      setError(e?.message || String(e));
    } finally {
      setOcupado(false);
    }
  };

  const pendientes = lista.filter((m) => m.awaiting_user);
  const boton: React.CSSProperties = {
    cursor: "pointer", padding: "5px 14px", fontSize: 12, borderRadius: 3,
    border: "1px solid var(--dim)",
  };

  return (
    <div style={{ padding: 14, overflowY: "auto", height: "100%", fontSize: 12 }}>
      {error && <div style={{ color: "#ff9a9a", marginBottom: 10 }}>{error}</div>}

      {/* La pregunta pendiente, arriba y sin que haya que buscarla. */}
      {pendientes.map((m) => (
        <div key={m.improvement_id}
             style={{ marginBottom: 14, padding: 12, borderRadius: 4,
                      background: "rgba(255,170,0,0.10)",
                      border: "1px solid rgba(255,170,0,0.35)" }}>
          <div style={{ color: "#ffcc66", fontSize: 14, marginBottom: 4 }}>
            {m.question}
          </div>
          <div style={{ color: "var(--dim)", marginBottom: 8 }}>
            {m.title} · {m.origin === "naoko" ? "idea de Naoko" : "propuesta tuya"}
            {m.circuit > 0 && ` · ${m.circuit} circuito(s) del enjambre`}
          </div>
          {m.plan && (
            <pre style={{ maxHeight: 220, overflowY: "auto", whiteSpace: "pre-wrap",
                          color: "#a8bcc1", margin: "0 0 8px" }}>{m.plan}</pre>
          )}
          <div style={{ display: "flex", gap: 8 }}>
            <button style={{ ...boton, background: "rgba(0,255,100,0.18)", color: "#7dfaa8" }}
                    disabled={ocupado}
                    onClick={() => decidir(m.improvement_id, true)}>Sí, adelante</button>
            <button style={{ ...boton, background: "rgba(255,50,50,0.18)", color: "#ff9a9a" }}
                    disabled={ocupado}
                    onClick={() => decidir(m.improvement_id, false)}>No, descarta</button>
          </div>
        </div>
      ))}

      {/* Narración en vivo: se pidió ver cada paso, no un resultado al final. */}
      {enVivo && !enVivo.awaiting_user && (
        <div style={{ marginBottom: 14, padding: 10, borderRadius: 4,
                      border: "1px solid var(--dim)" }}>
          <div style={{ color: "var(--acc)", marginBottom: 4 }}>
            {ETAPAS[enVivo.stage] ?? enVivo.stage} — {enVivo.title}
          </div>
          {(enVivo.rounds ?? []).map((r: any, i: number) => (
            <div key={i} style={{ color: "var(--dim)" }}>
              · circuito {r.circuit} · {r.agent}
            </div>
          ))}
          {(enVivo.execution_log ?? []).slice(-12).map((l: string, i: number) => (
            <div key={`e${i}`} style={{ color: "#a8bcc1" }}>· {l}</div>
          ))}
        </div>
      )}

      {/* Tu propia propuesta: recorre exactamente el mismo circuito. */}
      <div style={{ marginBottom: 16 }}>
        <div style={{ color: "var(--acc)", marginBottom: 6 }}>
          Proponer una mejora
        </div>
        <div style={{ color: "var(--dim)", marginBottom: 6 }}>
          Tu propuesta recorre lo mismo que una idea de Naoko: dos circuitos de
          Melchior → Balthasar → Casper antes de volver a ti. Que la idea sea
          tuya no la exime de la crítica.
        </div>
        <input value={titulo} onChange={(e) => setTitulo(e.target.value)}
               placeholder="Qué mejorar"
               style={{ width: "100%", padding: "5px 8px", marginBottom: 6,
                        background: "#0a1013", color: "#cfe0e4",
                        border: "1px solid var(--dim)", borderRadius: 3 }} />
        <input value={motivo} onChange={(e) => setMotivo(e.target.value)}
               placeholder="Por qué (opcional)"
               style={{ width: "100%", padding: "5px 8px", marginBottom: 6,
                        background: "#0a1013", color: "#cfe0e4",
                        border: "1px solid var(--dim)", borderRadius: 3 }} />
        <button style={{ ...boton, background: "rgba(0,200,255,0.12)", color: "var(--acc)" }}
                disabled={ocupado || !titulo.trim()} onClick={proponer}>
          Proponer
        </button>
      </div>

      <div style={{ color: "var(--acc)", marginBottom: 6 }}>Historial</div>
      {lista.length === 0 && (
        <div style={{ color: "var(--dim)" }}>Todavía no hay mejoras.</div>
      )}
      {lista.map((m) => (
        <div key={m.improvement_id}
             style={{ padding: "4px 0", borderTop: "1px solid rgba(255,255,255,0.06)" }}>
          <span style={{ color: "#cfe0e4" }}>{m.title}</span>
          <span style={{ color: "var(--dim)" }}>
            {" "}· {ETAPAS[m.stage] ?? m.stage}
            {" "}· {m.origin === "naoko" ? "Naoko" : "tú"}
          </span>
        </div>
      ))}
    </div>
  );
}
