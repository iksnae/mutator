import pytest

from mutator.runner import CommandResult


def test_passing_swift_report(tmp_path):
    from mutator.swift_results import classify_tests

    report = tmp_path / 'results.xml'
    report.write_text('<testsuites><testsuite tests="1" failures="0" errors="0">'
                      '<testcase name="example()" /></testsuite></testsuites>')
    result = CommandResult(code=0, timed_out=False, seconds=0.01, output='')
    assert classify_tests(result, report) == 'survived'


def test_failing_swift_report(tmp_path):
    from mutator.swift_results import classify_tests

    report = tmp_path / 'results.xml'
    report.write_text('<testsuites><testsuite tests="1" failures="1" errors="0">'
                      '<testcase name="example()"><failure message="Expectation failed" />'
                      '</testcase></testsuite></testsuites>')
    result = CommandResult(code=1, timed_out=False, seconds=0.01, output='')
    assert classify_tests(result, report) == 'killed'


@pytest.mark.parametrize('xml,code,timed_out,expected', [
    (None, 0, False, 'error'),
    ('not XML', 0, False, 'error'),
    ('<testsuites />', 0, False, 'error'),
    ('<testsuite tests="1"><testcase><skipped /></testcase></testsuite>', 0, False, 'error'),
    ('<testsuite tests="0"><testcase /></testsuite>', 0, False, 'error'),
    ('<testsuite tests="1"><testcase><failure /></testcase></testsuite>', 0, False, 'error'),
    ('<testsuite tests="1"><testcase /></testsuite>', 1, False, 'error'),
    ('<testsuite tests="1" errors="1"><testcase /></testsuite>', 0, False, 'error'),
    ('<testsuite tests="1"><testcase><error /></testcase></testsuite>', 1, False, 'error'),
    ('<testsuite tests="1"><testcase><failure /></testcase></testsuite>', 127, False, 'error'),
    (None, 124, True, 'timeout'),
])
def test_rejects_unusable_reports(tmp_path, xml, code, timed_out, expected):
    from mutator.swift_results import classify_tests

    report = tmp_path / 'results.xml'
    if xml is not None:
        report.write_text(xml)
    result = CommandResult(code=code, timed_out=timed_out, seconds=0.01, output='')
    assert classify_tests(result, report) == expected


def test_swift_testing_report_suffix(tmp_path):
    from mutator.swift_results import classify_tests

    report = tmp_path / 'results.xml'
    report.with_name('results-swift-testing.xml').write_text(
        '<testsuites><testsuite tests="1"><testcase name="example()" /></testsuite></testsuites>')
    result = CommandResult(code=0, timed_out=False, seconds=0.01, output='')
    assert classify_tests(result, report) == 'survived'


def test_both_frameworks_contribute_failures(tmp_path):
    from mutator.swift_results import classify_tests

    report = tmp_path / 'results.xml'
    report.write_text('<testsuite tests="1"><testcase name="xctest" /></testsuite>')
    report.with_name('results-swift-testing.xml').write_text(
        '<testsuite tests="1"><testcase name="swiftTesting"><failure /></testcase></testsuite>')
    result = CommandResult(code=1, timed_out=False, seconds=0.01, output='')
    assert classify_tests(result, report) == 'killed'
