/**
 * Vista previa de artefactos.
 *
 * LO QUE HABÍA
 * ============
 *     <iframe src="http://localhost:3000" style={{ background: "#fff" }} />
 *
 * Una URL fija en el código, apuntando a un servidor que nadie levanta. El
 * usuario abría la pestaña y veía la página de error del navegador —el cuadro
 * blanco con el icono de nube—, encima a fondo blanco dentro de una interfaz
 * negra. No estaba rota: estaba construida sobre una suposición falsa, que
 * MAGI produce servidores web.
 *
 * MAGI produce ARTEFACTOS: un script, una imagen, una página de manga, un
 * informe, un juego. Los deja en el workspace. Eso es lo que esta pestaña
 * enseña ahora, con el más reciente arriba, porque lo que acaba de generar el
 * enjambre es lo que se quiere mirar.
 *
 * El modo URL sigue estando, en su pestaña, para cuando de verdad haya algo
 * escuchando en un puerto.
 */
import { useCallback, useEffect, useMemo, useState } from "react";

type Item = { path: string; nombre: string; tipo: string; bytes: number; mtime: number };
type Contenido = {
  path: string; nombre: string; tipo: string; bytes: number;
  contenido?: string; data_url?: string; mime?: string; error?: string;
};

const ICONO: Record<string, string> = {
  imagen: "▣", web: "◈", video: "▶", audio: "♪",
  documento: "▤", texto: "≡", binario: "⬢",
};

function tamano(b: number) {
  if (b < 1024) return `${b} B`;
  if (b < 1024 * 1024) return `${(b / 1024).toFixed(1)} KB`;
  return `${(b / 1024 / 1024).toFixed(1)} MB`;
}

function cuando(ts: number) {
  const s = Math.max(0, Date.now() / 1000 - ts);
  if (s < 60) return "hace segundos";
  if (s < 3600) return `hace ${Math.floor(s / 60)} min`;
  if (s < 86400) return `hace ${Math.floor(s / 3600)} h`;
  return new Date(ts * 1000).toLocaleDateString();
}

