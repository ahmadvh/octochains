# 08 — Security Incident Triage (Anthropic / Claude)

Point three security specialists at the *same* incident export and let each one
analyse it in complete isolation, then merge their independent findings into a
single triage memo.

- **Security Threat Hunter** — external intrusion, indicators of compromise, ATT&CK tactics
- **Insider Threat Analyst** — misuse by an authenticated user (anomalous exports, off-hours access, privilege changes)
- **Breach Notification Analyst** — regulatory exposure: does this trigger GDPR Art. 33 / 34 notification duties?

Because each specialist runs isolated (no shared context), they don't anchor on
each other — the threat hunter, the insider-threat lens, and the regulatory lens
each reach the incident independently. A `Synthesizer` then reconciles them.

The `sample_input/incident_log.txt` is a synthetic case that deliberately spans
all three angles at once: a TOR-exit login with impossible travel, an
authenticated user granting a service account CRM-Admin and bulk-exporting
248k customer records off-network, and that data containing personal fields
(name, email, DOB, national ID, card last-4).

## Provider

**Anthropic (Claude)** via the official `anthropic` SDK. The `call_claude`
function is the `llm_callable` — swap `MODEL_NAME` for `claude-sonnet-5` or
`claude-haiku-4-5` for a cheaper/faster run.

## Run

```bash
export ANTHROPIC_API_KEY=sk-ant-...
pip install -r requirements.txt
python run_demo.py
```

## Presets used

All three are official Security-category presets:
[`security_threat_hunter`](../../README.md#official-preset-agents),
`insider_threat_analyst`, and `breach_notification_analyst`.
