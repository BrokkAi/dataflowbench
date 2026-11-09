package dataflowbench

object FoldedLocalConstantIfNegative {
  def dfb_source(): Int = { // DFB-SOURCE: folded-local-constant-source
    1
  }

  def dfb_sink(value: Int): Unit = { // DFB-SINK: folded-local-constant-sink
    println(value)
  }

  def runCase(): Unit = {
    val factor = 7
    val num = 86
    val limit = 200
    var value = 0
    if ((factor * 42) - num > limit) {
      value = 0
    } else {
      value = dfb_source()
    }
    dfb_sink(value)
  }

  def main(args: Array[String]): Unit = runCase()
}
