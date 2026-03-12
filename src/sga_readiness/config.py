from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from sga_readiness.checks import Check
from sga_readiness.checks.http import HTTPCheck
from sga_readiness.checks.port import PortCheck
from sga_readiness.checks.config import ConfigCheck
from sga_readiness.checks.dependency import DependencyCheck

_CHECK_TYPES: dict[str, type[Check]] = {
    "http": HTTPCheck,
    "port": PortCheck,
    "config": ConfigCheck,
    "dependency": DependencyCheck,
}

# Fields that are common to all check types and handled separately.
_COMMON_FIELDS = {"name", "type"}


def load_config(config_path: str) -> list[Check]:
    """Load a readiness YAML config file and return a list of Check instances."""
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict) or "checks" not in data:
        raise ValueError("Config file must contain a top-level 'checks' list")

    checks: list[Check] = []
    for entry in data["checks"]:
        check = _build_check(entry)
        checks.append(check)

    return checks


def _build_check(entry: dict[str, Any]) -> Check:
    """Build a Check instance from a config entry dict."""
    check_type = entry.get("type")
    name = entry.get("name", "unnamed")

    if check_type not in _CHECK_TYPES:
        raise ValueError(
            f"Unknown check type '{check_type}' for check '{name}'. "
            f"Valid types: {', '.join(_CHECK_TYPES)}"
        )

    kwargs = {k: v for k, v in entry.items() if k not in _COMMON_FIELDS}
    return _CHECK_TYPES[check_type](name=name, **kwargs)
