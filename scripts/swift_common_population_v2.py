"""Versioned common-population loader and private v1 engine composition.

The normal v1 runner and report modules remain byte-for-byte untouched.  This
module supplies their existing ``load_population`` dependency through private
module instances and projects only the exact Swift rows in the v0.9.0 union.
"""
from __future__ import annotations

import builtins
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POPULATION_PATH = "populations/v0.9.0.json"
RELEASE_PLAN_PATH = "reports/releases/v0.9.0/plan.json"
SWIFT_BASELINE_PATH = "populations/swift-synthetic-v3.json"
EXPECTED_COMMON_CASES = 1108
EXPECTED_SWIFT_CASES = 108
COMMON_OUTPUTS = {
    "codeql": "reports/raw/swift-common-v2",
    "joern": "reports/raw/joern-common-v2",
}
_PRIVATE_ENGINES = {}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _repo_file(root, relative):
    require(isinstance(relative, str) and relative, "missing repository path")
    path = Path(relative)
    require(not path.is_absolute() and ".." not in path.parts, "unsafe repository path")
    result = Path(root) / path
    require(result.is_file() and result.resolve().is_relative_to(Path(root).resolve()), "missing or escaped repository file: " + relative)
    return result


def ref(root, path):
    path = Path(path)
    return {"path": path.relative_to(Path(root)).as_posix(), "sha256": sha(path)}


def _check_rows(rows, label):
    require(isinstance(rows, list), label + " rows are missing")
    ids, paths = set(), set()
    for row in rows:
        require(isinstance(row, dict), label + " row is invalid")
        case_id, path = row.get("id"), row.get("path")
        require(isinstance(case_id, str) and case_id and case_id not in ids, "duplicate or missing " + label + " case id")
        require(isinstance(path, str) and path and path not in paths, "duplicate or missing " + label + " case path")
        ids.add(case_id)
        paths.add(path)
    return ids


def validate_swift_projection(common_rows, swift_rows, common_swift_ids):
    """Require the common manifest's Swift projection to equal the v3 roster."""
    common_ids = _check_rows(common_rows, "common population")
    swift_ids = _check_rows(swift_rows, "Swift baseline")
    require(len(common_rows) == EXPECTED_COMMON_CASES, "exact common 1108 population required")
    require(len(swift_rows) == EXPECTED_SWIFT_CASES, "exact Swift 108 baseline required")
    require(common_swift_ids == swift_ids, "Swift projection membership mismatch")
    projected = {row["id"]: row for row in common_rows if row["id"] in common_swift_ids}
    expected = {row["id"]: row for row in swift_rows}
    require(set(projected) == common_swift_ids, "Swift projection membership mismatch")
    require(projected == expected, "Swift projection row mismatch")
    require(common_ids >= swift_ids, "Swift baseline case missing from common population")
    return [row for row in common_rows if row["id"] in swift_ids]


