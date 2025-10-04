import subprocess
import re

class ADBManager:
    def __init__(self):
        self.device_connected = False
        self.check_adb()
    
    def check_adb(self):
        """Verifica si ADB está disponible"""
        try:
            result = subprocess.run(['adb', 'version'], capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ ADB detectado correctamente")
                return True
            else:
                print("❌ ADB no encontrado")
                return False
        except Exception as e:
            print(f"❌ Error al verificar ADB: {e}")
            return False
    
    def connect_device(self):
        """Verifica si hay un dispositivo conectado"""
        try:
            result = subprocess.run(['adb', 'devices'], capture_output=True, text=True)
            devices = [line for line in result.stdout.split('\n') if line.strip() and 'device' in line]
            
            if len(devices) > 1:  # Más de 1 porque la primera línea es "List of devices"
                self.device_connected = True
                print("✅ Dispositivo Android conectado")
                return True
            else:
                print("❌ No hay dispositivos Android conectados")
                return False
        except Exception as e:
            print(f"❌ Error al conectar dispositivo: {e}")
            return False
    
    def execute_command(self, command):
        """Ejecuta un comando ADB y retorna el resultado"""
        try:
            full_command = f"adb shell {command}"
            result = subprocess.run(full_command, shell=True, capture_output=True, text=True)
            return result.stdout.strip()
        except Exception as e:
            print(f"❌ Error ejecutando comando ADB: {e}")
            return None