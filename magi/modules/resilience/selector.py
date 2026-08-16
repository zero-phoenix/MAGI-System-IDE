class SystemPauseException(Exception):
    """
    Excepción lanzada cuando el sistema agota la cuota de modelos de nube
    y debe entrar en pausa global hasta que se restablezcan (Cortacircuitos de Sistema).
    """
    pass

class CloudSelector:
    """
    Selector de Modelos en Nube (Resiliencia Cloud-Only).
    Gestiona una lista de modelos disponibles. Si un modelo falla, rota al siguiente.
    No permite la caída a modelos locales.
    Si solo quedan 2 modelos disponibles (es decir, falló el antepenúltimo),
    lanza SystemPauseException para congelar el sistema entero.
    """
    def __init__(self, cloud_models: list):
        if not cloud_models:
            raise ValueError("Se requiere al menos un modelo de nube.")
        self.available_models = cloud_models

    def get_next_model(self) -> str:
        """
        Retorna el modelo actual para la tarea.
        """
        if not self.available_models:
            raise SystemPauseException("No hay modelos de nube disponibles.")

        return self.available_models[0]

    def mark_failure(self, model_id: str) -> None:
        """
        Marca un modelo como caído/sin cuota y rota al siguiente.
        Si la lista resultante tiene 2 o menos modelos, lanza SystemPauseException.
        """
        if model_id in self.available_models:
            self.available_models.remove(model_id)

        # Cuando quedan 2 (el antepenúltimo falló), hacemos pausa global.
        # Esos 2 quedan en reserva para culminaciones concretas, no se consumen ciegamente.
        if len(self.available_models) <= 2:
            raise SystemPauseException("Se agotaron los modelos de nube primarios. Pausa Global Activada. Esperando restauración de cuota.")

    def restore_models(self, models: list) -> None:
        """
        Simula el restablecimiento de cuota por tiempo, volviendo a poner
        modelos en la cola.
        """
        for m in models:
            if m not in self.available_models:
                self.available_models.append(m)
