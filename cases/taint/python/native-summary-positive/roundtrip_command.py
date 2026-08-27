"""Tool-native probe, template 4 (category O): a platform round trip.

`base64.b64encode` then `base64.b64decode`, with `str.encode` and `bytes.decode`
at the ends. An engine that reads no platform bodies needs a shipped summary on
every one of those four calls for the value to survive to the sink.
"""

import base64
import os


def run():
    payload = os.environ["DFB_NATIVE_PAYLOAD"]  # DFB-SOURCE: native-summary-environment
    encoded = base64.b64encode(payload.encode())
    decoded = base64.b64decode(encoded).decode()
    os.system(decoded)  # DFB-SINK: native-summary-command


if __name__ == "__main__":
    run()
