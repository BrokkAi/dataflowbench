package dataflowbench

object CallbackRegistrationPositive {
  class Registry {
    var hooks: List[String => Unit] = Nil

    def register(hook: String => Unit): Unit = {
      hooks = hooks :+ hook
    }

    def fire(value: String): Unit = { // DFB-WITNESS: callback-registration-fire
      for (hook <- hooks) {
        hook(value)
      }
    }
  }

  def dfb_source(): String = { // DFB-SOURCE: callback-registration-input
    "tainted"
  }

  def dfb_sink(value: String): Unit = {} // DFB-SINK: callback-registration-sink

  def leak(value: String): Unit = {
    dfb_sink(value)
  }

  def run(): Unit = {
    val registry = new Registry()
    registry.register(leak)
    registry.fire(dfb_source())
  }
}
