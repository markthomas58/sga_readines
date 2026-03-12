from __future__ import annotations

import os
import re
import time
from pathlib import Path

from sga_readiness.checks import Check
from sga_readiness.models import CheckResult, CheckStatus


class ConfigCheck(Check):
    def __init__(
        self,
        name: str,
        env_var: str | None = None,
        expected_value: str | None = None,
        file_path: str | None = None,
        file_pattern: str | None = None,
    ) -> None:
        super().__init__(name)
        self.env_var = env_var
        self.expected_value = expected_value
        self.file_path = file_path
        self.file_pattern = file_pattern

    def run(self) -> CheckResult:
        start = time.monotonic()

        if self.env_var:
            result = self._check_env_var()
        elif self.file_path:
            result = self._check_file()
        else:
            result = CheckResult(
                name=self.name,
                status=CheckStatus.SKIP,
                message="No env_var or file_path specified",
            )

        result.duration_ms = (time.monotonic() - start) * 1000
        return result

    def _check_env_var(self) -> CheckResult:
        value = os.environ.get(self.env_var)  # type: ignore[arg-type]
        if value is None:
            return CheckResult(
                name=self.name,
                status=CheckStatus.FAIL,
                message=f"Environment variable {self.env_var} is not set",
            )
        if self.expected_value is not None and value != self.expected_value:
            return CheckResult(
                name=self.name,
                status=CheckStatus.FAIL,
                message=f"Environment variable {self.env_var} expected "
                f"'{self.expected_value}', got '{value}'",
            )
        return CheckResult(
            name=self.name,
            status=CheckStatus.PASS,
            message=f"Environment variable {self.env_var} is set",
        )

    def _check_file(self) -> CheckResult:
        path = Path(self.file_path)  # type: ignore[arg-type]
        if not path.exists():
            return CheckResult(
                name=self.name,
                status=CheckStatus.FAIL,
                message=f"File {self.file_path} does not exist",
            )
        if self.file_pattern:
            content = path.read_text(encoding="utf-8", errors="replace")
            if not re.search(self.file_pattern, content):
                return CheckResult(
                    name=self.name,
                    status=CheckStatus.FAIL,
                    message=f"File {self.file_path} does not match pattern: {self.file_pattern}",
                )
        return CheckResult(
            name=self.name,
            status=CheckStatus.PASS,
            message=f"File {self.file_path} exists and is valid",
        )
