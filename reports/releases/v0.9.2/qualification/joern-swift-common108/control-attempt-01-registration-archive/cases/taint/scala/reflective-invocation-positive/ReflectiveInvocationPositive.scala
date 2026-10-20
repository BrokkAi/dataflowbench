package dataflowbench

object ReflectiveInvocationPositive {
  class Target {
    def leak(value: String): Unit = {
      dfb_sink(value)
    }

    def drop(value: String): Unit = {
      dfb_sink("clean")
    }
  }

  def dfb_source(): String = { // DFB-SOURCE: reflective-invocation-input
    "tainted"
  }

  def dfb_sink(value: String): Unit = {} // DFB-SINK: reflective-invocation-sink

  def run(): Unit = {
    val target = new Target()
    val name = "leak"
    val method = classOf[Target].getMethod(name, classOf[String]) // DFB-WITNESS: reflective-invocation-resolve
    method.invoke(target, dfb_source())
  }
}
