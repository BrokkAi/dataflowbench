"""Tool-native probe, template 6 (category B): a platform process-wide store.

The value is written into `os.environ` under key `DFB_NATIVE_STORED` and read
back out of the same store under the same key. Only a native model that links
the write to the read carries the taint to the sink.
"""

import os


def run():
    incoming = os.environ["DFB_NATIVE_INBOUND"]  # DFB-SOURCE: native-persistence-environment
    os.environ["DFB_NATIVE_STORED"] = incoming
    command = os.environ["DFB_NATIVE_STORED"]
    os.system(command)  # DFB-SINK: native-persistence-command


if __name__ == "__main__":
    run()
