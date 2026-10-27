"""Fresh real Python env/argv + actual worker body; engine callbacks fixture-only."""
import json
import os
from pathlib import Path
import sys
import test_native_qualifier as tests

root=Path(sys.argv[1]).resolve()
mode=sys.argv[2]
assert mode in {'positive','wrong-cf','extra','changed-java','import-mutation'}
startup=dict(os.environ)
test=tests.NativeTests('runTest')
test.root=root
# Real worker argv/source/receipt/environment/flock bodies execute. Only source
# fixture/controller native-process observation and observer engine I/O are seams.
test.worker_fixture(bad_environment=mode!='positive',actual_environment=True,
                    import_mutation=mode=='import-mutation')
namespace=root/'reports/releases/v0.9.2/qualification/joern-post-bifrost-01/native-controls-01'
receipt=namespace/'worker-invocation.json'
if mode=='positive':
    actual=json.loads(receipt.read_bytes())
    assert actual['environment']==startup
    assert actual['environment']['__CF_USER_TEXT_ENCODING']=='0x1F5:0x0:0x0'
else:
    assert not receipt.exists()
    assert not (namespace/'capture').exists()
print(json.dumps({'mode':mode,'ready':mode=='positive','worker_receipt':receipt.exists(),
                  'startup_cf':startup.get('__CF_USER_TEXT_ENCODING'),
                  'engine_executed':False,'fixture_controls_only':True},sort_keys=True))
