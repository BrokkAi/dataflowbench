//! Regression tests for the flowdroid adapter: population scoping, the pinned
//! identity, anchor reconciliation, dedicated report paths, and the guards that
//! keep a failed run from reading as a clean negative.

use crate::adapters::KernelPopulation;
use crate::adapters::flowdroid::{
    FLOWDROID_ANDROID_PLATFORM_SHA256, FLOWDROID_CONFIG_DIR, FLOWDROID_ENTRY_CALL_PLACEHOLDER,
    FLOWDROID_JAR_SHA256, FLOWDROID_PACKAGE_PLACEHOLDER, FLOWDROID_SINKS_PLACEHOLDER,
    FLOWDROID_SOURCES_PLACEHOLDER, FlowdroidKernel, flowdroid_completion_leaks,
    flowdroid_endpoint_signatures, flowdroid_entry_call, flowdroid_sink_definitions,
    flowdroid_template_paths, flowdroid_termination_state, parse_class_file,
    select_flowdroid_cases, witness_flowdroid_identity, write_stored_zip, xml_unescape, zip_crc32,
};
use crate::evidence::benchmark_endpoint_names;
use crate::templates::expected_core_templates;
use crate::tests::support::unique_test_dir;
use std::{fs, path::PathBuf};

/// Each FlowDroid kernel is language-scoped, selects its whole expanded
/// core, resolves every case's endpoints under its own dialect, and
/// loads committed materialization artifacts: a binary (AXML) manifest
/// blob, a wrapper template carrying both placeholders, and the endpoint
/// template carrying both signature placeholders — all bound into one
/// configuration hash.
#[test]
pub(crate) fn flowdroid_kernels_are_language_scoped_and_resolvable() {
    let kernels = [
        FlowdroidKernel::Java {
            javac: PathBuf::from("javac"),
        },
        FlowdroidKernel::Kotlin {
            kotlinc: PathBuf::from("kotlinc"),
            kotlin_stdlib: PathBuf::from("kotlin-stdlib.jar"),
        },
    ];
    let hashed = flowdroid_template_paths();
    let endpoint_template =
        fs::read_to_string(format!("{FLOWDROID_CONFIG_DIR}/sources-sinks.txt")).unwrap();
    assert!(endpoint_template.contains(FLOWDROID_SOURCES_PLACEHOLDER));
    assert!(endpoint_template.contains(FLOWDROID_SINKS_PLACEHOLDER));
    assert!(hashed.contains(&PathBuf::from(format!(
        "{FLOWDROID_CONFIG_DIR}/sources-sinks.txt"
    ))));
    for kernel in &kernels {
        let language = kernel.language();
        assert_eq!(
            kernel.report(),
            format!("reports/flowdroid-{language}-kernel.json")
        );
        assert_eq!(
            kernel.raw_dir(),
            format!("reports/raw/flowdroid-{language}-kernel")
        );
        let wrapper = fs::read_to_string(kernel.wrapper_template()).unwrap();
        assert!(wrapper.contains(FLOWDROID_PACKAGE_PLACEHOLDER));
        assert!(wrapper.contains(FLOWDROID_ENTRY_CALL_PLACEHOLDER));
        assert!(hashed.contains(&PathBuf::from(kernel.wrapper_template())));
        // The committed manifest is binary Android XML — FlowDroid's
        // manifest parser reads AXML, not text — and its first bytes are
        // the AXML document header.
        let manifest = fs::read(kernel.manifest()).unwrap();
        assert_eq!(&manifest[..4], &[0x03, 0x00, 0x08, 0x00]);
        assert!(hashed.contains(&PathBuf::from(kernel.manifest())));
        // The whole expanded core is selected and balanced, and every
        // case's endpoints resolve from its own markers, so no case can
        // fall out of the population silently.
        let selected = select_flowdroid_cases(kernel).unwrap();
        assert_eq!(selected.len(), 2 * expected_core_templates(language).len());
        for (path, case) in &selected {
            benchmark_endpoint_names(path, case, kernel.dialect()).unwrap_or_else(|reason| {
                panic!("{} endpoints do not resolve: {reason}", path.display())
            });
        }
    }
}

/// The pinned identity is witnessed, never asserted: the constants are
/// well-formed digests, and an artifact whose measured digest is not the
/// pinned one is refused with both values in the error.
#[test]
pub(crate) fn flowdroid_identity_is_witnessed_against_the_pin() {
    for constant in [FLOWDROID_JAR_SHA256, FLOWDROID_ANDROID_PLATFORM_SHA256] {
        assert_eq!(constant.len(), 64);
        assert!(constant.chars().all(|c| c.is_ascii_hexdigit()));
    }
    let root = unique_test_dir("dataflowbench-flowdroid-identity-test");
    let jar = root.join("not-the-pinned.jar");
    let platform = root.join("not-the-pinned-platform.jar");
    fs::write(&jar, b"not the pinned analyzer").unwrap();
    fs::write(&platform, b"not the pinned platform").unwrap();
    let error = witness_flowdroid_identity(&jar, &platform)
        .unwrap_err()
        .to_string();
    assert!(error.contains("witnessed sha256"));
    assert!(error.contains(FLOWDROID_JAR_SHA256));
    fs::remove_dir_all(&root).unwrap();
}

