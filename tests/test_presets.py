"""
Tests for SkilledAgent and the official preset catalog.
"""
import pytest
from octochains.skills import Skill
from octochains.agents.skilled_agent import SkilledAgent
from octochains.agents import presets
from octochains.agents.presets import (
    cfo_agent, cto_agent, cro_agent, cpo_agent, cmo_agent,
    data_sovereignty_auditor, ai_risk_assessor, phi_sanitizer, licensing_reviewer,security_threat_hunter,
)


# =============================================================================
# HELPERS
# =============================================================================

def make_skill(name="test-skill", description="A test skill.", content="Test skill body.", version="1.0.0"):
    return Skill(name=name, description=description, version=version, content=content)


def simple_llm(prompt: str) -> str:
    return "MOCK_RESPONSE"


ALL_PRESET_FACTORIES = [
    cfo_agent, cto_agent, cro_agent, cpo_agent, cmo_agent,
    data_sovereignty_auditor, ai_risk_assessor, phi_sanitizer, licensing_reviewer,security_threat_hunter,
]

EXPECTED_ROLES = {
    cfo_agent: "Chief Financial Officer (CFO)",
    cto_agent: "Chief Technology Officer (CTO)",
    cro_agent: "Chief Revenue Officer (CRO)",
    cpo_agent: "Chief Product Officer (CPO)",
    cmo_agent: "Chief Marketing Officer (CMO)",
    data_sovereignty_auditor: "Data Sovereignty Auditor",
    ai_risk_assessor: "AI Risk Assessor",
    phi_sanitizer: "Health Data Compliance Officer",
    licensing_reviewer: "Open-Source Compliance Engineer",
    security_threat_hunter: "Security Threat Hunter",
}


# =============================================================================
# 1. SkilledAgent — CONSTRUCTION  (unchanged — these already passed)
# =============================================================================

class TestSkilledAgentConstruction:

    def test_raises_when_skills_provided_without_llm_callable(self):
        with pytest.raises(ValueError, match="requires an llm_callable"):
            SkilledAgent(role="R", goal="G", llm_callable=None, skills=[make_skill()])

    def test_succeeds_when_no_skills_and_no_llm_callable(self):
        agent = SkilledAgent(role="R", goal="G", llm_callable=None)
        assert agent.skills == []
        assert agent.llm_callable is None

    def test_succeeds_with_both_skills_and_llm_callable(self):
        skill = make_skill()
        agent = SkilledAgent(role="R", goal="G", llm_callable=simple_llm, skills=[skill])
        assert agent.skills == [skill]

    def test_skills_defaults_to_empty_list_not_none(self):
        agent = SkilledAgent(role="R", goal="G", llm_callable=simple_llm)
        assert agent.skills == []
        assert isinstance(agent.skills, list)


# =============================================================================
# 2. SkilledAgent — execute() WITHOUT skills  (unchanged — already passed)
# =============================================================================

class TestSkilledAgentExecuteNoSkills:

    def test_execute_calls_llm_once_with_base_prompt(self):
        captured = []

        def llm(prompt):
            captured.append(prompt)
            return "MOCK_RESPONSE"

        agent = SkilledAgent(role="Generalist", goal="Do generic work.", llm_callable=llm)
        result = agent.execute("Some problem data.")

        assert result == "MOCK_RESPONSE"
        assert len(captured) == 1
        assert "Some problem data." in captured[0]
        assert "AVAILABLE SKILLS" not in captured[0]
        assert "APPLICABLE SKILL GUIDANCE" not in captured[0]

    def test_execute_without_llm_callable_raises_at_call_time(self):
        agent = SkilledAgent(role="R", goal="G", llm_callable=None)
        with pytest.raises(TypeError):
            agent.execute("data")


# =============================================================================
# 3. Agent skill helpers — get_skill() returns Optional[Skill], never raises
# =============================================================================

