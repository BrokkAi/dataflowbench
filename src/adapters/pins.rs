//! The prospective analyzer pin set for the v0.9.2 measurement profile.
//!
//! Historical reports and their versioned evidence keep the identities they
//! actually witnessed. These constants describe only the next prospective
//! adapter execution profile; changing one requires reviewing that analyzer's
//! declarations and compatibility evidence in the same change.

pub(crate) const PROFILE: &str = "v0.9.2";

pub(crate) const BIFROST_VERSION: &str = "bifrost 0.14.0";
pub(crate) const BIFROST_BUILD_IDENTITY: &str = "c11a13ffa03ebea154f587b899954e412b5b871e";
pub(crate) const BIFROST_OPEN_PACKS_DISABLE_ENV: &str = "BIFROST_OPEN_PACKS_DISABLE";
pub(crate) const BIFROST_OPEN_PACKS_DISABLE_VALUE: &str = "1";

pub(crate) const CODEQL_VERSION: &str = "2.27.2";
pub(crate) const JOERN_VERSION: &str = "4.0.660";
pub(crate) const SEMGREP_VERSION: &str = "1.181.0";
pub(crate) const PYRE_VERSION: &str = "0.10.0";
pub(crate) const PYREFLY_VERSION: &str = "1.4.0";
pub(crate) const OPENTAINT_VERSION: &str = "v0.4.6";
pub(crate) const INFER_VERSION: &str = "v1.3.0";
pub(crate) const FLOWDROID_VERSION: &str = "2.15.1";
