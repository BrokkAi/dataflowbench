def dfb_source # DFB-SOURCE: exception-persistence-input
  "tainted"
end

def dfb_sink(value) # DFB-SINK: exception-persistence-sink
end

class FlowBox
  attr_accessor :value

  def initialize(value)
    @value = value
  end
end

class FlowError < StandardError
end

def store_and_throw(box, value)
  box.value = value # DFB-WITNESS: exception-persistence-store
  raise FlowError, "exceptional exit" # DFB-WITNESS: exception-persistence-throw
end

def recover(box, value)
  begin
    store_and_throw(box, value)
    "unreachable"
  rescue FlowError
    box.value # DFB-WITNESS: exception-persistence-recovery
  end
end

def run
  dfb_sink(recover(FlowBox.new("seed"), dfb_source))
end
