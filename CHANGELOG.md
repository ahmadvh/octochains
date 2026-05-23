# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2026-05-23

### Added
- **Official Aggregators**: Introduced the first native, domain-agnostic aggregators to the Octochains core:
    - `Synthesizer`: Merges isolated agent reports into a single cohesive narrative.
    - `ConflictChecker`: Audits agent reports for logical inconsistencies using configurable `pairwise_audit` logic (supporting both multi-threaded isolation and dynamic prompt-matrices).
- **Core JSON Utilities**: Added `utils.py` featuring a robust `parse_and_validate_json` helper to ensure LLM outputs strictly adhere to framework schemas, providing automated fault tolerance.
- **Aggregator Schemas**: Added `SynthesisResult` and `ConflictReport` dataclasses to `schema.py` to support the new official aggregators.
- **Advanced Execution Tracing**: Introduced a `show_log` boolean across the `Engine` and official aggregators. When enabled, it provides a clean, Terminal UI (TUI) tree structure to track asynchronous thread dispatching and API lifecycles.
- **New Cookbook Recipe**: Added `Confict Analysis` demo using our new `ConflictChecker` aggregator. A high-stakes enterprise recipe demonstrating Executive Conflict Analysis for M&A Due Diligence.


### Changed
- **Directory Restructure**: Renamed the `demo_examples` directory to `cookbook` to align with standard open-source framework conventions.
- **Agent Initialization**: Relaxed constraints on the `Agent` base class by making the `input_description` parameter optional.
- **Medical Diagnostics Recipe**: Upgraded the existing medical diagnostics run script to natively utilize the new official `Synthesizer` aggregator.

---

## [0.2.0] - 2026-05-18

### Added

- **Dependency Injection (BYO-LLM)**: Added `llm_callable` initialization parameters to both `Agent` and `Aggregator` base classes. This completely decouples the framework from any specific LLM provider or SDK.

- **Custom Type Alias**: Introduced `LLMCallable = Callable[[str], Any]` to standardize model execution signatures across the framework.

- **Sensible Defaults & Dynamic Tools**: Added the `_build_prompt()` helper method to the `Agent` base class.
    - Automatically enforces "Double-Blind" isolation instructions.
    - Dynamically discovers and injects `@tool` JSON schemas directly into the system prompt.

- **Engine Safety Net**: Added `format_output` to the `Agent` base class to safely stringify unexpected agent return types before Phase 1 engine mapping, preventing dictionary mapping crashes.

### Changed

- **Structured Outputs Supported**: Changed the return type of `Aggregator.execute()` and `Report.consensus` from `str` to `Any`.
    - Aggregators can now natively return parsed JSON dictionaries or Pydantic models directly to the user's application.


---

## [0.1.1] - 2026-05-10

### Added
- **Agent Metadata**: Added a required `input_description` parameter to the `Agent` base class. This ensures all agents published to the Hub clearly define their expected data format (e.g., "JSON string of patient vitals" vs. "Raw text SEC filing").

### Changed
- **License Update**: Transitioned from MIT to **Business Source License (BSL) 1.1** to protect enterprise interests.
- **Aggregator Refactor**: Renamed `Aggregator.synthesize()` to `Aggregator.execute()`. This reflects that aggregators can perform any logical operation, not just synthesis.
- **Scientific Alignment**: Rewrote `README.md` to include performance benchmarks (+80.8% accuracy) based on the 2026 Google/MIT Scaling Paper.

### Removed
- **Unbiased Synthesis**: Removed the `problem_data` argument from the `Aggregator.execute()` method. 
    - *Rationale*: To ensure zero-bias synthesis, the Aggregator is now "blind" to the initial input, forcing it to judge the final verdict solely based on the conflicting or supporting evidence provided by the specialized agents.

---

## [0.1.0] - 2026-04-18

### Added
- Initial release of the Octochains Parallel Engine.
- Multi-expert broadcast logic for decomposable reasoning tasks.
- Abstract Base Classes for `Agent` and `Aggregator`.
- Updated documentation with scientific validation from the 2026 Google/MIT Scaling Paper.