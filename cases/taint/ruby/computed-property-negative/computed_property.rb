class Holder
  def initialize
    @alpha = "clean"
    @beta = "clean"
  end
end

def dfb_source # DFB-SOURCE: computed-property-input
  "tainted"
end

def dfb_sink(value) # DFB-SINK: computed-property-sink
end

def run
  holder = Holder.new
  write_key = "@alpha"
  read_key = "@beta"
  holder.instance_variable_set(write_key, dfb_source) # DFB-WITNESS: computed-property-store
  holder.instance_variable_set(read_key, "clean")
  dfb_sink(holder.instance_variable_get(read_key))
end
