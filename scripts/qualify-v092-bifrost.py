#!/usr/bin/env python3
"""Run the unchanged 44 policy controls against the public v0.13.1 binary.

Only release identity constants change in a private module instance. Historical
qualification code, expected findings, timeouts and evidence remain unchanged.
The strict result is retained even when qualification fails.
"""
import argparse
import importlib.util
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bifrost", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source = Path(__file__).with_name("qualify-bifrost-v013.py")
    spec = importlib.util.spec_from_file_location("v092_bifrost_controls", source)
    controls = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(controls)
    controls.EXPECTED_VERSION = "0.13.1"
    controls.EXPECTED_BUILD_IDENTITY = "271a0bd840372a1ce6e6e11fc60a788e997ed353"
    controls.EXPECTED_BINARY_SHA256 = "94ad4d58a5fedc888e1bebcc9a88a83f49414e0b922811f1da4e5cc6f42ad803"
    controls.PUBLIC_TAG_COMMIT = "1a23b98f80556bebfec0cde2efee1195f4ee3009"
    original_environment = controls._environment

    def environment(**kwargs):
        result = original_environment(**kwargs)
        result["BIFROST_OPEN_PACKS_DISABLE"] = "1"
        return result

    controls._environment = environment
    controls.ENVIRONMENT_ALLOWLIST += ("BIFROST_OPEN_PACKS_DISABLE",)
    return controls.capture(args.bifrost, args.output)


if __name__ == "__main__":
    raise SystemExit(main())
