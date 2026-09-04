//! Reconciling a tool's own retained evidence against the benchmark's declared
//! anchors.
//!
//! Every adapter reconciles by file and marker line, never by guessing at
//! tool-internal locations. The per-language surface rules live in
//! `AnchorDialect`; the SARIF helpers are shared by every adapter that reads
//! a SARIF document.

use serde_json::Value;
use std::{collections::BTreeSet, fs, path::Path};

#[derive(Clone, Debug, PartialEq, Eq)]
pub(crate) struct SinkAnchorLocation {
    pub(crate) file: String,
    pub(crate) marker_line: u64,
    pub(crate) function_name: String,
    pub(crate) callsite_lines: BTreeSet<u64>,
}

/// Anchor reconciliation is language-neutral apart from two surface questions:
/// which function a `DFB-SINK:` marker declares, and which lines call it. One
/// dialect covers JavaScript and TypeScript, which share the surface syntax the
/// reconciler inspects; C# and Go spell both differently from ECMAScript but
/// identically to each other, so they share the second dialect's rules while
/// staying separately named populations; C and C++ declare a sink the same way
/// again but reach a member through `.`, `->`, and `::`; Rust declares it the
/// same way once more and reaches a member through `.` and `::`, but never
/// `->`. Java declares a sink as an identifier before a parameter list and
/// reaches a member through `.` alone — the same two rules as C# and Go — but
/// it stays a separately named dialect so a Java population is never reconciled
/// by a selector that happens to be spelled for another language. Python
/// declares a sink the same way again and also reaches a member through `.`
/// alone, but its comments open with `#` rather than `//`, so it needs its own
/// literal/comment stripping.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum AnchorDialect {
    Ecma,
    /// JavaScript and TypeScript as the **modeling matrix** spells them:
    /// identical to `Ecma` except that a member-qualified call —
    /// `Audit.record(v)` — counts as a callsite of `record`.
    ///
    /// No kernel needs this. Every kernel endpoint is a bare function, so
    /// `Ecma` deliberately refuses a `.`-prefixed match and cannot mistake a
    /// property access for a call to the endpoint. A modeling declaration
    /// binds a *type* and a *member*, though, so the declared sink of
    /// `dfb-template-model-declared-sink` is only ever reached through its
    /// receiver, and refusing the member form would leave that case with no
    /// resolvable sink callsite at all. This variant is used by the modeling
    /// runners and by nothing else, so no kernel reconciliation changes.
    EcmaMember,
    CSharp,
    Go,
    Cpp,
    Rust,
    Java,
    /// Java as the **modeling matrix** spells it, and the exact counterpart of
    /// `EcmaMember`: identical to `Java` except that a member-qualified call —
    /// `Audit.record(v)`, `Config.fetchRemote()`, `alpha.get("k")` — counts as
    /// a callsite of the named member.
    ///
    /// Java needs this more sharply than JavaScript does, because Java has no
    /// free functions at all: *every* declared modeling entity is a member of
    /// some type, and every callsite of one in a fixture that does not declare
    /// it is therefore written through its receiver. `Java` refuses a
    /// `.`-prefixed match, which is right for the kernels — their `dfb_sink` is
    /// a static method called bare from the same class, and `other.dfb_sink(v)`
    /// really is a different method — and wrong for a modeling declaration,
    /// which binds a type and a member as one identity. Like `EcmaMember`, this
    /// variant is used by the modeling runners and by nothing else, so no
    /// kernel reconciliation changes.
    JavaMember,
    Python,
    Ruby,
    Php,
}

impl AnchorDialect {
    /// The function name declared on the line carrying an anchor marker. The
    /// same rule resolves a `DFB-SINK:` and a `DFB-SOURCE:` declaration: both
    /// markers sit on the endpoint function's own declaration line.
    pub(crate) fn declared_function_name(self, declaration: &str, marker: &str) -> Option<String> {
        match self {
            Self::Ecma | Self::EcmaMember => ecma_function_name(declaration, marker),
            Self::CSharp
            | Self::Go
            | Self::Cpp
            | Self::Rust
            | Self::Java
            | Self::JavaMember
            | Self::Python
            | Self::Php => parameter_list_function_name(declaration, marker),
            Self::Ruby => ruby_declared_function_name(declaration, marker),
        }
    }

