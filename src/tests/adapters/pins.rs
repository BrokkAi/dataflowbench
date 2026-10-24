//! Focused checks for the prospective adapter pin declaration.

use crate::adapters::ModelingTool;
use crate::adapters::bifrost::configure_bifrost_environment;
use crate::adapters::flowdroid::FLOWDROID_PINNED_VERSION;
use crate::adapters::infer::INFER_PINNED_VERSION;
use crate::adapters::opentaint::OPENTAINT_RELEASE_TAG;
use crate::adapters::pins;
use crate::adapters::pysa::{PYSA_PINNED_PYRE_VERSION, PYSA_PINNED_PYREFLY_VERSION};
use serde_json::Value;
use std::{ffi::OsStr, process::Command};

const PROFILE: &str = include_str!("../../../adapters/pins/v0.9.2-bifrost-v0140.json");

#[test]
pub(crate) fn v092_pin_profile_matches_runtime_guards_and_unchanged_pins() {
    let profile: Value = serde_json::from_str(PROFILE).unwrap();
    assert_eq!(profile["schema"], "dataflowbench-adapter-pin-profile/v1");
    assert_eq!(profile["profile"], pins::PROFILE);
    assert_eq!(
        profile["tools"]["bifrost"]["version"],
        pins::BIFROST_VERSION
    );
    assert_eq!(
        profile["tools"]["bifrost"]["build_identity"],
        pins::BIFROST_BUILD_IDENTITY
    );
    assert_eq!(profile["tools"]["codeql"]["version"], pins::CODEQL_VERSION);
    assert_eq!(profile["tools"]["joern"]["version"], pins::JOERN_VERSION);
    assert_eq!(
        profile["tools"]["semgrep_ce"]["version"],
        pins::SEMGREP_VERSION
    );
    assert_eq!(
        profile["tools"]["semgrep_ce"]["native_rules_profile"],
        "adapters/semgrep/native/v0.9.2/profile.json"
    );
    assert_eq!(
        profile["tools"]["pysa"]["pyre_check"],
        PYSA_PINNED_PYRE_VERSION
    );
    assert_eq!(
        profile["tools"]["pysa"]["pyrefly"],
        PYSA_PINNED_PYREFLY_VERSION
    );
    assert_eq!(
        OPENTAINT_RELEASE_TAG.strip_prefix('v').unwrap(),
        profile["tools"]["opentaint"]["version"]
    );
    assert_eq!(profile["tools"]["infer"]["version"], INFER_PINNED_VERSION);
    assert_eq!(
        profile["tools"]["flowdroid"]["version"],
        FLOWDROID_PINNED_VERSION
    );
    assert_eq!(
        profile["tools"]["bifrost"]["environment"][pins::BIFROST_OPEN_PACKS_DISABLE_ENV],
        pins::BIFROST_OPEN_PACKS_DISABLE_VALUE
    );
    assert_eq!(
        profile["swift_common_108"]["status"],
        "fresh-engine-qualification-required"
    );
    assert_eq!(profile["swift_common_108"]["scored_activation"], false);
    assert_eq!(ModelingTool::Bifrost.pinned_identity(), "Bifrost v0.14.0");
    assert_eq!(ModelingTool::Codeql.pinned_identity(), "CodeQL CLI 2.27.2");
    assert_eq!(ModelingTool::Joern.pinned_identity(), "Joern 4.0.660");
    assert_eq!(
        ModelingTool::Semgrep.pinned_identity(),
        "Semgrep CE 1.181.0"
    );
    assert_eq!(
        ModelingTool::Pysa.pinned_identity(),
        "Pysa (pyre-check 0.10.0 + Pyrefly 1.4.0)"
    );
}

#[test]
pub(crate) fn bifrost_process_boundary_disables_automatic_open_pack_acquisition() {
    let mut command = Command::new("bifrost");
    configure_bifrost_environment(&mut command);
    let value = command
        .get_envs()
        .find_map(|(key, value)| {
            (key == OsStr::new(pins::BIFROST_OPEN_PACKS_DISABLE_ENV)).then_some(value)
        })
        .flatten();
    assert_eq!(
        value,
        Some(OsStr::new(pins::BIFROST_OPEN_PACKS_DISABLE_VALUE))
    );
}
