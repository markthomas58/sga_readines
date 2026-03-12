from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed

from sga_readiness.config import load_config
from sga_readiness.models import ReadinessReport


def run_checks(config_path: str, *, parallel: bool = True) -> ReadinessReport:
    """Load config and run all checks, returning a ReadinessReport."""
    checks = load_config(config_path)
    report = ReadinessReport()

    if parallel and len(checks) > 1:
        results = [None] * len(checks)
        with ThreadPoolExecutor() as executor:
            future_to_index = {
                executor.submit(check.run): i
                for i, check in enumerate(checks)
            }
            for future in as_completed(future_to_index):
                idx = future_to_index[future]
                results[idx] = future.result()
        report.results = results
    else:
        for check in checks:
            result = check.run()
            report.results.append(result)

    return report
