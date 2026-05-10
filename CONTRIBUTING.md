### Contributing to Octochains 
First off, thank you for considering contributing to Octochains! It’s people like you who will help build the universal reasoning layer for high-stakes AI.

---

### Contribution Workflow
1. Fork the repository and create your branch from main.

2. Code your contribution following the directory standards below.

3. Test your agent or demo in an isolated environment.

4. Submit a Pull Request (PR). Note that all PRs are personally vetted for logic, safety, and architectural fit.

---

### The Hub Architecture
Octochains uses a Package Registry system. To ensure users can use clean shorthand imports, every new component must be registered.

1. **Adding a New Agent**
Agents live in domain-specific folders inside `src/octochains/agents/`.
      - **Placement:** Create a new .py file in an existing domain folder (e.g., medical/) or create a new domain folder if it doesn't exist.

      - **Requirements:** 
        - Inherit from the octochains.Agent base class.
        - Define a clear `role` and `goal` in super().__init__.
        - Implement the `execute(self, data: str)` method.

      - **Registration (Crucial):**
    You must update the `__init__.py` inside your domain folder to export your agent.
```python
# src/octochains/agents/medical/__init__.py
from .your_new_file import YourAgentClass
```
--- 

#### 💡 Example: Creating a Cybersecurity Agent
Here is how a typical "Expert" agent should look. This example uses a `@tool` and follows the `octochains` standard:
```python
from octochains import Agent, tool

class NetworkSecurityAgent(Agent):
    """
    This agent specializes in scanning network logs for unauthorized 
    access attempts and firewall misconfigurations.
    """

    def __init__(self):
        # 1. Define the Identity: This is broadcasted to the Aggregator
        super().__init__(
            role="Network Security Specialist",
            goal="Identify active intrusion patterns and open-port vulnerabilities."
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

    def execute(self, data: str) -> str:
        """
        The 'data' parameter is the full complex problem broadcasted by the Engine.
        In this method, you use your tools and your preferred LLM to 
        generate a specialized report.
        """
        
        # In a real-world scenario, you would pass self.tools to your LLM:
        # response = client.chat.completions.create(..., tools=self.tools)
        
        # For this example, we'll simulate an analysis:
        vulnerability_report = self.check_port_status(22)
        
        return f"Specialist Analysis: Found critical vulnerability. {vulnerability_report}"
```
---

### Creating Demo Examples
Demos are the best way to show Octochains in action. To keep the core framework lightweight, we enforce Strict Demo Isolation.
- **Placement:** Create a numbered folder in `demo-examples/` (e.g., `02-cybersecurity-threat-hunt`).
- **Structure:**
```plaintest
demo-examples/XX-your-demo/
├── requirements.txt  <-- MANDATORY: List all demo-specific libraries
├── run_demo.py       <-- MANDATORY: The entry point for the demo
└── README.md         <-- Optional: Explain the use case
```
- **The Dependency Rule:** If your demo requires libraries not found in the core `octochains` package (like `pandas`, `litellm`, or `biopython`), they must be listed in your demo's `requirements.txt`. 
❌ Do not add them to the core `pyproject.toml`.
---
### Code Standards

To keep the Octochains codebase clean and maintainable for everyone, please adhere to the following standards:

* **Threading Safety**: ⚠️ **Critical**: Agents in Octochains run in parallel threads. Avoid using global state, mutable module-level variables, or non-thread-safe resources within an Agent's `execute` method. Your code should be "Stateless" relative to other agents.
* **Type Hinting**: We follow modern Python practices. All public methods and function signatures **must** include Python type hints (e.g., `data: str -> str`).
* **Documentation**: We prioritize clarity. Include descriptive docstrings for all classes and `@tool` methods. Remember: The text in your tool's docstring is often what the LLM uses to understand how to call it!

---

### Licensing of Contributions

Octochains operates under a **Fair-Code** model. By submitting a contribution to this repository, you agree to the following:

1. **BSL 1.1 Licensing**: You agree that your contributions will be licensed under the **Business Source License 1.1**. This allows the project to remain sustainable while keeping the source code public and free for most users.
2. **Automatic Open Source Transition**: You acknowledge and agree that your contributions will automatically transition to the **Apache License, Version 2.0**, upon the project's predefined Change Date (the 4-year sunset). 

This structure ensures that while we protect the engine's development today, your work is guaranteed to eventually become part of a fully open-source public good.

### Questions?
If you have questions about where a specific expert belongs in the Hub or need help with the threading logic, feel free to [open an Issue](https://github.com/ahmadvh/octochains/issues) or reach out directly to the maintainer:

📩 [ahmad.vh7@gmail.com](mailto:ahmad.vh7@gmail.com)

**Let's build the future of parallel reasoning together!** ✨