# LLM/Agent/AI Library Trends Research

This repository tracks trends and potential in novel LLM/Agent/AI libraries through systematic research and analysis. Each research run identifies emerging libraries, synthesizes trends, and generates high-leverage ideas for the future of AI development.

## Methodology

- **Scope:** Serious, non-meme libraries that reshape how we program/operate LLMs/agents
- **Sources:** GitHub, arXiv, standards bodies, vendor blogs, global dev communities  
- **Quality bar:** 3-5 sources per trend/idea, evidence-backed analysis, falsification testing
- **Cadence:** Regular research runs with date-based folders for historical tracking

## Research Runs

### 02092025 - Initial Baseline Research

**Run summary:** Established baseline coverage across 9 high-quality libraries spanning 6 categories. Identified strong trend toward DSL-based LLM programming and stateful agent architectures. Successfully found one 10/10 idea that survived falsification.

**New libraries found:** 9 libraries across Structured/Guided Decoding, DSLs, Typed I/O, Planning/Compilers, Memory/State, and Graph-aware Retrieval categories.

**Notable additions:**
- Outlines (dottxt-ai) - Production-ready structured generation with enterprise adoption
- Guidance (guidance-ai) - Python-like DSL for LLM programming with unique architecture  
- DSPy (stanfordnlp) - Programming vs prompting framework with optimization algorithms
- Letta (letta-ai) - Virtual memory management for stateful agents (formerly MemGPT)
- BAML (BoundaryML) - Schema engineering DSL with Rust compiler and multi-language support

**Categories with highest novelty delta:**
1. DSLs / Declarative meta-layers (4 libraries: Guidance, DSPy, LMQL, BAML)
2. Memory/state (1 library: Letta with breakthrough virtual memory concepts)
3. Structured/Guided Decoding (1 library: Outlines with wide industry adoption)

## Trend Tracker

| Trend | 02092025 Status | Description |
|-------|----------------|-------------|
| DSL Renaissance for LLM Programming | ↑↑ Rising | 4/9 libraries introduce domain-specific languages |
| Structured Generation Standardization | ↑ Rising | Universal adoption of schema-first output generation |
| Memory Virtualization for Agents | ↑↑ Rising | OS-like memory management becoming critical |
| Compiler Approaches to Prompt Engineering | ↑ Rising | Treating prompts as compilable artifacts |
| Multi-Modal Grammar Systems | → Stable | Extensions beyond text to include media |
| Type System Evolution | ↑ Rising | Strong typing throughout LLM application stacks |
| Agent Computer Interface (ACI) Emergence | → Stable | Domain-specific tool interfaces replacing generic APIs |
| Cross-Provider Abstraction | ↑ Rising | Universal provider support with fallback strategies |
| Streaming-First Architecture | ↑ Rising | Native streaming with type-safe partial objects |
| Observable LLM Operations | → Stable | Built-in observability and debugging tooling |

## Best Ideas So Far

| Rank | Idea | Score | One-liner | Run |
|------|------|-------|-----------|-----|
| 1 | Multi-Modal Grammar Compiler | 10.0 | Unified compiler infrastructure for cross-modal structured generation | [02092025](02092025/) |
| 2 | LLM Memory Virtualization Protocol | 9.4 | Standardized virtual memory management for agents | [02092025](02092025/) |
| 3 | Constraint Programming DSL | 9.2 | Declarative language for complex LLM behavior specification | [02092025](02092025/) |
| 4 | LLM Function Composition Runtime | 8.6 | Runtime optimization for LLM function composition with parallelization | [02092025](02092025/) |
| 5 | Neural-Symbolic Bridge Compiler | 8.4 | Bidirectional translation between symbolic AI and neural operations | [02092025](02092025/) |

## 10/10 Ledger

| Date | Title | Rationale | Link |
|------|-------|-----------|------|
| 02092025 | Multi-Modal Grammar Compiler | Novel unified abstraction for cross-modal structured generation. Inevitable with multi-modal model adoption, massive value unlock potential. Survived technical complexity and market adoption falsification attempts. | [Details](02092025/trends_and_potential.md#the-1010-idea-multi-modal-grammar-compiler) |

## Post-Mortems

*No post-mortems yet - this is the initial research run.*

---

*Last updated: 02092025*