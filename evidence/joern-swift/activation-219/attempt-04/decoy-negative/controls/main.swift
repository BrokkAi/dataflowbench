func probeSource() -> Int { 7 }
func probeSink(_ value: Int) { print(value) }
struct Decoy {
 static func probeSource() -> Int { 9 }
 static func probeSink(_ value: Int) { print(value) }
}
func probe() {
 let tainted = probeSource()
 let clean = 0
 probeSink(clean)
 Decoy.probeSink(Decoy.probeSource())
}
probe()
