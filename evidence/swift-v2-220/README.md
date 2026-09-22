# Swift v2 input validation

`compile-control-attempt-01` retains the complete witnessed Xcode 27.0 / Swift
6.4 / macOS SDK 27.0 compile and control log for the 14 additions in
`swift-synthetic-v2`. The manifest binds the original evidence bytes.

All 12 native cases compile/link only: no shell call or UserDefaults operation
was executed. The two Result cases compile/link and are instrumented only for
bounded source values 7 and 19. Positive observations are 7 and 19; both negative
observations are 0. This is concrete fixture validation, not analyzer activation,
qualified correctness, an unsupported partition, or a release freeze.

Verify with `python3 scripts/verify-swift-v2-evidence.py`. The CI compiler job
retains a fresh independent artifact; it does not overwrite this local witness.
