import { useEffect, useRef } from 'react';
import { useMagiStore } from './store';

export function useMagiSocket(port: number = 20128) {
  const ws = useRef<WebSocket | null>(null);
  const { setConnected, addMessage, appendTerminal } = useMagiStore();

  useEffect(() => {
    const connect = () => {
      try {
        ws.current = new WebSocket(`ws://127.0.0.1:${port}`);

        ws.current.onopen = () => {
          setConnected(true);
          appendTerminal(`[NETWORK] Conexión WebSocket establecida en puerto ${port}`);
          // Solicitar estado real inicial
          ws.current?.send(JSON.stringify({ type: 'rpc.state.sync', id: 'sync_0' }));
          ws.current?.send(JSON.stringify({ type: 'GET_FILE_TREE', id: 'file_tree_0' }));
        };

        ws.current.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            
            if (data.type === 'event') {
              const topic = data.topic;
              const payload = data.payload;
              
              if (topic === 'AGENT_POST') {
                addMessage({
                  id: Math.random().toString(36),
                  task_id: payload.task_id,
                  agent: payload.agent,
                  role: payload.role || 'propone',
                  provider: payload.provider || 'local',
                  content: payload.content,
                  changes: payload.changes || 0,
                  stats: payload.stats || '0 ms'
                });
              } else if (topic === 'TERMINAL_OUT') {
                appendTerminal(payload.content || payload.message || String(payload));
              } else if (topic === 'naoko.log') {
                useMagiStore.getState().addNaokoMessage({
                  id: Math.random().toString(36),
                  agent: payload.agent,
                  role: "DevOps",
                  provider: "G4F",
                  content: payload.content,
                  changes: 0,
                  stats: "0 ms"
                });
              } else if (topic === 'naoko.status') {
                useMagiStore.getState().setNaokoStatus(payload.status);
              } else if (topic === 'system.project_created') {
                ws.current?.send(JSON.stringify({ type: 'rpc.state.sync', id: 'sync_0' }));
              }
            } else if (data.ok !== undefined) {
               // Es una respuesta directa RPC
               if (data.id === 'sync_0' && data.result) {
                 useMagiStore.getState().setProjects(data.result.projects || []);
                 if (data.result.metrics) {
                   useMagiStore.getState().setMetrics(data.result.metrics);
                 }
               } else if (data.id === 'req_telemetry' && data.result) {
                 useMagiStore.getState().setTelemetry(data.result);
               } else if (data.id === 'file_tree_0' && data.result) {
                 useMagiStore.getState().setFileTree(data.result);
               } else if (data.id === 'req_file_content' && data.result) {
                 if (data.result.content !== undefined) {
                   useMagiStore.getState().setActiveFile(data.result.path, data.result.content);
                 }
               }
            }
          } catch (e) {
            appendTerminal(`[NETWORK] Mensaje RAW: ${event.data}`);
          }
        };

        ws.current.onclose = () => {
          setConnected(false);
          // appendTerminal(`[NETWORK] Conexión perdida. Reconectando en 3s...`);
          setTimeout(connect, 3000);
        };
      } catch (err) {
         console.error("Socket error", err);
      }
    };

    connect();

    return () => {
      if (ws.current) ws.current.close();
    };
  }, [port]);

  // MAGI 9.0 §2.7 — narrativeStyle SÍ viaja al backend.
  // En v5.0.28 el <select> de estilo narrativo existía en App.tsx:307 pero su
  // valor no se enviaba nunca: esta firma no lo aceptaba. Era decorativo.
  const sendCommand = (
    cmd: string,
    taskId?: string,
    engine?: string,
    narrativeStyle?: string,
  ) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({
        type: "SYS_EXEC",
        payload: {
          command: cmd,
          id: taskId,
          engine: engine || "fast",
          narrative_style: narrativeStyle || "tecnico"
        }
      }));
    }
  };

  const sendGitClone = (url: string) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({
        type: "git.clone",
        payload: { url }
      }));
    }
  };

  const requestFileContent = (path: string) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({
        type: "GET_FILE_CONTENT",
        id: "req_file_content",
        payload: { path }
      }));
    }
  };

  const fetchTelemetry = () => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({
        type: "GET_TELEMETRY",
        id: "req_telemetry"
      }));
    }
  };

  const sendNaokoChat = (message: string, image?: string | null) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({
        type: "naoko.chat",
        payload: { message, image: image || null }
      }));
    }
  };

  return { sendCommand, sendGitClone, fetchTelemetry, requestFileContent, sendNaokoChat };
}
