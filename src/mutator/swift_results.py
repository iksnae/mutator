"""Require executed test-case evidence before counting a Swift test outcome."""

from pathlib import Path
from xml.etree import ElementTree

from mutator.runner import CommandResult


def report_paths(report: Path) -> tuple[Path, Path]:
    """SwiftPM emits separate reports for XCTest and Swift Testing."""
    return report, report.with_name(f"{report.stem}-swift-testing{report.suffix}")


def _validate_suite(suite) -> None:
    cases = list(suite.iter('testcase'))
    tests = int(suite.get('tests', len(cases)))
    errors = int(suite.get('errors', 0))
    failures = int(suite.get('failures', len(list(suite.iter('failure')))))
    if tests != len(cases) or errors != 0 or failures != len(list(suite.iter('failure'))):
        raise ValueError('Inconsistent or errored Swift test report')


def _cases(path: Path) -> list:
    root = ElementTree.parse(path).getroot()
    if root.tag not in {'testsuite', 'testsuites'}:
        raise ValueError('Not a test report')
    for suite in root.iter('testsuite'):
        _validate_suite(suite)
    if root.find('.//error') is not None:
        raise ValueError('Test execution error')
    return [case for case in root.iter('testcase') if case.find('skipped') is None]


def _status(code: int, cases: list) -> str:
    failed = any(case.find('failure') is not None for case in cases)
    if code == 0 and not failed:
        return 'survived'
    if code == 1 and failed:
        return 'killed'
    return 'error'


def classify_tests(result: CommandResult, report: Path) -> str:
    if result.timed_out:
        return 'timeout'
    try:
        cases = [case for path in report_paths(report) if path.is_file() for case in _cases(path)]
    except (OSError, ValueError, ElementTree.ParseError):
        return 'error'
    return _status(result.code, cases) if cases else 'error'
