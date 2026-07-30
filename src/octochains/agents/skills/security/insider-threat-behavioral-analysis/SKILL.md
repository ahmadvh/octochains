---
name: insider-threat-behavioral-analysis
description: Detects anomalous behavior from authenticated, legitimate users — unusual data exports, off-hours access, and unauthorized exfiltration — and weighs negligence against malicious intent.
version: 1.0.0
---

## Objective

Analyze the activity of *already-authenticated, legitimate* users to detect insider misuse. The access itself is assumed valid; the question is whether the user's *behavior* deviates from their expected baseline in a way that suggests data exfiltration, abuse of privilege, or negligence.

## Execution Protocol

1. **Baseline Deviation:** Establish what "normal" looks like for the user or their peer group from the provided data, then flag deviations:
   - **Timing:** access or exports well outside the user's usual working hours or established pattern.
   - **Volume:** downloads/exports far exceeding the user's historical norm or role expectation (e.g. bulk-exporting an entire customer table when the role touches single records).
   - **Scope:** access to data or systems unrelated to the user's function, or a sudden broadening of what they touch.
2. **Exfiltration Signals:** Flag movement of data toward exit channels — mass downloads, copies to removable/personal storage, uploads to external services, or forwarding to personal accounts.
3. **Intent Assessment:** For each finding, weigh **negligence** (misconfiguration, convenience shortcuts, unaware policy violation) against **malicious intent** (staging data before resignation, deliberate concealment, access timed to avoid oversight). When the evidence does not clearly favor one, **explicitly flag it as ambiguous** rather than guessing.
4. **Prioritization:** Rank findings by the combination of data sensitivity and the strength of the exfiltration/intent signal.

## Constraints

- Report only findings supported by the provided access, export, and privileged-activity evidence.
- Note when evidence needed to judge intent or baseline is missing (e.g. no historical activity, no peer baseline, no destination for an export).
- **Scope constraint:** Analyze only misuse by authenticated, legitimate users. Do **NOT** analyze external indicators of compromise or unauthenticated intrusions — those belong to the Security Threat Hunter.

## Output Format

**Overall Insider-Risk Level:** [LOW | MEDIUM | HIGH | CRITICAL]

**Priority Findings:**
- [Finding 1]
- [Finding 2]

**Baseline Deviations:**
- [Timing / volume / scope anomalies observed, or "none observed"]

**Exfiltration Signals:**
- [Data-movement indicators toward exit channels]

**Intent Assessment:**
- [Per finding: negligence | malicious | AMBIGUOUS — with the reasoning]

**Evidence Gaps:**
- [Missing baseline or destination data limiting confidence]

**Recommended Next Steps:**
- [Investigation or containment actions scoped to insider misuse]
