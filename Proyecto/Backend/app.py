from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from data_collector import DataCollector
from database import DatabaseManager
import threading
import time
import os

app = Flask(__name__)
# Si sirves el frontend desde Flask, CORS no es estrictamente necesario, pero lo dejamos.
CORS(app)

# --- Rutas del frontend (sirve /Proyecto/Frontend) ---
FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Frontend'))

@app.route("/")
def index():
    # Sirve index.html del frontend
    return send_from_directory(FRONTEND_DIR, "index.html")

@app.route("/<path:path>")
def static_proxy(path: str):
    """Sirve archivos estáticos del frontend (css, js, imágenes, etc.)."""
    file_path = os.path.join(FRONTEND_DIR, path)
    if os.path.exists(file_path):
        return send_from_directory(FRONTEND_DIR, path)
    # Fallback estilo SPA: devuelve index si no existe el archivo solicitado
    return send_from_directory(FRONTEND_DIR, "index.html")

# --- Estado y datos ---
collector = DataCollector()
db = DatabaseManager()

_current = {}                 # último muestreo en memoria
_lock = threading.Lock()      # para proteger _current entre hilos

def _safe_collect_once():
    """Intenta recolectar una muestra; nunca levanta excepción hacia afuera."""
    try:
        if not collector.adb.connect_device():
            # No hay dispositivo "device" en adb
            return {
                "error": "device_not_connected",
                "timestamp": time.time(),
                "cpu_usage": 0.0,
                "memory_info": {},
                "battery_info": {},
                "processes": []
            }
        data = collector.collect_all_metrics()
        # Garantiza campos base aunque algo falle parcialmente
        data.setdefault("cpu_usage", 0.0)
        data.setdefault("memory_info", {})
        data.setdefault("battery_info", {})
        data.setdefault("processes", [])
        data.setdefault("timestamp", time.time())
        return data
    except Exception as e:
        # Nunca dejes caer el hilo por errores intermitentes de adb
        return {
            "error": f"collect_error: {type(e).__name__}",
            "timestamp": time.time(),
            "cpu_usage": 0.0,
            "memory_info": {},
            "battery_info": {},
            "processes": []
        }

def _bg_loop():
    """Hilo en segundo plano: refresca _current cada 1s si hay dispositivo."""
    global _current
    while True:
        data = _safe_collect_once()
        with _lock:
            _current = data
        time.sleep(1.0)

@app.route("/api/status")
def api_status():
    """Disponibilidad de adb y si hay dispositivo conectado (estado 'device')."""
    try:
        adb_ok = collector.adb.check_adb()
        dev_ok = collector.adb.connect_device()
        return jsonify({
            "adb_available": bool(adb_ok),
            "device_connected": bool(dev_ok)
        })
    except Exception:
        return jsonify({
            "adb_available": False,
            "device_connected": False
        }), 200

@app.route("/api/metrics")
def api_metrics():
    """Último muestreo en memoria; si no hay, toma uno ahora mismo."""
    global _current
    with _lock:
        data = _current
    if not data:
        data = _safe_collect_once()
        with _lock:
            _current = data
    return jsonify(data)

@app.route("/api/collect", methods=["POST"])
def api_collect():
    """Recolecta ahora y guarda en SQLite una muestra."""
    data = _safe_collect_once()
    saved = db.save_metrics(data)
    return jsonify({"saved": bool(saved), "metrics": data})

@app.route("/api/ping")
def api_ping():
    return jsonify({"ok": True, "ts": time.time()})

if __name__ == "__main__":
    # Lanza el hilo de muestreo
    threading.Thread(target=_bg_loop, daemon=True).start()
    print("🚀 Servidor Flask en http://0.0.0.0:5000 (Frontend + API)")
    # Escucha en todas las interfaces para que Windows (host) acceda vía localhost
    app.run(host="0.0.0.0", port=5000, debug=True)
