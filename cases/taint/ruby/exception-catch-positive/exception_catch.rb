class FlowError < StandardError
  attr_accessor :value
end

def dfb_source # DFB-SOURCE: exception-catch-input
  "tainted"
end

def dfb_sink(value) # DFB-SINK: exception-catch-sink
end

def run
  begin
    flow = FlowError.new
    flow.value = dfb_source
    raise flow # DFB-WITNESS: exception-catch-throw
  rescue FlowError => caught
    dfb_sink(caught.value)
  end
end
