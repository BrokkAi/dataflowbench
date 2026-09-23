# Resolved Swift numeric sanitizer controls

The historical sanitizer control exposed two separate problems. The generic
property-RHS SSA repair restores the ordinary `Plain` wrapper body, while the
stock name-based numeric barrier still blocks the local `Int: Numeric` wrapper.
A second, isolated patch restricts that existing barrier to resolved `Swift`
struct declarations in the twelve scalar families enumerated by the pinned
numeric type library. Protocol conformance or a matching display name alone
cannot prove this identity. Other SDK scalar types remain unqualified.

The SSA-only control reports source 17 to direct sink 19 and Plain sink 31. With
the resolved barrier, local Int sink 27 is also reached; the real Swift.Int
conversion sink 23 remains clean. Both stages retain all conversion declaration
rows and numeric-base rows. The patch adds no barrier and contains no fixture,
source or sink special case.

A fresh database repeats all six queries with the same source and versioned
`6.8.4-dfb.4` adapter library. It again reaches only sinks 19, 27 and 31. Raw
queries, binary results, logs, source archive, runtime manifest and phase records
are retained with hashes. Earlier failed observations remain immutable.

The canonical positive/negative pair uses a separately committed plan and the
unchanged 104-entry population. Results are explicitly adapter-patched, never
vendor-native. No scored activation is made. The extraction deadline is 150
seconds, queries request 60 seconds and 2048 MiB, and aggregate memory compliance
and full semantic completeness remain unproven.

## Canonical observations

Both canonical cases completed extraction and all six queries and decodes.
The positive reports source 4 to sink 6; the negative recognizes source 4 and
sink 8 but reports no connecting flow. Its parse and render calls resolve to
Swift.FixedWidthInteger and Swift.String, and the parsed Swift.Int is a barrier.
The three portable verification suites include 26 tests and are wired into CI.
