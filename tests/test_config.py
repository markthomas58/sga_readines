import pytest
import tempfile
import os

from sga_readiness.config import load_config
from sga_readiness.checks.http import HTTPCheck
from sga_readiness.checks.port import PortCheck
from sga_readiness.checks.config import ConfigCheck
from sga_readiness.checks.dependency import DependencyCheck


def _write_yaml(content: str) -> str:
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False)
    f.write(content)
    f.close()
    return f.name


def test_load_config_http():
    path = _write_yaml("""
checks:
  - name: "API health"
    type: http
    url: "http://localhost:8080/health"
    expected_status: 200
""")
    try:
        checks = load_config(path)
        assert len(checks) == 1
        assert isinstance(checks[0], HTTPCheck)
        assert checks[0].name == "API health"
    finally:
        os.unlink(path)


def test_load_config_port():
    path = _write_yaml("""
checks:
  - name: "DB"
    type: port
    host: "localhost"
    port: 5432
    timeout: 3
""")
    try:
        checks = load_config(path)
        assert len(checks) == 1
        assert isinstance(checks[0], PortCheck)
        assert checks[0].port == 5432
    finally:
        os.unlink(path)


def test_load_config_config_check():
    path = _write_yaml("""
checks:
  - name: "API_KEY set"
    type: config
    env_var: "API_KEY"
""")
    try:
        checks = load_config(path)
        assert len(checks) == 1
        assert isinstance(checks[0], ConfigCheck)
    finally:
        os.unlink(path)


def test_load_config_dependency():
    path = _write_yaml("""
checks:
  - name: "Redis"
    type: dependency
    host: "localhost"
    port: 6379
    timeout: 3
""")
    try:
        checks = load_config(path)
        assert len(checks) == 1
        assert isinstance(checks[0], DependencyCheck)
    finally:
        os.unlink(path)


def test_load_config_multiple():
    path = _write_yaml("""
checks:
  - name: "check1"
    type: http
    url: "http://localhost/health"
  - name: "check2"
    type: port
    host: "localhost"
    port: 5432
""")
    try:
        checks = load_config(path)
        assert len(checks) == 2
    finally:
        os.unlink(path)


def test_load_config_file_not_found():
    with pytest.raises(FileNotFoundError):
        load_config("/nonexistent/path/readiness.yaml")


def test_load_config_invalid_format():
    path = _write_yaml("just a string")
    try:
        with pytest.raises(ValueError, match="top-level 'checks'"):
            load_config(path)
    finally:
        os.unlink(path)


def test_load_config_unknown_type():
    path = _write_yaml("""
checks:
  - name: "bad"
    type: unknown_type
""")
    try:
        with pytest.raises(ValueError, match="Unknown check type"):
            load_config(path)
    finally:
        os.unlink(path)
