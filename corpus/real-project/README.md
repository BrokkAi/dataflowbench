# Real-project confirmation slice — selection artifacts

The top-level R1 artifacts are the machine-checkable half of
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

## Wave R2

R1 remains an immutable failed audit: its selected pins and ground-truth
subjects were accepted, but its population eligibility could not be certified
from draw-time evidence. R2 is therefore a new prospective wave, never a
rewrite of the files above.

`r2/protocol.json` and
`docs/real-project-r2-preregistration.md` are committed and merged before the
first R2 query. Only after that boundary may the capture tool create the raw,
source-only response snapshot and derive the new frame. Later R2 artifacts stay
under `corpus/real-project/r2/`; no R2 pin or report is placed beside R1.
