# data_collector.py
import re
import time
import subprocess
from typing import Dict, List, Optional

from adb_manager import ADBManager
from database import DatabaseManager


class DataCollector:
    def __init__(self):
        self.adb = ADBManager()
        self.db = DatabaseManager()

    # ---------------------------
    # Helper ADB shell robusto
    # ---------------------------
    def _sh(self, cmd: str, timeout: int = 6) -> str:
        """Ejecuta 'adb shell <cmd>' usando ADBManager si tiene 'shell', si no con subprocess."""
        try:
            if hasattr(self.adb, "shell"):
                return self.adb.shell(cmd, timeout=timeout) or ""
        except Exception:
            pass
        try:
            out = subprocess.run(
                ["adb", "shell", cmd],
                capture_output=True, text=True, timeout=timeout
            )
            return out.stdout or ""
        except Exception:
            return ""

    # ---------------------------
    # Métricas principales
    # ---------------------------
    def get_cpu_usage(self) -> float:
        """
        CPU total % (aprox).
        Primero intenta dumpsys cpuinfo (línea 'TOTAL'), si no, top.
        """
        txt = self._sh("dumpsys cpuinfo")
        m = re.search(r"TOTAL:\s*([\d\.]+)%", txt)
        if m:
            try:
                return float(m.group(1))
            except ValueError:
                pass
        # fallback con top
        top = self._sh("top -n 1 -b")
        # Busca una línea con 'CPU usage from ...' o similar; si no, 0.0
        m2 = re.search(r"([\d\.]+)\s*%?\s*user.*?([\d\.]+)\s*%?\s*kernel", top, re.I)
        if m2:
            try:
                return float(m2.group(1)) + float(m2.group(2))
            except ValueError:
                return 0.0
        return 0.0

    def get_memory_info(self) -> Dict[str, str]:
        """
        Devuelve /proc/meminfo como dict {clave: '12345 kB', ...}
        """
        txt = self._sh("cat /proc/meminfo")
        mem = {}
        for line in txt.splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                mem[k.strip()] = v.strip()
        return mem

    def get_battery_info(self) -> Dict[str, str]:
        """
        Devuelve 'dumpsys battery' como dict. Claves útiles: level, temperature.
        """
        txt = self._sh("dumpsys battery")
        bat = {}
        for line in txt.splitlines():
            line = line.strip()
            if not line or ":" not in line:
                continue
            k, v = line.split(":", 1)
            bat[k.strip()] = v.strip()
        return bat

    # ---------------------------
    # Utilidades procesos/memoria
    # ---------------------------
    @staticmethod
    def _pkg_base(name: str) -> str:
        """Normaliza nombres con sufijos ':service' → com.app"""
        return (name or "").split(":", 1)[0]

    @staticmethod
    def _parse_meminfo_csv(mem_txt: str) -> Dict[str, float]:
        """
        Devuelve {package: mem_mb} desde 'dumpsys meminfo -c'.
        Soporta dos variantes:
          A) proc,PID,NAME,PSS,...
          B) proc,NAME,PID,PSS,...
        """
        mem_by_pkg: Dict[str, float] = {}
        for line in mem_txt.splitlines():
            parts = [p.strip() for p in line.split(",")]
            if not parts or parts[0] != "proc":
                continue

            pid_idx = name_idx = pss_idx = None
            if len(parts) >= 4:
                # Variante A: PID en [1]
                if parts[1].isdigit():
                    pid_idx, name_idx, pss_idx = 1, 2, 3
                # Variante B: PID en [2]
                elif len(parts) >= 4 and parts[2].isdigit():
                    pid_idx, name_idx, pss_idx = 2, 1, 3
            if pid_idx is None:
                continue

            name = DataCollector._pkg_base(parts[name_idx])
            try:
                pss_kb = int(parts[pss_idx])
            except Exception:
                pss_kb = 0
            if name:
                mem_by_pkg[name] = round(pss_kb / 1024.0, 1)  # MB
        return mem_by_pkg

    def _read_proc_rss_mb(self, pid: int) -> Optional[float]:
        """
        Fallback: lee /proc/<pid>/status y extrae VmRSS (kB) -> MB.
        """
        if not pid:
            return None
        txt = self._sh(f"cat /proc/{pid}/status")
        m = re.search(r"^VmRSS:\s+(\d+)\s*kB", txt, re.M)
        if m:
            try:
                kb = int(m.group(1))
                return round(kb / 1024.0, 1)
            except Exception:
                return None
        return None

    # ---------------------------
    # Procesos: CPU% y Mem (MB)
    # ---------------------------
    def get_process_list(self, top_n: int = 15) -> List[Dict]:
        """
        Une 'dumpsys cpuinfo' (CPU%) y 'dumpsys meminfo -c' (PSS KB) por nombre de paquete.
        Si meminfo -c no sirve para algunos, hace fallback con /proc/<pid>/status (VmRSS).
        Filtra apps de usuario. Devuelve top N por CPU.
        """
        procs: Dict[str, Dict] = {}

        # ---- CPU por proceso ----
        cpu_txt = self._sh("dumpsys cpuinfo") or ""
        # Ejemplo: "  2.3% 1234/com.spotify.music: 1.3% user + 1.0% kernel"
        cpu_re = re.compile(r"^\s*([\d\.]+)%\s+(\d+)\/([^:\s]+)", re.M)
        for m in cpu_re.finditer(cpu_txt):
            try:
                cpu = float(m.group(1))
                pid = int(m.group(2))
                rawname = m.group(3)
            except ValueError:
                continue
            pkg = self._pkg_base(rawname)
            procs.setdefault(pkg, {})
            procs[pkg].update({"pid": pid, "cpu": round(cpu, 1)})

        # ---- Memoria por proceso (PSS KB en CSV) ----
        mem_txt = self._sh("dumpsys meminfo -c") or ""
        mem_by_pkg = self._parse_meminfo_csv(mem_txt)

        # Aplica memoria obtenida
        for name, mem_mb in mem_by_pkg.items():
            procs.setdefault(name, {})
            procs[name]["mem_mb"] = mem_mb

        # ---- Construye filas y aplica fallback a VmRSS donde falte ----
        user_prefixes = ("com.", "org.", "io.", "net.", "me.", "co.", "app.", "dev.", "xyz.", "github.")
        rows: List[Dict] = []

        # Si no hubo CPU (raro), aún así arma fila desde memoria
        keys = set(procs.keys()) | set(mem_by_pkg.keys())
        for name in keys:
            if not any(name.startswith(pfx) for pfx in user_prefixes):
                continue
            d = procs.get(name, {})
            pid = d.get("pid")
            cpu = float(d.get("cpu", 0.0))
            mem_mb = d.get("mem_mb")
            if mem_mb is None and pid:
                rss = self._read_proc_rss_mb(int(pid))
                if rss is not None:
                    mem_mb = rss
            rows.append({
                "name": name,
                "pid": pid,
                "cpu": round(cpu, 1),
                "memory": round(float(mem_mb), 1) if mem_mb is not None else 0.0
            })

        rows.sort(key=lambda x: x["cpu"], reverse=True)
        return rows[:top_n]

    # ---------------------------
    # Agregador principal
    # ---------------------------
    def collect_all_metrics(self) -> Dict:
        data = {
            "cpu_usage": self.get_cpu_usage(),
            "memory_info": self.get_memory_info(),
            "battery_info": self.get_battery_info(),
            "timestamp": time.time(),
        }
        try:
            data["processes"] = self.get_process_list(top_n=20)
        except Exception:
            data["processes"] = []
        return data
