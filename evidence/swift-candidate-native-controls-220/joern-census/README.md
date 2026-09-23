# DataFlowBench #220 Joern complete census

This sidecar is a bounded, non-scored inspection of the already acquired Joern
4.0.633 macOS arm64 candidate. It owns only this directory and does not edit
the DataFlowBench repository.

Run:

```sh
python3 /private/tmp/dfb-220-joern-complete-census/reproduce_census.py \
  --candidate /private/tmp/dfb-220-candidate-assets/joern/extracted/joern-cli \
  --archive /private/tmp/dfb-220-candidate-assets/joern/joern-cli-macos-arm64.zip \
  --out /private/tmp/dfb-220-joern-complete-census
```

The JSONL outputs are append-only during the run. `all-files.jsonl` covers
every extracted file, `jars.jsonl` maps every JAR path to its content SHA,
`unique-jars.jsonl` defines the unique-JAR denominator, `all-jar-members.jsonl`
covers every member once per unique JAR SHA, and `all-jar-resources.jsonl`
retains every non-class and non-TASTy resource once per unique JAR regardless of
keyword selection. `first-party-classes.jsonl`
uses an explicit package provenance rule and makes no native-role claim.
`keyword-navigation-hits.jsonl` is only a navigation index and cannot support
absence proof.
