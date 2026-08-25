class Item
  attr_accessor :value

  def initialize
    @value = "clean"
  end
end

def dfb_source # DFB-SOURCE: element-object-input
  "tainted"
end

def dfb_sink(value) # DFB-SINK: element-object-sink
end

def run
  items = [Item.new, Item.new]
  items[0].value = dfb_source # DFB-WITNESS: element-object-store
  items[1].value = "clean"
  dfb_sink(items[1].value)
end
