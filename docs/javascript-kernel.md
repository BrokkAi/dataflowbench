# JavaScript propagation kernel

Issue #11 ports the sixteen scored Java propagation templates to JavaScript.
The JavaScript cases keep the Java `template_id` values, source-to-sink
polarity, and negative mechanism; only the smallest fixture construct is
adapted to JavaScript syntax. Every scored JavaScript template has exactly one
`positive` and one `negative` `core` case.

| Stratum | Template ID | JavaScript adaptation |
| --- | --- | --- |
| Local | `dfb-template-direct-propagation` | Direct function call, unchanged in meaning. |
| Local | `dfb-template-local-overwrite-kill` | `let` reassignment replaces the Java local assignment. |
| Local | `dfb-template-local-multi-step-chain` | `const` locals carry the value through the same chain. |
| Local | `dfb-template-arithmetic-expression-propagation` | JavaScript number arithmetic preserves the expression-flow distinction. |
| Calls/returns | `dfb-template-call-context-separation` | One relay is called with tainted and clean values; the selected call remains the distinction. |
| Calls/returns | `dfb-template-argument-position-separation` | A helper returns its first parameter, so the second-argument negative remains non-flowing. |
| Calls/returns | `dfb-template-return-relay-one-hop` | A one-hop helper return carries the value to the sink. |
| Calls/returns | `dfb-template-return-relay-two-hop` | Two JavaScript helper returns preserve the two-hop depth. |
| Heap/separation | `dfb-template-object-separation` | Separate object literals stand in for distinct Java objects. |
| Heap/separation | `dfb-template-same-object-field-separation` | One object has separate `tainted` and `clean` properties. |
| Heap/separation | `dfb-template-alias-propagation-separation` | Assignment of an object reference creates the alias; a second literal remains distinct. |
| Heap/separation | `dfb-template-array-element-separation` | Distinct array indices stand in for Java array elements. |
| Control transfer | `dfb-template-infeasible-branch` | Literal `true`/`false` conditions make the positive/negative path feasible or unreachable. |
| Control transfer | `dfb-template-branch-join` | The negative overwrites the value on both branches; the positive leaves one path tainted. |
| Control transfer | `dfb-template-loop-carried-kill` | A loop either overwrites the carried value or computes from it. |
| Control transfer | `dfb-template-exception-catch` | A JavaScript `Error` object carries a property through `throw`/`catch`; this replaces Java's checked exception class. |

All JavaScript fixtures use the benchmark-controlled `dfb_source` and
`dfb_sink` function names. The Bifrost adapter may lower those endpoints through
its JavaScript kernel policy, but fixture metadata remains analyzer-neutral and
retains only observed evidence in reports.

The Java kernel also has two calibration cases that are intentionally outside
this sixteen-template scored slice. `dfb-template-one-hop-relay` is a simpler
helper-flow calibration covered by the scored return-relay template, and
`dfb-template-modeled-external-summary` requires an explicitly activated
external semantic-model catalog. The standalone CLI cannot activate that
catalog, so it must remain `unsupported` rather than being translated into a
negative JavaScript result.