    pub(crate) fn is_call(self, line: &str, function_name: &str) -> bool {
        match self {
            Self::Ecma => ecma_function_call(line, function_name),
            Self::EcmaMember => ecma_member_function_call(line, function_name),
            Self::CSharp | Self::Go | Self::Java => {
                parameter_list_function_call(line, function_name)
            }
            Self::JavaMember => java_member_function_call(line, function_name),
            Self::Cpp => cpp_function_call(line, function_name),
            Self::Rust => rust_function_call(line, function_name),
            Self::Python => python_function_call(line, function_name),
            Self::Ruby => ruby_function_call(line, function_name),
            Self::Php => php_function_call(line, function_name),
        }
    }
}

/// How a dialect opens a line comment. Everything else `code_without_literals`
/// inspects — single and double quotes with backslash escapes — coincides
/// across every dialect reconciled here.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum CommentSyntax {
    DoubleSlash,
    Hash,
    /// PHP accepts both `//` and `#` as line-comment openers, and the kernel
    /// fixtures may legitimately use either.
    DoubleSlashOrHash,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum SarifAnchorMatch {
    Matched,
    Unmatched,
    Ambiguous,
}

/// Reconcile a SARIF document against the case's sink callsites and merge the
/// query's own messages into the retained diagnostics.
pub(crate) fn callsite_anchored_outcome(
    case_path: &Path,
    case: &Value,
    sarif: &Value,
    dialect: AnchorDialect,
) -> (&'static str, Vec<String>) {
    let mut diagnostics = sarif_messages(sarif);
    let (outcome, anchor_diagnostics) = sarif_anchor_outcome(case_path, case, sarif, dialect);
    diagnostics.extend(anchor_diagnostics);
    diagnostics.sort();
    diagnostics.dedup();
    (outcome, diagnostics)
}

pub(crate) fn sarif_anchor_outcome(
    case_path: &Path,
    case: &Value,
    sarif: &Value,
    dialect: AnchorDialect,
) -> (&'static str, Vec<String>) {
    if sarif_result_count(sarif) == 0 {
        return ("not-reached", Vec::new());
    }
    let sink_locations = match sink_anchor_locations(case_path, case, dialect) {
        Ok(locations) => locations,
        Err(reason) => {
            return (
                "inconclusive",
                vec![format!(
                    "cannot prove SARIF finding against sink anchor: {reason}"
                )],
            );
        }
    };
    let mut matched = 0;
    let mut unmatched = 0;
    let mut ambiguous = 0;
    for result in sarif["runs"]
        .as_array()
        .into_iter()
        .flatten()
        .flat_map(|run| run["results"].as_array().into_iter().flatten())
    {
        match sarif_result_anchor_match(result, &sink_locations) {
            SarifAnchorMatch::Matched => matched += 1,
            SarifAnchorMatch::Unmatched => unmatched += 1,
            SarifAnchorMatch::Ambiguous => ambiguous += 1,
        }
    }
    if ambiguous > 0 {
        return (
            "inconclusive",
            vec![format!(
                "{ambiguous} SARIF finding(s) have ambiguous sink-anchor locations"
            )],
        );
    }
    if matched > 0 {
        return ("reached", Vec::new());
    }
    (
        "inconclusive",
        vec![format!(
            "{unmatched} SARIF finding(s) did not match the case sink anchor"
        )],
    )
}

