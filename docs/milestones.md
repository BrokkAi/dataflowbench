# Milestones

Milestones are deliberately small enough for one maintainer to land directly
and revise. Follow-up issues are useful only when a slice needs independent
design discussion, external infrastructure, or parallel ownership.

## M0: contract and calibration

- Version the case contract around semantic templates, polarity, negative
  mechanisms, score tiers, semantic dimensions, and model profiles.
- Keep the bootstrap Java taint fixtures as non-scoring calibration cases.
- Reject unbalanced future core templates during validation.
- Document benchmark provenance and scoring before publishing scores.

## M1: breadth baseline and Java propagation kernel

First establish one balanced, benchmark-controlled direct-propagation pair in
every language/dialect supported by the Bifrost CLI. This 26-assertion breadth
baseline catches adapter, parser, and language-routing failures before deeper
language work begins.

Then author 16 Java benchmark-controlled templates, with one positive and one
negative case per template. Use four equally sized strata:

1. local propagation and flow-sensitive kills;
2. calls, returns, and context separation;
3. heap, field, alias, and object separation;
4. branches, loops, exceptions, and other control transfers.

The resulting 32 Java assertions form the first deep scored core. Test Bifrost
first; add CodeQL and Joern adapters after the fixture contract stabilizes, and
add OpenTaint when its neutral JVM-rule path is reproducible.

## M2: cross-language parity

Port the same 16 templates to JavaScript and Python without changing their
semantic intent, then extend parity language by language where the construct is
meaningful. Language-only constructs live in `language-extension` scorecards.

## M3: taint modeling

Add balanced categories for sources and sinks, propagators, sanitizers, opaque
library summaries, framework entry points, and persistence boundaries. Publish
benchmark-controlled and tool-native model profiles separately.

## M4: real-project confirmation

Add a small, pinned, manually reviewed corpus drawn from executable or
buggy/fixed upstream benchmarks. Keep these results separate from the synthetic
semantic core. Performance and typestate receive independent milestone plans
after the correctness contract is stable.
