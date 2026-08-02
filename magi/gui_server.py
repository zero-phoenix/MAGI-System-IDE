import os
import sys
import threading
import logging
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer

logger = logging.getLogger(__name__)

class GUIServer:
    def __init__(self, port=1420):
        self.port = port
        self.httpd = None
        self.thread = None

    def start(self):
        # Resolver ruta al dist empaquetado o en desarrollo
        if hasattr(sys, '_MEIPASS'):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            
        dist_path = os.path.join(base_path, 'magi-gui', 'dist')
        
        if not os.path.exists(dist_path):
            logger.error(f"[GUIServer] No se encontró el directorio de frontend estático en: {dist_path}")
            return
            
        class Handler(SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=dist_path, **kwargs)
                
            def log_message(self, format, *args):
                pass

        try:
            self.httpd = TCPServer(("127.0.0.1", self.port), Handler)
            logger.info(f"[GUIServer] Sirviendo Frontend nativo en http://127.0.0.1:{self.port}")
            
            self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
            self.thread.start()
        except Exception as e:
            logger.error(f"[GUIServer] Falló al iniciar el servidor local: {e}")

    def stop(self):
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()