export function PreviewPanel({ listArtifacts, readArtifact }: {
  listArtifacts: (limite?: number) => Promise<any>;
  readArtifact: (path: string) => Promise<any>;
}) {
  const [modo, setModo] = useState<"artefactos" | "url">("artefactos");
  const [items, setItems] = useState<Item[]>([]);
  const [raiz, setRaiz] = useState("");
  const [sel, setSel] = useState<string>("");
  const [cont, setCont] = useState<Contenido | null>(null);
  const [filtro, setFiltro] = useState("");
  const [error, setError] = useState("");
  const [url, setUrl] = useState("http://localhost:3000");
  const [urlCargada, setUrlCargada] = useState("");

  const cargarLista = useCallback(async () => {
    setError("");
    try {
      const r = await listArtifacts(300);
      setItems(r.items || []);
      setRaiz(r.raiz || "");
      // Auto-selección del más reciente: abrir en blanco una pestaña que SÍ
      // tiene contenido es el error que esta pantalla ya cometió una vez.
      if (!sel && r.items?.length) setSel(r.items[0].path);
    } catch (e: any) {
      setError(e?.message || "no se pudo leer el workspace");
    }
  }, [listArtifacts, sel]);

  useEffect(() => { cargarLista(); }, [cargarLista]);

  useEffect(() => {
    if (!sel) { setCont(null); return; }
    let vivo = true;
    readArtifact(sel)
      .then((c) => { if (vivo) setCont(c); })
      .catch((e) => { if (vivo) setCont({ path: sel, nombre: sel, tipo: "texto",
                                          bytes: 0, error: e?.message }); });
    return () => { vivo = false; };
    // Solo `sel`: `readArtifact` es una función nueva en cada render y ponerla
    // aquí relanzaba la lectura del artefacto sin parar. Ver
    // `tests/test_gui_sin_bucles_de_render.py`.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sel]);

  const visibles = useMemo(() => {
    const f = filtro.trim().toLowerCase();
    return f ? items.filter((i) => i.path.toLowerCase().includes(f)) : items;
  }, [items, filtro]);

  const barra = (
    <div style={{ display: "flex", alignItems: "center", gap: "8px",
                  padding: "8px 10px", background: "#050a0b",
                  borderBottom: "1px solid var(--dim)" }}>
      {(["artefactos", "url"] as const).map((m) => (
        <button key={m} className={`bt ${modo === m ? "go" : ""}`}
                onClick={() => setModo(m)}>
          {m === "artefactos" ? "Artefactos" : "URL"}
        </button>
      ))}
      {modo === "artefactos" ? (
        <>
          <input value={filtro} onChange={(e) => setFiltro(e.target.value)}
                 placeholder="Filtrar por nombre o carpeta…"
                 style={{ flex: 1, background: "#000", border: "1px solid var(--gr)",
                          color: "#cfe0e4", padding: "4px 8px", fontSize: "12px" }} />
          <button className="bt" onClick={cargarLista}>Releer</button>
          <span style={{ color: "var(--dim)", fontSize: "11px" }}>
            {items.length} artefacto{items.length === 1 ? "" : "s"}
          </span>
        </>
      ) : (
        <>
          <input value={url} onChange={(e) => setUrl(e.target.value)}
                 onKeyDown={(e) => { if (e.key === "Enter") setUrlCargada(url); }}
                 placeholder="http://localhost:3000"
                 style={{ flex: 1, background: "#000", border: "1px solid var(--gr)",
                          color: "#cfe0e4", padding: "4px 8px", fontSize: "12px" }} />
          <button className="bt go" onClick={() => setUrlCargada(url)}>Cargar</button>
        </>
      )}
    </div>
  );

  if (modo === "url") {
    return (
      <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
        {barra}
        {urlCargada ? (
          <iframe src={urlCargada} title="Vista previa por URL"
                  style={{ flex: 1, width: "100%", border: "none", background: "#fff" }} />
        ) : (
          <div style={{ flex: 1, display: "flex", alignItems: "center",
                        justifyContent: "center", flexDirection: "column",
                        gap: "8px", color: "var(--dim)", background: "#020506" }}>
            <div style={{ fontSize: "34px", opacity: 0.35 }}>◈</div>
            <div style={{ fontSize: "13px" }}>Escribe una dirección y pulsa Cargar.</div>
            <div style={{ fontSize: "11px", maxWidth: "440px", textAlign: "center" }}>
              Este modo sirve para cuando MAGI ha levantado un servidor. Si lo que
              quieres es ver lo que ha generado, usa <b>Artefactos</b>.
            </div>
          </div>
        )}
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
      {barra}
      <div style={{ flex: 1, display: "flex", minHeight: 0 }}>
        {/* ------------------------------------------------ lista ------- */}
        <div style={{ width: "270px", borderRight: "1px solid var(--dim)",
                      overflowY: "auto", background: "#020506" }}>
          {error && <div style={{ padding: "12px", color: "#f87171",
                                  fontSize: "12px" }}>{error}</div>}
          {!error && visibles.length === 0 && (
            <div style={{ padding: "16px", color: "var(--dim)", fontSize: "12px",
                          lineHeight: 1.6 }}>
              Todavía no hay artefactos.<br /><br />
              Aquí aparece lo que el enjambre genera —scripts, imágenes, páginas,
              informes— en cuanto lo escriba en el workspace.
            </div>
          )}
          {visibles.map((it) => (
            <div key={it.path} onClick={() => setSel(it.path)}
                 title={it.path}
                 style={{
                   padding: "8px 10px", cursor: "pointer", fontSize: "12px",
                   borderBottom: "1px solid #0b1416",
                   background: sel === it.path ? "var(--gr)" : "transparent",
                   borderLeft: `3px solid ${sel === it.path ? "var(--acc)" : "transparent"}`,
                 }}>
              <div style={{ display: "flex", gap: "6px", alignItems: "center" }}>
                <span style={{ color: "var(--acc)" }}>{ICONO[it.tipo] || "≡"}</span>
                <span style={{ overflow: "hidden", textOverflow: "ellipsis",
                               whiteSpace: "nowrap" }}>{it.nombre}</span>
              </div>
              <div style={{ color: "var(--dim)", fontSize: "10px", marginTop: "2px" }}>
                {tamano(it.bytes)} · {cuando(it.mtime)}
              </div>
            </div>
          ))}
        </div>

        {/* ---------------------------------------------- contenido ----- */}
        <div style={{ flex: 1, display: "flex", flexDirection: "column",
                      minWidth: 0, background: "#020506" }}>
          {!cont && (
            <div style={{ flex: 1, display: "flex", alignItems: "center",
                          justifyContent: "center", color: "var(--dim)" }}>
              {raiz ? "Elige un artefacto de la izquierda." : "Leyendo el workspace…"}
            </div>
          )}
          {cont && (
            <>
              <div style={{ padding: "8px 12px", borderBottom: "1px solid var(--dim)",
                            display: "flex", gap: "10px", alignItems: "baseline" }}>
                <span style={{ color: "var(--acc)", fontSize: "13px" }}>{cont.nombre}</span>
                <span style={{ color: "var(--dim)", fontSize: "11px" }}>
                  {cont.tipo} · {tamano(cont.bytes)}
                </span>
                <span style={{ color: "var(--dim)", fontSize: "10px",
                               marginLeft: "auto", overflow: "hidden",
                               textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {raiz}
                </span>
              </div>
              <div style={{ flex: 1, overflow: "auto", minHeight: 0 }}>
                {cont.error && (
                  <div style={{ padding: "16px", color: "#fbbf24", fontSize: "12px" }}>
                    {cont.error}
                  </div>
                )}
                {cont.tipo === "imagen" && cont.data_url && (
                  // Tablero de ajedrez detrás: sin él, un PNG con transparencia
                  // sobre fondo negro parece un recuadro vacío.
                  <div style={{ padding: "18px", display: "flex",
                                justifyContent: "center",
                                backgroundImage:
                                  "linear-gradient(45deg,#0a1213 25%,transparent 25%),"
                                  + "linear-gradient(-45deg,#0a1213 25%,transparent 25%),"
                                  + "linear-gradient(45deg,transparent 75%,#0a1213 75%),"
                                  + "linear-gradient(-45deg,transparent 75%,#0a1213 75%)",
                                backgroundSize: "16px 16px",
                                backgroundPosition: "0 0,0 8px,8px -8px,-8px 0" }}>
                    <img src={cont.data_url} alt={cont.nombre}
                         style={{ maxWidth: "100%", imageRendering: "pixelated" }} />
                  </div>
                )}
                {cont.tipo === "web" && cont.contenido && (
                  <iframe srcDoc={cont.contenido} title={cont.nombre}
                          sandbox="allow-scripts"
                          style={{ width: "100%", height: "100%", border: "none",
                                   background: "#fff" }} />
                )}
                {cont.tipo === "video" && cont.data_url && (
                  <div style={{ padding: "18px", display: "flex", justifyContent: "center" }}>
                    <video src={cont.data_url} controls style={{ maxWidth: "100%" }} />
                  </div>
                )}
                {cont.tipo === "audio" && cont.data_url && (
                  <div style={{ padding: "24px" }}>
                    <audio src={cont.data_url} controls style={{ width: "100%" }} />
                  </div>
                )}
                {cont.tipo === "documento" && cont.data_url && (
                  <iframe src={cont.data_url} title={cont.nombre}
                          style={{ width: "100%", height: "100%", border: "none" }} />
                )}
                {cont.tipo === "texto" && cont.contenido !== undefined && (
                  <pre className="selectable" style={{
                    margin: 0, padding: "14px", fontSize: "12px",
                    lineHeight: 1.6, color: "#cfe0e4", whiteSpace: "pre-wrap",
                    wordBreak: "break-word", userSelect: "text",
                  }}>{cont.contenido}</pre>
                )}
                {cont.tipo === "binario" && !cont.error && (
                  <div style={{ padding: "16px", color: "var(--dim)", fontSize: "12px" }}>
                    Binario: no se puede previsualizar. Está en {raiz}.
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default PreviewPanel;
