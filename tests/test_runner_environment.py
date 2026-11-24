import json
import os
import sys

from mutator.runner import CommandRunner


def test_runner_uses_only_supplied_environment(tmp_path, monkeypatch):
    monkeypatch.setenv('MUTATOR_PARENT_ONLY', 'must-not-leak')
    before = os.environ['HOME']
    environment = {'HOME': str(tmp_path), 'PATH': os.environ['PATH']}
    runner = CommandRunner(environment=environment)
    script = 'import os,json; print(json.dumps([os.environ["HOME"], os.getenv("MUTATOR_PARENT_ONLY")]))'
    result = runner.run([sys.executable, '-c', script], tmp_path, 5)
    assert result.code == 0
    assert json.loads(result.output) == [str(tmp_path), None]
    assert os.environ['HOME'] == before
    assert environment == {'HOME': str(tmp_path), 'PATH': os.environ['PATH']}
