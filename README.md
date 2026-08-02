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
## 🗺️ Arquitectura del Sistema: Flujo Integral Unidireccional

El siguiente diagrama detalla minuciosamente el ciclo de vida, integrando cada detalle de los procesos interactivos y lógicos de la arquitectura del Enjambre MAGI:

```mermaid
graph TD
    %% -- ESTILOS --
    classDef mainNode fill:#2c3e50,stroke:#34495e,stroke-width:3px,color:#fff,font-weight:bold
    classDef subNode fill:#2980b9,stroke:#3498db,stroke-width:2px,color:#fff
    classDef swarmNode fill:#8e44ad,stroke:#9b59b6,stroke-width:2px,color:#fff
    classDef cloudNode fill:#34495e,stroke:#7f8c8d,stroke-width:2px,color:#fff,stroke-dasharray: 5 5
    classDef action fill:#27ae60,stroke:#2ecc71,stroke-width:2px,color:#fff
    classDef db fill:#f39c12,stroke:#f1c40f,stroke-width:2px,color:#fff
    classDef terminal fill:#000,stroke:#0f0,stroke-width:2px,color:#0f0

    %% -- EJE VERTICAL PRINCIPAL --
    Start((Inicio)):::mainNode --> F1[1. Recepción & UI]:::mainNode
    F1 --> F2[2. Kernel & Persistencia]:::mainNode
    F2 --> F3[3. Orquestación del Enjambre]:::mainNode
    F3 --> F4[4. Debate Tripartito Asíncrono]:::mainNode
    F4 --> F5[5. Veredicto Final & Aprobación]:::mainNode
    F5 --> F6[6. Auto-Ejecución Nativa]:::mainNode
    F6 --> End((Fin)):::mainNode

    %% -- DETALLES HORIZONTALES (Sub-grafos) --
    
    subgraph "1. Interfaz Gráfica (Frontend React)"
        direction LR
        UI_Input[/Ingreso de Comando/]:::subNode --> UI_Parse[Parseo React]:::subNode
        UI_Parse --> UI_WS{WebSocket}:::subNode
    end
    F1 -.-> UI_Input
    UI_WS -.-> F2

    subgraph "2. Backend Local (Python)"
        direction LR
        K_WS[Recepción WebSocket]:::subNode --> K_Bus((MagiBus)):::subNode
        K_Bus --> K_DB[(SQLite Guardado)]:::db
        K_Bus --> K_Queue[Cola de Tareas]:::subNode
    end
    F2 -.-> K_WS
    K_Queue -.-> F3

    subgraph "3. Preparación del Enjambre (Swarm)"
        direction LR
        O_Init[Init Área 16]:::swarmNode --> O_Rule[Establecer Reglas]:::swarmNode
        O_Rule --> O_Context[Cargar Contexto]:::swarmNode
    end
    F3 -.-> O_Init
    O_Context -.-> F4

    subgraph "4. Interacción de Agentes (Cloud Auto-Routing)"
        direction LR
        A1(MELCHIOR)---A1_Task[Propone Código]:::action
        A2(BALTHASAR)---A2_Task[Critica Vulnerabilidades]:::action
        A3(CASPER)---A3_Task[Arbitra Soluciones]:::action
        
        C1((DeepSeek)):::cloudNode
        C2((Claude 3.5)):::cloudNode
        C3((Qwen 2.5)):::cloudNode
        
        A1_Task -.->|Evasión 429| C1
        A2_Task -.->|Fallback| C2
        A3_Task -.->|Conexión| C3
    end
    F4 -.-> A1
    
    subgraph "5. Resolución Interactiva"
        direction LR
        R_Format[JSON Limpio]:::swarmNode --> R_UI[Renderizado GUI]:::subNode
        R_UI --> R_Wait{¿Usuario Aprueba?}:::action
        R_Wait -->|Escribe 'sí'| R_Pass[Aprobado]:::action
    end
    F5 -.-> R_Format
    R_Pass -.-> F6

    subgraph "6. Modificación del Sistema Operativo"
        direction LR
        E_Regex[Regex Extracción]:::subNode --> E_Files[Crea Temp Scripts]:::subNode
        E_Files --> E_Run>Ejecución Shell / PS]:::terminal
        E_Run --> E_Disk[(Disco Local)]:::db
    end
    F6 -.-> E_Regex
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
