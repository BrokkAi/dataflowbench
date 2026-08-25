class Registry
  def initialize
    @hooks = []
  end

  def register(hook)
    @hooks.push(hook)
  end

  def fire(value) # DFB-WITNESS: callback-registration-fire
    @hooks.each do |hook|
      hook.call(value)
    end
  end
end

def dfb_source # DFB-SOURCE: callback-registration-input
  "tainted"
end

def dfb_sink(value) # DFB-SINK: callback-registration-sink
end

def leak(value)
  dfb_sink(value)
end

def run
  registry = Registry.new
  registry.register(method(:leak))
  registry.fire(dfb_source)
end
