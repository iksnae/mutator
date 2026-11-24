"""Sequential SwiftPM execution in a private source/build/HOME workspace."""

import hashlib
import json
import math
import os
import shlex
import shutil
from dataclasses import asdict
from pathlib import Path
from tempfile import TemporaryDirectory

from mutator.runner import CommandRunner
from mutator.sites import apply_site
from mutator.swift_results import classify_tests, report_paths

_SKIP = {'.git', '.build', 'target', '.metrics', '.venv', 'venv', '__pycache__'}


class SwiftExecutionError(RuntimeError):
    """A Swift worker has not established a trustworthy test control."""


def test_selection(command: str | None) -> list[str]:
    if command is None:
        return []
    words = shlex.split(command)
    if words[:2] != ['swift', 'test']:
        raise ValueError('Swift test commands must start with swift test.')
    selection = words[2:]
    for index in range(0, len(selection), 2):
        pair = selection[index:index + 2]
        if len(pair) != 2 or pair[0] not in {'--filter', '--skip'} or pair[1].startswith('-'):
            raise ValueError('Swift test commands support only --filter and --skip selections.')
    return selection


def _check_links(root: Path) -> None:
    for folder, dirs, names in os.walk(root):
        dirs[:] = [name for name in dirs if name not in _SKIP]
        for name in [*dirs, *names]:
            path = Path(folder) / name
            if path.is_symlink() and not path.resolve().is_relative_to(root):
                raise ValueError(f'Swift workspace symlink escapes project: {path}')


def _workspace(root: Path, base: Path) -> Path:
    _check_links(root)
    project = base / 'project'
    shutil.copytree(root, project, ignore=shutil.ignore_patterns(*_SKIP))
    return project


def _environment(base: Path) -> dict[str, str]:
    env = os.environ.copy()
    paths = {
        'HOME': 'home', 'TMPDIR': 'tmp',
        'CLANG_MODULE_CACHE_PATH': 'clang-cache',
        'SWIFTPM_MODULECACHE_OVERRIDE': 'swift-cache',
    }
    for key, name in paths.items():
        directory = base / name
        directory.mkdir(mode=0o700)
        env[key] = str(directory)
    for key in list(env):
        if key.startswith('GIT_'):
            del env[key]
    env.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL='/dev/null',
               GIT_CONFIG_SYSTEM='/dev/null', GIT_TERMINAL_PROMPT='0')
    return env


def _flags(base: Path) -> list[str]:
    options = []
    for flag, name in [('scratch', 'build'), ('cache', 'cache'),
                       ('config', 'config'), ('security', 'security')]:
        directory = base / name
        directory.mkdir(exist_ok=True)
        options.extend([f'--{flag}-path', str(directory)])
    return options + ['--disable-automatic-resolution', '--disable-dependency-cache', '--jobs', '2']


def _clear_reports(report: Path) -> None:
    for path in report_paths(report):
        path.unlink(missing_ok=True)


def _run(runner, command, project, timeout, phase, mutation, evidence, output):
    result = runner.run(command, project, timeout)
    evidence['commands'].append(dict(phase=phase, mutation=mutation,
                                     command=command, **asdict(result)))
    output.write_text(json.dumps(evidence, indent=2) + '\n')
    return result


def _compile_status(result) -> str | None:
    if result.timed_out:
        return 'timeout'
    if result.code == 1:
        return 'invalid'
    return 'error' if result.code else None


def _mutant(site, original, destination, runner, build, tests, project,
            timeout, report, evidence, output) -> str:
    if original[site.start:site.end].decode() != site.original:
        return 'error'
    destination.write_text(apply_site(original.decode(), site.start, site.end, site.mutant))
    try:
        compiled = _run(runner, build, project, timeout, 'build', site.mutation_id, evidence, output)
        status = _compile_status(compiled)
        if status is not None:
            return status
        _clear_reports(report)
        result = _run(runner, tests, project, timeout, 'test', site.mutation_id, evidence, output)
        return classify_tests(result, report)
    finally:
        destination.write_bytes(original)


def run_swift_mutants(root: Path, source: Path, original: bytes, sites,
                      test_command: str | None = None, timeout_factor: float = 10,
                      verbose: bool = False) -> dict[str, str]:
    selection = test_selection(test_command)
    if not math.isfinite(timeout_factor) or timeout_factor <= 0:
        raise ValueError('Swift timeout factor must be finite and positive.')
    root = root.resolve()
    if not (root / 'Package.swift').is_file():
        raise ValueError('Swift mutation execution requires Package.swift at --root.')
    relative = source.resolve().relative_to(root)
    workers = root / 'target/mutation-workers'
    workers.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix='run-', dir=workers) as directory:
        base = Path(directory)
        project = _workspace(root, base)
        destination = project / relative
        if destination.read_bytes() != original:
            raise SwiftExecutionError('Swift source changed before the control.')
        output_dir = root / 'target/mutation-runs' / base.name
        output_dir.mkdir(parents=True)
        output = output_dir / 'results.json'
        evidence = dict(source=str(relative), source_sha256=hashlib.sha256(original).hexdigest(),
                        inputs={str(p.relative_to(project)): hashlib.sha256(p.read_bytes()).hexdigest()
                                for p in sorted(project.rglob('*')) if p.is_file()},
                        commands=[], outcomes={})
        runner = CommandRunner(verbose=verbose, environment=_environment(base))
        flags = _flags(base)
        report = base / 'results.xml'
        build = ['swift', 'build', *flags, '--build-tests']
        tests = ['swift', 'test', *flags, '--skip-build', '--xunit-output', str(report), *selection]
        compiled = _run(runner, build, project, 300, 'control-build', None, evidence, output)
        if _compile_status(compiled) is not None:
            raise SwiftExecutionError(f'Swift build control failed; see {output}.')
        _clear_reports(report)
        control = _run(runner, tests, project, 300, 'control-test', None, evidence, output)
        if classify_tests(control, report) != 'survived':
            raise SwiftExecutionError(f'Swift test control failed or executed no tests; see {output}.')
        timeout = max(30.0, compiled.seconds * timeout_factor, control.seconds * timeout_factor)
        for site in sites:
            evidence['outcomes'][site.mutation_id] = _mutant(
                site, original, destination, runner, build, tests, project, timeout,
                report, evidence, output)
            output.write_text(json.dumps(evidence, indent=2) + '\n')
        return evidence['outcomes']
