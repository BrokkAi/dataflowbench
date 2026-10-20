"""Tool-native probe, template 3 (category Z), negative.

The identical flow passes through `shlex.quote`, CPython's own shell-quoting
idiom, before the same sink. docs/native-profile.md preregisters the
expectation that this credit is query-family-scoped in the shipped CodeQL set —
a barrier for `py/shell-command-constructed-from-input` and a plain taint
summary elsewhere — so a false positive here is a publishable product fact
about where the credit is scoped, not a defect in this fixture.
"""

import os
import shlex


def run():
    argument = os.environ["DFB_NATIVE_ARGUMENT"]  # DFB-SOURCE: native-sanitizer-environment
    quoted = shlex.quote(argument)
    os.system("echo " + quoted)  # DFB-SINK: native-sanitizer-command


if __name__ == "__main__":
    run()
