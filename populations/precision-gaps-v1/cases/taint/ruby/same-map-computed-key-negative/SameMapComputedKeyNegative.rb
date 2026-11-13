def dfb_source # DFB-SOURCE: issue303-source
  "DFB_SOURCE_303"
end
def dfb_sink(value) # DFB-SINK: issue303-sink
  puts value
end
def run(args)
  suffix = args[0] || "payload"
  key = "private:" + suffix
  values = { "payload" => "clean" }
  values[key] = dfb_source() # DFB-WITNESS: issue303-store
  dfb_sink(values.fetch("payload")) # DFB-WITNESS: issue303-read
end
run(ARGV)
