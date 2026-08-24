def dfb_source # DFB-SOURCE: infeasible-branch-input
  "tainted"
end

def dfb_sink(value) # DFB-SINK: infeasible-branch-sink
end

def run
  value = "clean"
  if true
    value = dfb_source # DFB-WITNESS: feasible-tainted-branch
  end
  dfb_sink(value)
end
