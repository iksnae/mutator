"""Text reports for a mutation run and for --scan."""

from __future__ import annotations

from mutator.model import FormResult, Site


def _score(form: FormResult) -> str:
    if form.score is None:
        return "   n/a"
    return f"{form.score * 100:5.1f}%"


def _extra_columns(invalid: int, timeout: int, errors: int, extended: bool) -> str:
    return f'{invalid:7d} {timeout:7d} {errors:6d} ' if extended else ''


def format_results(forms: list[FormResult]) -> str:
    if not forms:
        return "No functions to mutate.\n"
    name_width = max(8, min(48, max(len(form.name) for form in forms)))
    namespace_width = max(9, min(72, max(len(form.namespace) for form in forms)))
    extended = any(form.invalid + form.timeout + form.error for form in forms)
    extra_header = f"{'Invalid':>7} {'Timeout':>7} {'Errors':>6} " if extended else ''
    header = (
        f"{'Function':<{name_width}} {'Namespace':<{namespace_width}} "
        f"{'Killed':>7} {'Survived':>9} {'Uncovered':>10} "
        f"{extra_header}{'Sites':>6} {'Score':>7}"
    )
    ordered = sorted(
        forms,
        key=lambda form: (form.score is not None, form.score or 0, -form.survived, form.name),
    )
    lines = [header, "-" * len(header)]
    killed = survived = uncovered = sites = invalid = timeout = errors = 0
    for form in ordered:
        lines.append(
            f"{form.name:<{name_width}} {form.namespace:<{namespace_width}} "
            f"{form.killed:7d} {form.survived:9d} {form.uncovered:10d} "
            f"{_extra_columns(form.invalid, form.timeout, form.error, extended)}{form.sites:6d} {_score(form)}"
        )
        killed += form.killed
        survived += form.survived
        uncovered += form.uncovered
        sites += form.sites
        invalid += form.invalid
        timeout += form.timeout
        errors += form.error
    executed = killed + survived
    score = "n/a" if executed == 0 else f"{(killed / executed) * 100:.1f}%"
    lines.append("-" * len(header))
    lines.append(
        f"{'Total':<{name_width}} {'':<{namespace_width}} "
        f"{killed:7d} {survived:9d} {uncovered:10d} "
        f"{_extra_columns(invalid, timeout, errors, extended)}{sites:6d} {score:>7}"
    )
    lines.append("")
    return "\n".join(lines)


def format_site_log(sites: list[Site], status: dict[str, str]) -> str:
    lines = []
    for site in sites:
        label = status.get(site.mutation_id)
        if label is None:
            continue
        lines.append(f"{label.upper():9} {site.file}:{site.line} {site.description}")
    if not lines:
        return ""
    return "\n".join(lines) + "\n"


def format_scan(
    path: str, sites: list[Site], changed: set[tuple[str, str]], covered: dict[str, bool] | None
) -> str:
    lines = [f"Scan: {len(sites)} mutation sites in {path}"]
    for site in sites:
        mark = "*" if (site.namespace, site.form_id) in changed else " "
        coverage = ""
        if covered is not None and not covered.get(site.mutation_id, True):
            coverage = " uncovered"
        lines.append(f"{mark} {path}:{site.line} {site.description}{coverage}  [{site.form_id}]")
    if changed:
        lines.append("* marks a function whose text changed since the last snapshot.")
    lines.append("")
    return "\n".join(lines)
