"""Current observer actual-function tests, synthetic ancestry only; no JVM."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from test_native_control_observer_v07 import observer_module as m, witness, sync_ancestry

ROOT = Path('/Users/dave/.codex/worktrees/9f01/dataflowbench')
ACTUAL = ROOT / 'reports/releases/v0.9.2/qualification/joern-post-bifrost-01/native-controls-04'


class AncestryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='joern-v5-ancestry-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.observer = m.StartupObserver(self.root, self.root/'capture', m.STARTUP_POLICY_V5, static_check=False)
        self.observer.ensure_home()
        self.event = self.root/'event'; self.event.mkdir()
        self.record = {'tracked_descendants': [{'pid': 80, 'start_identity': '1704067200:123456'},
                                              {'pid': 1001, 'start_identity': '1704067200:123456'}]}
        witness(self.observer, self.event, 1001, 'io.joern.joerncli.console.ReplBridge')
        witness(self.observer, self.event, 100, None, parent_pid=90,
                parent_identity='2024-01-01T00:00:00.123Z')
        self.path = self.event/'jvm-100.json'
        self.payload = json.loads(self.path.read_text())
        n0 = self.payload['ancestry']['nodes'][0]
        n1 = copy.deepcopy(n0); n1['pid'] = 90; n1['parent_pid'] = 80
        self.payload['ancestry']['nodes'] = [n0,n1]
        self.payload['ancestry']['failure_at_depth'] = 1
        self.write()

    def write(self): self.path.write_text(json.dumps(self.payload))

    def read(self, phase='version', record=None, host=None):
        self.write()
        return self.observer._witnesses(self.event, phase, record or self.record,
                                       host, '1704067200:123456' if host else None)

    def rejected(self, fragment=None, **kwargs):
        with self.assertRaises(m.ObservationError) as caught: self.read(**kwargs)
        if fragment: self.assertIn(fragment, str(caught.exception))

    def test_untracked_version_exact_tracked_ancestor_is_diagnostic_only(self):
        diagnostic = next(x for x in self.read() if x['pid']==100)
        self.assertFalse(diagnostic['birth_verified'])
        self.assertTrue(diagnostic['diagnostic_only'])
        correlation = diagnostic['ancestry_correlation']
        self.assertEqual(correlation['anchor_pid'],80)
        self.assertEqual(correlation['anchor_source'],'native-tracked')
        self.assertEqual(correlation['birth_comparison'],'java-millisecond-floor')
        self.assertFalse(correlation['complete_descendant_coverage'])
        self.assertNotIn(100,[x['pid'] for x in self.record['tracked_descendants']])

    def test_terminal_parent_edge_can_bind_exact_invocation_host(self):
        record = {'tracked_descendants':[self.record['tracked_descendants'][1]]}
        diagnostic = next(x for x in self.read(record=record,host=80) if x['pid']==100)
        self.assertEqual(diagnostic['ancestry_correlation']['anchor_source'],'invocation-host')

    def test_foreign_unanchored_chain_rejected(self):
        self.payload['ancestry']['nodes'][1]['parent_pid']=70
        self.rejected('no exact invocation anchor')

    def test_first_pid_wrong_birth_cannot_skip_to_later_anchor(self):
        self.record['tracked_descendants'].insert(0,{'pid':90,'start_identity':'1704067200:124000'})
        self.rejected('parent pid/birth is not tracked')

    def test_recycled_host_birth_rejected(self):
        self.payload['ancestry']['nodes'][1]['parent_pid']=70
        self.payload['ancestry']['nodes'][1]['parent_start_epoch_nanos']=122000000
        self.payload['ancestry']['nodes'][1]['parent_start_identity']='2024-01-01T00:00:00.122Z'
        self.rejected('anchor PID/birth differs',host=70)

    def test_bool_pid_and_birth_and_failure_depth_rejected(self):
        for change in [('pid',True),('process_start_epoch_nanos',True)]:
            with self.subTest(change=change):
                before=copy.deepcopy(self.payload)
                self.payload['ancestry']['nodes'][0][change[0]]=change[1]
                self.rejected(); self.payload=before
        self.payload['ancestry']['failure_at_depth']=True
        self.rejected('failure depth')

    def test_missing_link_extra_fields_wrong_agent_schema_rejected(self):
        original=copy.deepcopy(self.payload)
        for mutation in [lambda d:d['ancestry']['nodes'][1].update(pid=91),
                         lambda d:d['ancestry'].update(extra=True),
                         lambda d:d['ancestry']['nodes'][0].update(extra=True),
                         lambda d:d.update(agent_version='anything'),
                         lambda d:d.update(schema='v092-joern-jvm-startup-witness/v4')]:
            with self.subTest(mutation=mutation):
                self.payload=copy.deepcopy(original);mutation(self.payload);self.rejected()

    def test_cycle_repeated_pid_and_inconsistent_sampling_rejected(self):
        self.payload['ancestry']['nodes'][1]['parent_pid']=100
        # Edge to a previously seen PID is invalid even when it would be above an anchor.
        self.rejected()
        self.payload['ancestry']['termination']='inconsistent';self.rejected('inconsistent')

    def test_unavailable_before_anchor_rejected(self):
        self.payload['ancestry']['nodes']=self.payload['ancestry']['nodes'][:1]
        self.payload['ancestry']['failure_at_depth']=0
        self.rejected('no exact invocation anchor')

    def test_truncation_before_anchor_rejected_at_exact_bound(self):
        sample=copy.deepcopy(self.payload['ancestry']['nodes'][0])
        nodes=[]
        for i in range(32):
            n=copy.deepcopy(sample);n['pid']=100+i;n['parent_pid']=101+i;nodes.append(n)
        self.payload.update(pid=100,parent_pid=101)
        self.payload['ancestry'].update(nodes=nodes,termination='truncated',failure_at_depth=31)
        self.rejected('no exact invocation anchor')
        self.payload['ancestry']['nodes'].append(copy.deepcopy(nodes[-1]));self.rejected('node bound')

    def test_actual_helper_accepts_32nd_edge_anchor_rejects_33rd(self):
        # Each node contains one parent edge.32nodes expose at most32edges.
        # No production helper is patched; invoke actual _witnesses and its
        # _validate_ancestry/_ancestry_anchor path with synthetic birth data.
        template=copy.deepcopy(self.payload['ancestry']['nodes'][0])
        nodes=[]
        for i in range(32):
            node=copy.deepcopy(template)
            node['pid']=100+i;node['parent_pid']=101+i;nodes.append(node)
        self.payload.update(pid=100,parent_pid=101)
        self.payload['ancestry'].update(nodes=nodes,termination='truncated',failure_at_depth=31)
        diagnostic=next(row for row in self.read(host=132) if row['pid']==100)
        correlation=diagnostic['ancestry_correlation']
        self.assertEqual(correlation['anchor_pid'],132)
        self.assertEqual(len(correlation['validated_prefix']),32)
        self.assertFalse(diagnostic['birth_verified'])
        self.assertTrue(correlation['diagnostic_only'])
        self.rejected('no exact invocation anchor',host=133)
        # The former33node payload must now fail the bound before it can
        # admit the terminal33rd edge, even with that exact host PID/birth.
        node=copy.deepcopy(template);node.update(pid=132,parent_pid=133)
        nodes.append(node)
        self.payload['ancestry']['failure_at_depth']=32
        self.rejected('node bound',host=133)

    def test_missing_parent_birth_never_makes_trusted_anchor(self):
        n=self.payload['ancestry']['nodes'][1]
        for suffix in ('_identity','_epoch_seconds','_epoch_nanos'):n['parent_start'+suffix]=None
        self.rejected('no exact invocation anchor')

    def test_suffix_unavailable_after_verified_anchor_does_not_claim_completeness(self):
        self.assertEqual(self.read()[0]['ancestry_correlation']['sample_termination'],'unavailable')

    def test_wrong_directory_and_impossible_parent_birth_rejected(self):
        self.payload['witness_directory_b64']=m._b64('/foreign');self.rejected('directory')
        self.payload['witness_directory_b64']=m._b64(str(self.event))
        n=self.payload['ancestry']['nodes'][1]
        n['parent_start_epoch_nanos']=124000000
        n['parent_start_identity']='2024-01-01T00:00:00.124Z'
        self.rejected('ancestor born after child')

    def test_semantic_self_missing_native_tracking_cannot_use_chain(self):
        self.payload['java_command_present']=True
        self.payload['java_command_b64']=m._b64('replpp.scripting.NonForkingScriptRunner')
        self.rejected('semantic JVM birth was not tracked')

    def test_command_present_version_cannot_get_new_ancestry_exception(self):
        self.payload['java_command_present']=True
        self.payload['java_command_b64']=m._b64('-version')
        self.rejected('outside the invocation')

    def test_self_tracked_semantic_cannot_use_ancestry_for_untracked_parent(self):
        self.record['tracked_descendants'].append({'pid':100,'start_identity':'1704067200:123456'})
        self.payload['java_command_present']=True
        self.payload['java_command_b64']=m._b64('replpp.scripting.NonForkingScriptRunner')
        self.rejected('outside the invocation',phase='query')

    def test_self_tracked_version_cannot_expand_direct_parent_rule(self):
        self.record['tracked_descendants'].append({'pid':100,'start_identity':'1704067200:123456'})
        self.rejected('outside the invocation')

    def test_helper_cannot_satisfy_missing_semantic_required_role(self):
        (self.event/'jvm-1001.json').unlink()
        self.rejected('missing required semantic roles')

    def test_exact_policy_and_unsealed_jar_fail_runtime_closed(self):
        policy=copy.deepcopy(m.STARTUP_POLICY_V5);policy['ancestry']['maximum_links']=31
        with self.assertRaises(m.ObservationError):
            m.StartupObserver(self.root,self.root/'other',policy,static_check=False)
        self.assertEqual(m._policy_agent(m.STARTUP_POLICY_V5),
                         (Path(m.AGENT_PATH).resolve(),
                          '1e30a6a5c88abb0216c5f205bd337f18fc30dd91345a8aeae244398cc0803261'))
        unsealed=copy.deepcopy(m.STARTUP_POLICY_V5)
        unsealed['agent_jar']['sha256']='UNSEALED'
        with self.assertRaisesRegex(m.ObservationError,'not sealed'):
            m._policy_agent(unsealed)

    def test_retained_actual_failure_replays_unchanged_old_body_and_new_rejects_v4(self):
        source=ROOT/'reports/releases/v0.9.2/acquisition/joern-native-startup-observer-06.py'
        spec=importlib.util.spec_from_file_location('retained_observer06_actual_failure',source)
        old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
        observation=json.loads((ACTUAL/'capture.startup-observation/004-query.json').read_text())
        event=ACTUAL/'capture.startup-observation/events/004-query'
        record=json.loads((ACTUAL/'capture/dfb-taint-swift-model-opaque-propagator-negative/off/query.command.json').read_text())
        before={p.name:m.sha(p) for p in event.iterdir()}
        prior=old.StartupObserver(ROOT,ACTUAL/'capture',old.STARTUP_POLICY_V4,
                                 sidecar_root=self.root/'old-sidecars',static_check=False)
        with self.assertRaisesRegex(old.ObservationError,'outside the invocation: jvm-99172.json'):
            prior._witnesses(event,'query',record,95468,observation['invocation_parent']['start_identity'])
        current=m.StartupObserver(ROOT,ACTUAL/'capture',m.STARTUP_POLICY_V5,
                                  sidecar_root=self.root/'new-sidecars',static_check=False)
        with self.assertRaisesRegex(m.ObservationError,'schema mismatch'):
            current._witnesses(event,'query',record,95468,observation['invocation_parent']['start_identity'])
        self.assertEqual(before,{p.name:m.sha(p) for p in event.iterdir()})


if __name__=='__main__': unittest.main()
