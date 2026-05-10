# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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