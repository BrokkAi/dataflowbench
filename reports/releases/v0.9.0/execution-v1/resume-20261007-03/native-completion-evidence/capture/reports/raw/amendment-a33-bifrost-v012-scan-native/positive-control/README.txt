This positive-control attempt records the v0.12.0 result produced by the scan.
The outcome is derived from the security-policy completion and finding count
in result.json; no prior result is assumed.

Observed outcome: inconclusive
Observed completion: {"reasons": ["partial_discovery"], "type": "inconclusive"}
Observed findings: 1

The source uses the exact servlet-parameter-to-JDBC shape named by the policy
in a Maven project declaring jakarta.servlet-api:6.1.0. Diagnostics and
dependency-pack decisions are retained in result.json and the full stderr is
beside this file.