class TestAgentSkillHelpers:

    def test_get_skill_returns_the_skill_object_for_known_name(self):
        skill = make_skill(name="known", content="KNOWN CONTENT")
        agent = SkilledAgent(role="R", goal="G", llm_callable=simple_llm, skills=[skill])

        result = agent.get_skill("known")

        assert result is skill  # same object, not a copy
        assert result.content == "KNOWN CONTENT"

    def test_get_skill_returns_none_for_unknown_name(self):
        skill = make_skill(name="known")
        agent = SkilledAgent(role="R", goal="G", llm_callable=simple_llm, skills=[skill])
        assert agent.get_skill("missing") is None

    def test_get_skill_returns_none_when_agent_has_no_skills(self):
        agent = SkilledAgent(role="R", goal="G", llm_callable=simple_llm)
        assert agent.get_skill("anything") is None

    def test_skill_index_lists_all_bundled_skills(self):
        agent = SkilledAgent(
            role="R", goal="G", llm_callable=simple_llm,
            skills=[make_skill(name="skill-a", description="Desc A"),
                    make_skill(name="skill-b", description="Desc B")]
        )
        index = agent._skill_index()
        assert "skill-a: Desc A" in index
        assert "skill-b: Desc B" in index

    def test_skill_index_empty_string_when_no_skills(self):
        agent = SkilledAgent(role="R", goal="G", llm_callable=simple_llm)
        assert agent._skill_index() == ""


# =============================================================================
# 4. load_relevant_skills() — the REAL base-class default:
#    unconditionally concatenates ALL bundled skills' full content.
#    No LLM call, no selection. (Docstring notes this is overridable
#    in a subclass for dynamic routing — but that's not the shipped default.)
# =============================================================================

class TestLoadRelevantSkillsDefaultBehavior:

    def test_returns_empty_string_when_agent_has_no_skills(self):
        agent = SkilledAgent(role="R", goal="G", llm_callable=simple_llm)
        assert agent.load_relevant_skills("data") == ""

    def test_never_calls_the_llm(self):
        calls = []

        def tracking_llm(p):
            calls.append(p)
            return "should never be reached"

        agent = SkilledAgent(role="R", goal="G", llm_callable=tracking_llm, skills=[make_skill()])
        agent.load_relevant_skills("data")
        assert calls == []

    def test_includes_full_content_and_version_of_every_bundled_skill(self):
        s1 = make_skill(name="first", version="1.0.0", content="FIRST BODY")
        s2 = make_skill(name="second", version="2.0.0", content="SECOND BODY")
        agent = SkilledAgent(role="R", goal="G", llm_callable=simple_llm, skills=[s1, s2])

        result = agent.load_relevant_skills("data")

        assert "FIRST BODY" in result
        assert "SECOND BODY" in result
        assert "SKILL: first (v1.0.0)" in result
        assert "SKILL: second (v2.0.0)" in result

    def test_output_is_unaffected_by_problem_data_content(self):
        # Selection is unconditional — problem_data doesn't influence it.
        skill = make_skill(name="always-included", content="ALWAYS BODY")
        agent = SkilledAgent(role="R", goal="G", llm_callable=simple_llm, skills=[skill])

        assert "ALWAYS BODY" in agent.load_relevant_skills("wildly unrelated text")
        assert "ALWAYS BODY" in agent.load_relevant_skills("")


# =============================================================================
# 5. SkilledAgent.execute() WITH skills — single LLM call,
#    full skill guidance always injected when skills are present.
# =============================================================================

class TestSkilledAgentExecuteWithSkills:

    def test_execute_calls_llm_exactly_once(self):
        skill = make_skill(name="alpha-skill", content="ALPHA SKILL BODY")
        calls = []

        def llm(p):
            calls.append(p)
            return "FINAL_REPORT"

        agent = SkilledAgent(role="Specialist", goal="Goal.", llm_callable=llm, skills=[skill])
        result = agent.execute("Task data.")

        assert result == "FINAL_REPORT"
        assert len(calls) == 1

    def test_execute_injects_full_skill_content_into_the_single_prompt(self):
        skill = make_skill(name="alpha-skill", content="ALPHA SKILL BODY")
        captured = []

        def llm(p):
            captured.append(p)
            return "FINAL_REPORT"

        agent = SkilledAgent(role="Specialist", goal="Goal.", llm_callable=llm, skills=[skill])
        agent.execute("Task data.")

        prompt = captured[0]
        assert "APPLICABLE SKILL GUIDANCE" in prompt
        assert "ALPHA SKILL BODY" in prompt

    def test_execute_omits_guidance_block_when_agent_has_no_skills(self):
        captured = []

        def llm(p):
            captured.append(p)
            return "FINAL_REPORT"

        agent = SkilledAgent(role="Specialist", goal="Goal.", llm_callable=llm)  # no skills
        agent.execute("Task data.")

        assert "APPLICABLE SKILL GUIDANCE" not in captured[0]

    def test_skill_index_and_full_guidance_both_present_when_skills_exist(self):
        # _build_prompt() injects the cheap name/description index;
        # execute() separately appends the full-content guidance block.
        # Both should appear — they serve different purposes.
        skill = make_skill(name="listed-and-loaded", description="Shown as index entry.", content="FULL BODY TEXT")
        captured = []

        def llm(p):
            captured.append(p)
            return "FINAL_REPORT"

        agent = SkilledAgent(role="Specialist", goal="Goal.", llm_callable=llm, skills=[skill])
        agent.execute("Task data.")

        prompt = captured[0]
        assert "AVAILABLE SKILLS" in prompt
        assert "APPLICABLE SKILL GUIDANCE" in prompt
        assert "FULL BODY TEXT" in prompt

    def test_multiple_skills_all_appear_in_single_call(self):
        s1 = make_skill(name="first", content="FIRST BODY")
        s2 = make_skill(name="second", content="SECOND BODY")
        captured = []

        def llm(p):
            captured.append(p)
            return "FINAL_REPORT"

        agent = SkilledAgent(role="Specialist", goal="Goal.", llm_callable=llm, skills=[s1, s2])
        agent.execute("Task data.")

        prompt = captured[0]
        assert "FIRST BODY" in prompt
        assert "SECOND BODY" in prompt


