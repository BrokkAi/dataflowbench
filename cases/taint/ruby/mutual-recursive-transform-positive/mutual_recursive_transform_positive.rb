def dfb_source # DFB-SOURCE: mutual-recursive-transform-input
  return 7
end

def dfb_sink(value) # DFB-SINK: mutual-recursive-transform-sink
end

def walk_a(value, depth)
  if depth == 0
    return value
  end
  next_value = value + 1
  recursive = walk_b(next_value, depth - 1) # DFB-WITNESS: mutual-recursive-transform-a-transfer
  recursive + 1 # DFB-WITNESS: mutual-recursive-transform-a-compose
end

def walk_b(value, depth)
  if depth == 0
    return value # DFB-WITNESS: mutual-recursive-transform-b-base
  end
  next_value = value + 1
  recursive = walk_a(next_value, depth - 1) # DFB-WITNESS: mutual-recursive-transform-b-transfer
  recursive + 1 # DFB-WITNESS: mutual-recursive-transform-b-compose
end

def run
  dfb_sink(walk_a(dfb_source, 3))
end
