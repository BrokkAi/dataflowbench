def dfb_source # DFB-SOURCE: recursive-callback-transform-input
  return 7
end

def dfb_sink(value) # DFB-SINK: recursive-callback-transform-sink
end

def walk(value, depth, callback)
  if depth == 0
    value = 0 # DFB-KILL: recursive-callback-transform-base-clean
    return value # DFB-WITNESS: recursive-callback-transform-base
  end
  callback.call(value, depth - 1) # DFB-WITNESS: recursive-callback-transform-indirect-transfer
end

def step(value, depth)
  next_value = value + 1 # DFB-WITNESS: recursive-callback-transform-step
  recursive = walk(next_value, depth, method(:step)) # DFB-WITNESS: recursive-callback-transform-recursive-transfer
  recursive + 1 # DFB-WITNESS: recursive-callback-transform-compose
end

def run
  dfb_sink(walk(dfb_source, 3, method(:step)))
end
