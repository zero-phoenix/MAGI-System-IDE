class IPCChannelError(Exception):
    pass

class IPCManager:
    """
    Gestión de canales locales (P21.a).
    Verifica que no haya puertos TCP abiertos para la interfaz.
    """
    def check_ports(self, open_ports: list) -> None:
        """
        Valida que la lista de puertos abiertos para UI esté estrictamente vacía.
        (A21-1).
        """
        if open_ports:
            raise IPCChannelError(f"Abortando: Se detectaron puertos no autorizados {open_ports}. El sistema de interfaz debe aislarse mediante pipes/sockets.")
            
    def init_channel(self) -> str:
        return "pipe://local/MagiSystem"
