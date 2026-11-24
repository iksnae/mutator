import pytest

from mutator.sites import apply_site, discover_raw


@pytest.mark.parametrize('expression,original,mutant', [
    ('a + b', '+', '-'), ('a - b', '-', '+'),
    ('a * b', '*', '/'), ('a / b', '/', '*'),
    ('a == b', '==', '!='), ('a != b', '!=', '=='),
    ('a > b', '>', '>='), ('a >= b', '>=', '>'),
    ('a < b', '<', '<='), ('a <= b', '<=', '<'),
    ('a && b', '&&', '||'), ('a || b', '||', '&&'),
    ('!a', '!', ''), ('-a', '-', ''),
    ('true', 'true', 'false'), ('false', 'false', 'true'),
    ('0', '0', '1'), ('1', '1', '0'),
])
def test_swift_expression_operators(expression, original, mutant):
    source = f'func example() {{ return {expression} }}'
    sites = discover_raw(source, 'swift', 'Example.swift')
    assert [(site.original, site.mutant) for site in sites] == [(original, mutant)]
    site = sites[0]
    assert source.encode()[site.start:site.end].decode() == original


@pytest.mark.parametrize('expression', [
    'value!', 'value?.count', 'value ?? fallback',
    '"true && 0 + 1"', '#"false || 0"#',
    '"value: \\(a + 1)"',
])
def test_swift_non_operator_syntax_is_not_mutated(expression):
    source = f'func example() {{ return {expression} }}'
    assert discover_raw(source, 'swift', 'Example.swift') == []


def test_swift_comments_and_unicode_offsets():
    source = '// true && 0\nfunc café(_ x: Int) -> Int { /* 0 + 1 */ return x + 1 }'
    sites = discover_raw(source, 'swift', 'Example.swift')
    assert [(site.original, site.mutant) for site in sites] == [('+', '-'), ('1', '0')]
    mutated = apply_site(source, sites[0].start, sites[0].end, sites[0].mutant)
    assert 'café' in mutated and 'return x - 1' in mutated


def test_swift_guard_and_multiline_condition_sites():
    source = '''actor Worker {
  func check(_ value: Int, ready: Bool) async -> Bool {
    guard value >= 0,
          !ready || value == 1 else { return false }
    return true
  }
}
'''
    pairs = {(site.original, site.mutant) for site in discover_raw(source, 'swift', 'Worker.swift')}
    assert {('>=', '>'), ('!', ''), ('||', '&&'), ('==', '!='),
            ('0', '1'), ('1', '0'), ('false', 'true'), ('true', 'false')} <= pairs
