---
name: eu-ai-act-tiering
description: Classifies proposed AI deployments into strict EU AI Act risk tiers.
version: 1.0.0
---

# Objective
Analyze the system description and assign an irreversible risk classification based on the EU AI Act legal framework.

# Execution Protocol
1. **Unacceptable Risk Check:** Does the system use subliminal techniques, exploit vulnerabilities, biometric categorization by sensitive traits, or social scoring? (If yes -> UNACCEPTABLE).
2. **High Risk Check:** Is the system used in critical infrastructure, employment/HR, essential private/public services (e.g., healthcare triage, insurance eligibility), or law enforcement? (If yes -> HIGH RISK).
3. **Transparency Risk Check:** Is the system an AI chatbot, deepfake generator, or emotion recognition system? (If yes -> LIMITED RISK, requires transparency labeling).
4. **Minimal Risk:** All other applications (e.g., spam filters, inventory optimization).

# Constraints
- An insurance claims processing or health triage AI is automatically HIGH RISK.
- Provide the tier and exactly one sentence of justification citing the specific use-case trigger.

# Output Format
Risk Classification: [TIER]
Justification: [Reasoning]