# Real-project confirmation slice — selection artifacts

These three artifacts are the machine-checkable half of
[the real-project preregistration](../../docs/real-project-preregistration.md).
The document states the contract; these files are what a validator replays.

| File | What it is |
| --- | --- |
| `frame.json` | The retained sampling frame: the exact advisory queries, the admission rule, and every candidate they produced. It is an immutable input, not a cache — a later re-query returns a different population and starts a new wave rather than correcting this one. |
| `draw.json` | The executed draw: the seed, the ordering rule, the frame digest it consumed, the eligibility criteria, and the ordered walk over each stratum with a disposition for every candidate the walk reached. |
| `pins/*.json` | One pin record per selected repository: the two pinned revisions, their source-archive digests, the licence record, and the ground-truth status including whether the case was independently reviewed. |

`cargo run -- validate` recomputes every draw key from the seed, re-derives each
stratum's ordering from the frame, and refuses a walk that does not reproduce.
`scripts/build-real-project-frame.py` rebuilds a frame from the same queries.

**No upstream source lives here.** Each pinned revision is fetched from its
archive URL and verified against its digest before use; nothing under this
directory redistributes anything.

Schemas: `schemas/real-project-pin.schema.json`,
`schemas/real-project-draw.schema.json`.
