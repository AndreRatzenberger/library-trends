# Deep Dive Notes - Novel LLM/AI Libraries & Frameworks

## Category Analysis

### 1. DSLs & Declarative Meta-layers
**Leaders:** LMQL, BAML, SGLang, GenAIScript, GPTScript, Colang

**Strengths:**
- LMQL: First-class constraints and probabilistic programming
- BAML: Strong typing with Rust-like syntax, good IDE support  
- SGLang: Performance-focused with runtime optimization
- Colang: Domain-specific for conversational AI flows

**What everyone else is missing:**
- Composable constraint libraries (mix regex, grammar, semantic constraints)
- Compile-time optimization for prompt templates
- Cross-model compatibility layers
- Visual programming interfaces for non-technical users

### 2. Structured/Guided Decoding  
**Leaders:** Guidance, Outlines, XGrammar, vLLM structured outputs

**Strengths:**
- Outlines: Clean JSON Schema + regex integration
- XGrammar: High-performance grammar parsing
- Guidance: Intuitive template-based approach
- vLLM: Production-scale serving integration

**What everyone else is missing:**
- Real-time constraint modification during generation
- Hierarchical schema with conditional branches
- Performance optimization for complex grammars
- Stream-aware structured generation

### 3. Planning/Compilers
**Leaders:** DSPy, SWE-agent

**Strengths:**
- DSPy: Automatic optimization of LLM programs
- SWE-agent: Task-specific interface design

**What everyone else is missing:**  
- Automatic parallelization of tool calls
- Cost-aware execution planning
- Rollback/retry mechanisms with state preservation
- Cross-model compilation targets

### 4. Memory/State Management
**Leaders:** MemGPT/Letta

**Strengths:**
- Virtual memory abstraction with paging
- OS-like memory management primitives
- Long-term conversation continuity

**What everyone else is missing:**
- Distributed memory across multiple instances
- Memory compression/archival strategies  
- Shared memory pools for multi-agent systems
- Event-sourced memory with replay capabilities

### 5. Novel Emerging Areas (2024-2025)

**Trend:** Engine-level integration
- vLLM, SGLang moving constraints into inference engines
- Better performance than post-processing approaches

**Trend:** Multi-modal constraint handling
- Extension of text constraints to vision/audio generation
- Cross-modal consistency enforcement

**Trend:** Agent society simulation
- Large-scale multi-agent environments
- Emergent behavior analysis

## Potential Novel Directions

1. **Temporal Logic for LLM Programs:** Using Linear Temporal Logic (LTL) or Computation Tree Logic (CTL) to specify agent behavior over time
2. **WebAssembly for Portable Agent Runtime:** WASM-based agent execution environments
3. **Datalog for Agent Knowledge:** Logic programming approaches to agent reasoning
4. **Category Theory for Prompt Composition:** Mathematical frameworks for composing prompts
5. **Probabilistic Programming for Uncertain Reasoning:** Deep integration with PPLs like Pyro/Stan