# MAGI System IDE 🖥️🤖

MAGI System IDE es un Entorno de Desarrollo Integrado (IDE) revolucionario, diseñado con una arquitectura de Enjambre de Inteligencias Artificiales colaborativas. Está construido para actuar como un compañero de programación altamente autónomo, analítico, seguro y resiliente.

---

## 🏗️ Arquitectura Completa del Sistema (Diagrama Unidireccional & Ramificaciones Horizontales)

El siguiente gráfico ilustra la arquitectura de **MAGI System IDE**, con un flujo unidireccional vertical de alto nivel que se ramifica horizontalmente en cada proceso y subproceso clave:

```mermaid
graph TD
    %% Estilos Globales
    classDef frontend fill:#1e1e2e,stroke:#89b4fa,stroke-width:2px,color:#cdd6f4;
    classDef kernel fill:#181825,stroke:#cba6f7,stroke-width:2px,color:#cdd6f4;
    classDef swarm fill:#11111b,stroke:#fab387,stroke-width:2px,color:#cdd6f4;
    classDef cloud fill:#181825,stroke:#a6e3a1,stroke-width:2px,color:#cdd6f4;
    classDef devops fill:#1e1e2e,stroke:#f38ba8,stroke-width:2px,color:#cdd6f4;
    classDef storage fill:#11111b,stroke:#94e2d5,stroke-width:2px,color:#cdd6f4;

    %% 1. FRONTEND PROCESS
    subgraph P1["🖥️ Proceso 1: Capa de Presentación (Frontend UI)"]
        direction LR
        UI1["React + Vite UI"] --> UI2["Monaco Code Editor"]
        UI1 --> UI3["Naoko Terminal & Logs"]
        UI1 --> UI4["WebSocket Client (useMagiSocket)"]
    end
    class P1,UI1,UI2,UI3,UI4 frontend;

    %% 2. KERNEL & EVENT BUS PROCESS
    subgraph P2["⚙️ Proceso 2: Núcleo del Sistema (Kernel & Bus Central)"]
        direction LR
        K1["PyWebView App Window"] --> K2["GUIServer (HTTP Static)"]
        K1 --> K3["Kernel Core"]
        K3 --> K4["MagiBus (Event Router)"]
        K4 --> K5["WSServer (JSON RPC Port 20128)"]
    end
    class P2,K1,K2,K3,K4,K5 kernel;

    %% 3. SWARM DEBATE PROCESS
    subgraph P3["🧠 Proceso 3: Orquestador del Enjambre (Swarm Popperiano)"]
        direction LR
        S1["SwarmOrchestrator"] --> S2["Melchior Agent<br/>(Arquitecto / Propuestas)"]
        S1 --> S3["Balthasar Agent<br/>(Crítico / Seguridad)"]
        S1 --> S4["Casper Agent<br/>(Árbitro / Decisión Final)"]
        S1 --> S5["Blackboard Memory<br/>(Estado del Debate)"]
    end
    class P3,S1,S2,S3,S4,S5 swarm;

    %% 4. CLOUD PROVIDER PROCESS
    subgraph P4["☁️ Proceso 4: Red Cloud LLM (FreeCloudLLM & Resiliencia)"]
        direction LR
        C1["FreeCloudLLM Engine"] --> C2["G4F Auto-Router"]
        C2 --> C3["Candidate Model Pool<br/>(gpt-4o / gpt-4o-mini / gpt-4 / llama-3.1 / qwen-2.5)"]
        C2 --> C4["IP Backoff & Cooloff"]
        C2 --> C5["In-Memory Zero-Latency Cache"]
    end
    class P4,C1,C2,C3,C4,C5 cloud;

    %% 5. NAOKO DEVOPS PROCESS
    subgraph P5["🛠️ Proceso 5: Naoko DevOps Autónoma (Mantenimiento & Auto-Patch)"]
        direction LR
        N1["NaokoAgent Listener"] --> N2["Error Diagnostician"]
        N2 --> N3["Local Patch Applicator<br/>(Python / PowerShell)"]
        N3 --> N4["Automated Git Engine<br/>(Add / Commit / Tag / Push)"]
    end
    class P5,N1,N2,N3,N4 devops;

    %% 6. PERSISTENCE PROCESS
    subgraph P6["💾 Proceso 6: Memoria & Persistencia (MagiDatabase)"]
        direction LR
        DB1["MagiDatabase (SQLite)"] --> DB2["Tasks & Debates Logs"]
        DB1 --> DB3["Provider Telemetry & Health"]
        DB1 --> DB4["Naoko Memory Table"]
    end
    class P6,DB1,DB2,DB3,DB4 storage;

    %% FLUJO VERTICAL PRINCIPAL UNIDIRECCIONAL
    P1 -->|1. Interacción de Usuario / Eventos RPC| P2
    P2 -->|2. Despacho de Tareas vía MagiBus| P3
    P3 -->|3. Consultas Cognitivas a LLMs| P4
    P4 -->|4. Reporte de Métricas y Fallos de Red| P6
    P2 -->|5. Suscripción a Errores Críticos| P5
    P5 -->|6. Actualización Autónoma de Código & Release| P6
```

---

## Características Principales 🚀

- **Enjambre de IAs (Swarm):** MAGI no utiliza una sola IA. Integra un enjambre colaborativo (**Melchior**, **Balthasar**, **Casper**) que debaten y analizan el código desde múltiples perspectivas antes de emitir una propuesta final para el usuario.
- **Naoko (DevOps Autónoma):** Una IA de infraestructura independiente (`Naoko`) que supervisa la salud del sistema. Si detecta fallos, caídas de red o excepciones en caliente, **Naoko investiga el error, auto-repara el código fuente localmente y realiza los `git push` a GitHub automáticamente**.
- **Auto-Router Gratuito en la Nube:** MAGI utiliza motores LLM gratuitos en la nube (`G4F`) y los enruta automáticamente. Si una API aplica Rate Limit (429), MAGI aplica enfriamiento inteligente de IP y conmuta suavemente entre modelos candidata (`gpt-4o`, `gpt-4o-mini`, `gpt-4`, `llama-3.1-70b`, `qwen-2.5-coder`).
- **Resiliencia & GUI Integrado:** Aplicación de ventana nativa de alta respuesta basada en `pywebview` y frontend empaquetado en React/Vite.

---

## Instalación y Ejecución ⚡

1. Ve a la pestaña **[Releases](https://github.com/4n0th1ng/MAGI-System-IDE/releases)** en el repositorio de GitHub.
2. Descarga la última versión empaquetada (ej. `MAGI-IDE-v5.zip`).
3. Extrae el archivo ZIP ejecutable.
4. Ejecuta `MAGI-IDE-v5.exe` autónomo.
5. ¡Disfruta del enjambre colaborativo!

---

## Tecnologías 🛠️

- **Backend:** Python 3.10 (Asyncio, SQLite, PyInstaller, WebSockets, PyWebView)
- **Frontend:** React (Vite), TypeScript, TailwindCSS, Monaco Editor
- **IA:** g4f (Auto-routing para motores en la nube como GPT-4o, Claude 3.5, Qwen, Llama 3.1)

---
*MAGI System IDE - Enjambre Autónomo de Inteligencias Artificiales.*


> **Actualización Autónoma (v1.0.0):** Auto-reparación aplicada por Naoko: {'message': '[CRITICAL] magi.core.providers.cloud:
