func probeSource() -> Int { 7 }
func probeSink(_ value: Int) { print(value) }
func probe() {
 let tainted = probeSource()
 let clean = 0
 probeSink(clean)
}
probe()