/// A minimal class file for the parser tests: one class, the given
/// methods, an empty attribute set everywhere.
pub(crate) fn flowdroid_test_class(binary_name: &str, methods: &[(&str, &str, u16)]) -> Vec<u8> {
    let internal = binary_name.replace('.', "/");
    let mut pool: Vec<Vec<u8>> = Vec::new();
    let mut utf8 = |value: &str| -> u16 {
        let mut entry = vec![1u8];
        entry.extend_from_slice(&(value.len() as u16).to_be_bytes());
        entry.extend_from_slice(value.as_bytes());
        pool.push(entry);
        pool.len() as u16
    };
    let name_index = utf8(&internal);
    let mut method_indices = Vec::new();
    for (name, descriptor, flags) in methods {
        method_indices.push((utf8(name), utf8(descriptor), *flags));
    }
    let class_index = {
        let mut entry = vec![7u8];
        entry.extend_from_slice(&name_index.to_be_bytes());
        pool.push(entry);
        pool.len() as u16
    };
    let mut bytes = 0xCAFE_BABEu32.to_be_bytes().to_vec();
    bytes.extend_from_slice(&0u16.to_be_bytes()); // minor
    bytes.extend_from_slice(&52u16.to_be_bytes()); // major
    bytes.extend_from_slice(&((pool.len() + 1) as u16).to_be_bytes());
    for entry in &pool {
        bytes.extend_from_slice(entry);
    }
    bytes.extend_from_slice(&0x0020u16.to_be_bytes()); // access flags
    bytes.extend_from_slice(&class_index.to_be_bytes());
    bytes.extend_from_slice(&0u16.to_be_bytes()); // super
    bytes.extend_from_slice(&0u16.to_be_bytes()); // interfaces
    bytes.extend_from_slice(&0u16.to_be_bytes()); // fields
    bytes.extend_from_slice(&(method_indices.len() as u16).to_be_bytes());
    for (name_index, descriptor_index, flags) in method_indices {
        bytes.extend_from_slice(&flags.to_be_bytes());
        bytes.extend_from_slice(&name_index.to_be_bytes());
        bytes.extend_from_slice(&descriptor_index.to_be_bytes());
        bytes.extend_from_slice(&0u16.to_be_bytes()); // attributes
    }
    bytes
}

/// The endpoint signatures FlowDroid is given are witnessed from the
/// compiled bytecode: the class parser reads names and descriptors, the
/// descriptor conversion spells the Java types Soot signatures use, and
/// compiler-synthesized members are invisible.
#[test]
pub(crate) fn flowdroid_signatures_are_witnessed_from_bytecode() {
    let class = parse_class_file(&flowdroid_test_class(
        "dataflowbench.taint.DirectPositive",
        &[
            ("directUntrustedInput", "()I", 0x0008),
            ("recordDirect", "(I)V", 0x0008),
            ("fancy", "([Ljava/lang/String;J)[[D", 0x0008),
            ("recordDirect", "(Ljava/lang/Object;)V", 0x1008), // synthetic
        ],
    ))
    .unwrap();
    assert_eq!(class.binary_name, "dataflowbench.taint.DirectPositive");
    let classes = vec![class];
    assert_eq!(
        flowdroid_endpoint_signatures(&classes, "directUntrustedInput")
            .unwrap()
            .into_iter()
            .collect::<Vec<_>>(),
        vec!["<dataflowbench.taint.DirectPositive: int directUntrustedInput()>".to_string()]
    );
    // The synthetic overload never widens the endpoint set.
    assert_eq!(
        flowdroid_endpoint_signatures(&classes, "recordDirect")
            .unwrap()
            .into_iter()
            .collect::<Vec<_>>(),
        vec!["<dataflowbench.taint.DirectPositive: void recordDirect(int)>".to_string()]
    );
    assert_eq!(
        flowdroid_endpoint_signatures(&classes, "fancy")
            .unwrap()
            .into_iter()
            .collect::<Vec<_>>(),
        vec![
            "<dataflowbench.taint.DirectPositive: double[][] fancy(java.lang.String[],long)>"
                .to_string()
        ]
    );
    assert!(
        flowdroid_endpoint_signatures(&classes, "absent")
            .unwrap_err()
            .contains("no compiled fixture class")
    );
}

