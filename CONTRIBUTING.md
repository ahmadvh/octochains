# Contributing to Octochains

First off, thank you for considering contributing to Octochains! It’s people like you who will help build the universal reasoning layer for high-stakes AI.

---

### Contribution Workflow

1. Fork the repository and create your branch from `main`.

2. Code your contribution following the directory standards below.

3. Test your agent or demo in an isolated environment.

4. Submit a Pull Request (PR). Note that all PRs are personally vetted for logic, safety, and architectural fit.

---

### The "Zero-Dependency" Golden Rule

**Octochains must remain lightweight.**

**Do NOT** submit Pull Requests that add heavy ML SDKs (`langchain`, `llama-index`, `openai`, `anthropic`, `transformers`, etc.) to the `requirements.txt` or `pyproject.toml`.

The core framework (`src/octochains`) must only rely on standard Python libraries.

If you are building an integration, demo, or specific wrapper, place it in the `demo-examples/` directory where users can choose to install those dependencies themselves.

---

### The Hub Architecture

Octochains uses a Package Registry system. To ensure users can use clean shorthand imports, every new component must be registered.

---

### 1. Adding a New Agent

Agents live in domain-specific folders inside `src/octochains/agents/`.

### Placement

Create a new `.py` file in an existing domain folder (e.g., `medical/`) or create a new domain folder if it doesn't exist.

### Requirements

- Inherit from the `octochains.Agent` base class.
- Define a clear `role`, `goal`, and `input_description` in `super().__init__`.
- **Dependency Injection:** Do not hardcode LLM calls inside your agent. Your agent must accept `llm_callable` in its `__init__` and pass it to the base class.
- Implement the `execute(self, problem_data: str) -> Any` method.
- Use `self._build_prompt(problem_data)` to automatically inject the double-blind isolation instructions and `@tool` schemas.

### Registration (Crucial)

You must update the `__init__.py` inside your domain folder to export your agent.

```python
# src/octochains/agents/medical/__init__.py

from .your_new_file import YourAgentClass
```

---

### 2. Adding a New Aggregator

Aggregators live in `src/octochains/aggregators/`.

## Placement

Create your logic file in the `aggregators` directory.

## Requirements

- Inherit from `octochains.Aggregator`.
- Aggregators process a dictionary of reports (`Dict[str, str]`).
- **Structured Outputs:** Aggregators return `Any`. You are highly encouraged to build aggregators that return clean JSON dictionaries or Pydantic models for API readiness.

---

### 💡 Example: Creating a Cybersecurity Agent

Here is how a typical "Expert" agent should look. This example uses a `@tool` and follows the updated Octochains BYO-LLM standard:

```python
from octochains import Agent, tool
from typing import Callable, Any


class NetworkSecurityAgent(Agent):
    """
    This agent specializes in scanning network logs for unauthorized
    access attempts and firewall misconfigurations.
    """

    def __init__(self, llm_callable: Callable[[str], Any]):

        # 1. Define the Identity:
        # This is passed to the base class prompt builder

        super().__init__(
            role="Network Security Specialist",
            goal="Identify active intrusion patterns and open-port vulnerabilities.",
            input_description="A raw network log or firewall configuration file.",
            llm_callable=llm_callable
        )

    @tool
    def check_port_status(self, port: int) -> str:
        """
        Queries the system firewall for the status of a specific port.

        Args:
            port: The network port number to check (e.g., 22, 80).
        """

        # Logic for the tool goes here

        protected_ports = [22, 3389]

        if port in protected_ports:
            return f"Port {port} is OPEN and vulnerable."

        return f"Port {port} is closed/secured."

    def execute(self, problem_data: str) -> Any:
        """
        The 'problem_data' parameter is the full complex problem
        broadcasted by the Engine.
        """

        # 2. The base class automatically builds the prompt
        # and injects the check_port_status tool schema!

        prompt = self._build_prompt(problem_data)

        # 3. Execute using the user's provided LLM

        return self.llm_callable(prompt)
```

---

### Creating Demo Examples

Demos are the best way to show Octochains in action.

To keep the core framework lightweight, we enforce **Strict Demo Isolation**.

## Placement

Create a numbered folder in `demo-examples/`.

Example:

```plaintext
demo-examples/02-cybersecurity-threat-hunt
```

## Structure

```plaintext
demo-examples/XX-your-demo/
├── requirements.txt  <-- MANDATORY: List all demo-specific libraries
├── run_demo.py       <-- MANDATORY: The entry point for the demo
└── README.md         <-- Optional: Explain the use case
```

### The Dependency Rule

If your demo requires libraries not found in the core `octochains` package (like `pandas`, `litellm`, or `biopython`), they must be listed in your demo's `requirements.txt`.

❌ Do not add them to the core `pyproject.toml`. 

---

# Code Standards

To keep the Octochains codebase clean and maintainable for everyone, please adhere to the following standards.

---

### Threading Safety

⚠️ **Critical:** Agents in Octochains run in parallel threads.

Avoid using:
- Global state
- Mutable module-level variables
- Non-thread-safe resources within an Agent's `execute` method

Your code should be **Stateless** relative to other agents.

---

### Type Hinting

We follow modern Python practices.

All public methods and function signatures must include Python type hints.

Use our custom `LLMCallable` alias (`Callable[[str], Any]`) for model execution parameters.

---

## Documentation

We prioritize clarity.

Include descriptive docstrings for:
- All classes
- All `@tool` methods

Remember:
The text in your tool's docstring is what the LLM uses to understand how to call it.

---

### Error Handling

Never let a failed LLM call crash the Engine.

Rely on the `format_output` safety nets in the base classes to prevent dictionary mapping crashes.

---

### Licensing of Contributions

Octochains operates under a Fair-Code model.

By submitting a contribution to this repository, you agree to the following:

**BSL 1.1 Licensing**

You agree that your contributions will be licensed under the Business Source License 1.1. This allows the project to remain sustainable while keeping the source code public and free for most users.

**Automatic Open Source Transition**

You acknowledge and agree that your contributions will automatically transition to the Apache License, Version 2.0, upon the project's predefined Change Date (the 4-year sunset). This structure ensures that while we protect the engine's development today, your work is guaranteed to eventually become part of a fully open-source public good.

---

### Questions?

If you have questions about where a specific expert belongs in the Hub or need help with the threading logic, feel free to open an Issue or reach out directly to the maintainer:

📩 ahmad.vh7@gmail.com

---

Let's build the future of parallel reasoning together! ✨
<img referrerpolicy="no-referrer-when-downgrade" src="https://static.scarf.sh/a.png?x-pxid=a2cb3b15-b3c7-4f80-9113-2405c8554543" />
