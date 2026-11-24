import shutil
from pathlib import Path

import pytest

from mutator.cli import run
from mutator.edn import loads


@pytest.mark.skipif(shutil.which('swift') is None, reason='Swift toolchain required')
def test_swift_cli_outcomes(tmp_path, capsys):
    fixture = Path(__file__).parent / 'fixtures/swift'
    project = tmp_path / 'project'
    shutil.copytree(fixture, project)
    original = (project / 'Sources/Demo/Demo.swift').read_bytes()
    status = run(['--root', str(project), '--no-coverage', '--mutate-all',
                  '--max-workers', '1', 'Sources/Demo/Demo.swift'])
    output = capsys.readouterr()
    assert status == 3, output.out + output.err
    snapshot = loads((project / '.metrics/mutate/Demo.edn').read_text())
    states = [value.lstrip(':') for value in snapshot['outcomes'].values()]
    assert sorted(states) == ['invalid', 'killed', 'survived']
    assert sum(form.get('invalid', 0) for form in snapshot['forms']) == 1
    assert (project / 'Sources/Demo/Demo.swift').read_bytes() == original
    assert not (project / '.build').exists()
