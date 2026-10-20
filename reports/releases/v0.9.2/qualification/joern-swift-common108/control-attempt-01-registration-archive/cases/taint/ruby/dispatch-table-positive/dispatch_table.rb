def dfb_source # DFB-SOURCE: dispatch-table-input
  "tainted"
end

def dfb_sink(value) # DFB-SINK: dispatch-table-sink
end

def run
  table = {
    "leak" => ->(value) { dfb_sink(value) },
    "drop" => ->(value) { dfb_sink("clean") }
  } # DFB-WITNESS: dispatch-table-build
  key = "leak"
  table[key].call(dfb_source)
end
