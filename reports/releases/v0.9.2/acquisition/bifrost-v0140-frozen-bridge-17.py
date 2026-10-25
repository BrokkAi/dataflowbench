#!/usr/bin/env python3
"""Stage-aware frozen bridge for the append-only Bifrost-14 successor.

This module is deliberately a small boundary around the reviewed frozen
bridge.  A stage owns the opaque runtime objects produced by one validation
and the complete module graph that produced them.  Callers pass the same
stage to admission, phase, terminal and completion checks; those operations
must not reload a graph or reconstruct runtime objects from JSON.

The production loader accepts only hash-pinned path references supplied by a
reviewed core.  The only injection seam is ``fixture_only=True`` under a
temporary directory, used by the focused tests.  No function in this module
starts a process, acquires a release lock, materializes a checkout, or runs
an analyzer.
"""
from __future__ import annotations

import builtins
from collections.abc import MutableMapping
import contextlib
import dataclasses
import hashlib
import importlib.machinery
import importlib.util
import inspect
import json
import os
from pathlib import Path, PurePosixPath
import re
import secrets
import stat
import sys
import sysconfig
import tempfile
import types
import time
from typing import Any, Iterable, Mapping, Sequence


HOST_STDLIB_IMPORTLIB = importlib


ROOT = Path(__file__).resolve().parents[4]
SCHEMA = "v092-bifrost-v0140-frozen-bridge/v17"
HANDSHAKE_SECONDS = 120
STARTUP_SECONDS = 600
PARENT_STAGE_COUNT = 21
CHILD_STAGE_COUNT = 20
REQUIRED_GRAPH_NAMES = (
    "bridge17", "replacement22", "executor", "checker", "configuration",
    "incoming_recovery", "policy_source", "policy_runtime", "protocol22",
    "admission22", "supervisor22",
)
OPTIONAL_GRAPH_NAMES = ("disk_guard",)
STAGE_RUNTIME_GRAPH_NAME = "stage_runtime09"
GRAPH_NAME_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]{0,127}\Z")
DEFAULT_GRAPH_SPEC = {'bare_import_route_table': [{'bare_name': 'codeql_swift_qualification_v092', 'target_path': 'scripts/codeql_swift_qualification_v092.py', 'target_role': 'local_004_codeql_swift_qualification_v092', 'target_sha256': 'adaf4ba27f45870ac500f30a7a89f63019efc9429d1377891aea5834bc1b781c'}, {'bare_name': 'joern_diagnostic_admission_v092', 'target_path': 'scripts/joern_diagnostic_admission_v092.py', 'target_role': 'local_005_joern_diagnostic_admission_v092', 'target_sha256': 'c2faeeb5ef99f539ad8a4bee6fbc85656c0cc142f92196c02f5f26a446140a9e'}, {'bare_name': 'joern_execution_revalidation_v1', 'target_path': 'scripts/joern_execution_revalidation_v1.py', 'target_role': 'local_006_joern_execution_revalidation_v1', 'target_sha256': '8b08b9022ac8eac0fd822d53980d0fcc49e352e8736bce9f2e42b0a488612126'}, {'bare_name': 'joern_normal_controls_v1', 'target_path': 'scripts/joern_normal_controls_v1.py', 'target_role': 'local_007_joern_normal_controls_v1', 'target_sha256': '78123e5f9247aca543f0c841f6adf0040859f1e8d1006d9fb45116535aa4ff21'}, {'bare_name': 'joern_normal_execution_v1', 'target_path': 'scripts/joern_normal_execution_v1.py', 'target_role': 'local_008_joern_normal_execution_v1', 'target_sha256': '01caead3c7e86880b9893128a0a65d7175f857b580d161ecbf586514e295577d'}, {'bare_name': 'joern_normal_reports_v1', 'target_path': 'scripts/joern_normal_reports_v1.py', 'target_role': 'nested_043_dfb_common_v2_joern_reports__root_token', 'target_sha256': 'a3fba23a07317be139a587186f529f3cccc4766a56b0c3d839886e7ce41f0b47'}, {'bare_name': 'joern_normal_runner_v092', 'target_path': 'scripts/joern_normal_runner_v092.py', 'target_role': 'nested_037_joern_normal_runner_v092_repair_pinned', 'target_sha256': '683a1bb22a2ec943d357cd4b86982dd7ee62c22a47c28ee3c32e91d114f977f4'}, {'bare_name': 'joern_normal_runner_v1', 'target_path': 'scripts/joern_normal_runner_v1.py', 'target_role': 'nested_042_dfb_common_v2_joern_runner__root_token', 'target_sha256': '4103ef8d9d2dc671408389dad57ee934ae01333a2cf5eecc8330ab9feb3be330'}, {'bare_name': 'joern_swift', 'target_path': 'scripts/joern_swift.py', 'target_role': 'local_009_joern_swift', 'target_sha256': 'c0c2322939ee61e39b85a80391192a27cd6323dcb6b234609985dee4fdc85822'}, {'bare_name': 'swift_artifact_closure', 'target_path': 'scripts/swift_artifact_closure.py', 'target_role': 'local_011_swift_artifact_closure', 'target_sha256': 'fe00daf7b75263e7add65675560f8731988333f75af3944e373599a85d7215c3'}, {'bare_name': 'swift_common_population_v2', 'target_path': 'scripts/swift_common_population_v2.py', 'target_role': 'local_012_swift_common_population_v2', 'target_sha256': '3dee12724faf7a3937a3741a086a9858518ed27271644bbb788b458caef6b6c6'}, {'bare_name': 'swift_entry_observation', 'target_path': 'scripts/swift_entry_observation.py', 'target_role': 'local_013_swift_entry_observation', 'target_sha256': '930b80478e989974a89c4f82ad01cae3c5e3bcdd7df16c4eb7ecdf0363cb6596'}, {'bare_name': 'swift_extraction_integrity', 'target_path': 'scripts/swift_extraction_integrity.py', 'target_role': 'local_014_swift_extraction_integrity', 'target_sha256': '06bf474314b6d14f01ebc3c94b06b1ff6a789d861cc54de548498436a5169156'}, {'bare_name': 'swift_normal_reports_v092', 'target_path': 'scripts/swift_normal_reports_v092.py', 'target_role': 'local_015_swift_normal_reports_v092', 'target_sha256': 'fb682d4b48d5c1a2ee32eb2d3d271bc624c28466e98e55318f9582efe8123b8a'}, {'bare_name': 'swift_normal_reports_v1', 'target_path': 'scripts/swift_normal_reports_v1.py', 'target_role': 'nested_041_dfb_common_v2_codeql_reports__root_token', 'target_sha256': '4a9ee1c8708ab368452492b87f01d721bb31aa31bd6f526ddb18890f82d01ff3'}, {'bare_name': 'swift_normal_runner_v092', 'target_path': 'scripts/swift_normal_runner_v092.py', 'target_role': 'local_016_swift_normal_runner_v092', 'target_sha256': 'f70fb98ee9b9073a1a31064c413a9278ad3ac3c8c8e95826190d58ce7fac1bfc'}, {'bare_name': 'swift_normal_runner_v1', 'target_path': 'scripts/swift_normal_runner_v1.py', 'target_role': 'nested_040_dfb_common_v2_codeql_runner__root_token', 'target_sha256': 'f046c917c5c809199d37956ba950a4267523a74872ee8291ac4a732b7882cafb'}, {'bare_name': 'swift_persistence_coverage', 'target_path': 'scripts/swift_persistence_coverage.py', 'target_role': 'local_017_swift_persistence_coverage', 'target_sha256': '62017833ad9e666a405f2650618173b97ab2d1568fb14b13cce8fed722dc4ec3'}, {'bare_name': 'swift_v2_process', 'target_path': 'scripts/swift_v2_process.py', 'target_role': 'local_018_swift_v2_process', 'target_sha256': '40aec2ef3e23def3d961caab709de9e636e9669d305b47bdc7b7c98ccf8a97dd'}, {'bare_name': 'swift_v3_reports', 'target_path': 'scripts/swift_v3_reports.py', 'target_role': 'local_019_swift_v3_reports', 'target_sha256': '5d5fd2c2046a9886de261037dca6d529a9841b7f889790e8723404fc5da501af'}, {'bare_name': 'swift_v3_runner', 'target_path': 'scripts/swift_v3_runner.py', 'target_role': 'local_020_swift_v3_runner', 'target_sha256': '454944d5ca461e8ae49361055408daaa9037388a151dcd8e5f3d34c8a3c2b954'}, {'bare_name': 'v092_qualification', 'target_path': 'scripts/v092_qualification.py', 'target_role': 'nested_038_v092_qualification', 'target_sha256': 'f673a5b5133c1101e7379fc365a83a47a7525c3daf15efa34a6eed12858e7cb5'}], 'dynamic_route_table': [{'caller_function': 'load_dependencies', 'caller_graph_roles': ['local_001_bifrost_v0140_frozen_bridge_08'], 'caller_path': 'reports/releases/v0.9.2/acquisition/bifrost-v0140-frozen-bridge-08.py', 'caller_sha256': 'd964c524cfec26e296a44e4c09ce3a606dcdfaec7c83114a1be3801222e35189', 'duplicate_path_identity_policy': 'target candidates remain distinct graph objects; this caller/selector selects exactly the named role', 'loader_selector': 'v092_frozen_bridge_02_replacement05', 'phase': 'function_late', 'reachability': 'mandatory-retained-replay', 'route_id': 'dynamic-001', 'selected_target_role': 'nested_001_v092_frozen_bridge_02_replacement05', 'target_path': 'reports/releases/v0.9.2/acquisition/bifrost-v0140-replacement-05.py', 'target_role_candidates': ['nested_001_v092_frozen_bridge_02_replacement05', 'replacement05'], 'target_sha256': '32e0f1811972eec57e9cf5f8e892f77bea0da68d063b19db9d324fa0ad30dafd'}, {'caller_function': '_load_frozen', 'caller_graph_roles': ['nested_001_v092_frozen_bridge_02_replacement05', 'replacement05'], 'caller_path': 'reports/releases/v0.9.2/acquisition/bifrost-v0140-replacement-05.py', 'caller_sha256': '32e0f1811972eec57e9cf5f8e892f77bea0da68d063b19db9d324fa0ad30dafd', 'duplicate_path_identity_policy': 'target candidates remain distinct graph objects; this caller/selector selects exactly the named role', 'loader_selector': 'replacement05_executor', 'phase': 'function_late', 'reachability': 'mandatory-retained-replay', 'route_id': 'dynamic-002', 'selected_target_role': 'nested_002_replacement05_executor', 'target_path': 'scripts/execute-release-v092.py', 'target_role_candidates': ['executor', 'incoming_nested_executor', 'nested_002_replacement05_executor', 'nested_003_codeql_pending_executor', 'nested_017_execute_release_v092_for_checker', 'nested_027_joern_continuation_frozen_execute', 'nested_031_joern_continuation_frozen_execute'], 'target_sha256': 'fae9e1c2b4bfa4f9e458293744e6463a84d4bc68de73389fe9a14feb9ced27b8'}, {'caller_function': 'load_frozen', 'caller_graph_roles': ['incoming_predecessor03', 'nested_013_codeql_terminal_history_03'], 'caller_path': 'reports/releases/v0.9.2/acquisition/independent-pending-codeql-03.py', 'caller_sha256': 'f9c543b504000d9594e91fc84cbf493adb238a0c61487daacdc1077334d1f7e8', 'duplicate_path_identity_policy': 'target candidates remain distinct graph objects; this caller/selector selects exactly the named role', 'loader_selector': 'codeql_pending_executor', 'phase': 'function_late', 'reachability': 'mandatory-retained-replay', 'route_id': 'dynamic-003', 'selected_target_role': 'nested_003_codeql_pending_executor', 'target_path': 'scripts/execute-release-v092.py', 'target_role_candidates': ['executor', 'incoming_nested_executor', 'nested_002_replacement05_executor', 'nested_003_codeql_pending_executor', 'nested_017_execute_release_v092_for_checker', 'nested_027_joern_continuation_frozen_execute', 'nested_031_joern_continuation_frozen_execute'], 'target_sha256': 'fae9e1c2b4bfa4f9e458293744e6463a84d4bc68de73389fe9a14feb9ced27b8'}, {'caller_function': '_load_frozen', 'caller_graph_roles': ['nested_001_v092_frozen_bridge_02_replacement05', 'replacement05'], 'caller_path': 'reports/releases/v0.9.2/acquisition/bifrost-v0140-replacement-05.py', 'caller_sha256': '32e0f1811972eec57e9cf5f8e892f77bea0da68d063b19db9d324fa0ad30dafd', 'duplicate_path_identity_policy': 'target candidates remain distinct graph objects; this caller/selector selects exactly the named role', 'loader_selector': 'replacement05_checker', 'phase': 'function_late', 'reachability': 'mandatory-retained-replay', 'route_id': 'dynamic-004', 'selected_target_role': 'nested_004_replacement05_checker', 'target_path': 'scripts/check-release-v092.py', 'target_role_candidates': ['checker', 'incoming_nested_checker', 'nested_004_replacement05_checker', 'nested_005_codeql_pending_checker', 'nested_016_check_release_v092_for_config_validation', 'nested_022_check_release_v092_scoped_replay', 'nested_023_check_release_v092_resource_replay', 'nested_028_joern_continuation_frozen_checker', 'nested_032_joern_continuation_frozen_checker'], 'target_sha256': '0a9f9df751b7e01443d8bedb09911f13119b36b366f09eeae107df9fcaf0d928'}, {'caller_function': 'load_frozen', 'caller_graph_roles': ['incoming_predecessor03', 'nested_013_codeql_terminal_history_03'], 'caller_path': 'reports/releases/v0.9.2/acquisition/independent-pending-codeql-03.py', 'caller_sha256': 'f9c543b504000d9594e91fc84cbf493adb238a0c61487daacdc1077334d1f7e8', 'duplicate_path_identity_policy': 'target candidates remain distinct graph objects; this caller/selector selects exactly the named role', 'loader_selector': 'codeql_pending_checker', 'phase': 'function_late', 'reachability': 'mandatory-retained-replay', 'route_id': 'dynamic-005', 'selected_target_role': 'nested_005_codeql_pending_checker', 'target_path': 'scripts/check-release-v092.py', 'target_role_candidates': ['checker', 'incoming_nested_checker', 'nested_004_replacement05_checker', 'nested_005_codeql_pending_checker', 'nested_016_check_release_v092_for_config_validation', 'nested_022_check_release_v092_scoped_replay', 'nested_023_check_release_v092_resource_replay', 'nested_028_joern_continuation_frozen_checker', 'nested_032_joern_continuation_frozen_checker'], 'target_sha256': '0a9f9df751b7e01443d8bedb09911f13119b36b366f09eeae107df9fcaf0d928'}, {'caller_function': '_load_frozen', 'caller_graph_roles': ['nested_001_v092_frozen_bridge_02_replacement05', 'replacement05'], 'caller_path': 'reports/releases/v0.9.2/acquisition/bifrost-v0140-replacement-05.py', 'caller_sha256': '32e0f1811972eec57e9cf5f8e892f77bea0da68d063b19db9d324fa0ad30dafd', 'duplicate_path_identity_policy': 'target candidates remain distinct graph objects; this caller/selector selects exactly the named role', 'loader_selector': 'replacement05_configuration', 'phase': 'function_late', 'reachability': 'mandatory-retained-replay', 'route_id': 'dynamic-006', 'selected_target_role': 'nested_006_replacement05_configuration', 'target_path': 'scripts/validate-v092-report-configurations.py', 'target_role_candidates': ['configuration', 'incoming_nested_configuration', 'nested_006_replacement05_configuration', 'nested_007_codeql_pending_configuration', 'nested_029_joern_continuation_frozen_configuration', 'nested_033_joern_continuation_frozen_configuration'], 'target_sha256': '21149f4cd75da8be2b6423eaa3ca5f2ed87753aaa7263758133b01ef902a3858'}, {'caller_function': 'load_frozen', 'caller_graph_roles': ['incoming_predecessor03', 'nested_013_codeql_terminal_history_03'], 'caller_path': 'reports/releases/v0.9.2/acquisition/independent-pending-codeql-03.py', 'caller_sha256': 'f9c543b504000d9594e91fc84cbf493adb238a0c61487daacdc1077334d1f7e8', 'duplicate_path_identity_policy': 'target candidates remain distinct graph objects; this caller/selector selects exactly the named role', 'loader_selector': 'codeql_pending_configuration', 'phase': 'function_late', 'reachability': 'mandatory-retained-replay', 'route_id': 'dynamic-007', 'selected_target_role': 'nested_007_codeql_pending_configuration', 'target_path': 'scripts/validate-v092-report-configurations.py', 'target_role_candidates': ['configuration', 'incoming_nested_configuration', 'nested_006_replacement05_configuration', 'nested_007_codeql_pending_configuration', 'nested_029_joern_continuation_frozen_configuration', 'nested_033_joern_continuation_frozen_configuration'], 'target_sha256': '21149f4cd75da8be2b6423eaa3ca5f2ed87753aaa7263758133b01ef902a3858'}, {'caller_function': 'load_frozen', 'caller_graph_roles': ['incoming_predecessor03', 'nested_013_codeql_terminal_history_03'], 'caller_path': 'reports/releases/v0.9.2/acquisition/independent-pending-codeql-03.py', 'caller_sha256': 'f9c543b504000d9594e91fc84cbf493adb238a0c61487daacdc1077334d1f7e8', 'duplicate_path_identity_policy': 'target candidates remain distinct graph objects; this caller/selector selects exactly the named role', 'loader_selector': 'codeql_pending_disk_guard', 'phase': 'function_late', 'reachability': 'mandatory-retained-replay', 'route_id': 'dynamic-008', 'selected_target_role': 'disk_guard', 'target_path': 'scripts/v092_disk_guard.py', 'target_role_candidates': ['disk_guard', 'nested_008_codeql_pending_disk_guard', 'nested_025_v092_disk_guard_runtime', 'nested_026_v092_replacement09_supervisor_terminal_disk_guard'], 'target_sha256': 'fa4201b0aa4ae73273c4d6ba9f2dbb4315e6fb9d52c7469c8be3d46f0b570e21'}, {'caller_function': '_incoming_recovery', 'caller_graph_roles': ['local_001_bifrost_v0140_frozen_bridge_08'], 'caller_path': 'reports/releases/v0.9.2/acquisition/bifrost-v0140-frozen-bridge-08.py', 'caller_sha256': 'd964c524cfec26e296a44e4c09ce3a606dcdfaec7c83114a1be3801222e35189', 'duplicate_path_identity_policy': 'target candidates remain distinct graph objects; this caller/selector selects exactly the named role', 'loader_selector': 'bridge06_incoming_policy', 'phase': 'function_late', 'reachability': 'mandatory-retained-replay', 'route_id': 'dynamic-009', 'selected_target_role': 'nested_009_bridge06_incoming_policy', 'target_path': 'reports/releases/v0.9.2/acquisition/bifrost-v0140-replacement-13.py', 'target_role_candidates': ['nested_009_bridge06_incoming_policy', 'nested_010_bridge03_window_policy', 'nested_011_v092_frozen_bridge_02_source_design04_policy'], 'target_sha256': '6fdc08000f673b5ac904aeb315be7dfa174747e31d7ff2f32b4090b161253842'}, {'caller_function': 'load_and_validate', 'caller_graph_roles': ['local_001_bifrost_v0140_frozen_bridge_08'], 'caller_path': 'reports/releases/v0.9.2/acquisition/bifrost-v0140-frozen-bridge-08.py', 'caller_sha256': 'd964c524cfec26e296a44e4c09ce3a606dcdfaec7c83114a1be3801222e35189', 'duplicate_path_identity_policy': 'target candidates remain distinct graph objects; this caller/selector selects exactly the named role', 'loader_selector': 'bridge03_window_policy', 'phase': 'function_late', 'reachability': 'mandatory-retained-replay', 'route_id': 'dynamic-010', 'selected_target_role': 'nested_010_bridge03_window_policy', 'target_path': 'reports/releases/v0.9.2/acquisition/bifrost-v0140-replacement-13.py', 'target_role_candidates': ['nested_009_bridge06_incoming_policy', 'nested_010_bridge03_window_policy', 'nested_011_v092_frozen_bridge_02_source_design04_policy'], 'target_sha256': '6fdc08000f673b5ac904aeb315be7dfa174747e31d7ff2f32b4090b161253842'}, {'caller_function': 'load_and_validate', 'caller_graph_roles': ['local_001_bifrost_v0140_frozen_bridge_08'], 'caller_path': 'reports/releases/v0.9.2/acquisition/bifrost-v0140-frozen-bridge-08.py', 'caller_sha256': 'd964c524cfec26e296a44e4c09ce3a606dcdfaec7c83114a1be3801222e35189', 'duplicate_path_identity_policy': 'target candidates remain distinct graph objects; this caller/selector selects exactly the named role', 'loader_selector': 'v092_frozen_bridge_02_source_design04_policy', 'phase': 'function_late', 'reachability': 'mandatory-retained-replay', 'route_id': 'dynamic-011', 'selected_target_role': 'nested_011_v092_frozen_bridge_02_source_design04_policy', 'target_path': 'reports/releases/v0.9.2/acquisition/bifrost-v0140-replacement-13.py', 'target_role_candidates': ['nested_009_bridge06_incoming_policy', 'nested_010_bridge03_window_policy', 'nested_011_v092_frozen_bridge_02_source_design04_policy'], 'target_sha256': '6fdc08000f673b5ac904aeb315be7dfa174747e31d7ff2f32b4090b161253842'}, {'caller_function': '_incoming_recovery', 'caller_graph_roles': ['local_001_bifrost_v0140_frozen_bridge_08'], 'caller_path': 'reports/releases/v0.9.2/acquisition/bifrost-v0140-frozen-bridge-08.py', 'caller_sha256': 'd964c524cfec26e296a44e4c09ce3a606dcdfaec7c83114a1be3801222e35189', 'duplicate_path_identity_policy': 'target candidates remain distinct graph objects; this caller/selector selects exactly the named role', 'loader_selector': 'v092_frozen_bridge_02_independent_codeql_history', 'phase': 'function_late', 'reachability': 'mandatory-retained-replay', 'route_id': 'dynamic-012', 'selected_target_role': 'nested_012_v092_frozen_bridge_02_independent_codeql_history', 'target_path': 'reports/releases/v0.9.2/acquisition/codeql-terminal-history-04.py', 'target_role_candidates': ['incoming_recovery', 'nested_012_v092_frozen_bridge_02_independent_codeql_history'], 'target_sha256': 'b9bede28c81ef1ce3324cfd3624f002cc3dfa835f3e2ac41e8ba8a0bf6aa7e5e'}, {'caller_function': 'load_predecessor', 'caller_graph_roles': ['incoming_recovery', 'nested_012_v092_frozen_bridge_02_independent_codeql_history'], 'caller_path': 'reports/releases/v0.9.2/acquisition/codeql-terminal-history-04.py', 'caller_sha256': 'b9bede28c81ef1ce3324cfd3624f002cc3dfa835f3e2ac41e8ba8a0bf6aa7e5e', 'duplicate_path_identity_policy': 'target candidates remain distinct graph objects; this caller/selector selects exactly the named role', 'loader_selector': 'codeql_terminal_history_03', 'phase': 'function_late', 'reachability': 'mandatory-retained-replay', 'route_id': 'dynamic-013', 'selected_target_role': 'nested_013_codeql_terminal_history_03', 'target_path': 'reports/releases/v0.9.2/acquisition/independent-pending-codeql-03.py', 'target_role_candidates': ['incoming_predecessor03', 'nested_013_codeql_terminal_history_03'], 'target_sha256': 'f9c543b504000d9594e91fc84cbf493adb238a0c61487daacdc1077334d1f7e8'}, {'caller_function': '_load_historical_replay_helper', 'caller_graph_roles': ['incoming_predecessor03', 'nested_013_codeql_terminal_history_03'], 'caller_path': 'reports/releases/v0.9.2/acquisition/independent-pending-codeql-03.py', 'caller_sha256': 'f9c543b504000d9594e91fc84cbf493adb238a0c61487daacdc1077334d1f7e8', 'duplicate_path_identity_policy': 'target candidates remain distinct graph objects; this caller/selector selects exactly the named role', 'loader_selector': 'codeql_pending_historical_replay_helper', 'phase': 'function_late', 'reachability': 'mandatory-retained-replay', 'route_id': 'dynamic-014', 'selected_target_role': 'nested_014_codeql_pending_historical_replay_helper', 'target_path': 'reports/releases/v0.9.2/acquisition/joern-capability-continuation-05.py', 'target_role_candidates': ['incoming_historical_replay_helper05', 'nested_014_codeql_pending_historical_replay_helper'], 'target_sha256': '848272ddad3328862b24151a27fd22b48fd6cf8ad6456c4b7c474d30d01bf4a6'}, {'caller_function': '_load_historical_previous_helper', 'caller_graph_roles': ['incoming_predecessor03', 'nested_013_codeql_terminal_history_03'], 'caller_path': 'reports/releases/v0.9.2/acquisition/independent-pending-codeql-03.py', 'caller_sha256': 'f9c543b504000d9594e91fc84cbf493adb238a0c61487daacdc1077334d1f7e8', 'duplicate_path_identity_policy': 'target candidates remain distinct graph objects; this caller/selector selects exactly the named role', 'loader_selector': 'codeql_pending_historical_previous_helper', 'phase': 'function_late', 'reachability': 'mandatory-retained-replay', 'route_id': 'dynamic-015', 'selected_target_role': 'nested_015_codeql_pending_historical_previous_helper', 'target_path': 'reports/releases/v0.9.2/acquisition/joern-capability-continuation-01.py', 'target_role_candidates': ['incoming_historical_previous_helper01', 'nested_015_codeql_pending_historical_previous_helper', 'nested_035_joern_capability_continuation_01_historical'], 'target_sha256': '712d456fdb7e8c7f658d5e3cded8a2bc8cc276b9a890cf0c4944fdbafa9828fa'}, {'caller_function': '<module>', 'caller_graph_roles': ['configuration', 'incoming_nested_configuration', 'nested_006_replacement05_configuration', 'nested_007_codeql_pending_configuration', 'nested_029_joern_continuation_frozen_configuration', 'nested_033_joern_continuation_frozen_configuration'], 'caller_path': 'scripts/validate-v092-report-configurations.py', 'caller_sha256': '21149f4cd75da8be2b6423eaa3ca5f2ed87753aaa7263758133b01ef902a3858', 'duplicate_path_identity_policy': 'target candidates remain distinct graph objects; this caller/selector selects exactly the named role', 'loader_selector': 'check_release_v092_for_config_validation', 'phase': 'import_time', 'reachability': 'import-time-mandatory', 'route_id': 'dynamic-016', 'selected_target_role': 'incoming_nested_checker', 'target_path': 'scripts/check-release-v092.py', 'target_role_candidates': ['checker', 'incoming_nested_checker', 'nested_004_replacement05_checker', 'nested_005_codeql_pending_checker', 'nested_016_check_release_v092_for_config_validation', 'nested_022_check_release_v092_scoped_replay', 'nested_023_check_release_v092_resource_replay', 'nested_028_joern_continuation_frozen_checker', 'nested_032_joern_continuation_frozen_checker'], 'target_sha256': '0a9f9df751b7e01443d8bedb09911f13119b36b366f09eeae107df9fcaf0d928'}, {'caller_function': '<module>/_load_executor', 'caller_graph_roles': ['checker', 'incoming_nested_checker', 'nested_004_replacement05_checker', 'nested_005_codeql_pending_checker', 'nested_016_check_release_v092_for_config_validation', 'nested_022_check_release_v092_scoped_replay', 'nested_023_check_release_v092_resource_replay', 'nested_028_joern_continuation_frozen_checker', 'nested_032_joern_continuation_frozen_checker'], 'caller_path': 'scripts/check-release-v092.py', 'caller_sha256': '0a9f9df751b7e01443d8bedb09911f13119b36b366f09eeae107df9fcaf0d928', 'duplicate_path_identity_policy': 'target candidates remain distinct graph objects; this caller/selector selects exactly the named role', 'loader_selector': 'execute_release_v092_for_checker', 'phase': 'import_time', 'reachability': 'import-time-mandatory', 'route_id': 'dynamic-017', 'selected_target_role': 'incoming_nested_executor', 'target_path': 'scripts/execute-release-v092.py', 'target_role_candidates': ['executor', 'incoming_nested_executor', 'nested_002_replacement05_executor', 'nested_003_codeql_pending_executor', 'nested_017_execute_release_v092_for_checker', 'nested_027_joern_continuation_frozen_execute', 'nested_031_joern_continuation_frozen_execute'], 'target_sha256': 'fae9e1c2b4bfa4f9e458293744e6463a84d4bc68de73389fe9a14feb9ced27b8'}, {'caller_function': '_load_resource_recovery_module', 'caller_graph_roles': ['checker', 'incoming_nested_checker', 'nested_004_replacement05_checker', 'nested_005_codeql_pending_checker', 'nested_016_check_release_v092_for_config_validation', 'nested_022_check_release_v092_scoped_replay', 'nested_023_check_release_v092_resource_replay', 'nested_028_joern_continuation_frozen_checker', 'nested_032_joern_continuation_frozen_checker'], 'caller_path': 'scripts/check-release-v092.py', 'caller_sha256': '0a9f9df751b7e01443d8bedb09911f13119b36b366f09eeae107df9fcaf0d928', 'duplicate_path_identity_policy': 'target candidates remain distinct graph objects; this caller/selector selects exactly the named role', 'loader_selector': 'v092_resource_recovery_for_checker', 'phase': 'function_late', 'reachability': 'mandatory-retained-replay', 'route_id': 'dynamic-018', 'selected_target_role': 'nested_018_v092_resource_recovery_for_checker', 'target_path': 'scripts/v092_resource_recovery.py', 'target_role_candidates': ['incoming_nested_resource_recovery', 'nested_018_v092_resource_recovery_for_checker', 'nested_021_v092_resource_recovery'], 'target_sha256': 'c0dc2ef56cd1cb20cb0d96b156438e2ee876081e85c0f8ff43ca4afb3091830d'}, {'caller_function': '_load_scoped_recovery_module', 'caller_graph_roles': ['checker', 'incoming_nested_checker', 'nested_004_replacement05_checker', 'nested_005_codeql_pending_checker', 'nested_016_check_release_v092_for_config_validation', 'nested_022_check_release_v092_scoped_replay', 'nested_023_check_release_v092_resource_replay', 'nested_028_joern_continuation_frozen_checker', 'nested_032_joern_continuation_frozen_checker'], 'caller_path': 'scripts/check-release-v092.py', 'caller_sha256': '0a9f9df751b7e01443d8bedb09911f13119b36b366f09eeae107df9fcaf0d928', 'duplicate_path_identity_policy': 'target candidates remain distinct graph objects; this caller/selector selects exactly the named role', 'loader_selector': 'v092_scoped_recovery_for_checker', 'phase': 'function_late', 'reachability': 'mandatory-retained-replay', 'route_id': 'dynamic-019', 'selected_target_role': 'nested_019_v092_scoped_recovery_for_checker', 'target_path': 'scripts/v092_scoped_recovery.py', 'target_role_candidates': ['incoming_nested_scoped_recovery', 'nested_019_v092_scoped_recovery_for_checker', 'nested_020_v092_scoped_recovery_packet'], 'target_sha256': '6f8b025aae344709e1ecc9722db8943877e6f08851e423f9ab735d8d7d311c0d'}, {'caller_function': '_scoped_recovery_module', 'caller_graph_roles': ['executor', 'incoming_nested_executor', 'nested_002_replacement05_executor', 'nested_003_codeql_pending_executor', 'nested_017_execute_release_v092_for_checker', 'nested_027_joern_continuation_frozen_execute', 'nested_031_joern_continuation_frozen_execute'], 'caller_path': 'scripts/execute-release-v092.py', 'caller_sha256': 'fae9e1c2b4bfa4f9e458293744e6463a84d4bc68de73389fe9a14feb9ced27b8', 'duplicate_path_identity_policy': 'target candidates remain distinct graph objects; this caller/selector selects exactly the named role', 'loader_selector': 'v092_scoped_recovery_packet', 'phase': 'function_late', 'reachability': 'mandatory-retained-replay', 'route_id': 'dynamic-020', 'selected_target_role': 'nested_020_v092_scoped_recovery_packet', 'target_path': 'scripts/v092_scoped_recovery.py', 'target_role_candidates': ['incoming_nested_scoped_recovery', 'nested_019_v092_scoped_recovery_for_checker', 'nested_020_v092_scoped_recovery_packet'], 'target_sha256': '6f8b025aae344709e1ecc9722db8943877e6f08851e423f9ab735d8d7d311c0d'}, {'caller_function': '_validate_resource_recovery', 'caller_graph_roles': ['executor', 'incoming_nested_executor', 'nested_002_replacement05_executor', 'nested_003_codeql_pending_executor', 'nested_017_execute_release_v092_for_checker', 'nested_027_joern_continuation_frozen_execute', 'nested_031_joern_continuation_frozen_execute'], 'caller_path': 'scripts/execute-release-v092.py', 'caller_sha256': 'fae9e1c2b4bfa4f9e458293744e6463a84d4bc68de73389fe9a14feb9ced27b8', 'duplicate_path_identity_policy': 'target candidates remain distinct graph objects; this caller/selector selects exactly the named role', 'loader_selector': 'v092_resource_recovery', 'phase': 'function_late', 'reachability': 'mandatory-retained-replay', 'route_id': 'dynamic-021', 'selected_target_role': 'nested_021_v092_resource_recovery', 'target_path': 'scripts/v092_resource_recovery.py', 'target_role_candidates': ['incoming_nested_resource_recovery', 'nested_018_v092_resource_recovery_for_checker', 'nested_021_v092_resource_recovery'], 'target_sha256': 'c0dc2ef56cd1cb20cb0d96b156438e2ee876081e85c0f8ff43ca4afb3091830d'}, {'caller_function': '_validate_scoped_recovery', 'caller_graph_roles': ['executor', 'incoming_nested_executor', 'nested_002_replacement05_executor', 'nested_003_codeql_pending_executor', 'nested_017_execute_release_v092_for_checker', 'nested_027_joern_continuation_frozen_execute', 'nested_031_joern_continuation_frozen_execute'], 'caller_path': 'scripts/execute-release-v092.py', 'caller_sha256': 'fae9e1c2b4bfa4f9e458293744e6463a84d4bc68de73389fe9a14feb9ced27b8', 'duplicate_path_identity_policy': 'target candidates remain distinct graph objects; this caller/selector selects exactly the named role', 'loader_selector': 'check_release_v092_scoped_replay', 'phase': 'function_late', 'reachability': 'mandatory-retained-replay', 'route_id': 'dynamic-022', 'selected_target_role': 'nested_022_check_release_v092_scoped_replay', 'target_path': 'scripts/check-release-v092.py', 'target_role_candidates': ['checker', 'incoming_nested_checker', 'nested_004_replacement05_checker', 'nested_005_codeql_pending_checker', 'nested_016_check_release_v092_for_config_validation', 'nested_022_check_release_v092_scoped_replay', 'nested_023_check_release_v092_resource_replay', 'nested_028_joern_continuation_frozen_checker', 'nested_032_joern_continuation_frozen_checker'], 'target_sha256': '0a9f9df751b7e01443d8bedb09911f13119b36b366f09eeae107df9fcaf0d928'}, {'caller_function': '_validate_resource_recovery', 'caller_graph_roles': ['executor', 'incoming_nested_executor', 'nested_002_replacement05_executor', 'nested_003_codeql_pending_executor', 'nested_017_execute_release_v092_for_checker', 'nested_027_joern_continuation_frozen_execute', 'nested_031_joern_continuation_frozen_execute'], 'caller_path': 'scripts/execute-release-v092.py', 'caller_sha256': 'fae9e1c2b4bfa4f9e458293744e6463a84d4bc68de73389fe9a14feb9ced27b8', 'duplicate_path_identity_policy': 'target candidates remain distinct graph objects; this caller/selector selects exactly the named role', 'loader_selector': 'check_release_v092_resource_replay', 'phase': 'function_late', 'reachability': 'mandatory-retained-replay', 'route_id': 'dynamic-023', 'selected_target_role': 'nested_023_check_release_v092_resource_replay', 'target_path': 'scripts/check-release-v092.py', 'target_role_candidates': ['checker', 'incoming_nested_checker', 'nested_004_replacement05_checker', 'nested_005_codeql_pending_checker', 'nested_016_check_release_v092_for_config_validation', 'nested_022_check_release_v092_scoped_replay', 'nested_023_check_release_v092_resource_replay', 'nested_028_joern_continuation_frozen_checker', 'nested_032_joern_continuation_frozen_checker'], 'target_sha256': '0a9f9df751b7e01443d8bedb09911f13119b36b366f09eeae107df9fcaf0d928'}, {'caller_function': '_process_tracker', 'caller_graph_roles': ['executor', 'incoming_nested_executor', 'nested_002_replacement05_executor', 'nested_003_codeql_pending_executor', 'nested_017_execute_release_v092_for_checker', 'nested_027_joern_continuation_frozen_execute', 'nested_031_joern_continuation_frozen_execute'], 'caller_path': 'scripts/execute-release-v092.py', 'caller_sha256': 'fae9e1c2b4bfa4f9e458293744e6463a84d4bc68de73389fe9a14feb9ced27b8', 'duplicate_path_identity_policy': 'single exact graph role', 'loader_selector': 'v092_process_tracker', 'phase': 'function_late', 'reachability': 'actual-attempt-monitoring', 'route_id': 'dynamic-024', 'selected_target_role': 'nested_024_v092_process_tracker', 'target_path': 'scripts/swift_v2_scored_process.py', 'target_role_candidates': ['nested_024_v092_process_tracker'], 'target_sha256': '09cc57d0893d3ab17c75f7934aba8ebd9cc736bd118e77163e5c5fd2fbf0456e'}, {'caller_function': 'run_group/_copy_file', 'caller_graph_roles': ['executor', 'incoming_nested_executor', 'nested_002_replacement05_executor', 'nested_003_codeql_pending_executor', 'nested_017_execute_release_v092_for_checker', 'nested_027_joern_continuation_frozen_execute', 'nested_031_joern_continuation_frozen_execute'], 'caller_path': 'scripts/execute-release-v092.py', 'caller_sha256': 'fae9e1c2b4bfa4f9e458293744e6463a84d4bc68de73389fe9a14feb9ced27b8', 'duplicate_path_identity_policy': 'target candidates remain distinct graph objects; this caller/selector selects exactly the named role', 'loader_selector': 'v092_disk_guard_runtime', 'phase': 'function_late', 'reachability': 'actual-attempt-retention', 'route_id': 'dynamic-025', 'selected_target_role': 'disk_guard', 'target_path': 'scripts/v092_disk_guard.py', 'target_role_candidates': ['disk_guard', 'nested_008_codeql_pending_disk_guard', 'nested_025_v092_disk_guard_runtime', 'nested_026_v092_replacement09_supervisor_terminal_disk_guard'], 'target_sha256': 'fa4201b0aa4ae73273c4d6ba9f2dbb4315e6fb9d52c7469c8be3d46f0b570e21'}, {'caller_function': 'terminal_continuation_safety', 'caller_graph_roles': ['host_supervisor14', 'supervisor14'], 'caller_path': 'reports/releases/v0.9.2/acquisition/bifrost-v0140-supervisor-14.py', 'caller_sha256': 'acb8fed0b9fdffd7ee866b0b8bb107b6fec067469535a4c0666bd89ef70d5811', 'duplicate_path_identity_policy': 'target candidates remain distinct graph objects; this caller/selector selects exactly the named role', 'loader_selector': 'v092_replacement09_supervisor_terminal disk guard', 'phase': 'function_late', 'reachability': 'actual-terminal-containment', 'route_id': 'dynamic-026', 'selected_target_role': 'disk_guard', 'target_path': 'scripts/v092_disk_guard.py', 'target_role_candidates': ['disk_guard', 'nested_008_codeql_pending_disk_guard', 'nested_025_v092_disk_guard_runtime', 'nested_026_v092_replacement09_supervisor_terminal_disk_guard'], 'target_sha256': 'fa4201b0aa4ae73273c4d6ba9f2dbb4315e6fb9d52c7469c8be3d46f0b570e21'}, {'caller_function': '_load_frozen', 'caller_graph_roles': ['incoming_historical_previous_helper01', 'nested_015_codeql_pending_historical_previous_helper', 'nested_035_joern_capability_continuation_01_historical'], 'caller_path': 'reports/releases/v0.9.2/acquisition/joern-capability-continuation-01.py', 'caller_sha256': '712d456fdb7e8c7f658d5e3cded8a2bc8cc276b9a890cf0c4944fdbafa9828fa', 'duplicate_path_identity_policy': 'target candidates remain distinct graph objects; this caller/selector selects exactly the named role', 'loader_selector': 'joern_continuation_frozen_execute', 'phase': 'function_late', 'reachability': 'historical-helper-full-validate branch; context-derivation path does not automatically imply call', 'route_id': 'dynamic-027', 'selected_target_role': 'nested_027_joern_continuation_frozen_execute', 'target_path': 'scripts/execute-release-v092.py', 'target_role_candidates': ['executor', 'incoming_nested_executor', 'nested_002_replacement05_executor', 'nested_003_codeql_pending_executor', 'nested_017_execute_release_v092_for_checker', 'nested_027_joern_continuation_frozen_execute', 'nested_031_joern_continuation_frozen_execute'], 'target_sha256': 'fae9e1c2b4bfa4f9e458293744e6463a84d4bc68de73389fe9a14feb9ced27b8'}, {'caller_function': '_load_frozen', 'caller_graph_roles': ['incoming_historical_previous_helper01', 'nested_015_codeql_pending_historical_previous_helper', 'nested_035_joern_capability_continuation_01_historical'], 'caller_path': 'reports/releases/v0.9.2/acquisition/joern-capability-continuation-01.py', 'caller_sha256': '712d456fdb7e8c7f658d5e3cded8a2bc8cc276b9a890cf0c4944fdbafa9828fa', 'duplicate_path_identity_policy': 'target candidates remain distinct graph objects; this caller/selector selects exactly the named role', 'loader_selector': 'joern_continuation_frozen_checker', 'phase': 'function_late', 'reachability': 'historical-helper-full-validate branch; context-derivation path does not automatically imply call', 'route_id': 'dynamic-028', 'selected_target_role': 'nested_028_joern_continuation_frozen_checker', 'target_path': 'scripts/check-release-v092.py', 'target_role_candidates': ['checker', 'incoming_nested_checker', 'nested_004_replacement05_checker', 'nested_005_codeql_pending_checker', 'nested_016_check_release_v092_for_config_validation', 'nested_022_check_release_v092_scoped_replay', 'nested_023_check_release_v092_resource_replay', 'nested_028_joern_continuation_frozen_checker', 'nested_032_joern_continuation_frozen_checker'], 'target_sha256': '0a9f9df751b7e01443d8bedb09911f13119b36b366f09eeae107df9fcaf0d928'}, {'caller_function': '_load_frozen', 'caller_graph_roles': ['incoming_historical_previous_helper01', 'nested_015_codeql_pending_historical_previous_helper', 'nested_035_joern_capability_continuation_01_historical'], 'caller_path': 'reports/releases/v0.9.2/acquisition/joern-capability-continuation-01.py', 'caller_sha256': '712d456fdb7e8c7f658d5e3cded8a2bc8cc276b9a890cf0c4944fdbafa9828fa', 'duplicate_path_identity_policy': 'target candidates remain distinct graph objects; this caller/selector selects exactly the named role', 'loader_selector': 'joern_continuation_frozen_configuration', 'phase': 'function_late', 'reachability': 'historical-helper-full-validate branch; context-derivation path does not automatically imply call', 'route_id': 'dynamic-029', 'selected_target_role': 'nested_029_joern_continuation_frozen_configuration', 'target_path': 'scripts/validate-v092-report-configurations.py', 'target_role_candidates': ['configuration', 'incoming_nested_configuration', 'nested_006_replacement05_configuration', 'nested_007_codeql_pending_configuration', 'nested_029_joern_continuation_frozen_configuration', 'nested_033_joern_continuation_frozen_configuration'], 'target_sha256': '21149f4cd75da8be2b6423eaa3ca5f2ed87753aaa7263758133b01ef902a3858'}, {'caller_function': '_invoke_repair_shim', 'caller_graph_roles': ['incoming_historical_previous_helper01', 'nested_015_codeql_pending_historical_previous_helper', 'nested_035_joern_capability_continuation_01_historical'], 'caller_path': 'reports/releases/v0.9.2/acquisition/joern-capability-continuation-01.py', 'caller_sha256': '712d456fdb7e8c7f658d5e3cded8a2bc8cc276b9a890cf0c4944fdbafa9828fa', 'duplicate_path_identity_policy': 'target candidates remain distinct graph objects; this caller/selector selects exactly the named role', 'loader_selector': 'joern_capability_repair_continuation_shim', 'phase': 'function_late', 'reachability': 'conditional historical validation shim', 'route_id': 'dynamic-030', 'selected_target_role': 'nested_030_joern_capability_repair_continuation_shim', 'target_path': 'scripts/joern_capability_repair_v092.py', 'target_role_candidates': ['nested_030_joern_capability_repair_continuation_shim', 'nested_034_joern_capability_repair_continuation_shim', 'nested_036_joern_continuation_repair_shim'], 'target_sha256': '535ec9dcc88f5562ccd468822b2c137928caccf614e97b82d94a0b68f905f16f'}, {'caller_function': '_load_frozen', 'caller_graph_roles': ['incoming_historical_replay_helper05', 'nested_014_codeql_pending_historical_replay_helper'], 'caller_path': 'reports/releases/v0.9.2/acquisition/joern-capability-continuation-05.py', 'caller_sha256': '848272ddad3328862b24151a27fd22b48fd6cf8ad6456c4b7c474d30d01bf4a6', 'duplicate_path_identity_policy': 'target candidates remain distinct graph objects; this caller/selector selects exactly the named role', 'loader_selector': 'joern_continuation_frozen_execute', 'phase': 'function_late', 'reachability': 'historical-helper-full-validate branch; context-derivation path does not automatically imply call', 'route_id': 'dynamic-031', 'selected_target_role': 'nested_031_joern_continuation_frozen_execute', 'target_path': 'scripts/execute-release-v092.py', 'target_role_candidates': ['executor', 'incoming_nested_executor', 'nested_002_replacement05_executor', 'nested_003_codeql_pending_executor', 'nested_017_execute_release_v092_for_checker', 'nested_027_joern_continuation_frozen_execute', 'nested_031_joern_continuation_frozen_execute'], 'target_sha256': 'fae9e1c2b4bfa4f9e458293744e6463a84d4bc68de73389fe9a14feb9ced27b8'}, {'caller_function': '_load_frozen', 'caller_graph_roles': ['incoming_historical_replay_helper05', 'nested_014_codeql_pending_historical_replay_helper'], 'caller_path': 'reports/releases/v0.9.2/acquisition/joern-capability-continuation-05.py', 'caller_sha256': '848272ddad3328862b24151a27fd22b48fd6cf8ad6456c4b7c474d30d01bf4a6', 'duplicate_path_identity_policy': 'target candidates remain distinct graph objects; this caller/selector selects exactly the named role', 'loader_selector': 'joern_continuation_frozen_checker', 'phase': 'function_late', 'reachability': 'historical-helper-full-validate branch; context-derivation path does not automatically imply call', 'route_id': 'dynamic-032', 'selected_target_role': 'nested_032_joern_continuation_frozen_checker', 'target_path': 'scripts/check-release-v092.py', 'target_role_candidates': ['checker', 'incoming_nested_checker', 'nested_004_replacement05_checker', 'nested_005_codeql_pending_checker', 'nested_016_check_release_v092_for_config_validation', 'nested_022_check_release_v092_scoped_replay', 'nested_023_check_release_v092_resource_replay', 'nested_028_joern_continuation_frozen_checker', 'nested_032_joern_continuation_frozen_checker'], 'target_sha256': '0a9f9df751b7e01443d8bedb09911f13119b36b366f09eeae107df9fcaf0d928'}, {'caller_function': '_load_frozen', 'caller_graph_roles': ['incoming_historical_replay_helper05', 'nested_014_codeql_pending_historical_replay_helper'], 'caller_path': 'reports/releases/v0.9.2/acquisition/joern-capability-continuation-05.py', 'caller_sha256': '848272ddad3328862b24151a27fd22b48fd6cf8ad6456c4b7c474d30d01bf4a6', 'duplicate_path_identity_policy': 'target candidates remain distinct graph objects; this caller/selector selects exactly the named role', 'loader_selector': 'joern_continuation_frozen_configuration', 'phase': 'function_late', 'reachability': 'historical-helper-full-validate branch; context-derivation path does not automatically imply call', 'route_id': 'dynamic-033', 'selected_target_role': 'nested_033_joern_continuation_frozen_configuration', 'target_path': 'scripts/validate-v092-report-configurations.py', 'target_role_candidates': ['configuration', 'incoming_nested_configuration', 'nested_006_replacement05_configuration', 'nested_007_codeql_pending_configuration', 'nested_029_joern_continuation_frozen_configuration', 'nested_033_joern_continuation_frozen_configuration'], 'target_sha256': '21149f4cd75da8be2b6423eaa3ca5f2ed87753aaa7263758133b01ef902a3858'}, {'caller_function': '_invoke_repair_shim', 'caller_graph_roles': ['incoming_historical_replay_helper05', 'nested_014_codeql_pending_historical_replay_helper'], 'caller_path': 'reports/releases/v0.9.2/acquisition/joern-capability-continuation-05.py', 'caller_sha256': '848272ddad3328862b24151a27fd22b48fd6cf8ad6456c4b7c474d30d01bf4a6', 'duplicate_path_identity_policy': 'target candidates remain distinct graph objects; this caller/selector selects exactly the named role', 'loader_selector': 'joern_capability_repair_continuation_shim', 'phase': 'function_late', 'reachability': 'conditional historical validation shim', 'route_id': 'dynamic-034', 'selected_target_role': 'nested_034_joern_capability_repair_continuation_shim', 'target_path': 'scripts/joern_capability_repair_v092.py', 'target_role_candidates': ['nested_030_joern_capability_repair_continuation_shim', 'nested_034_joern_capability_repair_continuation_shim', 'nested_036_joern_continuation_repair_shim'], 'target_sha256': '535ec9dcc88f5562ccd468822b2c137928caccf614e97b82d94a0b68f905f16f'}, {'caller_function': '_load_previous_continuation', 'caller_graph_roles': ['incoming_historical_replay_helper05', 'nested_014_codeql_pending_historical_replay_helper'], 'caller_path': 'reports/releases/v0.9.2/acquisition/joern-capability-continuation-05.py', 'caller_sha256': '848272ddad3328862b24151a27fd22b48fd6cf8ad6456c4b7c474d30d01bf4a6', 'duplicate_path_identity_policy': 'target candidates remain distinct graph objects; this caller/selector selects exactly the named role', 'loader_selector': 'joern_capability_continuation_01_historical', 'phase': 'function_late', 'reachability': 'conditional historical05 predecessor validation', 'route_id': 'dynamic-035', 'selected_target_role': 'nested_035_joern_capability_continuation_01_historical', 'target_path': 'reports/releases/v0.9.2/acquisition/joern-capability-continuation-01.py', 'target_role_candidates': ['incoming_historical_previous_helper01', 'nested_015_codeql_pending_historical_previous_helper', 'nested_035_joern_capability_continuation_01_historical'], 'target_sha256': '712d456fdb7e8c7f658d5e3cded8a2bc8cc276b9a890cf0c4944fdbafa9828fa'}, {'caller_function': '_recompute_repaired_projection', 'caller_graph_roles': ['incoming_historical_replay_helper05', 'nested_014_codeql_pending_historical_replay_helper'], 'caller_path': 'reports/releases/v0.9.2/acquisition/joern-capability-continuation-05.py', 'caller_sha256': '848272ddad3328862b24151a27fd22b48fd6cf8ad6456c4b7c474d30d01bf4a6', 'duplicate_path_identity_policy': 'target candidates remain distinct graph objects; this caller/selector selects exactly the named role', 'loader_selector': 'joern_continuation_repair_shim', 'phase': 'function_late', 'reachability': 'conditional historical projection validation', 'route_id': 'dynamic-036', 'selected_target_role': 'nested_036_joern_continuation_repair_shim', 'target_path': 'scripts/joern_capability_repair_v092.py', 'target_role_candidates': ['nested_030_joern_capability_repair_continuation_shim', 'nested_034_joern_capability_repair_continuation_shim', 'nested_036_joern_continuation_repair_shim'], 'target_sha256': '535ec9dcc88f5562ccd468822b2c137928caccf614e97b82d94a0b68f905f16f'}, {'caller_function': '_load_runner', 'caller_graph_roles': ['nested_030_joern_capability_repair_continuation_shim', 'nested_034_joern_capability_repair_continuation_shim', 'nested_036_joern_continuation_repair_shim'], 'caller_path': 'scripts/joern_capability_repair_v092.py', 'caller_sha256': '535ec9dcc88f5562ccd468822b2c137928caccf614e97b82d94a0b68f905f16f', 'duplicate_path_identity_policy': 'single exact graph role', 'loader_selector': 'joern_normal_runner_v092_repair_pinned', 'phase': 'function_late', 'reachability': 'conditional shim validation or execution; not all branches mandatory for context derivation', 'route_id': 'dynamic-037', 'selected_target_role': 'nested_037_joern_normal_runner_v092_repair_pinned', 'target_path': 'scripts/joern_normal_runner_v092.py', 'target_role_candidates': ['nested_037_joern_normal_runner_v092_repair_pinned'], 'target_sha256': '683a1bb22a2ec943d357cd4b86982dd7ee62c22a47c28ee3c32e91d114f977f4'}, {'caller_function': '_load_projection_module', 'caller_graph_roles': ['nested_030_joern_capability_repair_continuation_shim', 'nested_034_joern_capability_repair_continuation_shim', 'nested_036_joern_continuation_repair_shim'], 'caller_path': 'scripts/joern_capability_repair_v092.py', 'caller_sha256': '535ec9dcc88f5562ccd468822b2c137928caccf614e97b82d94a0b68f905f16f', 'duplicate_path_identity_policy': 'single exact graph role', 'loader_selector': 'v092_qualification', 'phase': 'function_late', 'reachability': 'conditional shim validation or execution; not all branches mandatory for context derivation', 'route_id': 'dynamic-038', 'selected_target_role': 'nested_038_v092_qualification', 'target_path': 'scripts/v092_qualification.py', 'target_role_candidates': ['nested_038_v092_qualification'], 'target_sha256': 'f673a5b5133c1101e7379fc365a83a47a7525c3daf15efa34a6eed12858e7cb5'}, {'caller_function': 'execute_repaired', 'caller_graph_roles': ['nested_030_joern_capability_repair_continuation_shim', 'nested_034_joern_capability_repair_continuation_shim', 'nested_036_joern_continuation_repair_shim'], 'caller_path': 'scripts/joern_capability_repair_v092.py', 'caller_sha256': '535ec9dcc88f5562ccd468822b2c137928caccf614e97b82d94a0b68f905f16f', 'duplicate_path_identity_policy': 'single exact graph role', 'loader_selector': 'joern_normal_reports_v092_repair_pinned', 'phase': 'function_late', 'reachability': 'conditional shim validation or execution; not all branches mandatory for context derivation', 'route_id': 'dynamic-039', 'selected_target_role': 'nested_039_joern_normal_reports_v092_repair_pinned', 'target_path': 'scripts/joern_normal_reports_v092.py', 'target_role_candidates': ['nested_039_joern_normal_reports_v092_repair_pinned'], 'target_sha256': '75531186a9091e9e907a2c42388efea0e33d4872787a28fa9fc20b3643131db1'}, {'caller_function': 'private_engine', 'caller_graph_roles': ['local_012_swift_common_population_v2'], 'caller_path': 'scripts/swift_common_population_v2.py', 'caller_sha256': '3dee12724faf7a3937a3741a086a9858518ed27271644bbb788b458caef6b6c6', 'duplicate_path_identity_policy': 'single exact graph role', 'loader_selector': '_dfb_common_v2_codeql_runner_<root-token>', 'phase': 'function_late', 'reachability': 'conditional private-engine construction', 'route_id': 'dynamic-040', 'selected_target_role': 'nested_040_dfb_common_v2_codeql_runner__root_token', 'target_path': 'scripts/swift_normal_runner_v1.py', 'target_role_candidates': ['nested_040_dfb_common_v2_codeql_runner__root_token'], 'target_sha256': 'f046c917c5c809199d37956ba950a4267523a74872ee8291ac4a732b7882cafb'}, {'caller_function': 'private_engine', 'caller_graph_roles': ['local_012_swift_common_population_v2'], 'caller_path': 'scripts/swift_common_population_v2.py', 'caller_sha256': '3dee12724faf7a3937a3741a086a9858518ed27271644bbb788b458caef6b6c6', 'duplicate_path_identity_policy': 'single exact graph role', 'loader_selector': '_dfb_common_v2_codeql_reports_<root-token>', 'phase': 'function_late', 'reachability': 'conditional private-engine construction', 'route_id': 'dynamic-041', 'selected_target_role': 'nested_041_dfb_common_v2_codeql_reports__root_token', 'target_path': 'scripts/swift_normal_reports_v1.py', 'target_role_candidates': ['nested_041_dfb_common_v2_codeql_reports__root_token'], 'target_sha256': '4a9ee1c8708ab368452492b87f01d721bb31aa31bd6f526ddb18890f82d01ff3'}, {'caller_function': 'private_engine', 'caller_graph_roles': ['local_012_swift_common_population_v2'], 'caller_path': 'scripts/swift_common_population_v2.py', 'caller_sha256': '3dee12724faf7a3937a3741a086a9858518ed27271644bbb788b458caef6b6c6', 'duplicate_path_identity_policy': 'single exact graph role', 'loader_selector': '_dfb_common_v2_joern_runner_<root-token>', 'phase': 'function_late', 'reachability': 'conditional private-engine construction', 'route_id': 'dynamic-042', 'selected_target_role': 'nested_042_dfb_common_v2_joern_runner__root_token', 'target_path': 'scripts/joern_normal_runner_v1.py', 'target_role_candidates': ['nested_042_dfb_common_v2_joern_runner__root_token'], 'target_sha256': '4103ef8d9d2dc671408389dad57ee934ae01333a2cf5eecc8330ab9feb3be330'}, {'caller_function': 'private_engine', 'caller_graph_roles': ['local_012_swift_common_population_v2'], 'caller_path': 'scripts/swift_common_population_v2.py', 'caller_sha256': '3dee12724faf7a3937a3741a086a9858518ed27271644bbb788b458caef6b6c6', 'duplicate_path_identity_policy': 'single exact graph role', 'loader_selector': '_dfb_common_v2_joern_reports_<root-token>', 'phase': 'function_late', 'reachability': 'conditional private-engine construction', 'route_id': 'dynamic-043', 'selected_target_role': 'nested_043_dfb_common_v2_joern_reports__root_token', 'target_path': 'scripts/joern_normal_reports_v1.py', 'target_role_candidates': ['nested_043_dfb_common_v2_joern_reports__root_token'], 'target_sha256': 'a3fba23a07317be139a587186f529f3cccc4766a56b0c3d839886e7ce41f0b47'}], 'ordinary_edges': [{'bare_name': 'swift_normal_runner_v092', 'caller_role': 'checker', 'line': 2042, 'phase': 'function_late', 'target_role': 'local_016_swift_normal_runner_v092'}, {'bare_name': 'swift_common_population_v2', 'caller_role': 'checker', 'line': 2043, 'phase': 'function_late', 'target_role': 'local_012_swift_common_population_v2'}, {'bare_name': 'swift_normal_runner_v092', 'caller_role': 'incoming_nested_checker', 'line': 2042, 'phase': 'function_late', 'target_role': 'local_016_swift_normal_runner_v092'}, {'bare_name': 'swift_common_population_v2', 'caller_role': 'incoming_nested_checker', 'line': 2043, 'phase': 'function_late', 'target_role': 'local_012_swift_common_population_v2'}, {'bare_name': 'swift_common_population_v2', 'caller_role': 'local_004_codeql_swift_qualification_v092', 'line': 16, 'phase': 'module_body', 'target_role': 'local_012_swift_common_population_v2'}, {'bare_name': 'swift_entry_observation', 'caller_role': 'local_004_codeql_swift_qualification_v092', 'line': 17, 'phase': 'module_body', 'target_role': 'local_013_swift_entry_observation'}, {'bare_name': 'v092_qualification', 'caller_role': 'local_004_codeql_swift_qualification_v092', 'line': 18, 'phase': 'module_body', 'target_role': 'nested_038_v092_qualification'}, {'bare_name': 'joern_normal_runner_v092', 'caller_role': 'local_005_joern_diagnostic_admission_v092', 'line': 136, 'phase': 'function_late', 'target_role': 'nested_037_joern_normal_runner_v092_repair_pinned'}, {'bare_name': 'joern_normal_runner_v092', 'caller_role': 'local_005_joern_diagnostic_admission_v092', 'line': 387, 'phase': 'function_late', 'target_role': 'nested_037_joern_normal_runner_v092_repair_pinned'}, {'bare_name': 'joern_normal_runner_v092', 'caller_role': 'local_005_joern_diagnostic_admission_v092', 'line': 485, 'phase': 'function_late', 'target_role': 'nested_037_joern_normal_runner_v092_repair_pinned'}, {'bare_name': 'swift_common_population_v2', 'caller_role': 'local_005_joern_diagnostic_admission_v092', 'line': 486, 'phase': 'function_late', 'target_role': 'local_012_swift_common_population_v2'}, {'bare_name': 'joern_normal_runner_v092', 'caller_role': 'local_005_joern_diagnostic_admission_v092', 'line': 522, 'phase': 'function_late', 'target_role': 'nested_037_joern_normal_runner_v092_repair_pinned'}, {'bare_name': 'swift_normal_reports_v1', 'caller_role': 'local_006_joern_execution_revalidation_v1', 'line': 12, 'phase': 'module_body', 'target_role': 'nested_041_dfb_common_v2_codeql_reports__root_token'}, {'bare_name': 'joern_normal_execution_v1', 'caller_role': 'local_006_joern_execution_revalidation_v1', 'line': 13, 'phase': 'module_body', 'target_role': 'local_008_joern_normal_execution_v1'}, {'bare_name': 'swift_normal_reports_v1', 'caller_role': 'local_006_joern_execution_revalidation_v1', 'line': 98, 'phase': 'function_late', 'target_role': 'nested_041_dfb_common_v2_codeql_reports__root_token'}, {'bare_name': 'joern_swift', 'caller_role': 'local_007_joern_normal_controls_v1', 'line': 4, 'phase': 'module_body', 'target_role': 'local_009_joern_swift'}, {'bare_name': 'swift_normal_reports_v1', 'caller_role': 'local_007_joern_normal_controls_v1', 'line': 5, 'phase': 'module_body', 'target_role': 'nested_041_dfb_common_v2_codeql_reports__root_token'}, {'bare_name': 'joern_swift', 'caller_role': 'local_010_run_joern_swift_case', 'line': 9, 'phase': 'module_body', 'target_role': 'local_009_joern_swift'}, {'bare_name': 'swift_common_population_v2', 'caller_role': 'local_015_swift_normal_reports_v092', 'line': 10, 'phase': 'module_body', 'target_role': 'local_012_swift_common_population_v2'}, {'bare_name': 'swift_normal_runner_v092', 'caller_role': 'local_015_swift_normal_reports_v092', 'line': 56, 'phase': 'function_late', 'target_role': 'local_016_swift_normal_runner_v092'}, {'bare_name': 'swift_common_population_v2', 'caller_role': 'local_016_swift_normal_runner_v092', 'line': 17, 'phase': 'module_body', 'target_role': 'local_012_swift_common_population_v2'}, {'bare_name': 'codeql_swift_qualification_v092', 'caller_role': 'local_016_swift_normal_runner_v092', 'line': 18, 'phase': 'module_body', 'target_role': 'local_004_codeql_swift_qualification_v092'}, {'bare_name': 'v092_qualification', 'caller_role': 'local_016_swift_normal_runner_v092', 'line': 19, 'phase': 'module_body', 'target_role': 'nested_038_v092_qualification'}, {'bare_name': 'swift_normal_reports_v092', 'caller_role': 'local_016_swift_normal_runner_v092', 'line': 285, 'phase': 'function_late', 'target_role': 'local_015_swift_normal_reports_v092'}, {'bare_name': 'swift_v3_reports', 'caller_role': 'local_020_swift_v3_runner', 'line': 3, 'phase': 'module_body', 'target_role': 'local_019_swift_v3_reports'}, {'bare_name': 'swift_normal_runner_v092', 'caller_role': 'nested_004_replacement05_checker', 'line': 2042, 'phase': 'function_late', 'target_role': 'local_016_swift_normal_runner_v092'}, {'bare_name': 'swift_common_population_v2', 'caller_role': 'nested_004_replacement05_checker', 'line': 2043, 'phase': 'function_late', 'target_role': 'local_012_swift_common_population_v2'}, {'bare_name': 'swift_normal_runner_v092', 'caller_role': 'nested_005_codeql_pending_checker', 'line': 2042, 'phase': 'function_late', 'target_role': 'local_016_swift_normal_runner_v092'}, {'bare_name': 'swift_common_population_v2', 'caller_role': 'nested_005_codeql_pending_checker', 'line': 2043, 'phase': 'function_late', 'target_role': 'local_012_swift_common_population_v2'}, {'bare_name': 'swift_normal_runner_v092', 'caller_role': 'nested_016_check_release_v092_for_config_validation', 'line': 2042, 'phase': 'function_late', 'target_role': 'local_016_swift_normal_runner_v092'}, {'bare_name': 'swift_common_population_v2', 'caller_role': 'nested_016_check_release_v092_for_config_validation', 'line': 2043, 'phase': 'function_late', 'target_role': 'local_012_swift_common_population_v2'}, {'bare_name': 'swift_normal_runner_v092', 'caller_role': 'nested_022_check_release_v092_scoped_replay', 'line': 2042, 'phase': 'function_late', 'target_role': 'local_016_swift_normal_runner_v092'}, {'bare_name': 'swift_common_population_v2', 'caller_role': 'nested_022_check_release_v092_scoped_replay', 'line': 2043, 'phase': 'function_late', 'target_role': 'local_012_swift_common_population_v2'}, {'bare_name': 'swift_normal_runner_v092', 'caller_role': 'nested_023_check_release_v092_resource_replay', 'line': 2042, 'phase': 'function_late', 'target_role': 'local_016_swift_normal_runner_v092'}, {'bare_name': 'swift_common_population_v2', 'caller_role': 'nested_023_check_release_v092_resource_replay', 'line': 2043, 'phase': 'function_late', 'target_role': 'local_012_swift_common_population_v2'}, {'bare_name': 'swift_normal_runner_v092', 'caller_role': 'nested_028_joern_continuation_frozen_checker', 'line': 2042, 'phase': 'function_late', 'target_role': 'local_016_swift_normal_runner_v092'}, {'bare_name': 'swift_common_population_v2', 'caller_role': 'nested_028_joern_continuation_frozen_checker', 'line': 2043, 'phase': 'function_late', 'target_role': 'local_012_swift_common_population_v2'}, {'bare_name': 'joern_normal_runner_v092', 'caller_role': 'nested_030_joern_capability_repair_continuation_shim', 'line': 515, 'phase': 'function_late', 'target_role': 'nested_037_joern_normal_runner_v092_repair_pinned'}, {'bare_name': 'swift_normal_runner_v092', 'caller_role': 'nested_032_joern_continuation_frozen_checker', 'line': 2042, 'phase': 'function_late', 'target_role': 'local_016_swift_normal_runner_v092'}, {'bare_name': 'swift_common_population_v2', 'caller_role': 'nested_032_joern_continuation_frozen_checker', 'line': 2043, 'phase': 'function_late', 'target_role': 'local_012_swift_common_population_v2'}, {'bare_name': 'joern_normal_runner_v092', 'caller_role': 'nested_034_joern_capability_repair_continuation_shim', 'line': 515, 'phase': 'function_late', 'target_role': 'nested_037_joern_normal_runner_v092_repair_pinned'}, {'bare_name': 'joern_normal_runner_v092', 'caller_role': 'nested_036_joern_continuation_repair_shim', 'line': 515, 'phase': 'function_late', 'target_role': 'nested_037_joern_normal_runner_v092_repair_pinned'}, {'bare_name': 'swift_common_population_v2', 'caller_role': 'nested_037_joern_normal_runner_v092_repair_pinned', 'line': 13, 'phase': 'module_body', 'target_role': 'local_012_swift_common_population_v2'}, {'bare_name': 'v092_qualification', 'caller_role': 'nested_037_joern_normal_runner_v092_repair_pinned', 'line': 14, 'phase': 'module_body', 'target_role': 'nested_038_v092_qualification'}, {'bare_name': 'joern_normal_controls_v1', 'caller_role': 'nested_037_joern_normal_runner_v092_repair_pinned', 'line': 15, 'phase': 'module_body', 'target_role': 'local_007_joern_normal_controls_v1'}, {'bare_name': 'joern_diagnostic_admission_v092', 'caller_role': 'nested_037_joern_normal_runner_v092_repair_pinned', 'line': 213, 'phase': 'function_late', 'target_role': 'local_005_joern_diagnostic_admission_v092'}, {'bare_name': 'joern_diagnostic_admission_v092', 'caller_role': 'nested_037_joern_normal_runner_v092_repair_pinned', 'line': 245, 'phase': 'function_late', 'target_role': 'local_005_joern_diagnostic_admission_v092'}, {'bare_name': 'swift_common_population_v2', 'caller_role': 'nested_039_joern_normal_reports_v092_repair_pinned', 'line': 8, 'phase': 'module_body', 'target_role': 'local_012_swift_common_population_v2'}, {'bare_name': 'swift_normal_reports_v1', 'caller_role': 'nested_039_joern_normal_reports_v092_repair_pinned', 'line': 9, 'phase': 'module_body', 'target_role': 'nested_041_dfb_common_v2_codeql_reports__root_token'}, {'bare_name': 'swift_v2_process', 'caller_role': 'nested_040_dfb_common_v2_codeql_runner__root_token', 'line': 16, 'phase': 'module_body', 'target_role': 'local_018_swift_v2_process'}, {'bare_name': 'swift_extraction_integrity', 'caller_role': 'nested_040_dfb_common_v2_codeql_runner__root_token', 'line': 17, 'phase': 'module_body', 'target_role': 'local_014_swift_extraction_integrity'}, {'bare_name': 'swift_artifact_closure', 'caller_role': 'nested_040_dfb_common_v2_codeql_runner__root_token', 'line': 18, 'phase': 'module_body', 'target_role': 'local_011_swift_artifact_closure'}, {'bare_name': 'swift_normal_reports_v1', 'caller_role': 'nested_040_dfb_common_v2_codeql_runner__root_token', 'line': 19, 'phase': 'module_body', 'target_role': 'nested_041_dfb_common_v2_codeql_reports__root_token'}, {'bare_name': 'swift_persistence_coverage', 'caller_role': 'nested_040_dfb_common_v2_codeql_runner__root_token', 'line': 21, 'phase': 'module_body', 'target_role': 'local_017_swift_persistence_coverage'}, {'bare_name': 'swift_v3_runner', 'caller_role': 'nested_040_dfb_common_v2_codeql_runner__root_token', 'line': 22, 'phase': 'module_body', 'target_role': 'local_020_swift_v3_runner'}, {'bare_name': 'swift_normal_runner_v1', 'caller_role': 'nested_041_dfb_common_v2_codeql_reports__root_token', 'line': 205, 'phase': 'function_late', 'target_role': 'nested_040_dfb_common_v2_codeql_runner__root_token'}, {'bare_name': 'swift_v2_process', 'caller_role': 'nested_042_dfb_common_v2_joern_runner__root_token', 'line': 10, 'phase': 'module_body', 'target_role': 'local_018_swift_v2_process'}, {'bare_name': 'joern_execution_revalidation_v1', 'caller_role': 'nested_042_dfb_common_v2_joern_runner__root_token', 'line': 11, 'phase': 'module_body', 'target_role': 'local_006_joern_execution_revalidation_v1'}, {'bare_name': 'joern_normal_execution_v1', 'caller_role': 'nested_042_dfb_common_v2_joern_runner__root_token', 'line': 12, 'phase': 'module_body', 'target_role': 'local_008_joern_normal_execution_v1'}, {'bare_name': 'swift_artifact_closure', 'caller_role': 'nested_042_dfb_common_v2_joern_runner__root_token', 'line': 13, 'phase': 'module_body', 'target_role': 'local_011_swift_artifact_closure'}, {'bare_name': 'swift_normal_reports_v1', 'caller_role': 'nested_042_dfb_common_v2_joern_runner__root_token', 'line': 14, 'phase': 'module_body', 'target_role': 'nested_041_dfb_common_v2_codeql_reports__root_token'}, {'bare_name': 'swift_normal_runner_v1', 'caller_role': 'nested_042_dfb_common_v2_joern_runner__root_token', 'line': 15, 'phase': 'module_body', 'target_role': 'nested_040_dfb_common_v2_codeql_runner__root_token'}, {'bare_name': 'joern_normal_controls_v1', 'caller_role': 'nested_042_dfb_common_v2_joern_runner__root_token', 'line': 16, 'phase': 'module_body', 'target_role': 'local_007_joern_normal_controls_v1'}, {'bare_name': 'joern_normal_reports_v1', 'caller_role': 'nested_042_dfb_common_v2_joern_runner__root_token', 'line': 217, 'phase': 'function_late', 'target_role': 'nested_043_dfb_common_v2_joern_reports__root_token'}, {'bare_name': 'joern_normal_reports_v1', 'caller_role': 'nested_042_dfb_common_v2_joern_runner__root_token', 'line': 364, 'phase': 'function_late', 'target_role': 'nested_043_dfb_common_v2_joern_reports__root_token'}, {'bare_name': 'swift_normal_reports_v1', 'caller_role': 'nested_043_dfb_common_v2_joern_reports__root_token', 'line': 5, 'phase': 'module_body', 'target_role': 'nested_041_dfb_common_v2_codeql_reports__root_token'}, {'bare_name': 'joern_normal_execution_v1', 'caller_role': 'nested_043_dfb_common_v2_joern_reports__root_token', 'line': 48, 'phase': 'function_late', 'target_role': 'local_008_joern_normal_execution_v1'}, {'bare_name': 'joern_normal_runner_v1', 'caller_role': 'nested_043_dfb_common_v2_joern_reports__root_token', 'line': 117, 'phase': 'function_late', 'target_role': 'nested_042_dfb_common_v2_joern_runner__root_token'}, {'bare_name': 'joern_normal_controls_v1', 'caller_role': 'nested_043_dfb_common_v2_joern_reports__root_token', 'line': 161, 'phase': 'function_late', 'target_role': 'local_007_joern_normal_controls_v1'}], 'eager_initialization_graph': {'edge_count': 78, 'provider_first_scc_order': [['admission14'], ['bridge09'], ['disk_guard'], ['executor'], ['host_admission14'], ['host_bridge09'], ['host_protocol14'], ['host_supervisor14'], ['incoming_historical_previous_helper01'], ['incoming_historical_replay_helper05'], ['incoming_nested_executor'], ['incoming_nested_resource_recovery'], ['incoming_nested_scoped_recovery'], ['incoming_predecessor03'], ['incoming_recovery'], ['local_001_bifrost_v0140_frozen_bridge_08'], ['local_008_joern_normal_execution_v1'], ['local_009_joern_swift'], ['local_011_swift_artifact_closure'], ['local_012_swift_common_population_v2'], ['local_013_swift_entry_observation'], ['local_014_swift_extraction_integrity'], ['local_017_swift_persistence_coverage'], ['local_018_swift_v2_process'], ['local_019_swift_v3_reports'], ['nested_001_v092_frozen_bridge_02_replacement05'], ['nested_002_replacement05_executor'], ['nested_003_codeql_pending_executor'], ['nested_008_codeql_pending_disk_guard'], ['nested_009_bridge06_incoming_policy'], ['nested_010_bridge03_window_policy'], ['nested_011_v092_frozen_bridge_02_source_design04_policy'], ['nested_012_v092_frozen_bridge_02_independent_codeql_history'], ['nested_013_codeql_terminal_history_03'], ['nested_014_codeql_pending_historical_replay_helper'], ['nested_015_codeql_pending_historical_previous_helper'], ['nested_017_execute_release_v092_for_checker'], ['nested_018_v092_resource_recovery_for_checker'], ['nested_019_v092_scoped_recovery_for_checker'], ['nested_020_v092_scoped_recovery_packet'], ['nested_021_v092_resource_recovery'], ['nested_024_v092_process_tracker'], ['nested_025_v092_disk_guard_runtime'], ['nested_026_v092_replacement09_supervisor_terminal_disk_guard'], ['nested_027_joern_continuation_frozen_execute'], ['nested_031_joern_continuation_frozen_execute'], ['nested_035_joern_capability_continuation_01_historical'], ['nested_038_v092_qualification'], ['policy_runtime'], ['policy_source'], ['protocol14'], ['replacement05'], ['replacement14'], ['runtime_loaders14'], ['stage_runtime01'], ['supervisor14'], ['local_010_run_joern_swift_case'], ['local_020_swift_v3_runner'], ['local_004_codeql_swift_qualification_v092'], ['nested_040_dfb_common_v2_codeql_runner__root_token', 'nested_041_dfb_common_v2_codeql_reports__root_token'], ['local_015_swift_normal_reports_v092', 'local_016_swift_normal_runner_v092'], ['local_006_joern_execution_revalidation_v1'], ['local_007_joern_normal_controls_v1'], ['nested_039_joern_normal_reports_v092_repair_pinned'], ['checker'], ['incoming_nested_checker'], ['nested_004_replacement05_checker'], ['nested_005_codeql_pending_checker'], ['nested_016_check_release_v092_for_config_validation'], ['nested_022_check_release_v092_scoped_replay'], ['nested_023_check_release_v092_resource_replay'], ['nested_028_joern_continuation_frozen_checker'], ['nested_032_joern_continuation_frozen_checker'], ['local_005_joern_diagnostic_admission_v092', 'nested_037_joern_normal_runner_v092_repair_pinned'], ['nested_042_dfb_common_v2_joern_runner__root_token', 'nested_043_dfb_common_v2_joern_reports__root_token'], ['configuration'], ['incoming_nested_configuration'], ['nested_006_replacement05_configuration'], ['nested_007_codeql_pending_configuration'], ['nested_029_joern_continuation_frozen_configuration'], ['nested_033_joern_continuation_frozen_configuration'], ['nested_030_joern_capability_repair_continuation_shim'], ['nested_034_joern_capability_repair_continuation_shim'], ['nested_036_joern_continuation_repair_shim']], 'scc_count': 84, 'sccs': [['admission14'], ['bridge09'], ['incoming_nested_executor'], ['local_012_swift_common_population_v2'], ['local_013_swift_entry_observation'], ['nested_038_v092_qualification'], ['local_004_codeql_swift_qualification_v092'], ['local_015_swift_normal_reports_v092', 'local_016_swift_normal_runner_v092'], ['checker'], ['incoming_nested_checker'], ['configuration'], ['disk_guard'], ['executor'], ['host_admission14'], ['host_bridge09'], ['host_protocol14'], ['host_supervisor14'], ['incoming_historical_previous_helper01'], ['incoming_historical_replay_helper05'], ['incoming_nested_configuration'], ['incoming_nested_resource_recovery'], ['incoming_nested_scoped_recovery'], ['incoming_predecessor03'], ['incoming_recovery'], ['local_001_bifrost_v0140_frozen_bridge_08'], ['local_009_joern_swift'], ['local_011_swift_artifact_closure'], ['local_014_swift_extraction_integrity'], ['local_017_swift_persistence_coverage'], ['local_018_swift_v2_process'], ['local_019_swift_v3_reports'], ['local_020_swift_v3_runner'], ['nested_040_dfb_common_v2_codeql_runner__root_token', 'nested_041_dfb_common_v2_codeql_reports__root_token'], ['local_007_joern_normal_controls_v1'], ['local_005_joern_diagnostic_admission_v092', 'nested_037_joern_normal_runner_v092_repair_pinned'], ['local_008_joern_normal_execution_v1'], ['local_006_joern_execution_revalidation_v1'], ['local_010_run_joern_swift_case'], ['nested_001_v092_frozen_bridge_02_replacement05'], ['nested_002_replacement05_executor'], ['nested_003_codeql_pending_executor'], ['nested_004_replacement05_checker'], ['nested_005_codeql_pending_checker'], ['nested_006_replacement05_configuration'], ['nested_007_codeql_pending_configuration'], ['nested_008_codeql_pending_disk_guard'], ['nested_009_bridge06_incoming_policy'], ['nested_010_bridge03_window_policy'], ['nested_011_v092_frozen_bridge_02_source_design04_policy'], ['nested_012_v092_frozen_bridge_02_independent_codeql_history'], ['nested_013_codeql_terminal_history_03'], ['nested_014_codeql_pending_historical_replay_helper'], ['nested_015_codeql_pending_historical_previous_helper'], ['nested_016_check_release_v092_for_config_validation'], ['nested_017_execute_release_v092_for_checker'], ['nested_018_v092_resource_recovery_for_checker'], ['nested_019_v092_scoped_recovery_for_checker'], ['nested_020_v092_scoped_recovery_packet'], ['nested_021_v092_resource_recovery'], ['nested_022_check_release_v092_scoped_replay'], ['nested_023_check_release_v092_resource_replay'], ['nested_024_v092_process_tracker'], ['nested_025_v092_disk_guard_runtime'], ['nested_026_v092_replacement09_supervisor_terminal_disk_guard'], ['nested_027_joern_continuation_frozen_execute'], ['nested_028_joern_continuation_frozen_checker'], ['nested_029_joern_continuation_frozen_configuration'], ['nested_030_joern_capability_repair_continuation_shim'], ['nested_031_joern_continuation_frozen_execute'], ['nested_032_joern_continuation_frozen_checker'], ['nested_033_joern_continuation_frozen_configuration'], ['nested_034_joern_capability_repair_continuation_shim'], ['nested_035_joern_capability_continuation_01_historical'], ['nested_036_joern_continuation_repair_shim'], ['nested_039_joern_normal_reports_v092_repair_pinned'], ['nested_042_dfb_common_v2_joern_runner__root_token', 'nested_043_dfb_common_v2_joern_reports__root_token'], ['policy_runtime'], ['policy_source'], ['protocol14'], ['replacement05'], ['replacement14'], ['runtime_loaders14'], ['stage_runtime01'], ['supervisor14']]}, 'union_graph': {'edge_count': 199, 'provider_first_scc_order': [['admission14'], ['bridge09'], ['disk_guard'], ['host_admission14'], ['host_bridge09'], ['host_protocol14'], ['incoming_nested_resource_recovery'], ['incoming_nested_scoped_recovery'], ['local_008_joern_normal_execution_v1'], ['local_009_joern_swift'], ['local_011_swift_artifact_closure'], ['local_013_swift_entry_observation'], ['local_014_swift_extraction_integrity'], ['local_017_swift_persistence_coverage'], ['local_018_swift_v2_process'], ['local_019_swift_v3_reports'], ['nested_008_codeql_pending_disk_guard'], ['nested_009_bridge06_incoming_policy'], ['nested_010_bridge03_window_policy'], ['nested_011_v092_frozen_bridge_02_source_design04_policy'], ['nested_018_v092_resource_recovery_for_checker'], ['nested_019_v092_scoped_recovery_for_checker'], ['nested_020_v092_scoped_recovery_packet'], ['nested_021_v092_resource_recovery'], ['nested_024_v092_process_tracker'], ['nested_025_v092_disk_guard_runtime'], ['nested_026_v092_replacement09_supervisor_terminal_disk_guard'], ['nested_038_v092_qualification'], ['policy_runtime'], ['policy_source'], ['protocol14'], ['replacement14'], ['runtime_loaders14'], ['stage_runtime01'], ['host_supervisor14'], ['supervisor14'], ['local_010_run_joern_swift_case'], ['local_020_swift_v3_runner'], ['nested_040_dfb_common_v2_codeql_runner__root_token', 'nested_041_dfb_common_v2_codeql_reports__root_token'], ['local_006_joern_execution_revalidation_v1'], ['local_007_joern_normal_controls_v1'], ['nested_042_dfb_common_v2_joern_runner__root_token', 'nested_043_dfb_common_v2_joern_reports__root_token'], ['local_012_swift_common_population_v2'], ['local_004_codeql_swift_qualification_v092'], ['local_005_joern_diagnostic_admission_v092', 'nested_037_joern_normal_runner_v092_repair_pinned'], ['nested_039_joern_normal_reports_v092_repair_pinned'], ['local_015_swift_normal_reports_v092', 'local_016_swift_normal_runner_v092'], ['nested_030_joern_capability_repair_continuation_shim'], ['nested_034_joern_capability_repair_continuation_shim'], ['nested_036_joern_continuation_repair_shim'], ['incoming_nested_executor', 'nested_022_check_release_v092_scoped_replay', 'nested_023_check_release_v092_resource_replay'], ['checker'], ['executor'], ['incoming_nested_checker'], ['nested_002_replacement05_executor'], ['nested_003_codeql_pending_executor'], ['nested_004_replacement05_checker'], ['nested_005_codeql_pending_checker'], ['nested_016_check_release_v092_for_config_validation'], ['nested_017_execute_release_v092_for_checker'], ['nested_027_joern_continuation_frozen_execute'], ['nested_028_joern_continuation_frozen_checker'], ['nested_031_joern_continuation_frozen_execute'], ['nested_032_joern_continuation_frozen_checker'], ['configuration'], ['incoming_nested_configuration'], ['nested_006_replacement05_configuration'], ['nested_007_codeql_pending_configuration'], ['nested_029_joern_continuation_frozen_configuration'], ['nested_033_joern_continuation_frozen_configuration'], ['nested_001_v092_frozen_bridge_02_replacement05'], ['replacement05'], ['incoming_historical_previous_helper01'], ['nested_015_codeql_pending_historical_previous_helper'], ['nested_035_joern_capability_continuation_01_historical'], ['incoming_historical_replay_helper05'], ['nested_014_codeql_pending_historical_replay_helper'], ['incoming_predecessor03'], ['nested_013_codeql_terminal_history_03'], ['incoming_recovery'], ['nested_012_v092_frozen_bridge_02_independent_codeql_history'], ['local_001_bifrost_v0140_frozen_bridge_08']], 'scc_count': 82, 'sccs': [['admission14'], ['bridge09'], ['disk_guard'], ['nested_020_v092_scoped_recovery_packet'], ['nested_021_v092_resource_recovery'], ['local_011_swift_artifact_closure'], ['local_014_swift_extraction_integrity'], ['local_017_swift_persistence_coverage'], ['local_018_swift_v2_process'], ['local_019_swift_v3_reports'], ['local_020_swift_v3_runner'], ['nested_040_dfb_common_v2_codeql_runner__root_token', 'nested_041_dfb_common_v2_codeql_reports__root_token'], ['local_008_joern_normal_execution_v1'], ['local_006_joern_execution_revalidation_v1'], ['local_009_joern_swift'], ['local_007_joern_normal_controls_v1'], ['nested_042_dfb_common_v2_joern_runner__root_token', 'nested_043_dfb_common_v2_joern_reports__root_token'], ['local_012_swift_common_population_v2'], ['local_013_swift_entry_observation'], ['nested_038_v092_qualification'], ['local_004_codeql_swift_qualification_v092'], ['local_015_swift_normal_reports_v092', 'local_016_swift_normal_runner_v092'], ['nested_018_v092_resource_recovery_for_checker'], ['nested_019_v092_scoped_recovery_for_checker'], ['nested_024_v092_process_tracker'], ['incoming_nested_executor', 'nested_022_check_release_v092_scoped_replay', 'nested_023_check_release_v092_resource_replay'], ['checker'], ['incoming_nested_checker'], ['configuration'], ['executor'], ['host_admission14'], ['host_bridge09'], ['host_protocol14'], ['host_supervisor14'], ['nested_027_joern_continuation_frozen_execute'], ['nested_028_joern_continuation_frozen_checker'], ['nested_029_joern_continuation_frozen_configuration'], ['local_005_joern_diagnostic_admission_v092', 'nested_037_joern_normal_runner_v092_repair_pinned'], ['nested_039_joern_normal_reports_v092_repair_pinned'], ['nested_030_joern_capability_repair_continuation_shim'], ['incoming_historical_previous_helper01'], ['nested_031_joern_continuation_frozen_execute'], ['nested_032_joern_continuation_frozen_checker'], ['nested_033_joern_continuation_frozen_configuration'], ['nested_034_joern_capability_repair_continuation_shim'], ['nested_035_joern_capability_continuation_01_historical'], ['nested_036_joern_continuation_repair_shim'], ['incoming_historical_replay_helper05'], ['incoming_nested_configuration'], ['incoming_nested_resource_recovery'], ['incoming_nested_scoped_recovery'], ['nested_003_codeql_pending_executor'], ['nested_005_codeql_pending_checker'], ['nested_007_codeql_pending_configuration'], ['nested_014_codeql_pending_historical_replay_helper'], ['nested_015_codeql_pending_historical_previous_helper'], ['incoming_predecessor03'], ['nested_013_codeql_terminal_history_03'], ['incoming_recovery'], ['nested_002_replacement05_executor'], ['nested_004_replacement05_checker'], ['nested_006_replacement05_configuration'], ['nested_001_v092_frozen_bridge_02_replacement05'], ['nested_009_bridge06_incoming_policy'], ['nested_010_bridge03_window_policy'], ['nested_011_v092_frozen_bridge_02_source_design04_policy'], ['nested_012_v092_frozen_bridge_02_independent_codeql_history'], ['local_001_bifrost_v0140_frozen_bridge_08'], ['local_010_run_joern_swift_case'], ['nested_008_codeql_pending_disk_guard'], ['nested_016_check_release_v092_for_config_validation'], ['nested_017_execute_release_v092_for_checker'], ['nested_025_v092_disk_guard_runtime'], ['nested_026_v092_replacement09_supervisor_terminal_disk_guard'], ['policy_runtime'], ['policy_source'], ['protocol14'], ['replacement05'], ['replacement14'], ['runtime_loaders14'], ['stage_runtime01'], ['supervisor14']]}}
DEFAULT_ORDINARY_EDGES = [{'bare_name': 'swift_normal_runner_v092', 'caller_role': 'checker', 'line': 2042, 'phase': 'function_late', 'target_role': 'local_016_swift_normal_runner_v092'}, {'bare_name': 'swift_common_population_v2', 'caller_role': 'checker', 'line': 2043, 'phase': 'function_late', 'target_role': 'local_012_swift_common_population_v2'}, {'bare_name': 'swift_normal_runner_v092', 'caller_role': 'incoming_nested_checker', 'line': 2042, 'phase': 'function_late', 'target_role': 'local_016_swift_normal_runner_v092'}, {'bare_name': 'swift_common_population_v2', 'caller_role': 'incoming_nested_checker', 'line': 2043, 'phase': 'function_late', 'target_role': 'local_012_swift_common_population_v2'}, {'bare_name': 'swift_common_population_v2', 'caller_role': 'local_004_codeql_swift_qualification_v092', 'line': 16, 'phase': 'module_body', 'target_role': 'local_012_swift_common_population_v2'}, {'bare_name': 'swift_entry_observation', 'caller_role': 'local_004_codeql_swift_qualification_v092', 'line': 17, 'phase': 'module_body', 'target_role': 'local_013_swift_entry_observation'}, {'bare_name': 'v092_qualification', 'caller_role': 'local_004_codeql_swift_qualification_v092', 'line': 18, 'phase': 'module_body', 'target_role': 'nested_038_v092_qualification'}, {'bare_name': 'joern_normal_runner_v092', 'caller_role': 'local_005_joern_diagnostic_admission_v092', 'line': 136, 'phase': 'function_late', 'target_role': 'nested_037_joern_normal_runner_v092_repair_pinned'}, {'bare_name': 'joern_normal_runner_v092', 'caller_role': 'local_005_joern_diagnostic_admission_v092', 'line': 387, 'phase': 'function_late', 'target_role': 'nested_037_joern_normal_runner_v092_repair_pinned'}, {'bare_name': 'joern_normal_runner_v092', 'caller_role': 'local_005_joern_diagnostic_admission_v092', 'line': 485, 'phase': 'function_late', 'target_role': 'nested_037_joern_normal_runner_v092_repair_pinned'}, {'bare_name': 'swift_common_population_v2', 'caller_role': 'local_005_joern_diagnostic_admission_v092', 'line': 486, 'phase': 'function_late', 'target_role': 'local_012_swift_common_population_v2'}, {'bare_name': 'joern_normal_runner_v092', 'caller_role': 'local_005_joern_diagnostic_admission_v092', 'line': 522, 'phase': 'function_late', 'target_role': 'nested_037_joern_normal_runner_v092_repair_pinned'}, {'bare_name': 'swift_normal_reports_v1', 'caller_role': 'local_006_joern_execution_revalidation_v1', 'line': 12, 'phase': 'module_body', 'target_role': 'nested_041_dfb_common_v2_codeql_reports__root_token'}, {'bare_name': 'joern_normal_execution_v1', 'caller_role': 'local_006_joern_execution_revalidation_v1', 'line': 13, 'phase': 'module_body', 'target_role': 'local_008_joern_normal_execution_v1'}, {'bare_name': 'swift_normal_reports_v1', 'caller_role': 'local_006_joern_execution_revalidation_v1', 'line': 98, 'phase': 'function_late', 'target_role': 'nested_041_dfb_common_v2_codeql_reports__root_token'}, {'bare_name': 'joern_swift', 'caller_role': 'local_007_joern_normal_controls_v1', 'line': 4, 'phase': 'module_body', 'target_role': 'local_009_joern_swift'}, {'bare_name': 'swift_normal_reports_v1', 'caller_role': 'local_007_joern_normal_controls_v1', 'line': 5, 'phase': 'module_body', 'target_role': 'nested_041_dfb_common_v2_codeql_reports__root_token'}, {'bare_name': 'joern_swift', 'caller_role': 'local_010_run_joern_swift_case', 'line': 9, 'phase': 'module_body', 'target_role': 'local_009_joern_swift'}, {'bare_name': 'swift_common_population_v2', 'caller_role': 'local_015_swift_normal_reports_v092', 'line': 10, 'phase': 'module_body', 'target_role': 'local_012_swift_common_population_v2'}, {'bare_name': 'swift_normal_runner_v092', 'caller_role': 'local_015_swift_normal_reports_v092', 'line': 56, 'phase': 'function_late', 'target_role': 'local_016_swift_normal_runner_v092'}, {'bare_name': 'swift_common_population_v2', 'caller_role': 'local_016_swift_normal_runner_v092', 'line': 17, 'phase': 'module_body', 'target_role': 'local_012_swift_common_population_v2'}, {'bare_name': 'codeql_swift_qualification_v092', 'caller_role': 'local_016_swift_normal_runner_v092', 'line': 18, 'phase': 'module_body', 'target_role': 'local_004_codeql_swift_qualification_v092'}, {'bare_name': 'v092_qualification', 'caller_role': 'local_016_swift_normal_runner_v092', 'line': 19, 'phase': 'module_body', 'target_role': 'nested_038_v092_qualification'}, {'bare_name': 'swift_normal_reports_v092', 'caller_role': 'local_016_swift_normal_runner_v092', 'line': 285, 'phase': 'function_late', 'target_role': 'local_015_swift_normal_reports_v092'}, {'bare_name': 'swift_v3_reports', 'caller_role': 'local_020_swift_v3_runner', 'line': 3, 'phase': 'module_body', 'target_role': 'local_019_swift_v3_reports'}, {'bare_name': 'swift_normal_runner_v092', 'caller_role': 'nested_004_replacement05_checker', 'line': 2042, 'phase': 'function_late', 'target_role': 'local_016_swift_normal_runner_v092'}, {'bare_name': 'swift_common_population_v2', 'caller_role': 'nested_004_replacement05_checker', 'line': 2043, 'phase': 'function_late', 'target_role': 'local_012_swift_common_population_v2'}, {'bare_name': 'swift_normal_runner_v092', 'caller_role': 'nested_005_codeql_pending_checker', 'line': 2042, 'phase': 'function_late', 'target_role': 'local_016_swift_normal_runner_v092'}, {'bare_name': 'swift_common_population_v2', 'caller_role': 'nested_005_codeql_pending_checker', 'line': 2043, 'phase': 'function_late', 'target_role': 'local_012_swift_common_population_v2'}, {'bare_name': 'swift_normal_runner_v092', 'caller_role': 'nested_016_check_release_v092_for_config_validation', 'line': 2042, 'phase': 'function_late', 'target_role': 'local_016_swift_normal_runner_v092'}, {'bare_name': 'swift_common_population_v2', 'caller_role': 'nested_016_check_release_v092_for_config_validation', 'line': 2043, 'phase': 'function_late', 'target_role': 'local_012_swift_common_population_v2'}, {'bare_name': 'swift_normal_runner_v092', 'caller_role': 'nested_022_check_release_v092_scoped_replay', 'line': 2042, 'phase': 'function_late', 'target_role': 'local_016_swift_normal_runner_v092'}, {'bare_name': 'swift_common_population_v2', 'caller_role': 'nested_022_check_release_v092_scoped_replay', 'line': 2043, 'phase': 'function_late', 'target_role': 'local_012_swift_common_population_v2'}, {'bare_name': 'swift_normal_runner_v092', 'caller_role': 'nested_023_check_release_v092_resource_replay', 'line': 2042, 'phase': 'function_late', 'target_role': 'local_016_swift_normal_runner_v092'}, {'bare_name': 'swift_common_population_v2', 'caller_role': 'nested_023_check_release_v092_resource_replay', 'line': 2043, 'phase': 'function_late', 'target_role': 'local_012_swift_common_population_v2'}, {'bare_name': 'swift_normal_runner_v092', 'caller_role': 'nested_028_joern_continuation_frozen_checker', 'line': 2042, 'phase': 'function_late', 'target_role': 'local_016_swift_normal_runner_v092'}, {'bare_name': 'swift_common_population_v2', 'caller_role': 'nested_028_joern_continuation_frozen_checker', 'line': 2043, 'phase': 'function_late', 'target_role': 'local_012_swift_common_population_v2'}, {'bare_name': 'joern_normal_runner_v092', 'caller_role': 'nested_030_joern_capability_repair_continuation_shim', 'line': 515, 'phase': 'function_late', 'target_role': 'nested_037_joern_normal_runner_v092_repair_pinned'}, {'bare_name': 'swift_normal_runner_v092', 'caller_role': 'nested_032_joern_continuation_frozen_checker', 'line': 2042, 'phase': 'function_late', 'target_role': 'local_016_swift_normal_runner_v092'}, {'bare_name': 'swift_common_population_v2', 'caller_role': 'nested_032_joern_continuation_frozen_checker', 'line': 2043, 'phase': 'function_late', 'target_role': 'local_012_swift_common_population_v2'}, {'bare_name': 'joern_normal_runner_v092', 'caller_role': 'nested_034_joern_capability_repair_continuation_shim', 'line': 515, 'phase': 'function_late', 'target_role': 'nested_037_joern_normal_runner_v092_repair_pinned'}, {'bare_name': 'joern_normal_runner_v092', 'caller_role': 'nested_036_joern_continuation_repair_shim', 'line': 515, 'phase': 'function_late', 'target_role': 'nested_037_joern_normal_runner_v092_repair_pinned'}, {'bare_name': 'swift_common_population_v2', 'caller_role': 'nested_037_joern_normal_runner_v092_repair_pinned', 'line': 13, 'phase': 'module_body', 'target_role': 'local_012_swift_common_population_v2'}, {'bare_name': 'v092_qualification', 'caller_role': 'nested_037_joern_normal_runner_v092_repair_pinned', 'line': 14, 'phase': 'module_body', 'target_role': 'nested_038_v092_qualification'}, {'bare_name': 'joern_normal_controls_v1', 'caller_role': 'nested_037_joern_normal_runner_v092_repair_pinned', 'line': 15, 'phase': 'module_body', 'target_role': 'local_007_joern_normal_controls_v1'}, {'bare_name': 'joern_diagnostic_admission_v092', 'caller_role': 'nested_037_joern_normal_runner_v092_repair_pinned', 'line': 213, 'phase': 'function_late', 'target_role': 'local_005_joern_diagnostic_admission_v092'}, {'bare_name': 'joern_diagnostic_admission_v092', 'caller_role': 'nested_037_joern_normal_runner_v092_repair_pinned', 'line': 245, 'phase': 'function_late', 'target_role': 'local_005_joern_diagnostic_admission_v092'}, {'bare_name': 'swift_common_population_v2', 'caller_role': 'nested_039_joern_normal_reports_v092_repair_pinned', 'line': 8, 'phase': 'module_body', 'target_role': 'local_012_swift_common_population_v2'}, {'bare_name': 'swift_normal_reports_v1', 'caller_role': 'nested_039_joern_normal_reports_v092_repair_pinned', 'line': 9, 'phase': 'module_body', 'target_role': 'nested_041_dfb_common_v2_codeql_reports__root_token'}, {'bare_name': 'swift_v2_process', 'caller_role': 'nested_040_dfb_common_v2_codeql_runner__root_token', 'line': 16, 'phase': 'module_body', 'target_role': 'local_018_swift_v2_process'}, {'bare_name': 'swift_extraction_integrity', 'caller_role': 'nested_040_dfb_common_v2_codeql_runner__root_token', 'line': 17, 'phase': 'module_body', 'target_role': 'local_014_swift_extraction_integrity'}, {'bare_name': 'swift_artifact_closure', 'caller_role': 'nested_040_dfb_common_v2_codeql_runner__root_token', 'line': 18, 'phase': 'module_body', 'target_role': 'local_011_swift_artifact_closure'}, {'bare_name': 'swift_normal_reports_v1', 'caller_role': 'nested_040_dfb_common_v2_codeql_runner__root_token', 'line': 19, 'phase': 'module_body', 'target_role': 'nested_041_dfb_common_v2_codeql_reports__root_token'}, {'bare_name': 'swift_persistence_coverage', 'caller_role': 'nested_040_dfb_common_v2_codeql_runner__root_token', 'line': 21, 'phase': 'module_body', 'target_role': 'local_017_swift_persistence_coverage'}, {'bare_name': 'swift_v3_runner', 'caller_role': 'nested_040_dfb_common_v2_codeql_runner__root_token', 'line': 22, 'phase': 'module_body', 'target_role': 'local_020_swift_v3_runner'}, {'bare_name': 'swift_normal_runner_v1', 'caller_role': 'nested_041_dfb_common_v2_codeql_reports__root_token', 'line': 205, 'phase': 'function_late', 'target_role': 'nested_040_dfb_common_v2_codeql_runner__root_token'}, {'bare_name': 'swift_v2_process', 'caller_role': 'nested_042_dfb_common_v2_joern_runner__root_token', 'line': 10, 'phase': 'module_body', 'target_role': 'local_018_swift_v2_process'}, {'bare_name': 'joern_execution_revalidation_v1', 'caller_role': 'nested_042_dfb_common_v2_joern_runner__root_token', 'line': 11, 'phase': 'module_body', 'target_role': 'local_006_joern_execution_revalidation_v1'}, {'bare_name': 'joern_normal_execution_v1', 'caller_role': 'nested_042_dfb_common_v2_joern_runner__root_token', 'line': 12, 'phase': 'module_body', 'target_role': 'local_008_joern_normal_execution_v1'}, {'bare_name': 'swift_artifact_closure', 'caller_role': 'nested_042_dfb_common_v2_joern_runner__root_token', 'line': 13, 'phase': 'module_body', 'target_role': 'local_011_swift_artifact_closure'}, {'bare_name': 'swift_normal_reports_v1', 'caller_role': 'nested_042_dfb_common_v2_joern_runner__root_token', 'line': 14, 'phase': 'module_body', 'target_role': 'nested_041_dfb_common_v2_codeql_reports__root_token'}, {'bare_name': 'swift_normal_runner_v1', 'caller_role': 'nested_042_dfb_common_v2_joern_runner__root_token', 'line': 15, 'phase': 'module_body', 'target_role': 'nested_040_dfb_common_v2_codeql_runner__root_token'}, {'bare_name': 'joern_normal_controls_v1', 'caller_role': 'nested_042_dfb_common_v2_joern_runner__root_token', 'line': 16, 'phase': 'module_body', 'target_role': 'local_007_joern_normal_controls_v1'}, {'bare_name': 'joern_normal_reports_v1', 'caller_role': 'nested_042_dfb_common_v2_joern_runner__root_token', 'line': 217, 'phase': 'function_late', 'target_role': 'nested_043_dfb_common_v2_joern_reports__root_token'}, {'bare_name': 'joern_normal_reports_v1', 'caller_role': 'nested_042_dfb_common_v2_joern_runner__root_token', 'line': 364, 'phase': 'function_late', 'target_role': 'nested_043_dfb_common_v2_joern_reports__root_token'}, {'bare_name': 'swift_normal_reports_v1', 'caller_role': 'nested_043_dfb_common_v2_joern_reports__root_token', 'line': 5, 'phase': 'module_body', 'target_role': 'nested_041_dfb_common_v2_codeql_reports__root_token'}, {'bare_name': 'joern_normal_execution_v1', 'caller_role': 'nested_043_dfb_common_v2_joern_reports__root_token', 'line': 48, 'phase': 'function_late', 'target_role': 'local_008_joern_normal_execution_v1'}, {'bare_name': 'joern_normal_runner_v1', 'caller_role': 'nested_043_dfb_common_v2_joern_reports__root_token', 'line': 117, 'phase': 'function_late', 'target_role': 'nested_042_dfb_common_v2_joern_runner__root_token'}, {'bare_name': 'joern_normal_controls_v1', 'caller_role': 'nested_043_dfb_common_v2_joern_reports__root_token', 'line': 161, 'phase': 'function_late', 'target_role': 'local_007_joern_normal_controls_v1'}]
DEFAULT_EAGER_ORDER = ('admission14', 'bridge09', 'disk_guard', 'executor', 'host_admission14', 'host_bridge09', 'host_protocol14', 'host_supervisor14', 'incoming_historical_previous_helper01', 'incoming_historical_replay_helper05', 'incoming_nested_executor', 'incoming_nested_resource_recovery', 'incoming_nested_scoped_recovery', 'incoming_predecessor03', 'incoming_recovery', 'local_001_bifrost_v0140_frozen_bridge_08', 'local_008_joern_normal_execution_v1', 'local_009_joern_swift', 'local_011_swift_artifact_closure', 'local_012_swift_common_population_v2', 'local_013_swift_entry_observation', 'local_014_swift_extraction_integrity', 'local_017_swift_persistence_coverage', 'local_018_swift_v2_process', 'local_019_swift_v3_reports', 'nested_001_v092_frozen_bridge_02_replacement05', 'nested_002_replacement05_executor', 'nested_003_codeql_pending_executor', 'nested_008_codeql_pending_disk_guard', 'nested_009_bridge06_incoming_policy', 'nested_010_bridge03_window_policy', 'nested_011_v092_frozen_bridge_02_source_design04_policy', 'nested_012_v092_frozen_bridge_02_independent_codeql_history', 'nested_013_codeql_terminal_history_03', 'nested_014_codeql_pending_historical_replay_helper', 'nested_015_codeql_pending_historical_previous_helper', 'nested_017_execute_release_v092_for_checker', 'nested_018_v092_resource_recovery_for_checker', 'nested_019_v092_scoped_recovery_for_checker', 'nested_020_v092_scoped_recovery_packet', 'nested_021_v092_resource_recovery', 'nested_024_v092_process_tracker', 'nested_025_v092_disk_guard_runtime', 'nested_026_v092_replacement09_supervisor_terminal_disk_guard', 'nested_027_joern_continuation_frozen_execute', 'nested_031_joern_continuation_frozen_execute', 'nested_035_joern_capability_continuation_01_historical', 'nested_038_v092_qualification', 'policy_runtime', 'policy_source', 'protocol14', 'replacement05', 'replacement14', 'runtime_loaders14', 'stage_runtime01', 'supervisor14', 'local_010_run_joern_swift_case', 'local_020_swift_v3_runner', 'local_004_codeql_swift_qualification_v092', 'nested_040_dfb_common_v2_codeql_runner__root_token', 'nested_041_dfb_common_v2_codeql_reports__root_token', 'local_015_swift_normal_reports_v092', 'local_016_swift_normal_runner_v092', 'local_006_joern_execution_revalidation_v1', 'local_007_joern_normal_controls_v1', 'nested_039_joern_normal_reports_v092_repair_pinned', 'checker', 'incoming_nested_checker', 'nested_004_replacement05_checker', 'nested_005_codeql_pending_checker', 'nested_016_check_release_v092_for_config_validation', 'nested_022_check_release_v092_scoped_replay', 'nested_023_check_release_v092_resource_replay', 'nested_028_joern_continuation_frozen_checker', 'nested_032_joern_continuation_frozen_checker', 'local_005_joern_diagnostic_admission_v092', 'nested_037_joern_normal_runner_v092_repair_pinned', 'nested_042_dfb_common_v2_joern_runner__root_token', 'nested_043_dfb_common_v2_joern_reports__root_token', 'configuration', 'incoming_nested_configuration', 'nested_006_replacement05_configuration', 'nested_007_codeql_pending_configuration', 'nested_029_joern_continuation_frozen_configuration', 'nested_033_joern_continuation_frozen_configuration', 'nested_030_joern_capability_repair_continuation_shim', 'nested_034_joern_capability_repair_continuation_shim', 'nested_036_joern_continuation_repair_shim')


