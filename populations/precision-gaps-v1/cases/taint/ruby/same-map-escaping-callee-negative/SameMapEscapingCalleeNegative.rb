def dfb_source # DFB-SOURCE: issue303-source
  "DFB_SOURCE_303"
end
def dfb_sink(value) # DFB-SINK: issue303-sink
  puts value
end
def write_source(values)
  values["private"] = dfb_source() # DFB-WITNESS: issue303-callee-store
end
def run(args)
  values = { "payload" => "clean" }
  write_source(values) # DFB-WITNESS: issue303-invoke
  dfb_sink(values.fetch("payload")) # DFB-WITNESS: issue303-read
end
run(ARGV)
