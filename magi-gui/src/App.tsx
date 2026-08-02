import { useState, useRef, useEffect } from "react";
import "./App.css";
import { useMagiStore } from "./store";
import { useMagiSocket } from "./useMagiSocket";

function App() {
  const [activeTab, setActiveTab] = useState("Vista previa");
  const [topSection, setTopSection] = useState("Conversación");
  const [selectedProject, setSelectedProject] = useState("Workspace Activo");
  const [inputVal, setInputVal] = useState("");
  
  const { connected, messages, terminalOutput, sysCommand } = useMagiStore();
  const { sendCommand } = useMagiSocket(20140);
  
  const terminalEndRef = useRef<HTMLDivElement>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll terminal and chat
  useEffect(() => {
    if (activeTab === "Terminal" && terminalEndRef.current) {
      terminalEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [terminalOutput, activeTab]);

  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  const handleExecute = () => {
    if(!inputVal.trim()) return;
    sysCommand(inputVal); // Echo local to terminal
    sendCommand(inputVal); // Send to Python backend
    setInputVal("");
  };

  const handleStopAll = () => {
    sysCommand("EMERGENCY_STOP");
    sendCommand("KILL_ALL_PROCESSES");
  };

  return (
    <div className="layout">
      {/* HEADER FIJO */}
      <header className="header">
        <div className="h-left">
          <span className="brand">MAGI SYSTEM IDE</span>
          <span className={`status ${connected ? "online" : "offline"}`}>
            {connected ? "EN LÍNEA" : "DESCONECTADO"}
          </span>
          <nav className="h-nav">
            <button className={topSection === "Conversación" ? "active" : ""} onClick={() => setTopSection("Conversación")}>Conversación</button>
            <button className={topSection === "Proyectos" ? "active" : ""} onClick={() => setTopSection("Proyectos")}>Proyectos</button>
          </nav>
        </div>
        <div className="h-right">
          <span className="stop-btn" onClick={handleStopAll}>PARAR TODO</span>
        </div>
      </header>

      {/* ÁREA PRINCIPAL PROPORCIONAL */}
      <main className="main-area">
        
        {/* BARRA LATERAL */}
        <aside className="sidebar">
          <div className="sidebar-content">
            <div className="lbl">PROYECTOS ACTIVOS</div>
            <div className={`th ${selectedProject === 'Workspace Activo' ? 'on' : ''}`} onClick={() => setSelectedProject('Workspace Activo')}>
              Workspace Activo
              <small>Enrutado a disco local</small>
            </div>
            <div className="lbl" style={{marginTop: "20px"}}>ESTADO ENJAMBRE</div>
            <div className="th">
              Balthasar (Crítico)
              <small>Conectado: Claude 3.5</small>
            </div>
            <div className="th">
              Casper (Árbitro)
              <small>Conectado: Gemini 1.5</small>
            </div>
            <div className="th">
              Melchior (Propone)
              <small>Conectado: GPT-4o</small>
            </div>
          </div>
          <div className="cfg" onClick={() => setActiveTab("Terminal")}>
            ⚙ Terminal del Sistema
          </div>
        </aside>

        {/* ÁREA CENTRAL: CONVERSACIÓN */}
        <section className="chat-section">
          {topSection === "Conversación" ? (
            <div className="chat-container">
              <div className="chat-history">
                {messages.length === 0 ? (
                  <div className="sys-msg">
                    SISTEMA: Conectado a la Pasarela de Inferencia. Esperando flujos del Enjambre...
                  </div>
                ) : (
                  messages.map((msg, i) => (
                    <div key={i} className={`card ${msg.role === 'propone' ? 'prop' : (msg.role === 'critica' ? 'crit' : 'arb')}`}>
                      <div className="ch">
                        <span style={{ display: "flex", gap: "6px", alignItems: "center" }}>
                          <span className="dot" style={{ background: msg.role === 'propone' ? 'var(--node)' : (msg.role === 'critica' ? 'var(--dang)' : 'var(--warn)') }}></span>
                          <b style={{ color: msg.role === 'propone' ? 'var(--node)' : (msg.role === 'critica' ? 'var(--dang)' : 'var(--warn)') }}>{msg.agent}</b>
                          <span style={{ color: "#6d8288", textTransform: "uppercase" }}>{msg.role}</span>
                        </span>
                      </div>
                      <div className="mid">
                        IA UTILIZADA: <b style={{color: "var(--acc)"}}>{msg.provider}</b>
                      </div>
                      <div className="pl">«{msg.content}»</div>
                      <div className="sec" style={{display: "flex", justifyContent: "space-between"}}>
                        <span>Cambios detectados: {msg.changes}</span>
                        <span>Inferencia: {msg.stats}</span>
                      </div>
                    </div>
                  ))
                )}
                <div ref={chatEndRef} />
              </div>
              <div className="chat-composer">
                <input
                  type="text"
                  placeholder="Escribe tu instrucción o comando (acceso total)…"
                  value={inputVal}
                  onChange={(e) => setInputVal(e.target.value)}
                  onKeyDown={(e) => { if (e.key === 'Enter') handleExecute(); }}
                />
                <button onClick={handleExecute}>Ejecutar ▸</button>
              </div>
            </div>
          ) : (
            <div className="projects-container">
              <h2 style={{ color: "var(--acc)", marginTop: 0 }}>Gestor de Proyectos (Workspace Activo)</h2>
              <p style={{ color: "#8fa4aa" }}>El sistema leerá los archivos de tu computadora y sincronizará los cambios automáticamente.</p>
            </div>
          )}
        </section>

        {/* ÁREA DERECHA: PESTAÑAS (LIENZO) */}
        <section className="canvas-section">
          <div className="tabs">
            {["Plan", "Código", "Vista previa", "Terminal", "Gráfico HDC"].map((tab) => (
              <div key={tab} className={`tab ${activeTab === tab ? "on" : ""}`} onClick={() => setActiveTab(tab)}>
                {tab}
              </div>
            ))}
          </div>
          <div className="canvas-body">
            
            {activeTab === "Vista previa" && (
              <div className="preview-pane">
                <div className="preview-content"></div>
                <div className="preview-footer">
                  <span>Entorno activo: nativo local</span>
                </div>
              </div>
            )}
            
            {activeTab === "Terminal" && (
              <div className="terminal-pane">
                <div className="terminal-content">
                  {terminalOutput}
                  <div ref={terminalEndRef} />
                </div>
              </div>
            )}
            
            {activeTab === "Código" && (
              <div className="code-pane">
                // Sin archivos abiertos.<br/>
                // Envía comandos al Enjambre para generar código.
              </div>
            )}

            {activeTab === "Plan" && (
               <div className="plan-pane">
                  <div style={{ fontSize: "12px", color: "var(--acc)", marginBottom: "8px" }}>PLAN DE EJECUCIÓN</div>
                  <ul className="plan-list">
                    <li>Esperando instrucciones del agente proponente.</li>
                  </ul>
               </div>
            )}

            {activeTab === "Gráfico HDC" && (
               <div className="hdc-pane">
                  [Renderizador WebGL de Memoria Hiperdimensional - Esperando Datos]
               </div>
            )}

          </div>
        </section>

      </main>
      
      {/* FOOTER */}
      <footer className="footer">
        <span>MAGI SYSTEM IDE v9.0 · ejecutable nativo puro</span>
        <span style={{color: "var(--acc)"}}>ACCESO ROOT: HABILITADO</span>
      </footer>
    </div>
  );
}

export default App;
