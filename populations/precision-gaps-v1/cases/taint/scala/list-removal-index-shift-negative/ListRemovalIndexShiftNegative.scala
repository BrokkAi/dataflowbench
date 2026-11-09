import scala.collection.mutable.ArrayBuffer

object ListRemovalIndexShiftNegative {
  def dfb_source(): Int = { // DFB-SOURCE: list-removal-index-shift-input
    sys.env("DFB_INPUT").toInt
  }

  def dfb_sink(value: Int): Unit = { // DFB-SINK: list-removal-index-shift-sink
    println(value)
  }

  def main(args: Array[String]): Unit = {
    val values = ArrayBuffer.empty[Int]
    values += 0
    values += dfb_source()
    values += 9
    values.remove(0) // DFB-WITNESS: list-removal-index-shift-remove-first
    dfb_sink(values(1))
  }
}
