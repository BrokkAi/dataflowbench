# Capture commands and boundaries

The successful structural run used `io.joern.dumpq.Main` from the exact extracted `querydb.zip` bundle, with its classpath supplemented only by the already pinned Joern 4.0.628 runtime JARs. The normal `updatedb` installer was not invoked. The first direct launcher attempt is retained in `direct-launcher-help.stderr`; it failed before catalog loading because the launcher archive omits a matching Scala runtime class.

The bundle was inspected structurally only. No Swift source or CPG was provided, no frontend or native fixture was executed, and no benchmark model, semantics file, score, unsupported partition, shell call, or UserDefaults operation was created.
