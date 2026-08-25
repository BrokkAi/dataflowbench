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
  key = "@alpha"
  holder.instance_variable_set(key, dfb_source) # DFB-WITNESS: computed-property-store
  dfb_sink(holder.instance_variable_get(key))
end
