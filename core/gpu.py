"""GPU process inspection module."""
from __future__ import annotations

import logging
import platform
import shutil
import subprocess
from dataclasses import dataclass
from typing import List

LOGGER = logging.getLogger(__name__)


@dataclass
class GPUProcessInfo:
    pid: int
    name: str
    gpu_memory_mb: float | None


class GPUInspector:
    """Attempt to discover processes using the GPU."""

    def inspect(self) -> List[GPUProcessInfo]:
        system = platform.system().lower()
        if system == "windows" and shutil.which("nvidia-smi"):
            return self._run_nvidia_smi()
        if system in {"linux", "darwin"} and shutil.which("nvidia-smi"):
            return self._run_nvidia_smi()
        LOGGER.info("GPU inspection not available on this system")
        return []

    def _run_nvidia_smi(self) -> List[GPUProcessInfo]:
        try:
            output = subprocess.check_output(
                [
                    "nvidia-smi",
                    "--query-compute-apps=pid,process_name,used_memory",
                    "--format=csv,noheader",
                ],
                text=True,
                stderr=subprocess.DEVNULL,
            )
        except (FileNotFoundError, subprocess.CalledProcessError) as exc:
            LOGGER.warning("Unable to execute nvidia-smi: %s", exc)
            return []

        processes: List[GPUProcessInfo] = []
        for line in output.splitlines():
            parts = [part.strip() for part in line.split(",")]
            if len(parts) != 3:
                continue
            try:
                pid = int(parts[0])
                name = parts[1]
                memory_value = parts[2].split()[0]
                memory = float(memory_value)
            except (ValueError, IndexError):
                memory = None
            processes.append(GPUProcessInfo(pid=pid, name=name, gpu_memory_mb=memory))
        return processes
