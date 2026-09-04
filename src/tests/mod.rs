//! The regression suite, laid out to mirror `src/`.
//!
//! Every adapter is expected to carry, at minimum, a population-scoping test,
//! an identity-pin test, an evidence/anchor-reconciliation test, a
//! report-path-disjointness test, and an anti-vacuous-negative test. See
//! docs/adding-an-adapter.md.

mod adapters;
mod cases;
mod evidence;
mod freeze;
mod latency;
mod modeling;
mod native;
mod real_project;
mod report;
mod results;
mod runtime;
mod support;
mod templates;
