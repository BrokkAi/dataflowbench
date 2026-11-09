def dfb_source # DFB-SOURCE: issue303-source
  "DFB_SOURCE_303"
end
def dfb_sink(value) # DFB-SINK: issue303-sink
  puts value
end
def run(args)
  values = { "payload" => "clean", "tainted" => "clean" }
  values["tainted"] = dfb_source() # DFB-WITNESS: issue303-store
  dfb_sink(values.fetch("tainted")) # DFB-WITNESS: issue303-read
end
run(ARGV)
