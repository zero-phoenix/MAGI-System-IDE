import { useState, useRef, useEffect, useMemo } from "react";
import "./App.css";
import { useMagiStore } from "./store";
import { useMagiSocket } from "./useMagiSocket";
import { useMagiAudio } from "./useMagiAudio";
import { FileTreeSidebar } from "./FileTreeSidebar";
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import DiffViewer from './DiffViewer';
import AgentMessageCard from './components/AgentMessageCard';
import CostPanel from './components/CostPanel';
import SystemPanel from './components/SystemPanel';
import CommandPalette from './components/CommandPalette';
import NaokoPanel from './components/NaokoPanel';
import RitsukoPanel from './components/RitsukoPanel';
import { crearRenderCode } from './components/CodigoMarkdown';
import GraficoRondas from './components/GraficoRondas';
import ImprovementPanel from './components/ImprovementPanel';
import ConfigPanel from './components/ConfigPanel';
import PreviewPanel from './components/PreviewPanel';
import ProveedoresEnCabecera from './components/ProveedoresEnCabecera';
import type { Command } from './lib/commands';
import { tail } from './lib/history';
import Editor from '@monaco-editor/react';
import '@xyflow/react/dist/style.css';


export default function App() {
  const [activeTab, setActiveTab] = useState("Vista previa");
  const { 
    connected, messages, activeConversationId, setActiveConversationId, 
    startNewConversation, addMessage, terminalOutput,
    // `metrics` ya no se usa aquí: alimentaba las etiquetas prov-a/prov-b/
    // prov-c de la cabecera, que no significaban nada y se han sustituido por
    // el reparto real del enjambre leído de `sys.config`.
    telemetry,
    activeFileContent, activeFilePath,
    naokoMessages, naokoStatus,
    ritsukoMessages, ritsukoStatus, ritsukoInformes,
    sysCommand, conversations, streaming, toolTrace, route, alerts, dismissAlert,
    approval, setApproval, awaitingApproval, setAwaitingApproval,
    taskTitles  // v5.3.0 — títulos IA de cada conversación
  } = useMagiStore();

  const [inputVal, setInputVal] = useState("");
  const [naokoImage, setNaokoImage] = useState<string | null>(null);
  const [gitUrl, setGitUrl] = useState("");
  // v5.3.0: dos motores, por defecto "Análisis profundo". El selector de
  // ESTILO desaparece de la GUI: Naoko decide el estilo internamente a partir
  // del comando (kernel llama a estilo_para). narrativeStyle se mantiene fijo
  // aquí solo para no romper sendCommand, pero el backend lo recalcula.
  const [engine, setEngine] = useState(
    () => (typeof window !== "undefined" && window.localStorage?.getItem("magi.engine")) || "deep");
  const [narrativeStyle] = useState("tecnico");
  const [pendingApproval, setPendingApproval] = useState<string | null>(null);
  // v5.3.0 — confirma el borrado inline (sin window.confirm, que rompe el flujo).
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null);
  const { sendCommand, fetchTelemetry, sendGitClone, cancelTask, stopEverything,
          fetchHealth, runBenchmark, runSelfImprovement,
          listImprovements, proposeImprovement, decideImprovement,
          requestFileContent, sendNaokoChat,
          sendRitsukoChat, fetchRitsukoInformes,
          fetchConfig, listArtifacts, readArtifact,
          archiveTask, deleteTask  // v5.3.0 — archivar / borrar conversación
        } = useMagiSocket(20128);
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
    // `fetchTelemetry` NO va en las dependencias, y esto no es un descuido.
    //
    // `useMagiSocket` devuelve funciones nuevas en cada render (son arrow
    // functions, no `useCallback`), así que ponerla aquí hacía que este efecto
    // se ejecutara en CADA render. Con la pestaña «Estado de Motores IA»
    // abierta el ciclo se cerraba solo: efecto -> fetchTelemetry ->
    // setTelemetry -> render -> identidad nueva -> efecto...
    //
    // Medido el 2026-08-20 sobre la aplicación en marcha: **97 % de un núcleo
    // de forma permanente estando parada**, mientras el mismo kernel arrancado
    // solo, sin interfaz, gastaba 0 %. De ahí salía la sensación de que el
    // sistema «va lento» y de que Naoko no contesta: contestaba, pero la
    // ventana estaba ahogada.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [terminalOutput, messages, activeTab]);

  // §7.4 — el evento estructurado manda. El raspado de texto de abajo queda
  // como respaldo para backends antiguos, pero ya no es la vía principal.
  useEffect(() => {
    if (approval) setActiveTab("Diff (Aprobación)");
  }, [approval]);

  useEffect(() => {
    if (awaitingApproval && !pendingApproval) {
      // Find the last proposal by Melchior or Balthasar
      const props = [...messages].reverse().find(m => m.role === 'propone' || m.role === 'critica');
      if (props) {
        setPendingApproval(props.content);
        setActiveTab("Diff (Aprobación)");
      }
    }
  }, [awaitingApproval, messages, pendingApproval]);

  const handleExecute = () => {
    if(!inputVal.trim()) return;
    sysCommand(inputVal);
    sendCommand(inputVal, activeConversationId, engine, narrativeStyle);
    
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

  // El renderizador de bloques de código vive en components/: extraerlo
  // fue lo que pidió test_app_tsx_no_vuelve_a_crecer_sin_limite cuando
  // este fichero pasó de 900 líneas. Ver CodigoMarkdown.tsx.
  const renderCode = useMemo(() => crearRenderCode(runHostScript), []);

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
    stopEverything();
  };

  // §7.3 — catálogo de la paleta. Las pestañas se derivan de la misma lista
  // que pinta la barra, para que añadir una no exija acordarse de esto.
  const PESTAÑAS = ["Plan", "Código", "Vista previa", "Terminal", "Naoko",
                    "Ritsuko", "Configuración", "Gráfico HDC",
                    "Estado de Motores IA", "Coste", "Sistema", "Mejoras"];

  const comandos: Command[] = [
    { id: "cancel", title: "Parar solo esta tarea", group: "Ejecución",
      keywords: "cancelar detener turno conversacion", dangerous: true },
    { id: "stopall", title: "Parar todo", group: "Ejecución",
      keywords: "emergencia kill procesos", dangerous: true },
    { id: "newchat", title: "Conversación nueva", group: "Ejecución",
      keywords: "limpiar empezar" },
    ...PESTAÑAS.map((t) => ({
      id: `tab:${t}`, title: `Ir a ${t}`, group: "Paneles", keywords: t,
    })),
  ];

  const ejecutarComando = (id: string) => {
    if (id.startsWith("tab:")) { setActiveTab(id.slice(4)); return; }
    if (id === "cancel") { handleCancelTask(); return; }
    if (id === "stopall") { handleStopAll(); return; }
    if (id === "newchat") { startNewConversation(); return; }
  };

  // §7.3 — parar solo esta conversación. Si tienes tres abiertas y una se va
  // por las ramas, no quieres tirar las otras dos.
  const handleCancelTask = () => {
    sysCommand(`task.cancel ${activeConversationId}`);
    cancelTask(activeConversationId);
  };

  // Reparto REAL del enjambre, leído de `sys.config`.
  //
  // Antes, las tres tarjetas centrales caían a `prov-a` / `prov-b` / `prov-c`
  // mientras no hubiera mensajes — es decir, siempre al abrir. Tres etiquetas
  // que no significan nada para nadie; el usuario preguntó literalmente por
  // qué no se entienden. Y encima el reparto cableado estaba mal: le daba
  // `prov-c` a BALTHASAR y `prov-a` a CASPER, letras que no correspondían a
  // ningún proveedor. La cabecera ya se arregló; esto se quedó sin tocar.
  const [reparto, setReparto] = useState<Record<string, string>>({});
  // La versión la dice el KERNEL (sys.config), no este fichero: una
  // versión escrita a mano aquí ya conto un tres cuando el sistema iba por el
  // la 5.18 — un pie de página que miente sobre qué estás usando.
  const [versionKernel, setVersionKernel] = useState("");
  useEffect(() => {
    if (!fetchConfig) return;
    let vivo = true;
    fetchConfig()
      .then((c: any) => { if (vivo) { setReparto(c?.enjambre?.familias || {}); setVersionKernel(c?.version || ""); } })
      .catch(() => { /* la cabecera ya avisa; aquí se calla y usa "—" */ });
    return () => { vivo = false; };
    // Solo `connected`: `fetchConfig` cambia de identidad en cada render y
    // arrastraba este efecto con él. Ver el comentario largo del efecto de
    // auto-scroll y `tests/test_gui_sin_bucles_de_render.py`.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [connected]);

  const getAgentData = (agentName: string) => {
    const msgs = messages.filter(m => m.agent === agentName);
    const lastMsg = msgs.length > 0 ? msgs[msgs.length - 1] : null;
    // Lo que respondió de verdad manda; si aún no ha hablado, la familia que
    // le toca según el reparto; y si tampoco se sabe, un guion honesto.
    const provider = lastMsg?.provider || reparto[agentName] || "—";
    const tel = telemetry?.find(t => t.provider === provider);
    const latency = tel ? `${tel.avg_latency_ms.toFixed(0)}ms` : '---';
    return { provider, latency };
  };

  const balthasarData = getAgentData("BALTHASAR");
  const casperData = getAgentData("CASPER");
  const melchiorData = getAgentData("MELCHIOR");
  
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
          {/* Los dos selectores no decían qué hacen: "MOTOR: Inferencia
              Optimizada" y "ESTILO: Técnico" son nombres, no explicaciones, y
              el usuario preguntó para qué sirven. Ahora cada opción lleva su
              efecto real en el título, y el <select> entero explica el mando.
              Ninguno cambia QUÉ modelo se usa: eso lo decide el reparto del
              enjambre, que se ve a la derecha. */}
          <select
            value={engine}
            onChange={(e) => { setEngine(e.target.value); try { window.localStorage?.setItem("magi.engine", e.target.value); } catch {} }}
            title={"MOTOR — cuánto se piensa cada respuesta.\n\n"
                   + "· Análisis profundo: baja temperatura, más iteraciones de "
                   + "herramientas y verificación. Más lenta y precisa.\n"
                   + "· Súper rapidez: temperatura normal, menos vueltas. Rápida.\n\n"
                   + "El estilo de redacción lo decide Naoko automáticamente según tu pregunta."}
            style={{ background: "#000", color: "#cfe0e4", border: "1px solid var(--gr)", fontSize: "11px", padding: "2px", marginRight: "10px", outline: "none" }}
          >
            <option value="deep" title="Baja temperatura, más iteraciones y verificación. Más precisa.">
              🔍 Análisis profundo
            </option>
            <option value="fast" title="Temperatura normal, menos iteraciones. Rápida.">
              ⚡ Súper rapidez
            </option>
          </select>
          {route && (
            <span title={route.reason} style={{ marginRight: 10 }}>
              ruta <b style={{ color: "var(--acc)" }}>{route.route}</b>
              <span style={{ color: "var(--dim)" }}> · {route.max_rounds}r</span>
            </span>
          )}
          {/* Antes: "prov-a 31/50 · prov-b agotado · prov-c ok". Tres etiquetas
              que no significan nada para nadie — ni siquiera decían a qué
              proveedor correspondía cada letra. Ahora se nombra la familia
              real que atiende a cada nodo, con su latencia medida. */}
          <ProveedoresEnCabecera fetchConfig={fetchConfig} />
          <span style={{cursor: "pointer"}} title="Abrir Configuración"
                onClick={() => setActiveTab("Configuración")}>⚙</span>
          <span style={{cursor: "pointer", color: "var(--acc)", marginRight: 10}}
                title="Para solo esta conversación; las demás siguen"
                onClick={handleCancelTask}>PARAR ESTA</span>
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
                style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer' }}
                onClick={() => setActiveConversationId(taskId)}
                title={taskId}
              >
                <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', flex: 1 }}>
                  {/* v5.3.0 — título IA si lo hay; si no, el task_id */}
                  {taskTitles[taskId] || taskId}
                </span>
                <small style={{ flexShrink: 0, marginLeft: '4px' }}>{conversations[taskId]?.length || 0}m</small>
                {/* v5.3.0 — archivar y borrar. No son mutuamente excluyentes con
                    abrir la conversación: el click del botón se frena aquí. */}
                {confirmDelete === taskId ? (
                  <span style={{ marginLeft: '4px', fontSize: '9px', whiteSpace: 'nowrap' }}
                        onClick={(e) => e.stopPropagation()}>
                    <span style={{ cursor: 'pointer', color: '#f44' }}
                          title="Confirmar borrado"
                          onClick={() => { deleteTask(taskId); setConfirmDelete(null); }}>¿borrar?</span>{' '}
                    <span style={{ cursor: 'pointer', color: '#888' }}
                          title="Cancelar"
                          onClick={() => setConfirmDelete(null)}>no</span>
                  </span>
                ) : (
                  <span style={{ marginLeft: '4px', fontSize: '12px', flexShrink: 0 }} onClick={(e) => e.stopPropagation()}>
                    <span style={{ cursor: 'pointer', marginRight: '4px' }}
                          title="Archivar conversación"
                          onClick={() => archiveTask(taskId)}>📦</span>
                    <span style={{ cursor: 'pointer', color: '#f66' }}
                          title="Borrar conversación"
                          onClick={() => setConfirmDelete(taskId)}>🗑</span>
                  </span>
                )}
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

            {/* §7.3 — solo se montan los últimos. El `.map` en sí es barato
                (3 ms por 50 repintados de 800 mensajes, medido); lo caro es
                montar un ReactMarkdown por mensaje, y eso se arregla no
                montándolos. */}
            {(() => {
              const { visible, hidden } = tail(messages);
              return (
                <>
                  {hidden > 0 && (
                    <div style={{ color: "var(--dim)", fontSize: 11, padding: "6px 0" }}>
                      {hidden} mensaje(s) anteriores no se muestran para no
                      hundir el render. Siguen en la conversación.
                    </div>
                  )}
                  {visible.map((msg, i) => (
                    <AgentMessageCard key={messages.length - visible.length + i}
                                      msg={msg} telemetry={telemetry}
                                      renderCode={renderCode} />
                  ))}
                </>
              );
            })()}

            {/* MAGI 9.0 §3.4 — alertas de degradación */}
            {alerts.length > 0 && (
              <div className="alerts">
                {alerts.map((a: any) => (
                  <div key={a.id}
                       className={a.severity === 'critical' ? 'alert crit' : 'alert'}>
                    <span className="alert-kind">{a.kind}</span>
                    <span className="alert-detail">{a.detail}</span>
                    <button className="alert-x" onClick={() => dismissAlert(a.id)}>×</button>
                  </div>
                ))}
              </div>
            )}

            {/* MAGI 9.0 §2.2 — traza de herramientas del turno en curso */}
            {toolTrace.filter((t: any) => t.task_id === activeConversationId)
                      .slice(-6).length > 0 && (
              <div className="tool-trace">
                {toolTrace.filter((t: any) => t.task_id === activeConversationId)
                          .slice(-6).map((t: any) => (
                  <div key={t.id} className="tool-line">
                    <span className="tool-agent">{t.agent}</span>
                    <span className="tool-name">{t.tool}</span>
                    <span className={t.ok === undefined ? "tool-run"
                                     : t.ok ? "tool-ok" : "tool-err"}>
                      {t.ok === undefined ? "ejecutando…" : t.ok ? "ok" : (t.error || "falló")}
                    </span>
                  </div>
                ))}
              </div>
            )}

            {/* MAGI 9.0 §1.2 — tarjeta en vivo mientras el agente escribe.
                Antes la pantalla se quedaba quieta 30-90 s por turno. */}
            {Object.entries(streaming)
              .filter(([key]) => key.startsWith(`${activeConversationId}:`))
              .map(([key, buf]: any) => (
                <div key={key} className="card streaming" style={{ opacity: 0.92 }}>
                  <div className="hd">
                    <b>{buf.agent}</b>
                    <span style={{ color: "var(--dim)", fontSize: "10px", marginLeft: 8 }}>
                      {buf.family || "…"} · escribiendo
                      <span className="cursor-blink" style={{ marginLeft: 4 }}>▊</span>
                    </span>
                  </div>
                  <div className="bd" style={{ whiteSpace: "pre-wrap" }}>
                    {buf.text}
                  </div>
                </div>
              ))}

            <div ref={chatEndRef} />
          </div>

          {/* BANNER PERSISTENTE DE APROBACIÓN CON BOTONES RÁPIDOS */}
          {(pendingApproval || awaitingApproval) && (
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
                    sendCommand("sí", activeConversationId, engine, narrativeStyle);
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
                    sendCommand("cancelar", activeConversationId, engine, narrativeStyle);
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
            {[...PESTAÑAS, ...((pendingApproval || approval) ? ["Diff (Aprobación)"] : [])].map((tab) => (
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
            
            {/* Antes: un <iframe src="http://localhost:3000"> fijo en el
                código. Nadie levanta ese puerto, así que la pestaña enseñaba
                la página de error del navegador —cuadro blanco con nube— sobre
                una interfaz negra. Ahora enseña los artefactos que MAGI
                genera de verdad, y la URL queda como modo secundario. */}
            {activeTab === "Vista previa" && (
              <PreviewPanel listArtifacts={listArtifacts}
                            readArtifact={readArtifact} connected={connected} />
            )}

            {/* La pestaña estaba en la barra y NO tenía render: se pulsaba y
                no aparecía nada. */}
            {activeTab === "Configuración" && (
              <ConfigPanel fetchConfig={fetchConfig} />
            )}
            
            {activeTab === "Terminal" && (
              <div className="selectable" style={{ flex: 1, background: "#000", border: "1px solid var(--dim)", padding: "10px", fontFamily: "monospace", color: "#0f0", whiteSpace: "pre-wrap", overflowY: "auto", userSelect: "text", WebkitUserSelect: "text" }}>
                {terminalOutput}
                <div ref={terminalEndRef} />
              </div>
            )}
            
            {activeTab === "Naoko" && (
              <NaokoPanel naokoMessages={naokoMessages}
                          naokoStatus={naokoStatus}
                          sendNaokoChat={sendNaokoChat}
                          renderCode={renderCode}
                          imagen={naokoImage}
                          setImagen={setNaokoImage} />
            )}

            {activeTab === "Ritsuko" && (
              <RitsukoPanel ritsukoMessages={ritsukoMessages}
                            ritsukoStatus={ritsukoStatus}
                            informes={ritsukoInformes}
                            sendRitsukoChat={sendRitsukoChat}
                            fetchRitsukoInformes={fetchRitsukoInformes}
                            renderCode={renderCode} />
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

            {activeTab === "Gráfico HDC" && <GraficoRondas messages={messages} />}

            {activeTab === "Mejoras" && (
               /* Ciclo de mejora: compuertas del usuario y rondas del enjambre. */
               <ImprovementPanel listImprovements={listImprovements}
                                 proposeImprovement={proposeImprovement}
                                 decideImprovement={decideImprovement} />
            )}

            {activeTab === "Sistema" && (
               /* §3.4 y §3.5 — salud, banco y auto-mejora. Estaban completas
                  en el backend y sin forma de invocarlas. */
               <SystemPanel fetchHealth={fetchHealth}
                            runBenchmark={runBenchmark}
                            runSelfImprovement={runSelfImprovement} />
            )}

            {activeTab === "Coste" && (
               /* §7.3 — tokens y tiempo por tarea y por agente. */
               <CostPanel taskId={activeConversationId} />
            )}

            {activeTab === "Diff (Aprobación)" && (approval || pendingApproval) && (
               /* §7.4 — antes iba `originalCode=""`, así que el panel pintaba
                  todo en verde y no era un diff. Ahora recibe el evento con
                  los ficheros y su contenido previo; `pendingApproval` queda
                  solo como texto de respaldo, y el propio panel avisa cuando
                  es lo único que hay. */
               <DiffViewer
                 approval={approval}
                 fallbackText={pendingApproval || undefined}
                 onApprove={() => {
                   sysCommand("SI");
                   sendCommand("SI", activeConversationId, engine, narrativeStyle);
                   setPendingApproval(null);
                   setApproval(null);
                   setAwaitingApproval(false);
                   setActiveTab("Terminal");
                 }}
                 onReject={() => {
                   sysCommand("NO");
                   sendCommand("NO", activeConversationId, engine, narrativeStyle);
                   setPendingApproval(null);
                   setApproval(null);
                   setAwaitingApproval(false);
                   setActiveTab("Terminal");
                 }}
               />
            )}

          </div>
        </div>
      </div>

      <CommandPalette commands={comandos} onRun={ejecutarComando} />

      <div className="foot">
        <div>
          ejecutable de escritorio · <b>MAGI SYSTEM IDE {versionKernel ? `v${versionKernel}` : ""}</b> · layout maestro
        </div>
        <div>acceso root habilitado</div>
      </div>
    </>
  );
}

