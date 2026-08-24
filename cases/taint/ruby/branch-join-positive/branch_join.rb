def dfb_source # DFB-SOURCE: branch-join-input
  "tainted"
end

def dfb_sink(value) # DFB-SINK: branch-join-sink
end

def run(overwrite)
  value = dfb_source
  if overwrite
    value = "clean"
  end
  # DFB-WITNESS: branch-join-value
  dfb_sink(value)
end
