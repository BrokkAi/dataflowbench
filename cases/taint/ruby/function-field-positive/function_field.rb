class Holder
  attr_accessor :fn

  def initialize
    @fn = nil
  end
end

def dfb_source # DFB-SOURCE: function-field-input
  "tainted"
end

def dfb_sink(value) # DFB-SINK: function-field-sink
end

def leak(value)
  dfb_sink(value)
end

def drop(value)
  dfb_sink("clean")
end

def dispatch(holder, value)
  holder.fn.call(value)
end

def run
  holder = Holder.new
  holder.fn = method(:leak) # DFB-WITNESS: function-field-store
  other = Holder.new
  other.fn = method(:drop)
  dispatch(holder, dfb_source)
end
