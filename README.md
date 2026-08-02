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
    classDef user fill:#2c3e50,stroke:#34495e,stroke-width:2px,color:#ecf0f1
    classDef gui fill:#2980b9,stroke:#3498db,stroke-width:2px,color:#fff
    classDef kernel fill:#8e44ad,stroke:#9b59b6,stroke-width:2px,color:#fff
    classDef orch fill:#d35400,stroke:#e67e22,stroke-width:2px,color:#fff
    classDef melchior fill:#27ae60,stroke:#2ecc71,stroke-width:2px,color:#fff
    classDef balthasar fill:#c0392b,stroke:#e74c3c,stroke-width:2px,color:#fff
    classDef casper fill:#f39c12,stroke:#f1c40f,stroke-width:2px,color:#fff
    classDef g4f fill:#34495e,stroke:#7f8c8d,stroke-width:2px,color:#ecf0f1
    classDef os fill:#16a085,stroke:#1abc9c,stroke-width:2px,color:#fff
    classDef db fill:#7f8c8d,stroke:#bdc3c7,stroke-width:2px,color:#fff

    subgraph "NIVEL 0: ENTRADA Y PERSISTENCIA (HOST LOCAL)"
        U(("1. Usuario (Windows)")):::user
        GUI["2. Interfaz Frontend (React)
        • Recibe Instrucción del usuario
        • Renderiza Markdown/JSON
        • Gestiona Pestañas de Historial"]:::gui
        KERNEL["3. Kernel Backend (Python)
        • Intercepta Comandos 
        • Mantiene Bus de Eventos WebSocket"]:::kernel
        DB[("4. Base de Datos Local
        • Persistencia SQLite
        • INSERT OR REPLACE (tasks.id)")]:::db

        U -->|Ingresa Instrucción| GUI
        GUI -->|JSON RPC (WS)| KERNEL
        KERNEL -->|Registra/Recupera Tarea| DB
    end

    subgraph "NIVEL 1: ORQUESTACIÓN Y ENJAMBRE (SWARM)"
        ORCH["5. Swarm Orchestrator (Área 16)
        • Modula a los Agentes
        • Obliga a un mínimo de 3 Rondas
        • Verifica estado: IN_PROGRESS / WAITING"]:::orch
        
        MELCHIOR["6. 🧠 MELCHIOR (Arquitecto)
        • Formula la Propuesta Técnica
        • Escribe Código / Scripts
        • No hace preguntas al usuario"]:::melchior
        
        BALTHASAR["7. 🛡️ BALTHASAR (Crítico)
        • Falsacionismo Riguroso
        • Busca Vulnerabilidades y Cuellos de Botella
        • Ataca el código de Melchior"]:::balthasar
        
        CASPER["8. ⚖️ CASPER (Árbitro Final)
        • Inteligencia Científica Superior
        • Corrige a Balthasar si es necesario
        • Emite Veredicto Final / JSON Limpio"]:::casper

        KERNEL -->|Despacha| ORCH
        ORCH -->|1ra Fase: Crea Plan| MELCHIOR
        MELCHIOR -->|Devuelve Plan| ORCH
        ORCH -->|2da Fase: Critica Plan| BALTHASAR
        BALTHASAR -->|Devuelve Crítica| ORCH
        ORCH -->|Bucle Iterativo Forzado| MELCHIOR
        ORCH -->|3ra Fase (Ronda 3+): Solicita Cierre| CASPER
    end

    subgraph "NIVEL 2: CONEXIÓN CLOUD (PASARELAS)"
        G4F_1["Pasarela (DeepSeek)"]:::g4f
        G4F_2["Pasarela (Claude 3.5 Sonnet)"]:::g4f
        G4F_3["Pasarela (Qwen 2.5)"]:::g4f
        
        MELCHIOR -.->|Petición Async| G4F_1
        BALTHASAR -.->|Petición Async| G4F_2
        CASPER -.->|Petición Async| G4F_3
    end

    subgraph "NIVEL 3: RESOLUCIÓN Y AUTO-EJECUCIÓN NATIVA"
        INTERACTIVE["9. Pausa Interactiva (Casper)
        • Único Agente que habla con el Usuario
        • Solicita Aprobación ('sí')"]:::casper
        
        AUTO_EXEC["10. Extracción y Ejecución
        • Regex extrae bloques (.py, .ps1, .bat)
        • Auto-crea scripts temporales
        • Ejecuta silenciosamente en 2do Plano"]:::os
        
        DISCO[("11. Host OS (Windows)
        • Archivos y Ejecutables Finales")]:::os

        CASPER -->|Decisión: APPROVED| INTERACTIVE
        INTERACTIVE -->|Muestra Feedback Limpio| GUI
        U -->|Escribe 'sí' o 'ejecuta'| GUI
        GUI -->|Transmite Aprobación| KERNEL
        KERNEL -->|Activa Ejecutor| AUTO_EXEC
        AUTO_EXEC -->|Modifica/Ejecuta| DISCO
        AUTO_EXEC -->|Envía Log de Éxito| GUI
    end
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
