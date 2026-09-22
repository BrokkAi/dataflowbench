import swift
from Method f
where f.getModule().getName() = "DataFlowBenchTaintSwift"
select f.getName(), f.getInterfaceType().toString(), f.getInterfaceType().(AnyFunctionType).getResult().toString(), f.getNumberOfParams()
