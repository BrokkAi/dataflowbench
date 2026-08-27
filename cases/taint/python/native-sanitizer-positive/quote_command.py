"""Tool-native probe, template 3 (category Z): the unsanitized path.

The environment read reaches the command sink with no platform sanitization
idiom between them. This cell establishes that the shipped model set sees the
flow at all, so that the negative's suppression means something.
"""

import os


def run():
    argument = os.environ["DFB_NATIVE_ARGUMENT"]  # DFB-SOURCE: native-sanitizer-environment
    os.system("echo " + argument)  # DFB-SINK: native-sanitizer-command


if __name__ == "__main__":
    run()
