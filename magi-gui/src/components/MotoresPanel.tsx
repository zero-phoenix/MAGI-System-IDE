/**
 * Estado de Motores IA (extraido de App.tsx por el trinquete de líneas,
 * 4-sep-2026).
 *
 * La tabla con «DeepSeek / LLaMA 3» y fallbacks escritos a mano era
 * DECORATIVA: el reparto real llega por `sys.config` y las latencias
 * medidas por la telemetría. Mostrar modelos inventados junto a datos
 * vivos es la clase de documento-que-miente que este proyecto caza.
 */

export function MotoresPanel({ telemetry }: {
  telemetry: any[];
}) {
  return (
<div style={{ flex: 1, background: "#050a0b", border: "1px solid var(--dim)", padding: "20px", color: "#cfe0e4", overflowY: "auto", userSelect: "text", WebkitUserSelect: "text" }}>
                  <h2 style={{ color: "var(--acc)", marginBottom: "15px" }}>Estado de Inteligencias Artificiales</h2>
                  <p style={{ color: "var(--dim)", marginBottom: "20px" }}>Resumen de la arquitectura del Enjambre y modelos utilizados por MAGI a través del G4F Auto-Router.</p>
                  
                  <table style={{ width: "100%", borderCollapse: "collapse", marginBottom: "20px", fontSize: "12px" }}>
                    <thead>
                      <tr style={{ background: "var(--gr)", textAlign: "left" }}>
                        <th style={{ padding: "8px", border: "1px solid var(--dim)" }}>IA (Rol)</th>
                        <th style={{ padding: "8px", border: "1px solid var(--dim)" }}>Modelo Principal</th>
                        <th style={{ padding: "8px", border: "1px solid var(--dim)" }}>Fallback (Evasión anti-429)</th>
                        <th style={{ padding: "8px", border: "1px solid var(--dim)" }}>Estado G4F</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr>
                        <td style={{ padding: "8px", border: "1px solid var(--dim)", color: "var(--var)", fontWeight: "bold" }}>🧠 MELCHIOR (Arquitecto)</td>
                        <td style={{ padding: "8px", border: "1px solid var(--dim)" }}>DeepSeek / LLaMA 3</td>
                        <td style={{ padding: "8px", border: "1px solid var(--dim)" }}>gpt-4o</td>
                        <td style={{ padding: "8px", border: "1px solid var(--dim)", color: "var(--ok)" }}>🟢 OK</td>
                      </tr>
                      <tr>
                        <td style={{ padding: "8px", border: "1px solid var(--dim)", color: "var(--acc)", fontWeight: "bold" }}>🛡️ BALTHASAR (Crítico)</td>
                        <td style={{ padding: "8px", border: "1px solid var(--dim)" }}>Claude 3.5 Sonnet</td>
                        <td style={{ padding: "8px", border: "1px solid var(--dim)" }}>gpt-4o</td>
                        <td style={{ padding: "8px", border: "1px solid var(--dim)", color: "var(--ok)" }}>🟢 OK</td>
                      </tr>
                      <tr>
                        <td style={{ padding: "8px", border: "1px solid var(--dim)", color: "var(--fn)", fontWeight: "bold" }}>⚖️ CASPER (Árbitro)</td>
                        <td style={{ padding: "8px", border: "1px solid var(--dim)" }}>Qwen 2.5</td>
                        <td style={{ padding: "8px", border: "1px solid var(--dim)" }}>gpt-4o</td>
                        <td style={{ padding: "8px", border: "1px solid var(--dim)", color: "var(--ok)" }}>🟢 OK</td>
                      </tr>
                    </tbody>
                  </table>
                  
                  <p style={{ color: "#8fa4aa", fontSize: "11px", fontStyle: "italic", marginBottom: "30px" }}>
                    * El enrutador intercepta caídas de los modelos principales y redirige hacia el ecosistema GPT-4o / Qwen. No se usan APIs locales. En caso extremo, se usa un mecanismo automatizado de detención segura.
                  </p>

                  <h2 style={{ color: "var(--acc)", marginBottom: "20px" }}>Dashboard de Telemetría (Empírica)</h2>
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: "10px" }}>
                    {telemetry && telemetry.length > 0 ? telemetry.map((prov, i) => (
                      <div key={i} style={{
                        background: "rgba(10, 20, 25, 0.7)", 
                        border: "1px solid var(--dim)",
                        borderRadius: "6px",
                        padding: "10px",
                        display: "flex",
                        flexDirection: "column",
                        gap: "5px",
                        boxShadow: "0 4px 6px rgba(0,0,0,0.3)"
                      }}>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                          <h3 style={{ margin: 0, color: "var(--node)", fontSize: "14px" }}>{prov.provider}</h3>
                          <span style={{ fontSize: "10px", padding: "2px 6px", borderRadius: "10px", background: prov.success_count > 0 ? "rgba(0,255,100,0.1)" : "rgba(255,50,50,0.1)", color: prov.success_count > 0 ? "#0f0" : "#f55" }}>
                            {prov.success_count > 0 ? "ALIVE" : "DEAD"}
                          </span>
                        </div>
                        <div style={{ fontSize: "11px", color: "var(--dim)" }}>Latencia media: <span style={{ color: "#cfe0e4" }}>{prov.avg_latency_ms.toFixed(0)} ms</span></div>
                        <div style={{ fontSize: "11px", color: "var(--dim)" }}>Éxitos / Fallos: <span style={{ color: "#cfe0e4" }}>{prov.success_count} / {prov.failure_count}</span></div>
                      </div>
                    )) : <span style={{ color: "var(--dim)", fontSize: "12px" }}>Esperando datos de la red G4F...</span>}
                  </div>
               </div>
  );
}

export default MotoresPanel;
