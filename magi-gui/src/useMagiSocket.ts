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
                  agent: payload.agent,
                  role: payload.role || 'propone',
                  provider: payload.provider || 'local',
                  content: payload.content,
                  changes: payload.changes || 0,
                  stats: payload.stats || '0 ms'
                });
              } else if (topic === 'TERMINAL_OUT') {
                appendTerminal(payload.content || payload.message || String(payload));
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

  const sendCommand = (cmd: string) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ type: 'SYS_EXEC', command: cmd }));
    }
  };

  const fetchTelemetry = () => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ type: 'GET_TELEMETRY', id: 'req_telemetry' }));
    }
  };

  return { sendCommand, fetchTelemetry };
}
