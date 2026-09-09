class FlowBox
  attr_accessor :value

  def initialize
    @value = 0
  end
end

def dfb_source # DFB-SOURCE: recursive-heap-unwind-input
  return 7
end

def dfb_sink(value) # DFB-SINK: recursive-heap-unwind-sink
end

def walk(box, value, depth)
  if depth == 0
    box.value = value # DFB-WITNESS: recursive-heap-unwind-base
    box.value = 0 # DFB-KILL: recursive-heap-unwind-base-clean
    return
  end
  walk(box, value, depth - 1) # DFB-WITNESS: recursive-heap-unwind-transfer
  box.value = box.value + 1 # DFB-WITNESS: recursive-heap-unwind-compose
end

def run
  box = FlowBox.new
  walk(box, dfb_source, 3)
  dfb_sink(box.value)
end
