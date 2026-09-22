func dfb_source() -> Int { 7 }
func dfb_sink(_ value: Int) { print(value) }

enum Signal: Error { case stop }
final class Box { var value = 0 }
func mutate(_ box: Box, _ input: Int) throws {
    box.value = input // DFB-WITNESS: interprocedural-exception-persistence-write
    throw Signal.stop // DFB-WITNESS: interprocedural-exception-persistence-throw
}
func relay(_ input: Int) -> Int {
    let box = Box()
    do { try mutate(box, input) }
    catch Signal.stop { return box.value } // DFB-WITNESS: interprocedural-exception-persistence-read
    catch { return 0 }
    return 0
}
let input = dfb_source() // DFB-SOURCE: interprocedural-exception-persistence-input
dfb_sink(relay(input)) // DFB-SINK: interprocedural-exception-persistence-sink
