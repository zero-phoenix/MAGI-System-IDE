import { useState, useRef, useEffect } from "react";
import "./App.css";
import { useMagiStore } from "./store";
import { useMagiSocket } from "./useMagiSocket";
import { useMagiAudio } from "./useMagiAudio";
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

function App() {
  const [activeTab, setActiveTab] = useState("Vista previa");
  const [selectedProject, setSelectedProject] = useState("");
  const [inputVal, setInputVal] = useState("");
  const [gitUrl, setGitUrl] = useState("");
  
  const { connected, messages, addMessage, terminalOutput, sysCommand, projects, metrics, telemetry } = useMagiStore();
  const { sendCommand, fetchTelemetry, sendGitClone } = useMagiSocket(20128);
  const { playCalcBeep, playDecisionClack } = useMagiAudio();
  
  const terminalEndRef = useRef<HTMLDivElement>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll terminal y conversacion
  useEffect(() => {
    if (activeTab === "Terminal" && terminalEndRef.current) {
      terminalEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
    if (activeTab === "Telemetría del Enjambre") {
      fetchTelemetry();
    }
  }, [terminalOutput, messages, activeTab, fetchTelemetry]);

  const handleExecute = () => {
    if(!inputVal.trim()) return;
    sysCommand(inputVal);
    sendCommand(inputVal);
    
    // Echo in chat
    addMessage({
      id: Date.now().toString(),
      agent: "Usuario",
      role: "comando",
      provider: "Local",
      content: inputVal,
      changes: 0,
      stats: ""
    });
    
    setInputVal("");
  };

  const handleGitPush = () => {
    if(!gitUrl.trim()) return;
    setActiveTab("Terminal");
    // Send RPC for git push
    sysCommand(`GIT_PUSH_TO_GITHUB ${gitUrl}`);
    sendCommand(`GIT_PUSH_TO_GITHUB ${gitUrl}`);
    setGitUrl("");
  };

  const handleGitClone = () => {
    if(!gitUrl.trim()) return;
    setActiveTab("Terminal");
    sendGitClone(gitUrl);
    setGitUrl("");
  };

  const handleStopAll = () => {
    sysCommand("EMERGENCY_STOP");
    sendCommand("KILL_ALL_PROCESSES");
  };

  const getAgentData = (agentName: string, defaultProv: string) => {
    const msgs = messages.filter(m => m.agent === agentName);
    const lastMsg = msgs.length > 0 ? msgs[msgs.length - 1] : null;
    const provider = lastMsg?.provider || defaultProv;
    const tel = telemetry?.find(t => t.provider === provider);
    const latency = tel ? `${tel.avg_latency_ms.toFixed(0)}ms` : '---';
    return { provider, latency };
  };

  const balthasarData = getAgentData("BALTHASAR", "prov-c");
  const casperData = getAgentData("CASPER", "prov-a");
  const melchiorData = getAgentData("MELCHIOR", "prov-b");
  
  const casperMsgs = messages.filter(m => m.agent === 'CASPER');
  const lastCasper = casperMsgs[casperMsgs.length - 1];
  const isApproved = lastCasper?.stats?.includes("APPROVED");
  const isRejected = lastCasper?.stats?.includes("REJECTED");
  
  const lastMsg = messages.length > 0 ? messages[messages.length - 1] : null;
  const isCasperThinking = lastMsg?.agent === "BALTHASAR";

  // Efectos de Sonido
  useEffect(() => {
    if (isCasperThinking) {
      playCalcBeep();
    } else if (lastMsg?.agent === "CASPER") {
      playDecisionClack();
    }
  }, [messages.length]);
  
  const casperColor = isApproved ? "#0f0" : (isRejected ? "#f55" : "");
  const melchiorColor = isApproved ? "#0f0" : "";
  const balthasarColor = isRejected ? "#f55" : (isApproved ? "#0f0" : "");
  
  // Filter Projects
  const filteredProjects = projects ? projects.filter(p => !p.name.includes('__pycache__') && p.name !== 'agentic-awesome-skills') : [];

  return (
    <>
      <div className="tt">
        <b>MAGI SYSTEM IDE</b> — ejecutable de escritorio. Interfaz horizontal fija.
      </div>

      <div className="bar">
        <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
          <span className="brand">MAGI SYSTEM IDE {connected ? "[EN LÍNEA]" : "[DESCONECTADO]"}</span>
        </div>
        <div className="q">
          <span>prov-a <b>{metrics?.prov_a || "0/0"}</b></span>
          <span>prov-b <b>{metrics?.prov_b || "offline"}</b></span>
          <span>prov-b <b>{metrics?.prov_b || "offline"}</b></span>
          <span>prov-c <b>{metrics?.prov_c || "offline"}</b></span>
          <span style={{cursor: "pointer"}} onClick={() => setActiveTab("Configuración")}>⚙</span>
          <span className="stop" style={{cursor: "pointer"}} onClick={handleStopAll}>PARAR TODO</span>
        </div>
      </div>

      {/* MASTER LAYOUT: 3 COLUMNAS */}
      <div className="app" style={{ display: "flex", width: "100%", overflow: "hidden" }}>
        
        {/* COLUMNA IZQUIERDA: SIDEBAR / PROYECTOS */}
        <div className="col rail" style={{ width: "260px", minWidth: "260px" }}>
          <input
            style={{ width: "100%", background: "#050a0b", border: "1px solid var(--gr)", color: "#cfe0e4", padding: "4px 6px", font: "inherit", fontSize: "11px", marginBottom: "8px" }}
            placeholder="Buscar proyectos…"
          />
          <div className="sc">
            <div className="lbl">REPOSITORIOS (scratch/)</div>
            {filteredProjects.length > 0 ? filteredProjects.map((item, idx) => (
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
                Sin proyectos locales válidos.
              </div>
            )}
          </div>

          <div style={{ marginTop: "15px", borderTop: "1px solid var(--gr)", paddingTop: "10px" }}>
             <div className="lbl" style={{ marginBottom: "5px" }}>CLONAR / SUBIR A GITHUB</div>
             <input 
                placeholder="https://github.com/..."
                value={gitUrl}
                onChange={(e) => setGitUrl(e.target.value)}
                style={{ width: "100%", background: "#050a0b", border: "1px solid var(--gr)", color: "#cfe0e4", padding: "4px", fontSize: "10px", marginBottom: "5px" }}
             />
             <div style={{ display: "flex", gap: "5px" }}>
               <button className="bt go" style={{ flex: 1, padding: "2px 0" }} onClick={handleGitClone}>Clone ↓</button>
               <button className="bt go" style={{ flex: 1, padding: "2px 0" }} onClick={handleGitPush}>Push ↑</button>
             </div>
          </div>
        </div>

        {/* COLUMNA CENTRAL: ENJAMBRE Y CONVERSACIÓN */}
        <div className="col" style={{ flex: 1, minWidth: "400px", borderRight: "1px solid var(--gr)", display: "flex", flexDirection: "column" }}>
          
          <div style={{ background: "#050809", padding: "5px 10px", borderBottom: "1px solid var(--gr)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ fontSize: "11px", color: "var(--dim)" }}>
              Proyecto Activo: <b style={{ color: "var(--node)" }}>{selectedProject || "[Global]"}</b>
            </span>
          </div>

          <div className="tri" style={{ paddingBottom: "10px" }}>
            <div className="nd b" style={{ backgroundColor: balthasarColor || undefined }}>
              <div className="fx">el que busca fallos</div>
              <div className="nm">BALTHASAR · 2</div>
              <div className="md" style={{ color: balthasarColor ? '#000' : 'var(--ink)' }}>{balthasarData.provider} · {balthasarData.latency}</div>
            </div>
            <div className="cn k1"></div>
            <div className="cn k2"></div>
            <div className="rh">
              <div className="lg">MAGI</div>
              <div className="r">ENJAMBRE ACTIVO</div>
            </div>
            <div className={`nd c ${isCasperThinking ? 'blinking' : ''}`} style={{ backgroundColor: casperColor || undefined }}>
              <div className="fx">el que decide</div>
              <div className="nm">CASPER · 3</div>
              <div className="md" style={{ color: casperColor ? '#000' : 'var(--ink)' }}>{casperData.provider} · {casperData.latency}</div>
            </div>
            <div className="nd m1" style={{ backgroundColor: melchiorColor || undefined }}>
              <div className="fx">el que propone</div>
              <div className="nm">MELCHIOR · 1</div>
              <div className="md" style={{ color: melchiorColor ? '#000' : 'var(--ink)' }}>{melchiorData.provider} · {melchiorData.latency}</div>
            </div>
          </div>

          <div className="conv" style={{ flex: 1 }}>
            <div className="you">
              <div className="w">SISTEMA</div>
              {selectedProject ? `Contexto anclado a ${selectedProject}. Esperando flujos del Enjambre...` : "Conectado a la Pasarela Global. Esperando flujos del Enjambre..."}
            </div>

            {messages.map((msg, i) => (
              <div key={i} className={`card ${msg.role === 'propone' ? 'prop' : (msg.role === 'critica' ? 'crit' : 'arb')}`} style={{ userSelect: "text", WebkitUserSelect: "text" }}>
                <div className="ch">
                  <span style={{ display: "flex", gap: "6px", alignItems: "center" }}>
                    <span className="dot" style={{ background: msg.role === 'comando' ? '#fff' : (msg.role === 'propone' ? 'var(--node)' : (msg.role === 'critica' ? 'var(--dang)' : 'var(--warn)')) }}></span>
                    <b style={{ color: msg.role === 'comando' ? '#fff' : (msg.role === 'propone' ? 'var(--node)' : (msg.role === 'critica' ? 'var(--dang)' : 'var(--warn)')) }}>{msg.agent}</b>
                    <span style={{ color: "#6d8288" }}>{msg.role}</span>
                  </span>
                </div>
                <div className="mid" style={{ display: "flex", justifyContent: "space-between" }}>
                  <span><b>{msg.provider}</b> · modelo enjambre</span>
                  {telemetry?.find(t => t.provider === msg.provider) && (
                    <span style={{ color: "var(--ok)", opacity: 0.8 }}>
                      {telemetry.find(t => t.provider === msg.provider).avg_latency_ms.toFixed(0)}ms
                    </span>
                  )}
                </div>
                <div className="pl markdown-body">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {msg.content}
                  </ReactMarkdown>
                </div>
                <div className="sec">
                  Cambios propuestos <span style={{ color: "#5f7378" }}>{msg.changes || 0}</span>
                </div>
                {msg.stats && <div className="ft">{msg.stats}</div>}
              </div>
            ))}
          </div>

          <div className="comp">
            <div className="cr">
              <button className="pre">SYS_EXEC ▾</button>
              <textarea
                className="pf"
                rows={1}
                placeholder={`Instrucciones para ${selectedProject || 'el sistema global'}...`}
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
              <label className="chip" style={{ borderStyle: "dashed", color: "#6d8288", cursor: "pointer" }}>
                <input 
                  type="file" 
                  style={{ display: "none" }} 
                  onChange={(e) => {
                    const file = e.target.files?.[0];
                    if(file) sysCommand(`[Archivo Adjuntado: ${file.name}]`);
                  }}
                />
                adjuntar / arrastrar evidencia aquí
              </label>
            </div>
          </div>
        </div>

        {/* COLUMNA DERECHA: LIENZO (CANVAS) */}
        <div className="col canvas" style={{ flex: 1, minWidth: "400px" }}>
          <div className="tabs">
            {["Plan", "Código", "Vista previa", "Terminal", "Configuración", "Gráfico HDC", "Telemetría del Enjambre"].map((tab) => (
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
              <div className="pv" style={{ border: "1px dashed var(--dim)", display: "flex", alignItems: "center", justifyContent: "center", color: "var(--dim)" }}>
                [Vista previa vacía]
              </div>
            )}
            
            {activeTab === "Terminal" && (
              <div className="selectable" style={{ flex: 1, background: "#000", border: "1px solid var(--dim)", padding: "10px", fontFamily: "monospace", color: "#0f0", whiteSpace: "pre-wrap", overflowY: "auto", userSelect: "text", WebkitUserSelect: "text" }}>
                {terminalOutput}
                <div ref={terminalEndRef} />
              </div>
            )}
            
            {activeTab === "Configuración" && (
               <div style={{ flex: 1, background: "#050a0b", border: "1px solid var(--dim)", padding: "20px", color: "#cfe0e4", overflowY: "auto", userSelect: "text", WebkitUserSelect: "text" }}>
                  <h2 style={{ color: "var(--acc)", marginBottom: "15px" }}>Configuración del Sistema MAGI</h2>
                  <p style={{ color: "var(--dim)", marginBottom: "20px" }}>Ajustes del orquestador y conexiones de red.</p>
                  
                  <div style={{ marginBottom: "15px" }}>
                    <label style={{ display: "block", marginBottom: "5px", color: "var(--node)" }}>Conexión LLM (Backend)</label>
                    <select style={{ background: "#000", color: "#fff", border: "1px solid var(--gr)", padding: "5px", width: "100%" }}>
                      <option>Nativo (G4F Auto-Router Open Source)</option>
                      <option>Ollama (Local LLM)</option>
                      <option>OpenRouter (Bring Your Own Key)</option>
                    </select>
                  </div>
                  
                  <div style={{ marginBottom: "15px" }}>
                    <label style={{ display: "block", marginBottom: "5px", color: "var(--node)" }}>Ollama URL (Opcional)</label>
                    <input type="text" placeholder="http://localhost:11434" style={{ background: "#000", color: "#fff", border: "1px solid var(--gr)", padding: "5px", width: "100%" }} />
                  </div>

                  <div style={{ marginBottom: "15px" }}>
                    <label style={{ display: "block", marginBottom: "5px", color: "var(--node)" }}>API Key Personal (Opcional)</label>
                    <input type="password" placeholder="sk-..." style={{ background: "#000", color: "#fff", border: "1px solid var(--gr)", padding: "5px", width: "100%" }} />
                  </div>

                  <button className="bt go" onClick={() => sysCommand("Guardando configuración...")}>Guardar Cambios</button>
               </div>
            )}
            
            {activeTab === "Código" && (
               <div style={{ flex: 1, background: "#1e1e1e", border: "1px solid var(--dim)", padding: "10px", fontFamily: "monospace", color: "#d4d4d4", overflowY: "auto", display: "flex", alignItems: "center", justifyContent: "center" }}>
                  <span style={{ color: "var(--dim)" }}>[Esperando sincronización de árbol de archivos para {selectedProject || "Global"}]</span>
               </div>
            )}

            {activeTab === "Plan" && (
               <div style={{ flex: 1, padding: "10px", color: "#cfe0e4", overflowY: "auto", border: "1px dashed var(--dim)", display: "flex", alignItems: "center", justifyContent: "center" }}>
                  <span style={{ color: "var(--dim)" }}>[Sin plan de ejecución activo]</span>
               </div>
            )}

            {activeTab === "Gráfico HDC" && (
               <div style={{ flex: 1, padding: "10px", border: "1px dashed var(--dim)", display: "flex", alignItems: "center", justifyContent: "center", color: "var(--node)", textAlign: "center" }}>
                  [Renderizador WebGL de Memoria Hiperdimensional - Esperando Datos de Vector DB]
               </div>
            )}

            {activeTab === "Telemetría del Enjambre" && (
              <div style={{ flex: 1, padding: "20px", overflowY: "auto", background: "#050a0b", color: "#cfe0e4" }}>
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
                      
                      <div style={{ fontSize: "11px", display: "flex", flexDirection: "column", gap: "2px", color: "var(--dim)" }}>
                        <div style={{ display: "flex", justifyContent: "space-between" }}><span>Aciertos:</span><b style={{ color: "#0f0" }}>{prov.success_count}</b></div>
                        <div style={{ display: "flex", justifyContent: "space-between" }}><span>Fallos:</span><b style={{ color: "#f55" }}>{prov.failure_count}</b></div>
                        <div style={{ display: "flex", justifyContent: "space-between" }}><span>Latencia:</span><b>{prov.avg_latency_ms.toFixed(0)} ms</b></div>
                        <div style={{ display: "flex", justifyContent: "space-between" }}><span>Complejidad:</span><b>{prov.avg_word_count.toFixed(0)} pal.</b></div>
                      </div>
                    </div>
                  )) : (
                    <div style={{ color: "var(--dim)" }}>Sin datos de telemetría reales.</div>
                  )}
                </div>
              </div>
            )}

          </div>
        </div>
      </div>

      <div className="foot">
        <div>
          ejecutable de escritorio · <b>MAGI SYSTEM IDE v3.0</b> · layout maestro
        </div>
        <div>acceso root habilitado</div>
      </div>
    </>
  );
}

export default App;
