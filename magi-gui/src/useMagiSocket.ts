import { useEffect, useRef } from 'react';
import { useMagiStore } from './store';

export function useMagiSocket(port: number = 20140) {
  const ws = useRef<WebSocket | null>(null);
  const { setConnected, addMessage, appendTerminal } = useMagiStore();

  useEffect(() => {
    const connect = () => {
      try {
        ws.current = new WebSocket(`ws://127.0.0.1:${port}`);

        ws.current.onopen = () => {
          setConnected(true);
          appendTerminal(`[NETWORK] Conexión WebSocket establecida en puerto ${port}`);
        };

        ws.current.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data.type === 'AGENT_POST') {
              addMessage({
                id: Math.random().toString(36),
                agent: data.agent,
                role: data.role || 'propone',
                provider: data.provider || 'local',
                content: data.content,
                changes: data.changes || 0,
                stats: data.stats || '0 ms'
              });
            } else if (data.type === 'TERMINAL_OUT') {
              appendTerminal(data.content);
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

  return { sendCommand };
}