# =============================================================================
# 6. Official presets — uniform behavior across the full catalog
#    (unchanged — these already passed)
# =============================================================================

@pytest.mark.parametrize("factory", ALL_PRESET_FACTORIES, ids=lambda f: f.__name__)
class TestAllPresetsUniformly:

    def test_raises_without_llm_callable(self, factory):
        with pytest.raises(ValueError, match="requires an llm_callable"):
            factory(llm_callable=None)

    def test_returns_skilled_agent_instance(self, factory):
        assert isinstance(factory(llm_callable=simple_llm), SkilledAgent)

    def test_ships_with_at_least_one_bundled_skill(self, factory):
        agent = factory(llm_callable=simple_llm)
        assert len(agent.skills) >= 1, f"{factory.__name__} has no bundled skills — packaging or wiring bug."

    def test_has_expected_role(self, factory):
        assert factory(llm_callable=simple_llm).role == EXPECTED_ROLES[factory]

    def test_has_non_empty_goal_and_input_description(self, factory):
        agent = factory(llm_callable=simple_llm)
        assert agent.goal and agent.goal.strip()
        assert agent.input_description and agent.input_description.strip()

    def test_extra_skills_are_merged_with_bundled_skills(self, factory):
        custom = Skill(name="custom-extra-skill", description="Extra.", version="1.0.0", content="Extra content.")
        agent = factory(llm_callable=simple_llm, extra_skills=[custom])
        names = [s.name for s in agent.skills]
        assert "custom-extra-skill" in names
        assert len(agent.skills) >= 2

    def test_llm_callable_is_correctly_assigned(self, factory):
        agent = factory(llm_callable=simple_llm)
        assert agent.llm_callable is simple_llm


# =============================================================================
# 7. End-to-end: a real preset's bundled skill content actually reaches the LLM
# =============================================================================

class TestPresetEndToEndSkillGuidance:

    def test_cfo_agent_execute_includes_all_bundled_skill_content(self):
        probe_agent = cfo_agent(llm_callable=simple_llm)
        assert probe_agent.skills, "cfo_agent must ship with at least one bundled skill."

        captured = []

        def llm(prompt):
            captured.append(prompt)
            return "MOCK_FINAL_REPORT"

        agent = cfo_agent(llm_callable=llm)
        result = agent.execute("Startup dossier: $10k MRR, $50k burn.")

        assert result == "MOCK_FINAL_REPORT"
        assert len(captured) == 1
        prompt = captured[0]
        assert "APPLICABLE SKILL GUIDANCE" in prompt
        for skill in agent.skills:
            assert skill.content in prompt


# =============================================================================
# 8. Packaging guard  (unchanged — already passed)
# =============================================================================

class TestLoadSkillsHelperPackaging:

    def test_load_skills_raises_clearly_when_skill_file_missing(self, tmp_path, monkeypatch):
        def fake_files(package_path):
            return tmp_path

        monkeypatch.setattr("importlib.resources.files", fake_files)

        with pytest.raises(FileNotFoundError):
            presets._load_skills("fake.package.path", "nonexistent_skill_name")
