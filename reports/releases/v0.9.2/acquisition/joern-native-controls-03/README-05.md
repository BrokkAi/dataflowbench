# Private native qualifier05: explicit Darwin startup environment

Evidence-backed runtime change only: expected_environment sets __CF_USER_TEXT_ENCODING=0x1F5:0x0:0x0 on Darwin, explicitly in the Popen environment rather than deleting/filtering fields after startup. This exact user/platform value is observed in the failed controls02 stop and independent explicit-key probe. No ambient value, UID-derived wildcard, arbitrary extra or alternate value is accepted. Non-Darwin environment generation is unchanged. Exact worker dict equality and guarded locales/Java/source/argv/lock checks remain untouched.

All prior43 tests remain. Five fresh Homebrew Python subprocess fixtures run the actual run_worker pre-ready argv/receipt/same-FD flock/environment bodies with real startup environment (no os.environ clearing/replacement in the worker fixture). Positive writes its own observed environment receipt before ready; wrong Darwin field, arbitrary extra, Java change and observer-load import mutation each fail before ready with no receipt or capture. Controller process-table observations, acquisition evidence, and observer.controls engine I/O remain explicit fixture seams. Synthetic returned control results are not actual native qualification. No engine/JVM/native controls/replay/actual admission/bootstrap/qualification occurs.

The helper process imports test fixture code, and fixture files live in unique canonical /private/tmp roots. These are unit source-composition checks, not a substitute for root exact source integration, source commit, new request/namespace, independent invocation review and fresh live admission.

Reproduce: /opt/homebrew/bin/python3.13 -B -E /private/tmp/joern05-native-qualifier-05/test_native_qualifier.py

Frozen04, canonical02 and outer06 untouched. No runtime policy/resource/clock/closure/ownership/interpreter changes beyond the explicit Darwin environment value.
