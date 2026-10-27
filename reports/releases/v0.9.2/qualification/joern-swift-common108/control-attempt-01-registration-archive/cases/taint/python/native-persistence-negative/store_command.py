"""Tool-native probe, template 6 (category B), negative.

The write goes to `DFB_NATIVE_STORED`; the read that reaches the sink is under
the distinct key `DFB_NATIVE_OTHER`. docs/native-profile.md names the hazard in
advance: the read side of this store is itself a shipped environment source in
at least one catalog, so a tool that treats it as a source rather than as a
store-read reports both cells and takes a false positive here. That behaviour
is what this template exists to make visible.
"""

import os


def run():
    incoming = os.environ["DFB_NATIVE_INBOUND"]  # DFB-SOURCE: native-persistence-environment
    os.environ["DFB_NATIVE_STORED"] = incoming
    command = os.environ["DFB_NATIVE_OTHER"]
    os.system(command)  # DFB-SINK: native-persistence-command


if __name__ == "__main__":
    run()