def load_common_population(root=ROOT):
    """Verify all common case/fixture bytes and return its exact Swift slice."""
    root = Path(root).resolve()
    population_file = _repo_file(root, POPULATION_PATH)
    plan_file = _repo_file(root, RELEASE_PLAN_PATH)
    swift_file = _repo_file(root, SWIFT_BASELINE_PATH)
    population = read(population_file)
    release_plan = read(plan_file)
    swift_baseline = read(swift_file)

    require(population.get("population") == "v0.9.0", "v0.9.0 common population required")
    require(isinstance(population.get("fixture_revision"), str), "common fixture revision missing")
    population_sha = sha(population_file)
    require(release_plan.get("population") == {"path": POPULATION_PATH, "sha256": population_sha}, "common population digest differs from v0.9.0 plan")
    require(release_plan.get("fixture_revision") == population["fixture_revision"], "common fixture revision differs from v0.9.0 plan")
    require(swift_baseline.get("population") == "swift-synthetic-v3", "Swift v3 projection baseline required")

    common_rows = population.get("cases")
    swift_rows = swift_baseline.get("cases")
    _check_rows(common_rows, "common population")
    baseline_ids = _check_rows(swift_rows, "Swift baseline")
    require(len(common_rows) == EXPECTED_COMMON_CASES, "exact common 1108 population required")
    require(len(swift_rows) == EXPECTED_SWIFT_CASES, "exact Swift 108 baseline required")

    revision = hashlib.sha256()
    common_swift_ids = set()
    cases_by_id = {}
    for selected in sorted(common_rows, key=lambda item: item["path"]):
        case_path = _repo_file(root, selected["path"])
        case_bytes = case_path.read_bytes()
        require(hashlib.sha256(case_bytes).hexdigest() == selected.get("sha256"), "case bytes changed: " + selected["path"])
        case = json.loads(case_bytes)
        case_id = selected["id"]
        require(case.get("id") == case_id, "case identity mismatch: " + case_id)
        for field in ("track", "model_profile", "score_tier", "template_id", "polarity"):
            require(case.get(field) == selected.get(field), "population metadata mismatch: " + field + ": " + case_id)
        if case.get("language") == "swift":
            common_swift_ids.add(case_id)

        fixture_rows = selected.get("fixture_digests")
        require(isinstance(fixture_rows, list), "fixture digest list missing: " + case_id)
        fixtures = {row.get("path"): row.get("sha256") for row in fixture_rows if isinstance(row, dict)}
        require(len(fixtures) == len(fixture_rows), "duplicate or malformed fixture digest: " + case_id)
        expected_fixtures = {str(Path(selected["path"]).parent / name) for name in case.get("fixture_files", [])}
        require(set(fixtures) == expected_fixtures, "fixture membership mismatch: " + case_id)

        revision.update(selected["path"].encode())
        revision.update(case_bytes)
        for name in case["fixture_files"]:
            fixture_path = str(Path(selected["path"]).parent / name)
            fixture = _repo_file(root, fixture_path)
            fixture_bytes = fixture.read_bytes()
            require(hashlib.sha256(fixture_bytes).hexdigest() == fixtures[fixture_path], "fixture bytes changed: " + fixture_path)
            revision.update(name.encode())
            revision.update(fixture_bytes)
        cases_by_id[case_id] = case

    computed_revision = "sha256:" + revision.hexdigest()
    require(population["fixture_revision"] == computed_revision, "common fixture revision mismatch")
    projected_rows = validate_swift_projection(common_rows, swift_rows, common_swift_ids)
    require(common_swift_ids == baseline_ids, "Swift case language projection mismatch")
    projected_cases = {case_id: cases_by_id[case_id] for case_id in sorted(common_swift_ids)}
    projected_population = dict(population)
    projected_population["cases"] = projected_rows
    return projected_population, common_rows, projected_rows, projected_cases, population_sha


def load_population(root=ROOT):
    """Drop-in v1 population provider, returning only the verified Swift slice."""
    population, _all_rows, _rows, cases, digest = load_common_population(root)
    return population, cases, digest


def _configuration_key(kind):
    return "patched-codeql" if kind == "codeql" else "joern-current108"


def _wrapper_paths(kind):
    return [
        "scripts/swift_common_population_v2.py",
        "scripts/run-swift-common-v2.py" if kind == "codeql" else "scripts/run-joern-common-v2.py",
        POPULATION_PATH,
        RELEASE_PLAN_PATH,
        SWIFT_BASELINE_PATH,
    ]


def bind_plan(root, plan_path, kind, wrapper_script=None):
    """Bind wrapper/population inputs and a versioned output root into a plan."""
    root = Path(root).resolve()
    require(kind in COMMON_OUTPUTS, "unknown common Swift engine")
    plan_file = _repo_file(root, plan_path)
    plan = read(plan_file)
    population, _all_rows, _rows, cases, digest = load_common_population(root)
    key = _configuration_key(kind)
    configurations = plan.get("configurations")
    require(isinstance(configurations, dict) and isinstance(configurations.get(key), list), "v1 prospective configuration missing")

    references = configurations[key]
    known = {reference.get("path") for reference in references if isinstance(reference, dict)}
    for relative in _wrapper_paths(kind):
        path = _repo_file(root, relative)
        reference = ref(root, path)
        if relative not in known:
            references.append(reference)
            known.add(relative)

    wrapper_relative = _wrapper_paths(kind)[1]
    require(wrapper_script in (None, wrapper_relative), "wrong common v2 wrapper identity")
    wrapper_reference = next(reference for reference in references if reference["path"] == wrapper_relative)
    population_reference = {"path": POPULATION_PATH, "sha256": digest}
    swift_ids = sorted(cases)
    membership_bytes = (json.dumps(swift_ids, separators=(",", ":")) + "\n").encode()
    integration = {
        "schema": "swift-common-population-integration/v2",
        "engine": kind,
        "population": population_reference,
        "fixture_revision": population["fixture_revision"],
        "common_case_count": EXPECTED_COMMON_CASES,
        "swift_projection_count": EXPECTED_SWIFT_CASES,
        "swift_projection_sha256": hashlib.sha256(membership_bytes).hexdigest(),
        "wrapper": wrapper_reference,
    }
    plan["versioned_common_population"] = integration
    plan["output_root"] = COMMON_OUTPUTS[kind]
    plan_file.write_text(json.dumps(plan, indent=2) + "\n")

    if kind == "joern":
        controls_path = plan_file.parent / "controls.json"
        if controls_path.is_file():
            controls = read(controls_path)
            controls["plan"] = ref(root, plan_file)
            controls_path.write_text(json.dumps(controls, indent=2) + "\n")
    return plan


