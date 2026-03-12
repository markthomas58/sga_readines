from __future__ import annotations

import re
import time
import urllib.request
import urllib.error

from sga_readiness.checks import Check
from sga_readiness.models import CheckResult, CheckStatus


class HTTPCheck(Check):
    def __init__(
        self,
        name: str,
        url: str,
        expected_status: int = 200,
        body_pattern: str | None = None,
        timeout: int = 10,
    ) -> None:
        super().__init__(name)
        self.url = url
        self.expected_status = expected_status
        self.body_pattern = body_pattern
        self.timeout = timeout

    def run(self) -> CheckResult:
        start = time.monotonic()
        try:
            req = urllib.request.Request(self.url, method="GET")
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                status_code = resp.status
                body = resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            status_code = e.code
            body = ""
        except Exception as e:
            duration = (time.monotonic() - start) * 1000
            return CheckResult(
                name=self.name,
                status=CheckStatus.FAIL,
                message=f"Request failed: {e}",
                duration_ms=duration,
            )

        duration = (time.monotonic() - start) * 1000

        if status_code != self.expected_status:
            return CheckResult(
                name=self.name,
                status=CheckStatus.FAIL,
                message=f"Expected status {self.expected_status}, got {status_code}",
                duration_ms=duration,
            )

        if self.body_pattern and not re.search(self.body_pattern, body):
            return CheckResult(
                name=self.name,
                status=CheckStatus.FAIL,
                message=f"Body did not match pattern: {self.body_pattern}",
                duration_ms=duration,
            )

        return CheckResult(
            name=self.name,
            status=CheckStatus.PASS,
            message=f"HTTP {status_code} OK",
            duration_ms=duration,
        )
