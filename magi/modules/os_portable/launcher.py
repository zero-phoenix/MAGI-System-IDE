class Launcher:
    """
    Lanzador de Ventana Segura (P16.a).
    Supervisa la sesión de QEMU/WASM.
    """
    def launch(self, artifact_path: str, network_enabled: bool = False) -> dict:
        """
        Inicia la sesión.
        """
        session_id = "vm_01"
        
        # Simulación de un intento de fuga (escape)
        # Si la VM intenta acceder a la red pero la red está desactivada, salta la alarma.
        guest_wants_network = True # Simulación de comportamiento huésped hostil
        
        if guest_wants_network and not network_enabled:
             return {
                 "status": "stopped",
                 "event": "vm.escape_attempt",
                 "detail": "Guest tried to send packets while network is NONE"
             }
             
        return {"status": "running", "event": "vm.started"}
