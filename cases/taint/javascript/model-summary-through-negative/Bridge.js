// The external-shaped boundary of dfb-template-model-summary-through: declared
// in its own fixture file, named as a boundary, and covered by a summary whose
// semantics the analysis must produce whether or not it reads these bodies.
// Both bodies are the identity function, so the bodies agree and only the two
// summaries disagree.
var Bridge = {
  pass: function pass(value) {
    return value;
  },
  hold: function hold(value) {
    return value;
  }
};
