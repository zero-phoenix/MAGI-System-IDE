import concurrent.futures


def _execute_in_isolation(code: str) -> str:
    """
    Ejecuta código limitando el entorno global.
    """
    safe_globals = {"__builtins__": {}}
    safe_locals = {}
    try:
        exec(code, safe_globals, safe_locals)
        return str(safe_locals.get("result", "No result variable defined"))
    except Exception as e:
        return f"Error: {e}"

class SandboxEvaluator:
    """
    Sandbox Determinista (P2.d).
    Aisla la evaluación matemática de 5 segundos de límite (sin red).
    """
    def __init__(self, timeout: int = 5):
        self.timeout = timeout

    def evaluate(self, python_code: str) -> str:
        """
        Ejecuta el bloque matematico en un hilo (o proceso) con timeout.
        """
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        future = executor.submit(_execute_in_isolation, python_code)
        try:
            result = future.result(timeout=self.timeout)
            return result
        except concurrent.futures.TimeoutError:
            return "Error: Timeout exceeded (5s limit)"
