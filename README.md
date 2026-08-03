# MAGI System IDE (V5.0.11)

MAGI System IDE es una interfaz gráfica de escritorio y un orquestador backend potenciado por un enjambre de Inteligencias Artificiales coordinadas, diseñado para operar localmente y comunicarse con proveedores de IA en la nube mediante técnicas de evasión, proporcionando un entorno autónomo de ingeniería de software.

## 🚀 Características Principales

*   **Enjambre de IA Tripartito (Balthasar, Melchior, Casper):** Tres nodos especializados debaten asíncronamente para proponer código, criticar vulnerabilidades y arbitrar decisiones finales.
*   **Red Nube Evasiva (G4F Auto-Routing Resiliente):** Se eluden los bloqueos de Rate Limit (Error 429) mediante intercepción dinámica de modelos caídos. Si un modelo complejo colapsa (ej. Claude/Qwen), MAGI lo enruta nativamente de manera transparente hacia el modelo más estable (`gpt-4o`) para garantizar la persistencia del Enjambre sin API Keys.
*   **Layout Maestro de 3 Columnas:** Una interfaz construida en React de alto rendimiento. Integra gestor de proyectos, visualizador del enjambre y paneles técnicos (Código, Terminal, Pestaña de Configuración Nativa y Telemetría) en una sola vista persistente con texto completamente seleccionable.
*   **Ejecución Git Nativa:** Funcionalidad de autoconexión para clonar y operar sobre repositorios remotos directamente en el disco duro físico (`scratch/`) con *feedback* directo a la consola del IDE.
*   **Telemetría Empírica:** Métrica de desempeño algorítmico, velocidad de inferencia, fallos y densidad de código monitorizada permanentemente en una base de datos SQLite persistente.
*   **Portabilidad Extrema:** Empaquetado completo en un solo ejecutable (`.exe`) sin dependencias mediante PyInstaller y PyWebView (Motor Edge de Windows).

---
## 🗺️ Arquitectura del Sistema: Flujo Integral Detallado

El siguiente diagrama ilustra de manera gráfica, vertical y unidireccional todo el proceso de MAGI System IDE, desde la interacción inicial hasta la ejecución de los comandos sobre el sistema operativo físico, detallando horizontalmente cada capa lógica.

```mermaid
graph TD
    %% -- ESTILOS --
    classDef step fill:#2c3e50,stroke:#34495e,stroke-width:3px,color:#fff,font-weight:bold
    classDef ui fill:#2980b9,stroke:#3498db,stroke-width:2px,color:#fff
    classDef kernel fill:#f39c12,stroke:#f1c40f,stroke-width:2px,color:#fff
    classDef agent fill:#8e44ad,stroke:#9b59b6,stroke-width:2px,color:#fff
    classDef cloud fill:#34495e,stroke:#7f8c8d,stroke-width:2px,color:#fff,stroke-dasharray: 5 5
    classDef os fill:#27ae60,stroke:#2ecc71,stroke-width:2px,color:#fff
    classDef db fill:#000,stroke:#0f0,stroke-width:2px,color:#0f0

    %% --------------------------------------------------------
    %% FASE 1: ENTRADA Y UI
    %% --------------------------------------------------------
    subgraph Fase1 ["1. Interacción Front-End (React)"]
        direction LR
        UI_In[/Comando del Usuario/]:::ui --> UI_Render[Layout Maestro 3 Columnas]:::ui
        UI_Render --> WS_Emit((WebSocket RPC)):::ui
    end
    
    %% --------------------------------------------------------
    %% FASE 2: MIDDLEWARE Y PERSISTENCIA
    %% --------------------------------------------------------
    subgraph Fase2 ["2. Capa Backend & Orquestación Base (Python)"]
        direction LR
        WS_Emit --> K_Receive[Recepción Kernel]:::kernel
        K_Receive --> DB_Log[(SQLite Telemetría & Historial)]:::db
        K_Receive --> K_Queue[Encolado de Tareas]:::kernel
    end

    %% --------------------------------------------------------
    %% FASE 3: ENJAMBRE TRI-ÁRQUICO
    %% --------------------------------------------------------
    subgraph Fase3 ["3. Debate del Enjambre (Auto-Routing)"]
        direction LR
        K_Queue --> O_Init[Orquestador Central]:::agent
        O_Init --> Melchior(🧠 MELCHIOR - Arquitecto):::agent
        Melchior -->|Propuesta Código| Balthasar(🛡️ BALTHASAR - Crítico):::agent
        Balthasar -->|Auditoría| Casper(⚖️ CASPER - Árbitro):::agent
        Casper -->|Decisión Final| O_End[Veredicto]:::agent
        
        %% Conexiones G4F
        Cloud1((DeepSeek / LLaMA3)):::cloud
        Cloud2((Claude 3.5)):::cloud
        Cloud3((GPT-4o / Fallback)):::cloud
        
        Melchior -.->|Petición principal| Cloud1
        Balthasar -.->|Petición principal| Cloud2
        Melchior -.->|Falla 429 -> Enrutamiento dinámico| Cloud3
        Balthasar -.->|Falla 429 -> Enrutamiento dinámico| Cloud3
        Casper -.->|Petición segura| Cloud3
    end

    %% --------------------------------------------------------
    %% FASE 4: VALIDACIÓN INTERACTIVA
    %% --------------------------------------------------------
    subgraph Fase4 ["4. Aprobación y Visualización (Diff)"]
        direction LR
        O_End --> V_Format[Formateo de Cambios]:::ui
        V_Format --> V_Diff{Usuario Revisa Diff Viewer}:::ui
        V_Diff -->|Rechaza| V_Reject[Retorno al Enjambre]:::agent
        V_Diff -->|Aprueba| V_Pass[Autorizado]:::kernel
        V_Reject -.-> Fase3
    end

    %% --------------------------------------------------------
    %% FASE 5: EJECUCIÓN FÍSICA
    %% --------------------------------------------------------
    subgraph Fase5 ["5. Ejecución Host & SO"]
        direction LR
        V_Pass --> OS_Extract[Extracción Regex JS/PY/PS]:::os
        OS_Extract --> OS_Script[Generación Scratch Temp]:::os
        OS_Script --> OS_Run>Ejecución Popen Terminal]:::db
        OS_Run --> OS_Save[(Guardado en Disco / Repositorio)]:::db
    end

    %% -- Flujo principal vertical --
    Fase1 --> Fase2
    Fase2 --> Fase3
    Fase3 --> Fase4
    Fase4 --> Fase5
```



## 📦 Compilación

Para compilar el proyecto en un ejecutable `.exe` portable en Windows:

1. Instalar dependencias en el entorno base:
   `pip install -r requirements.txt`
2. Construir la UI (requiere Node.js):
   `cd magi-gui && npm run build`
3. Ejecutar PyInstaller:
   `powershell -ExecutionPolicy Bypass -File build.ps1`

El resultado estará en `dist/MAGI-IDE-v5.exe`.
