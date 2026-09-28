"""Portable, bounded reuse proof for the twelve registered Joern controls.

No native process is launched. This is exact AST and recorded-input comparison,
not general program equivalence or retroactive resource qualification.
"""
import ast
import os
from pathlib import Path
import shlex
from unittest.mock import patch

from swift_normal_reports_v1 import read, require, bound_file, load_population
from joern_normal_execution_v1 import env_for, compiler_argv, frontend_argv, query_argv

AMENDMENT='adapters/joern/swift-normal-v1/execution-revalidation-2026-09-28-02/amendment.json'
EXECUTION='scripts/joern_normal_execution_v1.py'
# These exact new bytes require review and a bound amendment, not a blanket
# exemption from compatibility checks whenever orchestration changes.
REVIEWED=[
    'scripts/joern_normal_runner_v1.py', 'scripts/joern_normal_reports_v1.py',
    'scripts/run-joern-normal-v1.py', 'scripts/swift_normal_reports_v1.py',
    'scripts/swift_normal_runner_v1.py', 'scripts/swift_artifact_closure.py',
    'adapters/joern/swift-normal-v1/README.md',
]


def normalized(node):
    return ast.dump(node, include_attributes=False)


def verify_ast(old_source, new_source):
    old=ast.parse(old_source);new=ast.parse(new_source)
    functions={n.name:n for n in old.body if isinstance(n,ast.FunctionDef)}
    current={n.name:n for n in new.body if isinstance(n,ast.FunctionDef)}
    require(set(current)=={'env_for','compiler_argv','frontend_argv','query_argv'},'execution function membership')
    # Closed module shape prevents rebinding os, dict, functions or constants.
    allowed=ast.parse('import os\nBASE="adapters/joern/swift-normal-v1"').body
    actual=[n for n in new.body if not isinstance(n,ast.FunctionDef) and not (isinstance(n,ast.Expr) and isinstance(n.value,ast.Constant) and isinstance(n.value.value,str))]
    require([normalized(n) for n in actual]==[normalized(n) for n in allowed],'execution imports/constants changed')
    require(any(normalized(n)==normalized(allowed[0]) for n in old.body),'registered os import missing')
    require(normalized(functions['env_for'])==normalized(current['env_for']),'environment function AST changed')
    run=functions['run_case']
    compiler=next(n.value for n in ast.walk(run) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='argv' for t in n.targets))
    calls={n.args[2].value:n.args[0] for n in ast.walk(run) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='phase' and len(n.args)>2 and isinstance(n.args[2],ast.Constant)}
    # Substitute only local aliases whose original assignments are checked.
    require("source=directory/'DataFlowBenchTaintSwift'" in old_source and "cpg=directory/'cpg.bin'" in old_source,'registered path aliases changed')
    class Paths(ast.NodeTransformer):
        def visit_Name(self,node):
            if node.id=='cpg':return ast.parse("directory/'cpg.bin'",mode='eval').body
            if node.id=='source':return ast.parse("directory/'DataFlowBenchTaintSwift'",mode='eval').body
            return node
    for name,args,expression in [('compiler_argv','rt,case,directory',compiler),('frontend_argv','rt,directory',calls['frontend']),('query_argv','root,rt,directory',calls['query'])]:
        expected=ast.parse('def '+name+'('+args+'):\n    return '+ast.unparse(Paths().visit(expression))).body[0]
        require(normalized(current[name])==normalized(expected),'invocation function AST changed:'+name)


