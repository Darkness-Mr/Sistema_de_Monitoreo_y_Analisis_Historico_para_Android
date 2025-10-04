import sqlite3
import json
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_path='monitoring.db'):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Inicializa las tablas de la base de datos"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabla para métricas del sistema
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                cpu_usage REAL,
                memory_total INTEGER,
                memory_available INTEGER,
                battery_level INTEGER,
                battery_status TEXT
            )
        ''')
        
        # Tabla para procesos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS processes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_id INTEGER,
                process_name TEXT,
                pid INTEGER,
                user TEXT,
                FOREIGN KEY (metric_id) REFERENCES system_metrics (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Base de datos inicializada")
    
    def save_metrics(self, metrics):
        """Guarda las métricas en la base de datos"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Extraer datos de memoria
            mem_total = int(metrics['memory_info'].get('MemTotal', '0 kB').split()[0])
            mem_available = int(metrics['memory_info'].get('MemAvailable', '0 kB').split()[0])
            
            # Extraer datos de batería
            battery_level = int(metrics['battery_info'].get('level', 0))
            battery_status = metrics['battery_info'].get('status', 'unknown')
            
            # Insertar métricas del sistema
            cursor.execute('''
                INSERT INTO system_metrics 
                (cpu_usage, memory_total, memory_available, battery_level, battery_status)
                VALUES (?, ?, ?, ?, ?)
            ''', (metrics['cpu_usage'], mem_total, mem_available, battery_level, battery_status))
            
            metric_id = cursor.lastrowid
            
            # Insertar procesos
            for process in metrics['processes']:
                cursor.execute('''
                    INSERT INTO processes (metric_id, process_name, pid, user)
                    VALUES (?, ?, ?, ?)
                ''', (metric_id, process['name'], process['pid'], process['user']))
            
            conn.commit()
            conn.close()
            print(f"✅ Métricas guardadas - ID: {metric_id}")
            return True
        except Exception as e:
            print(f"❌ Error guardando métricas: {e}")
            return False