def verify_plan(root, plan_path, kind):
    root = Path(root).resolve()
    plan_file = _repo_file(root, plan_path)
    plan = read(plan_file)
    population, _all_rows, _rows, cases, digest = load_common_population(root)
    integration = plan.get("versioned_common_population")
    require(isinstance(integration, dict) and integration.get("schema") == "swift-common-population-integration/v2", "common v2 plan binding required")
    require(integration.get("engine") == kind, "common v2 engine mismatch")
    require(integration.get("population") == {"path": POPULATION_PATH, "sha256": digest}, "common population plan drift")
    require(integration.get("fixture_revision") == population["fixture_revision"], "common fixture revision drift")
    require(integration.get("common_case_count") == EXPECTED_COMMON_CASES and integration.get("swift_projection_count") == EXPECTED_SWIFT_CASES, "common/Swift denominator mismatch")
    require(set(plan.get("cases", {})) == set(cases), "prospective plan is not the exact Swift 108 projection")
    require(plan.get("population_sha256") == digest and plan.get("fixture_revision") == population["fixture_revision"], "v1 engine population binding mismatch")
    require(plan.get("output_root") == COMMON_OUTPUTS[kind], "common v2 output root required")

    key = _configuration_key(kind)
    references = plan.get("configurations", {}).get(key, [])
    by_path = {reference.get("path"): reference for reference in references if isinstance(reference, dict)}
    for relative in _wrapper_paths(kind):
        expected = ref(root, _repo_file(root, relative))
        require(by_path.get(relative) == expected, "common v2 configuration identity missing or changed: " + relative)
    wrapper_relative = _wrapper_paths(kind)[1]
    require(integration.get("wrapper") == by_path[wrapper_relative], "common v2 wrapper identity mismatch")
    expected_ids = sorted(cases)
    membership = (json.dumps(expected_ids, separators=(",", ":")) + "\n").encode()
    require(integration.get("swift_projection_sha256") == hashlib.sha256(membership).hexdigest(), "Swift projection membership digest mismatch")
    return plan


def _load_private_module(name, path, import_router):
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, "cannot load private v1 module: " + str(path))
    module = importlib.util.module_from_spec(spec)
    private_builtins = dict(vars(builtins))
    private_builtins["__import__"] = import_router
    module.__dict__["__builtins__"] = private_builtins
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(name, None)
        raise
    return module


def _import_router(routes):
    original = builtins.__import__

    def routed(name, globals=None, locals=None, fromlist=(), level=0):
        if level == 0 and fromlist and name in routes and routes[name] is not None:
            return routes[name]
        return original(name, globals, locals, fromlist, level)

    return routed


def _bound(root, reference):
    require(isinstance(reference, dict) and set(reference) == {'path', 'sha256'}, 'exact reference required')
    path = _repo_file(root, reference['path'])
    require(sha(path) == reference['sha256'], 'bridge reference drift: ' + reference['path'])
    return path


def _without(value, fields):
    return {k: v for k, v in value.items() if k not in fields}


