# MAGI System IDE (V5.0.1)

MAGI System IDE es una interfaz gráfica de escritorio y un orquestador backend potenciado por un enjambre de Inteligencias Artificiales coordinadas, diseñado para operar localmente y comunicarse con proveedores de IA en la nube mediante técnicas de evasión, proporcionando un entorno autónomo de ingeniería de software.

## 🚀 Características Principales

*   **Enjambre de IA Tripartito (Balthasar, Melchior, Casper):** Tres nodos especializados debaten asíncronamente para proponer código, criticar vulnerabilidades y arbitrar decisiones finales.
*   **Red Nube Evasiva (G4F Auto-Routing Resiliente):** Se eluden los bloqueos de Rate Limit (Error 429) mediante intercepción dinámica de modelos caídos. Si un modelo complejo colapsa (ej. Claude/Qwen), MAGI lo enruta nativamente de manera transparente hacia el modelo más estable (`gpt-4o`) para garantizar la persistencia del Enjambre sin API Keys.
*   **Layout Maestro de 3 Columnas:** Una interfaz construida en React de alto rendimiento. Integra gestor de proyectos, visualizador del enjambre y paneles técnicos (Código, Terminal, Pestaña de Configuración Nativa y Telemetría) en una sola vista persistente con texto completamente seleccionable.
*   **Ejecución Git Nativa:** Funcionalidad de autoconexión para clonar y operar sobre repositorios remotos directamente en el disco duro físico (`scratch/`) con *feedback* directo a la consola del IDE.
*   **Telemetría Empírica:** Métrica de desempeño algorítmico, velocidad de inferencia, fallos y densidad de código monitorizada permanentemente en una base de datos SQLite persistente.
*   **Portabilidad Extrema:** Empaquetado completo en un solo ejecutable (`.exe`) sin dependencias mediante PyInstaller y PyWebView (Motor Edge de Windows).

---

## 🗺️ Arquitectura del Sistema (Flujos Verticales y Horizontales)

El diseño de MAGI opera de manera bidimensional: **Verticalmente** (flujo de datos desde la máquina física hasta la nube) y **Horizontalmente** (la interacción asíncrona entre los múltiples agentes del Enjambre).

### 1. Flujo Vertical (Hardware -> Nube)

Este flujo detalla cómo una instrucción del usuario viaja desde el cliente React hasta los proveedores de IA.

```mermaid
graph TD
    %% Flujo Vertical
    U((Usuario)) -->|Click / Texto| A(Frontend React - Master Layout)
    A -->|WebSocket| B(Servidor RPC - WSServer)
    B -->|MagiBus Event| C(Kernel Python - Área 0)
    
    subgraph Backend Core
        C -->|SYS_EXEC / git.clone| D(Controlador del SO / Subprocess)
        C -->|Instrucción IAM| E(Swarm Orchestrator - Área 16)
        E --> F{Gestor de Proveedores - G4F}
    end

    F -->|Handshake TLS Nativo| G[Nube LLM 1: DuckDuckGo]
    F -->|Handshake TLS Nativo| H[Nube LLM 2: Blackbox]
    F -->|Handshake TLS Nativo| I[Nube LLM 3: Pollinations]
    
    G & H & I -->|Respuesta Generada| E
    E -->|Telemetría Empírica| J[(MagiDatabase - SQLite)]
    E -->|Broadcasting| B
    B -->|Estado / Mensaje| A
    D -->|Archivos / Logs| A
```

### 2. Flujo Horizontal (Subdivisión Funcional del Enjambre)

Este flujo detalla cómo se subdividen y procesan los problemas internamente a través de los nodos lógicos.

```mermaid
graph LR
    %% Flujo Horizontal
    Task[Nueva Tarea] --> O[Swarm Orchestrator]
    
    subgraph "Debate y Resolución"
        O -->|Inicia Ronda| M(MELCHIOR - Nodo 1)
        M -->|1. Genera Código Inicial / Propuesta| B(BALTHASAR - Nodo 2)
        B -->|2. Falsacionismo / Crítica Feroz| C(CASPER - Nodo 3)
        C -->|3. Arbitraje Final / Ejecución| O
    end
    
    O -->|Iteración Fallida| M
    O -->|Consenso Alcanzado| Output[Decisión Aprobada]
    
    M -.->|Usa| P1(Prov B)
    B -.->|Usa| P2(Prov C)
    C -.->|Usa| P3(Prov A)
```

### Detalles de la Subdivisión Funcional

1.  **Orquestador (Área 16):** Coordina los ciclos de vida de las tareas. Mantiene la memoria transaccional y delega los *prompts* a los agentes correspondientes.
2.  **Melchior (Generación):** Toma la petición bruta y formula la mejor aproximación constructiva (escribir código, diseñar plan).
3.  **Balthasar (Crítica):** Ejecuta un algoritmo de falsacionismo. Trata de romper el código propuesto y encuentra fallas lógicas o de seguridad.
4.  **Casper (Decisión):** Analiza la propuesta y la crítica. Decide si la propuesta se acepta, si necesita parche, o si la ronda debe reiniciarse.
5.  **Pasarela Cloud:** El motor G4F distribuye estas tres mentes en tres llamadas paralelas a proveedores distintos para evitar bloqueos por sobrecarga (Rate Limiting).

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
