from sga_readiness.__about__ import __version__


def test_version():
    assert __version__ == "0.0.1"


def test_import():
    import sga_readiness

    assert sga_readiness is not None


def test_public_api():
    from sga_readiness import (
        CheckResult,
        CheckStatus,
        ReadinessReport,
        load_config,
        run_checks,
    )

    assert all([CheckResult, CheckStatus, ReadinessReport, load_config, run_checks])
