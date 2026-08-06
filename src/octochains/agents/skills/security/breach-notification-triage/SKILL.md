---
name: breach-notification-triage
description: Determines whether a security incident involves personal data, triggers regulatory breach-notification obligations (e.g. GDPR Art. 33/34), and what notification timelines apply.
version: 1.0.0
---

## Objective

Assess a security incident purely through a regulatory breach-notification lens: decide whether personal data was affected, which notification obligations are triggered, and the deadlines that apply.

## Execution Protocol

1. **Data Classification:** From the evidence, separate affected *personal data* (anything that identifies or relates to a natural person — names, emails, credentials, government/customer IDs, location, health or financial records) from purely *system or infrastructure data* (internal IPs, service metrics, non-personal configuration). Only exposure of personal data can trigger notification duties.
2. **Breach Determination:** Decide whether the incident is a personal-data breach — a breach of security leading to the unlawful destruction, loss, alteration, or unauthorized disclosure of or access to personal data. State which aspect is affected: confidentiality, integrity, or availability.
3. **Authority Notification (GDPR Art. 33):** If a personal-data breach is likely, assess the duty to notify the supervisory authority without undue delay and, where feasible, within **72 hours** of becoming aware of it. Identify the "awareness" moment the clock runs from. The exemption is where the breach is "unlikely to result in a risk to the rights and freedoms" of individuals.
4. **Individual Notification (GDPR Art. 34):** Determine whether the breach is likely to result in a **high risk** to individuals, which additionally requires notifying the affected data subjects without undue delay. Note recognized mitigations that can remove this duty (e.g. the affected data was rendered unintelligible through strong encryption).
5. **Timeline & Obligations Summary:** State each triggered obligation, its deadline, and its recipient (supervisory authority vs. affected individuals vs. none).

## Constraints

- Base every conclusion on the provided evidence; call out missing information (e.g. unknown data categories, no record of what was actually accessed) rather than assuming.
- Focus only on notification obligations and timelines. Do **not** perform technical severity, intrusion, or root-cause analysis — that is the Security Threat Hunter's scope.
- Default to GDPR (Art. 33/34) framing; note another regime may also apply only where the evidence clearly indicates it.
- This is a triage aid, not legal advice; recommend confirmation with a qualified DPO or counsel for the final determination.

## Output Format

**Personal Data Involved:** [YES | NO | UNCERTAIN]

**Affected Data Categories:**
- [e.g. account credentials, email addresses, health records]

**Breach Assessment:** [Personal-data breach: YES | NO | UNCERTAIN] — [confidentiality | integrity | availability]

**Authority Notification (GDPR Art. 33):** [REQUIRED | NOT REQUIRED | UNCERTAIN] — deadline: within 72 hours of awareness ([awareness reference])

**Individual Notification (GDPR Art. 34):** [REQUIRED (high risk) | NOT REQUIRED | UNCERTAIN] — [applicable mitigations, if any]

**Missing Information:**
- [Evidence gaps affecting the determination]

**Recommended Next Steps:**
- [e.g. escalate to DPO, document the awareness timestamp, prepare the Art. 33 notification]
