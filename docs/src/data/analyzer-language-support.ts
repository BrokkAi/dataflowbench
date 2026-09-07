// Audited language/dialect inventories for the current analyzer pins. These are
// deliberately independent of which language kernels DataFlowBench implements:
// the overview uses them to describe analyzer breadth, while the chart's table
// reports benchmark kernel participation separately.
//
// Counting convention: C and C++, Java and Kotlin, and JavaScript and
// TypeScript are separate language/dialect entries. Binary formats and generic
// bytecode front ends are not counted as additional languages.

export interface AnalyzerLanguageSupport {
  languages: readonly string[];
  source: string;
  sourceUrl: string;
}

const supportByTool: Record<string, AnalyzerLanguageSupport> = {
  bifrost: {
    languages: ['C', 'C++', 'C#', 'Go', 'Java', 'JavaScript', 'Kotlin', 'PHP', 'Python', 'Ruby', 'Rust', 'Scala', 'TypeScript'],
    source: 'pinned Bifrost adapter inventory',
    sourceUrl: 'https://github.com/BrokkAi/dataflowbench/blob/main/adapters/bifrost/README.md',
  },
  codeql: {
    languages: ['C', 'C++', 'C#', 'Go', 'Java', 'JavaScript', 'Kotlin', 'Python', 'Ruby', 'Rust', 'Swift', 'TypeScript'],
    source: 'CodeQL data-flow guides and supported-language inventory',
    sourceUrl: 'https://codeql.github.com/docs/codeql-overview/supported-languages-and-frameworks/',
  },
  joern: {
    languages: ['C', 'C++', 'C#', 'Go', 'Java', 'JavaScript', 'Kotlin', 'PHP', 'Python', 'Ruby', 'Swift'],
    source: 'Joern source front ends and data-flow engine documentation',
    sourceUrl: 'https://docs.joern.io/frontends/',
  },
  semgrep: {
    languages: ['C', 'C++', 'Go', 'Java', 'JavaScript', 'Kotlin', 'PHP', 'Python', 'Ruby', 'Rust', 'TypeScript'],
    source: 'pinned Semgrep CE taint-language inventory',
    sourceUrl: 'https://github.com/BrokkAi/dataflowbench/blob/main/adapters/semgrep/README.md#front-end-maturity',
  },
  infer: {
    languages: ['C', 'C++', 'Java'],
    source: 'verified Pulse taint-language inventory',
    sourceUrl: 'https://github.com/BrokkAi/dataflowbench/blob/main/adapters/infer/README.md',
  },
  opentaint: {
    languages: ['Java', 'Kotlin'],
    source: 'verified OpenTaint analyzer inventory',
    sourceUrl: 'https://github.com/BrokkAi/dataflowbench/blob/main/adapters/opentaint/README.md',
  },
  flowdroid: {
    languages: ['Java', 'Kotlin'],
    source: 'verified FlowDroid analyzer inventory',
    sourceUrl: 'https://github.com/BrokkAi/dataflowbench/blob/main/adapters/flowdroid/README.md',
  },
  pysa: {
    languages: ['Python'],
    source: 'Pysa Python taint-analysis documentation',
    sourceUrl: 'https://pyre-check.org/docs/pysa-basics/',
  },
};

export function analyzerLanguageSupport(tool: string): AnalyzerLanguageSupport {
  const support = supportByTool[tool];
  if (!support) throw new Error(`No data-flow language inventory for ${tool}`);
  return support;
}
