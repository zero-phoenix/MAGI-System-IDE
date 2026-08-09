/**
 * Panel de Naoko (§7.1 — descomposición de App.tsx).
 *
 * Se extrae porque `App.tsx` volvió a pasar de 900 líneas y saltó la guarda de
 * `tests/test_approval.py`. Esa guarda dice explícitamente que el arreglo es
 * EXTRAER un panel, no subir el número — un límite que cede cada vez que
 * estorba no es un límite.
 *
 * El estado del cuadro de texto se muda aquí con el componente: vivía en `App`
 * y solo lo usaba este panel, así que cada letra escrita a Naoko repintaba la
 * aplicación entera.
 */
import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface Props {
  naokoMessages: Array<{ agent: string; content: string }>;
  naokoStatus: string;
  sendNaokoChat: (mensaje: string, imagen: string | null) => void;
  renderCode: any;
  /** Captura pegada con Ctrl+V; la escucha global vive en App. */
  imagen: string | null;
  setImagen: (v: string | null) => void;
}

export default function NaokoPanel({
  naokoMessages, naokoStatus, sendNaokoChat, renderCode, imagen, setImagen,
}: Props) {
  const [texto, setTexto] = useState("");

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%", background: "#050a0b", border: "1px solid var(--dim)" }}>
       <div style={{ padding: "10px", background: "rgba(0,0,0,0.5)", borderBottom: "1px solid var(--dim)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
         <div style={{ color: "#d2a8ff", fontWeight: "bold" }}>NAOKO [DevOps Autónoma & Visión Multimodal]</div>
         <div style={{ color: naokoStatus === "Inactiva" ? "var(--dim)" : "var(--acc)", fontSize: "12px" }}>
           Estado: {naokoStatus}
         </div>
       </div>
       
       {/* `minWidth: 0` y `overflowX: hidden` son lo que impide que un mensaje
           largo de Naoko —un traceback, un diccionario de error sin espacios—
           empuje el ancho de la columna y saque la barra de pestañas de la
           pantalla. Un contenedor flex tiene `min-width: auto` por defecto, es
           decir: se niega a encoger por debajo de su contenido. Con contenido
           que no se puede partir, eso es un ancho infinito. */}
       <div style={{ flex: 1, padding: "15px", overflowY: "auto", overflowX: "hidden",
                     minWidth: 0, display: "flex", flexDirection: "column", gap: "10px" }}>
         {naokoMessages.map((msg, i) => (
            <div key={i} style={{
              background: msg.agent === "USER" ? "rgba(10,20,25,0.9)" : "rgba(30,20,30,0.7)",
              border: `1px solid ${msg.agent === "USER" ? "var(--dim)" : "#d2a8ff"}`,
              padding: "10px",
              borderRadius: "8px",
              alignSelf: msg.agent === "USER" ? "flex-end" : "flex-start",
              maxWidth: "85%",
              minWidth: 0,
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
          {imagen && (
            <div style={{ position: 'relative', display: 'inline-block', marginBottom: '8px' }}>
              <img src={imagen} alt="Adjunto Naoko" style={{ maxHeight: '80px', borderRadius: '4px', border: '1px solid var(--acc)' }} />
              <button 
                onClick={() => setImagen(null)}
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
                  reader.onloadend = () => setImagen(reader.result as string);
                  reader.readAsDataURL(file);
                }
              }} style={{ display: 'none' }} />
            </label>
            <textarea
              className="pf"
              rows={1}
              placeholder="Pregunta a Naoko o adjunta una captura visual..."
              value={texto}
              onChange={(e) => setTexto(e.target.value)}
              onKeyDown={(e) => {
                if(e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  if(texto.trim() || imagen){
                     sendNaokoChat(texto.trim() || "Analizar captura de pantalla adjunta", imagen);
                     setTexto("");
                     setImagen(null);
                  }
                }
              }}
            ></textarea>
            <button className="bt go" onClick={() => {
              if(texto.trim() || imagen){
                 sendNaokoChat(texto.trim() || "Analizar captura de pantalla adjunta", imagen);
                 setTexto("");
                 setImagen(null);
              }
            }}>Enviar ▸</button>
          </div>
       </div>
    </div>
  );
}
