from magi.modules.studio.spec import MediaSpec


class AutoCorrectionLoop:
    """
    Bucle de Autocorrección (P20.b).
    Genera, mide y critica hasta converger o hasta alcanzar meseta.
    """
    def __init__(self, max_versions: int = 4):
        self.max_versions = max_versions

    def run_loop(self, spec: MediaSpec, measurement_function) -> dict:
        """
        measurement_function es un mock de Measure() determinista.
        """
        hard_criteria = spec.get_hard_criteria()

        history = []
        last_failed_count = len(hard_criteria)
        plateau_count = 0

        for v in range(1, self.max_versions + 1):
            # 1. Generar (Simulado)
            # 2. Materializar (Simulado)

            # 3. Medir
            # (measurement_function simula la evaluación y nos dice cuántos fallaron)
            failed_count = measurement_function(v, hard_criteria)

            history.append({"version": v, "failed": failed_count})

            # 4. Chequeo de Convergencia
            if failed_count == 0:
                return {"status": "converged", "version": v, "history": history}

            # 5. Chequeo de Meseta (si no hay mejora por dos versiones seguidas)
            if failed_count >= last_failed_count:
                plateau_count += 1
            else:
                plateau_count = 0

            last_failed_count = failed_count

            if plateau_count >= 2:
                return {"status": "plateau", "version": v, "history": history, "reason": "No hay mejora en criterios medibles tras múltiples versiones."}

        return {"status": "max_versions_reached", "history": history}