pub(crate) fn sink_anchor_locations(
    case_path: &Path,
    case: &Value,
    dialect: AnchorDialect,
) -> std::result::Result<Vec<SinkAnchorLocation>, String> {
    let fixture_root = case_path
        .parent()
        .ok_or_else(|| "case path has no parent".to_string())?;
    let mut locations = Vec::new();
    for anchor in case["sink_anchors"]
        .as_array()
        .ok_or_else(|| "case has no sink anchors".to_string())?
    {
        let file = anchor["file"]
            .as_str()
            .ok_or_else(|| "sink anchor lacks file".to_string())?;
        let marker = anchor["marker"]
            .as_str()
            .ok_or_else(|| "sink anchor lacks marker".to_string())?;
        let body = fs::read_to_string(fixture_root.join(file))
            .map_err(|error| format!("read sink fixture {file}: {error}"))?;
        let line = anchor_marker_line(&body, marker, anchor["line_hint"].as_u64())?;
        let declaration = body
            .lines()
            .nth(line as usize - 1)
            .ok_or_else(|| format!("sink anchor line {line} is outside {file}"))?;
        let function_name = dialect
            .declared_function_name(declaration, marker)
            .ok_or_else(|| format!("sink marker {marker:?} is not on a function declaration"))?;
        let callsite_lines = body
            .lines()
            .enumerate()
            .filter_map(|(index, candidate)| {
                let candidate_line = index as u64 + 1;
                (candidate_line != line && dialect.is_call(candidate, &function_name))
                    .then_some(candidate_line)
            })
            .collect::<BTreeSet<_>>();
        if callsite_lines.is_empty() {
            return Err(format!(
                "sink function {function_name} has no callsites in {file}"
            ));
        }
        locations.push(SinkAnchorLocation {
            file: file.to_string(),
            marker_line: line,
            function_name,
            callsite_lines,
        });
    }
    if locations.is_empty() {
        return Err("case has no resolvable sink locations".to_string());
    }
    if locations
        .iter()
        .map(|location| (&location.file, location.marker_line))
        .collect::<BTreeSet<_>>()
        .len()
        != locations.len()
    {
        return Err("case contains duplicate sink anchors".to_string());
    }
    Ok(locations)
}

/// Resolve the single line an anchor marker sits on: the declared hint when the
/// case supplies one, and otherwise the marker's only occurrence. An ambiguous
/// marker is an error rather than a guess.
pub(crate) fn anchor_marker_line(
    body: &str,
    marker: &str,
    hinted_line: Option<u64>,
) -> std::result::Result<u64, String> {
    let lines = body
        .lines()
        .enumerate()
        .filter_map(|(index, line)| line.contains(marker).then_some(index as u64 + 1))
        .collect::<Vec<_>>();
    if let Some(line) = hinted_line {
        if !lines.contains(&line) {
            return Err(format!("marker {marker:?} is not on hinted line {line}"));
        }
        return Ok(line);
    }
    if lines.len() == 1 {
        return Ok(lines[0]);
    }
    Err(format!(
        "marker {marker:?} has {} possible lines",
        lines.len()
    ))
}

pub(crate) fn ecma_function_name(line: &str, marker: &str) -> Option<String> {
    let marker_start = line.find(marker)?;
    let declaration = &line[..marker_start];
    let function_start = declaration
        .match_indices("function")
        .filter(|(start, _)| {
            let before = declaration[..*start].chars().next_back();
            let after = declaration[*start + "function".len()..].chars().next();
            !before.is_some_and(ecma_identifier_char) && !after.is_some_and(ecma_identifier_char)
        })
        .map(|(start, _)| start)
        .last()?;
    let mut name = declaration[function_start + "function".len()..].trim_start();
    if let Some(rest) = name.strip_prefix('*') {
        name = rest.trim_start();
    }
    let end = name
        .char_indices()
        .find_map(|(index, character)| (!ecma_identifier_char(character)).then_some(index))
        .unwrap_or(name.len());
    (end > 0).then(|| name[..end].to_string())
}

pub(crate) fn ecma_identifier_char(character: char) -> bool {
    character == '_' || character == '$' || character.is_ascii_alphanumeric()
}

/// The C#, Go, C, and C++ sink markers all sit on a declaration such as
/// `static void dfb_sink(int value) { } // DFB-SINK: ...` or
/// `func dfb_sink(value int) {} // DFB-SINK: ...`. In every one the declared
/// name is the identifier immediately before the parameter list.
pub(crate) fn parameter_list_function_name(declaration: &str, marker: &str) -> Option<String> {
    let marker_start = declaration.find(marker)?;
    let declaration = &declaration[..marker_start];
    let declaration = declaration.split("//").next().unwrap_or(declaration);
    let parameters = declaration.find('(')?;
    let name = declaration[..parameters].trim_end();
    let start = name
        .char_indices()
        .rev()
        .find(|(_, character)| !ascii_identifier_char(*character))
        .map(|(index, character)| index + character.len_utf8())
        .unwrap_or(0);
    let name = &name[start..];
    (!name.is_empty() && !name.starts_with(|character: char| character.is_ascii_digit()))
        .then(|| name.to_string())
}

