package dataflowbench

object FoldedLocalConstantConditionalExpressionPositive {
  def dfb_source(): Int = { // DFB-SOURCE: folded-local-constant-source
    1
  }

  def dfb_sink(value: Int): Unit = { // DFB-SINK: folded-local-constant-sink
    println(value)
  }

  def runCase(): Unit = {
    val factor = 7
    val num = 100
    val limit = 200
    val value = if ((factor * 42) - num > limit) 0 else /* DFB-WITNESS: folded-local-constant-source-selected */ dfb_source()
    dfb_sink(value)
  }

  def main(args: Array[String]): Unit = runCase()
}