def verify_common_activation(root, plan):
    """Verify original activation before admitting the exact common-population amendment."""
    import importlib
    root = Path(root).resolve()
    original = importlib.import_module('joern_normal_runner_v1')
    receipt = read(_bound(root, plan.get('activation_receipt')))
    bridge = receipt.get('common_population_bridge')
    require(isinstance(bridge, dict) and bridge.get('schema') == 'joern-common-activation-bridge/v2', 'common activation bridge required')
    old_path = 'adapters/joern/swift-normal-v1/plan-2026-09-28-04/plan.json'
    require(bridge.get('original_plan', {}).get('path') == old_path, 'original activation plan required')
    old = read(_bound(root, bridge['original_plan']))
    prior_receipt = original.verify_activation(root, old)
    # The original verifier keeps its original v3 population provider and
    # checks all controls, AST equivalence and historical execution evidence.
    population, _, _, cases, digest = load_common_population(root)
    require(plan['population_sha256'] == digest and plan['fixture_revision'] == population['fixture_revision'], 'bridge common identity mismatch')
    require(bridge.get('population') == {'path': POPULATION_PATH, 'sha256': digest}, 'bridge population reference mismatch')
    integration = plan.get('versioned_common_population')
    require(bridge.get('integration') == integration, 'bridge wrapper/projection binding mismatch')
    require(isinstance(integration, dict) and integration.get('engine') == 'joern', 'bridge integration required')
    require(set(plan['cases']) == set(old['cases']) == set(cases), 'bridge case membership mismatch')
    allowed = {'registered_at_unix_seconds', 'population_sha256', 'fixture_revision', 'execution_contract', 'configurations', 'cases', 'output_root', 'activation_receipt', 'versioned_common_population'}
    require(_without(plan, allowed) == _without(old, allowed), 'bridge changed runtime, capability policy or identity')
    require(plan['output_root'] == COMMON_OUTPUTS['joern'], 'bridge output root mismatch')
    old_contract = read(_bound(root, old['execution_contract']))
    contract = read(_bound(root, plan['execution_contract']))
    require(_without(contract, {'population_sha256', 'fixture_revision'}) == _without(old_contract, {'population_sha256', 'fixture_revision'}), 'bridge changed execution semantics')
    require(contract['population_sha256'] == digest and contract['fixture_revision'] == population['fixture_revision'], 'bridge execution contract identity')
    expected_refs = [plan['execution_contract'] if r == old['execution_contract'] else r for r in old['configurations']['joern-current108']]
    expected_refs += [ref(root, _repo_file(root, name)) for name in _wrapper_paths('joern') if name not in {r['path'] for r in expected_refs}]
    require(plan['configurations'] == {'joern-current108': expected_refs}, 'bridge configuration closure changed')
    for reference in expected_refs:
        _bound(root, reference)
    config_hash = original.configuration_hash(root, expected_refs)
    require(receipt['population_sha256'] == digest and receipt['configuration_hash'] == config_hash, 'bridge receipt identity mismatch')
    changed_receipt = {'population_sha256', 'configuration_hash', 'reviewed_at_unix_seconds', 'common_population_bridge'}
    require(_without(receipt, changed_receipt) == _without(prior_receipt, changed_receipt), 'bridge changed original activation scope or evidence')
    stamp = receipt['reviewed_at_unix_seconds']
    require(type(stamp) is int and prior_receipt['reviewed_at_unix_seconds'] <= stamp <= plan['registered_at_unix_seconds'], 'bridge chronology mismatch')
    for case_id, previous in old['cases'].items():
        current = plan['cases'][case_id]
        require(_without(current, {'decision'}) == _without(previous, {'decision'}), 'bridge capability changed: ' + case_id)
        if previous['disposition'] == 'unsupported':
            before = read(_bound(root, previous['decision']))
            after = read(_bound(root, current['decision']))
            require(_without(after, {'population_sha256', 'configuration_hash', 'reviewed_at_unix_seconds'}) == _without(before, {'population_sha256', 'configuration_hash', 'reviewed_at_unix_seconds'}), 'bridge unsupported rationale changed')
            require(after['population_sha256'] == digest and after['configuration_hash'] == config_hash, 'bridge unsupported decision identity mismatch')
            require(after['reviewed_at_unix_seconds'] == stamp, 'bridge unsupported decision chronology')
        else:
            require(current == previous, 'bridge attempted case changed')
    return receipt


