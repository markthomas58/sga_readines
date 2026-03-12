from __future__ import annotations

import time

from sga_readiness.checks import Check
from sga_readiness.checks.port import PortCheck
from sga_readiness.checks.http import HTTPCheck
from sga_readiness.models import CheckResult, CheckStatus


class DependencyCheck(Check):
    def __init__(
        self,
        name: str,
        host: str,
        port: int,
        timeout: int = 5,
        health_url: str | None = None,
        expected_status: int = 200,
    ) -> None:
        super().__init__(name)
        self.host = host
        self.port = port
        self.timeout = timeout
        self.health_url = health_url
        self.expected_status = expected_status

    def run(self) -> CheckResult:
        start = time.monotonic()

        port_result = PortCheck(
            name=f"{self.name} (port)",
            host=self.host,
            port=self.port,
            timeout=self.timeout,
        ).run()

        if port_result.status == CheckStatus.FAIL:
            duration = (time.monotonic() - start) * 1000
            return CheckResult(
                name=self.name,
                status=CheckStatus.FAIL,
                message=f"Dependency unreachable: {port_result.message}",
                duration_ms=duration,
            )

        if self.health_url:
            http_result = HTTPCheck(
                name=f"{self.name} (health)",
                url=self.health_url,
                expected_status=self.expected_status,
                timeout=self.timeout,
            ).run()

            duration = (time.monotonic() - start) * 1000
            if http_result.status == CheckStatus.FAIL:
                return CheckResult(
                    name=self.name,
                    status=CheckStatus.FAIL,
                    message=f"Dependency health check failed: {http_result.message}",
                    duration_ms=duration,
                )

        duration = (time.monotonic() - start) * 1000
        return CheckResult(
            name=self.name,
            status=CheckStatus.PASS,
            message=f"Dependency {self.host}:{self.port} is reachable",
            duration_ms=duration,
        )
