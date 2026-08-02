import { useState, useRef, useEffect } from "react";
import "./App.css";
import { useMagiStore } from "./store";
import { useMagiSocket } from "./useMagiSocket";

function App() {
  const [activeTab, setActiveTab] = useState("Vista previa");
  const [topSection, setTopSection] = useState("Conversación");
  const [selectedProject, setSelectedProject] = useState("");
  const [inputVal, setInputVal] = useState("");
  
  const { connected, messages, terminalOutput, sysCommand, projects, metrics, telemetry } = useMagiStore();
  const { sendCommand, fetchTelemetry } = useMagiSocket(20128);
  
  const terminalEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll terminal
  useEffect(() => {
    if (activeTab === "Terminal" && terminalEndRef.current) {
      terminalEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
    if (activeTab === "Telemetría del Enjambre") {
      fetchTelemetry();
    }
  }, [terminalOutput, activeTab, fetchTelemetry]);

  const handleExecute = () => {
    if(!inputVal.trim()) return;
    sysCommand(inputVal);
    sendCommand(inputVal);
    setInputVal("");
  };

  const handleStopAll = () => {
    sysCommand("EMERGENCY_STOP");
    sendCommand("KILL_ALL_PROCESSES");
  };

  return (
    <>
      <div className="tt">
        <b>MAGI SYSTEM IDE</b> — ejecutable de escritorio. Interfaz horizontal fija.
      </div>

      <div className="bar">
        <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
          <span className="brand">MAGI SYSTEM IDE {connected ? "[EN LÍNEA]" : "[DESCONECTADO]"}</span>
          <span className="secs">
            <button 
              className={topSection === "Conversación" ? "on" : ""} 
              onClick={() => setTopSection("Conversación")}
            >Conversación</button>
            <button 
              className={topSection === "Proyectos" ? "on" : ""}
              onClick={() => setTopSection("Proyectos")}
            >Proyectos</button>
          </span>
        </div>
        <div className="q">
          <span>prov-a <b>{metrics?.prov_a || "0/0"}</b></span>
          <span>prov-b <b>{metrics?.prov_b || "offline"}</b></span>
          <span>prov-c <b>{metrics?.prov_c || "offline"}</b></span>
          <span>⚙</span>
          <span className="stop" style={{cursor: "pointer"}} onClick={handleStopAll}>PARAR TODO</span>
        </div>
      </div>

      <div className="app">
        {/* CARRIL */}
        <div className="col rail">
          <input
            style={{ width: "100%", background: "#050a0b", border: "1px solid var(--gr)", color: "#cfe0e4", padding: "4px 6px", font: "inherit", fontSize: "11px", marginBottom: "8px" }}
            placeholder="Buscar…"
          />
          <div className="sc">
            <div className="lbl">PROYECTOS</div>
            {projects && projects.length > 0 ? projects.map((item, idx) => (
              <div 
                key={idx} 
                className={`th ${selectedProject === item.name ? 'on' : ''}`}
                onClick={() => setSelectedProject(item.name)}
              >
                {item.name}
                <small>{item.desc}</small>
              </div>
            )) : (
              <div style={{ padding: "10px", fontSize: "10px", color: "#5f7378" }}>
                Sin proyectos activos.
              </div>
            )}
          </div>
          <div className="cfg" onClick={() => setActiveTab("Terminal")}>
            ⚙ Terminal del Sistema
            <br />
            <span style={{ fontSize: "9px", fontWeight: 400 }}>Acceso Irrestricto</span>
          </div>
        </div>

        {/* CONVERSACIÓN O PROYECTOS */}
        <div className="col">
          {topSection === "Conversación" ? (
            <>
              <div className="tri">
                <div className="nd b">
                  <div className="fx">el que busca fallos</div>
                  <div className="nm">BALTHASAR · 2</div>
                  <div className="md">prov-c · nube · activo</div>
                </div>
                <div className="cn k1"></div>
                <div className="cn k2"></div>
                <div className="rh">
                  <div className="lg">MAGI</div>
                  <div className="r">RONDA 3 / 3–7 · cuota ok</div>
                </div>
                <div className="nd c">
                  <div className="fx">el que decide</div>
                  <div className="nm">CASPER · 3</div>
                  <div className="md">prov-a · nube · analizando</div>
                </div>
                <div className="nd m1">
                  <div className="fx">el que propone</div>
                  <div className="nm">MELCHIOR · 1</div>
                  <div className="md">prov-b · agotado · espera</div>
                </div>
              </div>

              <div className="conv">
                <div className="you">
                  <div className="w">SISTEMA</div>
                  Conectado a la Pasarela de Inferencia. Esperando flujos del Enjambre...
                </div>

                {messages.map((msg, i) => (
                  <div key={i} className={`card ${msg.role === 'propone' ? 'prop' : (msg.role === 'critica' ? 'crit' : 'arb')}`}>
                    <div className="ch">
                      <span style={{ display: "flex", gap: "6px", alignItems: "center" }}>
                        <span className="dot" style={{ background: msg.role === 'propone' ? 'var(--node)' : (msg.role === 'critica' ? 'var(--dang)' : 'var(--warn)') }}></span>
                        <b style={{ color: msg.role === 'propone' ? 'var(--node)' : (msg.role === 'critica' ? 'var(--dang)' : 'var(--warn)') }}>{msg.agent}</b>
                        <span style={{ color: "#6d8288" }}>{msg.role}</span>
                      </span>
                    </div>
                    <div className="mid">
                      <b>{msg.provider}</b> · modelo enjambre
                    </div>
                    <div className="pl">«{msg.content}»</div>
                    <div className="sec">
                      Cambios detectados <span style={{ color: "#5f7378" }}>{msg.changes} cambios</span>
                    </div>
                    <div className="ft">{msg.stats}</div>
                  </div>
                ))}
              </div>

              <div className="comp">
                <div className="cr">
                  <button className="pre">SYS_EXEC ▾</button>
                  <textarea
                    className="pf"
                    rows={1}
                    placeholder="Escribe tu instrucción o comando (acceso total)…"
                    value={inputVal}
                    onChange={(e) => setInputVal(e.target.value)}
                    onKeyDown={(e) => {
                      if(e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        handleExecute();
                      }
                    }}
                  ></textarea>
                  <button className="bt go" onClick={handleExecute}>Ejecutar ▸</button>
                </div>
                <div className="att">
                  <span className="chip" style={{ borderStyle: "dashed", color: "#6d8288" }}>
                    arrastra evidencia / logs aquí
                  </span>
                </div>
              </div>
            </>
          ) : (
            <div style={{ padding: "20px", display: "flex", flexDirection: "column", gap: "10px" }}>
              <h2 style={{ color: "var(--acc)" }}>Gestor de Proyectos</h2>
              <div style={{ border: "1px solid var(--gr)", padding: "10px", background: "#050809" }}>
                Activo: <b style={{ color: "var(--node)" }}>{selectedProject || "Ninguno"}</b>
              </div>
              <p style={{ color: "#8fa4aa" }}>El gestor de versiones se sincronizará con GitHub automáticamente desde esta pestaña.</p>
            </div>
          )}
        </div>

        {/* LIENZO */}
        <div className="col canvas">
          <div className="tabs">
            {["Plan", "Código", "Vista previa", "Terminal", "Gráfico HDC", "Telemetría del Enjambre"].map((tab) => (
              <div
                key={tab}
                className={`tab ${activeTab === tab ? "on" : ""}`}
                onClick={() => setActiveTab(tab)}
              >
                {tab}
              </div>
            ))}
          </div>
          <div className="cbody" style={{ display: "flex", flexDirection: "column", height: "100%" }}>
            
            {activeTab === "Vista previa" && (
              <>
                <div className="pv" style={{ border: "1px dashed var(--dim)", display: "flex", alignItems: "center", justifyContent: "center", color: "var(--dim)" }}>
                  [Vista previa vacía]
                </div>
              </>
            )}
            
            {activeTab === "Terminal" && (
              <div style={{ flex: 1, background: "#000", border: "1px solid var(--dim)", padding: "10px", fontFamily: "monospace", color: "#0f0", whiteSpace: "pre-wrap", overflowY: "auto" }}>
                {terminalOutput}
                <div ref={terminalEndRef} />
              </div>
            )}
            
            {activeTab === "Código" && (
               <div style={{ flex: 1, background: "#1e1e1e", border: "1px solid var(--dim)", padding: "10px", fontFamily: "monospace", color: "#d4d4d4", overflowY: "auto", display: "flex", alignItems: "center", justifyContent: "center" }}>
                  <span style={{ color: "var(--dim)" }}>[Esperando sincronización de árbol de archivos]</span>
               </div>
            )}

            {activeTab === "Plan" && (
               <div style={{ flex: 1, padding: "10px", color: "#cfe0e4", overflowY: "auto", border: "1px dashed var(--dim)", display: "flex", alignItems: "center", justifyContent: "center" }}>
                  <span style={{ color: "var(--dim)" }}>[Sin plan de ejecución activo]</span>
               </div>
            )}

            {activeTab === "Gráfico HDC" && (
               <div style={{ flex: 1, padding: "10px", border: "1px dashed var(--dim)", display: "flex", alignItems: "center", justifyContent: "center", color: "var(--node)" }}>
                  [Renderizador WebGL de Memoria Hiperdimensional - Esperando Datos]
               </div>
            )}

            {activeTab === "Telemetría del Enjambre" && (
              <div style={{ flex: 1, padding: "20px", overflowY: "auto", background: "#050a0b", color: "#cfe0e4" }}>
                <h2 style={{ color: "var(--acc)", marginBottom: "20px" }}>Dashboard de Telemetría (Empírica)</h2>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(250px, 1fr))", gap: "15px" }}>
                  {telemetry && telemetry.length > 0 ? telemetry.map((prov, i) => (
                    <div key={i} style={{
                      background: "rgba(10, 20, 25, 0.7)", 
                      border: "1px solid var(--dim)",
                      borderRadius: "6px",
                      padding: "15px",
                      display: "flex",
                      flexDirection: "column",
                      gap: "10px",
                      boxShadow: "0 4px 6px rgba(0,0,0,0.3)",
                      backdropFilter: "blur(5px)"
                    }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <h3 style={{ margin: 0, color: "var(--node)", fontSize: "16px" }}>{prov.provider}</h3>
                        <span style={{ fontSize: "12px", padding: "2px 6px", borderRadius: "10px", background: prov.success_count > 0 ? "rgba(0,255,100,0.1)" : "rgba(255,50,50,0.1)", color: prov.success_count > 0 ? "#0f0" : "#f55" }}>
                          {prov.success_count > 0 ? "ALIVE" : "DEAD"}
                        </span>
                      </div>
                      
                      <div style={{ fontSize: "12px", display: "flex", flexDirection: "column", gap: "4px" }}>
                        <div style={{ display: "flex", justifyContent: "space-between" }}>
                          <span style={{ color: "var(--dim)" }}>Aciertos:</span>
                          <b style={{ color: "#0f0" }}>{prov.success_count}</b>
                        </div>
                        <div style={{ display: "flex", justifyContent: "space-between" }}>
                          <span style={{ color: "var(--dim)" }}>Fallos:</span>
                          <b style={{ color: "#f55" }}>{prov.failure_count}</b>
                        </div>
                        <div style={{ display: "flex", justifyContent: "space-between" }}>
                          <span style={{ color: "var(--dim)" }}>Latencia:</span>
                          <b>{prov.avg_latency_ms.toFixed(1)} ms</b>
                        </div>
                      </div>

                      <div style={{ marginTop: "10px", paddingTop: "10px", borderTop: "1px solid rgba(255,255,255,0.05)", fontSize: "12px" }}>
                        <div style={{ color: "var(--acc)", fontWeight: "bold", marginBottom: "5px" }}>Inteligencia y Complejidad</div>
                        <div style={{ display: "flex", justifyContent: "space-between" }}>
                          <span style={{ color: "var(--dim)" }}>Extensión de Lógica:</span>
                          <b>{prov.avg_word_count.toFixed(0)} palabras</b>
                        </div>
                        <div style={{ display: "flex", justifyContent: "space-between" }}>
                          <span style={{ color: "var(--dim)" }}>Densidad de Código:</span>
                          <b>{(prov.code_density_ratio * 100).toFixed(0)}%</b>
                        </div>
                        <div style={{ display: "flex", justifyContent: "space-between", marginTop: "5px" }}>
                          <span style={{ color: "var(--dim)" }}>Especialidad:</span>
                          <b style={{ color: "var(--warn)" }}>{prov.specialization}</b>
                        </div>
                      </div>
                    </div>
                  )) : (
                    <div style={{ color: "var(--dim)" }}>No hay datos de telemetría disponibles. El enjambre necesita procesar comandos reales primero.</div>
                  )}
                </div>
              </div>
            )}

          </div>
        </div>
      </div>

      <div className="foot">
        <div>
          ejecutable de escritorio · <b>MAGI SYSTEM IDE v8.0</b> · proyecto en carpeta
        </div>
        <div>acceso root habilitado</div>
      </div>
    </>
  );
}

export default App;
