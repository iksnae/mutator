# Swift support and qualification

## Outcome

Extend the mutator fork, not Krapper, with syntax-aware Swift mutations and
credible execution evidence. Preserve the upstream license, package name and
existing language behavior where it is safe. Keep fixes in cohesive commits for
a future upstream PR; do not submit upstream before qualification.

Fork base: upstream `0136cf555797f1c9552388c40207eb2f13af9535`.
Baseline: 96 existing tests passed in an isolated Python environment.

## Discovery boundary

Reuse the existing crapper function/namespace contract. The first fork uses
Krapper's compatible `crapper` package for Swift extraction, rather than copying
its Swift parser. Current upstream crapper lacks Swift discovery. Swift must
therefore fail with an actionable error when that backend is unavailable, never
silently report zero sites. Document this dependency explicitly. Before upstream
submission, settle Swift discovery availability with upstream; no additional
crapper fork is assumed authorized by this plan.

Add Swift token contexts to the existing tree-sitter visitor: arithmetic,
comparisons, equality, Boolean conjunction/disjunction, Boolean literals, integer
0/1 and removal of unary logical/arithmetical negation. Do not mutate force
unwraps, optional type markers, strings, comments, attributes or type syntax.
Swift nil coalescing is not equivalent to Boolean disjunction; leave it alone.
Respect UTF-8 byte offsets and actual function ownership. Exclude SwiftTests and
SwiftPM build outputs. Test modern guard expressions, async functions, actors,
initializers, computed properties and malformed/unsupported syntax explicitly.

## Execution boundary

Start with one SwiftPM package at the selected project root and installed tools.
No tool installation, runtime activation, provider calls or policy changes.

Swift workers need private source/resource/configuration copies and private build
and HOME/cache paths. Do not share writable build products or use the symlink
overlay that invalidated the KSPD trial. Validate a pristine worker with the exact
test selection before accepting any mutant outcome. A failing worker control
aborts without publishing a successful score; it is not a killed mutant.

Separate Swift test compilation from test execution. Compilation failure makes an
invalid mutant, not a kill. Run tests only against the successfully compiled
mutated tests. Keep killed, survived, invalid, timeout and execution-error outcomes
separate in snapshots and terminal output; only killed and survived enter the
score denominator. Do not classify arbitrary shell/build failures as assertions.
Explicit test commands must have a documented relationship to the build step.
Validate timeout inputs as finite and positive.

For the first Swift release, rerun every selected mutation rather than reusing
upstream's function-text-only cached kills. Broader differential-cache provenance
is separate work. Qualification always disables outcome reuse explicitly.

Retain enough per-mutation evidence to reproduce the edit and explain the result:
source revision/digest, operator and byte span, commands, exit codes, timings,
output and test selection. Do not claim that tests were executed when none ran.

## Delivery sequence

1. Add failing Swift discovery/site tests, then minimal language integration.
2. Add failing worker-control and outcome-classification tests, then the Swift
   execution path and reporting changes.
3. Run a real small SwiftPM fixture: asserted defect killed, intentional
   assertion gap survives, invalid mutation excluded, failing control rejected.
4. Rerun the existing Python suite and Krapper's small arithmetic trial. Revisit
   the KSPD embedded-resource reproduction as an engine-control regression.
5. Acquire an owned sdm-agent lease and bind the run to its exact commit. Establish
   the original tests pass, select a bounded set of actual Swift sites, and run
   each independently against declared focused tests. Use isolated HOME and
   preserve the installed/live checkout and its pre-existing state.
6. Record individual results, selection scope and unclassified equivalent mutants
   in a dated qualification report. Never call a bounded sample a repository-wide
   mutation score. No comparisons across different operator sets without caveats.
7. Review, commit and push the fork. List any blockers to upstream submission.

## Verification and rollback

Use pytest unit tests for syntax/selection/report contracts and executable fixture
checks for worker import/resource/build behavior. Capture red and green results.
Run real Swift checks only when the toolchain is available; label skips explicitly.
Keep source restoration in finally blocks and verify owned/live git status.
Independent review is required before claiming upstream readiness; if its service
is unavailable, report that rather than inventing approval.

Keep all product changes on `feat/swift-mutation-support`. Roll back by reverting
an individual fork commit; no installed binary or analyzed project's production
code is changed. If qualification cannot distinguish build/setup failures from
assertion-detected defects, stop without claiming a mutation score and retain the
logs and the exact blocker.
