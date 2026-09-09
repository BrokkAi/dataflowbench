class FlowBox
  attr_accessor :value

  def initialize
    @value = 0
  end
end

class RecursiveSignal < StandardError
end

def dfb_source # DFB-SOURCE: recursive-exception-persistence-input
  return 7
end

def dfb_sink(value) # DFB-SINK: recursive-exception-persistence-sink
end

def walk(box, value, depth)
  if depth == 0
    box.value = value # DFB-WITNESS: recursive-exception-persistence-base
    box.value = 0 # DFB-KILL: recursive-exception-persistence-base-clean
    raise RecursiveSignal, "recursive exceptional exit" # DFB-WITNESS: recursive-exception-persistence-throw
  end
  walk(box, value, depth - 1) # DFB-WITNESS: recursive-exception-persistence-transfer
end

def run
  box = FlowBox.new
  begin
    walk(box, dfb_source, 3)
  rescue RecursiveSignal => caught # DFB-WITNESS: recursive-exception-persistence-catch
    dfb_sink(box.value + 1) # DFB-WITNESS: recursive-exception-persistence-compose
  end
end
