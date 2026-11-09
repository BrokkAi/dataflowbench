# Issue #304: list index shift after first removal

## Proposed identity

- Template: `dfb-template-list-removal-index-shift`
- Capability: `heap-list-index-shift-taint`
- Case directories, for each applicable language: `populations/precision-gaps-v1/cases/taint/<language>/list-removal-index-shift-positive/` and `...-negative/`
- Case IDs: `dfb-taint-<language>-list-removal-index-shift-positive` and `dfb-taint-<language>-list-removal-index-shift-negative`
- Markers: `DFB-SOURCE: list-removal-index-shift-input`, `DFB-WITNESS: list-removal-index-shift-remove-first`, and `DFB-SINK: list-removal-index-shift-sink`

These are prospective core cases. The orchestrator must register the template and add it to each applicable population before corpus-wide validation can accept the new denominator.

## Semantic pair and safety proof

Each fixture starts with the ordered values `[safe, dfb_source(), more-safe]`, removes the first value, and reads one position from the resulting collection. The positive reads index `0`; after removal the source value is at that position. The negative reads index `1`; after removal that position contains the original third value (`"more-safe"` or integer `9`). It is distinct from and independent of the input read by `dfb_source`.

Fixtures retain the established no-argument `dfb_source()` endpoint shape. Numeric-return languages use `int`/`Int`/`i32` values `[0, dfb_source(), 9]`; JavaScript, TypeScript, Python, Ruby, and PHP use strings `["safe", dfb_source(), "more-safe"]`. In all languages except Swift, the helper reads `DFB_INPUT`, which the validator varies over `17` and `83`. It compiles or interprets each fixture and requires both positive runs to print the respective source value. Both negative runs must print the unchanged safe third value (`9` or `more-safe`). For Swift, the established zero-argument `dfb_source() -> Int` and `dfb_sink(_ value: Int)` endpoints are preserved; the validator substitutes return literals `17` and `83` into temporary copies and checks both outputs. Its source and sink anchors mark the endpoint call lines as required by the current Swift anchor validator. These checks establish runtime dependence without consulting analyzer output. `field-separation` describes the negative: source and sink use distinct current positions in the same collection after the shift.

## Language applicability

All 14 target languages have a natural sequence/list operation matching this behavior:

| Language | Idiom covered | Applicability and notes |
| --- | --- | --- |
| C | fixed-capacity integer array, active length, `memmove` | C has no standard growable-list type. A small array plus active length and `memmove` is the conventional way to shift a contiguous C array; this tests the element displacement while avoiding a synthetic allocator/vector implementation. It does not claim to test capacity growth. |
| C++ | `std::vector<int>`, `push_back`, `erase(begin())`, `operator[]` | Direct growable-vector behavior. |
| C# | `List<int>`, `Add`, `RemoveAt(0)`, indexer | Direct mutable-list behavior. |
| Go | `[]int` slice, `append`, `s = s[1:]`, indexing | Direct slice-header re-slicing behavior. |
| Java | `ArrayList<Integer>`, `add`, `remove(0)`, `get` | Direct OWASP-style list behavior. |
| JavaScript | array, `push`, `shift`, indexing | Direct mutable-array behavior. |
| TypeScript | typed `string[]`, `push`, `shift`, indexing | JavaScript array behavior with a statically typed element list. |
| Kotlin | `MutableList<Int>`, `add`, `removeAt(0)`, indexing | Direct mutable-list behavior. |
| Scala | `mutable.ArrayBuffer[Int]`, `+=`, `remove(0)`, `apply` | Uses the mutable indexed sequence whose removal shifts later positions. |
| Swift | `Array<Int>`, `append`, `removeFirst()`, subscript | Preserves the existing `DataFlowBenchTaintSwift.dfb_source() -> Int` and `dfb_sink(_ value: Int)` endpoints; post-removal indices are read from the mutated array. |
| Rust | `Vec<i32>`, `push`, `remove(0)`, indexing | Direct growable-vector behavior. |
| Python | `list[str]`, `append`, `pop(0)`, indexing | Direct list behavior. |
| Ruby | `Array<String>`, `push`, `shift`, indexing | Direct mutable-array behavior. |
| PHP | list array of strings, append, `array_shift`, numeric indexing | Uses a list with consecutive integer keys; `array_shift` reindexes it. No associative-key behavior is implied. |

No language is marked inapplicable. The C row is deliberately the limited array-backed equivalent called out in the issue checklist; it uses no invented standard-library feature.

## Runtime and schema validation

Run `python3 scripts/validate-precision-issue-304.py`. It checks every pair's schema, case balance, anchors and markers, then independently runs each fixture twice with distinct source values. It reports a missing compiler/runtime as unavailable and fails rather than treating that language as validated.

The integration registers these fixtures under the versioned prospective input root. The canonical corpus loader and core denominator checks include them; historical populations retain their original input roots.
