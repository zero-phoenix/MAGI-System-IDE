/**
 * Panel de sistema: salud, banco y auto-mejora (§3.4, §3.5, §7.3).
 *
 * POR QUÉ ESTE PANEL EXISTE
 * =========================
 * Una auditoría de qué handlers RPC tienen quien los llame desde la interfaz
 * encontró TRES capacidades completas y sin forma de invocarlas:
 *
 *   obs.metrics         panel de salud (§3.4)
 *   eval.run            banco de evaluación (§3.5)
 *   naoko.self_improve  auto-mejora medible (§3.5)
 *
 * El motor estaba construido, probado y enganchado al bus. Faltaba el botón.
 * Es el mismo patrón que ya apareció con la contabilidad de tokens y con la
 * cancelación: la pieza hecha y el cable que no está.
 *
 * Y la auto-mejora es justo lo que se pidió al encargar todo esto — «que haga
 * perfectible al sistema» — así que tenerla inalcanzable era el peor sitio
 * posible para dejar un cable suelto.
 */
import { useState } from "react";
import { Diagnosis, HealthSnapshot, diagnose, formatMs, slowest } from "../lib/health";

const COLOR_SEVERIDAD: Record<Diagnosis["severity"], string> = {
  ok: "#7dfaa8", aviso: "#ffcc66", grave: "#ff9a9a",
};

interface Props {
  fetchHealth: () => Promise<HealthSnapshot>;
  runBenchmark: () => Promise<any>;
  runSelfImprovement: (h: string) => Promise<any>;
}

export default function SystemPanel({ fetchHealth, runBenchmark, runSelfImprovement }: Props) {
  const [salud, setSalud] = useState<HealthSnapshot | null>(null);
  const [banco, setBanco] = useState<any>(null);
  const [mejora, setMejora] = useState<any>(null);
  const [hipotesis, setHipotesis] = useState("");
  const [ocupado, setOcupado] = useState("");
  const [error, setError] = useState("");

  const correr = async (etiqueta: string, fn: () => Promise<any>,
                        guardar: (v: any) => void) => {
    setOcupado(etiqueta); setError("");
    try {
      guardar(await fn());
    } catch (e: any) {
      // Un panel que se queda en blanco cuando algo falla es peor que uno que
      // dice qué falló: el usuario no sabe si esperar o reintentar.
      setError(e?.message || String(e));
    } finally {
      setOcupado("");
    }
  };

  const diag = salud ? diagnose(salud) : [];
  const lento = salud ? slowest(salud) : null;
  const boton: React.CSSProperties = {
    cursor: "pointer", padding: "5px 12px", fontSize: 12,
    background: "rgba(0,200,255,0.12)", color: "var(--acc)",
    border: "1px solid var(--dim)", borderRadius: 3,
  };

  return (
    <div style={{ padding: 14, overflowY: "auto", height: "100%", fontSize: 12 }}>
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 14 }}>
        <button style={boton} disabled={!!ocupado}
                onClick={() => correr("salud", fetchHealth, setSalud)}>
          {ocupado === "salud" ? "midiendo…" : "Medir salud"}
        </button>
        <button style={boton} disabled={!!ocupado}
                onClick={() => correr("banco", runBenchmark, setBanco)}>
          {ocupado === "banco" ? "ejecutando el banco…" : "Ejecutar banco de evaluación"}
        </button>
      </div>

      {error && (
        <div style={{ color: "#ff9a9a", marginBottom: 12 }}>No se pudo: {error}</div>
      )}

      {/* ---------------------------------------------------- §3.4 salud */}
      {salud && (
        <section style={{ marginBottom: 20 }}>
          <h4 style={{ color: "var(--acc)", margin: "0 0 6px" }}>
            Salud del sistema
          </h4>
          {diag.map((d, i) => (
            <div key={i} style={{ color: COLOR_SEVERIDAD[d.severity], marginBottom: 3 }}>
              {d.severity === "ok" ? "·" : "⚠"} {d.text}
            </div>
          ))}

          {lento && (
            <div style={{ color: "var(--dim)", marginTop: 8 }}>
              Más lento: <b>{lento[0]}</b> — p50 {formatMs(lento[1].p50)},
              p95 {formatMs(lento[1].p95)}, {lento[1].total} llamadas.
              <div style={{ marginTop: 3 }}>
                Se ordena por p95 y no por la media: un proveedor que responde
                en 2s nueve veces y en 40s la décima tiene buena media y una
                décima llamada insufrible.
              </div>
            </div>
          )}
        </section>
      )}

      {/* ---------------------------------------------------- §3.5 banco */}
      {banco && (
        <section style={{ marginBottom: 20 }}>
          <h4 style={{ color: "var(--acc)", margin: "0 0 6px" }}>
            Banco de evaluación
          </h4>
          <div>
            {banco.passed}/{banco.total} tareas superadas
            {typeof banco.score === "number" &&
              ` · ${Math.round(banco.score * 100)}%`}
          </div>
          <div style={{ color: "var(--dim)", marginTop: 4 }}>
            Las tareas se corrigen con código, no pidiéndole a un modelo que se
            puntúe a sí mismo.
          </div>
        </section>
      )}

      {/* ----------------------------------------------- §3.5 auto-mejora */}
      <section>
        <h4 style={{ color: "var(--acc)", margin: "0 0 6px" }}>
          Auto-mejora medible
        </h4>
        <div style={{ color: "var(--dim)", marginBottom: 6 }}>
          Propón un cambio del sistema. Se mide el banco antes y después y solo
          se conserva si mejora <b>sin romper nada</b>. No se dispara sola:
          cambiar el sistema gasta cuota y la decisión es tuya.
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <input
            value={hipotesis}
            onChange={(e) => setHipotesis(e.target.value)}
            placeholder="p. ej.: subir la temperatura de Balthasar a 0.5 mejora la crítica"
            style={{ flex: 1, padding: "5px 8px", fontSize: 12,
                     background: "#0a1013", color: "#cfe0e4",
                     border: "1px solid var(--dim)", borderRadius: 3 }}
          />
          <button style={boton}
                  disabled={!!ocupado || !hipotesis.trim()}
                  onClick={() => correr(
                    "mejora", () => runSelfImprovement(hipotesis.trim()), setMejora)}>
            {ocupado === "mejora" ? "midiendo…" : "Probar"}
          </button>
        </div>

        {mejora && (
          <pre style={{ marginTop: 10, whiteSpace: "pre-wrap", color: "#a8bcc1" }}>
            {typeof mejora === "string" ? mejora : JSON.stringify(mejora, null, 1)}
          </pre>
        )}
      </section>
    </div>
  );
}
