from __future__ import annotations

import socket
import time

from sga_readiness.checks import Check
from sga_readiness.models import CheckResult, CheckStatus


class PortCheck(Check):
    def __init__(
        self,
        name: str,
        host: str,
        port: int,
        timeout: int = 5,
    ) -> None:
        super().__init__(name)
        self.host = host
        self.port = port
        self.timeout = timeout

    def run(self) -> CheckResult:
        start = time.monotonic()
        try:
            with socket.create_connection(
                (self.host, self.port), timeout=self.timeout
            ):
                pass
        except (OSError, TimeoutError) as e:
            duration = (time.monotonic() - start) * 1000
            return CheckResult(
                name=self.name,
                status=CheckStatus.FAIL,
                message=f"Cannot connect to {self.host}:{self.port} — {e}",
                duration_ms=duration,
            )

        duration = (time.monotonic() - start) * 1000
        return CheckResult(
            name=self.name,
            status=CheckStatus.PASS,
            message=f"Connected to {self.host}:{self.port}",
            duration_ms=duration,
        )