def prepare_joern_bridge(root, directory):
    """Create a prospective amendment; no analyzer or historical artifact is changed."""
    import copy
    import importlib
    import time
    root = Path(root).resolve()
    directory = Path(directory).resolve()
    require(directory.is_relative_to(root / 'adapters/joern/swift-common-v2'), 'versioned Joern plan directory required')
    require(not directory.exists(), 'bridge directory already exists')
    original = importlib.import_module('joern_normal_runner_v1')
    old_path = root / 'adapters/joern/swift-normal-v1/plan-2026-09-28-04/plan.json'
    old = read(old_path)
    receipt = copy.deepcopy(original.verify_activation(root, old))
    population, _, _, _, digest = load_common_population(root)
    plan = copy.deepcopy(old)
    contract = read(_bound(root, old['execution_contract']))
    contract.update(population_sha256=digest, fixture_revision=population['fixture_revision'])
    directory.mkdir(parents=True)
    def save(name, value):
        path = directory / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, indent=2) + '\n')
        return ref(root, path)
    contract_ref = save('contract.json', contract)
    plan['execution_contract'] = contract_ref
    plan['configurations']['joern-current108'] = [contract_ref if r == old['execution_contract'] else r for r in plan['configurations']['joern-current108']]
    stamp = int(time.time())
    plan.update(population_sha256=digest, fixture_revision=population['fixture_revision'], registered_at_unix_seconds=stamp)
    save('plan.json', plan)
    relative = str((directory / 'plan.json').relative_to(root))
    plan = bind_plan(root, relative, 'joern')
    config_hash = original.configuration_hash(root, plan['configurations']['joern-current108'])
    receipt.update(population_sha256=digest, configuration_hash=config_hash, reviewed_at_unix_seconds=stamp)
    receipt['common_population_bridge'] = {'schema': 'joern-common-activation-bridge/v2', 'original_plan': ref(root, old_path), 'population': {'path': POPULATION_PATH, 'sha256': digest}, 'integration': plan['versioned_common_population']}
    for case_id, selected in plan['cases'].items():
        if selected['disposition'] == 'unsupported':
            decision = read(_bound(root, selected['decision']))
            decision.update(population_sha256=digest, configuration_hash=config_hash, reviewed_at_unix_seconds=stamp)
            selected['decision'] = save('decisions/' + case_id + '.json', decision)
    plan['activation_receipt'] = save('activation.json', receipt)
    save('plan.json', plan)
    verify_plan(root, relative, 'joern')
    verify_common_activation(root, plan)
    return plan


def private_engine(root=ROOT, kind="codeql"):
    """Return isolated v1 runner/report modules with the v2 loader injected."""
    root = Path(root).resolve()
    require(kind in COMMON_OUTPUTS, "unknown common Swift engine")
    cache_key = (str(root), kind)
    if cache_key in _PRIVATE_ENGINES:
        return _PRIVATE_ENGINES[cache_key]
    token = hashlib.sha256((str(root) + kind).encode()).hexdigest()[:12]
    if kind == "codeql":
        runner_path = root / "scripts/swift_normal_runner_v1.py"
        reporter_path = root / "scripts/swift_normal_reports_v1.py"
    else:
        runner_path = root / "scripts/joern_normal_runner_v1.py"
        reporter_path = root / "scripts/joern_normal_reports_v1.py"
    routes = {
        "swift_normal_reports_v1": None,
        "swift_normal_runner_v1": None,
        "joern_normal_reports_v1": None,
        "joern_normal_runner_v1": None,
    }
    router = _import_router(routes)
    reporter = _load_private_module("_dfb_common_v2_" + kind + "_reports_" + token, reporter_path, router)
    if kind == "codeql":
        routes["swift_normal_reports_v1"] = reporter
    else:
        routes["joern_normal_reports_v1"] = reporter
    engine = _load_private_module("_dfb_common_v2_" + kind + "_runner_" + token, runner_path, router)
    if kind == "codeql":
        routes["swift_normal_runner_v1"] = engine
    else:
        routes["joern_normal_runner_v1"] = engine
    reporter.load_population = load_population
    engine.load_population = load_population
    if kind == "codeql":
        engine.export = reporter.export
    else:
        # Preserve the historical verifier in its original population context.
        engine.verify_activation = verify_common_activation
    result = {"runner": engine, "reports": reporter}
    _PRIVATE_ENGINES[cache_key] = result
    return result


def prepare(root, directory, runtime, kind, wrapper_script):
    root = Path(root).resolve()
    directory = Path(directory).resolve()
    require(directory.is_relative_to(root / "adapters"), "common v2 plan belongs under adapters")
    engine = private_engine(root, kind)["runner"]
    engine.prepare(root, directory, runtime)
    plan_path = directory / "plan.json"
    return bind_plan(root, plan_path.relative_to(root).as_posix(), kind, wrapper_script)


def check_queries(root, plan_path, output):
    verify_plan(root, plan_path, "codeql")
    return private_engine(root, "codeql")["runner"].check_queries(Path(root).resolve(), plan_path, Path(output).resolve())


def controls(root, plan_path, control_path, output, reservation):
    verify_plan(root, plan_path, "joern")
    return private_engine(root, "joern")["runner"].controls(Path(root).resolve(), plan_path, control_path, Path(output).resolve(), reservation)


def execute(root, plan_path, output, reservation, kind):
    verify_plan(root, plan_path, kind)
    return private_engine(root, kind)["runner"].execute(Path(root).resolve(), plan_path, Path(output).resolve(), reservation)
