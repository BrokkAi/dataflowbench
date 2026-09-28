#!/usr/bin/env python3
"""Prospective controls and phase failure tests; never invoke an analyzer."""
import copy
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch
from joern_normal_controls_v1 import config_for, observe, assess_controls, WRAPPERS
from joern_normal_runner_v1 import ROOT, phase, capacity, RESERVE, SCRATCH, execute
from swift_normal_reports_v1 import load_population


class Controls(unittest.TestCase):
    def test_capacity_and_unresolved_partition(self):
        capacity(RESERVE);capacity(RESERVE+SCRATCH,True)
        for value,launch in [(RESERVE-1,False),(RESERVE+SCRATCH-1,True)]:
            with self.assertRaises(ValueError):capacity(value,launch)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'plan.json').write_text(json.dumps({'partition_status':'unresolved'}))
            with patch('joern_normal_runner_v1.process.run') as native:
                with self.assertRaisesRegex(ValueError,'Incomplete'):execute(root,'plan.json',root/'out',{})
                native.assert_not_called()

    def test_four_exact_control_mappings(self):
        _,cases,_=load_population(ROOT)
        ids=[i for i in cases if 'opaque-propagator' in i or 'propagator-position' in i]
        self.assertEqual(len(ids),4)
        for identity in ids:
            on=config_for(ROOT,cases[identity]);off=config_for(ROOT,cases[identity],'off')
            self.assertEqual(off['semantics'],[])
            self.assertEqual(on['wrappers'],WRAPPERS)
            self.assertEqual(on['semantics'][0]['flows'],[[1,-1]])
            self.assertEqual(on['semantics'][1]['flows'],[])
            self.assertEqual(on['semantics'][2]['flows'],[[2,-1]])
            self.assertEqual(on['source_anchors'],cases[identity]['source_anchors'])
            self.assertEqual(on['selected_wrapper'],off['selected_wrapper'])

    def test_real_endpoint_evidence_and_missing_wrapper_proof(self):
        base=ROOT/'evidence/joern-swift/model-activation-219/attempt-06/direct-negative/on'
        graph=json.loads((base/'graph.json').read_text());config=json.loads((base/'config.json').read_text())
        graph['wrapper_evidence']=[];config.update(wrappers=[],selected_wrapper='')
        self.assertEqual(observe(graph,config)[0],'not-reached')
        config['wrappers']=WRAPPERS
        self.assertEqual(observe(graph,config)[0],'inconclusive')
        config['wrappers']=[]
        graph['source_method_ids']=graph['sink_method_ids']
        self.assertEqual(observe(graph,config)[0],'inconclusive')

    def test_wrapper_native_join_rejects_same_name_wrong_owner_and_position(self):
        base=ROOT/'evidence/joern-swift/model-activation-219/attempt-06/direct-negative/on'
        graph=json.loads((base/'graph.json').read_text());config=json.loads((base/'config.json').read_text())
        spec=copy.deepcopy(WRAPPERS[2]);config.update(wrappers=[spec],selected_wrapper=spec['method'])
        method={'id':'wrapper','full_name':spec['method'],'external':False,'node':{'id':'wrapper'},'parameters':[{'index':i,'type':spec['owner'] if i==0 else 'Swift.String','node':{'id':'p'+str(i)}} for i in [0,1,2]]}
        graph['methods'].append(method)
        graph['wrapper_evidence']=[{'method_id':'wrapper','owner_id':'owner','owner_full_name':spec['owner'],'owner_ast_method_ids':['wrapper'],'return_types':['Swift.String']}]
        anchor=config['sink_anchors'][0]
        graph['calls'].append({'node':{'id':'wrapper-call','file':anchor['file'],'line':anchor['line_hint']},'callee_ids':['wrapper'],'method_full_name':spec['method'],'arguments':[{'index':i,'node':{'id':'a'+str(i)}} for i in [0,1,2]]})
        self.assertEqual(observe(graph,config)[0],'not-reached')
        for kind in ['owner','callee','position','return','type','receiver-type']:
            bad=copy.deepcopy(graph)
            if kind=='owner':bad['wrapper_evidence'][0]['owner_ast_method_ids']=[]
            if kind=='callee':bad['calls'][-1]['callee_ids']=['same-name-decoy']
            if kind=='position':bad['calls'][-1]['arguments'][-1]['index']=0
            if kind=='type':bad['methods'][-1]['parameters'][2]['type']='Swift.Int'
            if kind=='receiver-type':bad['methods'][-1]['parameters'][0]['type']='Other.Owner'
            if kind=='return':bad['wrapper_evidence'][0]['return_types']=['Swift.Int']
            with self.subTest(kind=kind):self.assertEqual(observe(bad,config)[0],'inconclusive')

    def test_control_closure_rejects_query_model_and_runtime_drift(self):
        from joern_normal_runner_v1 import control_semantics, ref, write
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'query.sc').write_text('query');(root/'models.py').write_text('models')
            write(root/'tree.json',{'binary':{'sha256':'abc','mode':493}})
            write(root/'contract.json',{'total_wall_clock_seconds':75})
            plan={'execution_contract':ref(root,root/'contract.json'),'configurations':{'test':[ref(root,root/'query.sc'),ref(root,root/'models.py')]},'runtime':{'joern':'/pinned/joern','inventories':{'joern_root':ref(root,root/'tree.json')}}}
            before=control_semantics(root,plan)
            for name in ['query.sc','models.py']:
                original=(root/name).read_text();(root/name).write_text('changed')
                with self.assertRaisesRegex(ValueError,'semantic file'):control_semantics(root,plan)
                (root/name).write_text(original)
            changed=copy.deepcopy(plan);changed['runtime']['joern']='/other/joern'
            self.assertNotEqual(before,control_semantics(root,changed))
            write(root/'tree.json',{'binary':{'sha256':'foreign','mode':493}})
            changed=copy.deepcopy(plan);changed['runtime']['inventories']['joern_root']=ref(root,root/'tree.json')
            self.assertNotEqual(before,control_semantics(root,changed))

    def test_query_failure_is_not_endpoint_incompleteness(self):
        self.assertEqual(observe({'state':'runner-error','error':'query failed'},{}),('runner-error',['QueryRuntimeError:query failed']))
        self.assertEqual(observe({'state':'analyzed','query_completed':False},{})[0],'runner-error')
        self.assertEqual(observe({'state':'incomplete','identity_status':'incomplete','error':'missing owner'},{})[0],'inconclusive')

    def test_matrix_is_load_bearing_and_cannot_omit_a_control(self):
        matrix={'direct-positive':{'off':'reached','on':'reached'},'direct-negative':{'off':'not-reached','on':'not-reached'},
          'dfb-taint-swift-model-opaque-propagator-positive':{'off':'not-reached','on':'reached'},
          'dfb-taint-swift-model-opaque-propagator-negative':{'off':'reached','on':'not-reached'},
          'dfb-taint-swift-model-propagator-position-positive':{'off':'not-reached','on':'reached'},
          'dfb-taint-swift-model-propagator-position-negative':{'off':'not-reached','on':'not-reached'}}
        self.assertEqual(assess_controls(matrix)['status'],'bounded-controls-observed')
        changed=copy.deepcopy(matrix);changed['dfb-taint-swift-model-opaque-propagator-positive']['off']='reached'
        self.assertEqual(assess_controls(changed)['status'],'incomplete')
        changed.pop('direct-negative')
        with self.assertRaises(ValueError):assess_controls(changed)

    def test_case_timeout_and_uncertain_cleanup_retain_failed_prefix(self):
        from joern_normal_runner_v1 import run_case, write
        case={'template_id':'dfb-template-model-opaque-propagator','polarity':'positive','model_profile':'benchmark-controlled','source_anchors':[],'sink_anchors':[],'fixture_files':['main.swift']}
        rt={k:'/fake/'+k for k in ['joern','frontend','compiler','sdk','java_home','astgen']}
        for reason in ['BudgetExhausted','UncertainCleanup']:
            with tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);fixture=root/'fixture';fixture.mkdir();(fixture/'main.swift').write_text('let x = 1')
                def fail(argv,directory,name,deadline,env):
                    write(directory/(name+'.command.json'),{'argv':argv,'phase_id':name,'role':'analysis','exit_status':1,'timed_out':reason=='BudgetExhausted','elapsed_seconds':1,'deadline_seconds':75,'cleanup_status':'uncertain' if reason=='UncertainCleanup' else 'tracked-processes-stopped'})
                    (directory/(name+'.stderr')).write_text('retained')
                    if reason=='BudgetExhausted':raise TimeoutError(reason)
                    raise ValueError(reason)
                with patch('joern_normal_runner_v1.phase',side_effect=fail),patch('joern_normal_runner_v1.snapshot',side_effect=OSError('closure failed')):
                    raw,stop=run_case(root,{'runtime':rt},fixture/'case.json',case,root/'out')
                self.assertTrue(stop);self.assertIn(reason,raw['diagnostics'])
                self.assertTrue(any(d.startswith('ArtifactClosureFailed:') for d in raw['diagnostics']))
                self.assertEqual(len(raw['commands']),1)
                self.assertEqual(raw['raw_outcome'],'inconclusive' if reason=='BudgetExhausted' else 'runner-error')
                self.assertTrue(any(r['path'].endswith('stderr') for r in raw['native_outputs']))

    def test_phase_shared_deadline_and_failure_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory=Path(tmp)
            def invoke(argv,path,name,timeout,**kwargs):
                self.assertLessEqual(timeout,1)
                return {'argv':argv,'exit_status':1,'timed_out':False,'elapsed_seconds':0.1,'deadline_seconds':timeout,'cleanup_status':'tracked-processes-stopped'}
            with patch('joern_normal_runner_v1.capacity'):
                with self.assertRaisesRegex(ValueError,'CommandFailed'):phase(['fake'],directory,'frontend',time.monotonic()+1,{},invoke)
            record=json.loads((directory/'frontend.command.json').read_text())
            self.assertEqual(record['phase_id'],'frontend');self.assertEqual(record['role'],'analysis')
            with self.assertRaises(TimeoutError):phase(['fake'],directory,'query',time.monotonic()-1,{},invoke)


if __name__=='__main__':unittest.main()
