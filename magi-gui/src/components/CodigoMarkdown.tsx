/**
 * Cómo se pinta el código dentro de un mensaje.
 *
 * POR QUÉ VIVE AQUÍ Y NO EN App.tsx
 * =================================
 * Estaba dentro de App.tsx. Al documentar el arreglo de desbordamiento, el
 * fichero pasó de 900 líneas y `test_app_tsx_no_vuelve_a_crecer_sin_limite`
 * lo cazó con el mensaje que toca: «extrae un panel a components/ en lugar de
 * subir este límite».
 *
 * Subir el límite habría sido lo cómodo y habría desactivado el guardián para
 * siempre — que es como los límites dejan de existir sin que nadie lo decida.
 *
 * EL DESBORDAMIENTO QUE ARREGLA
 * =============================
 * Un `<code>` no parte líneas. Cuando Naoko informa de un error pega el
 * diccionario entero en una sola línea:
 *
 *     {'message': '[ERROR] magi.modules.swarm.orchestrator: [SWARM] Error
 *      catastrófico durante orquestación: ninguna variante se completó'}
 *
 * Doscientos caracteres sin un solo espacio: para el navegador es UNA palabra,
 * y una palabra no se parte. El bloque se sale de su tarjeta, la tarjeta
 * ensancha la columna, la columna ensancha la aplicación, y la barra de
 * pestañas —hermana de ese contenido— se va fuera de la pantalla.
 *
 * Resultado: un mensaje de error dejaba media interfaz inalcanzable. Justo
 * cuando más falta hace poder navegarla.
 */

/** Lenguajes cuyo bloque ofrece el botón de ejecutar en la máquina. */
const EJECUTABLES = ["bash", "powershell", "python", "sh", "cmd", "ps1"];

/**
 * Construye el renderizador de `code` para ReactMarkdown.
 *
 * Es una fábrica y no un componente suelto porque necesita `runHostScript`,
 * que vive en App: pasarlo por parámetro evita tener que enhebrarlo por props
 * a través de cada panel que renderice markdown.
 */
export function crearRenderCode(runHostScript: (codigo: string) => void) {
  return function RenderCode({ inline, className, children, ...props }: any) {
    const match = /language-(\w+)/.exec(className || "");
    const codeString = String(children).replace(/\n$/, "");

    // ---------------------------------------------------------- bloque
    if (!inline && match) {
      const ejecutable = EJECUTABLES.includes(match[1].toLowerCase());
      return (
        // `maxWidth: 100%` y `minWidth: 0` mantienen el scroll DENTRO del
        // bloque. Sin ellos `overflowX: auto` no basta: el contenedor sigue
        // reclamando el ancho de su contenido y lo empuja hacia arriba.
        <div style={{ position: "relative", marginTop: "10px", marginBottom: "10px",
                      maxWidth: "100%", minWidth: 0 }}>
          <div style={{ background: "#1a1a1a", padding: "10px", borderRadius: "4px",
                        overflowX: "auto", maxWidth: "100%" }}>
            <code className={className}
                  style={{ color: "#00ff00", fontFamily: "monospace" }} {...props}>
              {children}
            </code>
          </div>
          {ejecutable && (
            <button
              onClick={() => runHostScript(codeString)}
              style={{ position: "absolute", top: "5px", right: "5px",
                       background: "var(--acc)", color: "#000", border: "none",
                       padding: "4px 8px", fontSize: "10px", cursor: "pointer",
                       fontWeight: "bold" }}
            >
              ▶ Ejecutar en PC
            </button>
          )}
        </div>
      );
    }

    // ---------------------------------------------------------- en línea
    return (
      <code
        className={className}
        style={{
          background: "#333", padding: "2px 4px", borderRadius: "2px",
          whiteSpace: "pre-wrap",      // respeta saltos y permite partir
          overflowWrap: "anywhere",    // parte también dentro de una «palabra»
          wordBreak: "break-word",
          maxWidth: "100%",
        }}
        {...props}
      >
        {children}
      </code>
    );
  };
}

export default crearRenderCode;
