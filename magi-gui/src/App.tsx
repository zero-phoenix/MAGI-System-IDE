import { useState, useRef, useEffect } from "react";
import "./App.css";
import { useMagiStore } from "./store";
import { useMagiSocket } from "./useMagiSocket";
import { useMagiAudio } from "./useMagiAudio";
import { FileTreeSidebar } from "./FileTreeSidebar";
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import DiffViewer from './DiffViewer';
import Editor from '@monaco-editor/react';
import { ReactFlow, Background, Controls, Node, Edge } from '@xyflow/react';
import '@xyflow/react/dist/style.css';

const AgentMessageCard = ({ msg, telemetry, renderCode }: any) => {
  const [isExpanded, setIsExpanded] = useState(false);
  
  let body = "";
  let conclusion = "";

  const cleanText = (str: string) => {
    return str
      .replace(/^(?:###\s*)?\*\*?CONCLUSIÓ[NN](?:\s*FINAL\s*CONSOLIDADA)?:?\*\*?\s*/gi, '')
      .replace(/^\*\*?CONCLUSIÓ[NN]:?\*\*?\s*/gi, '')
      .trim();
  };

  if (msg.agent === 'USER') {
    body = msg.content || "";
  } else {
    let rawContent = (msg.content || "").trim();
    rawContent = cleanText(rawContent);

    const paragraphs = rawContent.split(/\n\s*\n/);
    if (paragraphs.length > 1) {
      conclusion = cleanText(paragraphs[paragraphs.length - 1]);
      body = cleanText(paragraphs.slice(0, paragraphs.length - 1).join('\n\n'));
    } else {
      conclusion = rawContent;
      body = "";
    }
  }

  return (
    <div className={`msg-card ${msg.agent.toLowerCase()}`} style={{ border: `1px solid var(--dim)`, background: 'rgba(10, 20, 25, 0.7)', marginBottom: '12px', borderRadius: '8px', overflow: 'hidden', width: '100%', boxSizing: 'border-box', flex: '0 0 auto' }}>
      <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 12px', background: 'rgba(0,0,0,0.5)', borderBottom: '1px solid var(--dim)', fontSize: '11px', color: 'var(--dim)' }}>
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <strong style={{ color: msg.agent === 'MELCHIOR' ? 'var(--var)' : msg.agent === 'BALTHASAR' ? 'var(--acc)' : msg.agent === 'CASPER' ? 'var(--fn)' : '#fff' }}>
            {msg.agent}
          </strong>
          <span>[{msg.role}]</span>
        </div>
        <div style={{ display: 'flex', gap: '15px' }}>
          <span>⚙️ {msg.provider}</span>
          {telemetry?.find((t: any) => t.provider === msg.provider) && (
            <span style={{ color: 'var(--node)' }}>
              ⚡ {telemetry.find((t: any) => t.provider === msg.provider).avg_latency_ms.toFixed(0)}ms
            </span>
          )}
        </div>
      </div>
      <div className="card-body" style={{ padding: '12px', fontSize: '13px', wordBreak: 'break-word', overflowWrap: 'anywhere' }}>
        {msg.agent === 'USER' ? (
          <div>
            <ReactMarkdown remarkPlugins={[remarkGfm]} components={{ code: renderCode }}>
              {msg.content}
            </ReactMarkdown>
          </div>
        ) : (
          <>
            {conclusion && (
              <div className="card-conclusion-text" style={{ marginBottom: body ? '8px' : '0', color: '#cfe0e4', fontWeight: 400, fontSize: '13px', lineHeight: 1.55 }}>
                <ReactMarkdown remarkPlugins={[remarkGfm]} components={{ code: renderCode }}>
                  {conclusion}
                </ReactMarkdown>
              </div>
            )}

            {body && (
              <div style={{ marginTop: '8px' }}>
                <button 
                  onClick={() => setIsExpanded(!isExpanded)} 
                  style={{ background: 'transparent', border: 'none', color: 'var(--acc)', cursor: 'pointer', fontSize: '11px', padding: 0, fontWeight: 'bold' }}
                >
                  {isExpanded ? 'Ocultar análisis ▴' : 'Ver análisis completo ▾'}
                </button>
                {isExpanded && (
                  <div className="card-body-text" style={{ marginTop: '8px', paddingTop: '8px', borderTop: '1px dashed var(--dim)', color: '#cfe0e4', fontWeight: 400, fontSize: '13px', lineHeight: 1.55 }}>
                    <ReactMarkdown remarkPlugins={[remarkGfm]} components={{ code: renderCode }}>
                      {body}
                    </ReactMarkdown>
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default function App() {
  const [activeTab, setActiveTab] = useState("Vista previa");
  const { 
    connected, messages, activeConversationId, setActiveConversationId, 
    startNewConversation, addMessage, terminalOutput, 
    metrics, telemetry,
    activeFileContent, activeFilePath,
    naokoMessages, naokoStatus,
    sysCommand, conversations
  } = useMagiStore();

  const [inputVal, setInputVal] = useState("");
  const [naokoInputVal, setNaokoInputVal] = useState("");
  const [naokoImage, setNaokoImage] = useState<string | null>(null);
  const [gitUrl, setGitUrl] = useState("");
  const [engine, setEngine] = useState("fast");
  const [narrativeStyle, setNarrativeStyle] = useState("tecnico");
  const [pendingApproval, setPendingApproval] = useState<string | null>(null);
  const { sendCommand, fetchTelemetry, sendGitClone, requestFileContent, sendNaokoChat } = useMagiSocket(20128);
  const { playCalcBeep, playDecisionClack } = useMagiAudio();
  
  const terminalEndRef = useRef<HTMLDivElement>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Capturar imágenes pegadas desde el portapapeles (Ctrl+V con Herramienta de recorte de Windows)
  useEffect(() => {
    const handleGlobalPaste = (e: ClipboardEvent) => {
      const items = e.clipboardData?.items;
      if (items) {
        for (let i = 0; i < items.length; i++) {
          if (items[i].type.indexOf("image") !== -1) {
            const file = items[i].getAsFile();
            if (file) {
              const reader = new FileReader();
              reader.onloadend = () => {
                setNaokoImage(reader.result as string);
                setActiveTab("Naoko");
              };
              reader.readAsDataURL(file);
              e.preventDefault();
              break;
            }
          }
        }
      }
    };
    window.addEventListener("paste", handleGlobalPaste);
    return () => window.removeEventListener("paste", handleGlobalPaste);
  }, []);

  // Auto-scroll terminal y conversacion
  useEffect(() => {
    if (activeTab === "Terminal" && terminalEndRef.current) {
      terminalEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
    if (activeTab === "Estado de Motores IA") {
      fetchTelemetry();
    }
  }, [terminalOutput, messages, activeTab, fetchTelemetry]);

  useEffect(() => {
    if (terminalOutput.includes("Esperando aprobación interactiva del usuario") && !pendingApproval) {
      // Find the last proposal by Melchior or Balthasar
      const props = [...messages].reverse().find(m => m.role === 'propone' || m.role === 'critica');
      if (props) {
        setPendingApproval(props.content);
        setActiveTab("Diff (Aprobación)");
      }
    }
  }, [terminalOutput, messages, pendingApproval]);

  const handleExecute = () => {
    if(!inputVal.trim()) return;
    sysCommand(inputVal);
    sendCommand(inputVal, activeConversationId, engine);
    
    // Add to conversations
    addMessage({
      id: Math.random().toString(36),
      agent: "USER",
      role: "comando",
      provider: "local",
      content: inputVal,
      changes: 0,
      stats: "",
      task_id: activeConversationId
    });
    
    setInputVal("");
  };

  const runHostScript = (code: string) => {
    setActiveTab("Terminal");
    sysCommand(`SYS_EXEC_HOST \n${code}`);
    sendCommand(`SYS_EXEC_HOST \n${code}`, activeConversationId);
  };

  const renderCode = ({node, inline, className, children, ...props}: any) => {
    const match = /language-(\w+)/.exec(className || '');
    const codeString = String(children).replace(/\n$/, '');
    
    if (!inline && match) {
      const isExecutable = ['bash', 'powershell', 'python', 'sh', 'cmd', 'ps1'].includes(match[1].toLowerCase());
      return (
        <div style={{ position: 'relative', marginTop: '10px', marginBottom: '10px' }}>
          <div style={{ background: '#1a1a1a', padding: '10px', borderRadius: '4px', overflowX: 'auto' }}>
            <code className={className} style={{ color: '#00ff00', fontFamily: 'monospace' }} {...props}>
              {children}
            </code>
          </div>
          {isExecutable && (
            <button 
              onClick={() => runHostScript(codeString)}
              style={{ position: 'absolute', top: '5px', right: '5px', background: 'var(--acc)', color: '#000', border: 'none', padding: '4px 8px', fontSize: '10px', cursor: 'pointer', fontWeight: 'bold' }}
            >
              ▶ Ejecutar en PC
            </button>
          )}
        </div>
      );
    }
    return <code className={className} style={{background: '#333', padding: '2px 4px', borderRadius: '2px'}} {...props}>{children}</code>;
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
  
  // Filter Conversations (instead of projects)
  const conversationKeys = Object.keys(conversations);

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
          <select 
            value={engine} 
            onChange={(e) => setEngine(e.target.value)}
            style={{ background: "#000", color: "#cfe0e4", border: "1px solid var(--gr)", fontSize: "11px", padding: "2px", marginRight: "10px", outline: "none" }}
          >
            <option value="fast">MOTOR: Inferencia Optimizada</option>
            <option value="deep">MOTOR: Razonamiento Superior (Seguro)</option>
          </select>
          <select 
            value={narrativeStyle} 
            onChange={(e) => setNarrativeStyle(e.target.value)}
            style={{ background: "#000", color: "var(--acc)", border: "1px solid var(--gr)", fontSize: "11px", padding: "2px", marginRight: "10px", outline: "none" }}
          >
            <option value="tecnico">ESTILO: Técnico (Ingeniería)</option>
            <option value="sintetico">ESTILO: Sintético (Resumido)</option>
            <option value="creativo">ESTILO: Creativo (Innovación)</option>
            <option value="analitico">ESTILO: Analítico (Profundo)</option>
          </select>
          <span>prov-a <b>{metrics?.prov_a || "0/0"}</b></span>
          <span>prov-b <b>{metrics?.prov_b || "offline"}</b></span>
          <span>prov-c <b>{metrics?.prov_c || "offline"}</b></span>
          <span style={{cursor: "pointer"}} onClick={() => setActiveTab("Configuración")}>⚙</span>
          <span className="stop" style={{cursor: "pointer"}} onClick={handleStopAll}>PARAR TODO</span>
        </div>
      </div>

      {/* MASTER LAYOUT: 4 COLUMNAS */}
      <div className="app" style={{ display: "flex", width: "100%", overflow: "hidden" }}>
        
        {/* COLUMNA 1: GESTOR DE PROYECTOS / ESTADO */}
        <div className="col rail" style={{ width: "260px", minWidth: "260px" }}>
          <input
            style={{ width: "100%", background: "#050a0b", border: "1px solid var(--gr)", color: "#cfe0e4", padding: "4px 6px", font: "inherit", fontSize: "11px", marginBottom: "8px" }}
            placeholder="Buscar proyectos…"
          />
          <div className="sc">
            <div className="sect">Conversaciones Activas</div>
            {conversationKeys.length > 0 ? conversationKeys.map((taskId, idx) => (
              <div 
                key={idx} 
                className={`th ${activeConversationId === taskId ? 'on' : ''}`}
                onClick={() => setActiveConversationId(taskId)}
              >
                {taskId}
                <small>{conversations[taskId]?.length || 0} mensajes</small>
              </div>
            )) : (
              <div style={{ padding: "10px", fontSize: "10px", color: "#5f7378" }}>
                Sin conversaciones.
              </div>
            )}
            
            <div style={{ marginTop: '20px', padding: '10px 15px' }}>
              <button 
                className="bt go" 
                style={{ width: '100%', display: 'flex', justifyContent: 'center', gap: '8px' }}
                onClick={() => startNewConversation()}
              >
                <span>+</span> Nueva Conversación
              </button>
            </div>
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
              Contexto Activo: <b style={{ color: "var(--node)" }}>{activeConversationId}</b>
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

          <div className="conv">
            <div className="you">
              <div className="w">SISTEMA</div>
              Conectado a la Pasarela Global. Esperando flujos del Enjambre para {activeConversationId}...
            </div>

            {messages.map((msg, i) => (
              <AgentMessageCard key={i} msg={msg} telemetry={telemetry} renderCode={renderCode} />
            ))}
            <div ref={chatEndRef} />
          </div>

          {/* BANNER PERSISTENTE DE APROBACIÓN CON BOTONES RÁPIDOS */}
          {(pendingApproval || terminalOutput.includes("Esperando aprobación interactiva del usuario")) && (
            <div className="approval-banner" style={{ background: "rgba(0, 30, 40, 0.95)", borderTop: "2px solid var(--acc)", borderBottom: "1px solid var(--dim)", padding: "10px 14px", display: "flex", justifyContent: "space-between", alignItems: "center", gap: "10px", zIndex: 11 }}>
              <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                <span style={{ fontSize: "18px", color: "var(--acc)" }}>⚡</span>
                <div>
                  <div style={{ fontSize: "12px", fontWeight: "bold", color: "#fff" }}>PROPUESTA LISTA PARA EJECUCIÓN NATIVA</div>
                  <div style={{ fontSize: "10px", color: "var(--dim)" }}>El Enjambre completó la deliberación. Haz clic en una acción rápida:</div>
                </div>
              </div>
              <div style={{ display: "flex", gap: "8px" }}>
                <button 
                  className="bt go" 
                  style={{ padding: "5px 12px", fontWeight: "bold", background: "var(--acc)", color: "#000", cursor: "pointer" }}
                  onClick={() => {
                    sysCommand("sí");
                    sendCommand("sí", activeConversationId, engine);
                    addMessage({ id: Math.random().toString(36), agent: "USER", role: "comando", provider: "local", content: "sí", changes: 0, stats: "", task_id: activeConversationId });
                    setPendingApproval(null);
                  }}
                >
                  ✅ Apruebo (Ejecutar)
                </button>
                <button 
                  className="bt" 
                  style={{ padding: "5px 10px", background: "#222", color: "#fff", border: "1px solid var(--dim)", cursor: "pointer" }}
                  onClick={() => {
                    setInputVal("Modificar: ");
                  }}
                >
                  ✏️ Modificar
                </button>
                <button 
                  className="bt stop" 
                  style={{ padding: "5px 10px", background: "var(--dang)", color: "#000", fontWeight: "bold", cursor: "pointer" }}
                  onClick={() => {
                    sysCommand("cancelar");
                    sendCommand("cancelar", activeConversationId, engine);
                    setPendingApproval(null);
                  }}
                >
                  🛑 Cancelar
                </button>
              </div>
            </div>
          )}

          <div className="comp">
            <div className="cr">
              <button className="pre">SYS_EXEC ▾</button>
              <textarea
                className="pf"
                rows={1}
                placeholder={`Instrucciones para ${activeConversationId}...`}
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
            {["Plan", "Código", "Vista previa", "Terminal", "Naoko", "Configuración", "Gráfico HDC", "Estado de Motores IA", ...(pendingApproval ? ["Diff (Aprobación)"] : [])].map((tab) => (
              <div
                key={tab}
                className={`tab ${activeTab === tab ? "on" : ""}`}
                onClick={() => setActiveTab(tab)}
              >
                {tab === "Diff (Aprobación)" ? "⚠️ " + tab : tab}
              </div>
            ))}
          </div>
          <div className="cbody" style={{ display: "flex", flexDirection: "column", height: "100%" }}>
            
            {activeTab === "Vista previa" && (
              <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
                <div style={{ padding: "10px", background: "#050a0b", borderBottom: "1px solid var(--dim)", display: "flex", gap: "10px" }}>
                  <span style={{ color: "var(--dim)", fontSize: "12px", alignSelf: "center" }}>URL:</span>
                  <input 
                    type="text" 
                    id="previewUrl"
                    defaultValue="http://localhost:3000"
                    style={{ flex: 1, background: "#000", border: "1px solid var(--gr)", color: "#cfe0e4", padding: "4px 8px", fontSize: "12px" }}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        const iframe = document.getElementById('previewIframe') as HTMLIFrameElement;
                        if (iframe) iframe.src = e.currentTarget.value;
                      }
                    }}
                  />
                  <button 
                    className="bt go" 
                    onClick={() => {
                      const input = document.getElementById('previewUrl') as HTMLInputElement;
                      const iframe = document.getElementById('previewIframe') as HTMLIFrameElement;
                      if (iframe && input) iframe.src = input.value;
                    }}
                  >
                    Actualizar
                  </button>
                </div>
                <iframe 
                  id="previewIframe"
                  src="http://localhost:3000" 
                  style={{ flex: 1, width: "100%", border: "none", background: "#fff" }}
                  title="Live Preview"
                />
              </div>
            )}
            
            {activeTab === "Terminal" && (
              <div className="selectable" style={{ flex: 1, background: "#000", border: "1px solid var(--dim)", padding: "10px", fontFamily: "monospace", color: "#0f0", whiteSpace: "pre-wrap", overflowY: "auto", userSelect: "text", WebkitUserSelect: "text" }}>
                {terminalOutput}
                <div ref={terminalEndRef} />
              </div>
            )}
            
            {activeTab === "Naoko" && (
              <div style={{ display: "flex", flexDirection: "column", height: "100%", background: "#050a0b", border: "1px solid var(--dim)" }}>
                 <div style={{ padding: "10px", background: "rgba(0,0,0,0.5)", borderBottom: "1px solid var(--dim)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                   <div style={{ color: "#d2a8ff", fontWeight: "bold" }}>NAOKO [DevOps Autónoma & Visión Multimodal]</div>
                   <div style={{ color: naokoStatus === "Inactiva" ? "var(--dim)" : "var(--acc)", fontSize: "12px" }}>
                     Estado: {naokoStatus}
                   </div>
                 </div>
                 
                 <div style={{ flex: 1, padding: "15px", overflowY: "auto", display: "flex", flexDirection: "column", gap: "10px" }}>
                   {naokoMessages.map((msg, i) => (
                      <div key={i} style={{ 
                        background: msg.agent === "USER" ? "rgba(10,20,25,0.9)" : "rgba(30,20,30,0.7)", 
                        border: `1px solid ${msg.agent === "USER" ? "var(--dim)" : "#d2a8ff"}`, 
                        padding: "10px", 
                        borderRadius: "8px",
                        alignSelf: msg.agent === "USER" ? "flex-end" : "flex-start",
                        maxWidth: "85%",
                        fontSize: "13px",
                        wordBreak: "break-word",
                        overflowWrap: "anywhere"
                      }}>
                        <div style={{ fontSize: "11px", color: "var(--dim)", marginBottom: "5px" }}>{msg.agent}</div>
                        <ReactMarkdown remarkPlugins={[remarkGfm]} components={{ code: renderCode }}>
                          {msg.content}
                        </ReactMarkdown>
                      </div>
                   ))}
                 </div>
                 
                 <div className="comp" style={{ padding: "10px", borderTop: "1px solid var(--dim)" }}>
                    {naokoImage && (
                      <div style={{ position: 'relative', display: 'inline-block', marginBottom: '8px' }}>
                        <img src={naokoImage} alt="Adjunto Naoko" style={{ maxHeight: '80px', borderRadius: '4px', border: '1px solid var(--acc)' }} />
                        <button 
                          onClick={() => setNaokoImage(null)}
                          style={{ position: 'absolute', top: '-6px', right: '-6px', background: 'var(--dang)', color: '#000', border: 'none', borderRadius: '50%', width: '18px', height: '18px', cursor: 'pointer', fontSize: '10px', fontWeight: 'bold' }}
                        >
                          ✕
                        </button>
                      </div>
                    )}
                    <div className="cr" style={{ margin: 0, gap: '6px' }}>
                      <label className="chip" style={{ borderStyle: "dashed", cursor: "pointer", display: "flex", alignItems: "center", padding: "4px 8px", fontSize: "11px", background: "rgba(210,168,255,0.1)", color: "#d2a8ff", border: "1px dashed #d2a8ff", borderRadius: "4px" }}>
                        📷 <input type="file" accept="image/*" onChange={(e) => {
                          const file = e.target.files?.[0];
                          if (file) {
                            const reader = new FileReader();
                            reader.onloadend = () => setNaokoImage(reader.result as string);
                            reader.readAsDataURL(file);
                          }
                        }} style={{ display: 'none' }} />
                      </label>
                      <textarea
                        className="pf"
                        rows={1}
                        placeholder="Pregunta a Naoko o adjunta una captura visual..."
                        value={naokoInputVal}
                        onChange={(e) => setNaokoInputVal(e.target.value)}
                        onKeyDown={(e) => {
                          if(e.key === 'Enter' && !e.shiftKey) {
                            e.preventDefault();
                            if(naokoInputVal.trim() || naokoImage){
                               sendNaokoChat(naokoInputVal.trim() || "Analizar captura de pantalla adjunta", naokoImage);
                               setNaokoInputVal("");
                               setNaokoImage(null);
                            }
                          }
                        }}
                      ></textarea>
                      <button className="bt go" onClick={() => {
                        if(naokoInputVal.trim() || naokoImage){
                           sendNaokoChat(naokoInputVal.trim() || "Analizar captura de pantalla adjunta", naokoImage);
                           setNaokoInputVal("");
                           setNaokoImage(null);
                        }
                      }}>Enviar ▸</button>
                    </div>
                 </div>
              </div>
            )}
            
             {activeTab === "Estado de Motores IA" && (
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
            )}
            
            {activeTab === "Código" && (
               <div style={{ flex: 1, display: 'flex', background: "#1e1e1e", border: "1px solid var(--dim)", color: "#d4d4d4", overflow: "hidden" }}>
                  <FileTreeSidebar onFileClick={requestFileContent} />
                  <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
                    <div style={{ padding: '8px', background: '#252526', borderBottom: '1px solid var(--dim)', fontSize: '12px', color: 'var(--acc)' }}>
                      {activeFilePath || 'Ningún archivo seleccionado'}
                    </div>
                    <div style={{ flex: 1 }}>
                      {activeFilePath ? (
                        <Editor
                          height="100%"
                          theme="vs-dark"
                          path={activeFilePath}
                          value={activeFileContent}
                          options={{ readOnly: true, minimap: { enabled: false }, fontSize: 13 }}
                        />
                      ) : (
                        <div style={{ display: 'flex', height: '100%', alignItems: 'center', justifyContent: 'center', color: 'var(--dim)' }}>
                          Selecciona un archivo del explorador
                        </div>
                      )}
                    </div>
                  </div>
               </div>
            )}

            {activeTab === "Plan" && (() => {
               const latestPlanMsg = [...messages].reverse().find(m => m.content.includes('### PLAN'));
               let planContent = null;
               if (latestPlanMsg) {
                 const parts = latestPlanMsg.content.split('### PLAN');
                 if (parts.length > 1) {
                   planContent = parts[1].split('###')[0].trim();
                 }
               }
               return (
                 <div style={{ flex: 1, padding: "20px", color: "#cfe0e4", overflowY: "auto", background: "#050a0b" }}>
                   {planContent ? (
                     <div>
                       <h2 style={{ color: "var(--acc)", borderBottom: "1px solid var(--dim)", paddingBottom: "10px" }}>Plan de Ejecución Activo</h2>
                       <div className="markdown-body">
                         <ReactMarkdown remarkPlugins={[remarkGfm]}>{planContent}</ReactMarkdown>
                       </div>
                     </div>
                   ) : (
                     <div style={{ display: "flex", height: "100%", alignItems: "center", justifyContent: "center", border: "1px dashed var(--dim)" }}>
                       <span style={{ color: "var(--dim)" }}>[Sin plan de ejecución activo]</span>
                     </div>
                   )}
                 </div>
               );
            })()}

            {activeTab === "Gráfico HDC" && (() => {
               const nodes: Node[] = [];
               const edges: Edge[] = [];
               
               nodes.push({
                 id: 'user',
                 position: { x: 250, y: 20 },
                 data: { label: '👤 Usuario (Input)' },
                 style: { background: '#2c3e50', color: 'white', border: '1px solid #34495e', borderRadius: '8px' }
               });
               
               let prevId = 'user';
               let yPos = 100;
               
               messages.forEach((msg, idx) => {
                 const id = `msg_${idx}`;
                 let color = '#2980b9';
                 if (msg.agent === 'MELCHIOR') color = 'var(--var)';
                 if (msg.agent === 'BALTHASAR') color = 'var(--acc)';
                 if (msg.agent === 'CASPER') color = 'var(--fn)';
                 
                 nodes.push({
                   id,
                   position: { x: 250, y: yPos },
                   data: { label: `${msg.agent} [${msg.role}]` },
                   style: { background: 'rgba(10,20,25,0.9)', color, border: `1px solid ${color}`, borderRadius: '8px' }
                 });
                 
                 edges.push({
                   id: `e_${prevId}_${id}`,
                   source: prevId,
                   target: id,
                   animated: true,
                   style: { stroke: 'var(--dim)' }
                 });
                 
                 prevId = id;
                 yPos += 80;
               });

               return (
                 <div style={{ flex: 1, height: '100%', background: '#050a0b' }}>
                   <ReactFlow nodes={nodes} edges={edges} fitView>
                     <Background color="#222" gap={16} />
                     <Controls />
                   </ReactFlow>
                 </div>
               );
            })()}

            {activeTab === "Diff (Aprobación)" && pendingApproval && (
               <DiffViewer 
                 originalCode="" 
                 newCode={pendingApproval} 
                 onApprove={() => {
                   sysCommand("SI");
                   // sendCommand("SI", activeConversationId, engine);
                   setPendingApproval(null);
                   setActiveTab("Terminal");
                 }}
                 onReject={() => {
                   sysCommand("NO");
                   // sendCommand("NO", activeConversationId, engine);
                   setPendingApproval(null);
                   setActiveTab("Terminal");
                 }}
               />
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

