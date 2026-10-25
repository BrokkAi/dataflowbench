"""Fresh interpreter: actual pending gate and inherited88 boundary, no replay."""
import json
from pathlib import Path
import subprocess
import sys
import types
from unittest import mock
import native_qualifier as n

mode=sys.argv[1]
assert mode in {'positive','foreign','foreign-selector'}
cfg={'pending_plan':n.PLAN,'observer':n.OBSERVER}
if mode=='foreign-selector':
    token=n.hashlib.sha256((str(n.ROOT)+'joern').encode()).hexdigest()[:12]
    name='_dfb_common_v2_joern_reports_'+token
    foreign=types.ModuleType(name)
    foreign.__file__='/private/tmp/foreign-private-selector.py'
    sys.modules[name]=foreign
    with mock.patch.object(subprocess,'Popen',side_effect=AssertionError('no dispatch')) as spawn:
        try:n.pending_plan_preflight(n.ROOT,cfg)
        except ValueError as error:
            assert 'already registered' in str(error)
            assert sys.modules[name] is foreign
            assert spawn.call_count==0
            print(json.dumps({'mode':mode,'foreign_preserved':True,'gate_rejected':True,'dispatches':0}))
        else:raise AssertionError('foreign selector accepted')
    raise SystemExit(0)
with mock.patch.object(subprocess,'Popen',side_effect=AssertionError('no process dispatch authorized')) as spawn:
    before=n.pending_plan_preflight(n.ROOT,cfg)
    foreign=None
    try:
        with n.modules(n.ROOT) as (core,graph):
            assert len(core['runtime_module_graph'])==88
            with n.owned_module_scope():
                observer=n.load(n.ROOT,n.OBSERVER,'_native_fresh_schema_probe')
                inside=n.validate_pending_plan(n.ROOT,cfg,observer)
            if mode=='foreign':
                foreign=types.ModuleType('_native_foreign_pending_probe')
                foreign.__file__='/private/tmp/not-a-sealed-graph-module.py'
                sys.modules[foreign.__name__]=foreign
    except BaseException as error:
        if mode!='foreign':raise
        assert foreign is not None and sys.modules.get(foreign.__name__) is foreign
        print(json.dumps({'mode':mode,'foreign_preserved':True,'boundary_rejected':True,
                          'error':str(error),'dispatches':spawn.call_count}))
    else:
        assert mode=='positive','foreign module unexpectedly accepted'
        assert before['full_validator_returned'] and inside['full_validator_returned']
        print(json.dumps({'mode':mode,'full_validator_before_graph':True,
                          'full_validator_after_graph_baseline':True,'frozen88_closed':True,
                          'dispatches':spawn.call_count,'replay_performed':False}))
    assert spawn.call_count==0
