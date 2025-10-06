import subprocess
from typing import List, Tuple

class ADBManager:
    """
    Pequeño wrapper para ADB con:
    - timeouts (evita cuelgues)
    - helpers para listar dispositivos/estado
    - API estable: shell(), run_shell() y execute_command() (alias)
    """
    def __init__(self):
        self.device_connected = False
        self.check_adb()

    # -------------------------
    # Helpers internos
    # -------------------------
    def _run(self, args: List[str], timeout: int = 6) -> subprocess.CompletedProcess:
        """Ejecuta un comando del sistema con timeout y captura stdout/stderr."""
        return subprocess.run(args, capture_output=True, text=True, timeout=timeout)

    # -------------------------
    # ADB básico
    # -------------------------
    def check_adb(self) -> bool:
        """Devuelve True si 'adb version' funciona."""
        try:
            r = self._run(['adb', 'version'], timeout=4)
            return r.returncode == 0
        except Exception:
            return False

    def start_server(self) -> bool:
        try:
            r = self._run(['adb', 'start-server'], timeout=5)
            return r.returncode == 0
        except Exception:
            return False

    def kill_server(self) -> bool:
        try:
            r = self._run(['adb', 'kill-server'], timeout=5)
            return r.returncode == 0
        except Exception:
            return False

    # -------------------------
    # Dispositivos
    # -------------------------
    def devices(self) -> List[Tuple[str, str]]:
        """
        Lista dispositivos como (serial, status). Ejemplos de status:
        'device', 'unauthorized', 'offline', 'unknown'.
        """
        try:
            r = self._run(['adb', 'devices'], timeout=4)
            lines = (r.stdout or '').splitlines()
            out: List[Tuple[str, str]] = []
            for line in lines[1:]:  # salta encabezado
                line = line.strip()
                if not line:
                    continue
                parts = line.split()
                if len(parts) >= 2:
                    out.append((parts[0], parts[1]))
            return out
        except Exception:
            return []

    def _list_devices(self) -> List[Tuple[str, str]]:
        # alias para compatibilidad con tu código previo
        return self.devices()

    def connect_device(self) -> bool:
        """
        Devuelve True si hay al menos un dispositivo en estado 'device'.
        Actualiza self.device_connected.
        """
        devs = self.devices()
        self.device_connected = any(status == 'device' for _, status in devs)
        return self.device_connected

    # -------------------------
    # Shell (API estable)
    # -------------------------
    def shell(self, command: str, timeout: int = 6) -> str:
        """
        Ejecuta 'adb shell <command>' y devuelve stdout (sin .strip() agresivo
        para no perder saltos de línea que a veces se usan al parsear).
        """
        try:
            r = self._run(['adb', 'shell', command], timeout=timeout)
            # No lanzamos excepción si returncode != 0; devolvemos lo que haya
            return (r.stdout or '').strip()
        except Exception:
            return ""

    # Alias para compatibilidad con distintos llamadores
    def run_shell(self, command: str, timeout: int = 6) -> str:
        return self.shell(command, timeout=timeout)

    def execute_command(self, command: str) -> str:
        """Alias legacy (tu código original llamaba a esto)."""
        return self.shell(command, timeout=6)