/// The harness entry call is witnessed from the compiled classes and
/// supports exactly the two shapes the core fixtures declare; the
/// boolean shape's argument is derived from the activity bundle so it
/// stays statically unknown. Anything else is unresolvable, never a
/// synthesized outcome.
#[test]
pub(crate) fn flowdroid_entry_call_supports_the_two_fixture_shapes() {
    let plain = parse_class_file(&flowdroid_test_class(
        "dataflowbench.taint.DirectPositive",
        &[("run", "()V", 0x0008)],
    ))
    .unwrap();
    assert_eq!(
        flowdroid_entry_call(&[plain]).unwrap(),
        "DirectPositive.run()"
    );
    let boolean = parse_class_file(&flowdroid_test_class(
        "dataflowbench.taint.BranchJoinPositive",
        &[("run", "(Z)V", 0x0008)],
    ))
    .unwrap();
    assert_eq!(
        flowdroid_entry_call(&[boolean]).unwrap(),
        "BranchJoinPositive.run(savedInstanceState == null)"
    );
    let none = parse_class_file(&flowdroid_test_class(
        "dataflowbench.taint.Helper",
        &[("helper", "()V", 0x0008)],
    ))
    .unwrap();
    assert!(
        flowdroid_entry_call(&[none])
            .unwrap_err()
            .contains("found 0")
    );
    let extra = parse_class_file(&flowdroid_test_class(
        "dataflowbench.taint.Extra",
        &[("run", "()V", 0x0008), ("run", "(I)V", 0x0008)],
    ))
    .unwrap();
    assert!(
        flowdroid_entry_call(&[extra])
            .unwrap_err()
            .contains("found 2")
    );
    let unsupported = parse_class_file(&flowdroid_test_class(
        "dataflowbench.taint.Odd",
        &[("run", "(I)V", 0x0008)],
    ))
    .unwrap();
    assert!(
        flowdroid_entry_call(&[unsupported])
            .unwrap_err()
            .contains("unsupported descriptor")
    );
}

/// Reconciliation reads FlowDroid's own results document: the
/// self-reported `TerminationState` and each result's echoed sink
/// definition, with the writer's XML entities unescaped.
#[test]
pub(crate) fn flowdroid_results_xml_reading_is_exact() {
    let xml = r#"<?xml version="1.0" encoding="UTF-8"?><DataFlowResults FileFormatVersion="102" TerminationState="Success"><Results><Result><Sink Statement="staticinvoke &lt;a.B: void dfb_sink(int)&gt;($i0)" Method="&lt;a.B: void run()&gt;" MethodSourceSinkDefinition="&lt;a.B: void dfb_sink(int)&gt;"></Sink></Result></Results></DataFlowResults>"#;
    assert_eq!(flowdroid_termination_state(xml).as_deref(), Some("Success"));
    assert_eq!(
        flowdroid_sink_definitions(xml),
        vec!["<a.B: void dfb_sink(int)>".to_string()]
    );
    let timed_out = xml.replace("Success", "DataFlowTimeout");
    assert_eq!(
        flowdroid_termination_state(&timed_out).as_deref(),
        Some("DataFlowTimeout")
    );
    assert_eq!(flowdroid_termination_state("<NotResults/>"), None);
    assert_eq!(xml_unescape("&lt;x&gt; &quot;&apos;&amp;"), "<x> \"'&");
}

/// The completion guard is what keeps the pinned CLI's zero-exit failure
/// modes from reading as clean negatives: the failure banner
/// disqualifies the run, a log with no completion line proves nothing,
/// and only the analyzer's own "Found N leaks" line reports a count.
#[test]
pub(crate) fn flowdroid_completion_guard_refuses_silent_failures() {
    assert_eq!(
        flowdroid_completion_leaks("[main] INFO SetupApplication - Found 0 leaks from 0 sources"),
        Ok(0)
    );
    assert_eq!(
        flowdroid_completion_leaks("[main] INFO SetupApplication - Found 3 leaks from 2 sources"),
        Ok(3)
    );
    assert!(
        flowdroid_completion_leaks(
            "The data flow analysis has failed. Error message: Parse app resource failed"
        )
        .unwrap_err()
        .contains("reported failure")
    );
    // A crash after the completion line would still print the banner
    // somewhere in the log; the banner wins over the count.
    assert!(
        flowdroid_completion_leaks(
            "Found 0 leaks from 0 sources\nThe data flow analysis has failed"
        )
        .is_err()
    );
    assert!(
        flowdroid_completion_leaks("Initializing Soot...")
            .unwrap_err()
            .contains("no completion line")
    );
}

/// The stored-zip writer produces a structurally whole archive — the CRC
/// is the standard zip polynomial and the end-of-central-directory
/// record counts every entry — since a malformed APK would surface as an
/// analyzer parse failure attributed to the tool.
#[test]
pub(crate) fn flowdroid_apk_zip_writer_is_structurally_whole() {
    assert_eq!(zip_crc32(b"123456789"), 0xCBF4_3926);
    let root = unique_test_dir("dataflowbench-flowdroid-zip-test");
    let path = root.join("case.apk");
    write_stored_zip(
        &path,
        &[
            ("AndroidManifest.xml", b"manifest".as_slice()),
            ("classes.dex", b"dex-bytes".as_slice()),
        ],
    )
    .unwrap();
    let bytes = fs::read(&path).unwrap();
    assert_eq!(&bytes[..4], &0x0403_4B50u32.to_le_bytes());
    let eocd = bytes.len() - 22;
    assert_eq!(&bytes[eocd..eocd + 4], &0x0605_4B50u32.to_le_bytes());
    assert_eq!(
        u16::from_le_bytes([bytes[eocd + 10], bytes[eocd + 11]]),
        2,
        "the central directory must count both entries"
    );
    fs::remove_dir_all(&root).unwrap();
}
