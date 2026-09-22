import swift
from CallExpr call, Function target
where target = call.getStaticTarget() and target.getModule().getName() = "DFBActivation"
select call, target.getName(), target.getModule().getName(),  target.getLocation().toString()
