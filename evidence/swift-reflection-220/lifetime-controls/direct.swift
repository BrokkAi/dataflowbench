struct Owner { let identity: (String) -> String = { value in value } }
func direct(_ input: String) -> String {
 let owner = Owner()
 let callback = owner.identity
 return withExtendedLifetime(owner) { callback(input) }
}
precondition(direct("SOURCE") == "SOURCE")
precondition(direct("SECOND") == "SECOND")
