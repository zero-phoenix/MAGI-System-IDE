/**
 * Panel de Ritsuko — la auditora.
 *
 * Separado del de Naoko A PROPÓSITO, y no por estética: Ritsuko revisa a
 * Naoko, y mezclar en una misma conversación al corrector y a quien lo
 * corrige es la forma más rápida de no saber quién dijo qué cuando algo sale
 * mal.
 *
 * Dos diferencias visibles con el panel de Naoko, las dos deliberadas:
 *
 *   1. No hay adjuntar imagen ni botón de acción. Ritsuko no ejecuta nada; un
 *      botón que sugiera lo contrario sería mentir con la interfaz.
 *   2. Hay una lista de informes con su ruta en disco. El usuario pidió
 *      informes DESCARGABLES: un panel que enseñe el texto y no diga dónde
 *      está el fichero no cumple eso.
 */
import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface Informe {
  nombre: string;
  ruta: string;
  bytes: number;
}

interface Props {
  ritsukoMessages: Array<{ agent: string; content: string }>;
  ritsukoStatus: string;
  informes: Informe[];
  sendRitsukoChat: (mensaje: string) => void;
  fetchRitsukoInformes: () => void;
  renderCode: any;
}

export default function RitsukoPanel({ ritsukoMessages, ritsukoStatus, informes,
                                       sendRitsukoChat, fetchRitsukoInformes,
                                       renderCode }: Props) {
  const [texto, setTexto] = useState("");

  // Se pide UNA vez al abrir la pestaña. `fetchRitsukoInformes` no va en las
  // dependencias porque `useMagiSocket` devuelve funciones nuevas en cada
  // render: ponerla ahí convertía este efecto en un bucle infinito —efecto ->
  // RPC -> respuesta -> setRitsukoInformes -> render -> identidad nueva ->
  // efecto— que inundaba el kernel de peticiones y se comía un núcleo.
  // La lista se refresca sola con cada `ritsuko.informe`, y hay botón.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { fetchRitsukoInformes(); }, []);

  const enviar = () => {
    if (!texto.trim()) return;
    sendRitsukoChat(texto);
    setTexto("");
  };

  return (
    <div style={{ flex: 1, display: "flex", gap: "12px", overflow: "hidden" }}>
      <div style={{ flex: 2, display: "flex", flexDirection: "column",
                    background: "#050a0b", border: "1px solid var(--dim)" }}>
        <div style={{ padding: "8px 12px", borderBottom: "1px solid var(--dim)",
                      color: "var(--acc)", display: "flex", justifyContent: "space-between" }}>
          <span>RITSUKO · auditoría</span>
          <span style={{ color: "var(--dim)", fontSize: "11px" }}>{ritsukoStatus}</span>
        </div>

        <div style={{ flex: 1, overflowY: "auto", padding: "12px",
                      userSelect: "text", WebkitUserSelect: "text" }}>
          {ritsukoMessages.length === 0 && (
            <p style={{ color: "var(--dim)", fontSize: "12px", lineHeight: 1.6 }}>
              Ritsuko revisa si Naoko corrige bien a Melchior, Balthasar y
              Casper. Solo informa: no aplica cambios, no ejecuta nada y no
              toca la configuración.<br /><br />
              Pídele «¿cómo va el sistema?» o «megaplan» y deja el informe
              escrito para que decidas tú.
            </p>
          )}
          {ritsukoMessages.map((m, i) => (
            <div key={i} style={{ marginBottom: "14px" }}>
              <div style={{ color: m.agent === "RITSUKO" ? "var(--acc)" : "#8aa",
                            fontSize: "11px", marginBottom: "3px" }}>{m.agent}</div>
              <div style={{ color: "#cfe0e4", fontSize: "13px" }}>
                <ReactMarkdown remarkPlugins={[remarkGfm]} components={{ code: renderCode }}>
                  {m.content}
                </ReactMarkdown>
              </div>
            </div>
          ))}
        </div>

        <div style={{ display: "flex", borderTop: "1px solid var(--dim)" }}>
          <input value={texto} onChange={(e) => setTexto(e.target.value)}
                 onKeyDown={(e) => { if (e.key === "Enter") enviar(); }}
                 placeholder="Pregunta a Ritsuko (español o inglés)"
                 style={{ flex: 1, background: "transparent", border: "none",
                          color: "#cfe0e4", padding: "10px", outline: "none" }} />
          <button onClick={enviar}
                  style={{ background: "var(--gr)", color: "var(--acc)",
                           border: "none", padding: "0 18px", cursor: "pointer" }}>
            Auditar
          </button>
        </div>
      </div>

      <div style={{ flex: 1, background: "#050a0b", border: "1px solid var(--dim)",
                    display: "flex", flexDirection: "column" }}>
        <div style={{ padding: "8px 12px", borderBottom: "1px solid var(--dim)",
                      color: "var(--acc)" }}>
          Informes ({informes.length})
        </div>
        <div style={{ flex: 1, overflowY: "auto", padding: "8px",
                      userSelect: "text", WebkitUserSelect: "text" }}>
          {informes.length === 0 && (
            <p style={{ color: "var(--dim)", fontSize: "11px" }}>
              Todavía no hay informes. Cada auditoría deja uno en disco.
            </p>
          )}
          {informes.map((inf) => (
            <div key={inf.nombre} style={{ marginBottom: "10px", fontSize: "11px" }}>
              <div style={{ color: "#cfe0e4" }}>{inf.nombre}</div>
              <div style={{ color: "var(--dim)", wordBreak: "break-all" }}>{inf.ruta}</div>
              <div style={{ color: "var(--dim)" }}>{Math.round(inf.bytes / 1024)} KB</div>
            </div>
          ))}
        </div>
        <button onClick={fetchRitsukoInformes}
                style={{ background: "var(--gr)", color: "var(--acc)", border: "none",
                         borderTop: "1px solid var(--dim)", padding: "8px",
                         cursor: "pointer" }}>
          Actualizar lista
        </button>
      </div>
    </div>
  );
}
