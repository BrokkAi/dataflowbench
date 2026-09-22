import swift
from FreeFunction f
where f.getModule().getName() = "DFBActivation"
select f.getName(), f.getInterfaceType().toString(), f.getInterfaceType().(AnyFunctionType).getResult().toString()