def _graph_name_variants() -> tuple[tuple[str, ...], ...]:
    """Return the only accepted graph rosters, in deterministic order.

    ``stage_runtime09`` is an append-only successor seam.  It is optional for
    the historical bridge fixture and mandatory for the production successor;
    accepting arbitrary extra names here would let a caller smuggle an
    unreviewed loader into the runtime graph.
    """
    return (
        REQUIRED_GRAPH_NAMES,
        REQUIRED_GRAPH_NAMES + ("disk_guard",),
        REQUIRED_GRAPH_NAMES + (STAGE_RUNTIME_GRAPH_NAME,),
        REQUIRED_GRAPH_NAMES + ("disk_guard", STAGE_RUNTIME_GRAPH_NAME),
    )


def _validate_graph_names(names: Sequence[str]) -> tuple[str, ...]:
    """Validate the mandatory roster plus explicitly sealed transitive extras.

    The first eleven roles are fixed.  Later names are the exact extra module
    instances enumerated by the reviewed core graph (aliases are permitted),
    sorted for deterministic graph identity.  A loader cannot add a module
    after this boundary; each extra is still path/SHA checked by load/bind.
    """
    names = tuple(names)
    require(names[:len(REQUIRED_GRAPH_NAMES)] == REQUIRED_GRAPH_NAMES,
            "graph omits or reorders a required runtime role")
    extras = names[len(REQUIRED_GRAPH_NAMES):]
    require(len(set(names)) == len(names), "graph has duplicate module names")
    require(all(isinstance(name, str) and GRAPH_NAME_RE.fullmatch(name) for name in extras),
            "graph contains a malformed transitive module instance name")
    require(tuple(sorted(extras)) == extras, "transitive graph extras are not deterministically sorted")
    return names


