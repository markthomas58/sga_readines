import os
import tempfile
import json

from unittest.mock import patch

from sga_readiness.cli import main


def _write_yaml(content: str) -> str:
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False)
    f.write(content)
    f.close()
    return f.name


def test_cli_check_pass(capsys):
    path = _write_yaml("""
checks:
  - name: "MY_VAR"
    type: config
    env_var: "MY_VAR"
""")
    try:
        with patch.dict(os.environ, {"MY_VAR": "hello"}):
            exit_code = main(["check", "--config", path])

        assert exit_code == 0
        output = capsys.readouterr().out
        assert "READY" in output
    finally:
        os.unlink(path)


def test_cli_check_fail(capsys):
    path = _write_yaml("""
checks:
  - name: "MISSING"
    type: config
    env_var: "DEFINITELY_NOT_SET_99999"
""")
    try:
        with patch.dict(os.environ, {}, clear=True):
            exit_code = main(["check", "--config", path])

        assert exit_code == 1
        output = capsys.readouterr().out
        assert "NOT READY" in output
    finally:
        os.unlink(path)


def test_cli_json_format(capsys):
    path = _write_yaml("""
checks:
  - name: "MY_VAR"
    type: config
    env_var: "MY_VAR"
""")
    try:
        with patch.dict(os.environ, {"MY_VAR": "hello"}):
            exit_code = main(["check", "--config", path, "--format", "json"])

        assert exit_code == 0
        output = capsys.readouterr().out
        data = json.loads(output)
        assert data["passed"] is True
        assert len(data["results"]) == 1
        assert data["results"][0]["status"] == "PASS"
    finally:
        os.unlink(path)


def test_cli_verbose(capsys):
    path = _write_yaml("""
checks:
  - name: "MY_VAR"
    type: config
    env_var: "MY_VAR"
""")
    try:
        with patch.dict(os.environ, {"MY_VAR": "hello"}):
            exit_code = main(["check", "--config", path, "--verbose"])

        assert exit_code == 0
        output = capsys.readouterr().out
        assert "ms" in output
    finally:
        os.unlink(path)


def test_cli_missing_config(capsys):
    exit_code = main(["check", "--config", "/nonexistent/file.yaml"])
    assert exit_code == 1
    err = capsys.readouterr().err
    assert "Error" in err


def test_cli_no_command(capsys):
    exit_code = main([])
    assert exit_code == 1
