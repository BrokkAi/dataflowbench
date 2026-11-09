DFB_FACTOR = 7
DFB_LIMIT = 200

def dfb_source # DFB-SOURCE: folded-local-constant-source
  "tainted"
end

def dfb_sink(value) # DFB-SINK: folded-local-constant-sink
  puts value
end

def run_case
  num = 100
  value = "safe"
  if (DFB_FACTOR * 42) - num > DFB_LIMIT
    value = "safe"
  else
    value = dfb_source # DFB-WITNESS: folded-local-constant-source-selected
  end
  dfb_sink(value)
end

run_case