pub(crate) fn ascii_identifier_char(character: char) -> bool {
    character == '_' || character.is_ascii_alphanumeric()
}

/// C#, Go, and Java reach a member through `.` only. Java's `::` is a method
/// reference, never a call, so it never has to be excluded here.
pub(crate) fn parameter_list_function_call(line: &str, function_name: &str) -> bool {
    member_prefixed_function_call(line, function_name, &['.'])
}

/// The modeling tier's Java rule: `parameter_list_function_call` with the `.`
/// exclusion lifted, so `Audit.record(v)` counts as a callsite of `record`
/// while `myRecord(v)` — an identifier that merely ends in the member's name —
/// still does not. The identifier boundary before the name and the `(` after it
/// are unchanged, which is what keeps a field access or a method reference from
/// matching.
pub(crate) fn java_member_function_call(line: &str, function_name: &str) -> bool {
    member_prefixed_function_call(line, function_name, &[])
}

/// Python reaches a member through `.` only, and opens a comment with `#`.
pub(crate) fn python_function_call(line: &str, function_name: &str) -> bool {
    member_prefixed_call_in(line, function_name, &['.'], CommentSyntax::Hash)
}

/// Ruby reaches a method through `.` and a constant path through `::`, and
/// opens a comment with `#`. A parenless Ruby call carries no argument list, so
/// it is not a sink callsite under this rule: every benchmark sink takes one
/// positional argument and every fixture spells that call with parentheses.
/// The receiverless source calls the fixtures do spell parenlessly are resolved
/// from their declaration lines, never from a callsite scan.
pub(crate) fn ruby_function_call(line: &str, function_name: &str) -> bool {
    member_prefixed_call_in(line, function_name, &['.', ':'], CommentSyntax::Hash)
}

/// A Ruby endpoint marker sits on a `def` line, and Ruby's parameter list is
/// optional: `def dfb_source # DFB-SOURCE: ...` declares a method exactly as
/// `def dfb_sink(value) # DFB-SINK: ...` does. The declared name is therefore
/// read after the `def` keyword rather than before a parameter list, which is
/// the one surface rule Ruby does not share with the parameter-list dialects.
pub(crate) fn ruby_declared_function_name(declaration: &str, marker: &str) -> Option<String> {
    let marker_start = declaration.find(marker)?;
    let declaration = &declaration[..marker_start];
    let declaration = declaration.split('#').next().unwrap_or(declaration);
    let (keyword, _) = declaration.match_indices("def").find(|(start, _)| {
        let before = declaration[..*start].chars().next_back();
        let after = declaration[*start + "def".len()..].chars().next();
        !before.is_some_and(ascii_identifier_char)
            && after.is_some_and(|character| character.is_whitespace())
    })?;
    let name = declaration[keyword + "def".len()..].trim_start();
    let name = name.strip_prefix("self.").unwrap_or(name);
    let end = name
        .char_indices()
        .find_map(|(index, character)| (!ascii_identifier_char(character)).then_some(index))
        .unwrap_or(name.len());
    (end > 0 && !name.starts_with(|character: char| character.is_ascii_digit()))
        .then(|| name[..end].to_string())
}

/// PHP reaches an instance member through `->` and a static member or class
/// constant through `::`. Its `.` is string concatenation, not a member
/// operator, so — unlike every other dialect here — a call preceded by `.` is a
/// genuine call of the free benchmark function and must not be excluded. PHP
/// opens a line comment with either `//` or `#`.
pub(crate) fn php_function_call(line: &str, function_name: &str) -> bool {
    member_prefixed_call_in(
        line,
        function_name,
        &['>', ':'],
        CommentSyntax::DoubleSlashOrHash,
    )
}

/// C and C++ reach a member through `.`, `->`, and `::`; none of those is a
/// call of the free benchmark sink function the anchor declares.
pub(crate) fn cpp_function_call(line: &str, function_name: &str) -> bool {
    member_prefixed_function_call(line, function_name, &['.', '>', ':'])
}

