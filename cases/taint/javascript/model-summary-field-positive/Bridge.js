// The external-shaped boundary of dfb-template-model-summary-field. `deposit`
// writes nothing at all, so whatever the sink reads out of the box comes from
// the supplied store-through summary or from nowhere.
var Bridge = {
  deposit: function deposit(value, box) {}
};
