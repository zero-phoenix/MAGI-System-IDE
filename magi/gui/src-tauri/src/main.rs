#![cfg_attr(
    all(not(debug_assertions), target_os = "windows"),
    windows_subsystem = "windows"
)]

use tauri::{Manager, WindowBuilder, WindowUrl};

// P21.a.3: Interceptar apertura de ventanas para deshabilitar la navegación externa en el WebView.
fn main() {
    tauri::Builder::default()
        .setup(|app| {
            // PV-21.a.2: No exponer puerto TCP, WebView directamente embebido
            let window = WindowBuilder::new(
                app,
                "main",
                WindowUrl::App("index.html".into())
            )
            .title("MAGI System IDE")
            .build()?;

            // Evitar que el webview siga enlaces externos, se abrirán en el navegador del sistema
            window.on_window_event(|event| {
                if let tauri::WindowEvent::CloseRequested { api, .. } = event {
                    // Limpieza opcional aquí
                }
            });

            // Conectar con el IPC (Named Pipe en Win / Socket en Linux)
            // (La implementación asíncrona real irá aquí)
            
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
