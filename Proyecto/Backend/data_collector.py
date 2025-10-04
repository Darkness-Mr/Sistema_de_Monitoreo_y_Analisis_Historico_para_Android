import re
import time
from adb_manager import ADBManager

class DataCollector:
    def __init__(self):
        self.adb = ADBManager()
    
    def get_cpu_usage(self):
        """Obtiene el uso de CPU del sistema"""
        try:
            # Comando para obtener uso de CPU
            result = self.adb.execute_command("cat /proc/stat | grep '^cpu '")
            if result:
                # Parsear resultado (simplificado)
                values = result.split()[1:8]
                values = [int(x) for x in values]
                total = sum(values)
                idle = values[3]
                usage = 100 * (total - idle) / total if total > 0 else 0
                return round(usage, 2)
            return 0
        except Exception as e:
            print(f"Error obteniendo CPU: {e}")
            return 0
    
    def get_memory_info(self):
        """Obtiene información de memoria"""
        try:
            result = self.adb.execute_command("cat /proc/meminfo")
            memory_data = {}
            if result:
                for line in result.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        memory_data[key.strip()] = value.strip()
            return memory_data
        except Exception as e:
            print(f"Error obteniendo memoria: {e}")
            return {}
    
    def get_battery_info(self):
        """Obtiene información de batería"""
        try:
            result = self.adb.execute_command("dumpsys battery")
            battery_data = {}
            if result:
                for line in result.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        battery_data[key.strip()] = value.strip()
            return battery_data
        except Exception as e:
            print(f"Error obteniendo batería: {e}")
            return {}
    
    def get_running_processes(self):
        """Obtiene lista de procesos en ejecución"""
        try:
            result = self.adb.execute_command("ps -A")
            processes = []
            if result:
                lines = result.split('\n')[1:]  # Saltar encabezado
                for line in lines:
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 4:
                            processes.append({
                                'user': parts[0],
                                'pid': parts[1],
                                'ppid': parts[2],
                                'name': parts[3]
                            })
            return processes
        except Exception as e:
            print(f"Error obteniendo procesos: {e}")
            return []
    
    def collect_all_metrics(self):
        """Recolecta todas las métricas del sistema"""
        return {
            'timestamp': time.time(),
            'cpu_usage': self.get_cpu_usage(),
            'memory_info': self.get_memory_info(),
            'battery_info': self.get_battery_info(),
            'processes': self.get_running_processes()
        }