/// Rust reaches a member through `.` and a path through `::`; it has no `->`
/// member operator, so — unlike C and C++ — `>` is not a qualifying prefix.
pub(crate) fn rust_function_call(line: &str, function_name: &str) -> bool {
    member_prefixed_function_call(line, function_name, &['.', ':'])
}

pub(crate) fn member_prefixed_function_call(
    line: &str,
    function_name: &str,
    member_prefixes: &[char],
) -> bool {
    member_prefixed_call_in(
        line,
        function_name,
        member_prefixes,
        CommentSyntax::DoubleSlash,
    )
}

pub(crate) fn member_prefixed_call_in(
    line: &str,
    function_name: &str,
    member_prefixes: &[char],
    comment: CommentSyntax,
) -> bool {
    let line = code_without_literals_in(line, comment);
    let mut search_from = 0;
    while let Some(offset) = line[search_from..].find(function_name) {
        let start = search_from + offset;
        let end = start + function_name.len();
        let before = line[..start].chars().next_back();
        let after = line[end..]
            .chars()
            .find(|character| !character.is_whitespace());
        if !before.is_some_and(ascii_identifier_char)
            && !before.is_some_and(|character| member_prefixes.contains(&character))
            && after == Some('(')
        {
            return true;
        }
        search_from = end;
    }
    false
}

pub(crate) fn ecma_function_call(line: &str, function_name: &str) -> bool {
    let line = code_without_literals(line);
    let mut search_from = 0;
    while let Some(offset) = line[search_from..].find(function_name) {
        let start = search_from + offset;
        let end = start + function_name.len();
        let before = line[..start].chars().next_back();
        let after = line[end..]
            .chars()
            .find(|character| !character.is_whitespace());
        let preceded_by_member = before == Some('.') || before == Some('?');
        if !before.is_some_and(ecma_identifier_char) && !preceded_by_member && after == Some('(') {
            let prefix = line[..start].trim_end();
            if !prefix.ends_with("function") {
                return true;
            }
        }
        search_from = end;
    }
    false
}

/// `ecma_function_call`, with a member-qualified callsite accepted.
///
/// The two differ in exactly one respect: `Audit.record(v)` and `alpha.get(k)`
/// are callsites of `record` and `get` here and are not under `Ecma`. The
/// declaration guard is unchanged — a `function record(...)` declaration is
/// still never counted as a call — and so is the literal and comment stripping.
pub(crate) fn ecma_member_function_call(line: &str, function_name: &str) -> bool {
    let line = code_without_literals(line);
    let mut search_from = 0;
    while let Some(offset) = line[search_from..].find(function_name) {
        let start = search_from + offset;
        let end = start + function_name.len();
        let before = line[..start].chars().next_back();
        let after = line[end..]
            .chars()
            .find(|character| !character.is_whitespace());
        if !before.is_some_and(ecma_identifier_char) && after == Some('(') {
            let prefix = line[..start].trim_end();
            if !prefix.ends_with("function") {
                return true;
            }
        }
        search_from = end;
    }
    false
}

/// Blank out string literals and drop line comments so a call-shaped substring
/// inside a literal never counts as a callsite. Single/double/backtick quotes
/// with backslash escapes are common to every dialect reconciled here; only the
/// comment opener differs.
pub(crate) fn code_without_literals(line: &str) -> String {
    code_without_literals_in(line, CommentSyntax::DoubleSlash)
}

pub(crate) fn code_without_literals_in(line: &str, comment: CommentSyntax) -> String {
    let mut output = String::with_capacity(line.len());
    let mut quote = None;
    let mut escaped = false;
    let mut characters = line.chars().peekable();
    while let Some(character) = characters.next() {
        if let Some(active_quote) = quote {
            if escaped {
                escaped = false;
            } else if character == '\\' {
                escaped = true;
            } else if character == active_quote {
                quote = None;
            }
            output.push(' ');
            continue;
        }
        let opens_comment = match comment {
            CommentSyntax::DoubleSlash => character == '/' && characters.peek() == Some(&'/'),
            CommentSyntax::Hash => character == '#',
            CommentSyntax::DoubleSlashOrHash => {
                character == '#' || (character == '/' && characters.peek() == Some(&'/'))
            }
        };
        if opens_comment {
            break;
        }
        if matches!(character, '\'' | '"' | '`') {
            quote = Some(character);
            output.push(' ');
        } else {
            output.push(character);
        }
    }
    output
}

