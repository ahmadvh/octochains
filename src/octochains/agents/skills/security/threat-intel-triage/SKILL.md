---
name: threat-intel-triage
description: Identifies indicators of compromise, anomalous network/endpoint behavior, and active intrusion patterns from the provided data.
version: 1.0.0
---

## Objective

Analyze security logs to identify suspicious activity and potential cyber attacks.

## Execution Protocol

1. **Threat Detection:** Identify unusual activity that may indicate a security attack, such as unusual outbound traffic, privilege escalation patterns, or off-hours access.
2. **Severity Prioritization:** If several suspicious activities are found, prioritize the most critical findings based on their severity.
3. **Framework Mapping:** If possible, relate the suspicious activity to the appropriate MITRE ATT&CK tactic.

## Constraints

- Report only findings supported by the provided evidence.
- Mention if any important information is missing.
- Don't assume an attack occurred if there is insufficient supporting evidence.

## Output Format

**Overall Threat Level:** [LOW | MEDIUM | HIGH | CRITICAL]

**Priority Findings:**
- [Finding 1]
- [Finding 2]

**Indicators of Compromise:**
- [Observed IoCs]

**MITRE ATT&CK Mapping:**
- [Relevant tactic categories]

**Recommended Next Steps:**
- [Immediate investigation or containment actions]
