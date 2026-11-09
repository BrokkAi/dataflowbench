def dfb_source
  "source-one" # DFB-SOURCE: constant-selector-input
end

def dfb_sink(value) # DFB-SINK: constant-selector-sink
  puts value
end

selector = "ABC"[1]
case selector
when "C"
  value = dfb_source # DFB-WITNESS: constant-selector-source-arm
when "B"
  value = "safe"
else
  value = "safe"
end
dfb_sink(value)
