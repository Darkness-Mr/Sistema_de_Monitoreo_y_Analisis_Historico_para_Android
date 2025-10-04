from flask import Flask, jsonify, render_template
from data_collector import DataCollector
from database import DatabaseManager
import threading
import time

app = Flask(__name__)
data_collector = DataCollector()
db_manager = DatabaseManager()

# Variable global para las métricas actuales
current_metrics = {}

def background_monitoring():
    """Función que corre en segundo plano recolectando métricas"""
    global current_metrics
    while True:
        try:
            metrics = data_collector.collect_all_metrics()
            current_metrics = metrics
            db_manager.save_metrics(metrics)
            time.sleep(5)  # Recolectar cada 5 segundos
        except Exception as e:
            print(f"Error en monitoreo: {e}")
            time.sleep(10)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/current-metrics')
def get_current_metrics():
    """API para obtener métricas actuales"""
    return jsonify(current_metrics)

@app.route('/api/device-status')
def get_device_status():
    """API para verificar estado del dispositivo"""
    status = data_collector.adb.connect_device()
    return jsonify({
        'device_connected': status,
        'adb_available': data_collector.adb.check_adb()
    })

if __name__ == '__main__':
    # Iniciar monitoreo en segundo plano
    monitor_thread = threading.Thread(target=background_monitoring, daemon=True)
    monitor_thread.start()
    
    # Verificar conexión inicial
    data_collector.adb.connect_device()
    
    # Iniciar servidor Flask
    print("🚀 Iniciando servidor de monitoreo...")
    app.run(debug=True, host='0.0.0.0', port=5000)