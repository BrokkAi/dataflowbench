def dfb_source # DFB-SOURCE: map-iteration-input
  "tainted"
end

def dfb_sink(value) # DFB-SINK: map-iteration-sink
end

def run
  records = {}
  records["record"] = dfb_source # DFB-WITNESS: map-iteration-store
  records.each do |key, value|
    dfb_sink(value)
  end
end
