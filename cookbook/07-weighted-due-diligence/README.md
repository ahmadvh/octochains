# Demo 06: Weighted Due-Diligence, Emphasis Without Erasure

This demo showcases `WeightedSynthesizer`, the aggregator built for a problem
`Synthesizer` and `ConflictChecker` don't solve: **the same evidence needs a
different throughline depending on who's reading it and why.**

## The Business Problem: "The Report Nobody Can Use"

A due-diligence council of five C-suite specialists, CFO, CTO, CRO, CPO, CMO,
evaluates a target company in full parallel isolation, exactly as any other
Octochains council would. That part isn't new.

The problem shows up at synthesis time. A plain `Synthesizer` gives every
perspective equal narrative weight by default. That's the right call when you
genuinely want a balanced, neutral brief. But real due-diligence reports are
almost never read that way, an engineering-talent acquihire and a
growth-equity term sheet are evaluating the *same* target for entirely
different reasons, and a report that averages five equally-weighted opinions
together tends to bury the one perspective that actually matters to the
decision being made.

`ConflictChecker` doesn't help here either, this isn't a case of the experts
disagreeing. All five reports can be perfectly consistent with each other, and
the report can still fail its audience because the wrong voice is leading.

---

## The Octochains Solution

`WeightedSynthesizer` lets you assign proportional emphasis per agent role.
Higher-weighted perspectives drive the framing and conclusions; lower-weighted
ones are still fully represented, just as supporting context rather than the
throughline. This demo runs the **exact same isolated council output** through
two different weight profiles to make the effect concrete:

- **Acquihire Framing**, `CTO: 0.55, CPO: 0.20`, rest low. The narrative
  should be built around the engineering team and the proprietary indexing
  architecture.
- **Growth-Equity Framing**, `CFO: 0.40, CMO: 0.25, CRO: 0.20`, rest low. The
  narrative should be built around burn, runway, CAC efficiency, and revenue
  trajectory.

Same five expert reports. Same target company. Two legitimate, differently
shaped verdicts.

---

## Technical Architecture

### Phase 1: Parallel Domain Isolation (run once)

The five presets, `cfo_agent`, `cto_agent`, `cro_agent`, `cpo_agent`,
`cmo_agent`, evaluate the target dossier simultaneously, in complete
isolation, exactly as in any Octochains council.

This demo deliberately runs Phase 1 **exactly once**. To do that without
committing to a synthesis, it plugs a trivial `PassthroughAggregator` into
`Engine`, a five-line `Aggregator` subclass that makes no LLM call and just
returns the isolated reports unchanged:

```python
class PassthroughAggregator(Aggregator):
    def __init__(self):
        super().__init__(role="Passthrough", goal="Pass reports through unchanged.")

    def execute(self, agent_reports):
        return agent_reports
```

This is a good illustration of how lightweight the `Aggregator` contract in
`base.py` really is, it only requires `execute(agent_reports) -> Any`.

### Phase 2: Reweight, Don't Re-Query

The isolated reports collected in Phase 1 are fed into **two separate
`WeightedSynthesizer` instances**, one per weight profile. No agent is
re-executed between profiles, only the aggregation lens changes:

```python
boss = WeightedSynthesizer(
    llm_callable=call_openai,
    weights={
        "Chief Technology Officer (CTO)": 0.55,
        "Chief Product Officer (CPO)": 0.20,
        "Chief Financial Officer (CFO)": 0.10,
        "Chief Revenue Officer (CRO)": 0.075,
        "Chief Marketing Officer (CMO)": 0.075,
    },
)
result = boss.execute(valid_reports)
```

Each `result` carries a deterministic audit trail, `dominant_perspective` and
`weights_applied` are computed directly from the configured weights, not
returned by the LLM, so they always reflect the real configuration regardless
of what the model does with the prose.

---

## What This Demo Surfaces

- **The Acquihire narrative** leads with the sub-40ms proprietary indexing
  engine, the ex-Google/DeepMind engineering bench, and the two informal
  acquisition approaches that already cited the architecture as the draw,
  with the thin pipeline and paused ad channel folded in as secondary risk
  notes rather than headline concerns.
- **The Growth-Equity narrative** leads with the 9-month runway against
  $340K/month burn, the 4x-over-target CAC on the paused LinkedIn campaign,
  and the fact that only 2 of 6 pilots have converted to signed ARR, with the
  technical differentiation folded in as a supporting asset rather than the
  thesis.

Neither narrative contradicts the other. That's the point: `WeightedSynthesizer`
isn't resolving disagreement, it's choosing which true story to tell first.

---

## Running the Demo

Ensure your environment variables are configured with your OpenAI API key:

```bash
export OPENAI_API_KEY="your-api-key-here"
```

Install dependencies:

```bash
pip install -r cookbook/06-weighted-due-diligence/requirements.txt
```

Navigate to the repo root and execute the demo:

```bash
python cookbook/06-weighted-due-diligence/run_demo.py
```

Output (both narratives, side by side) is written to
`cookbook/06-weighted-due-diligence/results/output.txt`.
