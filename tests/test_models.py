from sga_readiness.models import CheckResult, CheckStatus, ReadinessReport


def test_check_status_values():
    assert CheckStatus.PASS.value == "PASS"
    assert CheckStatus.FAIL.value == "FAIL"
    assert CheckStatus.WARN.value == "WARN"
    assert CheckStatus.SKIP.value == "SKIP"


def test_check_result_defaults():
    r = CheckResult(name="test", status=CheckStatus.PASS)
    assert r.name == "test"
    assert r.status == CheckStatus.PASS
    assert r.message == ""
    assert r.duration_ms == 0.0


def test_check_result_with_values():
    r = CheckResult(
        name="test",
        status=CheckStatus.FAIL,
        message="something broke",
        duration_ms=42.5,
    )
    assert r.message == "something broke"
    assert r.duration_ms == 42.5


def test_report_passed_all_pass():
    report = ReadinessReport(
        results=[
            CheckResult(name="a", status=CheckStatus.PASS),
            CheckResult(name="b", status=CheckStatus.PASS),
        ]
    )
    assert report.passed is True


def test_report_passed_with_warn():
    report = ReadinessReport(
        results=[
            CheckResult(name="a", status=CheckStatus.PASS),
            CheckResult(name="b", status=CheckStatus.WARN),
        ]
    )
    assert report.passed is True


def test_report_passed_with_skip():
    report = ReadinessReport(
        results=[
            CheckResult(name="a", status=CheckStatus.PASS),
            CheckResult(name="b", status=CheckStatus.SKIP),
        ]
    )
    assert report.passed is True


def test_report_failed():
    report = ReadinessReport(
        results=[
            CheckResult(name="a", status=CheckStatus.PASS),
            CheckResult(name="b", status=CheckStatus.FAIL),
        ]
    )
    assert report.passed is False


def test_report_summary_all_pass():
    report = ReadinessReport(
        results=[
            CheckResult(name="a", status=CheckStatus.PASS),
            CheckResult(name="b", status=CheckStatus.PASS),
        ]
    )
    summary = report.summary()
    assert "READY" in summary
    assert "2 checks" in summary
    assert "2 passed" in summary


def test_report_summary_mixed():
    report = ReadinessReport(
        results=[
            CheckResult(name="a", status=CheckStatus.PASS),
            CheckResult(name="b", status=CheckStatus.FAIL),
            CheckResult(name="c", status=CheckStatus.WARN),
            CheckResult(name="d", status=CheckStatus.SKIP),
        ]
    )
    summary = report.summary()
    assert "NOT READY" in summary
    assert "4 checks" in summary


def test_report_empty():
    report = ReadinessReport()
    assert report.passed is True
    assert "0 checks" in report.summary()