def verify(root, reference=None, prospective_plan=None):
    amendment_path=bound_file(root,reference) if reference else root/AMENDMENT
    amendment=read(amendment_path)
    require(amendment.get('schema')=='joern-execution-revalidation/v1','execution amendment required')
    require(amendment.get('environment_limitations')=={'JAVA_OPTS':'unobserved; registered-code equivalence only','LANG':'unobserved; registered-code equivalence only','LC_ALL':'unobserved; registered-code equivalence only','aggregate_memory':'unqualified'},'missing environment limitations')
    control=read(bound_file(root,amendment['control_plan']))
    plan=read(bound_file(root,control['plan']))
    run=read(bound_file(root,amendment['control_run']))
    require(run['controls_sha256']==amendment['control_plan']['sha256'] and run['plan_sha256']==control['plan']['sha256'],'execution control binding')
    require(run['ended_at_unix_seconds']<amendment['registered_at_unix_seconds'],'amendment chronology')
    old=bound_file(root,amendment['registered_runner'])
    refs={r['path']:r['sha256'] for rows in plan['configurations'].values() for r in rows}
    require(amendment['registered_runner']['sha256']==refs['scripts/joern_normal_runner_v1.py'],'registered runner is not control-plan source')
    module=bound_file(root,amendment['execution_module'])
    require(amendment['execution_module']['path']==EXECUTION,'execution module path')
    reviewed=amendment['reviewed_files']
    require(len(reviewed)==len(REVIEWED)+1 and {r['path'] for r in reviewed}==set(REVIEWED+['scripts/joern_execution_revalidation_v1.py']),'reviewed closure membership')
    for r in reviewed:bound_file(root,r)
    verify_ast(old.read_text(),module.read_text())
    # Old semantic dependencies remain byte-exact; only listed reviewed files
    # may differ, and their replacement bytes were checked above.
    for rows in plan['configurations'].values():
        for r in rows:
            if r['path'] not in REVIEWED:bound_file(root,r)
    _,cases,_=load_population(root)
    population=read(root/'populations/swift-synthetic-v3.json')
    paths={c['id']:root/c['path'] for c in population['cases']}
    execution_root=Path(amendment['recorded_execution_root'])
    require(execution_root.is_absolute(),'absolute recorded root required')
    expected={(label,arm) for label in control['controls'] for arm in ('off','on')}
    require(len(run['records'])==12 and {(r['control'],r['arm']) for r in run['records']}==expected,'execution matrix membership')
    for row in run['records']:
        require(row['case_id']==control['controls'][row['control']],'execution case routing')
        raw_path=bound_file(root,row['raw']);raw=read(raw_path)
        directory=raw_path.parent;recorded=execution_root/directory.relative_to(root)
        case=cases[row['case_id']];rt=plan['runtime']
        generated=[compiler_argv(rt,case,recorded),frontend_argv(rt,recorded),query_argv(execution_root,rt,recorded)]
        outputs={r['path']:bound_file(root,r) for r in raw['native_outputs']}
        for name in ('build.log','fixture-hashes.json','source-closure.json'):
            require(str((directory/name).relative_to(root)) in outputs,'unbound execution input:'+name)
        require((directory/'build.log').read_text()==shlex.join(generated[0])+'\n','build log invocation changed')
        from swift_normal_reports_v1 import sha
        hashes={n:sha(paths[row['case_id']].parent/n) for n in case['fixture_files']}
        require(read(directory/'fixture-hashes.json')==hashes,'execution fixture hashes changed')
        require({n:sha(directory/'DataFlowBenchTaintSwift'/n) for n in case['fixture_files']}==hashes,'staged execution source changed')
        require(len(raw['commands'])==3,'three recorded execution phases required')
        for r,argv in zip(raw['commands'],generated):
            command=read(bound_file(root,r))
            require(command['argv']==argv and command['cwd']==str(recorded),'recorded invocation changed')
            require(command['measurement_wrapper']==[],'unexpected measurement wrapper')
            observed=command['environment']
            require(set(observed)=={'JAVA_HOME','SWIFTASTGEN_BIN','_JAVA_OPTIONS','PATH'},'recorded environment witness shape')
            # PATH is an observed ambient input. Other unrecorded ambient values
            # are not invented. env_for AST equivalence checks fixed JAVA_OPTS.
            with patch.dict(os.environ,{'PATH':amendment['recorded_path']},clear=True):env=env_for(rt)
            require(observed=={k:env.get(k) for k in observed},'recorded environment changed')
    if prospective_plan is not None:
        require(amendment['registered_at_unix_seconds']<=prospective_plan['registered_at_unix_seconds'],'amendment must precede prospective plan')
        current={r['path']:r['sha256'] for rows in prospective_plan['configurations'].values() for r in rows}
        for r in [amendment['execution_module'],*reviewed]:
            require(current.get(r['path'])==r['sha256'],'prospective execution closure changed')
        require(current.get(AMENDMENT)==reference['sha256'],'prospective amendment not bound')
    return amendment