def _replacement_runtime_member(graph: Any) -> object:
    """Return the graph-owned full bridge validator, never the protocol facade."""
    names = {getattr(member, "name", "") for member in getattr(graph, "members", ())}
    # BF16's full bridge validator is the authority even when the graph keeps
    # replacement05 as a retained historical instance.  The BF14 import-only
    # smoke has replacement14 as its current validator.  replacement05 is a
    # last-resort historical graph shape only; it is never preferred over the
    # current protocol member.
    for role in ("replacement05", "replacement22", "replacement14"):
        if role in names:
            return graph.module(role)
    raise FrozenBridge17Error("graph has no current replacement validator")
SHA_RE = set("0123456789abcdef")


class FrozenBridge17Error(ValueError):
    """A stage, graph, sidecar, or stable file binding failed closed."""


def require(condition: object, message: str) -> None:
    if not condition:
        raise FrozenBridge17Error(message)


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _stdlib_module(name: str) -> bool:
    """Recognize interpreter modules without admitting site-packages.

    ``sys.stdlib_module_names`` is unavailable on the Python 3.9 runtime used
    by the release harness, so the fallback checks the resolved module origin
    against ``stdlib`` while explicitly excluding ``purelib``/``platlib``.
    """
    top = name.split(".", 1)[0]
    if top in sys.builtin_module_names or top in {"__future__", "importlib"}:
        return True
    names = getattr(sys, "stdlib_module_names", ())
    if top in names:
        return True
    try:
        origin = importlib.util.find_spec(top).origin
    except (ImportError, AttributeError, ValueError):
        return False
    if origin in {None, "built-in", "frozen"}:
        return True
    try:
        origin_path = Path(origin).resolve()
        stdlib = Path(sysconfig.get_paths()["stdlib"]).resolve()
        purelib = Path(sysconfig.get_paths().get("purelib", "")).resolve()
        platlib = Path(sysconfig.get_paths().get("platlib", "")).resolve()
        return origin_path.is_relative_to(stdlib) and not (
            origin_path.is_relative_to(purelib) or origin_path.is_relative_to(platlib))
    except (OSError, ValueError):
        return False


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def _sha(value: object, label: str = "sha256") -> str:
    require(isinstance(value, str) and len(value) == 64 and set(value) <= SHA_RE, f"{label} is malformed")
    return value


