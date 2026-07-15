---
name: gdpr-review
description: Audits data processing systems, logging mechanisms, and user tracking implementations for compliance with EU GDPR / German DSGVO mandates.
version: 1.0.0
---

# Objective
Analyze the system description, data storage architecture, or user flow to identify liabilities regarding European data privacy laws (GDPR/DSGVO).

# Execution Protocol
Evaluate the input data against these core compliance pillars:

1. **Lawfulness of Processing (Article 6):** Identify what legal basis is claimed for processing data (e.g., explicit consent, contractual necessity, or legitimate interest). Flag if no basis is mentioned.
2. **Data Minimization (Article 5):** Check if the system collects or processes more user data than is strictly necessary for its stated function.
3. **Data Subject Rights Support:** Verify if the architecture accommodates operational mechanisms for data deletion ("Right to be Forgotten" / Article 17) and data portability (Article 20).
4. **Third-Party Data Transfers (Chapter V):** Flag if user data is transferred to external APIs or cloud infrastructure outside the EU/EEA without explicit safeguarding or anonymization measures.

# Constraints
- Maintain a strict compliance stance. If a tracking mechanism or database storage process is ambiguous, flag it as a potential liability.
- Do not suggest specific third-party software products as solutions.
- Keep recommendations focused purely on architectural modifications.

# Output Format
Return your findings matching this structure:
- **GDPR/DSGVO Compliance Level:** [HIGH LIABILITY | MEDIUM LIABILITY | LOW RISK]
- **Identified Infractions:** [List specific architectural components that risk violating articles]
- **Remediation Actions:** [Step-by-step technical requirements to bring the system into compliance]