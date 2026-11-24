import pytest

from mutator.cli import _record, run
from mutator.crapper_link import ensure_crapper
from mutator.model import FormResult, RunResult


@pytest.mark.parametrize('counts', [{'timeout': 1}, {'error': 1}, {'invalid': 1}])
def test_unusable_outcomes_refuse_success(counts):
    form = FormResult(id='defn/f', namespace='Demo', name='f', private=False,
                      file='f.swift', line=1, end_line=1, digest='hash', sites=1, **counts)
    result = RunResult(path='f.swift', forms=[form], written=[])
    assert _record(result, [], []) == 'baseline'


def test_unsupported_swift_backend_is_a_cli_error(tmp_path, monkeypatch, capsys):
    source = tmp_path / 'Example.swift'
    source.write_text('func f() -> Bool { true }')
    monkeypatch.setattr(ensure_crapper().discover, 'language_of', lambda _: None)
    assert run(['--root', str(tmp_path), '--scan', str(source)]) == 2
    assert 'Swift-capable crapper backend' in capsys.readouterr().err
