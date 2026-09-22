func dfb_source() -> Int { 7 }
func dfb_source(_ seed: Int) -> Int { seed }
func dfb_sink(_ value: Int) {}
func dfb_sink(_ value: String) {}
struct Foreign {
    static func dfb_source() -> Int { 7 }
    static func dfb_sink(_ value: Int) {}
}
func directControl() { dfb_sink(dfb_source()) }
func wrongSourceArity() { dfb_sink(dfb_source(1)) }
func wrongSinkType() { dfb_sink(String(dfb_source())) }
func wrongDeclarationKind() { Foreign.dfb_sink(Foreign.dfb_source()) }
