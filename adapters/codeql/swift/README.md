# Swift CodeQL adapter

See [A35](../../../docs/codeql-swift.md) for independent pins, activation controls,
per-template partition, reproduction, and memory-budget limitations. Core,
controlled modeling, and calibration have separate reports. Native/opaque,
extension and real-project deferrals remain explicit. Bifrost support is unchanged.

The runner requires committed configuration, exact pin witnesses, both activation
certificates, and a resolved partition. It retains failed and inconclusive outcomes
and refuses to overwrite evidence. A `--ram` setting does not establish aggregate
process-tree memory compliance.
