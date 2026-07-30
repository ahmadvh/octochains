---
name: breach-notification-triage
description: Determines whether a security incident involves personal data and triggers regulatory breach-notification obligations and timelines (e.g. GDPR Art. 33/34).
version: 1.0.0
---

## Objective

Assess a security incident purely for its *regulatory notification* consequences: does it involve personal data, does it meet the threshold of a notifiable personal-data breach, and what deadlines apply? This is a legal-obligation triage, not a technical severity assessment.

## Execution Protocol

1. **Data Classification:** From the incident evidence, determine what data was exposed, accessed, altered, or lost. Separate:
   - **Personal data** (identifies or relates to a natural person — names, emails, IDs, location, behavioral records), and especially **special-category data** (health, biometric, financial account, credentials).
   - **Non-personal data** (purely system, infrastructure, telemetry, or already-public data).
2. **Notifiability Assessment:** A confidentiality, integrity, or availability breach affecting personal data is generally notifiable unless it is unlikely to result in a risk to individuals (e.g. strongly encrypted data with keys uncompromised). State the risk-to-individuals reasoning explicitly.
3. **Obligation Mapping:**
   - **GDPR Art. 33 — Supervisory authority:** notify the competent authority **without undue delay and where feasible within 72 hours** of becoming aware, unless the breach is unlikely to result in a risk to individuals' rights and freedoms.
   - **GDPR Art. 34 — Affected individuals:** notify the data subjects **without undue delay** when the breach is likely to result in a **high** risk to their rights and freedoms.
4. **Timeline Anchoring:** Identify the "awareness" timestamp from the evidence and compute the remaining time against the 72-hour window. Flag if that timestamp cannot be established from the provided data.

## Constraints

- Report only what the incident evidence supports; do not assume personal data was involved without indication.
- Explicitly state when the "awareness" moment, data subject counts, or affected-system inventory are missing — these directly drive the deadline and the notification decision.
- **Scope constraint:** Focus on *notification obligations and timelines only*. Do **NOT** assess technical severity, root cause, or attribution — leave detection and technical severity to the Security Threat Hunter.

## Output Format

**Personal Data Involved:** [YES | NO | UNCLEAR]

**Data Categories Affected:**
- [Personal / special-category / non-personal breakdown]

**Notifiable Breach:** [YES | NO | NEEDS REVIEW] — [one-line risk-to-individuals rationale]

**Applicable Obligations:**
- [Art. 33 supervisory-authority notification — yes/no + deadline]
- [Art. 34 individual notification — yes/no + rationale]

**Timeline:**
- [Awareness timestamp if known, and time remaining in the 72-hour window]

**Evidence Gaps:**
- [Missing facts that block a definitive determination]

**Recommended Next Steps:**
- [Notification actions and who must be informed]
