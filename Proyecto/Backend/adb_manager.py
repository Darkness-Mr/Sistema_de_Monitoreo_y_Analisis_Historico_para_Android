import subprocess

class ADBManager:
    def __init__(self):
        self.device_connected = False
        self.check_adb()

    def check_adb(self) -> bool:
        try:
            r = subprocess.run(['adb', 'version'], capture_output=True, text=True)
            return r.returncode == 0
        except Exception:
            return False

    def _list_devices(self):
        try:
            out = subprocess.run(['adb', 'devices'], capture_output=True, text=True).stdout.splitlines()
            devs = []
            for line in out[1:]:
                line = line.strip()
                if not line:
                    continue
                parts = line.split()
                if len(parts) >= 2:
                    devs.append((parts[0], parts[1]))  # (serial, status)
            return devs
        except Exception:
            return []

    def connect_device(self) -> bool:
        """Marca el estado según 'adb devices'."""
        devs = self._list_devices()
        self.device_connected = any(status == 'device' for _, status in devs)
        return self.device_connected

    def execute_command(self, command: str) -> str:
        """Ejecuta 'adb shell <command>' y devuelve stdout (o '')."""
        try:
            r = subprocess.run(['adb', 'shell', command], capture_output=True, text=True)
            return r.stdout.strip()
        except Exception:
            return ""
