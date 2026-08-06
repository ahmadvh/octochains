# Octochains: A Technical Architecture for Parallel Isolated Multi-Agent Reasoning

**Engineering white paper**

Prepared August 2026 · github.com/ahmadvh/octochains · v0.6.0 (Beta)

---

## Abstract

Octochains is a Python framework for orchestrating multiple large language model (LLM) agents in parallel, isolated execution contexts, synthesized by a single centralized aggregation layer. It has one required third-party dependency (Pydantic v2) and is model-agnostic by design: the framework never calls a model provider's API directly, and instead accepts a plain callable from the developer.

This paper describes the concrete engineering decisions behind three layers of the system: the `Engine` orchestrator, the `Agent`/`Aggregator` base class contracts, and the Skills system for injecting versioned procedural knowledge into an agent without prompt-engineering boilerplate. Code shown is drawn directly from the current `main` branch of the repository.

---

## 1. Design Goals

Octochains is built around four constraints, in priority order:

1. **Isolation is structural, not just instructional.** An agent must not be able to see another agent's reasoning during execution, because contextual bloat and anchoring bias degrade output quality and make failure modes harder to audit. This is enforced by executing each agent in its own thread with its own prompt construction, not by a system-prompt instruction that an agent could be talked out of.
2. **A single component sees the whole picture.** Exactly one layer, the aggregator, has visibility into every agent's output. This gives the system a single, auditable point where conflicts get resolved and a final verdict gets produced, rather than resolution being distributed and implicit.
3. **Fault tolerance at the thread level.** One agent crashing, timing out, or returning malformed output must not take down the whole pipeline unless the caller explicitly opts into strict behavior.
4. **Minimal, auditable dependency surface.** The only hard dependency is Pydantic v2, used for schema validation and structured output. Everything else, including the Skill frontmatter parser, is implemented against the Python standard library.

---

## 2. The Engine: Orchestration and Fault Isolation

The `Engine` class (`src/octochains/engine.py`) is the orchestrator. It takes a list of `Agent` instances and a single `Aggregator`, and exposes one method, `run(problem_data, show_log=False)`, that returns a `Report`.

### 2.1 Construction-time validation

The constructor rejects duplicate agent roles immediately, rather than allowing them to silently overwrite each other's reports in the results dictionary later:

```python
roles = [agent.role for agent in agents]
if len(roles) != len(set(roles)):
    duplicates = {r for r in roles if roles.count(r) > 1}
    raise ValueError(
        f"Duplicate agent role(s) detected: {duplicates}. Each agent's "
        "role must be unique — duplicate roles would silently overwrite "
        "each other's reports during aggregation."
    )
```

This is a fail-fast design choice: a misconfiguration that would otherwise manifest as silently missing data in the aggregator's input is caught at `Engine.__init__`, before any API calls are made.

### 2.2 Execution model

`run()` submits every agent's `execute()` method to a `concurrent.futures.ThreadPoolExecutor`, keyed by a `future_to_agent` map, and consumes results via `as_completed()`. Two configuration parameters control the failure envelope:

