/**
 * Panel de coste: tokens y tiempo por tarea y por agente (§7.3).
 *
 * Antes no existía, y no por falta de sitio en la interfaz: no había datos.
 * `agent_loop.py` contaba los tokens, `AgentTurn` los traía y `agents.py` los
 * metía en una cadena de log con `turn.summary()`. `TaskStore.record_usage()`
 * existía y no lo llamaba nadie, así que la tabla `token_ledger` llevaba
 * vacía desde que se creó.
 *
 * Lo que hace útil este panel no es la tabla: son las observaciones de
 * arriba. La más importante es la que detecta que los tres nodos corrieron
 * sobre la misma familia — el fallo original de v5.0.28, que convierte el
 * debate popperiano en un modelo hablando solo.
 */
import { useMagiStore } from "../store";
import { formatSeconds, formatTokens, summarize } from "../lib/cost";

export default function CostPanel({ taskId }: { taskId?: string }) {
  const usage = useMagiStore((s) => s.usage);
  const s = summarize(usage, taskId);

  if (!s.calls) {
    return (
      <div style={{ padding: 16, color: "var(--dim)", fontSize: 13 }}>
        Todavía no hay gasto registrado en esta sesión. Aparece en cuanto un
        nodo del enjambre completa un turno.
      </div>
    );
  }

  const celda: React.CSSProperties = { padding: "4px 10px", textAlign: "right" };

  return (
    <div style={{ padding: 12, overflowY: "auto", height: "100%", fontSize: 12 }}>
      <div style={{ display: "flex", gap: 22, flexWrap: "wrap", marginBottom: 12 }}>
        {[
          ["llamadas", String(s.calls)],
          ["tokens", formatTokens(s.tokens)],
          ["entrada / salida", `${formatTokens(s.tokensIn)} / ${formatTokens(s.tokensOut)}`],
          ["tiempo de modelo", formatSeconds(s.seconds)],
          ["herramientas", String(s.toolCalls)],
        ].map(([k, v]) => (
          <div key={k}>
            <div style={{ color: "var(--dim)", fontSize: 10, textTransform: "uppercase" }}>{k}</div>
            <div style={{ color: "var(--acc)", fontSize: 18 }}>{v}</div>
          </div>
        ))}
      </div>

      {s.notes.length > 0 && (
        <div style={{ marginBottom: 12, padding: "8px 10px",
                      background: "rgba(255,170,0,0.10)",
                      border: "1px solid rgba(255,170,0,0.3)", borderRadius: 3 }}>
          {s.notes.map((n, i) => (
            <div key={i} style={{ color: "#ffcc66", marginBottom: 3 }}>⚠ {n}</div>
          ))}
        </div>
      )}

      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr style={{ color: "var(--dim)", textAlign: "right", fontSize: 10 }}>
            <th style={{ ...celda, textAlign: "left" }}>agente</th>
            <th style={{ ...celda, textAlign: "left" }}>familia</th>
            <th style={celda}>llamadas</th>
            <th style={celda}>tokens</th>
            <th style={celda}>cuota</th>
            <th style={celda}>s/llamada</th>
            <th style={celda}>herram.</th>
          </tr>
        </thead>
        <tbody>
          {s.byAgent.map((a) => (
            <tr key={`${a.agent}-${a.family}`}
                style={{ borderTop: "1px solid rgba(255,255,255,0.06)" }}>
              <td style={{ ...celda, textAlign: "left", color: "var(--node)" }}>{a.agent}</td>
              <td style={{ ...celda, textAlign: "left", color: "var(--dim)" }}>{a.family || "—"}</td>
              <td style={celda}>{a.calls}</td>
              <td style={celda}>{formatTokens(a.tokens)}</td>
              <td style={celda}>{Math.round(a.share * 100)}%</td>
              <td style={{ ...celda, color: a.avgSeconds > 25 ? "#ff9a9a" : undefined }}>
                {a.avgSeconds.toFixed(1)}
              </td>
              <td style={celda}>{a.toolCalls}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <div style={{ marginTop: 10, color: "var(--dim)", fontSize: 11 }}>
        El tiempo es de modelo, no de reloj: los turnos del enjambre corren en
        paralelo, así que la suma supera lo que tardó la tarea.
      </div>
    </div>
  );
}
