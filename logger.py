import threading
from datetime import datetime

class Logger:
    _instancia = None
    _lock = threading.Lock()

    def __init__(self):
        self._logs = []

    @classmethod
    def get_instancia(cls):
        if cls._instancia is None:
            with cls._lock:
                if cls._instancia is None:
                    cls._instancia = Logger()
        return cls._instancia

    def log(self, mensaje, nivel="INFO"):
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        except:
            timestamp = "FECHA ERROR"
        entry = f"[{timestamp}] [{nivel}] {mensaje}"
        self._logs.append(entry)
        print(entry)

    def get_logs(self):
        return self._logs.copy()