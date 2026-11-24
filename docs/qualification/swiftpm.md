# SwiftPM CLI qualification

Tested implementation: `0f5cc9a943e5a0f828fa68701d3f046b81848047`.
Environment: macOS/arm64, Apple Swift 6.4.2, Python 3.12.7,
Krapper v0.2.0's compatible discovery backend.

The fork CLI, not a separate mutation harness, ran the public package under
`tests/fixtures/swift`. It copied sources into a private workspace, compiled
and ran the original test control, then compiled each mutation separately.

| Mutation | Result | Interpretation |
| --- | --- | --- |
| `choose`: `>` → `>=` | survived | The fixture deliberately omits an assertion at zero. |
| `choose`: `0` → `1` | killed | The positive-input assertion detects the changed result. |
| `join`: `+` → `-` | invalid | String subtraction does not compile; it is not a kill. |

Totals: **1 killed, 1 survived, 1 invalid, 0 timeouts, 0 errors**.
The score is **50.0%**, using only the two valid executed mutants. Exit code
**3** correctly reports the survivor. This intentionally incomplete fixture
qualifies outcome handling; it is not a claim of strong application tests.

Seven build/test command records were retained. The original fixture source
was byte-identical after execution; no `.build` was created in its original
checkout. Temporary worker directories were removed.

## Reproduce

Install the fork and compatible backend as described in the root README, then:

```sh
mkdir -p target/qualification
cp -R tests/fixtures/swift target/qualification/cli-demo
.venv/bin/mutator --root target/qualification/cli-demo \
  --no-coverage --mutate-all Sources/Demo/Demo.swift
```

Use a fresh destination. Exit 3 is expected. Inspect
`target/qualification/cli-demo/.metrics/mutate/Demo.edn` and
`target/qualification/cli-demo/target/mutation-runs/<run>/results.json`.

## Additional checks and limits

- The 163-test regression suite passed locally, including all 96 upstream tests.
- Real Swift tests reject zero-test and failing pristine controls.
- Regression tests cover source/output aliases, malformed or inconsistent test
  reports, separate XCTest/Swift Testing report names, non-finite timeout factors
  and timeout-budget overflow. Invalid, timeout and error outcomes cannot enter
  the kill denominator.
- Swift runs sequentially, requires a package at the root, and rejects source
  symlinks. The initial test command adapter accepts only `swift test` with
  `--filter`/`--skip` selection pairs.
- Tests are trusted code, not OS-sandboxed. Other Swift toolchain versions,
  external SwiftPM dependencies and viewer rendering of new counters have not
  been qualified by this run.
- No sdm-agent mutation run was performed with this fork. No live SDK/provider
  delivery or installation was performed.
- Independent review could not run because its service authentication failed.
  No independent approval or upstream-readiness verdict is claimed. The known
  legacy Go overlay/resource issue remains outside this Swift path.
