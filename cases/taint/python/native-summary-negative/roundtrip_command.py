"""Tool-native probe, template 4 (category O), negative.

A fresh constant makes the identical round trip into the same sink; the
environment read is present and goes nowhere.
"""

import base64
import os


def run():
    unused = os.environ["DFB_NATIVE_PAYLOAD"]  # DFB-SOURCE: native-summary-environment
    encoded = base64.b64encode("id".encode())
    decoded = base64.b64decode(encoded).decode()
    os.system(decoded)  # DFB-SINK: native-summary-command


if __name__ == "__main__":
    run()
