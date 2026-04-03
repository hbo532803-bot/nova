import os
import shutil
from backend.frontend_api.event_bus import broadcast


class SystemMonitor:

    # ----------------------------------
    # CPU LOAD
    # ----------------------------------

    def get_cpu_load(self):

        try:

            if hasattr(os, "getloadavg"):

                load1, load5, load15 = os.getloadavg()

                return round(load1, 2)

        except Exception:

            pass

        return 0

    # ----------------------------------
    # MEMORY USAGE
    # ----------------------------------

    def get_memory_usage(self):

        try:

            total, used, free = shutil.disk_usage("/")

            percent = round((used / total) * 100, 2)

            return percent

        except Exception:

            return 0

    # ----------------------------------
    # SYSTEM STATUS
    # ----------------------------------

    def get_system_status(self):

        return {
            "cpu_load": self.get_cpu_load(),
            "disk_usage_percent": self.get_memory_usage()
        }

    # ----------------------------------
    # BROADCAST STATUS
    # ----------------------------------

    def broadcast_status(self):

        status = self.get_system_status()

        broadcast({
            "type": "system_status",
            "data": status
        })