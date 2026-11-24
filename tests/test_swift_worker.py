import json
import os
import shutil
from pathlib import Path

import pytest

from mutator.functions import sites_in_file


def project_fixture(tmp_path):
    root = tmp_path / 'project'
    shutil.copytree(Path(__file__).parent / 'fixtures/swift', root)
    path = root / 'Sources/Demo/Demo.swift'
    original = path.read_bytes()
    sites = sites_in_file(original.decode(), path, root, 'Sources/Demo/Demo.swift')
    return root, path, original, sites


@pytest.mark.skipif(shutil.which('swift') is None, reason='Swift toolchain required')
def test_private_swift_worker(tmp_path):
    from mutator.swift_runner import run_swift_mutants

    root, path, original, sites = project_fixture(tmp_path)
    home = os.environ.get('HOME')
    outcomes = run_swift_mutants(root, path, original, sites)
    assert sorted(outcomes.values()) == ['invalid', 'killed', 'survived']
    assert path.read_bytes() == original
    assert os.environ.get('HOME') == home
    assert not (root / '.build').exists()
    records = json.loads(next(root.glob('target/mutation-runs/*/results.json')).read_text())
    assert records['source_sha256']
    assert [item['phase'] for item in records['commands'][:2]] == ['control-build', 'control-test']
    assert not list(root.glob('target/mutation-workers/run-*'))


@pytest.mark.skipif(shutil.which('swift') is None, reason='Swift toolchain required')
@pytest.mark.parametrize('failure', ['zero-tests', 'failing-tests'])
def test_swift_control_must_pass(tmp_path, failure):
    from mutator.swift_runner import SwiftExecutionError, run_swift_mutants

    root, path, original, sites = project_fixture(tmp_path)
    command = 'swift test --filter NoSuchTest' if failure == 'zero-tests' else None
    if failure == 'failing-tests':
        tests = root / 'Tests/DemoTests/DemoTests.swift'
        tests.write_text(tests.read_text().replace('#expect(choose(1))', '#expect(!choose(1))'))
    with pytest.raises(SwiftExecutionError, match='control'):
        run_swift_mutants(root, path, original, sites, test_command=command)
    assert path.read_bytes() == original


@pytest.mark.parametrize('command', [
    'swift test --scratch-path /tmp/other', 'swift test --package-path /tmp/other',
    'swift test --xunit-output /tmp/other', 'echo success',
])
def test_swift_selection_cannot_override_isolation(command):
    from mutator.swift_runner import test_selection

    with pytest.raises(ValueError):
        test_selection(command)
