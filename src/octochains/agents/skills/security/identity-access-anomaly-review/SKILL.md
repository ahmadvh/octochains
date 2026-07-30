---
name: identity-access-anomaly-review
description: Reviews authentication and authorization events for failed-login clustering, privilege-escalation chains, credential-stuffing patterns, and MFA-bypass indicators.
version: 1.0.0
---

## Objective

Analyze authentication and access-grant events to determine *how* access was obtained and whether that access was legitimate. Stay scoped to the identity layer: logins, credential use, authorization changes, and MFA events.

## Execution Protocol

1. **Failed-Login Clustering:** Group failed authentication attempts by account, source, and time window. Distinguish likely automation from human error using volume and velocity:
   - **Credential stuffing / brute force (suspicious):** many failures across *many distinct accounts* from few sources, or a high-velocity burst (e.g. 10+ failures against one account in under a minute) often followed by a success.
   - **User error (benign):** a small number of failures (typically fewer than ~5) against a single account, spread over time, with no eventual anomalous success.
2. **Privilege-Escalation Chains:** Reconstruct the sequence of authorization changes. Red-flag patterns include a rapid admin/role grant immediately preceding access to sensitive resources, self-granted privileges, escalation outside a change window, and grants that are never rolled back.
3. **Credential & MFA Anomalies:** Flag impossible-travel logins, reuse of a single credential across many source IPs, MFA-bypass or fallback-to-weaker-factor events, and successful logins that skipped an expected MFA challenge.
4. **Severity Prioritization:** When multiple findings exist, rank them by how directly they indicate unauthorized access was actually *achieved* (successful escalation > attempted escalation > isolated failed attempts).

## Constraints

- Report only findings supported by the provided authentication, IAM, and MFA evidence.
- Explicitly note when key evidence is missing (e.g. no MFA logs, no source-IP data) rather than inferring around the gap.
- **Scope constraint:** Stay purely at the access-grant and authentication layer. Do **NOT** evaluate post-login user behavior or data activity (that belongs to the Insider Threat Analyst) and do **NOT** attribute external threats or map IoCs (that belongs to the Security Threat Hunter).

## Output Format

**Overall Access-Risk Level:** [LOW | MEDIUM | HIGH | CRITICAL]

**Priority Findings:**
- [Finding 1]
- [Finding 2]

**Failed-Login Assessment:**
- [Clustering observed and whether it reads as automation or user error]

**Privilege-Escalation Chains:**
- [Reconstructed escalation sequences and red flags, or "none observed"]

**Credential / MFA Indicators:**
- [Impossible travel, credential reuse, MFA-bypass signals]

**Evidence Gaps:**
- [Missing logs or fields that limit confidence]

**Recommended Next Steps:**
- [Containment or investigation actions scoped to identity/access]