- **`max_workers`**: caps concurrent threads (defaults to Python's standard heuristic if unset).
- **`agent_timeout`**: bounds how long the engine waits for the full parallel batch. Because Python cannot forcibly kill a running thread, a timed-out agent's underlying call may continue running in the background, detached, after `run()` returns; the engine records it as failed and moves on rather than blocking indefinitely.

The executor is managed manually rather than via a `with` block, specifically because a plain context manager blocks on exit until all submitted work finishes, which would defeat the purpose of `agent_timeout`. On the timeout path, the `finally` block shuts the executor down with `wait=False, cancel_futures=True`; on the normal path, it waits for a clean shutdown.

### 2.3 Failure semantics

Each individual agent's execution is wrapped in its own `try`/`except`, and every outcome, success, error, or timeout, produces a `Trace` (a Pydantic model with `agent_role`, `status`, `output`, `error_message`). No agent failure raises out of the parallel phase; it is captured and recorded.

After the parallel phase, two gates run in a specific order:

```python
if not valid_agent_reports:
    raise NoValidReportsError(...)   # total failure — always fatal

if self.require_all_agents and failed_roles:
    raise IncompleteAgentBatchError(...)  # opt-in strictness
```

Total failure (zero successful agents) is unconditionally fatal, because there is nothing for the aggregator to synthesize. Partial failure is only fatal if the caller set `require_all_agents=True`; by default, the engine proceeds to aggregation with whatever valid reports it has, on the reasoning that a partial expert panel is often still more useful than no answer, provided the aggregator is told (via the `Report.traces` list) exactly who did and didn't respond.

The aggregator's own execution is wrapped separately: an exception there raises `AggregatorError`, distinct from `AgentExecutionError`, `NoValidReportsError`, and `IncompleteAgentBatchError`, giving callers a typed exception hierarchy to handle each failure class differently.

### 2.4 Why this matters architecturally

This error-handling design is a direct engineering response to a specific finding from external research on multi-agent reliability (Section 7): uncoordinated parallel agents amplify errors sharply because nothing catches a bad output before it reaches the final result. Octochains' answer is a two-part containment strategy: contain failures at the thread level (so one bad agent doesn't crash the run), and contain them again at the aggregation gate (so the aggregator, and by extension the final consensus, is explicitly told which experts it does and doesn't have data from, rather than silently degrading).

---

## 3. The Agent Contract

`Agent` (`src/octochains/base.py`) is an abstract base class. Subclasses must implement `execute(problem_data) -> Any`; everything else is provided.

### 3.1 Forced Perspective prompt construction

`_build_prompt()` is the default prompt builder, and it is opinionated: it explicitly tells the model it has no knowledge of other agents, injects the agent's role and goal, and, if the agent has skills, appends a lightweight skill index (name and description only, not full content):

```python
prompt = f"""
    You are operating in a highly restricted, isolated environment.
    You have NO knowledge of what other agents are doing. Do not assume anything outside your domain.

    === YOUR IDENTITY ===
    Role: {self.role}
    Goal: {self.goal}{self._skill_index()}
    ...
    """
```

Subclasses are free to ignore `_build_prompt()` entirely and construct their own prompt, or to call it and layer tool-calling logic around it, since `execute()` is where API calls, tool schemas, and parsing all happen. The base class does not make an HTTP call on the developer's behalf anywhere; it only assembles strings and normalizes output.

### 3.2 Structured output enforcement

If a subclass passes `output_format` (a Pydantic `BaseModel` subclass), `_build_prompt()` appends the model's JSON schema and instructs the model to return only valid JSON matching it, with no markdown fencing or conversational filler.

### 3.3 Output normalization

`format_output()` is the single chokepoint every agent's raw result passes through before it becomes visible to the aggregator. It handles five input shapes uniformly: raw strings, Pydantic `BaseModel` instances (via `model_dump_json`), dicts, dataclasses, and legacy Pydantic v1 objects (`.json()`), falling back to `str()` for anything else. It also strips `<think>...</think>` blocks from reasoning-model output before the result is passed downstream, so an agent built on a thinking model doesn't leak its chain-of-thought into the aggregator's context.

### 3.4 Fail-fast skill validation

```python
if skills and llm_callable is None:
    raise ValueError(
        f"Agent '{role}' requires an llm_callable because it has skills "
        "attached (skill routing needs an LLM to select relevant guidance). "
        "Pass llm_callable=..., or construct this agent without skills."
    )
```

This is representative of the codebase's general posture: configuration errors that would otherwise surface as a confusing runtime failure inside a worker thread are checked and raised at construction time instead.

---

## 4. The Aggregator Contract

`Aggregator` is the second abstract base class. It implements one shared helper, `_format_reports()`, which renders a `Dict[str, str]` of agent reports into a labeled block (`=== EXPERT REPORT: {role} ===`) for inclusion in a prompt, and requires subclasses to implement `execute(agent_reports) -> Any`.

Three aggregators ship today; a fourth is designed but not yet merged.

### 4.1 Synthesizer

The general-purpose "Chief Integration Officer." It merges all reports into one narrative and returns a `SynthesisResult` (`narrative: str`, `key_takeaways: List[str]`, `confidence: float`, `citations: Dict[str, str]`), with `model_config = ConfigDict(extra='ignore')` so that any extra keys hallucinated by the LLM are silently dropped rather than causing a validation error.

### 4.2 ConflictChecker

The deterministic "Chief Justice." It supports two distinct execution strategies, toggled with a single constructor flag, `pairwise_audit`:

**Strategy 1, prompt-matrix (default, `pairwise_audit=False`).** All reports go into a single API call. The prompt is dynamically constructed with an explicit step-by-step instruction enumerating every unique pair of agents (`N*(N-1)/2` combinations, computed via `itertools.combinations`), asking the model to internally walk through each pair before producing one consolidated `ConflictReport`. This is cheap, one call regardless of agent count, but has more run-to-run variance because the model is holding the entire comparison matrix in a single context window.

**Strategy 2, parallel pairwise (`pairwise_audit=True`).** The aggregator itself spins up a second, nested `ThreadPoolExecutor` and fires one isolated API call per unique agent pair, each call seeing only those two reports:

```python
def _check_single_pair(pair) -> List[Conflict]:
    (agent_a, report_a), (agent_b, report_b) = pair
    pair_dict = {agent_a: report_a, agent_b: report_b}
    ...
    result = parse_and_validate_json(raw_output, ConflictReport)
    return result.conflicts if result.has_conflicts else []

with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_threads) as executor:
    results = list(executor.map(_check_single_pair, pairs))
```

This costs `O(N^2)` API calls but produces deterministic, hyper-focused bilateral comparisons, each free of the noise of unrelated reports in context. The choice between the two strategies is a direct cost-versus-determinism trade-off exposed to the caller rather than hidden inside the framework.

Both strategies share prompt-building and validation logic through `_build_prompt()` and `parse_and_validate_json()`, and both gate on a minimum of two valid reports before running at all:

```python
if len(agent_reports) < 2:
    return ConflictReport(has_conflicts=False, conflicts=[], summary=error_msg)
```

This mirrors the engine's own total-failure gate: conflict detection is mathematically undefined with fewer than two inputs, so the aggregator returns a well-formed, explicit "cannot evaluate" result instead of either crashing or fabricating a comparison.

### 4.3 WeightedSynthesizer

A `Synthesizer` variant for proportional emphasis rather than conflict resolution: some perspectives should shape the final narrative more than others as a baseline, even when every expert agrees.

Weight resolution is entirely deterministic, computed in Python before the LLM is ever called:

```python
def _resolve_weights(self, roles) -> Dict[str, float]:
    roles = list(roles)
    effective = {role: float(self.weights.get(role, self.default_weight)) for role in roles}
    effective = {role: max(0.0, w) for role, w in effective.items()}  # clamp negatives
    total = sum(effective.values())
    if total <= 0:
        equal = 1.0 / len(roles) if roles else 0.0
        return {role: round(equal, 4) for role in roles}
    return {role: round(w / total, 4) for role, w in effective.items()}
```

Roles present in the responding reports but absent from the `weights` dict fall back to `default_weight` (1.0 by default) rather than being silently dropped from the blend. Weights are normalized to sum to 1.0 and then bucketed into four emphasis bands in the generated prompt (ANCHOR at 40%+, MAJOR at 20-39%, SUPPORTING at 8-19%, MINOR under 8%), each band carrying explicit, literal instructions for how many narrative sentences and key takeaways that perspective must receive. The resulting `WeightedSynthesisResult` extends `SynthesisResult` with `weights_applied` and `dominant_perspective`, both computed in Python rather than returned by the model, so the audit trail of how the blend was shaped is guaranteed accurate even if the LLM's narrative text drifts.

This is the clearest illustration of the framework's general pattern: anything that can be computed deterministically (weight normalization, dominant-perspective selection, pair enumeration) is computed in Python, and the LLM is only asked to do the part that requires language understanding.

---

## 5. The Skills System

A `Skill` (`src/octochains/skills.py`) is a `dataclass` with four fields: `name`, `description`, `version`, `content`. It is parsed from a `SKILL.md` file with a hand-rolled frontmatter parser, deliberately avoiding a PyYAML dependency:

```python
segments = cleaned_text.split("---", 2)
frontmatter_block = segments[1].strip()
markdown_content = segments[2].strip()

metadata: Dict[str, str] = {}
for line in frontmatter_block.splitlines():
    line = line.strip()
    if not line or line.startswith("#"):
        continue
    if ":" in line:
        key, val = line.split(":", 1)
        metadata[key.strip().lower()] = val.strip()
```

The parser supports flat `key: value` pairs only, no nested structures or lists, which keeps it a few dozen lines of stdlib code instead of a general-purpose YAML implementation. `name` is mandatory and raises `ValueError` if missing; `description` and `version` have defaults.

Skills are surfaced to an agent in two tiers, a pattern the framework calls progressive disclosure:

1. **Index tier** (`_skill_index()`): every prompt includes just each skill's `name` and `description`, cheap and always-on.
2. **Full content tier** (`load_relevant_skills()`): the complete markdown body of every attached skill, injected in full. The base implementation loads all attached skills' full content unconditionally; it is explicitly designed to be overridden in a subclass for LLM-based dynamic routing (selecting which skills' full content to load based on the specific problem data) when an agent carries more skills than should be loaded into every prompt.

