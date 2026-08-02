import { useState } from "react";
import "./App.css";
import { useMagiStore } from "./store";
import { useMagiSocket } from "./useMagiSocket";

function App() {
  const [activeTab, setActiveTab] = useState("Vista previa");
  const [terminalVisible, setTerminalVisible] = useState(false);
  const [inputVal, setInputVal] = useState("");
  
  const { connected, messages, terminalOutput, sysCommand } = useMagiStore();
  const { sendCommand } = useMagiSocket(20140);

  const handleExecute = () => {
    if(!inputVal) return;
    sysCommand(inputVal);
    sendCommand(inputVal);
    setInputVal("");
  };

  return (
    <>
      <div className="tt">
        <b>MAGI SYSTEM IDE</b> — ejecutable de escritorio. Interfaz horizontal fija.
      </div>

      <div className="app">
        <div className="bar">
          <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
            <span className="brand">MAGI SYSTEM IDE {connected ? "[EN LÍNEA]" : "[DESCONECTADO]"}</span>
            <span className="secs">
              <button className="on">Conversación</button>
              <button>Proyectos</button>
            </span>
          </div>
          <div className="q">
            <span>
              prov-a <b>31/50</b>
            </span>
            <span>
              prov-b <b>agotado · repone 19:40</b>
            </span>
            <span>
              prov-c <b>ok</b>
            </span>
            <span>⚙</span>
            <span className="stop">PARAR TODO</span>
          </div>
        </div>

        {/* CARRIL */}
        <div className="col rail">
          <input
            style={{
              width: "100%",
              background: "#050a0b",
              border: "1px solid var(--gr)",
              color: "#cfe0e4",
              padding: "4px 6px",
              font: "inherit",
              fontSize: "11px",
            }}
            placeholder="Buscar…"
          />
          <div className="sc">
            <div className="lbl">HOY</div>
            <div className="th on">
              Juego de plataformas 8 bits
              <small>versión 3 de 6 · midiendo</small>
            </div>
            <div className="th">
              Revisar contrato
              <small>terminado · v4</small>
            </div>
            <div className="lbl">PROYECTOS</div>
            <div className="th">
              emulador-psp
              <small>↑2 ↓0 · repositorio conectado</small>
            </div>
            <div className="th">
              soporte-perfil-20
              <small>local · sin remoto</small>
            </div>
          </div>
          <div className="cfg" onClick={() => setTerminalVisible(!terminalVisible)}>
            ⚙ Terminal del Sistema
            <br />
            <span style={{ fontSize: "9px", fontWeight: 400 }}>Acceso Irrestricto</span>
          </div>
        </div>

        {/* CONVERSACIÓN */}
        <div className="col">
          <div className="tri">
            <div className="nd b">
              <div className="fx">el que busca fallos</div>
              <div className="nm">BALTHASAR · 2</div>
              <div className="md">prov-c · nube · 3 fallos nuevos</div>
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
        </div>

        {/* LIENZO */}
        <div className="col canvas">
          <div className="tabs">
            {["Plan", "Código", "Vista previa", "Terminal", "Gráfico HDC"].map((tab) => (
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
                <div className="pv">
                  <div className="game"></div>
                  <div
                    style={{
                      position: "absolute",
                      bottom: 0,
                      left: 0,
                      right: 0,
                      background: "#0f1a1d",
                      borderTop: "1px solid var(--gr)",
                      padding: "2px 6px",
                      fontSize: "9.5px",
                      color: "#8fa4aa",
                      display: "flex",
                      justifyContent: "space-between",
                    }}
                  >
                    <span>entorno activo</span>
                    <span>Tauri nativo</span>
                  </div>
                </div>

                <div style={{ fontSize: "10px", letterSpacing: ".1em", color: "var(--acc)", marginBottom: "3px" }}>
                  CRITERIOS DUROS
                </div>
                <div className="mrow">
                  <b>Compilación Rust</b>
                  <span className="ok">Completado ✓</span>
                </div>
                <div className="mrow">
                  <b>Acceso irrestricto</b>
                  <span className="ok">Concedido ✓</span>
                </div>
              </>
            )}
            
            {activeTab === "Terminal" && (
              <div style={{ flex: 1, background: "#000", border: "1px solid var(--dim)", padding: "10px", fontFamily: "monospace", color: "#0f0", whiteSpace: "pre-wrap", overflowY: "auto" }}>
                {terminalOutput}
              </div>
            )}
            
            {activeTab === "Código" && (
               <div style={{ flex: 1, background: "#1e1e1e", border: "1px solid var(--dim)", padding: "10px", fontFamily: "monospace", color: "#d4d4d4" }}>
                // Módulo React - Editor Monaco simulado<br/>
                <span style={{color: "#569cd6"}}>import</span> {"{"} useState {"}"} <span style={{color: "#569cd6"}}>from</span> <span style={{color: "#ce9178"}}>"react"</span>;<br/>
                ...
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
