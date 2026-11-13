# Issue 303: same-map key precision

This change adds three balanced core same-local-map templates. The constant-key
pair measures separation between two constant keys in one map. The computed-key
and callee-mutation pairs exercise cases where that precision must be constrained.
Every positive sends the value returned by the marked source to the marked sink
at runtime. Every negative is safe under the language's key and mutation semantics.

## Stable identities

| Template ID | Case directory slug | Tier | Meaning |
| --- | --- | --- | --- |
| dfb-template-issue-303-same-map-constant-keys | same-map-constant-keys | core | Same local map, two distinct constant keys; positive reads the source key, negative reads the clean key. |
| dfb-template-issue-303-same-map-computed-key | same-map-computed-key | core | Positive runtime key aliases the sink key; negative prefixes every computed key so it cannot alias the sink key. |
| dfb-template-issue-303-same-map-escaping-callee | same-map-escaping-callee | core | A mutable map is passed to a callee; positive callee stores the source at the sink key, negative callee stores it at a distinct key. |

Case IDs follow dfb-taint-<language>-<slug>-<polarity>. For each applicable
language, each slug has exactly one positive and one negative case under the
matching template ID and benchmark-controlled model profile.

All three templates are core and are intended for the benchmark-controlled
profile. Each applicable language therefore contributes one balanced positive
and negative pair per template.

## Applicability and native containers

The constant-key template and both controls apply to cpp, csharp, go, java,
javascript, typescript, kotlin, scala, swift, rust, python, ruby, and php.

C has no standard-library associative map or dictionary. A project-specific
array of key-value structs would invent a container API and would not be a
natural native-map counterpart, so C is recorded as inapplicable and has no
fixture pair.

Fixtures use the idiomatic container for each language:

| Language | Fixture API | Native alternative considered |
| --- | --- | --- |
| cpp | std::unordered_map with string keys | std::map has the same equality behavior for these keys; both preserve distinct constant string keys. |
| csharp | Dictionary<string,string> indexer | Add and TryGetValue operate on the same key identity; the indexer keeps the store/read path compact. |
| go | map[string]string | Map literals and index expressions are the ordinary form; string keys compare by value. |
| java | HashMap<String,String> put/get | The issue's OWASP BenchmarkJava idiom. |
| javascript | Map set/get | Object properties also support string keys, but Map avoids prototype and property-key coercion behavior. |
| typescript | Map<string,string> set/get | Record and object properties are runtime objects with property-key coercion; Map makes the tested string key identity explicit. |
| kotlin | mutableMapOf<String,String> indexer | HashMap put/get has the same key equality for String keys. |
| scala | mutable.Map[String,String] update/apply | get is an Option-returning read of the same key space. |
| swift | Dictionary<String,Int> subscript | Dictionary String keys use value equality; mutation through inout preserves caller-visible updates. |
| rust | HashMap<String,String> insert/get | The owned String key is compared by Eq/Hash content. |
| python | dict subscripts | get reads the same string-keyed dictionary. |
| ruby | Hash subscripts | fetch reads the same string-keyed Hash; these nonnumeric string keys remain distinct. |
| php | string-keyed arrays | String keys are used instead of numeric-looking keys, which PHP may coerce to integers. |

The fixtures choose one representative native API per language. Alternatives
above were checked for key identity, mutation, and read semantics. The three
templates share the same map API within each language.

## Pair semantics

### Constant keys

Both cases create one local map and initialize two different string keys.
The positive stores the marked source under the tainted key and reads that key
at the sink. The negative performs the same source store but reads the other,
preinitialized clean key. The maps are not aliased or passed elsewhere. The
negative therefore cannot receive the source value through the sink read.
Its negative mechanism is unrelated-value: the selected entry contains the
literal clean value, while the source remains under a different key.

### Computed key

The positive obtains the write key from a runtime argument, with the
validation invocation supplying the sink key. It stores the marked source
under that computed key and reads the sink key, so the concrete execution
aliases and flows. Supplying another key makes that positive execution emit
the clean value instead.

The negative computes the write key by prefixing a runtime suffix with the
fixed string private:. That key cannot equal payload for any suffix. It stores
the source under this computed key and reads the preinitialized payload key.
The negative is safe for all argument values, not just the validation input.
Its negative mechanism is unrelated-value.

### Map passed to a callee

The caller initializes payload to clean and passes the same mutable map to a
defined helper. In the positive, the helper stores the marked source under
payload and the caller reads payload after return. In the negative, the
helper stores the source under private and the caller reads payload. The
negative is safe because the helper's only write uses a distinct constant key.
The map does escape to a callee in both cases, and the positive is a real
interprocedural source-to-sink flow. Its negative mechanism is
unrelated-value.

Swift uses Dictionary<String,Int> with source value 7 and clean value 0. Its
source and sink functions retain the existing zero-argument Int source and Int
sink signatures, and the DFB-SOURCE/DFB-SINK markers sit on the exact call
lines. The runtime validator changes the source return literal in a temporary
copy. Swift uses an inout Dictionary parameter, Rust uses &mut HashMap, C++ uses
a map reference, and PHP uses an array reference so helper mutations are visible
to the caller. The other selected containers are mutable reference objects or
maps.

## Fixture and runtime validation

All authored source files carry DFB-SOURCE and DFB-SINK anchors. Positive
cases also mark the store and read path with DFB-WITNESS markers. The case
metadata includes fixture provenance, expected flows or nonflows, and the
language-neutral capability required by each template. Tool model references
are copied from the same language's infeasible-branch-positive case so existing
Bifrost and CodeQL partitions can resolve them; Swift stays empty, matching its
canonical case.

The dedicated validator checks schema shape, marker uniqueness, marker-to-file
anchors, pair balance, and metadata consistency. It independently compiles or
runs each executable fixture, confirms its expected sink value, then changes
the marked source value and runs it again. Positive sink output must change
with the source value; negative sink output must remain clean. It also checks
computed-key executions with both an aliasing and a nonaliasing key.

No analyzer output is used to establish runtime flow or nonflow.

The integration registers these fixtures under the versioned prospective input root. The canonical corpus loader and core denominator checks include them; historical populations retain their original input roots.
