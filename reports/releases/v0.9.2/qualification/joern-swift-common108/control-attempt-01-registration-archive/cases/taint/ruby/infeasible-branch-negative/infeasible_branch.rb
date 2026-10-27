def dfb_source # DFB-SOURCE: infeasible-branch-input
  "tainted"
end

def dfb_sink(value) # DFB-SINK: infeasible-branch-sink
end

def run
  value = "clean"
  if false
    value = dfb_source # DFB-WITNESS: infeasible-tainted-branch
  end
  dfb_sink(value)
end
