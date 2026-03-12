from __future__ import annotations

import enum
from dataclasses import dataclass, field


class CheckStatus(enum.Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARN = "WARN"
    SKIP = "SKIP"


@dataclass
class CheckResult:
    name: str
    status: CheckStatus
    message: str = ""
    duration_ms: float = 0.0


@dataclass
class ReadinessReport:
    results: list[CheckResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(r.status != CheckStatus.FAIL for r in self.results)

    def summary(self) -> str:
        total = len(self.results)
        passed = sum(1 for r in self.results if r.status == CheckStatus.PASS)
        failed = sum(1 for r in self.results if r.status == CheckStatus.FAIL)
        warned = sum(1 for r in self.results if r.status == CheckStatus.WARN)
        skipped = sum(1 for r in self.results if r.status == CheckStatus.SKIP)

        parts = [f"{total} checks:"]
        if passed:
            parts.append(f"{passed} passed")
        if failed:
            parts.append(f"{failed} failed")
        if warned:
            parts.append(f"{warned} warnings")
        if skipped:
            parts.append(f"{skipped} skipped")

        status = "READY" if self.passed else "NOT READY"
        return f"{status} — {', '.join(parts)}"
