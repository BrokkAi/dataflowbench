class Inner
  attr_accessor :value, :other

  def initialize
    @value = "clean"
    @other = "clean"
  end
end

class Middle
  attr_accessor :inner

  def initialize
    @inner = Inner.new
  end
end

class Outer
  attr_accessor :middle

  def initialize
    @middle = Middle.new
  end
end

def dfb_source # DFB-SOURCE: nested-access-path-input
  "tainted"
end

def dfb_sink(value) # DFB-SINK: nested-access-path-sink
end

def run
  outer = Outer.new
  outer.middle.inner.value = dfb_source # DFB-WITNESS: nested-access-path-store
  dfb_sink(outer.middle.inner.value)
end