pub(crate) fn sarif_result_anchor_match(
    result: &Value,
    sink_locations: &[SinkAnchorLocation],
) -> SarifAnchorMatch {
    let Some(locations) = result["locations"].as_array() else {
        return SarifAnchorMatch::Ambiguous;
    };
    if locations.is_empty() {
        return SarifAnchorMatch::Ambiguous;
    }
    let mut matches = BTreeSet::new();
    let mut malformed = false;
    for location in locations {
        let Some(uri) = location["physicalLocation"]["artifactLocation"]["uri"].as_str() else {
            malformed = true;
            continue;
        };
        let Some(line) = location["physicalLocation"]["region"]["startLine"].as_u64() else {
            malformed = true;
            continue;
        };
        for (index, anchor) in sink_locations.iter().enumerate() {
            if evidence_path_matches_file(uri, &anchor.file)
                && anchor.callsite_lines.contains(&line)
            {
                matches.insert(index);
            }
        }
    }
    if malformed || matches.len() > 1 {
        SarifAnchorMatch::Ambiguous
    } else if matches.len() == 1 {
        SarifAnchorMatch::Matched
    } else {
        SarifAnchorMatch::Unmatched
    }
}

/// Does a path reported by a tool denote the case's fixture file? SARIF reports
/// a URI and Joern reports a CPG filename; both are matched the same way,
/// against absolute, workspace-relative, and bare-filename spellings.
///
/// The final bare-basename fallback means a finding in a same-named file in
/// another directory can satisfy the anchor. This is near-inert while every
/// fixture is a single file in its own case workspace, but must be revisited
/// (e.g. with a stricter suffix match) if fixtures ever span multiple
/// directories.
pub(crate) fn evidence_path_matches_file(uri: &str, file: &str) -> bool {
    let uri = uri.replace('\\', "/");
    let uri = uri.split(['?', '#']).next().unwrap_or(&uri);
    // Stripping the bare `file:` scheme subsumes `file://`: Infer's SARIF
    // spells a workspace-relative artifact as `file:direct_flow.c`, with no
    // slashes at all, and the slash trim below already absorbs the two a
    // fully-spelled `file://` URI leaves behind.
    let uri = uri.strip_prefix("file:").unwrap_or(uri);
    let uri = uri.trim_start_matches('/');
    let normalize = |path: &str| path.trim_start_matches("./").replace('\\', "/");
    let uri = normalize(uri);
    let file = normalize(file);
    uri == file
        || uri.ends_with(&format!("/{file}"))
        || Path::new(&uri).file_name().and_then(|name| name.to_str())
            == Path::new(&file).file_name().and_then(|name| name.to_str())
}

pub(crate) fn sink_anchor_file_matches(case: &Value, uri: &str) -> bool {
    case["sink_anchors"]
        .as_array()
        .into_iter()
        .flatten()
        .any(|anchor| {
            let Some(file) = anchor["file"].as_str() else {
                return false;
            };
            evidence_path_matches_file(uri, file)
        })
}

pub(crate) fn sarif_result_count(sarif: &Value) -> usize {
    sarif["runs"]
        .as_array()
        .into_iter()
        .flatten()
        .map(|run| run["results"].as_array().map_or(0, Vec::len))
        .sum()
}

pub(crate) fn sarif_messages(sarif: &Value) -> Vec<String> {
    let mut messages = sarif["runs"]
        .as_array()
        .into_iter()
        .flatten()
        .flat_map(|run| run["results"].as_array().into_iter().flatten())
        .filter_map(|result| result["message"]["text"].as_str())
        .map(str::to_string)
        .collect::<Vec<_>>();
    messages.sort();
    messages.dedup();
    messages
}

