#!/usr/bin/env python3
"""Synthetic completed and failed command artifacts exercise replay without corpus runs."""
import copy,json,shlex,tempfile,unittest,zipfile
from pathlib import Path
from swift_v3_verify import verify_case

class Verify(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.base=Path(self.tmp.name)
        self.paths={'output':'/original/run','repository':'/repo','cli':'/tools/codeql','compiler':'/tools/swiftc','sdk':'/sdk','packs':'/packs','native_packs':'/native'}
        self.case={'id':'case','fixture_files':['main.swift'],'model_profile':'benchmark-controlled','template_id':'direct','score_tier':'core','source_anchors':[{'file':'main.swift','line_hint':1}],'sink_anchors':[{'file':'main.swift','line_hint':3}]}
        self.original=Path('/original/run/case');db=self.original/'database';cli='/tools/codeql'
        compiler=['/tools/swiftc','-swift-version','6','-Onone','-sdk','/sdk','-target','arm64-apple-macosx26.5','-module-name','DataFlowBenchTaintSwift','-module-cache-path',str(self.original/'cache'),str(self.original/'source/main.swift'),'-o',str(self.original/'never-executed')]
        commands={'extract':self.record([cli,'database','create',str(db),'--language=swift','--source-root='+str(self.original/'source'),'--threads=2','--ram=2048','--command='+shlex.join(compiler)],150),
                  'resolve-database':self.record([cli,'resolve','database','--format=json',str(db)],30)}
        elapsed=0
        for name in ['roles','flow']:
            commands[name]=self.record([cli,'query','run','/repo/adapters/codeql/swift-v3/queries/kernel-'+name+'.ql','--database='+str(db),'--output='+str(self.original/(name+'.bqrs')),'--additional-packs=/packs','--threads=2','--ram=2048','--timeout='+str(60-elapsed)],60-elapsed);elapsed+=1
            commands[name+'-decode']=self.record([cli,'bqrs','decode',str(self.original/(name+'.bqrs')),'--format=json','--output='+str(self.original/(name+'.json'))],60-elapsed);elapsed+=1
        self.raw={'execution_status':'completed','commands':commands,'lane':'kernel','outcome':'reached','diagnostics':[],'analysis_elapsed_seconds':4,
                  'rows':{'roles':[['main.swift',1,1,'source'],['main.swift',3,1,'sink']],'flow':[['main.swift',1,'main.swift',3,1]]}}
        (self.base/'source').mkdir();(self.base/'source/main.swift').write_text('source\n\nsink\n')
        (self.base/'database/log/swift/extractor').mkdir(parents=True)
        (self.base/'database/log/swift/extractor/extract.log').write_text('INFO extracted\n')
        (self.base/'database/codeql-database.yml').write_text('finalised: true\n')
        (self.base/'resolve-database.stdout').write_text(json.dumps({'languages':['swift'],'datasetFolder':str(db/'db-swift')}))
        with zipfile.ZipFile(self.base/'database/src.zip','w') as z:z.write(self.base/'source/main.swift','original/source/main.swift')
        for n,rows in self.raw['rows'].items():
            (self.base/(n+'.json')).write_text(json.dumps({'#select':{'tuples':rows}}));(self.base/(n+'.bqrs')).write_bytes(b'BQRS-placeholder')
        self.sync()
    def record(self,argv,deadline):return {'argv':argv,'elapsed_seconds':1,'deadline_seconds':deadline,'exit_status':0,'timed_out':False,'cleanup_status':'tracked-processes-stopped'}
    def sync(self):
        for n,r in self.raw['commands'].items():(self.base/(n+'.command.json')).write_text(json.dumps(r))
    def check(self):verify_case(Path('/repo'),self.base,self.case,self.raw,self.paths)
    def test_complete(self):self.check()
    def test_empty_complete(self):
        self.raw['commands']={}
        with self.assertRaisesRegex(ValueError,'phase prefix'):self.check()
    def test_wrong_query_database_source_runtime(self):
        for phase,index,value in [('flow',3,'/foreign/query.ql'),('flow',4,'--database=/foreign'),('extract',5,'--source-root=/foreign'),('extract',0,'/foreign/codeql'),('extract',8,'--command=/foreign/swiftc')]:
            with self.subTest(phase=phase,index=index):
                original=copy.deepcopy(self.raw);self.raw['commands'][phase]['argv'][index]=value;self.sync()
                with self.assertRaises(ValueError):self.check()
                self.raw=original;self.sync()
    def test_rehashed_outcome_and_rows_not_trusted(self):
        self.raw['outcome']='not-reached'
        with self.assertRaisesRegex(ValueError,'derived observation'):self.check()
        self.raw['outcome']='reached';self.raw['rows']['flow']=[]
        with self.assertRaisesRegex(ValueError,'decoded row'):self.check()
    def test_missing_archive(self):
        (self.base/'database/src.zip').unlink()
        with self.assertRaisesRegex(ValueError,'source archive'):self.check()
    def test_budget_overrun(self):
        self.raw['analysis_elapsed_seconds']=61
        with self.assertRaisesRegex(ValueError,'analysis overrun'):self.check()
    def test_finalization_and_logs(self):
        (self.base/'database/codeql-database.yml').write_text('finalised: false\n')
        with self.assertRaisesRegex(ValueError,'finalization'):self.check()
        (self.base/'database/codeql-database.yml').write_text('finalised: true\n');(self.base/'database/log/swift/extractor/extract.log').write_text('ERROR incomplete\n')
        with self.assertRaisesRegex(ValueError,'log integrity'):self.check()
    def test_valid_timeout_prefix_and_wrong_type(self):
        self.raw.update(execution_status='attempted',failure_kind='timeout',outcome='inconclusive',diagnostics=['BudgetExhausted:extract'])
        self.raw['commands']={'extract':self.raw['commands']['extract']};self.raw['commands']['extract'].update(timed_out=True,exit_status=-15,elapsed_seconds=150.1);self.sync();self.check()
        self.raw['outcome']='reached'
        with self.assertRaisesRegex(ValueError,'failure outcome'):self.check()
    def test_cleanup_prefix_and_unknown_status(self):
        self.raw.update(execution_status='attempted',failure_kind='cleanup',outcome='runner-error',diagnostics=['UncertainCleanup'])
        self.raw['commands']={'extract':self.raw['commands']['extract']};self.raw['commands']['extract']['cleanup_status']='uncertain';self.sync();self.check()
        self.raw['execution_status']='magic'
        with self.assertRaisesRegex(ValueError,'execution status'):self.check()

if __name__=='__main__':unittest.main(verbosity=2)
