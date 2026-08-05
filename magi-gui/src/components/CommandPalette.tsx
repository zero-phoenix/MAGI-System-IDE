/**
 * Paleta de comandos con Ctrl+K (Plan MAGI 9.0 §7.3).
 *
 * A estas alturas hay diez pestañas y una docena de acciones repartidas entre
 * ellas. Una capacidad que existe pero hay que ir a buscarla a la cuarta
 * pestaña es, en la práctica, una capacidad que no se usa — una versión suave
 * del problema que ya apareció tres veces aquí: la pieza construida y el
 * camino que no lleva a ella.
 *
 * Cada entrada muestra su grupo a propósito. La paleta debe ENSEÑAR dónde
 * vive cada cosa, no sustituir a la interfaz: si el usuario acaba dependiendo
 * de ella para todo, es que la interfaz no se entiende.
 */
import { useEffect, useMemo, useRef, useState } from "react";
import { Command, filterCommands, moveSelection } from "../lib/commands";

interface Props {
  commands: Command[];
  onRun: (id: string) => void;
}

function Resaltado({ texto, hits }: { texto: string; hits: number[] }) {
  if (!hits.length) return <>{texto}</>;
  const marcados = new Set(hits);
  return (
    <>
      {[...texto].map((ch, i) => (
        <span key={i} style={marcados.has(i)
          ? { color: "var(--acc)", fontWeight: 600 } : undefined}>{ch}</span>
      ))}
    </>
  );
}

export default function CommandPalette({ commands, onRun }: Props) {
  const [abierta, setAbierta] = useState(false);
  const [consulta, setConsulta] = useState("");
  const [sel, setSel] = useState(0);
  const entrada = useRef<HTMLInputElement>(null);

  const resultados = useMemo(
    () => filterCommands(commands, consulta), [commands, consulta]);

  useEffect(() => {
    const alPulsar = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setAbierta((v) => !v);
        setConsulta("");
        setSel(0);
      } else if (e.key === "Escape") {
        setAbierta(false);
      }
    };
    window.addEventListener("keydown", alPulsar);
    return () => window.removeEventListener("keydown", alPulsar);
  }, []);

  useEffect(() => {
    if (abierta) entrada.current?.focus();
  }, [abierta]);

  // La selección se reajusta al filtrar: si estabas en el quinto y ahora hay
  // dos, pulsar Enter ejecutaría algo que no está en pantalla.
  useEffect(() => { setSel(0); }, [consulta]);

  if (!abierta) return null;

  const ejecutar = (i: number) => {
    const elegido = resultados[i];
    if (!elegido) return;             // lista vacía: Enter no puede reventar
    setAbierta(false);
    onRun(elegido.command.id);
  };

  return (
    <div
      onClick={() => setAbierta(false)}
      style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.55)",
               zIndex: 999, display: "flex", justifyContent: "center",
               alignItems: "flex-start", paddingTop: "12vh" }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{ width: "min(620px, 92vw)", background: "#0a1013",
                 border: "1px solid var(--acc)", borderRadius: 5,
                 boxShadow: "0 10px 40px rgba(0,0,0,0.6)", overflow: "hidden" }}
      >
        <input
          ref={entrada}
          value={consulta}
          onChange={(e) => setConsulta(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "ArrowDown") {
              e.preventDefault();
              setSel((s) => moveSelection(s, 1, resultados.length));
            } else if (e.key === "ArrowUp") {
              e.preventDefault();
              setSel((s) => moveSelection(s, -1, resultados.length));
            } else if (e.key === "Enter") {
              e.preventDefault();
              ejecutar(sel);
            }
          }}
          placeholder="Escribe para buscar una acción…  (Esc para cerrar)"
          style={{ width: "100%", padding: "12px 14px", fontSize: 14,
                   background: "transparent", color: "#cfe0e4",
                   border: "none", borderBottom: "1px solid var(--dim)",
                   outline: "none" }}
        />

        <div style={{ maxHeight: "50vh", overflowY: "auto" }}>
          {resultados.length === 0 && (
            <div style={{ padding: 14, color: "var(--dim)", fontSize: 12 }}>
              Nada coincide con «{consulta}».
            </div>
          )}
          {resultados.map((r, i) => (
            <div
              key={r.command.id}
              onMouseEnter={() => setSel(i)}
              onClick={() => ejecutar(i)}
              style={{ padding: "8px 14px", cursor: "pointer", fontSize: 13,
                       display: "flex", justifyContent: "space-between",
                       gap: 12, alignItems: "center",
                       background: i === sel ? "rgba(0,200,255,0.12)" : "transparent" }}
            >
              <span style={{ color: r.command.dangerous ? "#ff9a9a" : "#cfe0e4" }}>
                <Resaltado texto={r.command.title} hits={r.hits} />
              </span>
              <span style={{ color: "var(--dim)", fontSize: 11, flexShrink: 0 }}>
                {r.command.group}
              </span>
            </div>
          ))}
        </div>

        <div style={{ padding: "6px 14px", borderTop: "1px solid var(--dim)",
                      color: "var(--dim)", fontSize: 11 }}>
          ↑↓ moverse · Enter ejecutar · Esc cerrar
        </div>
      </div>
    </div>
  );
}
