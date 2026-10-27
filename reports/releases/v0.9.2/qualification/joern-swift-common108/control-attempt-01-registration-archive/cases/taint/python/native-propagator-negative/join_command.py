"""Tool-native probe, template 2 (category P), negative.

The same `os.path.join` operation, at the same `os.system` callsite. The joined
value that reaches the sink is the clean one; the tainted join goes nowhere.
"""

import os
import os.path


def run():
    name = os.environ["DFB_NATIVE_PATH"]  # DFB-SOURCE: native-propagator-environment
    unused = os.path.join("/srv/reports", name)
    target = os.path.join("/srv/reports", "index.txt")
    os.system(target)  # DFB-SINK: native-propagator-command


if __name__ == "__main__":
    run()
