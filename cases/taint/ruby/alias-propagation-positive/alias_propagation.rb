class Holder
  attr_accessor :value

  def initialize
    @value = "clean"
  end
end

def dfb_source # DFB-SOURCE: alias-propagation-input
  "tainted"
end

def dfb_sink(value) # DFB-SINK: alias-propagation-sink
end

def run
  original = Holder.new
  aliased = original # DFB-WITNESS: alias-propagation-alias
  distinct = Holder.new
  original.value = dfb_source # DFB-WITNESS: alias-propagation-store
  dfb_sink(aliased.value)
end
