"""Read-only exact policy and full historical capacity accounting. No replay."""
from pathlib import Path
import contextlib,fcntl,importlib.util,json,os,stat,sys

def load_exact(root,ref,stable,name):
 stable(root,ref);spec=importlib.util.spec_from_file_location(name,Path(root)/ref['path']);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);stable(root,ref);return m

@contextlib.contextmanager
def observe_existing_lock(path):
 path=Path(path)
 for part in [path,*path.parents]:
  if part.is_symlink():raise ValueError('lock contains symlink')
 fd=os.open(path,os.O_RDONLY|getattr(os,'O_NOFOLLOW',0))
 try:
  before=os.fstat(fd)
  if not stat.S_ISREG(before.st_mode):raise ValueError('lock is not regular')
  fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
  now=path.lstat()
  if (before.st_dev,before.st_ino)!=(now.st_dev,now.st_ino):raise ValueError('canonical lock identity changed')
  yield {'path':str(path),'dev':before.st_dev,'ino':before.st_ino,'existing_only':True,'fd':fd}
 finally:os.close(fd)

def accounting_paths(root,contract,executor,protocol):
 root=Path(root).resolve();base=root/Path(*executor.EXECUTION_ROOT.parts)
 # Existing API accounts original cache, prior HOME/TMP and current-contract
 # output roots. A nonexistent hypothetical future root is not materialized.
 future=base/'qualification-capacity-observation'
 retained,scratch=executor._matrix_capacity_paths({'repo_root':root,'plan':contract},future,{'HOME':str(future/'home'),'TMPDIR':str(future/'tmp')},[])
 rows=executor._ledger_rows(root/Path(*executor.LEDGER_PATH.parts));sources=set()
 groups={g['id']:g for g in contract['groups']}
 for row in rows:
  previous=Path(row['execution_root'])
  if not previous.is_absolute() or not executor._under(previous,base):raise ValueError('historical execution root escapes task namespace')
  sources.add(previous)
  for output in row.get('output_roots',[]):retained.append(previous/Path(*protocol._relative(output,'historical output').parts))
 if base.exists():
  for series in base.iterdir():
   if series.is_symlink() or not series.is_dir():raise ValueError('unsafe execution series')
   for group in series.iterdir():
    if group.is_symlink() or not group.is_dir() or group.name not in groups:raise ValueError('unsafe execution group')
    for attempt in group.iterdir():
     if attempt.is_symlink() or not attempt.is_dir():raise ValueError('unsafe execution attempt')
     sources.add(attempt);scratch.extend([attempt/'home',attempt/'tmp'])
     retained.extend(attempt/Path(*protocol._relative(output,'unclosed/current output').parts) for output in groups[group.name]['output_roots'])
 members=tuple(executor.SNAPSHOT_DIRECTORIES)+tuple(executor.SNAPSHOT_FILES)+tuple(x['path'] for x in contract['source_inputs'])+('.git',)
 working=[source/Path(*protocol._relative(member,'working source member').parts) for source in sources for member in members]
 return {'scratch':scratch,'retention':retained,'working':working}

def evaluate(root,core,contract,*,admission,protocol,bridge,executor,disk):
 # Real admission policy equality+digest and real no-expiry/30GiB authorities.
 live=admission._live_resources(Path(root),core)
 authority=protocol.validate_working_cap(Path(root),core)
 unchanged=authority['unchanged'];policy=live['resource_policy'];gib=1024**3
 if live['resource_policy_sha256']!=admission._policy_sha(core['resource_policy']):raise ValueError('resource policy digest differs')
 limits={'launch':policy['minimum_free_gib']*gib,'reserve':unchanged['protected_reserve_bytes'],'stop':unchanged['stop_free_bytes'],'working':authority['authorized_change']['after_bytes'],'scratch':unchanged['scratch_ceiling_bytes'],'retention':unchanged['retention_ceiling_bytes']}
 paths=accounting_paths(root,contract,executor,protocol)
 guard=disk.DiskGuard(launch_floor_bytes=limits['launch'],protected_reserve_bytes=limits['reserve'],stop_margin_bytes=limits['stop']-limits['reserve'],stop_floor_bytes=limits['stop'],scratch_ceiling_bytes=limits['scratch'],retention_ceiling_bytes=limits['retention'],working_ceiling_bytes=limits['working'])
 measured={category:guard.check(projected_bytes=0,category=category,paths=values,capacity_path=root,phase='launch') for category,values in paths.items()}
 sample=bridge.ResourceSample(min(x['free_bytes'] for x in measured.values()),measured['working']['current_bytes'],measured['scratch']['current_bytes'],measured['retention']['current_bytes'])
 bridge.validate_resource_sample(sample,free_floor=limits['launch'],working_cap=limits['working'],scratch_cap=limits['scratch'],retention_cap=limits['retention'])
 return {'live_policy':live,'limits_bytes':limits,'categories':measured,'accounting_path_counts':{k:len(v) for k,v in paths.items()},'scope':'Actual read-only authority/window/policy plus full ledger and unclosed task-root accounting; no runtime replay.'}