def _relative(value: object, label: str = "path") -> PurePosixPath:
    require(isinstance(value, str) and value and "\x00" not in value and "\\" not in value,
            f"{label} is not a relative path")
    path = PurePosixPath(value)
    require(not path.is_absolute() and path.as_posix() == value and
            all(part not in {"", ".", ".."} for part in path.parts), f"unsafe {label}")
    return path


def _path(root: Path, value: str, label: str = "path") -> Path:
    relative = _relative(value, label)
    current = root.resolve()
    for part in relative.parts:
        current = current / part
        require(not current.is_symlink(), f"symlink in {label}: {value}")
    require(current.is_relative_to(root.resolve()), f"{label} escaped root")
    return current


def _ref(value: object, label: str = "ref") -> dict[str, Any]:
    require(isinstance(value, Mapping) and set(value) <= {"path", "sha256", "rows", "stat"},
            f"{label} has unexpected fields")
    require("path" in value and "sha256" in value, f"{label} needs path and sha256")
    path = value["path"]
    _relative(path, f"{label} path")
    digest = _sha(value["sha256"], f"{label} sha256")
    result: dict[str, Any] = {"path": path, "sha256": digest}
    if "rows" in value:
        require(type(value["rows"]) is int and value["rows"] > 0, f"{label} rows malformed")
        result["rows"] = value["rows"]
    if "stat" in value:
        require(isinstance(value["stat"], Mapping), f"{label} stat malformed")
        result["stat"] = dict(value["stat"])
    return result


def _stat_tuple(path: Path, label: str = "file") -> tuple[int, int, int, int, int]:
    try:
        value = path.lstat()
    except OSError as exc:
        raise FrozenBridge17Error(f"cannot stat {label}") from exc
    require(stat.S_ISREG(value.st_mode) and not path.is_symlink(), f"{label} must be a regular non-symlink file")
    return (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns)


def _stat_dict(value: tuple[int, int, int, int, int]) -> dict[str, int]:
    return dict(zip(("dev", "ino", "size", "mtime_ns", "ctime_ns"), value))


def stable_read(root: Path | str, reference: Mapping[str, Any], label: str = "file") -> tuple[bytes, dict[str, int]]:
    """Read and hash an immutable ref with lstat-before/hash/lstat-after."""
    root = Path(root).resolve()
    ref = _ref(reference, label)
    path = _path(root, ref["path"], f"{label} path")
    before = _stat_tuple(path, label)
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise FrozenBridge17Error(f"cannot read {label}") from exc
    after = _stat_tuple(path, label)
    require(before == after, f"{label} changed while being read")
    require(sha256(raw) == ref["sha256"], f"{label} digest changed")
    return raw, _stat_dict(before)


def stable_metadata(root: Path | str, reference: Mapping[str, Any], label: str = "file") -> dict[str, int]:
    """Check current metadata for a same-stage file without rehashing it."""
    root = Path(root).resolve()
    ref = _ref(reference, label)
    path = _path(root, ref["path"], f"{label} path")
    current = _stat_dict(_stat_tuple(path, label))
    expected = ref.get("stat")
    if expected is not None:
        require(dict(expected) == current, f"{label} metadata changed")
    return current


