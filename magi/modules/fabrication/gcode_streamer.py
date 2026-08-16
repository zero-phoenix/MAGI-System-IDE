import collections


class GCodeStreamer:
    """
    Emisor de G-Code con Ventana de Crédito (P9.A.1).
    Maneja checksums y Resend.
    """
    def __init__(self, W=4):
        self.W = W
        self.history = collections.deque(maxlen=64)
        self.credit = self.W
        self.n = 1

    def stream(self, lines: list[str], simulator) -> dict:
        """
        Envía líneas al simulador consumiendo crédito.
        """
        pointer = 0

        while pointer < len(lines) or self.credit < self.W:
            # Enviar mientras haya crédito
            while self.credit > 0 and pointer < len(lines):
                line = lines[pointer].strip()
                if not line or line.startswith(";"):
                    pointer += 1
                    continue

                # Empaquetar
                cmd = f"N{self.n} {line}"

                # Calcular XOR Checksum
                chk = 0
                for c in cmd:
                    chk ^= ord(c)
                full_cmd = f"{cmd}*{chk}"

                # Enviar y registrar
                self.history.append((self.n, full_cmd))
                simulator.send_line(full_cmd)
                self.credit -= 1
                self.n += 1
                pointer += 1

            # Procesar respuestas del buffer del simulador
            # (El simulador procesa sincrónicamente en esta versión, así que lo inyectamos)
            # En un entorno real leeríamos del socket/tty
            # Aquí, por diseño, enviamos y luego verificamos si el simulador generó un "Resend"
            # Simularemos la lectura de respuestas enviando comandos vacíos para que devuelva "ok"
            resp = simulator.send_line("")
            if "Resend:" in resp:
                # Recargar history
                req_n = int(resp.split(":")[1].strip())
                self.n = req_n
                self.credit = self.W

                # Buscar puntero a línea
                # Para simplificar la demo abstracta: avanzamos el pointer
                pointer -= 1 # Reintentar

            elif "ok" in resp:
                self.credit += 1
                if self.credit > self.W:
                    self.credit = self.W

            elif "Error:Thermal Runaway" in resp:
                # E-STOP
                simulator.send_line("M112")
                return {"status": "failed", "reason": "E-STOP: Thermal Runaway detectado"}

        return {"status": "success"}
