/**
 * El eslabón que faltaba: que el markdown con enlaces open: que produce
 * `enlazarRutas` llegue a ser un <a> REAL.
 *
 * Historia (pase de Balthasar, 4-sep-2026): la lógica estaba probada en
 * lib/rutas.test.ts y en vivo no había anclas. Dos culpables encontrados
 * aquí: el sanitizador de react-markdown tumba el esquema open: (arreglado
 * con urlTransform en el componente), y mi PRIMER test de este fichero
 * olvidó pasar onOpenFile — el componente degrada a texto por diseño cuando
 * nadie sabe abrir el fichero, y yo acusé al componente de mi propio bug.
 *
 * Se renderiza a STRING y no a DOM a propósito: cero dependencias nuevas, y
 * lo que hay que comprobar —que el href sobrevive— se ve igual en el HTML
 * serializado.
 */
import { describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import { enlazarRutas as directa } from "../lib/rutas";
import AgentMessageCard from "./AgentMessageCard";

describe("AgentMessageCard — rutas clicables", () => {
  it("con onOpenFile, la ruta llega como ancla con href semántico", () => {
    const html = renderToString(
      <AgentMessageCard
        msg={{ agent: "USER", role: "comando",
               content: directa("que dice docs/BITACORA-OPTIMIZACION.md sobre R6") }}
        telemetry={[]}
        renderCode={() => <code />}
        onOpenFile={() => {}} />);
    expect(html).toContain('href="docs/BITACORA-OPTIMIZACION.md"');
  });

  it("sin onOpenFile no rompe: el enlace se degrada a texto", () => {
    const html = renderToString(
      <AgentMessageCard
        msg={{ agent: "USER", role: "comando",
               content: "mira src/vita/main.c" }}
        telemetry={[]} />);
    expect(html).toContain("src/vita/main.c");
    expect(html).not.toContain("<a");
  });
});
