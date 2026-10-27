def dfb_source # DFB-SOURCE: loop-carried-input
  "tainted"
end

def dfb_sink(value) # DFB-SINK: loop-carried-sink
end

def run
  value = dfb_source
  iteration = 0
  while iteration < 3
    value = "clean" # DFB-WITNESS: loop-carried-value
    iteration += 1
  end
  dfb_sink(value)
end
