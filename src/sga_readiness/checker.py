from __future__ import annotations

from sga_readiness.config import load_config
from sga_readiness.models import ReadinessReport


def run_checks(config_path: str) -> ReadinessReport:
    """Load config and run all checks, returning a ReadinessReport."""
    checks = load_config(config_path)
    report = ReadinessReport()

    for check in checks:
        result = check.run()
        report.results.append(result)

    return report
