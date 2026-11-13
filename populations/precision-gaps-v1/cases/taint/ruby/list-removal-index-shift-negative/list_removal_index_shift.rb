def dfb_source # DFB-SOURCE: list-removal-index-shift-input
  ENV.fetch("DFB_INPUT")
end

def dfb_sink(value) # DFB-SINK: list-removal-index-shift-sink
  puts value
end

values = []
values.push("safe")
values.push(dfb_source)
values.push("more-safe")
values.shift # DFB-WITNESS: list-removal-index-shift-remove-first
dfb_sink(values[1])
