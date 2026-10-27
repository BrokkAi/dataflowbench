class Holder
  attr_accessor :tainted, :clean

  def initialize
    @tainted = "clean"
    @clean = "clean"
  end
end

def dfb_source # DFB-SOURCE: same-object-field-input
  "tainted"
end

def dfb_sink(value) # DFB-SINK: same-object-field-sink
end

def run
  holder = Holder.new
  holder.tainted = dfb_source # DFB-WITNESS: same-object-field-store
  holder.clean = "clean"
  dfb_sink(holder.tainted)
end
