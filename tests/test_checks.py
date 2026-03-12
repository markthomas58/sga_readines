import os
import tempfile
from unittest.mock import patch, MagicMock

from sga_readiness.models import CheckStatus
from sga_readiness.checks.http import HTTPCheck
from sga_readiness.checks.port import PortCheck
from sga_readiness.checks.config import ConfigCheck
from sga_readiness.checks.dependency import DependencyCheck


# --- HTTP Check ---


class TestHTTPCheck:
    def test_pass(self):
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = b'{"status": "ok"}'
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_resp):
            check = HTTPCheck(name="test", url="http://localhost/health")
            result = check.run()

        assert result.status == CheckStatus.PASS
        assert result.duration_ms >= 0

    def test_wrong_status(self):
        mock_resp = MagicMock()
        mock_resp.status = 500
        mock_resp.read.return_value = b"error"
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_resp):
            check = HTTPCheck(
                name="test", url="http://localhost/health", expected_status=200
            )
            result = check.run()

        assert result.status == CheckStatus.FAIL
        assert "500" in result.message

    def test_body_pattern_match(self):
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = b'{"status": "healthy"}'
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_resp):
            check = HTTPCheck(
                name="test",
                url="http://localhost/health",
                body_pattern="healthy",
            )
            result = check.run()

        assert result.status == CheckStatus.PASS

    def test_body_pattern_no_match(self):
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = b'{"status": "degraded"}'
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_resp):
            check = HTTPCheck(
                name="test",
                url="http://localhost/health",
                body_pattern="healthy",
            )
            result = check.run()

        assert result.status == CheckStatus.FAIL
        assert "pattern" in result.message

    def test_connection_error(self):
        with patch(
            "urllib.request.urlopen", side_effect=ConnectionError("refused")
        ):
            check = HTTPCheck(name="test", url="http://localhost/health")
            result = check.run()

        assert result.status == CheckStatus.FAIL
        assert "Request failed" in result.message


# --- Port Check ---


class TestPortCheck:
    def test_pass(self):
        mock_conn = MagicMock()
        mock_conn.__enter__ = lambda s: s
        mock_conn.__exit__ = MagicMock(return_value=False)

        with patch("socket.create_connection", return_value=mock_conn):
            check = PortCheck(name="test", host="localhost", port=5432)
            result = check.run()

        assert result.status == CheckStatus.PASS
        assert "5432" in result.message

    def test_fail(self):
        with patch(
            "socket.create_connection",
            side_effect=OSError("Connection refused"),
        ):
            check = PortCheck(name="test", host="localhost", port=5432, timeout=1)
            result = check.run()

        assert result.status == CheckStatus.FAIL
        assert "Cannot connect" in result.message


# --- Config Check ---


class TestConfigCheck:
    def test_env_var_set(self):
        with patch.dict(os.environ, {"MY_VAR": "hello"}):
            check = ConfigCheck(name="test", env_var="MY_VAR")
            result = check.run()

        assert result.status == CheckStatus.PASS

    def test_env_var_not_set(self):
        with patch.dict(os.environ, {}, clear=True):
            check = ConfigCheck(name="test", env_var="MISSING_VAR")
            result = check.run()

        assert result.status == CheckStatus.FAIL
        assert "not set" in result.message

    def test_env_var_expected_value_match(self):
        with patch.dict(os.environ, {"MY_VAR": "production"}):
            check = ConfigCheck(
                name="test", env_var="MY_VAR", expected_value="production"
            )
            result = check.run()

        assert result.status == CheckStatus.PASS

    def test_env_var_expected_value_mismatch(self):
        with patch.dict(os.environ, {"MY_VAR": "staging"}):
            check = ConfigCheck(
                name="test", env_var="MY_VAR", expected_value="production"
            )
            result = check.run()

        assert result.status == CheckStatus.FAIL
        assert "expected" in result.message

    def test_file_exists(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".conf", delete=False) as f:
            f.write("key=value\n")
            path = f.name

        try:
            check = ConfigCheck(name="test", file_path=path)
            result = check.run()
            assert result.status == CheckStatus.PASS
        finally:
            os.unlink(path)

    def test_file_not_exists(self):
        check = ConfigCheck(name="test", file_path="/nonexistent/file.conf")
        result = check.run()
        assert result.status == CheckStatus.FAIL
        assert "does not exist" in result.message

    def test_file_pattern_match(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".conf", delete=False) as f:
            f.write("database_url=postgres://localhost/db\n")
            path = f.name

        try:
            check = ConfigCheck(
                name="test", file_path=path, file_pattern="database_url="
            )
            result = check.run()
            assert result.status == CheckStatus.PASS
        finally:
            os.unlink(path)

    def test_file_pattern_no_match(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".conf", delete=False) as f:
            f.write("other_key=value\n")
            path = f.name

        try:
            check = ConfigCheck(
                name="test", file_path=path, file_pattern="database_url="
            )
            result = check.run()
            assert result.status == CheckStatus.FAIL
        finally:
            os.unlink(path)

    def test_no_env_or_file(self):
        check = ConfigCheck(name="test")
        result = check.run()
        assert result.status == CheckStatus.SKIP


# --- Dependency Check ---


class TestDependencyCheck:
    def test_pass_port_only(self):
        mock_conn = MagicMock()
        mock_conn.__enter__ = lambda s: s
        mock_conn.__exit__ = MagicMock(return_value=False)

        with patch("socket.create_connection", return_value=mock_conn):
            check = DependencyCheck(
                name="Redis", host="localhost", port=6379
            )
            result = check.run()

        assert result.status == CheckStatus.PASS

    def test_fail_port(self):
        with patch(
            "socket.create_connection",
            side_effect=OSError("Connection refused"),
        ):
            check = DependencyCheck(
                name="Redis", host="localhost", port=6379, timeout=1
            )
            result = check.run()

        assert result.status == CheckStatus.FAIL
        assert "unreachable" in result.message

    def test_pass_with_health_url(self):
        mock_conn = MagicMock()
        mock_conn.__enter__ = lambda s: s
        mock_conn.__exit__ = MagicMock(return_value=False)

        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = b"ok"
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with (
            patch("socket.create_connection", return_value=mock_conn),
            patch("urllib.request.urlopen", return_value=mock_resp),
        ):
            check = DependencyCheck(
                name="API",
                host="localhost",
                port=8080,
                health_url="http://localhost:8080/health",
            )
            result = check.run()

        assert result.status == CheckStatus.PASS

    def test_fail_health_url(self):
        mock_conn = MagicMock()
        mock_conn.__enter__ = lambda s: s
        mock_conn.__exit__ = MagicMock(return_value=False)

        mock_resp = MagicMock()
        mock_resp.status = 500
        mock_resp.read.return_value = b"error"
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with (
            patch("socket.create_connection", return_value=mock_conn),
            patch("urllib.request.urlopen", return_value=mock_resp),
        ):
            check = DependencyCheck(
                name="API",
                host="localhost",
                port=8080,
                health_url="http://localhost:8080/health",
            )
            result = check.run()

        assert result.status == CheckStatus.FAIL
        assert "health check failed" in result.message
