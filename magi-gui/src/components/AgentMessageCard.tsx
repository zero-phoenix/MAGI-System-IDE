/**
 * Tarjeta de intervención de un agente (Plan MAGI 9.0 §7.1).
 *
 * Estaba definida DENTRO de App.tsx, que es el ejemplo que el plan usa para
 * explicar por qué había que descomponerlo: un componente anidado en el
 * fichero de 903 líneas no se puede probar por separado, no se puede
 * reutilizar, y obliga a leer entera la pantalla principal para tocarlo.
 */
import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export const AgentMessageCard = ({ msg, telemetry, renderCode }: any) => {
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

export default AgentMessageCard;