pub(crate) fn sarif_execution_errors(sarif: &Value) -> Vec<String> {
    let mut errors = Vec::new();
    for invocation in sarif["runs"]
        .as_array()
        .into_iter()
        .flatten()
        .flat_map(|run| run["invocations"].as_array().into_iter().flatten())
    {
        if invocation["executionSuccessful"] == false {
            errors.push("CodeQL SARIF reports unsuccessful execution".to_string());
        }
        for notification in invocation["toolExecutionNotifications"]
            .as_array()
            .into_iter()
            .flatten()
        {
            if notification["level"] == "error" {
                errors.push(
                    notification["message"]["text"]
                        .as_str()
                        .unwrap_or("CodeQL SARIF contains an execution error")
                        .to_string(),
                );
            }
        }
    }
    errors.sort();
    errors.dedup();
    errors
}

/// The two benchmark-controlled endpoint identifiers of one case, read out of
/// the fixture's own marker lines.
#[derive(Clone, Debug, PartialEq, Eq)]
pub(crate) struct BenchmarkEndpoints {
    pub(crate) source_function: String,
    pub(crate) sink_function: String,
}

/// Resolve a case's source and sink function names from its anchors. The
/// fixtures are frozen and mostly spell both `dfb_source`/`dfb_sink`, but the
/// two Java direct-propagation assertions predate that convention, so the names
/// are always read from the marker line rather than assumed. Both the Joern
/// kernels and the Semgrep kernels resolve their benchmark-controlled endpoint
/// contract through this one function, so neither can drift from the other.
pub(crate) fn benchmark_endpoint_names(
    case_path: &Path,
    case: &Value,
    dialect: AnchorDialect,
) -> std::result::Result<BenchmarkEndpoints, String> {
    let sink_functions = sink_anchor_locations(case_path, case, dialect)?
        .into_iter()
        .map(|location| location.function_name)
        .collect::<BTreeSet<_>>();
    let sink_function = match sink_functions.len() {
        1 => sink_functions.into_iter().next().expect("length checked"),
        count => {
            return Err(format!(
                "case declares {count} distinct sink functions; the kernel query tags exactly one"
            ));
        }
    };
    let source_functions = anchor_function_names(case_path, case, "source_anchors", dialect)?;
    let source_function = match source_functions.len() {
        1 => source_functions.into_iter().next().expect("length checked"),
        count => {
            return Err(format!(
                "case declares {count} distinct source functions; the kernel query tags exactly one"
            ));
        }
    };
    Ok(BenchmarkEndpoints {
        source_function,
        sink_function,
    })
}

/// The distinct function names declared on one anchor set's marker lines.
pub(crate) fn anchor_function_names(
    case_path: &Path,
    case: &Value,
    anchor_field: &str,
    dialect: AnchorDialect,
) -> std::result::Result<BTreeSet<String>, String> {
    let fixture_root = case_path
        .parent()
        .ok_or_else(|| "case path has no parent".to_string())?;
    let anchors = case[anchor_field]
        .as_array()
        .ok_or_else(|| format!("case has no {anchor_field}"))?;
    let mut names = BTreeSet::new();
    for anchor in anchors {
        let file = anchor["file"]
            .as_str()
            .ok_or_else(|| format!("{anchor_field} entry lacks file"))?;
        let marker = anchor["marker"]
            .as_str()
            .ok_or_else(|| format!("{anchor_field} entry lacks marker"))?;
        let body = fs::read_to_string(fixture_root.join(file))
            .map_err(|error| format!("read fixture {file}: {error}"))?;
        let line = anchor_marker_line(&body, marker, anchor["line_hint"].as_u64())?;
        let declaration = body
            .lines()
            .nth(line as usize - 1)
            .ok_or_else(|| format!("anchor line {line} is outside {file}"))?;
        names.insert(
            dialect
                .declared_function_name(declaration, marker)
                .ok_or_else(|| format!("marker {marker:?} is not on a function declaration"))?,
        );
    }
    if names.is_empty() {
        return Err(format!("case has no resolvable {anchor_field}"));
    }
    Ok(names)
}

/// How one piece of retained non-SARIF evidence reconciles against a case's
/// sink anchors. A Joern flow and a Semgrep finding are reconciled by the same
/// three-way answer, so neither adapter can drift into treating unusable
/// evidence as a negative.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum EvidenceAnchorMatch {
    Matched,
    Unmatched,
    Ambiguous,
}
