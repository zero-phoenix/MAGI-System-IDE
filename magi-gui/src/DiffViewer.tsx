const DiffViewer = ({ originalCode, newCode, onApprove, onReject }: any) => {
  const oldLines = originalCode ? originalCode.split('\n') : [];
  const newLines = newCode ? newCode.split('\n') : [];
  
  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%", background: "#050a0b", color: "#cfe0e4" }}>
      <div style={{ padding: "10px", background: "rgba(10, 20, 25, 0.9)", borderBottom: "1px solid var(--dim)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h3 style={{ margin: 0, color: "var(--acc)", fontSize: "14px" }}>⚠️ Aprobación de Código Requerida</h3>
        <div style={{ display: "flex", gap: "10px" }}>
          <button className="bt go" style={{ background: "rgba(0, 255, 100, 0.2)", color: "#0f0" }} onClick={onApprove}>Aprobar (Sí)</button>
          <button className="bt go" style={{ background: "rgba(255, 50, 50, 0.2)", color: "#f55" }} onClick={onReject}>Rechazar (No)</button>
        </div>
      </div>
      
      <div style={{ display: "flex", flex: 1, overflow: "hidden" }}>
        <div style={{ flex: 1, borderRight: "1px solid var(--dim)", overflowY: "auto", padding: "10px" }}>
          <div style={{ color: "var(--dim)", fontSize: "12px", marginBottom: "10px" }}>Código Original (Estado Actual)</div>
          <pre style={{ margin: 0, fontFamily: "monospace", fontSize: "12px", color: "#6d8288" }}>
            {oldLines.map((line: string, i: number) => (
              <div key={i} style={{ display: "flex" }}>
                <span style={{ width: "30px", opacity: 0.5, userSelect: "none" }}>{i + 1}</span>
                <span style={{ whiteSpace: "pre-wrap" }}>{line}</span>
              </div>
            ))}
          </pre>
        </div>
        <div style={{ flex: 1, overflowY: "auto", padding: "10px" }}>
          <div style={{ color: "var(--node)", fontSize: "12px", marginBottom: "10px" }}>Código Propuesto (Cambios)</div>
          <pre style={{ margin: 0, fontFamily: "monospace", fontSize: "12px" }}>
            {newLines.map((line: string, i: number) => {
              const isNew = !oldLines.includes(line) && line.trim() !== "";
              return (
                <div key={i} style={{ display: "flex", background: isNew ? "rgba(0, 255, 100, 0.15)" : "transparent" }}>
                  <span style={{ width: "30px", opacity: 0.5, userSelect: "none" }}>{i + 1}</span>
                  <span style={{ whiteSpace: "pre-wrap", color: isNew ? "#0f0" : "#cfe0e4" }}>{line}</span>
                </div>
              );
            })}
          </pre>
        </div>
      </div>
    </div>
  );
};

export default DiffViewer;
