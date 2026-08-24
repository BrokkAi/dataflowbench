class Holder
  attr_accessor :value

  def initialize
    @value = "clean"
  end
end

def dfb_source # DFB-SOURCE: object-separation-input
  "tainted"
end

def dfb_sink(value) # DFB-SINK: object-separation-sink
end

def run
  tainted = Holder.new
  clean = Holder.new
  tainted.value = dfb_source # DFB-WITNESS: object-separation-store
  clean.value = "clean"
  dfb_sink(clean.value)
end
