from pathlib import Path
from types import SimpleNamespace

import pytest

from mutator.crapper_link import ensure_crapper
from mutator.functions import sites_in_file
from mutator.sources import is_mutable_source, iter_source_files


def test_swift_backend_missing_is_an_error(tmp_path):
    backend = ensure_crapper()
    discover = SimpleNamespace(**vars(backend.discover))
    discover.language_of = lambda _path: None
    backend = SimpleNamespace(discover=discover)
    path = tmp_path / 'Sources/Example/App.swift'
    with pytest.raises(ValueError, match='Swift.*backend'):
        is_mutable_source(path, tmp_path, backend)


@pytest.mark.parametrize('visibility', ['private', 'fileprivate'])
def test_swift_private_function_identity(tmp_path, visibility):
    path = tmp_path / 'Sources/Demo/Worker.swift'
    source = f'''actor Worker {{
  {visibility} func check(_ value: Int) async -> Bool {{ value > 0 }}
}}
'''
    sites = sites_in_file(source, path, tmp_path, 'Sources/Demo/Worker.swift')
    assert sites
    assert {site.form_id for site in sites} == {'defn-/check'}
    assert {site.namespace for site in sites} == {'Demo.Worker'}


def test_swift_initializers_properties_and_methods_bind_to_owners(tmp_path):
    path = tmp_path / 'Sources/Demo/Value.swift'
    source = '''struct Value {
  init(_ x: Int) { value = x + 1 }
  var value: Int
  var valid: Bool { value > 0 }
  func changed() -> Int { value - 1 }
}
'''
    sites = sites_in_file(source, path, tmp_path, 'Sources/Demo/Value.swift')
    assert {site.name for site in sites} == {'init', 'valid', 'changed'}
    assert {site.namespace for site in sites} == {'Demo.Value'}


def test_swift_tests_are_excluded_with_older_backend_test_directories(tmp_path):
    backend = ensure_crapper()
    discover = SimpleNamespace(**vars(backend.discover))
    discover.TEST_DIRS = {'tests', 'test'}
    backend = SimpleNamespace(discover=discover)
    for relative in ['Sources/Demo/Value.swift', 'SwiftTests/DemoTests/ValueTests.swift']:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('func check() -> Bool { true }')
    assert [path.relative_to(tmp_path).as_posix() for path in
            iter_source_files([tmp_path], tmp_path, backend)] == ['Sources/Demo/Value.swift']
