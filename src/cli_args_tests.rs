use super::{Cli, run_cli};
use clap::Parser;
use clap::error::ErrorKind;
use std::collections::HashSet;

const RECOVERY_CONTRACT: &str =
    include_str!("../reports/releases/v0.9.0/execution-v1/recovery-20260930-01/contract.json");
const RECOVERY_INVENTORY: &str = include_str!(
    "../reports/releases/v0.9.0/execution-v1/recovery-20260930-01/control-inventory.json"
);

#[test]
fn validates_every_registered_recovery_runner_argv_without_dispatch() {
    let contract: serde_json::Value = serde_json::from_str(RECOVERY_CONTRACT).unwrap();
    let inventory: serde_json::Value = serde_json::from_str(RECOVERY_INVENTORY).unwrap();
    let runner = contract["tools"]["runner"]["path"].as_str().unwrap();
    let mut operations = Vec::new();

    for group in contract["groups"].as_array().unwrap() {
        if group["argv"][0].as_str() == Some(runner) {
            operations.push((
                group["id"].as_str().unwrap(),
                group["argv"].as_array().unwrap(),
            ));
        }
    }
    for control in inventory["controls"].as_array().unwrap() {
        if control["argv"][0].as_str() == Some(runner) {
            operations.push((
                control["id"].as_str().unwrap(),
                control["argv"].as_array().unwrap(),
            ));
        }
    }

    assert_eq!(operations.len(), 82 + 11);
    let mut operation_ids = HashSet::new();
    for (id, argv) in operations {
        assert!(
            operation_ids.insert(id),
            "duplicate recovery operation id: {id}"
        );

        let mut validation_argv: Vec<String> = argv
            .iter()
            .map(|argument| argument.as_str().unwrap().to_owned())
            .collect();
        validation_argv.insert(1, "--validate-args".to_owned());

        let cli = Cli::try_parse_from(validation_argv)
            .unwrap_or_else(|error| panic!("recovery operation {id} did not parse: {error}"));
        assert!(cli.validate_args, "validation flag missing for {id}");
        run_cli(cli).unwrap_or_else(|error| panic!("recovery operation {id} dispatched: {error}"));
    }
    assert_eq!(operation_ids.len(), 93);
}

#[test]
fn validation_still_rejects_missing_required_arguments_and_invalid_enum_modes() {
    let missing = match Cli::try_parse_from([
        "dataflowbench",
        "--validate-args",
        "run-opentaint-modeling",
        "--language",
        "java",
    ]) {
        Ok(_) => panic!("validation accepted missing required analyzer assets"),
        Err(error) => error,
    };
    assert_eq!(missing.kind(), ErrorKind::MissingRequiredArgument);

    let invalid_mode = match Cli::try_parse_from([
        "dataflowbench",
        "--validate-args",
        "measure-warm-latency",
        "--tool",
        "joern",
        "--language",
        "kotlin",
    ]) {
        Ok(_) => panic!("validation accepted an unsupported warm language"),
        Err(error) => error,
    };
    assert_eq!(invalid_mode.kind(), ErrorKind::InvalidValue);
}

#[test]
fn validation_help_cannot_short_circuit_required_argument_checks() {
    let error = super::run_from([
        "dataflowbench",
        "--validate-args",
        "run-codeql-modeling",
        "--help",
    ])
    .unwrap_err();
    assert!(
        error
            .to_string()
            .contains("--help cannot replace command arguments")
    );
}

#[test]
fn validation_rejects_unknown_flags_and_skips_population_setup() {
    assert!(super::run_from(["dataflowbench", "--validate-args", "--unknown-option"]).is_err());
    super::run_from([
        "dataflowbench",
        "--validate-args",
        "--population",
        "nonexistent-population",
        "measure-warm-latency",
        "--tool",
        "joern",
        "--language",
        "java",
    ])
    .unwrap();
}
