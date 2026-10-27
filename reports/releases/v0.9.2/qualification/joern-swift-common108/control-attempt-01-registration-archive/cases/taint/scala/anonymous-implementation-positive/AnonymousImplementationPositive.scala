package dataflowbench

object AnonymousImplementationPositive {
  trait Handler {
    def handle(value: String): Unit
  }

  def dfb_source(): String = { // DFB-SOURCE: anonymous-implementation-input
    "tainted"
  }

  def dfb_sink(value: String): Unit = {} // DFB-SINK: anonymous-implementation-sink

  def run(): Unit = {
    val leak: Handler = new Handler { // DFB-WITNESS: anonymous-implementation-bind
      def handle(value: String): Unit = {
        dfb_sink(value)
      }
    }
    val drop: Handler = new Handler {
      def handle(value: String): Unit = {
        dfb_sink("clean")
      }
    }
    leak.handle(dfb_source())
  }
}
