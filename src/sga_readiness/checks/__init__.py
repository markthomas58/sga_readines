from __future__ import annotations

from abc import ABC, abstractmethod

from sga_readiness.models import CheckResult


class Check(ABC):
    def __init__(self, name: str) -> None:
        self.name = name

    @abstractmethod
    def run(self) -> CheckResult: ...
