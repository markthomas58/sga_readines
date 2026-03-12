import os
import tempfile

from unittest.mock import patch, MagicMock

from sga_readiness.checker import run_checks
from sga_readiness.models import CheckStatus


def _write_yaml(content: str) -> str:
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False)
    f.write(content)
    f.close()
    return f.name


def test_run_checks_all_pass():
    path = _write_yaml("""
checks:
  - name: "MY_VAR set"
    type: config
    env_var: "MY_VAR"
""")
    try:
        with patch.dict(os.environ, {"MY_VAR": "hello"}):
            report = run_checks(path)

        assert report.passed is True
        assert len(report.results) == 1
        assert report.results[0].status == CheckStatus.PASS
    finally:
        os.unlink(path)


def test_run_checks_with_failure():
    path = _write_yaml("""
checks:
  - name: "MISSING_VAR"
    type: config
    env_var: "DEFINITELY_NOT_SET_12345"
""")
    try:
        with patch.dict(os.environ, {}, clear=True):
            report = run_checks(path)

        assert report.passed is False
        assert report.results[0].status == CheckStatus.FAIL
    finally:
        os.unlink(path)


def test_run_checks_multiple():
    path = _write_yaml("""
checks:
  - name: "VAR1"
    type: config
    env_var: "VAR1"
  - name: "VAR2"
    type: config
    env_var: "VAR2"
""")
    try:
        with patch.dict(os.environ, {"VAR1": "a", "VAR2": "b"}):
            report = run_checks(path)

        assert report.passed is True
        assert len(report.results) == 2
    finally:
        os.unlink(path)
