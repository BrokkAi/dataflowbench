struct Owner { let identity: (String) -> String = { value in value } }
func reflect(_ input: String) -> String {
 let owner = Owner()
 let mirror = Mirror(reflecting: owner)
 let runtimeLabel = "identity"
 guard let child = mirror.children.first(where: { $0.label == runtimeLabel }),
       let callback = child.value as? (String) -> String else {
  preconditionFailure("missing correctly typed reflected closure")
 }
 return withExtendedLifetime(owner) {
  withExtendedLifetime(mirror) { callback(input) }
 }
}
precondition(reflect("SOURCE") == "SOURCE")
precondition(reflect("SECOND") == "SECOND")
