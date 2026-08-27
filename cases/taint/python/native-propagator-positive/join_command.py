"""Tool-native probe, template 2 (category P): taint crosses a platform path
join whose body is inside CPython.

Only a shipped propagator summary for `os.path.join` carries the environment
read to the command sink; the fixture gives the engine nothing to read.
"""

import os
import os.path


def run():
    name = os.environ["DFB_NATIVE_PATH"]  # DFB-SOURCE: native-propagator-environment
    target = os.path.join("/srv/reports", name)
    os.system(target)  # DFB-SINK: native-propagator-command


if __name__ == "__main__":
    run()
