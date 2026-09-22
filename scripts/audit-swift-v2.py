#!/usr/bin/env python3
"""Publish fixture participation separately from historical v1 outcome coverage."""
import argparse
from swift_population_v2 import ROOT, audit


def render():
    _,additions=audit()
    lines=['# Swift v2 fixture participation', '',
           'This is an unfrozen fixture inventory under A38/A39, not analyzer support or a scored result. '
           'The immutable `swift-synthetic-v2` input population contains the original 90 v1 assertions '
           'plus 12 native assertions and two Result extension assertions. The original reports still '
           'bind v1 and do not acquire rows for these additions.', '',
           'The [v1 outcome reconciliation](swift-coverage-audit.md) retains all prior results. '
           'Seven formerly deferred families now have canonical pairs, with independent analyzer '
           'qualification and execution still pending. The two opaque modeling identities remain unresolved. '
           'No absent execution is labeled unsupported, inconclusive, runner-error, or not-reached. '
           'Bifrost Swift remains unsupported; no Bifrost result rows are invented.', '',
           '| Template | Polarity | Example | Profile | Validation policy | Analyzer results |',
           '| --- | --- | --- | --- | --- | --- |']
    for path,case in additions:
        policy='Compile only; never execute' if case['model_profile']=='tool-native' else 'Compile and bounded source-dependence controls'
        lines.append(f'| `{case["template_id"]}` | {case["polarity"]} | [{case["id"]}](../{path.relative_to(ROOT)}) | {case["model_profile"]} | {policy} | Pending qualification and execution |')
    lines += ['', 'The new population preserves core (66), calibration (4), controlled modeling (20), '
              'native modeling (12), and language extension (2) as separate partitions. '
              'No rate or score denominator pools them. All analyzer budgets remain 512 MiB / 60 seconds. '
              'Real-project work stays separate and reserved tracks remain inactive.', '',
              'Reproduce input integrity with `python3 scripts/audit-swift-v2.py --check`; '
              'compile/control the new tranche with `python3 scripts/validate-swift-v2.py --output <fresh-directory>`. '
              'The existing Swift fixture validator continues to validate v1 independently. '
              'Prospective independent native API/model qualification and extension partitions must precede '
              'fresh analyzer execution; neither existing adapter configuration is modified here.', '']
    return '\n'.join(lines)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--write',action='store_true');parser.add_argument('--check',action='store_true');args=parser.parse_args()
    content=render();path=ROOT/'docs/swift-v2-coverage.md'
    if args.write:path.write_text(content)
    elif path.read_text()!=content:raise SystemExit('stale v2 participation inventory')
    print('Swift v2: 104 immutable inputs; 14 additions await analyzer qualification; two opaque identities unresolved')
