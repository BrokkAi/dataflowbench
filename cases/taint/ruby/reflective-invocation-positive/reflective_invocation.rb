class Target
  def leak(value)
    dfb_sink(value)
  end

  def drop(value)
    dfb_sink("clean")
  end
end

def dfb_source # DFB-SOURCE: reflective-invocation-input
  "tainted"
end

def dfb_sink(value) # DFB-SINK: reflective-invocation-sink
end

def run
  target = Target.new
  name = "leak"
  target.public_send(name, dfb_source) # DFB-WITNESS: reflective-invocation-resolve
end
