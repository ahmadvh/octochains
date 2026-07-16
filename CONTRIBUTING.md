# Contributing to Octochains

First off, thank you for considering contributing to Octochains! It’s people like you who will help build the universal reasoning layer for high-stakes AI.

---

### Contribution Workflow

1. Fork the repository and create your branch from `main`.
2. Code your contribution following the standards below.
3. Test your Agent, Skill, or Aggregator locally (see testing notes below).
4. Submit a Pull Request. By submitting, you agree to the licensing terms in the [Licensing of Contributions](#licensing-of-contributions) section below.
5. All PRs are personally vetted for logic, safety, and architectural fit.

---

### The Minimal-Dependency Rule

**Octochains stays lightweight.** The core framework (`src/octochains`) has exactly one dependency: **Pydantic**. Skill parsing (`skills.py`) is deliberately hand-rolled stdlib — no YAML library — to keep that count at one.

**Do NOT** add heavy ML SDKs (`langchain`, `llama-index`, `openai`, `anthropic`, `transformers`, etc.) to `pyproject.toml`.

If you're building an integration, demo, or specific LLM wrapper, place it in `demo-examples/` where users opt into those dependencies themselves.

---

### 1. Adding a New Official Agent Preset

Official agents in Octochains are built from two pieces: a **Skill** (the domain knowledge, as a markdown file) and a **preset factory function** (the wiring). You do not need to write a new `Agent` subclass — `SkilledAgent` already handles execution.

**Step 1 — Write the Skill.**
Create a new folder under `src/octochains/agents/skills/<domain>/<skill-name>/SKILL.md`. Required frontmatter fields: `name`, `description`. Optional: `version`.

```markdown
---
name: your-skill-name
description: One sentence describing what this skill teaches the agent.
version: 1.0.0
---

## Your Skill Title
1. Step-by-step domain guidance goes here...
```

Rules for Skill content:
- **Provider-agnostic.** No vendor-specific prompting tricks, no assumptions about a particular model's context window.
- **Markdown only — no bundled scripts or executable code.** This is a hard rule; skills that execute code are a supply-chain risk we don't accept.
- Frontmatter is flat `key: value` pairs only — no nested lists or objects (our parser is intentionally simple, by design, to avoid a YAML dependency).

**Step 2 — Register the preset factory.**
Add a function to `src/octochains/agents/presets.py` following the existing pattern:

```python
def your_agent(llm_callable: LLMCallable, extra_skills: Optional[List[Skill]] = None) -> SkilledAgent:
    base_skills = _load_skills("octochains.agents.skills.<domain>", "your-skill-name")
    return SkilledAgent(
        role="Your Agent's Persona",
        goal="What this agent is trying to achieve.",
        input_description="What kind of input data this agent expects.",
        llm_callable=llm_callable,
        skills=base_skills + (extra_skills or [])
    )
```

**Step 3 — Register the package data.**
If this is a new domain folder, add it to `pyproject.toml`'s `package-data` so the SKILL.md ships inside the built wheel.

**Step 4 — Tests.**
At minimum: the preset raises without `llm_callable`, ships with the skill attached, has a non-empty `role`/`goal`, and correctly merges `extra_skills`. See `tests/test_presets.py` for the pattern.

**Step 5 — Docs.**
Add a row to the appropriate table in `README.md` under "Official Preset Agents."

---

### 2. Building a Fully Custom Agent (not a preset)

If your contribution needs custom execution logic beyond prompting — live API calls, custom tool-calling, a different output structure — subclass `Agent` directly instead of using a preset:

```python
from octochains.base import Agent
from typing import Callable, Any


class NetworkSecurityAgent(Agent):
    """Scans network logs for unauthorized access attempts and misconfigurations."""

    def __init__(self, llm_callable: Callable[[str], Any]):
        super().__init__(
            role="Network Security Specialist",
            goal="Identify active intrusion patterns and open-port vulnerabilities.",
            input_description="A raw network log or firewall configuration file.",
            llm_callable=llm_callable
        )

    def execute(self, problem_data: str) -> Any:
        # self._build_prompt() gives you the strict isolated identity prompt.
        # You own everything else — custom tool schemas, API calls, parsing.
        prompt = self._build_prompt(problem_data)
        return self.llm_callable(prompt)
```

These are contributed as standalone examples in `demo-examples/`, not registered as official presets, unless a maintainer explicitly agrees to adopt one into the core catalog.

---

### 3. Adding a New Official Aggregator

Aggregators live in `src/octochains/aggregators/`.

**Requirements:**
- Inherit from `octochains.Aggregator`.
- Process a `Dict[str, str]` of agent reports via `self._format_reports(...)`.
- Define a Pydantic output schema in `schema.py` (see `ConflictReport` as a reference) using `model_config = ConfigDict(extra='ignore')` so hallucinated LLM keys don't crash validation.
- Handle the "insufficient input" edge case explicitly — see `ConflictChecker`'s mathematical safety gate (aborts cleanly if fewer than 2 valid reports arrive) for the expected pattern.
- Export it from `src/octochains/aggregators/__init__.py`.
- Add tests covering: normal execution, malformed LLM output, and your insufficient-input edge case.
- Add a section to `README.md` under "Official Enterprise Aggregators."

---

### Creating Demo Examples

Demos are the best way to show Octochains in action, and the place for anything that needs a heavier dependency (an LLM SDK, `pandas`, etc.).

**Structure:**
```
cookbook/XX-your-demo/
├── requirements.txt   <-- MANDATORY: demo-specific libraries
├── run_demo.py        <-- MANDATORY: entry point
└── README.md          <-- optional: explain the use case
```
❌ Never add demo-specific dependencies to the core `pyproject.toml`.

---

## Code Standards

### Threading Safety
⚠️ **Critical:** Agents run in parallel threads via `Engine`. Avoid global state, mutable module-level variables, or non-thread-safe resources inside `execute()`. Your code should be stateless relative to other agents.

### Type Hinting
All public methods and function signatures need type hints. Use `LLMCallable` (`Callable[[str], Any]`) for model execution parameters.

### Documentation
Every class needs a docstring. Be descriptive — docstrings are read by contributors, not by the LLM (unlike the Skill markdown content, which the model does read).

### Error Handling
Never let a failed LLM call crash the Engine. Rely on `format_output()`'s existing safety nets rather than adding new ad hoc exception handling.

---

### Licensing of Contributions

Octochains operates under a Fair-Code model, distributed under the **Business Source License 1.1** (see [LICENSE.md](LICENSE.md) for the full commercial-use restriction and 2030 sunset date).

By submitting a pull request to this repository, you agree to the following:

- You wrote the contribution yourself, or otherwise have the right to submit it under these terms.
- You grant Ahmad Varasteh (Octochains) permission to license your contribution under BSL 1.1, or any future terms he chooses, in order to keep the project's licensing consistent and sustainable.
- Your contribution comes as-is, without warranty of any kind, and you won't be liable for any damages related to it, to the extent the law allows.
- You acknowledge your contribution will automatically transition to Apache License 2.0 alongside the rest of the codebase on the project's Change Date (May 10, 2030).

No separate signature or paperwork is required — submitting a PR constitutes agreement to these terms.

---

### Questions?

Open an Issue, or reach out directly:

📩 ahmad.vh7@gmail.com

---

Let's build the future of parallel reasoning together! ✨
<img referrerpolicy="no-referrer-when-downgrade" src="https://static.scarf.sh/a.png?x-pxid=a2cb3b15-b3c7-4f80-9113-2405c8554543" />