Skills attach to any preset agent via `extra_skills=[...]` without subclassing, which is the mechanism for layering a team's proprietary methodology on top of an official preset (for example, a house valuation model added to `cfo_agent`) without forking the framework.

---

## 6. Data Contracts

All structured outputs are Pydantic v2 `BaseModel`s (`src/octochains/schema.py`), which gives the framework runtime validation, JSON schema generation for prompts, and `.model_dump()` / `.model_dump_json()` serialization for free.

- **`Trace`**: `agent_role`, `status` (`"success"` or `"error"`), `output`, `error_message`. One per agent per run, regardless of outcome.
- **`Report`**: the `Engine.run()` return value. `consensus` (the aggregator's output, typed per-aggregator) and `traces: List[Trace]`.
- **`SynthesisResult`** / **`WeightedSynthesisResult`** / **`ConflictReport`** / **`Conflict`**: the per-aggregator structured outputs described in Section 4.

All LLM-facing result models set `model_config = ConfigDict(extra='ignore')`. This is a deliberate anti-fragility choice: if a model hallucinates an extra JSON key beyond the schema, validation does not fail the entire run over it.

---

## 7. Research Grounding

Octochains' core architectural bet, independent parallel agents with a single centralized synthesis and audit step, is not novel to this framework, but it is validated by a specific, recent, large-scale controlled study: "Towards a Science of Scaling Agent Systems" (Kim et al., Google Research / Google DeepMind / MIT, arXiv:2512.08296, January 2026). The study ran 180 controlled configurations across five canonical architectures (single-agent, independent, centralized, decentralized, hybrid), three model families, and four benchmarks.

Two findings map directly onto Octochains' design:

**Task-architecture alignment.** On decomposable tasks (their example: financial analysis, where distinct sub-problems don't depend on each other), centralized coordination beat single-agent baselines by 80.9%. On sequential tasks (their example: planning), every multi-agent configuration tested, including centralized, degraded performance by 39 to 70%. This is a hard boundary condition for the framework: Octochains' architecture is not a general-purpose improvement over single-model inference, and should not be reached for on tasks that require one continuous chain of reasoning rather than genuinely independent sub-problems.

**Error containment via centralization.** The study measured error amplification, how far a single agent's mistake propagates into the final output. Independent parallel agents with no communication and no synthesis step amplified errors by up to 17.2x. Centralized architectures, where an orchestrator synthesizes and audits the parallel outputs before finalizing, contained that same amplification to 4.4x. Octochains has no "independent, no aggregator" execution mode; the `Engine` always requires an `Aggregator`, which structurally rules out the configuration the research identifies as least reliable.

---

## 8. Extensibility Model

The framework exposes exactly two extension points, both abstract methods: `Agent.execute()` and `Aggregator.execute()`. Everything else (`_build_prompt()`, `format_output()`, `_format_reports()`, the Skills loader) is a default implementation a subclass can call, partially override, or ignore entirely. A minimal custom agent is:

```python
class TechAnalyst(Agent):
    def __init__(self, llm_callable):
        super().__init__(
            role="Chief Technology Officer",
            goal="Evaluate technical feasibility and database scalability.",
            llm_callable=llm_callable
        )

    def execute(self, problem_data: str) -> str:
        system_prompt = self._build_prompt(problem_data)
        return self.llm_callable(f"{system_prompt} Please provide your expert analysis.")
```

Because `execute()` owns the full request loop, tool-calling is unopinionated: a subclass can inject a provider's native tool schema (OpenAI functions, Anthropic tool use) directly into its own API call inside `execute()`, and the framework never mediates or wraps that call. The trade-off is that Octochains has no built-in tool-orchestration layer of its own; it is a coordination and consensus layer that sits above whatever request-execution logic the developer writes.

---

## 9. Roadmap: In-Progress Technical Work

- **`MajorityVote` aggregator**: currently stubbed out (`aggregators/__init__.py` imports it commented out) pending final implementation. Design calls for two selectable strategies mirroring `ConflictChecker`'s pattern: a deterministic `verdict_field`-based JSON parse, and an LLM-extraction fallback, with tie-breaking routed through a single additional LLM call only when a tie is detected, and an honest "unresolved tie" result if no LLM is available for tie-breaking. The result schema (`MajorityVoteResult`) is planned to carry `final_verdict`, `vote_counts`, `margin`, `dissenting_agents`, `was_tie`, and `tie_break_rationale`.
- **Human-in-the-loop gateways**: a planned intercept protocol allowing a human reviewer to pause execution at a decision fork, most likely surfaced as an optional callback or gate evaluated between Phase 1 (parallel analysis) and Phase 3 (aggregation) in `Engine.run()`, given the two-phase gating pattern already established for `require_all_agents`.
- **Expanded preset and Skill catalog**: the Skills system's flat, dependency-free format is designed to make community-contributed `SKILL.md` files reviewable as plain markdown diffs, which is the current mechanism for growing the preset catalog via external contribution.

---

## 10. Summary

Octochains' technical thesis is narrow and specific: for tasks that genuinely decompose into independent sub-problems, run the sub-problems in structurally isolated threads, normalize every possible output shape into one contract, fail loudly and specifically rather than silently, and route everything through exactly one auditable synthesis step. Every mechanism described in this paper, the duplicate-role check, the two-gate failure model, the `<think>` tag stripping, the deterministic weight resolution in `WeightedSynthesizer`, the flat-file Skill parser, exists to make that thesis hold up under real failure conditions rather than only in a demo.

---

*Code references: github.com/ahmadvh/octochains, `main` branch, `src/octochains/{engine,base,skills,schema}.py` and `src/octochains/aggregators/{conflict_checker,weighted_synthesizer}.py`. Research reference: Kim, Y. et al., "Towards a Science of Scaling Agent Systems," arXiv:2512.08296 (2026).*