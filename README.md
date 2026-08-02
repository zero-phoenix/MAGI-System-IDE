# MAGI System IDE (V5.0.9)

MAGI System IDE es una interfaz gráfica de escritorio y un orquestador backend potenciado por un enjambre de Inteligencias Artificiales coordinadas, diseñado para operar localmente y comunicarse con proveedores de IA en la nube mediante técnicas de evasión, proporcionando un entorno autónomo de ingeniería de software.

## 🚀 Características Principales

*   **Enjambre de IA Tripartito (Balthasar, Melchior, Casper):** Tres nodos especializados debaten asíncronamente para proponer código, criticar vulnerabilidades y arbitrar decisiones finales.
*   **Red Nube Evasiva (G4F Auto-Routing Resiliente):** Se eluden los bloqueos de Rate Limit (Error 429) mediante intercepción dinámica de modelos caídos. Si un modelo complejo colapsa (ej. Claude/Qwen), MAGI lo enruta nativamente de manera transparente hacia el modelo más estable (`gpt-4o`) para garantizar la persistencia del Enjambre sin API Keys.
*   **Layout Maestro de 3 Columnas:** Una interfaz construida en React de alto rendimiento. Integra gestor de proyectos, visualizador del enjambre y paneles técnicos (Código, Terminal, Pestaña de Configuración Nativa y Telemetría) en una sola vista persistente con texto completamente seleccionable.
*   **Ejecución Git Nativa:** Funcionalidad de autoconexión para clonar y operar sobre repositorios remotos directamente en el disco duro físico (`scratch/`) con *feedback* directo a la consola del IDE.
*   **Telemetría Empírica:** Métrica de desempeño algorítmico, velocidad de inferencia, fallos y densidad de código monitorizada permanentemente en una base de datos SQLite persistente.
*   **Portabilidad Extrema:** Empaquetado completo en un solo ejecutable (`.exe`) sin dependencias mediante PyInstaller y PyWebView (Motor Edge de Windows).

---

## 🗺️ Arquitectura del Sistema: Flujo Integral Unidireccional

A continuación se detalla el ciclo de vida de una instrucción en MAGI System IDE, desde la entrada del usuario en su PC local hasta el arbitraje final, pasando por la nube.

```mermaid
graph TD
    %% -- CAPA CLIENTE LOCAL (WINDOWS) --
    U(("Usuario (Windows)")) -->|Ingresa Instrucción o Carga Archivo| GUI["Frontend (React / Master Layout)"]
    GUI -->|WebSocket (JSON RPC)| KERNEL["Kernel (Área 0)"]
    
    %% -- CAPA KERNEL Y RUTEO --
    KERNEL -->|Filtra Comandos (SYS_EXEC_HOST)| SO["Sistema Operativo Local"]
    SO -->|Crea Archivos / Ejecuta Scripts| DISCO[("Disco Duro (scratch/)")]
    KERNEL -->|Despacha Tarea de IA| ORCH["Swarm Orchestrator (Área 16)"]
    
    %% -- CAPA ENJAMBRE Y NUBE --
    ORCH -->|1. Solicita Propuesta Inicial| MELCHIOR["🧠 MELCHIOR (Arquitecto)"]
    MELCHIOR -->|Consulta| G4F_1["Pasarela G4F (DeepSeek)"]
    G4F_1 -->|Retorna Código/Plan| ORCH
    
    ORCH -->|2. Envía Propuesta para Crítica| BALTHASAR["🛡️ BALTHASAR (Seguridad/Crítica)"]
    BALTHASAR -->|Consulta| G4F_2["Pasarela G4F (Claude 3.5 Sonnet)"]
    G4F_2 -->|Retorna Vulnerabilidades| ORCH
    
    ORCH -->|Fuerza Mejora Continua| MELCHIOR
    
    ORCH -->|3. Tras 3 rondas mínimas, solicita Veredicto| CASPER["⚖️ CASPER (Árbitro Final)"]
    CASPER -->|Consulta| G4F_3["Pasarela G4F (Qwen 2.5)"]
    G4F_3 -->|Retorna Síntesis Final| ORCH
    
    %% -- CAPA INTERACTIVA --
    ORCH -->|4. Solicita Aprobación| GUI_INTERACT["Casper Pausa el Debate"]
    GUI_INTERACT -->|Muestra al Usuario| U
    U -->|Aprueba (Ejecutar)| GUI_INTERACT
    GUI_INTERACT -->|Publica Veredicto| SO
```

### Detalle del Proceso (Horizontal)
- **1. Inicialización (Usuario -> Kernel):** El usuario introduce una meta (ej. "Crea el juego de Tetris en Python"). La UI manda un WebSocket al Kernel. MAGI se comporta de manera *Agentic* reconociendo su host Windows y su acceso a disco.
- **2. Propuesta Arquitectónica (Melchior):** Sin dudar ni hacer preguntas, Melchior diseña el plan técnico y redacta el script/código necesario usando su proveedor de IA asíncrono.
- **3. Falsacionismo Riguroso (Balthasar):** Balthasar intenta romper la propuesta, buscando cuellos de botella o errores. No habla con el usuario, solo ataca el código de Melchior.
- **4. Iteración Forzada (Regla de 3 Rondas):** El Orquestador obliga a que Melchior y Balthasar repitan el ciclo (Corregir -> Criticar) al menos 3 veces, asegurando un nivel de ingeniería ultra refinado.
- **5. Aprobación Interactiva (Casper):** Al final del debate, Casper consolida la versión definitiva. Como único agente autorizado, te pregunta directamente en pantalla: *"¿Apruebas ejecutar esto?"*. Si dices "sí", habilita la ejecución en tu disco.

---

## 📦 Compilación

Para compilar el proyecto en un ejecutable `.exe` portable en Windows:

1. Instalar dependencias en el entorno base:
   `pip install -r requirements.txt`
2. Construir la UI (requiere Node.js):
   `cd magi-gui && npm run build`
3. Ejecutar PyInstaller:
   `powershell -ExecutionPolicy Bypass -File build.ps1`

El resultado estará en `dist/MAGI-IDE-v5.exe`.