def _jsonable(value: Any) -> Any:
    if isinstance(value, Path):
        return {"__type__": "path", "value": str(value)}
    if isinstance(value, bytes):
        return {"__type__": "bytes", "value": value.hex()}
    if isinstance(value, Mapping):
        return {str(k): _jsonable(v) for k, v in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    # Opaque runtime objects are represented by type only.  Their authority
    # never comes from this digestable representation; the pinned bridge's
    # lossless in-process object identity is retained separately by the stage.
    # Omitting ``id`` keeps the compact receipt stable across parent/child
    # processes while preventing JSON from becoming a runtime substitute.
    return {"__opaque_type__": type(value).__module__ + ":" + type(value).__qualname__}


def runtime_digest(runtime: object) -> str:
    if isinstance(runtime, ActualRuntimeContext):
        digest = runtime.diagnostic.get("context_digest")
        return _sha(digest, "actual runtime context digest")
    return sha256(canonical_json(_jsonable(runtime)))


@dataclasses.dataclass(frozen=True)
class GraphMember:
    name: str
    canonical_path: str
    source_sha256: str
    module_object: object = dataclasses.field(repr=False, compare=False)
    loader_identity: str

    def public(self) -> dict[str, str]:
        return {"name": self.name, "canonical_path": self.canonical_path,
                "source_sha256": self.source_sha256, "loader_identity": self.loader_identity}

    def binding(self) -> dict[str, str]:
        """Stable cross-process identity; loader identity stays stage-local."""
        return {"name": self.name, "canonical_path": self.canonical_path,
                "source_sha256": self.source_sha256}


class _GraphSpec:
    __slots__ = ("name", "target_role", "loader", "_context")

    def __init__(self, name: str, target_role: str, context: "GraphImportContext") -> None:
        self.name = name
        self.target_role = target_role
        self.loader = _GraphLoader(context, target_role, name)
        self._context = context


class _GraphLoader:
    def __init__(self, context: "GraphImportContext", target_role: str, selector: str) -> None:
        self.context = context
        self.target_role = target_role
        self.selector = selector

    def create_module(self, spec: object) -> object:
        return self.context.module(self.target_role)

    def exec_module(self, module: object) -> None:
        require(module is self.context.module(self.target_role),
                "dynamic loader received a foreign graph object")
        self.context.ensure(self.target_role)
        self.context._restore_dynamic_selector(self.selector, module)


class _GraphImportlibFacade:
    """Module-local importlib view bound to one sealed graph context.

    It is installed into a fresh module's globals before its body executes.
    The real process-global importlib object is never modified.
    """
    def __init__(self, context: "GraphImportContext", caller_role: str) -> None:
        self._context = context
        self._caller_role = caller_role
        self.util = types.SimpleNamespace(
            spec_from_file_location=self._spec_from_file_location,
            module_from_spec=self._module_from_spec,
        )
        self.machinery = types.SimpleNamespace(ModuleSpec=importlib.machinery.ModuleSpec)

    def import_module(self, name: str, package: str | None = None) -> object:
        require(package is None, "relative import_module calls are not reviewed")
        role = self._context.bare_target(self._caller_role, name)
        require(role is not None, f"unregistered graph import_module name: {name}")
        return self._context.ensure(role)

    def _spec_from_file_location(self, selector: str, location: object, *args: object,
                                 **kwargs: object) -> _GraphSpec:
        require(not args and not kwargs, "unreviewed spec_from_file_location options")
        return self._context.dynamic_spec(self._caller_role, selector, location)

    def _module_from_spec(self, spec: object) -> object:
        require(isinstance(spec, _GraphSpec) and spec._context is self._context,
                "foreign graph import spec")
        return self._context.ensure(spec.target_role)


class _GraphModulesProxy(MutableMapping[str, object]):
    """Module-local ``sys.modules`` view; the process registry is immutable."""

    def __init__(self, context: "GraphImportContext") -> None:
        self._context = context

    def __getitem__(self, key: str) -> object:
        if key in self._context._local_modules:
            return self._context._local_modules[key]
        # After the graph is sealed, synthetic registrations are withdrawn
        # from the local staging map.  A graph member may still legitimately
        # introspect its own module through ``sys.modules[__name__]`` during a
        # later scoped loader call; resolve that name back to the already
        # pinned object without recreating a process-global registration.
        role = self._context._role_by_synthetic.get(key)
        if role is not None:
            return self._context.module(role)
        # A private/dynamic selector is graph-local authority.  Falling back
        # to the real registry for a selector would let a pre-existing
        # foreign module satisfy a frozen loader lookup, even though the
        # graph never registered that object.  Treat it as absent (and let
        # the caller's exact route validation fail closed).
        if key in self._context._selector_names:
            raise KeyError(key)
        return sys.modules[key]

    def __setitem__(self, key: str, value: object) -> None:
        require(key in self._context._sys_keys or key in self._context._selector_names,
                f"graph module attempted an unregistered sys.modules write: {key}")
        self._context._local_modules[key] = value

    def __delitem__(self, key: str) -> None:
        if key in self._context._local_modules:
            del self._context._local_modules[key]
            return
        raise KeyError(key)

    def __iter__(self):
        return iter(set(sys.modules) | set(self._context._local_modules) |
                    set(self._context._role_by_synthetic))

    def __len__(self) -> int:
        return len(set(sys.modules) | set(self._context._local_modules) |
                   set(self._context._role_by_synthetic))


class _GraphSysFacade:
    """Proxy ``sys`` with a graph-owned module registry."""

    def __init__(self, context: "GraphImportContext") -> None:
        self.modules = _GraphModulesProxy(context)

    def __getattr__(self, name: str) -> object:
        return getattr(sys, name)


class GraphImportContext:
    """Dependency-aware source loader for the sealed 88-member graph.

    The context owns every shell, route, and synthetic registration.  It is
    intentionally independent of process-global import state.  The source
    graph specification is itself hash-pinned by the reviewed core or, for
    the read-only smoke, by the BF14 design02 artifact.
    """
    def __init__(self, root: Path, refs: Mapping[str, Mapping[str, Any]],
                 spec: Mapping[str, Any], *, host_modules: Mapping[str, object] | None = None,
                 allow_legacy_smoke: bool = False) -> None:
        self.root = root.resolve()
        self.refs = {str(k): dict(v) for k, v in refs.items()}
        self.spec = spec
        # This context is only constructed for a real repository graph.  The
        # legacy switch is intentionally confined to ``fixture_only`` in
        # ``load_graph`` and can never relax the production loader here.
        require(not allow_legacy_smoke,
                "legacy graph context is forbidden outside an explicit fixture")
        self.allow_legacy_smoke = False
        self.ordinary_edges = tuple(spec.get("ordinary_edges") or DEFAULT_ORDINARY_EDGES)
        self.bare_by_role: dict[str, dict[str, str]] = {}
        self.bare_by_name: dict[str, str] = {}
        for row in spec.get("bare_import_route_table", ()):
            require(isinstance(row, Mapping), "bare graph route is not an object")
            name, role = row.get("bare_name"), row.get("target_role")
            path, digest = row.get("target_path"), row.get("target_sha256")
            require(isinstance(name, str) and isinstance(role, str), "bare graph route identity is malformed")
            require(isinstance(path, str) and isinstance(digest, str), "bare graph route ref is malformed")
            require(role in self.refs, f"bare graph route target is not in the sealed graph: {role}")
            require(self.refs[role].get("path") == path and self.refs[role].get("sha256") == digest,
                    f"bare graph route ref differs for {name}")
            require(name not in self.bare_by_name, f"duplicate bare graph route: {name}")
            self.bare_by_name[name] = role
        self.dynamic_by_role: dict[str, list[Mapping[str, Any]]] = {}
        for row in spec.get("dynamic_route_table", ()):
            require(isinstance(row, Mapping), "dynamic graph route is not an object")
            caller_roles = row.get("caller_graph_roles")
            target = row.get("selected_target_role")
            require(isinstance(caller_roles, list) and caller_roles and isinstance(target, str),
                    "dynamic graph route roles are malformed")
            require(target in self.refs, f"dynamic graph route target is not in graph: {target}")
            for caller in caller_roles:
                require(caller in self.refs, f"dynamic graph route caller is not in graph: {caller}")
                self.dynamic_by_role.setdefault(caller, []).append(row)
            caller_path = row.get("caller_path")
            caller_sha = row.get("caller_sha256")
            require(isinstance(caller_path, str) and isinstance(caller_sha, str),
                    "dynamic graph caller ref is malformed")
            require(all(self.refs[caller].get("path") == caller_path and
                        self.refs[caller].get("sha256") == caller_sha
                        for caller in caller_roles),
                    f"dynamic graph caller ref differs for {row.get('route_id')}")
        require(len(spec.get("dynamic_route_table", ())) == 43,
                "complete graph requires exactly 43 resolved dynamic routes")
        require(len(self.bare_by_name) == 22, "complete graph requires exactly 22 bare routes")
        self.modules: dict[str, object] = {}
        self.states: dict[str, str] = {name: "new" for name in self.refs}
        self._context_nonce = secrets.token_hex(8)
        self._synthetic: dict[str, str] = {
            role: f"v092_bifrost17_graph_{self._context_nonce}_{role}" for role in self.refs
        }
        self._role_by_synthetic = {value: key for key, value in self._synthetic.items()}
        self._sys_before: dict[str, object] = {}
        # Keep a complete key snapshot only for detecting imports that escape
        # the sealed graph.  Standard-library imports are explicitly allowed;
        # any new non-stdlib key is a bare/dynamic alias leak and fails closed.
        self._global_sys_before = dict(sys.modules)
        self._selector_before: dict[str, object] = {}
        self._sys_keys = tuple(self._synthetic.values())
        self._selector_names = {
            str(row.get("loader_selector")) for row in spec.get("dynamic_route_table", ())
        }
        # The common private engine computes four finite selectors from the
        # stage root and semantic engine kind.  Register only those exact
        # values in the local sys.modules view; the reviewed template marker
        # remains a specification label and is never accepted as a runtime
        # alias.
        for kind in ("codeql", "joern"):
            token = hashlib.sha256((str(self.root) + kind).encode()).hexdigest()[:12]
            for family in ("runner", "reports"):
                self._selector_names.add(f"_dfb_common_v2_{kind}_{family}_{token}")
        self._local_modules: dict[str, object] = {}
        self._sys_facade = _GraphSysFacade(self)
        # A source that defines dataclasses can be introspected by stdlib code
        # using the real process ``sys.modules`` (dataclasses looks up
        # ``cls.__module__`` there).  Host-owned modules are already normally
        # registered by the caller, so duplicate graph instances for the same
        # source path use that registered name for class metadata without
        # registering their synthetic names globally.  This keeps the
        # module-local registry boundary while preserving stdlib semantics.
        self._host_module_names_by_path: dict[str, str] = {}
        self._closed = False
        self._sealed_once = False
        host_modules = dict(host_modules or {})
        require(set(host_modules) <= set(self.refs), "host graph contains an unknown role")
        for role, module in host_modules.items():
            self._bind_host(role, module)
        self._eager_order = self._derive_execution_order()
        self._build_shells()

    def _bind_host(self, role: str, module: object) -> None:
        require(role in self.refs and hasattr(module, "__file__"), f"host role is malformed: {role}")
        expected = _path(self.root, self.refs[role]["path"], f"host graph {role}").resolve()
        require(Path(str(module.__file__)).resolve() == expected,
                f"host graph role has an unexpected source path: {role}")
        raw, _ = stable_read(self.root, self.refs[role], f"host graph {role}")
        require(sha256(raw) == self.refs[role]["sha256"],
                f"host graph {role} source digest differs")
        self.modules[role] = module
        self.states[role] = "done"
        name = getattr(module, "__name__", None)
        if isinstance(name, str) and name:
            self._host_module_names_by_path[str(expected)] = name

    def _derive_execution_order(self) -> tuple[str, ...]:
        graph = self.spec.get("eager_initialization_graph", {})
        groups = graph.get("provider_first_scc_order", []) if isinstance(graph, Mapping) else []
        order: list[str] = []
        for group in groups:
            require(isinstance(group, list), "eager SCC order is malformed")
            for role in group:
                require(role in self.refs, f"eager SCC references unknown role: {role}")
                require(role not in order, f"eager SCC order repeats role: {role}")
                order.append(role)
        require(set(order) == set(self.refs) and len(order) == len(self.refs),
                "eager SCC order is not an exact partition of the sealed graph")
        return tuple(order)

    def _build_shells(self) -> None:
        for role, ref in self.refs.items():
            if role in self.modules:
                continue
            raw, _ = stable_read(self.root, ref, f"graph {role}")
            path = _path(self.root, ref["path"], f"graph {role} path")
            spec = importlib.machinery.ModuleSpec(
                self._synthetic[role], _GraphLoader(self, role, self._synthetic[role]), origin=str(path)
            )
            module = types.ModuleType(spec.name)
            module.__file__ = str(path)
            module.__name__ = self._host_module_names_by_path.get(str(path), spec.name)
            module.__loader__ = spec.loader
            module.__package__ = ""
            module.__spec__ = spec
            module.__graph_role__ = role
            self.modules[role] = module
            self._sys_before.setdefault(spec.name, sys.modules.get(spec.name, _MISSING))
            self._local_modules[spec.name] = module
            require(sha256(raw) == ref["sha256"], f"graph {role} source changed while shell was built")

    def module(self, role: str) -> object:
        require(role in self.modules, f"graph role is not registered: {role}")
        return self.modules[role]

    def bare_target(self, caller_role: str, name: str) -> str | None:
        target = self.bare_by_name.get(name.split(".", 1)[0])
        if target is None:
            return None
        # The route table is graph-wide, but a caller must also have an exact
        # ordinary edge to this bare name.  This prevents a valid target from
        # becoming a global alias for an unrelated caller.
        rows = [row for row in self.ordinary_edges
                if row.get("caller_role") == caller_role and row.get("bare_name") == name]
        require(rows, f"bare import caller is not registered: {caller_role}:{name}")
        require(all(row.get("target_role") == target for row in rows),
                f"bare import target differs for {caller_role}:{name}")
        return target

    def _stdlib(self, name: str) -> bool:
        return _stdlib_module(name)

    def import_for(self, caller_role: str, module_globals: Mapping[str, Any], name: str,
                   globals_arg: object = None, locals_arg: object = None,
                   fromlist: object = (), level: int = 0) -> object:
        require(level == 0, f"relative graph import is not reviewed: {caller_role}:{name}")
        if name == "sys":
            return self._sys_facade
        if name == "importlib" or name.startswith("importlib."):
            return self.facade(caller_role)
        target = self.bare_target(caller_role, name)
        if target is not None:
            return self.ensure(target)
        require(self._stdlib(name), f"unknown non-stdlib local import: {caller_role}:{name}")
        return builtins.__import__(name, globals_arg, locals_arg, fromlist, level)

    def facade(self, caller_role: str) -> _GraphImportlibFacade:
        return _GraphImportlibFacade(self, caller_role)

    @contextlib.contextmanager
    def private_engine_scope(self):
        """Bound the common loader's temporary private-engine mutations.

        ``swift_common_population_v2.private_engine`` uses the graph's
        importlib facade to load four concrete runner/report targets.  The
        frozen common module then patches those target objects and retains
        them in its process-local cache.  A provider scope may safely reuse
        that cache, but its aliases, cache object, and target attributes must
        not become authority for a later stage or graph.  Snapshot the exact
        graph-owned objects on entry and restore them on every exit path;
        nested scopes therefore retain their outer cache while still
        restoring the outer scope's state when they leave.
        """
        common_role = "local_012_swift_common_population_v2"
        target_roles = (
            "nested_040_dfb_common_v2_codeql_runner__root_token",
            "nested_041_dfb_common_v2_codeql_reports__root_token",
            "nested_042_dfb_common_v2_joern_runner__root_token",
            "nested_043_dfb_common_v2_joern_reports__root_token",
        )
        target_fields = ("__builtins__", "load_population", "export", "verify_activation")
        common = self.module(common_role)
        common_globals = getattr(common, "__dict__", None)
        require(isinstance(common_globals, dict),
                "private-engine common module has no graph-owned globals")
        cache = common_globals.get("_PRIVATE_ENGINES", _MISSING)
        require(isinstance(cache, dict),
                "private-engine common cache is not an exact mapping")
        cache_contents = dict(cache)
        local_modules = dict(self._local_modules)
        selector_before = dict(self._selector_before)
        selector_names = set(self._selector_names)
        sys_before = dict(self._sys_before)
        target_snapshots: list[tuple[object, dict[str, object]]] = []
        for role in target_roles:
            target = self.module(role)
            target_globals = getattr(target, "__dict__", None)
            require(isinstance(target_globals, dict),
                    f"private-engine target has no graph-owned globals: {role}")
            target_snapshots.append((target, {
                field: target_globals.get(field, _MISSING)
                for field in target_fields
            }))

        try:
            yield common
        finally:
            # Restore target attributes before the cache so no restored cache
            # entry can observe a target patched by an earlier scope.
            for target, snapshot in target_snapshots:
                target_globals = target.__dict__
                for field, value in snapshot.items():
                    if value is _MISSING:
                        target_globals.pop(field, None)
                    else:
                        target_globals[field] = value

            # Restore the original cache object itself as well as its exact
            # contents.  The common source currently mutates this mapping,
            # but restoring identity also closes over future reassignment.
            current_cache = common_globals.get("_PRIVATE_ENGINES", _MISSING)
            if current_cache is not cache and isinstance(current_cache, dict):
                current_cache.clear()
            common_globals["_PRIVATE_ENGINES"] = cache
            cache.clear()
            cache.update(cache_contents)

            # A private loader may register concrete selectors or leave one
            # registered when its body raises.  Restore every graph-local
            # registration and selector witness exactly as found.
            self._local_modules.clear()
            self._local_modules.update(local_modules)
            self._selector_before.clear()
            self._selector_before.update(selector_before)
            self._selector_names.clear()
            self._selector_names.update(selector_names)
            self._sys_before.clear()
            self._sys_before.update(sys_before)

    def _caller_function(self, caller_role: str) -> str | None:
        functions = self._caller_functions(caller_role)
        return functions[0] if functions else None

    def _caller_functions(self, caller_role: str) -> tuple[str, ...]:
        frame = inspect.currentframe()
        found: list[str] = []
        try:
            frame = frame.f_back if frame is not None else None
            while frame is not None:
                if frame.f_globals.get("__graph_role__") == caller_role:
                    found.append(frame.f_code.co_name)
                frame = frame.f_back
            return tuple(found)
        finally:
            del frame

    def _private_engine_frame(self, caller_role: str, kind: str) -> object:
        """Return the real ``private_engine`` owner frame for a computed route.

        The four common-engine selectors are computed inside the real
        ``swift_common_population_v2.private_engine`` body.  A function with
        the same display name, or a generated frame carrying the same graph
        role, is not sufficient authority: the frame must belong to the
        graph-owned module, have the exact source path/digest, and be entered
        through that module's ``_load_private_module`` call.  This keeps the
        finite selector expansion bound to the actual root and engine kind.
        """
        require(kind in {"codeql", "joern"}, "private-engine kind is not reviewed")
        owner = self.module(caller_role)
        owner_globals = getattr(owner, "__dict__", None)
        require(isinstance(owner_globals, dict),
                "private-engine caller has no graph-owned globals")
        expected_ref = self.refs[caller_role]
        expected_path = _path(self.root, expected_ref["path"],
                              "private-engine owner path").resolve()
        raw, _ = stable_read(self.root, expected_ref, "private-engine owner")
        require(sha256(raw) == expected_ref["sha256"],
                "private-engine owner source digest changed")

        current = inspect.currentframe()
        owner_frame = None
        loader_frame = None
        try:
            frame = current.f_back if current is not None else None
            while frame is not None:
                if (frame.f_code.co_name == "private_engine" and
                        frame.f_globals is owner_globals):
                    candidate_root = frame.f_locals.get("root")
                    candidate_kind = frame.f_locals.get("kind")
                    if (candidate_kind == kind and
                            isinstance(candidate_root, (str, Path)) and
                            Path(candidate_root).resolve() == self.root):
                        owner_frame = frame
                if (frame.f_code.co_name == "_load_private_module" and
                        frame.f_globals is owner_globals):
                    loader_frame = frame
                frame = frame.f_back
            require(owner_frame is not None,
                    "private-engine route is not owned by the exact graph frame")
            require(loader_frame is not None and loader_frame.f_back is owner_frame,
                    "private-engine call chain is not private_engine->_load_private_module")
            require(Path(owner_frame.f_code.co_filename).resolve() == expected_path,
                    "private-engine frame path differs from the sealed owner")
            require(sha256(Path(owner_frame.f_code.co_filename).read_bytes()) ==
                    expected_ref["sha256"],
                    "private-engine frame source differs from the sealed owner")
            function = owner_globals.get("private_engine")
            require(callable(function) and getattr(function, "__globals__", None) is owner_globals and
                    getattr(function, "__code__", None) is owner_frame.f_code,
                    "private-engine function globals/code are not graph-owned")
            require(owner_globals.get("__graph_role__") == caller_role,
                    "private-engine graph owner role differs")
            return owner_frame
        finally:
            del current

    def _computed_private_engine_route(self, row: Mapping[str, Any], selector: str,
                                       caller_role: str) -> bool:
        """Validate one of the four finite root-token selector families."""
        template = row.get("loader_selector")
        if not (isinstance(template, str) and template.endswith("_<root-token>")):
            return False
        require(row.get("caller_function") == "private_engine" and
                row.get("phase") == "function_late",
                f"computed private-engine route metadata differs: {row.get('route_id')}")
        require(template.count("<root-token>") == 1,
                f"computed private-engine selector must contain exactly one root token: {template}")
        prefix = template[: -len("_<root-token>")]
        parts = prefix.split("_")
        require(len(parts) >= 2 and parts[-2] in {"codeql", "joern"} and
                parts[-1] in {"runner", "reports"},
                f"computed private-engine selector family is not finite: {template}")
        kind, family = parts[-2], parts[-1]
        token = hashlib.sha256((str(self.root) + kind).encode()).hexdigest()[:12]
        expected_selector = template.replace("<root-token>", token)
        if selector != expected_selector:
            return False
        expected_targets = {
            ("codeql", "runner"): "nested_040_dfb_common_v2_codeql_runner__root_token",
            ("codeql", "reports"): "nested_041_dfb_common_v2_codeql_reports__root_token",
            ("joern", "runner"): "nested_042_dfb_common_v2_joern_runner__root_token",
            ("joern", "reports"): "nested_043_dfb_common_v2_joern_reports__root_token",
        }
        require(row.get("selected_target_role") == expected_targets[(kind, family)],
                f"computed private-engine target role differs: {row.get('route_id')}")
        require(row.get("caller_graph_roles") == [caller_role],
                f"computed private-engine caller role differs: {row.get('route_id')}")
        self._private_engine_frame(caller_role, kind)
        return True

    def dynamic_spec(self, caller_role: str, selector: str, location: object) -> _GraphSpec:
        try:
            relative = Path(location).resolve().relative_to(self.root).as_posix()
        except (OSError, ValueError) as exc:
            raise FrozenBridge17Error("dynamic loader escaped the sealed graph root") from exc
        functions = self._caller_functions(caller_role)
        function = functions[0] if functions else None
        rows = []
        for row in self.dynamic_by_role.get(caller_role, ()):
            # A root-token row is a template, never a literal selector.  It
            # must always pass the computed-family/owner-frame validation,
            # even when a caller supplies the template text verbatim.  The
            # literal therefore fails closed instead of bypassing the
            # private_engine provenance check.
            template = row.get("loader_selector")
            if isinstance(template, str) and template.endswith("_<root-token>"):
                if not self._computed_private_engine_route(row, selector, caller_role):
                    continue
            elif template != selector:
                continue
            if row.get("target_path") != relative:
                continue
            route_function = str(row.get("caller_function"))
            if function is None:
                raise FrozenBridge17Error(
                    "dynamic route caller frame is unavailable in the sealed graph")
            elif route_function == "private_engine":
                # The computed-family helper above validates the exact owner
                # frame, root token, engine kind, and call chain.  A generated
                # same-name frame must never satisfy this branch.
                exact_function = True
            else:
                exact_function = (function == route_function or
                                  route_function.endswith("/" + function) or
                                  (route_function == "<module>" and "<module>" in functions) or
                                  (route_function.startswith("<module>/") and
                                   route_function.rsplit("/", 1)[-1] in functions and
                                   "<module>" in functions))
                if not exact_function:
                    continue
                allowed_phases = ({"module_body", "import_time"} if
                                  (function == "<module>" or route_function == "<module>" or
                                   route_function.startswith("<module>/"))
                                  else {"function_late"})
                require(row.get("phase") in allowed_phases,
                        f"dynamic route phase differs for {row.get('route_id')}")
            rows.append(row)
        require(len(rows) == 1,
                f"dynamic route is not exact for {caller_role}:{selector}:{relative}:{function}")
        row = rows[0]
        target = row["selected_target_role"]
        require(self.refs[target]["path"] == row["target_path"] and
                self.refs[target]["sha256"] == row["target_sha256"],
                f"dynamic target binding changed: {row['route_id']}")
        # The graph-local proxy is intentionally authoritative for the
        # selector during loading.  A foreign process-global selector can be
        # inserted after graph construction, though, so check the live
        # registry immediately before admitting the route; the construction
        # snapshot alone cannot detect that late insertion.
        require(sys.modules.get(selector, _MISSING) is _MISSING,
                f"dynamic selector already exists in process-global registry: {selector}")
        self._selector_before.setdefault(selector, self._global_sys_before.get(selector, _MISSING))
        return _GraphSpec(selector, target, self)

    def _restore_dynamic_selector(self, selector: str, module: object) -> None:
        """Reject and remove a loader's process-global selector registration.

        Frozen modules sometimes assign ``sys.modules[spec.name]`` during
        ``exec_module``.  That is a loader-local implementation detail; it is
        never a permitted graph alias.  A pre-existing selector is rejected
        unless it is the exact current target, and all temporary bindings are
        restored before the next route.
        """
        old = self._selector_before.get(selector, _MISSING)
        current = self._local_modules.get(selector, _MISSING)
        require(current is _MISSING or current is module,
                f"dynamic loader registered a foreign selector: {selector}")
        live = sys.modules.get(selector, _MISSING)
        require(live is _MISSING or live is module,
                f"dynamic selector acquired a foreign process-global binding: {selector}")
        if old is not _MISSING:
            require(old is module,
                    f"dynamic selector already existed outside this graph: {selector}")
        self._local_modules.pop(selector, None)

    def _assert_sys_module_boundary(self) -> None:
        current = set(sys.modules)
        before = set(self._global_sys_before)
        added = current - before
        removed = before - current
        require(not removed,
                "graph import removed a pre-existing process-global sys.modules entry")
        # A graph source may import an as-yet-unloaded standard-library module;
        # that import is an ordinary interpreter cache effect.  Graph-owned
        # synthetic names, loader selectors, and every non-stdlib name remain
        # forbidden in the real registry.  Existing bindings must also retain
        # object identity, so a graph cannot replace a process-global module.
        require(all(_stdlib_module(name) for name in added),
                "graph import added a non-stdlib process-global sys.modules entry")
        require(all(sys.modules[name] is self._global_sys_before[name] for name in before),
                "graph import replaced a process-global sys.modules entry")
        allowed = set(self._sys_keys) | self._selector_names
        require(set(self._local_modules) <= allowed,
                "graph import escaped into an unregistered local sys.modules key")

    def _install_builtins(self, role: str, module: object) -> None:
        original = getattr(module, "__builtins__", builtins.__dict__)
        mapping = dict(original if isinstance(original, Mapping) else vars(builtins))
        mapping["__import__"] = lambda name, globals=None, locals=None, fromlist=(), level=0: self.import_for(
            role, getattr(module, "__dict__", {}), name, globals, locals, fromlist, level)
        module.__builtins__ = mapping
        module.importlib = self.facade(role)

    def ensure(self, role: str) -> object:
        require(not self._closed, "graph import context is closed")
        require(role in self.modules, f"graph role is not registered: {role}")
        state = self.states[role]
        if state == "done":
            return self.modules[role]
        if state == "loading":
            return self.modules[role]
        require(state == "new", f"graph role cannot be loaded from state {state}: {role}")
        self.states[role] = "loading"
        module = self.modules[role]
        self._install_builtins(role, module)
        try:
            path = _path(self.root, self.refs[role]["path"], f"graph {role} path")
            before, _ = stable_read(self.root, self.refs[role], f"graph {role} before import")
            code = compile(before, str(path), "exec", dont_inherit=True)
            exec(code, module.__dict__, module.__dict__)
            after, _ = stable_read(self.root, self.refs[role], f"graph {role} after import")
            require(sha256(before) == sha256(after) == self.refs[role]["sha256"],
                    f"graph member changed during import: {role}")
            self._assert_sys_module_boundary()
            self.states[role] = "done"
            return module
        except Exception:
            self.states[role] = "failed"
            raise

    def execute_all(self) -> None:
        for role in self._eager_order:
            self.ensure(role)
        require(all(value == "done" for value in self.states.values()),
                "graph contains a role that was not import-validated")

    def seal(self) -> None:
        require(not self._closed, "graph import context already closed")
        if self._sealed_once:
            self._assert_sys_module_boundary()
            for selector, old in self._selector_before.items():
                require(self._local_modules.get(selector, _MISSING) is old,
                        f"dynamic selector was registered after graph seal: {selector}")
            for name, old in self._sys_before.items():
                require(self._local_modules.get(name, _MISSING) is old,
                        f"synthetic graph binding was registered after graph seal: {name}")
            require(not self._local_modules,
                    "local graph module bindings were registered after graph seal")
            return
        self.execute_all()
        require(len(self.modules) == len(self.refs), "graph member count changed")
        self._assert_sys_module_boundary()
        for selector, old in self._selector_before.items():
            current = self._local_modules.get(selector, _MISSING)
            require(current is old,
                    f"dynamic selector remained registered after graph seal: {selector}")
        # Keep the sealed context usable for registered late-loader calls; all
        # targets are initialized, and their synthetic names remain absent.
        for name, old in self._sys_before.items():
            require(self._local_modules.get(name, _MISSING) is self.modules[self._role_by_synthetic[name]],
                    "synthetic sys.modules binding changed during graph execution")
            require(sys.modules.get(name, _MISSING) is old,
                    "process-global synthetic module binding changed")
        self._local_modules.clear()
        self._sealed_once = True

    def close_on_error(self) -> None:
        if self._closed:
            return
        self._assert_sys_module_boundary()
        self._local_modules.clear()
        self._closed = True


_MISSING = object()


class PinnedBridgeGraph:
    """Complete stage-local module graph; members and import context are immutable."""
    __slots__ = ("_members", "_by_name", "graph_sha256", "fixture_only", "_sealed", "_import_context")

    def __init__(self, members: Sequence[GraphMember], *, fixture_only: bool = False,
                 import_context: GraphImportContext | None = None,
                 allow_legacy_smoke: bool = False) -> None:
        canonical_names = tuple(item.name for item in members)
        if not allow_legacy_smoke:
            _validate_graph_names(canonical_names)
        else:
            require(len(set(canonical_names)) == len(canonical_names),
                    "legacy smoke graph has duplicate roles")
        names = [item.name for item in members]
        require(len(set(names)) == len(names), "graph has duplicate module names")
        self._members = tuple(members)
        self._by_name = {item.name: item for item in members}
        self.graph_sha256 = sha256(canonical_json([item.binding() for item in members]))
        self.fixture_only = fixture_only
        self._import_context = import_context
        self._sealed = True

    @property
    def members(self) -> tuple[GraphMember, ...]:
        return self._members

    @property
    def import_context(self) -> GraphImportContext | None:
        return self._import_context

    def module(self, name: str) -> object:
        require(name in self._by_name, f"graph member is not registered: {name}")
        return self._by_name[name].module_object

    def assert_member(self, name: str, module: object) -> None:
        expected = self._by_name.get(name)
        require(expected is not None and expected.module_object is module,
                f"foreign or reloaded graph member: {name}")

    def assert_complete(self, modules: Mapping[str, object]) -> None:
        require(tuple(modules) in (REQUIRED_GRAPH_NAMES, tuple(self._by_name)),
                "graph consumer supplied incomplete module set")
        for name in modules:
            self.assert_member(name, modules[name])

    def __setattr__(self, name: str, value: object) -> None:
        if getattr(self, "_sealed", False):
            raise FrozenBridge17Error("pinned graph is immutable")
        object.__setattr__(self, name, value)

    def __getstate__(self) -> None:
        raise FrozenBridge17Error("pinned graph cannot be serialized")


_ROLE_RENAMES = {
    "bridge09": "bridge17", "replacement14": "replacement22",
    "protocol14": "protocol22", "admission14": "admission22",
    "supervisor14": "supervisor22", "runtime_loaders14": "runtime_loaders22",
    "stage_runtime01": "stage_runtime09", "host_bridge09": "host_bridge17",
    "host_protocol14": "host_protocol22", "host_admission14": "host_admission22",
    "host_supervisor14": "host_supervisor22",
}
# Roles which do not occur as a route endpoint are still part of the sealed
# predecessor graph.  Keep their reviewed path/SHA bindings in the source so
# an arbitrary 88-member mapping cannot be smuggled in through a route table.
_DEFAULT_TEMPLATE_ONLY_REFS = {
    "admission14": {"path": "reports/releases/v0.9.2/acquisition/bifrost-v0140-admission-14.py", "sha256": "d9ee7312111e23df9d69d1a99f28717968990579f980b2eed810eafef27702bb"},
    "bridge09": {"path": "reports/releases/v0.9.2/acquisition/bifrost-v0140-frozen-bridge-09.py", "sha256": "16747e65045a0e19aecf37137e96609ba0a7da1fba2b2b398228240b03cc2611"},
    "host_admission14": {"path": "reports/releases/v0.9.2/acquisition/bifrost-v0140-admission-14.py", "sha256": "d9ee7312111e23df9d69d1a99f28717968990579f980b2eed810eafef27702bb"},
    "host_bridge09": {"path": "reports/releases/v0.9.2/acquisition/bifrost-v0140-frozen-bridge-09.py", "sha256": "16747e65045a0e19aecf37137e96609ba0a7da1fba2b2b398228240b03cc2611"},
    "host_protocol14": {"path": "reports/releases/v0.9.2/acquisition/bifrost-v0140-replacement-14.py", "sha256": "72661b1a8c7c64ae6ae7384cf976ab42632db2320874c9af9001a48b7d540f6a"},
    "incoming_nested_resource_recovery": {"path": "scripts/v092_resource_recovery.py", "sha256": "c0dc2ef56cd1cb20cb0d96b156438e2ee876081e85c0f8ff43ca4afb3091830d"},
    "incoming_nested_scoped_recovery": {"path": "scripts/v092_scoped_recovery.py", "sha256": "6f8b025aae344709e1ecc9722db8943877e6f08851e423f9ab735d8d7d311c0d"},
    "local_010_run_joern_swift_case": {"path": "scripts/run-joern-swift-case.py", "sha256": "1a033f1c563003e91fe43fb4c4612d67539c9aad420e351d7a45782da7353516"},
    "nested_008_codeql_pending_disk_guard": {"path": "scripts/v092_disk_guard.py", "sha256": "fa4201b0aa4ae73273c4d6ba9f2dbb4315e6fb9d52c7469c8be3d46f0b570e21"},
    "nested_025_v092_disk_guard_runtime": {"path": "scripts/v092_disk_guard.py", "sha256": "fa4201b0aa4ae73273c4d6ba9f2dbb4315e6fb9d52c7469c8be3d46f0b570e21"},
    "nested_026_v092_replacement09_supervisor_terminal_disk_guard": {"path": "scripts/v092_disk_guard.py", "sha256": "fa4201b0aa4ae73273c4d6ba9f2dbb4315e6fb9d52c7469c8be3d46f0b570e21"},
    "policy_runtime": {"path": "reports/releases/v0.9.2/acquisition/bifrost-v0140-replacement-14.py", "sha256": "72661b1a8c7c64ae6ae7384cf976ab42632db2320874c9af9001a48b7d540f6a"},
    "policy_source": {"path": "reports/releases/v0.9.2/acquisition/bifrost-v0140-replacement-14.py", "sha256": "72661b1a8c7c64ae6ae7384cf976ab42632db2320874c9af9001a48b7d540f6a"},
    "protocol14": {"path": "reports/releases/v0.9.2/acquisition/bifrost-v0140-replacement-14.py", "sha256": "72661b1a8c7c64ae6ae7384cf976ab42632db2320874c9af9001a48b7d540f6a"},
    "replacement14": {"path": "reports/releases/v0.9.2/acquisition/bifrost-v0140-replacement-14.py", "sha256": "72661b1a8c7c64ae6ae7384cf976ab42632db2320874c9af9001a48b7d540f6a"},
    "runtime_loaders14": {"path": "reports/releases/v0.9.2/acquisition/bifrost-v0140-runtime-loaders-14.py", "sha256": "056ae0392ef5d4fbdb15251cbd7f9f8c184758ca879061af9aea1a55cfe28fa3"},
    "stage_runtime01": {"path": "reports/releases/v0.9.2/acquisition/bifrost-v0140-stage-runtime-01.py", "sha256": "363be2b30226b6f94262f5f2b870a4b9286e3a4e99a981312867bf3497357587"},
    "supervisor14": {"path": "reports/releases/v0.9.2/acquisition/bifrost-v0140-supervisor-14.py", "sha256": "acb8fed0b9fdffd7ee866b0b8bb107b6fec067469535a4c0666bd89ef70d5811"},
}

_CHANGED_GRAPH_ROLES = set(_ROLE_RENAMES.values()) | {"policy_source", "policy_runtime"}
_SUCCESSOR_GRAPH_PATHS = {
    "bridge17": "reports/releases/v0.9.2/acquisition/bifrost-v0140-frozen-bridge-17.py",
    "host_bridge17": "reports/releases/v0.9.2/acquisition/bifrost-v0140-frozen-bridge-17.py",
    "replacement22": "reports/releases/v0.9.2/acquisition/bifrost-v0140-replacement-22.py",
    "protocol22": "reports/releases/v0.9.2/acquisition/bifrost-v0140-replacement-22.py",
    "host_protocol22": "reports/releases/v0.9.2/acquisition/bifrost-v0140-replacement-22.py",
    "policy_source": "reports/releases/v0.9.2/acquisition/bifrost-v0140-replacement-22.py",
    "policy_runtime": "reports/releases/v0.9.2/acquisition/bifrost-v0140-replacement-22.py",
    "admission22": "reports/releases/v0.9.2/acquisition/bifrost-v0140-admission-22.py",
    "host_admission22": "reports/releases/v0.9.2/acquisition/bifrost-v0140-admission-22.py",
    "supervisor22": "reports/releases/v0.9.2/acquisition/bifrost-v0140-supervisor-22.py",
    "host_supervisor22": "reports/releases/v0.9.2/acquisition/bifrost-v0140-supervisor-22.py",
    "runtime_loaders22": "reports/releases/v0.9.2/acquisition/bifrost-v0140-runtime-loaders-22.py",
    "stage_runtime09": "reports/releases/v0.9.2/acquisition/bifrost-v0140-stage-runtime-09.py",
}


def _map_graph_role(role: str, rename: Mapping[str, str]) -> str:
    return rename.get(role, role)


def _default_template_refs() -> dict[str, dict[str, str]]:
    refs = {name: dict(value) for name, value in _DEFAULT_TEMPLATE_ONLY_REFS.items()}
    for row in DEFAULT_GRAPH_SPEC["bare_import_route_table"]:
        refs.setdefault(row["target_role"], {
            "path": row["target_path"], "sha256": row["target_sha256"]})
    for row in DEFAULT_GRAPH_SPEC["dynamic_route_table"]:
        refs.setdefault(row["selected_target_role"], {
            "path": row["target_path"], "sha256": row["target_sha256"]})
        for role in row["caller_graph_roles"]:
            refs.setdefault(role, {
                "path": row["caller_path"], "sha256": row["caller_sha256"]})
    require(set(refs) == set(DEFAULT_EAGER_ORDER),
            "embedded graph template does not cover the complete role roster")
    return refs


def _adapt_default_graph_spec(refs: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    """Adapt the reviewed BF14 route topology to the fixed BF15 role names.

    The topology, route IDs, phases, and SCC order are immutable reviewed
    evidence.  Only the explicit seven successor role labels and their
    path/SHA bindings may change; any missing/extra role remains a hard error.
    """
    value = json.loads(json.dumps(DEFAULT_GRAPH_SPEC))
    successor = {"bridge17", "replacement22", "protocol22", "admission22", "supervisor22"}
    use_successor = successor <= set(refs) and "bridge09" not in refs
    rename = _ROLE_RENAMES if use_successor else {}
    old_names = set(DEFAULT_EAGER_ORDER)
    mapped_names = {_map_graph_role(role, rename) for role in old_names}
    require(mapped_names == set(refs),
            "runtime graph roles differ from the reviewed fixed BF15 topology")
    template_refs = _default_template_refs()
    changed_roles = _CHANGED_GRAPH_ROLES if use_successor else set()
    for old_role in DEFAULT_EAGER_ORDER:
        mapped_role = _map_graph_role(old_role, rename)
        if mapped_role in changed_roles:
            require(refs[mapped_role].get("path") == _SUCCESSOR_GRAPH_PATHS[mapped_role],
                    f"successor graph member path is not canonical: {mapped_role}")
            continue
        expected = template_refs[old_role]
        require(refs[mapped_role].get("path") == expected["path"] and
                refs[mapped_role].get("sha256") == expected["sha256"],
                f"unchanged graph member was rebound: {mapped_role}")

    def mapped_ref(role: str) -> Mapping[str, Any]:
        mapped = _map_graph_role(role, rename)
        require(mapped in refs, f"graph route role is not bound by core: {mapped}")
        return refs[mapped]

    bare = []
    for row in value["bare_import_route_table"]:
        target = _map_graph_role(row["target_role"], rename)
        ref = mapped_ref(row["target_role"])
        row.update(target_role=target, target_path=ref["path"], target_sha256=ref["sha256"])
        bare.append(row)
    value["bare_import_route_table"] = bare

    def caller_binding(row: Mapping[str, Any]) -> tuple[str, str]:
        roles = [_map_graph_role(role, rename) for role in row["caller_graph_roles"]]
        require(roles and all(role in refs for role in roles), "dynamic caller role is not core-bound")
        refs_for_roles = [refs[role] for role in roles]
        require(all(ref["path"] == refs_for_roles[0]["path"] and
                    ref["sha256"] == refs_for_roles[0]["sha256"] for ref in refs_for_roles),
                f"duplicate dynamic caller roles disagree: {row['route_id']}")
        return refs_for_roles[0]["path"], refs_for_roles[0]["sha256"]

    dynamic = []
    for row in value["dynamic_route_table"]:
        callers = [_map_graph_role(role, rename) for role in row["caller_graph_roles"]]
        require(callers and all(role in refs for role in callers),
                f"dynamic caller role is not core-bound: {row['route_id']}")
        target_name = _map_graph_role(row["selected_target_role"], rename)
        target = mapped_ref(row["selected_target_role"])
        caller_path, caller_sha = caller_binding(row)
        row.update(caller_graph_roles=callers, caller_path=caller_path,
                   caller_sha256=caller_sha, selected_target_role=target_name,
                   target_path=target["path"], target_sha256=target["sha256"],
                   target_role_candidates=[_map_graph_role(role, rename)
                                           for role in row.get("target_role_candidates", [])])
        dynamic.append(row)
    value["dynamic_route_table"] = dynamic

    eager = value["eager_initialization_graph"]
    eager["provider_first_scc_order"] = [
        [_map_graph_role(role, rename) for role in group]
        for group in eager["provider_first_scc_order"]]
    eager["sccs"] = [[_map_graph_role(role, rename) for role in group]
                     for group in eager["sccs"]]
    value["ordinary_edges"] = [
        {**row, "caller_role": _map_graph_role(row["caller_role"], rename),
         "target_role": _map_graph_role(row["target_role"], rename)}
        for row in value["ordinary_edges"]]
    union = value["union_graph"]
    union["provider_first_scc_order"] = [
        [_map_graph_role(role, rename) for role in group]
        for group in union["provider_first_scc_order"]]
    union["sccs"] = [[_map_graph_role(role, rename) for role in group]
                     for group in union["sccs"]]
    return value


def _read_graph_spec(root: Path, graph_spec_ref: Mapping[str, Any] | None,
                     refs: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    if graph_spec_ref is None:
        return _adapt_default_graph_spec(refs)
    raw, _ = stable_read(root, graph_spec_ref, "graph import specification")
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise FrozenBridge17Error("graph import specification is not JSON") from exc
    require(isinstance(value, Mapping), "graph import specification is not an object")
    require(len(value.get("bare_import_route_table", ())) == 22 and
            len(value.get("dynamic_route_table", ())) == 43,
            "graph import specification is incomplete")
    candidate = dict(value)
    expected = _adapt_default_graph_spec(refs)
    structural_keys = ("bare_import_route_table", "dynamic_route_table",
                       "ordinary_edges", "eager_initialization_graph", "union_graph")
    for key in structural_keys:
        require(canonical_json(candidate.get(key)) == canonical_json(expected.get(key)),
                f"graph import topology differs from the embedded reviewed route template: {key}")
    return candidate


def _load_one(root: Path, name: str, ref: Mapping[str, Any], namespace: str) -> object:
    # A single-role load cannot prove the reviewed route/SCC closure and is
    # therefore never a production API. Callers must use ``load_graph`` so
    # all members and their exact import routes are bound together.
    raise FrozenBridge17Error(
        f"single-role graph loading is forbidden ({namespace}:{name}); use load_graph"
    )


def load_graph(root: Path | str, refs: Mapping[str, Mapping[str, Any]], *,
               fixture_modules: Mapping[str, object] | None = None,
               fixture_only: bool = False,
               graph_spec_ref: Mapping[str, Any] | None = None,
               allow_legacy_smoke: bool = False,
               host_modules: Mapping[str, object] | None = None) -> PinnedBridgeGraph:
    """Load the complete exact graph through a dependency-aware context."""
    root = Path(root).resolve()
    graph_names = tuple(refs)
    # The historical escape hatch is fixture-only.  A production/repository
    # graph must always use the current BF15 roster and the embedded route
    # template; accepting old names at the real root would bypass the sealed
    # source/SCC validation.  Fixture callers may still exercise small legacy
    # shapes under a temporary directory without touching process state.
    if allow_legacy_smoke:
        require(fixture_only,
                "legacy graph names are allowed only by an explicit temporary fixture")
    if not fixture_only:
        _validate_graph_names(graph_names)
    else:
        require(len(set(graph_names)) == len(graph_names),
                "fixture graph has duplicate roles")
    if fixture_only:
        require(fixture_modules is not None, "fixture_only requires fixture modules")
        require(root != ROOT and any(root == p or p in root.parents
                                     for p in (Path(tempfile.gettempdir()).resolve(), Path("/private/var/folders").resolve())),
                "fixture graph must be under a temporary root")
        require(tuple(fixture_modules) == graph_names, "fixture graph is incomplete")
        members = tuple(GraphMember(name, refs[name]["path"], refs[name]["sha256"], fixture_modules[name],
                                    f"{type(fixture_modules[name]).__module__}:{type(fixture_modules[name]).__qualname__}:{id(fixture_modules[name])}")
                        for name in graph_names)
        return PinnedBridgeGraph(members, fixture_only=True,
                                 allow_legacy_smoke=allow_legacy_smoke)
    spec = _read_graph_spec(root, graph_spec_ref, refs)
    context = GraphImportContext(root, refs, spec, host_modules=host_modules, allow_legacy_smoke=allow_legacy_smoke)
    try:
        context.execute_all()
        members = tuple(GraphMember(name, refs[name]["path"], refs[name]["sha256"], context.module(name),
                                    f"{type(context.module(name)).__module__}:{type(context.module(name)).__qualname__}:{id(context.module(name))}")
                        for name in graph_names)
        graph = PinnedBridgeGraph(members, fixture_only=False, import_context=context,
                                  allow_legacy_smoke=allow_legacy_smoke)
        context.seal()
        return graph
    except Exception:
        context.close_on_error()
        raise


def bind_graph(root: Path | str, refs: Mapping[str, Mapping[str, Any]],
               host_modules: Mapping[str, object], *, graph_spec_ref: Mapping[str, Any] | None = None) -> PinnedBridgeGraph:
    """Bind host modules and load every remaining member in one exact context."""
    root = Path(root).resolve()
    graph_names = tuple(refs)
    _validate_graph_names(graph_names)
    require(set(host_modules) <= set(graph_names) and host_modules,
            "host graph contains an unknown or empty module set")
    for name, module in host_modules.items():
        require(hasattr(module, "__file__"), f"host graph member {name} has no module file")
        require(Path(str(module.__file__)).resolve() == _path(root, refs[name]["path"], f"graph {name} path").resolve(),
                f"host graph member {name} is loaded from an unexpected path")
    return load_graph(root, refs, host_modules=host_modules, graph_spec_ref=graph_spec_ref)


def prepare_graph(root: Path | str, refs: Mapping[str, Mapping[str, Any]],
                  host_modules: Mapping[str, object] | None = None,
                  *, graph_spec_ref: Mapping[str, Any] | None = None) -> PinnedBridgeGraph:
    """Build one dependency-aware graph; core supplies the exact spec ref."""
    if "graph_refs" in refs or "runtime_module_graph" in refs:
        core = refs
        refs = _core_graph_inputs(core)
        graph_spec_ref = graph_spec_ref or core.get("runtime_graph_config") or core.get("runtime_module_graph_config")
    if host_modules is None:
        return load_graph(root, refs, graph_spec_ref=graph_spec_ref)
    # The focused stage fixtures intentionally use a temporary ``graph/``
    # tree and already-created module objects.  Keep that injection seam
    # explicit and structural; a production host graph must provide the
    # reviewed graph-spec reference and therefore cannot enter this branch.
    fixture_root = Path(root).resolve()
    fixture_root_allowed = (fixture_root != ROOT and
        any(fixture_root == p or p in fixture_root.parents
            for p in (Path(tempfile.gettempdir()).resolve(), Path("/private/var/folders").resolve())))
    fixture_paths = all(isinstance(ref.get("path"), str) and
                        ref["path"].startswith("graph/") for ref in refs.values())
    if fixture_root_allowed and fixture_paths and graph_spec_ref is None:
        return load_graph(fixture_root, refs, fixture_modules=host_modules, fixture_only=True)
    return bind_graph(root, refs, host_modules, graph_spec_ref=graph_spec_ref)


@dataclasses.dataclass(frozen=True)
class LockIdentity:
    path: str
    dev: int
    ino: int
    parent_pid: int
    parent_birth: str


def capture_lock(root: Path | str, lock_path: str, parent_pid: int, parent_birth: str) -> LockIdentity:
    root = Path(root).resolve()
    path = Path(lock_path)
    require(path.is_absolute(), "canonical lock path must be absolute")
    require(type(parent_pid) is int and parent_pid > 0 and isinstance(parent_birth, str) and parent_birth,
            "parent lock owner identity is malformed")
    st = _stat_tuple(path, "canonical lock")
    return LockIdentity(str(path), st[0], st[1], parent_pid, parent_birth)


@dataclasses.dataclass(frozen=True)
class ResourceSample:
    free_bytes: int
    working_bytes: int
    scratch_bytes: int
    retention_bytes: int

    def satisfies(self, *, free_floor: int, working_cap: int, scratch_cap: int,
                  retention_cap: int) -> bool:
        return (self.free_bytes >= free_floor and self.working_bytes <= working_cap and
                self.scratch_bytes <= scratch_cap and self.retention_bytes <= retention_cap)


@dataclasses.dataclass(frozen=True)
class Lease:
    popen_monotonic: float
    registered_deadline_seconds: float
    startup_seconds: float = STARTUP_SECONDS

    def setup_remaining(self, now_monotonic: float) -> float:
        elapsed = now_monotonic - self.popen_monotonic
        require(elapsed >= 0, "clock moved backwards")
        return self.registered_deadline_seconds + self.startup_seconds - elapsed


@dataclasses.dataclass(frozen=True)
class StageIdentity:
    index: int
    ledger_sha256: str
    ledger_rows: int
    runtime_sha256: str
    source_commit: str
    plan_commit: str
    contract_sha256: str
    lock: LockIdentity
    analyzer_deadline_seconds: float
    startup_seconds: float
    created_monotonic: float

    def digest(self) -> str:
        value = dataclasses.asdict(self)
        value["lock"] = dataclasses.asdict(self.lock)
        return sha256(canonical_json(value))


@dataclasses.dataclass(frozen=True)
class StageRef:
    path: str
    sha256: str
    stat: dict[str, int]

    def as_dict(self) -> dict[str, Any]:
        return {"path": self.path, "sha256": self.sha256, "stat": dict(self.stat)}


def _stage_ref(root: Path, ref: Mapping[str, Any], label: str) -> StageRef:
    raw, st = stable_read(root, ref, label)
    return StageRef(ref["path"], ref["sha256"], st)


def _witnessed_stage_ref(root: Path, ref: Mapping[str, Any], label: str) -> StageRef:
    """Validate and preserve a receipt's original stat witness.

    ``_stage_ref`` is appropriate for a newly produced dispatch sidecar: it
    records the metadata observed at that creation boundary.  Inherited
    receipt refs are different.  Their stat tuple is part of the prior
    immutable evidence and must be compared before returning the exact old
    tuple; silently replacing it with a fresh stat would erase the mutation
    proof the child is supposed to check.
    """
    checked = _ref(ref, label)
    require(isinstance(checked.get("stat"), Mapping),
            f"{label} must carry a witnessed stat tuple")
    _, current = stable_read(root, checked, label)
    expected = dict(checked["stat"])
    require(expected == current, f"{label} metadata differs from its receipt witness")
    return StageRef(checked["path"], checked["sha256"], expected)


def _stage_ref_equal(left: StageRef, right: StageRef, label: str) -> None:
    require(left.as_dict() == right.as_dict(), f"{label} differs from its witnessed StageRef")


def _current_ref(root: Path, ref: StageRef, label: str) -> None:
    stable_metadata(root, ref.as_dict(), label)


def _validate_identity_fields(source_commit: str, plan_commit: str, contract_sha256: str) -> None:
    require(isinstance(source_commit, str) and len(source_commit) == 40 and set(source_commit) <= SHA_RE,
            "source commit is malformed")
    require(isinstance(plan_commit, str) and len(plan_commit) == 40 and set(plan_commit) <= SHA_RE,
            "plan commit is malformed")
    _sha(contract_sha256, "contract sha256")


class _OpaqueStage:
    __slots__ = ("_identity", "_graph", "_runtime", "_inventory", "_sidecars",
                 "_live_ledger", "_sealed")

    def __init__(self, identity: StageIdentity, graph: PinnedBridgeGraph, runtime: object,
                 inventory: Sequence[StageRef], sidecars: Mapping[str, StageRef],
                 live_ledger: StageRef | None = None) -> None:
        require(isinstance(graph, PinnedBridgeGraph), "stage needs a pinned graph")
        self._identity = identity
        self._graph = graph
        self._runtime = runtime
        self._inventory = tuple(inventory)
        self._sidecars = dict(sidecars)
        self._live_ledger = live_ledger
        self._sealed = True

    @property
    def identity(self) -> StageIdentity:
        return self._identity

    @property
    def identity_sha256(self) -> str:
        return self._identity.digest()

    @property
    def graph(self) -> PinnedBridgeGraph:
        return self._graph

    @property
    def runtime(self) -> object:
        return self._runtime

    @property
    def inventory(self) -> tuple[StageRef, ...]:
        return self._inventory

    @property
    def sidecars(self) -> Mapping[str, StageRef]:
        return dict(self._sidecars)

    @property
    def live_ledger(self) -> StageRef | None:
        """The mutable canonical ledger witness, kept outside the snapshot."""
        return self._live_ledger

    def assert_graph(self, graph: PinnedBridgeGraph) -> None:
        require(graph is self._graph, "same-stage consumer supplied a different graph")

    def __setattr__(self, name: str, value: object) -> None:
        if getattr(self, "_sealed", False):
            raise FrozenBridge17Error("stage is immutable")
        object.__setattr__(self, name, value)

    def __getstate__(self) -> None:
        raise FrozenBridge17Error("stage runtime is opaque and cannot be serialized")


class ParentStage(_OpaqueStage):
    pass


class SuccessorStageDraft(_OpaqueStage):
    __slots__ = ("_predecessor_identity_sha256", "_ledger_before_sha256")

    def __init__(self, *args: Any, predecessor_identity_sha256: str, ledger_before_sha256: str, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        object.__setattr__(self, "_predecessor_identity_sha256", predecessor_identity_sha256)
        object.__setattr__(self, "_ledger_before_sha256", ledger_before_sha256)

    @property
    def predecessor_identity_sha256(self) -> str:
        return self._predecessor_identity_sha256

    @property
    def ledger_before_sha256(self) -> str:
        return self._ledger_before_sha256


class FinalizedParentStage(_OpaqueStage):
    __slots__ = ("_predecessor_identity_sha256",)

    def __init__(self, *args: Any, predecessor_identity_sha256: str, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        object.__setattr__(self, "_predecessor_identity_sha256", predecessor_identity_sha256)

    @property
    def predecessor_identity_sha256(self) -> str:
        return self._predecessor_identity_sha256


class ChildStage(_OpaqueStage):
    __slots__ = ("_parent_identity_sha256", "_child_creator_pid", "_child_creator_birth", "_child_pid", "_child_birth", "_lease")

    def __init__(self, *args: Any, parent_identity_sha256: str, child_creator_pid: int,
                 child_creator_birth: str, child_pid: int, child_birth: str,
                 lease: Lease, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        require(all(type(v) is int and v > 0 for v in (child_creator_pid, child_pid)), "child PIDs malformed")
        require(all(isinstance(v, str) and v for v in (child_creator_birth, child_birth)), "child births malformed")
        object.__setattr__(self, "_parent_identity_sha256", parent_identity_sha256)
        object.__setattr__(self, "_child_creator_pid", child_creator_pid)
        object.__setattr__(self, "_child_creator_birth", child_creator_birth)
        object.__setattr__(self, "_child_pid", child_pid)
        object.__setattr__(self, "_child_birth", child_birth)
        object.__setattr__(self, "_lease", lease)

    @property
    def parent_identity_sha256(self) -> str:
        return self._parent_identity_sha256

    @property
    def child_identity(self) -> dict[str, Any]:
        return {"creator_pid": self._child_creator_pid, "creator_birth": self._child_creator_birth,
                "pid": self._child_pid, "birth": self._child_birth}

    @property
    def lease(self) -> Lease:
        return self._lease


# The supervisor supplies exactly these three current-dispatch witnesses.  The
# keys are canonical sidecar paths (rather than short labels), so a receipt
# can bind the exact file that the child consumed.  Historical/inherited
# sidecars remain separate and are never replaced by these refs.
CHILD_DISPATCH_SIDECAR_COUNT = 3


def _canonical_stage_receipt_path(core: Mapping[str, Any] | None, index: int) -> str:
    """Return the only accepted compact receipt path for a stage index."""
    require(type(index) is int and 0 <= index < PARENT_STAGE_COUNT,
            "stage receipt index is outside the reviewed parent range")
    if core is not None:
        namespace = core.get("sidecar_namespace")
        require(isinstance(namespace, str) and namespace,
                "core sidecar namespace is required for canonical stage receipts")
        _relative(namespace, "core sidecar namespace")
        return (PurePosixPath(namespace) / "stages" / f"stage-{index:02d}.json").as_posix()
    # Compatibility for the existing supervisor call boundary.  The caller
    # still supplies the reviewed sidecar namespace in its path; this fallback
    # refuses arbitrary copies while allowing the root-owned supervisor to
    # migrate to the explicit ``core=`` argument.
    return (PurePosixPath("stages") / f"stage-{index:02d}.json").as_posix()


# Compatibility boundary for the reviewed frozen validators.  The stage API
# above owns the graph and prevents reloads for same-stage consumers.  The
# legacy validator itself is still pinned by path/SHA here so the BF14
# supervisor can migrate its existing read-only bridge call sites without
# accepting an unreviewed module or serialized context.
LEGACY_BRIDGE_REF = {
    "path": "reports/releases/v0.9.2/acquisition/bifrost-v0140-frozen-bridge-08.py",
    "sha256": "d964c524cfec26e296a44e4c09ce3a606dcdfaec7c83114a1be3801222e35189",
}
_LEGACY_MODULE_CACHE: dict[str, object] = {}


def _legacy_bridge(root: Path) -> object:
    key = str(root.resolve())
    cached = _LEGACY_MODULE_CACHE.get(key)
    if cached is not None:
        return cached
    raw, _ = stable_read(root, LEGACY_BRIDGE_REF, "legacy frozen bridge")
    path = _path(root, LEGACY_BRIDGE_REF["path"], "legacy frozen bridge path")
    spec = importlib.util.spec_from_file_location("v092_bifrost15_legacy_bridge08", path)
    require(spec is not None and spec.loader is not None, "legacy frozen bridge cannot be imported")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    after, _ = stable_read(root, LEGACY_BRIDGE_REF, "legacy frozen bridge after import")
    require(raw == after, "legacy frozen bridge changed during import")
    _LEGACY_MODULE_CACHE[key] = module
    return module


def load_dependencies(root: Path | str, *, fixture_modules: Mapping[str, Any] | None = None,
                      fixture_only: bool = False) -> dict[str, Any]:
    """Expose the exact legacy nested modules for migration call sites."""
    if fixture_only:
        require(fixture_modules is not None, "fixture-only dependencies need modules")
        return dict(fixture_modules)
    legacy = _legacy_bridge(Path(root).resolve())
    loader = getattr(legacy, "load_dependencies", None)
    require(callable(loader), "pinned legacy bridge lacks load_dependencies")
    modules = loader(Path(root).resolve())
    require(isinstance(modules, Mapping), "legacy bridge returned no module graph")
    return dict(modules)


def load_and_validate(root: Path | str, core: Mapping[str, Any], *, mode: str = "before",
                      ledger_bytes: bytes | None = None, fixture_modules: Mapping[str, Any] | None = None,
                      fixture_only: bool = False, _runtime_sink: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Run the pinned frozen validator once; no caller-supplied result is accepted."""
    legacy = _legacy_bridge(Path(root).resolve())
    loader = getattr(legacy, "load_and_validate", None)
    require(callable(loader), "pinned legacy bridge lacks load_and_validate")
    return loader(Path(root).resolve(), core, mode=mode, ledger_bytes=ledger_bytes,
                  fixture_modules=fixture_modules, fixture_only=fixture_only,
                  _runtime_sink=_runtime_sink)


@dataclasses.dataclass(frozen=True)
class ActualRuntimeContext:
    """Opaque in-process result retained by one parent/child stage.

    The diagnostic is useful for audit receipts, but no consumer is allowed
    to reconstruct runtime authority from it.  The graph and module mapping
    retain the exact objects used by the validation call.
    """

    root: Path
    mode: str
    graph: PinnedBridgeGraph
    modules: Mapping[str, object]
    diagnostic: Mapping[str, Any]
    objects: Mapping[str, object] = dataclasses.field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        require(tuple(self.modules) == REQUIRED_GRAPH_NAMES,
                "opaque runtime graph is incomplete")
        self.graph.assert_complete(self.modules)
        if self.objects:
            object_modules = self.objects.get("modules")
            # Historical bridge consumers expose the complete graph mapping.
            # The BF14 stage adapter additionally exposes the four frozen
            # checker roles under their legacy names while retaining the full
            # graph separately on ``self.modules``.  Both mappings must point
            # at the exact graph objects; neither may be reconstructed from
            # the compact diagnostic.
            if object_modules is not self.modules:
                require(isinstance(object_modules, Mapping) and
                        tuple(object_modules) == ("replacement05", "executor", "checker", "configuration"),
                        "runtime object map does not retain a recognized module mapping")
                require(object_modules["replacement05"] is _replacement_runtime_member(self.graph) and
                        object_modules["executor"] is self.graph.module("executor") and
                        object_modules["checker"] is self.graph.module("checker") and
                        object_modules["configuration"] is self.graph.module("configuration"),
                        "runtime object map contains foreign module instances")

    def __getstate__(self) -> None:
        raise FrozenBridge17Error("runtime context is opaque and cannot be serialized")


def _graph_runtime_context(root: Path, core: Mapping[str, Any], graph: PinnedBridgeGraph,
                           *, mode: str, ledger_bytes: bytes | None) -> ActualRuntimeContext:
    """Run the copied complete bridge08 validator through the pinned graph.

    Production requires stage_runtime09, which retains every historical,
    source, contract, capture and resource check and returns live objects.
    The small provider branch below is restricted to temporary fixture graphs.
    """
    require(mode in {"before", "after"}, "runtime validation mode is unknown")

    # The successor graph owns the complete frozen bridge adapter.  Keep this
    # dispatch here, rather than importing the successor by path: the graph
    # member was hash-checked and (for the parent process) is the exact module
    # object already executing the supervisor.  The adapter returns the
    # lossless v092 runtime mapping used by the frozen checker/configuration;
    # this wrapper only turns it into the bridge17 opaque holder.
    stage_loader = graph.module("stage_runtime09") if "stage_runtime09" in tuple(
        member.name for member in graph.members
    ) else None
    if stage_loader is not None:
        loader = getattr(stage_loader, "load_runtime_context", None)
        require(callable(loader), "stage-runtime graph member lacks load_runtime_context")
        value = loader(root, core, graph=graph, mode=mode, ledger_bytes=ledger_bytes,
                       stdlib_importlib=HOST_STDLIB_IMPORTLIB)
        require(isinstance(value, Mapping), "stage-runtime provider returned no runtime mapping")
        require(value.get("schema") == "v092-bifrost-v0140-runtime-context/v1" and
                value.get("lossless_runtime_objects") is True,
                "stage-runtime provider returned an unreviewed runtime schema")
        runtime_modules = value.get("modules")
        require(isinstance(runtime_modules, Mapping) and
                tuple(runtime_modules) == ("replacement05", "executor", "checker", "configuration"),
                "stage-runtime module roster is not the frozen lossless roster")
        # The full replacement05 validator is a distinct pinned graph member;
        # the replacement22 packet protocol cannot substitute for it.
        require(runtime_modules["replacement05"] is _replacement_runtime_member(graph),
                "stage-runtime replacement object is not the pinned full bridge member")
        for name in ("executor", "checker", "configuration"):
            require(runtime_modules[name] is graph.module(name),
                    f"stage-runtime returned a foreign {name} object")
        bridge_context = value.get("bridge_context")
        require(isinstance(bridge_context, Mapping) and
                isinstance(bridge_context.get("context_digest"), str) and
                len(bridge_context["context_digest"]) == 64,
                "stage-runtime bridge context has no stable digest")
        graph_modules = {name: graph.module(name) for name in REQUIRED_GRAPH_NAMES}
        objects = dict(value)
        manifest_path = core.get("manifest_path")
        require(isinstance(manifest_path, str), "stage core lacks the exact manifest path")
        static = graph.module("protocol22").validate_static(root, manifest_path)
        require(isinstance(static, Mapping) and static.get("core") == core,
                "stage protocol static core differs from the actual runtime core")
        objects["protocol_static"] = static
        diagnostic = dict(bridge_context)
        diagnostic.setdefault("schema", "v092-bifrost-v0140-runtime-context-diagnostic/v1")
        diagnostic.setdefault("graph_sha256", graph.graph_sha256)
        return ActualRuntimeContext(root=root, mode=mode, graph=graph,
                                    modules=graph_modules, diagnostic=diagnostic,
                                    objects=objects)

    require(graph.fixture_only, "production graph omits the complete stage-runtime validator")
    replacement = graph.module("replacement22")
    executor = graph.module("executor")
    require(callable(getattr(replacement, "validate_static", None)),
            "replacement22 has no reviewed static validator")
    manifest_value = core.get("manifest_ref", core.get("manifest_path"))
    if isinstance(manifest_value, Mapping):
        manifest_path = manifest_value.get("path")
    else:
        manifest_path = manifest_value
    require(isinstance(manifest_path, str), "core has no reviewed manifest path")
    static = replacement.validate_static(root, manifest_path)
    require(isinstance(static, Mapping) and isinstance(static.get("core"), Mapping),
            "replacement22 returned no validated core")
    canonical_core = static["core"]
    contract_value = canonical_core.get("contract")
    require(isinstance(contract_value, Mapping), "validated core has no contract ref")
    contract_ref = _ref(contract_value, "validated contract")
    contract_path = _path(root, contract_ref["path"], "validated contract path")
    validate_plan = getattr(executor, "validate_plan", None)
    require(callable(validate_plan), "frozen executor has no validate_plan")
    try:
        validated = validate_plan(contract_path, repo_root=root)
    except TypeError:
        # Older frozen executors use the path plus a positional checkout root;
        # this fallback is signature-bound and does not catch validator errors.
        validated = validate_plan(contract_path, root)
    require(isinstance(validated, Mapping), "frozen executor returned no normalized plan")
    require(validated.get("bytes_sha256") == contract_ref["sha256"],
            "frozen executor normalized a different contract")
    modules = {name: graph.module(name) for name in REQUIRED_GRAPH_NAMES}
    # Full checker/configuration replay is supplied by one graph-owned
    # incoming-recovery provider.  The provider is itself pinned in the graph;
    # accepting a caller callback here would permit a serialized or foreign
    # context to masquerade as the actual replay result.  Providers may load a
    # fresh dependency graph for a changed ledger, but the returned module
    # objects must be members of this graph (or the provider must fail closed).
    provider = graph.module("incoming_recovery")
    provider_loader = getattr(provider, "load_runtime_context", None)
    require(callable(provider_loader),
            "pinned incoming-recovery graph member lacks the complete runtime provider")
    provider_kwargs: dict[str, Any] = {"mode": mode, "core": core, "graph": graph,
                                      "root": root, "ledger_bytes": ledger_bytes}
    provider_params = inspect.signature(provider_loader).parameters
    accepts_kwargs = any(parameter.kind is inspect.Parameter.VAR_KEYWORD
                         for parameter in provider_params.values())
    if not accepts_kwargs:
        provider_kwargs = {key: value for key, value in provider_kwargs.items() if key in provider_params}
    provided = provider_loader(**provider_kwargs)
    require(isinstance(provided, Mapping), "incoming-recovery provider returned no runtime mapping")
    required_runtime = {"modules", "validated", "mixed_context", "checker_summary",
                        "configuration_summary", "bridge_context"}
    require(required_runtime <= set(provided),
            "incoming-recovery provider returned an incomplete runtime mapping")
    provider_modules = provided["modules"]
    require(isinstance(provider_modules, Mapping), "incoming-recovery runtime module mapping is malformed")
    for name, module in provider_modules.items():
        graph_name = name
        # replacement05 is the historical public name used by the frozen
        # checker.  A successor graph may expose the same object under its
        # replacement22 role, but it may never silently import a second copy.
        if name == "replacement05":
            expected = _replacement_runtime_member(graph)
            require(expected is module,
                    "runtime provider returned a foreign replacement05 module")
            continue
        require(graph_name in modules and modules[graph_name] is module,
                f"runtime provider returned a foreign module: {name}")
    require(isinstance(provided["validated"], Mapping), "runtime provider normalized plan is malformed")
    require(isinstance(provided["mixed_context"], Mapping), "runtime provider mixed context is malformed")
    require(isinstance(provided["checker_summary"], Mapping), "runtime provider checker summary is malformed")
    require(isinstance(provided["configuration_summary"], Mapping),
            "runtime provider configuration summary is malformed")
    bridge_context = provided["bridge_context"]
    require(isinstance(bridge_context, Mapping), "runtime provider bridge context is malformed")
    diagnostic = {
        "schema": SCHEMA + "/graph-runtime",
        "status": "graph-owned-frozen-validation-passed",
        "execution_authorized": False,
        "mode": mode,
        "manifest_path": manifest_path,
        "manifest_sha256": sha256(_path(root, manifest_path, "manifest").read_bytes()),
        "contract": contract_ref,
        "validated": validated,
        "ledger_bytes_sha256": None if ledger_bytes is None else sha256(ledger_bytes),
        "graph_sha256": graph.graph_sha256,
        "lossless_runtime_objects": True,
        "protocol_static": static,
        "bridge_context": bridge_context,
        "modules": modules,
        "mixed_context": provided["mixed_context"],
        "checker_summary": provided["checker_summary"],
        "configuration_summary": provided["configuration_summary"],
    }
    objects = {
        "protocol_static": static,
        "modules": modules,
        "validated": provided["validated"],
        "mixed_context": provided["mixed_context"],
        "checker_summary": provided["checker_summary"],
        "configuration_summary": provided["configuration_summary"],
        "bridge_context": bridge_context,
    }
    return ActualRuntimeContext(root=root, mode=mode, graph=graph,
                                modules=modules, diagnostic=diagnostic, objects=objects)


def load_runtime_context(root: Path | str, core: Mapping[str, Any], *, mode: str = "before",
                         ledger_bytes: bytes | None = None, fixture_modules: Mapping[str, Any] | None = None,
                         fixture_only: bool = False,
                         graph: PinnedBridgeGraph | None = None) -> object:
    """Return one lossless opaque runtime context from the pinned graph.

    ``graph`` is mandatory for production stage construction.  The legacy
    bridge is used only as a pinned validator compatibility boundary while
    migration call sites are being moved; the returned object is wrapped in
    an opaque stage-local value and cannot be supplied as serialized JSON.
    """
    require(isinstance(graph, PinnedBridgeGraph),
            "runtime validation requires a pinned complete graph")
    graph.assert_member("bridge17", sys.modules.get(__name__))
    if fixture_only:
        require(fixture_modules is not None, "fixture-only runtime needs modules")
        # Fixture graph modules own their harmless runtime loader.  Production
        # never reaches this branch because fixture_only is rejected by the
        # graph boundary.
        fixture_loader = getattr(graph.module("bridge17"), "fixture_runtime_context", None)
        require(callable(fixture_loader), "fixture graph has no explicit runtime seam")
        return fixture_loader(mode=mode, core_identity=core, graph=graph)
    require(not fixture_modules, "production runtime cannot inject modules")
    return _graph_runtime_context(Path(root).resolve(), core, graph,
                                  mode=mode, ledger_bytes=ledger_bytes)


def validate_frozen_bridge(root: Path | str, core: Mapping[str, Any], *, mode: str = "before",
                           **kwargs: Any) -> dict[str, Any]:
    """Compatibility name used by admission's static bridge loader."""
    return load_and_validate(root, core, mode=mode, **kwargs)


def _make_identity(*, index: int, ledger_ref: StageRef, runtime: object, source_commit: str,
                   plan_commit: str, contract_sha256: str, lock: LockIdentity,
                   ledger_rows: int,
                   analyzer_deadline_seconds: float, startup_seconds: float,
                   created_monotonic: float) -> StageIdentity:
    require(index >= 0, "stage index is negative")
    _validate_identity_fields(source_commit, plan_commit, contract_sha256)
    require(ledger_ref.stat.get("size", 0) > 0, "stage ledger is empty")
    rows = int(ledger_rows)
    require(rows > 0, "stage ledger rows are empty")
    return StageIdentity(index, ledger_ref.sha256, rows, runtime_digest(runtime), source_commit,
                         plan_commit, contract_sha256, lock, float(analyzer_deadline_seconds),
                         float(startup_seconds), float(created_monotonic))


def build_parent_stage(root: Path | str, *, index: int, ledger: Mapping[str, Any],
                       runtime: object, graph: PinnedBridgeGraph, source_commit: str,
                       plan_commit: str, contract_sha256: str, lock: LockIdentity,
                       sidecars: Mapping[str, Mapping[str, Any]], source_refs: Sequence[Mapping[str, Any]],
                       analyzer_deadline_seconds: float, startup_seconds: float = STARTUP_SECONDS,
                       created_monotonic: float | None = None,
                       live_ledger: Mapping[str, Any] | None = None) -> ParentStage:
    """Build one immutable parent stage after one full actual replay."""
    require(index < PARENT_STAGE_COUNT, "parent stage index exceeds the 21-state contract")
    root = Path(root).resolve()
    require(graph is not None and isinstance(runtime, object), "actual runtime graph/context are required")
    ledger_ref = _stage_ref(root, ledger, "stage ledger")
    require(type(ledger.get("rows")) is int and ledger["rows"] > 0, "stage ledger rows are required")
    inventory = [ledger_ref]
    for index_ref, source_ref in enumerate(source_refs):
        inventory.append(_stage_ref(root, source_ref, f"stage source closure {index_ref}"))
    refs: dict[str, StageRef] = {}
    for name, ref in sidecars.items():
        _relative(name, "sidecar key")
        refs[name] = _stage_ref(root, ref, f"stage sidecar {name}")
    identity = _make_identity(index=index, ledger_ref=ledger_ref, runtime=runtime, source_commit=source_commit,
                              plan_commit=plan_commit, contract_sha256=contract_sha256, lock=lock,
                              ledger_rows=int(ledger["rows"]),
                              analyzer_deadline_seconds=analyzer_deadline_seconds,
                              startup_seconds=startup_seconds,
                              created_monotonic=time.monotonic() if created_monotonic is None else created_monotonic)
    live_ref = None if live_ledger is None else _stage_ref(root, live_ledger, "live ledger witness")
    return ParentStage(identity, graph, runtime, inventory, refs, live_ledger=live_ref)


def assert_stage_current(root: Path | str, stage: ParentStage | SuccessorStageDraft | FinalizedParentStage,
                         graph: PinnedBridgeGraph | None = None) -> None:
    require(isinstance(stage, _OpaqueStage), "stage must be an opaque stage object")
    if graph is not None:
        stage.assert_graph(graph)
    for ref in stage.inventory:
        _current_ref(Path(root).resolve(), ref, f"stage inventory {ref.path}")
    for name, ref in stage.sidecars.items():
        _current_ref(Path(root).resolve(), ref, f"stage sidecar {name}")
    if stage.live_ledger is not None:
        _current_ref(Path(root).resolve(), stage.live_ledger, "stage live ledger witness")


def _assert_immutable_stage(root: Path | str, stage: ParentStage | FinalizedParentStage,
                            graph: PinnedBridgeGraph | None = None) -> None:
    """Validate the prior immutable snapshot while allowing its live ledger append."""
    require(isinstance(stage, _OpaqueStage), "stage must be an opaque stage object")
    if graph is not None:
        stage.assert_graph(graph)
    root = Path(root).resolve()
    for ref in stage.inventory:
        _current_ref(root, ref, f"stage inventory {ref.path}")
    for name, ref in stage.sidecars.items():
        _current_ref(root, ref, f"stage sidecar {name}")


def build_successor_stage(root: Path | str, *, predecessor: ParentStage | FinalizedParentStage,
                          index: int, ledger_after: Mapping[str, Any], runtime: object,
                          graph: PinnedBridgeGraph, source_commit: str, plan_commit: str,
                          contract_sha256: str, sidecars: Mapping[str, Mapping[str, Any]],
                          source_refs: Sequence[Mapping[str, Any]],
                          analyzer_deadline_seconds: float, startup_seconds: float = STARTUP_SECONDS,
                          created_monotonic: float | None = None,
                          live_ledger: Mapping[str, Any] | None = None) -> SuccessorStageDraft:
    require(index == predecessor.identity.index + 1, "successor stage is not the immediate next state")
    require(index < PARENT_STAGE_COUNT, "successor index exceeds the 21-state contract")
    _assert_immutable_stage(root, predecessor, predecessor.graph)
    root = Path(root).resolve()
    after_ref = _stage_ref(root, ledger_after, "successor ledger")
    require(type(ledger_after.get("rows")) is int and ledger_after["rows"] == predecessor.identity.ledger_rows + 1,
            "successor must append exactly one ledger row")
    before_path = _path(root, predecessor.inventory[0].path, "predecessor ledger")
    after_path = _path(root, after_ref.path, "successor ledger")
    before_raw = before_path.read_bytes()
    after_raw = after_path.read_bytes()
    require(after_raw.startswith(before_raw), "successor ledger is not the predecessor prefix")
    tail = after_raw[len(before_raw):]
    require(tail.count(b"\n") == 1 and tail.endswith(b"\n"), "successor ledger appends one complete row")
    if live_ledger is not None:
        live_raw, _ = stable_read(root, live_ledger, "successor live ledger witness")
        require(live_raw == after_raw,
                "successor live ledger witness is not the exact successor bytes")
    inventory = [after_ref]
    for n, ref in enumerate(source_refs):
        inventory.append(_stage_ref(root, ref, f"successor source closure {n}"))
    # A successor is an immutable extension of its predecessor.  Existing
    # admission/phase/permit/ledger sidecars remain part of the stage
    # inventory; a caller may only add new deterministic names or repeat the
    # exact same binding.  Silently replacing or dropping prior evidence would
    # make the compact stage receipt unable to account for the full history.
    refs = dict(predecessor.sidecars)
    for name, ref in sidecars.items():
        _relative(name, "successor sidecar key")
        current = refs.get(name)
        checked = _stage_ref(root, ref, f"successor sidecar {name}")
        if current is not None:
            require(current.path == checked.path and current.sha256 == checked.sha256,
                    f"successor attempts to replace prior sidecar: {name}")
        refs[name] = checked
    ledger_ref = after_ref
    identity = _make_identity(index=index, ledger_ref=ledger_ref, runtime=runtime, source_commit=source_commit,
                              plan_commit=plan_commit, contract_sha256=contract_sha256, lock=predecessor.identity.lock,
                              ledger_rows=int(ledger_after["rows"]),
                              analyzer_deadline_seconds=analyzer_deadline_seconds,
                              startup_seconds=startup_seconds,
                              created_monotonic=time.monotonic() if created_monotonic is None else created_monotonic)
    draft = SuccessorStageDraft(identity, graph, runtime, inventory, refs,
                                predecessor_identity_sha256=predecessor.identity_sha256,
                                ledger_before_sha256=predecessor.identity.ledger_sha256,
                                live_ledger=None if live_ledger is None else _stage_ref(
                                    root, live_ledger, "successor live ledger witness"))
    return draft


def write_completion(root: Path | str, *, predecessor: ParentStage | FinalizedParentStage,
                     successor: SuccessorStageDraft, completion_path: str,
                     completion: Mapping[str, Any], expected_group_id: str,
                     expected_attempt_id: str, graph: PinnedBridgeGraph) -> FinalizedParentStage:
    """Write one completion sidecar and return a new immutable successor stage."""
    require(successor.predecessor_identity_sha256 == predecessor.identity_sha256,
            "completion predecessor/successor identity mismatch")
    predecessor.assert_graph(graph)
    successor.assert_graph(graph)
    require(completion.get("group_id") == expected_group_id and completion.get("attempt_id") == expected_attempt_id,
            "completion group/attempt does not match the transition")
    root = Path(root).resolve()
    _relative(completion_path, "completion path")
    target = _path(root, completion_path, "completion path")
    raw = canonical_json(dict(completion))
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        with target.open("xb") as handle:
            handle.write(raw)
    except FileExistsError as exc:
        raise FrozenBridge17Error("completion sidecar already exists; retry is forbidden") from exc
    ref = {"path": completion_path, "sha256": sha256(raw)}
    completion_ref = _stage_ref(root, ref, "completion sidecar")
    sidecars = dict(successor.sidecars)
    require(completion_path not in sidecars, "completion path already appeared in successor draft")
    sidecars[completion_path] = completion_ref
    return FinalizedParentStage(successor.identity, successor.graph, successor.runtime, successor.inventory,
                                sidecars, live_ledger=successor.live_ledger,
                                predecessor_identity_sha256=predecessor.identity_sha256)


def _read_compact_parent(root: Path, value: Mapping[str, Any], *,
                         core: Mapping[str, Any] | None = None,
                         expected_index: int | None = None,
                         validate_live_current: bool = True,
                         _chain: tuple[str, ...] = ()) -> dict[str, Any]:
    """Read one exact parent receipt and its bounded predecessor chain.

    The JSON is a stable witness only.  This function validates every ref and
    predecessor link, but it never creates a runtime object from receipt
    fields.  ``expected_index`` prevents a valid receipt from another point
    in the breadth-first sequence being reused by a child.
    """
    require(isinstance(value, Mapping) and set(value) == {"path", "sha256"},
            "parent receipt ref has unexpected fields")
    receipt_path = value["path"]
    raw, _ = stable_read(root, value, "parent stage receipt")
    try:
        receipt = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise FrozenBridge17Error("parent stage receipt is not JSON") from exc
    require(isinstance(receipt, Mapping) and
            receipt.get("schema") == SCHEMA + "/stage-receipt",
            "parent receipt schema is not the reviewed compact stage schema")
    required = {"stage_receipt_path", "stage_index", "stage_identity",
                "stage_identity_sha256", "ledger_ref", "ledger_rows", "inventory_refs",
                "live_ledger_ref", "graph_members", "graph_bindings", "graph_sha256",
                "source_commit", "plan_commit", "contract_sha256", "lock", "manifest_ref",
                "core_identity", "sidecars", "sidecar_refs", "predecessor_identity_sha256",
                "predecessor_receipt_ref", "status"}
    require(required <= set(receipt), "parent receipt omits a stable binding")
    index = receipt["stage_index"]
    require(type(index) is int and 0 <= index < PARENT_STAGE_COUNT,
            "parent receipt stage index is malformed")
    require(receipt["stage_receipt_path"] == receipt_path,
            "parent receipt path is not self-bound")
    if core is not None:
        require(receipt_path == _canonical_stage_receipt_path(core, index),
                "parent receipt is not at the canonical stage path")
    else:
        parts = PurePosixPath(receipt_path).parts
        require(len(parts) >= 2 and parts[-2:] == ("stages", f"stage-{index:02d}.json"),
                "parent receipt is not at a canonical stage path")
    if expected_index is not None:
        require(index == expected_index, "parent receipt stage index differs from the expected stage")
    require(receipt_path not in _chain, "parent receipt predecessor chain contains a cycle")
    chain = _chain + (receipt_path,)

    stage_identity = receipt["stage_identity"]
    require(isinstance(receipt["ledger_ref"], Mapping),
            "parent receipt ledger ref is malformed")
    require(isinstance(stage_identity, Mapping) and
            receipt["stage_identity_sha256"] == sha256(canonical_json(stage_identity)) and
            type(stage_identity.get("index")) is int and stage_identity["index"] == index and
            stage_identity.get("ledger_sha256") == receipt["ledger_ref"].get("sha256") and
            stage_identity.get("ledger_rows") == receipt["ledger_rows"],
            "parent receipt identity fields are inconsistent")
    require(receipt["status"] == ("parent-stage-verified" if index == 0 else "successor-stage-verified"),
            "parent receipt status does not match its stage index")
    require(receipt["source_commit"] == stage_identity.get("source_commit") and
            receipt["plan_commit"] == stage_identity.get("plan_commit") and
            receipt["contract_sha256"] == stage_identity.get("contract_sha256"),
            "parent receipt source/plan/contract bindings are inconsistent")
    _validate_identity_fields(receipt["source_commit"], receipt["plan_commit"], receipt["contract_sha256"])

    require(isinstance(receipt["graph_members"], list) and receipt["graph_members"],
            "parent receipt graph binding is empty")
    graph_bindings = []
    for item in receipt["graph_members"]:
        require(isinstance(item, Mapping) and
                set(item) == {"name", "canonical_path", "source_sha256", "loader_identity"},
                "parent receipt graph member is malformed")
        graph_bindings.append({"name": item["name"], "canonical_path": item["canonical_path"],
                               "source_sha256": item["source_sha256"]})
    require(receipt.get("graph_bindings") == graph_bindings,
            "parent receipt graph bindings differ from its public members")
    require(receipt.get("graph_sha256") == sha256(canonical_json(graph_bindings)),
            "parent receipt graph digest is not bound to its members")

    inventory = receipt["inventory_refs"]
    require(isinstance(inventory, list) and inventory,
            "parent receipt inventory is empty")
    inventory_refs = []
    seen_paths: set[str] = set()
    for number, item in enumerate(inventory):
        checked = _ref(item, f"parent receipt inventory {number}")
        require(set(checked) == {"path", "sha256", "stat"},
                "parent receipt inventory ref must preserve its stat witness")
        require(checked["path"] not in seen_paths,
                "parent receipt inventory contains a duplicate path")
        seen_paths.add(checked["path"])
        inventory_refs.append(checked)
        _witnessed_stage_ref(Path(root).resolve(), checked, f"parent receipt inventory {number}")
    require(receipt["ledger_ref"] == inventory_refs[0],
            "parent receipt ledger ref differs from ordered inventory[0]")
    require(receipt["live_ledger_ref"] is None or isinstance(receipt["live_ledger_ref"], Mapping),
            "parent receipt live ledger ref is malformed")
    if receipt["live_ledger_ref"] is not None:
        live = _ref(receipt["live_ledger_ref"], "parent receipt live ledger")
        require(set(live) == {"path", "sha256", "stat"},
                "parent receipt live ledger must preserve its stat witness")
        if validate_live_current:
            _witnessed_stage_ref(Path(root).resolve(), live, "parent receipt live ledger")

    sidecars = receipt["sidecars"]
    sidecar_refs = receipt["sidecar_refs"]
    require(isinstance(sidecars, list) and sidecars == sorted(set(sidecars)),
            "parent receipt sidecar names are not exact sorted names")
    require(isinstance(sidecar_refs, Mapping) and tuple(sidecar_refs) == tuple(sidecars),
            "parent receipt sidecar refs do not match its exact key order")
    for name in sidecars:
        _relative(name, "parent receipt sidecar name")
        checked = _ref(sidecar_refs[name], f"parent receipt sidecar {name}")
        require(set(checked) == {"path", "sha256", "stat"},
                "parent receipt sidecar must preserve its stat witness")
        _witnessed_stage_ref(Path(root).resolve(), checked, f"parent receipt sidecar {name}")

    predecessor_ref = receipt["predecessor_receipt_ref"]
    predecessor_identity = receipt["predecessor_identity_sha256"]
    if index == 0:
        require(predecessor_ref is None and predecessor_identity is None,
                "stage zero cannot carry predecessor metadata")
    else:
        require(isinstance(predecessor_ref, Mapping) and set(predecessor_ref) == {"path", "sha256"},
                "successor receipt needs one exact predecessor receipt ref")
        _sha(predecessor_identity, "predecessor identity sha256")
        predecessor = _read_compact_parent(
            root, predecessor_ref, core=core, expected_index=index - 1,
            validate_live_current=False, _chain=chain)
        require(predecessor["stage_identity_sha256"] == predecessor_identity,
                "successor predecessor identity does not match the referenced receipt")
        # A valid receipt from another manifest/graph lineage must not be
        # spliceable into this successor merely because its immediate
        # predecessor digest was copied.  These fields are the stable
        # cross-stage contract; only the ledger snapshot and stage-local
        # evidence are expected to advance.
        for field in ("manifest_ref", "core_identity", "source_commit", "plan_commit",
                      "contract_sha256", "lock", "graph_bindings", "graph_sha256"):
            require(predecessor[field] == receipt[field],
                    f"successor predecessor {field} escaped the stable lineage")
        for name in predecessor["sidecars"]:
            require(name in sidecars and
                    predecessor["sidecar_refs"][name] == sidecar_refs[name],
                    f"successor dropped or replaced predecessor sidecar: {name}")
    return dict(receipt)


def lock_identity_matches(actual: LockIdentity, expected: LockIdentity) -> bool:
    return actual == expected


def build_child_stage(root: Path | str, *,
                      parent: ParentStage | FinalizedParentStage | None = None,
                      parent_binding: Mapping[str, Any] | None = None,
                      runtime: object, graph: PinnedBridgeGraph, source_refs: Sequence[Mapping[str, Any]],
                      child_creator_pid: int, child_creator_birth: str, child_pid: int, child_birth: str,
                      analyzer_deadline_seconds: float, popen_monotonic: float,
                      sidecars: Mapping[str, Mapping[str, Any]], ledger: Mapping[str, Any],
                      live_ledger: Mapping[str, Any] | None = None,
                      lock_identity: LockIdentity | None = None) -> ChildStage:
    root = Path(root).resolve()
    inherited_inventory: tuple[StageRef, ...] | None = None
    inherited_sidecars: dict[str, StageRef] = {}
    inherited_live_ledger: StageRef | None = None
    if parent is not None:
        require(isinstance(parent, _OpaqueStage), "child stage needs parent stage")
        parent.assert_graph(parent.graph)
        parent_identity_sha = parent.identity_sha256
        parent_graph_binding = tuple(member.binding() for member in parent.graph.members)
        parent_identity = parent.identity
        inherited_inventory = parent.inventory
        inherited_sidecars = dict(parent.sidecars)
        inherited_live_ledger = parent.live_ledger
    else:
        require(isinstance(parent_binding, Mapping),
                "child stage needs a validated compact parent binding")
        parent_identity_sha = parent_binding.get("stage_identity_sha256")
        _sha(parent_identity_sha, "parent stage identity sha256")
        bindings = parent_binding.get("graph_bindings")
        require(isinstance(bindings, list) and bindings,
                "compact parent graph bindings are malformed")
        parent_graph_binding = tuple(dict(item) for item in bindings)
        identity_value = parent_binding.get("stage_identity")
        require(isinstance(identity_value, Mapping), "compact parent identity is malformed")
        lock_value = parent_binding.get("lock")
        require(isinstance(lock_value, Mapping), "compact parent lock is malformed")
        parent_identity = StageIdentity(
            index=identity_value.get("index"),
            ledger_sha256=identity_value.get("ledger_sha256"),
            ledger_rows=identity_value.get("ledger_rows"),
            runtime_sha256=identity_value.get("runtime_sha256"),
            source_commit=parent_binding.get("source_commit"),
            plan_commit=parent_binding.get("plan_commit"),
            contract_sha256=parent_binding.get("contract_sha256"),
            lock=LockIdentity(**dict(lock_value)),
            analyzer_deadline_seconds=identity_value.get("analyzer_deadline_seconds"),
            startup_seconds=identity_value.get("startup_seconds"),
            created_monotonic=identity_value.get("created_monotonic"),
        )
        require(parent_identity.digest() == parent_identity_sha,
                "compact parent identity fields do not match its digest")
        inventory_value = parent_binding.get("inventory_refs")
        require(isinstance(inventory_value, list) and inventory_value,
                "compact parent inventory is absent")
        inherited_inventory = tuple(
            _witnessed_stage_ref(root, item, f"compact parent inventory {number}")
            for number, item in enumerate(inventory_value))
        require(parent_binding.get("ledger_ref") == inherited_inventory[0].as_dict(),
                "compact parent ledger is not inventory[0]")
        sidecar_names = parent_binding.get("sidecars")
        sidecar_values = parent_binding.get("sidecar_refs")
        require(isinstance(sidecar_names, list) and sidecar_names == sorted(set(sidecar_names)) and
                isinstance(sidecar_values, Mapping) and tuple(sidecar_values) == tuple(sidecar_names),
                "compact parent sidecars are not exact")
        inherited_sidecars = {
            name: _witnessed_stage_ref(root, sidecar_values[name], f"compact parent sidecar {name}")
            for name in sidecar_names
        }
        live_value = parent_binding.get("live_ledger_ref")
        if live_value is not None:
            inherited_live_ledger = _witnessed_stage_ref(root, live_value,
                                                         "compact parent live ledger")
    if lock_identity is None:
        lock_identity = parent_identity.lock
    require(lock_identity_matches(lock_identity, parent_identity.lock),
            "child lock identity differs from the parent permit")
    lease = Lease(float(popen_monotonic), float(analyzer_deadline_seconds), STARTUP_SECONDS)
    require(lease.setup_remaining(float(popen_monotonic)) == analyzer_deadline_seconds + STARTUP_SECONDS,
            "child lease start is not the actual Popen time")
    # The child graph is intentionally a fresh graph for a separate process,
    # but its public path/SHA tuple must equal the parent graph tuple.
    require(tuple(member.binding() for member in graph.members) == parent_graph_binding,
            "child graph path/SHA tuple differs from parent stage")
    require(inherited_inventory is not None and inherited_inventory,
            "child has no immutable parent inventory")
    # The caller's ledger/source closure is an input selector, not a license
    # to rebuild the parent's evidence.  Compare it to the witnessed ordered
    # inventory, then retain the original StageRef tuples unchanged.
    ledger_check = _ref(ledger, "child ledger")
    require(ledger_check["path"] == inherited_inventory[0].path and
            ledger_check["sha256"] == inherited_inventory[0].sha256 and
            ("rows" not in ledger_check or ledger_check["rows"] == parent_identity.ledger_rows),
            "child ledger differs from ready parent")
    require(len(source_refs) == len(inherited_inventory) - 1,
            "child source closure length differs from ready parent inventory")
    for n, (source_ref, witnessed) in enumerate(zip(source_refs, inherited_inventory[1:])):
        checked = _ref(source_ref, f"child source closure {n}")
        require(checked["path"] == witnessed.path and checked["sha256"] == witnessed.sha256,
                f"child source closure {n} differs from ready parent inventory")
    inventory = list(inherited_inventory)

    dispatch = dict(sidecars)
    if parent_binding is not None:
        require(len(dispatch) == CHILD_DISPATCH_SIDECAR_COUNT,
                "child dispatch must contain exactly admission, phase, and raw permit refs")
    overlap = set(inherited_sidecars) & set(dispatch)
    require(not overlap, "child dispatch sidecar replaces inherited evidence")
    refs = dict(inherited_sidecars)
    refs.update({name: _stage_ref(root, ref, f"child dispatch sidecar {name}")
                 for name, ref in dispatch.items()})
    if live_ledger is None:
        live_ref = inherited_live_ledger
    else:
        supplied_live = _stage_ref(root, live_ledger, "child live ledger witness")
        if inherited_live_ledger is None:
            require(False, "child supplied a live ledger absent from the ready parent")
        _stage_ref_equal(supplied_live, inherited_live_ledger, "child live ledger")
        live_ref = inherited_live_ledger
    identity = dataclasses.replace(parent_identity, runtime_sha256=runtime_digest(runtime),
                                   created_monotonic=float(popen_monotonic), lock=lock_identity)
    return ChildStage(identity, graph, runtime, inventory, refs,
                      live_ledger=live_ref,
                      parent_identity_sha256=parent_identity_sha,
                      child_creator_pid=child_creator_pid, child_creator_birth=child_creator_birth,
                      child_pid=child_pid, child_birth=child_birth, lease=lease)


def assert_child_ready(root: Path | str, child: ChildStage, *, parent: ParentStage | FinalizedParentStage,
                       graph: PinnedBridgeGraph, now_monotonic: float) -> float:
    require(child.parent_identity_sha256 == parent.identity_sha256, "child parent identity differs")
    child.assert_graph(graph)
    assert_stage_current(root, parent, parent.graph)
    assert_stage_current(root, child, graph)
    remaining = child.lease.setup_remaining(now_monotonic)
    require(remaining > 0, "child startup lease expired")
    return remaining


def assert_child_ready_from_receipt(root: Path | str, child: ChildStage, *,
                                    parent_receipt_ref: Mapping[str, Any],
                                    graph: PinnedBridgeGraph,
                                    manifest_ref: Mapping[str, Any],
                                    core_identity: Mapping[str, Any],
                                    core: Mapping[str, Any],
                                    dispatch_sidecars: Mapping[str, Mapping[str, Any]],
                                    now_monotonic: float,
                                    stage_bridge: object | None = None) -> float:
    """Validate a child against a compact parent witness at both process edges.

    ``parent_receipt_ref`` contains no runtime authority.  The actual opaque
    ``child`` and its exact pinned ``graph`` are mandatory, while the receipt
    supplies only stable path/SHA/stat/identity evidence.  This is the API
    used by admission immediately after child creation and again immediately
    before ``run_group``.
    """
    require(type(child) is ChildStage, "child-ready guard needs an opaque ChildStage")
    require(type(graph) is PinnedBridgeGraph, "child-ready guard needs a pinned graph")
    if stage_bridge is not None:
        guard = getattr(stage_bridge, "assert_child_ready_from_receipt", None)
        require(guard is assert_child_ready_from_receipt,
                "child-ready guard must use the exact pinned bridge module")
    root = Path(root).resolve()
    receipt = _read_compact_parent(root, parent_receipt_ref, core=core,
                                   expected_index=child.identity.index)
    require(receipt["manifest_ref"] == dict(manifest_ref),
            "child parent receipt escaped the bound manifest")
    require(receipt["core_identity"] == dict(core_identity),
            "child parent receipt escaped the bound core identity")
    require(child.parent_identity_sha256 == receipt["stage_identity_sha256"],
            "child parent identity differs from the compact parent witness")
    child.assert_graph(graph)
    require(child.identity.index == receipt["stage_index"],
            "child stage index differs from the compact parent witness")
    identity = receipt["stage_identity"]
    require(receipt["source_commit"] == _core_source_commit(core) and
            receipt["plan_commit"] == _core_plan_commit(core) and
            receipt["contract_sha256"] == _core_contract_sha(core),
            "child parent receipt is not bound to the exact current core")
    declared_core_identity = core.get("core_identity")
    if declared_core_identity is not None:
        require(declared_core_identity == dict(core_identity),
                "child parent core identity differs from the exact current core")
    stable_fields = ("source_commit", "plan_commit", "contract_sha256", "ledger_sha256",
                     "ledger_rows", "analyzer_deadline_seconds", "startup_seconds")
    for field in stable_fields:
        require(getattr(child.identity, field) == identity[field],
                f"child identity field differs from parent receipt: {field}")
    require(dataclasses.asdict(child.identity.lock) == dict(receipt["lock"]),
            "child lock identity differs from parent receipt")
    require(tuple(member.binding() for member in graph.members) ==
            tuple(receipt["graph_bindings"]),
            "child graph path/SHA tuple differs from parent receipt")
    require(graph.graph_sha256 == receipt["graph_sha256"],
            "child graph digest differs from parent receipt")
    graph.assert_complete({member.name: member.module_object for member in graph.members})

    expected_inventory = tuple(receipt["inventory_refs"])
    actual_inventory = tuple(ref.as_dict() for ref in child.inventory)
    require(actual_inventory == expected_inventory,
            "child inventory is not the exact ordered parent receipt inventory")
    require(child.live_ledger is None if receipt["live_ledger_ref"] is None else
            child.live_ledger.as_dict() == receipt["live_ledger_ref"],
            "child live ledger differs from the parent receipt witness")
    require(isinstance(dispatch_sidecars, Mapping) and
            len(dispatch_sidecars) == CHILD_DISPATCH_SIDECAR_COUNT,
            "child dispatch must contain exactly three current sidecars")
    inherited_names = tuple(receipt["sidecars"])
    require(not set(dispatch_sidecars) & set(inherited_names),
            "child dispatch sidecar replaces inherited evidence")
    expected_names = tuple(sorted(set(inherited_names) | set(dispatch_sidecars)))
    require(tuple(sorted(child.sidecars)) == expected_names,
            "child sidecar keyset is not the exact inherited/dispatch union")
    for name in inherited_names:
        require(child.sidecars[name].as_dict() == receipt["sidecar_refs"][name],
                f"child inherited sidecar changed: {name}")
    for name, ref in dispatch_sidecars.items():
        checked = _stage_ref(root, ref, f"child dispatch sidecar {name}")
        _stage_ref_equal(child.sidecars[name], checked, f"child dispatch sidecar {name}")
    assert_stage_current(root, child, graph)
    remaining = child.lease.setup_remaining(now_monotonic)
    require(remaining > 0, "child startup lease expired")
    # Keep the same scalar return contract as ``assert_child_ready``.  The
    # admission wrapper owns the public diagnostic; returning a mapping here
    # would make the wrapper unable to distinguish a valid lease from an
    # untrusted caller-supplied result.
    return remaining


def write_compact_stage_receipt(root: Path | str, path: str, stage: _OpaqueStage,
                                *, status: str, sidecar_names: Sequence[str],
                                manifest_ref: Mapping[str, Any] | None = None,
                                core_identity: Mapping[str, Any] | None = None,
                                predecessor_receipt_ref: Mapping[str, Any] | None = None,
                                core: Mapping[str, Any] | None = None) -> dict[str, str]:
    require(status in {"parent-stage-verified", "child-stage-verified", "successor-stage-verified"},
            "unknown stage receipt status")
    require(type(stage.identity.index) is int and 0 <= stage.identity.index < PARENT_STAGE_COUNT,
            "stage receipt index is malformed")
    require(tuple(sidecar_names) == tuple(sorted(set(sidecar_names))) and
            tuple(sidecar_names) == tuple(sorted(stage.sidecars)),
            "stage sidecars are not deterministic or complete")
    require(isinstance(manifest_ref, Mapping) and isinstance(core_identity, Mapping),
            "compact stage receipt needs exact manifest and core bindings")
    require(set(manifest_ref) == {"path", "sha256"}, "manifest receipt binding has unexpected fields")
    _sha(manifest_ref.get("sha256"), "manifest receipt sha256")
    _relative(manifest_ref.get("path"), "manifest receipt path")
    if core is not None:
        require(stage.identity.source_commit == _core_source_commit(core) and
                stage.identity.plan_commit == _core_plan_commit(core) and
                stage.identity.contract_sha256 == _core_contract_sha(core),
                "stage receipt is not bound to the exact current core")
        declared_core_identity = core.get("core_identity")
        if declared_core_identity is not None:
            require(dict(core_identity) == declared_core_identity,
                    "stage receipt core identity differs from the exact current core")
        declared_manifest_ref = core.get("manifest_ref")
        if declared_manifest_ref is not None:
            require(dict(manifest_ref) == declared_manifest_ref,
                    "stage receipt manifest differs from the exact current core")
    expected_path = _canonical_stage_receipt_path(core, stage.identity.index)
    if core is not None:
        require(path == expected_path, "stage receipt path is not the canonical core path")
    else:
        # Qualification-only witnesses predate the stage-specific core and
        # may live at their reviewed evidence path.  They still receive all
        # normal relative-path/symlink/hash checks.  Production parent
        # receipts always pass ``core`` and therefore use the canonical
        # stage-{index:02d}.json path above.
        _relative(path, "stage receipt path")
    if stage.identity.index == 0:
        require(type(stage) is ParentStage and
                status == "parent-stage-verified" and predecessor_receipt_ref is None and
                not hasattr(stage, "predecessor_identity_sha256"),
                "stage zero cannot carry predecessor metadata")
        predecessor_identity_sha256 = None
    else:
        require(type(stage) is FinalizedParentStage and
                status == "successor-stage-verified" and
                isinstance(predecessor_receipt_ref, Mapping) and
                set(predecessor_receipt_ref) == {"path", "sha256"},
                "successor receipt needs one exact predecessor receipt ref")
        predecessor_identity_sha256 = getattr(stage, "predecessor_identity_sha256", None)
        _sha(predecessor_identity_sha256, "successor predecessor identity sha256")
        predecessor_receipt_ref = dict(predecessor_receipt_ref)
        predecessor = _read_compact_parent(Path(root).resolve(), predecessor_receipt_ref, core=core,
                                           expected_index=stage.identity.index - 1,
                                           validate_live_current=False)
        require(predecessor["stage_identity_sha256"] == predecessor_identity_sha256,
                "successor predecessor identity does not match its receipt")
    stage_identity = dataclasses.asdict(stage.identity)
    stage_identity["lock"] = dataclasses.asdict(stage.identity.lock)
    inventory_refs = [ref.as_dict() for ref in stage.inventory]
    sidecar_refs = {name: stage.sidecars[name].as_dict() for name in sidecar_names}
    value = {"schema": SCHEMA + "/stage-receipt", "status": status,
             "stage_receipt_path": path, "stage_index": stage.identity.index,
             "stage_identity_sha256": stage.identity_sha256,
             "stage_identity": stage_identity,
             "ledger_sha256": stage.identity.ledger_sha256, "ledger_rows": stage.identity.ledger_rows,
             "runtime_sha256": stage.identity.runtime_sha256,
             "graph_sha256": stage.graph.graph_sha256,
             "graph_members": [member.public() for member in stage.graph.members],
             "graph_bindings": [member.binding() for member in stage.graph.members],
             "source_commit": stage.identity.source_commit,
             "plan_commit": stage.identity.plan_commit,
             "contract_sha256": stage.identity.contract_sha256,
             "lock": dataclasses.asdict(stage.identity.lock),
             "ledger_ref": inventory_refs[0], "inventory_refs": inventory_refs,
             "live_ledger_ref": None if stage.live_ledger is None else stage.live_ledger.as_dict(),
             "manifest_ref": dict(manifest_ref), "core_identity": dict(core_identity),
             "sidecars": list(sidecar_names), "sidecar_refs": sidecar_refs,
             "predecessor_identity_sha256": predecessor_identity_sha256,
             "predecessor_receipt_ref": predecessor_receipt_ref}
    root = Path(root).resolve()
    target = _path(root, path, "stage receipt path")
    target.parent.mkdir(parents=True, exist_ok=True)
    raw = canonical_json(value)
    try:
        with target.open("xb") as handle:
            handle.write(raw)
    except FileExistsError as exc:
        raise FrozenBridge17Error("stage receipt already exists; retry is forbidden") from exc
    return {"path": path, "sha256": sha256(raw)}


def validate_sidecar_transition(*, allowed: Iterable[str], present: Iterable[str],
                                future: Iterable[str] = (), required: Iterable[str] = ()) -> None:
    allowed_set, present_set, future_set, required_set = set(allowed), set(present), set(future), set(required)
    require(required_set <= allowed_set, "required sidecar is outside deterministic allowlist")
    require(not future_set - allowed_set, "future sidecar is outside deterministic allowlist")
    require(present_set <= allowed_set, "unexpected sidecar in stage inventory")
    require(required_set <= present_set, "required sidecar is missing")
    require(not future_set & present_set, "future sidecar is already present")


def validate_resource_sample(sample: ResourceSample, *, free_floor: int, working_cap: int,
                             scratch_cap: int, retention_cap: int) -> None:
    require(sample.satisfies(free_floor=free_floor, working_cap=working_cap,
                             scratch_cap=scratch_cap, retention_cap=retention_cap),
            "fresh resource sample violates unchanged guard")


def validate_lease_progress(lease: Lease, *, now_monotonic: float, registered_deadline_seconds: float) -> float:
    require(lease.registered_deadline_seconds == registered_deadline_seconds,
            "registered analyzer deadline changed")
    remaining = lease.setup_remaining(now_monotonic)
    require(remaining > 0, "registered startup lease expired")
    return remaining


def build_parent_sequence(root: Path | str, stage_specs: Sequence[Mapping[str, Any]]) -> list[ParentStage]:
    """Materialize the 21 parent states from already verified actual inputs.

    ``stage_specs`` contains the runtime object and complete pinned graph
    returned by one actual replay per state.  This function does not call a
    loader, reload a bridge, or manufacture a context from a receipt.
    """
    require(len(stage_specs) == PARENT_STAGE_COUNT, "exactly 21 parent stage inputs are required")
    stages: list[ParentStage] = []
    for index, spec in enumerate(stage_specs):
        required = {"ledger", "runtime", "graph", "source_commit", "plan_commit", "contract_sha256",
                    "lock", "sidecars", "source_refs", "analyzer_deadline_seconds"}
        require(required <= set(spec), f"parent stage {index} is missing typed actual inputs")
        stage = build_parent_stage(root, index=index, **dict(spec))
        if stages:
            require(stage.identity.ledger_rows == stages[-1].identity.ledger_rows + 1,
                    f"parent stage {index} did not append one terminal row")
            require(stage.identity.lock == stages[-1].identity.lock,
                    f"parent stage {index} changed the canonical lock identity")
        stages.append(stage)
    return stages


def build_child_sequence(root: Path | str, child_specs: Sequence[Mapping[str, Any]],
                         parent_stages: Sequence[ParentStage | FinalizedParentStage]) -> list[ChildStage]:
    """Build exactly one fresh child runtime stage after each ready phase."""
    require(len(child_specs) == CHILD_STAGE_COUNT and len(parent_stages) == PARENT_STAGE_COUNT,
            "BF14 child/parent cardinalities are not exact")
    children: list[ChildStage] = []
    for index, spec in enumerate(child_specs):
        require(spec.get("parent") is parent_stages[index],
                f"child stage {index} is not bound to its parent stage")
        child = build_child_stage(root, **dict(spec))
        require(child.identity.index == index, f"child stage {index} has a non-deterministic index")
        children.append(child)
    return children


def load_runtime_stage(root: Path | str, *, graph: PinnedBridgeGraph, runtime_loader: Any,
                       mode: str, core_identity: Mapping[str, Any],
                       ledger_bytes: bytes | None = None) -> tuple[object, str]:
    """Invoke one graph-owned runtime loader exactly once and retain its object.

    A caller cannot supply an arbitrary callback.  The callable must be the
    ``load_runtime_context`` export of one of the graph's pinned modules; the
    graph object is the authority for both the source bytes and the module
    identity.  The helper below is preferred by production callers.
    """
    require(not isinstance(runtime_loader, (str, bytes, Mapping)) and callable(runtime_loader),
            "runtime loader must be a graph-owned callable")
    owner_names = []
    for member in graph.members:
        candidate = getattr(member.module_object, "load_runtime_context", None)
        if candidate is not None and getattr(candidate, "__self__", None) is getattr(runtime_loader, "__self__", None) \
                and getattr(candidate, "__func__", candidate) is getattr(runtime_loader, "__func__", runtime_loader):
            owner_names.append(member.name)
    require(len(owner_names) == 1, "runtime loader is not the pinned graph loader")
    parameters = inspect.signature(runtime_loader).parameters
    kwargs: dict[str, Any] = {"mode": mode, "graph": graph}
    if "core" in parameters:
        kwargs["core"] = core_identity
    else:
        require(graph.fixture_only and "core_identity" in parameters,
                "production runtime loader lacks the exact core argument")
        kwargs["core_identity"] = core_identity
    if "ledger_bytes" in parameters:
        kwargs["ledger_bytes"] = ledger_bytes
    else:
        require(graph.fixture_only and ledger_bytes is None,
                "production runtime loader lacks the exact ledger argument")
    # Fixture loaders intentionally have a small signature.  The production
    # bridge loader accepts the root so it can bind every reviewed input from
    # the same checkout; inspect only the already graph-owned callable and do
    # not catch arbitrary TypeErrors from inside it.
    if "root" in parameters:
        kwargs["root"] = Path(root).resolve()
    runtime = runtime_loader(**kwargs)
    require(runtime is not None and not isinstance(runtime, (str, bytes, Mapping)),
            "runtime loader returned a serialized or missing context")
    return runtime, runtime_digest(runtime)


def load_stage_runtime(root: Path | str, *, graph: PinnedBridgeGraph, mode: str,
                       core_identity: Mapping[str, Any],
                       ledger_bytes: bytes | None = None) -> tuple[object, str]:
    """Load a lossless runtime context through the pinned bridge member."""
    loader = getattr(graph.module("bridge17"), "load_runtime_context", None)
    require(callable(loader), "pinned bridge graph lacks load_runtime_context")
    return load_runtime_stage(root, graph=graph, runtime_loader=loader, mode=mode,
                              core_identity=core_identity, ledger_bytes=ledger_bytes)


def runtime_objects(stage: _OpaqueStage) -> object:
    """Return the exact in-process runtime object owned by ``stage``.

    This is intentionally not a JSON or mapping conversion.  Cross-process
    callers use the compact stage receipt and perform their own actual child
    validation; they cannot manufacture a runtime by passing receipt fields
    back into this function.
    """
    require(isinstance(stage, _OpaqueStage), "runtime_objects needs an opaque stage")
    return stage.runtime


def _core_graph_inputs(core: Mapping[str, Any]) -> Mapping[str, Mapping[str, Any]]:
    refs = core.get("runtime_module_graph", core.get("graph_refs", core.get("frozen_graph_refs")))
    require(isinstance(refs, Mapping), "core has no exact frozen graph refs")
    # JSON object order is not semantic: canonical serialization sorts its
    # keys. Reconstruct the fixed role order without dropping any sealed alias.
    require(all(isinstance(name, str) for name in refs), "graph has a non-string module name")
    require(set(REQUIRED_GRAPH_NAMES) <= set(refs), "graph omits a required runtime role")
    names = REQUIRED_GRAPH_NAMES + tuple(sorted(set(refs) - set(REQUIRED_GRAPH_NAMES)))
    _validate_graph_names(names)
    return {name: refs[name] for name in names}


def _validate_typed_source_inputs(value: object, label: str) -> list[dict[str, str]]:
    """Validate the canonical release-input roster without changing it.

    ``source_inputs`` is a provenance-bearing roster, not a stage-reference
    list.  Keep this check at the one boundary where the canonical core enters
    the frozen builders; the generic ``_ref`` contract remains deliberately
    strict and is never widened to admit ``role``.
    """
    require(isinstance(value, Sequence) and not isinstance(value, (str, bytes)),
            f"{label} is not an ordered source roster")
    require(bool(value), f"{label} is empty")
    result: list[dict[str, str]] = []
    paths: set[str] = set()
    for index, entry in enumerate(value):
        item_label = f"{label} {index}"
        require(isinstance(entry, Mapping) and set(entry) == {"path", "sha256", "role"},
                f"{item_label} is not an exact typed release input")
        require(entry.get("role") == "release-input",
                f"{item_label} has an invalid role")
        path = entry.get("path")
        _relative(path, f"{item_label} path")
        digest = _sha(entry.get("sha256"), f"{item_label} sha256")
        require(path not in paths, f"{label} repeats a path")
        paths.add(path)
        # This is a projection only.  The raw ordered record remains owned by
        # the core/contract and is compared byte-for-byte at the contract
        # boundary before this strict stage-reference shape is returned.
        result.append({"path": path, "sha256": digest})
    return result


def _read_bound_source_contract(root: Path, contract_ref: object, label: str) -> Mapping[str, Any]:
    """Read the exact hash-bound contract selected by one source context."""
    checked = _ref(contract_ref, f"{label} contract")
    raw, _ = stable_read(root, checked, f"{label} contract")
    try:
        value = json.loads(raw)
    except (TypeError, ValueError) as exc:
        raise FrozenBridge17Error(f"{label} contract is not JSON") from exc
    require(isinstance(value, Mapping), f"{label} contract is not an object")
    return value


def _canonical_source_refs(root: Path, owner: Mapping[str, Any], label: str) -> list[dict[str, str]]:
    """Bind a typed source roster to its own contract, then project refs."""
    entries = owner.get("source_inputs")
    require(entries is not None, f"{label} has no source_inputs")
    projected = _validate_typed_source_inputs(entries, f"{label} source_inputs")
    contract_ref = owner.get("contract")
    require(contract_ref is not None, f"{label} contract is missing")
    contract = _read_bound_source_contract(root, contract_ref, label)
    contract_entries = contract.get("source_inputs")
    _validate_typed_source_inputs(contract_entries, f"{label} contract source_inputs")
    require(entries == contract_entries,
            f"{label} source_inputs differ from its hash-bound contract")
    source_commit = owner.get("source_commit")
    require(isinstance(source_commit, str) and source_commit,
            f"{label} source_commit is missing")
    require(contract.get("source_commit") == source_commit,
            f"{label} source_commit differs from its hash-bound contract")
    return projected


def _core_source_refs(root: Path, core: Mapping[str, Any]) -> Sequence[Mapping[str, Any]]:
    """Return strict stage refs from an explicit fixture or typed core roster.

    Explicit ``source_refs`` is the compatibility/fixture branch and remains
    strict ``_ref`` input.  Canonical production ``source_inputs`` and the
    continuation fallback each bind their own contract before projection;
    neither can accidentally reuse the replacement contract for continuation.
    """
    if "source_refs" in core:
        refs = core["source_refs"]
        require(isinstance(refs, Sequence) and not isinstance(refs, (str, bytes)),
                "core source_refs is not an ordered fixture closure")
        return [_ref(value, f"core source_refs {index}") for index, value in enumerate(refs)]
    if "source_inputs" in core:
        return _canonical_source_refs(root, core, "core")
    continuation = core.get("continuation")
    require(isinstance(continuation, Mapping), "core has no typed source closure")
    return _canonical_source_refs(root, continuation, "continuation")


def _core_contract_sha(core: Mapping[str, Any]) -> str:
    value = core.get("contract_sha256")
    if value is None and isinstance(core.get("contract"), Mapping):
        value = core["contract"].get("sha256")
    continuation = core.get("continuation")
    if value is None and isinstance(continuation, Mapping) and isinstance(continuation.get("contract"), Mapping):
        value = continuation["contract"].get("sha256")
    _sha(value, "core contract sha256")
    return value


def _core_source_commit(core: Mapping[str, Any]) -> str:
    value = core.get("source_commit")
    continuation = core.get("continuation")
    if value is None and isinstance(continuation, Mapping):
        value = continuation.get("source_commit")
    require(isinstance(value, str), "core source commit is missing")
    return value


def _core_plan_commit(core: Mapping[str, Any]) -> str:
    value = core.get("plan_commit")
    continuation = core.get("continuation")
    if value is None and isinstance(continuation, Mapping):
        value = continuation.get("plan_commit")
    require(isinstance(value, str), "core plan commit is missing")
    return value


def _core_deadline(core: Mapping[str, Any]) -> float:
    value = core.get("analyzer_deadline_seconds")
    continuation = core.get("continuation")
    if value is None and isinstance(continuation, Mapping):
        value = continuation.get("analyzer_deadline_seconds")
    if value is None and isinstance(core.get("resource_policy"), Mapping):
        value = core["resource_policy"].get("minimum_replacement_seconds")
    require(type(value) in {int, float} and value > 0, "core analyzer deadline is missing")
    return float(value)


def _core_startup(core: Mapping[str, Any]) -> float:
    value = core.get("startup_seconds")
    if value is None and isinstance(core.get("resource_policy"), Mapping):
        value = core["resource_policy"].get("startup_seconds")
    return STARTUP_SECONDS if value is None else float(value)


def _load_bound_ledger_runtime(root: Path, graph: PinnedBridgeGraph,
                              core: Mapping[str, Any], ledger_ref: Mapping[str, Any],
                              mode: str) -> object:
    """Validate precisely the immutable ledger claimed by the new stage."""
    raw, metadata = stable_read(root, ledger_ref, "runtime ledger snapshot")
    require(type(ledger_ref.get("rows")) is int and
            len(raw.splitlines()) == ledger_ref["rows"],
            "runtime ledger snapshot row count differs")
    runtime, _ = load_stage_runtime(root, graph=graph, mode=mode,
                                    core_identity=core, ledger_bytes=raw)
    require(isinstance(runtime, ActualRuntimeContext),
            "production ledger runtime is not the actual opaque context")
    context = runtime.objects.get("bridge_context")
    mixed = runtime.objects.get("mixed_context")
    require(isinstance(context, Mapping) and context.get("ledger_sha256") == ledger_ref["sha256"],
            "actual validator used a different ledger snapshot")
    require(isinstance(mixed, Mapping) and
            isinstance(mixed.get("rows"), list) and len(mixed["rows"]) == ledger_ref["rows"] and
            context.get("ledger_rows") == ledger_ref["rows"],
            "actual mixed runtime does not retain the exact ledger snapshot")
    require(stable_metadata(root, {**ledger_ref, "stat": metadata}, "runtime ledger snapshot") == metadata,
            "runtime ledger snapshot changed during validation")
    return runtime


def create_parent_stage(root: Path | str, core: Mapping[str, Any], manifest_ref: Mapping[str, Any],
                        index: int, lock_identity: LockIdentity, ledger_ref: Mapping[str, Any],
                        sidecars: Mapping[str, Mapping[str, Any]] | None = None,
                        predecessor: ParentStage | FinalizedParentStage | None = None,
                        host_modules: Mapping[str, object] | None = None,
                        mode: str = "before", graph: PinnedBridgeGraph | None = None
                        , live_ledger: Mapping[str, Any] | None = None
                        ) -> ParentStage | SuccessorStageDraft:
    """Create an actual parent stage through one pinned validation call.

    Host production callers pass the modules already executing the command;
    no duplicate import is allowed.  With a predecessor this is the single
    append-only successor transition: the same pinned graph is reused and a
    fresh graph-owned runtime is produced for the new immutable ledger.
    """
    root = Path(root).resolve()
    graph_refs = _core_graph_inputs(core)
    if graph is None:
        if predecessor is not None:
            graph = predecessor.graph
            if host_modules is not None:
                supplied = bind_graph(root, graph_refs, host_modules)
                require(tuple(m.binding() for m in supplied.members) ==
                        tuple(m.binding() for m in graph.members),
                        "successor host graph differs from predecessor graph")
        elif host_modules is None:
            graph = load_graph(root, graph_refs)
        else:
            graph = bind_graph(root, graph_refs, host_modules)
    elif predecessor is not None:
        predecessor.assert_graph(graph)
    stable_read(root, manifest_ref, "stage manifest")
    runtime = _load_bound_ledger_runtime(root, graph, core, ledger_ref, mode)
    if live_ledger is None and root == ROOT:
        live_ledger = {"path": "reports/releases/v0.9.2/ledger-v1.jsonl",
                       "sha256": ledger_ref["sha256"]}
    ledger = dict(ledger_ref)
    require(type(ledger.get("rows")) is int and ledger["rows"] > 0,
            "stage ledger ref needs a positive row count")
    source_refs = list(_core_source_refs(root, core))
    common = dict(root=root, index=index, runtime=runtime, graph=graph,
                  source_commit=_core_source_commit(core), plan_commit=_core_plan_commit(core),
                  contract_sha256=_core_contract_sha(core), lock=lock_identity,
                  sidecars={} if sidecars is None else sidecars, source_refs=source_refs,
                  analyzer_deadline_seconds=_core_deadline(core), startup_seconds=_core_startup(core),
                  live_ledger=live_ledger)
    if predecessor is None:
        return build_parent_stage(ledger=ledger, **common)
    return build_successor_stage(root, predecessor=predecessor, index=index, ledger_after=ledger,
                                 **{key: value for key, value in common.items()
                                    if key not in {"root", "index", "lock"}})


def create_child_stage(root: Path | str, core: Mapping[str, Any], manifest_ref: Mapping[str, Any],
                       parent_receipt_ref: ParentStage | FinalizedParentStage | Mapping[str, Any],
                       lock_identity: LockIdentity, lease: Lease,
                       child_identity: Mapping[str, Any], ledger_ref: Mapping[str, Any],
                       sidecars: Mapping[str, Mapping[str, Any]] | None = None,
                       host_modules: Mapping[str, object] | None = None,
                       mode: str = "after", graph: PinnedBridgeGraph | None = None,
                       live_ledger: Mapping[str, Any] | None = None) -> ChildStage:
    """Create a child stage with one fresh actual replay after its ready gate."""
    root = Path(root).resolve()
    parent_stage = parent_receipt_ref if isinstance(parent_receipt_ref, (ParentStage, FinalizedParentStage)) else None
    parent_binding = None if parent_stage is not None else _read_compact_parent(
        root, parent_receipt_ref, core=core)
    if parent_binding is not None:
        expected_core = core.get("core_identity", core.get("manifest_ref"))
        if expected_core is not None:
            require(parent_binding.get("core_identity") == expected_core,
                    "compact parent receipt belongs to another core")
        require(parent_binding.get("manifest_ref") == manifest_ref,
                "compact parent receipt belongs to another manifest")
    graph_refs = _core_graph_inputs(core)
    if graph is None:
        graph = load_graph(root, graph_refs) if host_modules is None else bind_graph(root, graph_refs, host_modules)
    stable_read(root, manifest_ref, "child manifest")
    runtime = _load_bound_ledger_runtime(root, graph, core, ledger_ref, mode)
    if live_ledger is None and root == ROOT:
        live_ledger = {"path": "reports/releases/v0.9.2/ledger-v1.jsonl",
                       "sha256": ledger_ref["sha256"]}
    require(lease.popen_monotonic >= 0, "child lease is malformed")
    require(isinstance(child_identity, Mapping), "child identity is malformed")
    required = {"creator_pid", "creator_birth", "pid", "birth"}
    require(set(child_identity) == required, "child identity fields are not exact")
    return build_child_stage(
        root, parent=parent_stage, parent_binding=parent_binding, runtime=runtime, graph=graph,
        source_refs=list(_core_source_refs(root, core)),
        child_creator_pid=child_identity["creator_pid"],
        child_creator_birth=child_identity["creator_birth"],
        child_pid=child_identity["pid"], child_birth=child_identity["birth"],
        analyzer_deadline_seconds=lease.registered_deadline_seconds,
        popen_monotonic=lease.popen_monotonic,
        sidecars={} if sidecars is None else sidecars, ledger=dict(ledger_ref),
        lock_identity=lock_identity, live_ledger=live_ledger)


@contextlib.contextmanager
def stage_scope(root: Path | str, stage: _OpaqueStage, graph: PinnedBridgeGraph) -> Any:
    """Yield the opaque stage only while its graph and files remain stable."""
    assert_stage_current(root, stage, graph)
    try:
        yield stage
    finally:
        # Re-checking metadata after a consumer is intentional.  It detects a
        # sidecar/source mutation even when the consumer raised an exception.
        assert_stage_current(root, stage, graph)


def execute(*args: Any, **kwargs: Any) -> None:
    raise FrozenBridge17Error("frozen bridge is validation-only; execution belongs to supervisor-14")


if __name__ == "__main__":
    raise SystemExit("frozen bridge 09 is a library; production execution is disabled")
