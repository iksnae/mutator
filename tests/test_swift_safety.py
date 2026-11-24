import shutil
from pathlib import Path

import pytest

from mutator.cli import parse_args
from mutator.swift_runner import run_swift_mutants


@pytest.mark.parametrize('alias', ['target', 'target/mutation-workers', 'target/mutation-runs', 'Alias.swift'])
def test_swift_rejects_unsafe_paths(tmp_path, alias):
    root = tmp_path / 'project'
    shutil.copytree(Path(__file__).parent / 'fixtures/swift', root)
    source = root / 'Sources/Demo/Demo.swift'
    link = root / alias
    link.parent.mkdir(parents=True, exist_ok=True)
    destination = source if alias == 'Alias.swift' else tmp_path / 'outside'
    if alias != 'Alias.swift':
        destination.mkdir()
    link.symlink_to(destination)
    with pytest.raises(ValueError, match='symlink|escape'):
        run_swift_mutants(root, source, source.read_bytes(), [])
    if alias != 'Alias.swift':
        assert list(destination.iterdir()) == []


@pytest.mark.parametrize('value', ['nan', 'inf', '1e309'])
def test_nonfinite_cli_timeouts_are_rejected(value):
    options = parse_args(['--timeout-factor', value])
    assert options.action == 'help'
    assert options.exit_code == 1


def test_timeout_product_overflow_is_rejected(tmp_path, monkeypatch):
    from mutator.runner import CommandResult

    root = tmp_path / 'project'
    shutil.copytree(Path(__file__).parent / 'fixtures/swift', root)
    source = root / 'Sources/Demo/Demo.swift'

    class ControlRunner:
        def __init__(self, **_kwargs):
            pass

        def run(self, command, _cwd, _timeout):
            if '--xunit-output' in command:
                report = Path(command[command.index('--xunit-output') + 1])
                report.write_text('<testsuite tests="1"><testcase /></testsuite>')
            return CommandResult(code=0, timed_out=False, seconds=100.0, output='')

    monkeypatch.setattr('mutator.swift_runner.CommandRunner', ControlRunner)
    with pytest.raises(ValueError, match='timeout'):
        run_swift_mutants(root, source, source.read_bytes(), [], timeout_factor=1e308)
