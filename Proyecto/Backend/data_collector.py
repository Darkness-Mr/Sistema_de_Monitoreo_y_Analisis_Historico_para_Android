import time
from adb_manager import ADBManager

class DataCollector:
    def __init__(self):
        self.adb = ADBManager()

    # ---- CPU ----
    def _read_proc_stat(self):
        out = self.adb.execute_command("cat /proc/stat | head -n 1")
        if not out.startswith("cpu"):
            return None
        parts = out.split()
        nums = [int(x) for x in parts[1:]]
        total = sum(nums)
        idle = nums[3] + (nums[4] if len(nums) > 4 else 0)
        return total, idle

    def get_cpu_usage(self) -> float:
        a = self._read_proc_stat()
        if not a:
            return 0.0
        time.sleep(0.12)
        b = self._read_proc_stat()
        if not b:
            return 0.0
        total = b[0] - a[0]
        idle = b[1] - a[1]
        if total <= 0:
            return 0.0
        usage = (1.0 - idle / total) * 100.0
        return round(usage, 1)

    # ---- Memoria ----
    def get_memory_info(self) -> dict:
        out = self.adb.execute_command("cat /proc/meminfo")
        info = {}
        for line in out.splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                info[k.strip()] = v.strip()
        return info

    # ---- Batería ----
    def get_battery_info(self) -> dict:
        out = self.adb.execute_command("dumpsys battery")
        info = {}
        for line in out.splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                info[k.strip()] = v.strip()
        return info

    # ---- Procesos ----
    def get_running_processes(self) -> list:
        # Lista simple sin %CPU/%MEM (varía según Android). Suficiente para UI.
        out = self.adb.execute_command("ps -A -o USER,PID,NAME | head -n 30")
        lines = out.splitlines()
        procs = []
        for line in lines[1:]:
            parts = line.split()
            if len(parts) >= 3:
                user = parts[0]
                pid = int(parts[1]) if parts[1].isdigit() else -1
                name = " ".join(parts[2:])
                procs.append({"user": user, "pid": pid, "name": name})
        return procs

    def collect_all_metrics(self) -> dict:
        return {
            "timestamp": time.time(),
            "cpu_usage": self.get_cpu_usage(),
            "memory_info": self.get_memory_info(),
            "battery_info": self.get_battery_info(),
            "processes": self.get_running_processes(),
        }
