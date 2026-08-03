# MAGI System IDE 🖥️🤖

MAGI System IDE es un Entorno de Desarrollo Integrado (IDE) revolucionario, diseñado con una arquitectura de Enjambre de Inteligencias Artificiales integradas. Está construido para actuar como un compañero de programación altamente autónomo, analítico e inteligente.

## Características Principales 🚀

- **Enjambre de IAs (Swarm):** MAGI no utiliza una sola IA. Integra un enjambre colaborativo (Melchior, Balthasar, Casper) que debaten y analizan el código desde múltiples perspectivas antes de emitir una respuesta.
- **Naoko (DevOps Autónoma):** Una IA de infraestructura independiente (`Naoko`) que monitorea la salud del sistema. Si detecta fallos, caídas de red o errores de dependencias, **Naoko investiga el error, auto-repara el código fuente localmente y realiza los `git push` a GitHub automáticamente** sin requerir intervención humana.
- **Memoria Hiperdimensional:** MAGI cuenta con un sistema de memoria (Memgraph) persistente. Las IAs recuerdan contextos pasados y soluciones anteriores a través de una base de datos de grafos de conocimiento.
- **Auto-Router Gratuito en la Nube:** MAGI utiliza proveedores LLM gratuitos (G4F) y los enruta automáticamente. Si una API rate-limitea, MAGI congela el hilo (backoff) y rota los proxies hasta asegurar una conexión estable. Todo de forma transparente.

## Instalación y Ejecución ⚡

1. Ve a la pestaña **Releases** en GitHub.
2. Descarga la última versión (`MAGI-IDE-v5.zip`).
3. Extrae el archivo y ejecuta `MAGI-IDE-v5.exe`.
4. ¡Disfruta del enjambre colaborativo!

## Tecnologías 🛠️

- **Backend:** Python 3.10 (Asyncio, SQLite, PyInstaller, WebSockets)
- **Frontend:** React (Vite), TypeScript, TailwindCSS
- **IA:** g4f (Modelos en la nube gratuitos como GPT-4o, Claude 3.5, Qwen)

---
*Hecho por la inteligencia de MAGI System.*
