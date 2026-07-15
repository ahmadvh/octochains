import pytest
from pathlib import Path
from octochains.skills import Skill


# =============================================================================
# HELPERS
# =============================================================================

def make_skill_md(name=None, description=None, version=None, content="Default body content.", extra_frontmatter_lines=None):
    """Builds a raw SKILL.md-style string for test input construction."""
    lines = ["---"]
    if name is not None:
        lines.append(f"name: {name}")
    if description is not None:
        lines.append(f"description: {description}")
    if version is not None:
        lines.append(f"version: {version}")
    if extra_frontmatter_lines:
        lines.extend(extra_frontmatter_lines)
    lines.append("---")
    lines.append(content)
    return "\n".join(lines)


# =============================================================================
# 1. from_string: SUCCESS PATHS
# =============================================================================

class TestSkillFromStringSuccess:

    def test_full_frontmatter_parses_correctly(self):
        raw = make_skill_md(
            name="gdpr-review",
            description="Reviews GDPR Article 5/17 compliance.",
            version="2.1.0",
            content="## GDPR Review\n1. Check data retention windows."
        )
        skill = Skill.from_string(raw)

        assert skill.name == "gdpr-review"
        assert skill.description == "Reviews GDPR Article 5/17 compliance."
        assert skill.version == "2.1.0"
        assert skill.content == "## GDPR Review\n1. Check data retention windows."

    def test_name_only_uses_defaults_for_description_and_version(self):
        raw = make_skill_md(name="minimal-skill", description=None, version=None, content="Body text.")
        skill = Skill.from_string(raw)

        assert skill.name == "minimal-skill"
        assert skill.description == ""
        assert skill.version == "1.0.0"
        assert skill.content == "Body text."

    def test_multiline_markdown_content_is_preserved_verbatim(self):
        body = "## Heading\n\n1. Step one\n2. Step two\n\n> A blockquote note."
        raw = make_skill_md(name="multi-line", content=body)
        skill = Skill.from_string(raw)

        assert skill.content == body

    def test_returns_skill_instance(self):
        raw = make_skill_md(name="type-check")
        skill = Skill.from_string(raw)
        assert isinstance(skill, Skill)


# =============================================================================
# 2. from_string: VALIDATION / ERROR PATHS
# =============================================================================

class TestSkillFromStringValidation:

    def test_missing_leading_delimiter_raises(self):
        raw = "name: no-leading-dashes\n---\nSome content."
        with pytest.raises(ValueError, match="must begin with a '---' frontmatter boundary"):
            Skill.from_string(raw)

    def test_missing_closing_delimiter_raises(self):
        raw = "---\nname: unterminated\ndescription: no closing delimiter\nSome content."
        with pytest.raises(ValueError, match="Missing closing '---'"):
            Skill.from_string(raw)

    def test_missing_name_field_raises(self):
        raw = make_skill_md(name=None, description="Has description but no name.")
        with pytest.raises(ValueError, match="'name' attribute is mandatory"):
            Skill.from_string(raw)

    def test_empty_frontmatter_raises_missing_name(self):
        raw = "---\n---\nBody with no frontmatter fields at all."
        with pytest.raises(ValueError, match="'name' attribute is mandatory"):
            Skill.from_string(raw)

    def test_completely_empty_string_raises(self):
        with pytest.raises(ValueError, match="must begin with a '---' frontmatter boundary"):
            Skill.from_string("")

    def test_name_present_but_blank_value_raises(self):
        # "name:" with nothing after it should behave like a missing name
        raw = "---\nname:\ndescription: has a blank name value\n---\nBody."
        with pytest.raises(ValueError, match="'name' attribute is mandatory"):
            Skill.from_string(raw)


# =============================================================================
# 3. from_string: EDGE CASES
# =============================================================================

class TestSkillFromStringEdgeCases:

    def test_leading_and_trailing_whitespace_in_raw_text_is_ignored(self):
        raw = "\n\n   " + make_skill_md(name="whitespace-padded", content="Body.") + "   \n\n"
        skill = Skill.from_string(raw)
        assert skill.name == "whitespace-padded"
        assert skill.content == "Body."

    def test_comment_lines_in_frontmatter_are_ignored(self):
        raw = make_skill_md(
            name="commented-skill",
            extra_frontmatter_lines=["# this is a comment, not a field", "# author: someone (should be ignored)"]
        )
        skill = Skill.from_string(raw)
        assert skill.name == "commented-skill"

    def test_blank_lines_in_frontmatter_are_ignored(self):
        raw = "---\nname: blank-line-skill\n\n\ndescription: has gaps\n---\nBody."
        skill = Skill.from_string(raw)
        assert skill.name == "blank-line-skill"
        assert skill.description == "has gaps"

    def test_frontmatter_keys_are_case_insensitive(self):
        raw = "---\nName: Case-Insensitive\nDESCRIPTION: Upper key test\nVersion: 3.0.0\n---\nBody."
        skill = Skill.from_string(raw)
        assert skill.name == "Case-Insensitive"
        assert skill.description == "Upper key test"
        assert skill.version == "3.0.0"

    def test_colon_within_value_is_preserved(self):
        # split(":", 1) must only split on the FIRST colon, preserving the rest.
        raw = "---\nname: colon-value-skill\ndescription: Ratio is 3:1, handle with care\n---\nBody."
        skill = Skill.from_string(raw)
        assert skill.description == "Ratio is 3:1, handle with care"

    def test_duplicate_keys_last_value_wins(self):
        raw = "---\nname: first-name\nname: second-name\n---\nBody."
        skill = Skill.from_string(raw)
        assert skill.name == "second-name"

    def test_windows_style_line_endings_are_handled(self):
        raw = "---\r\nname: crlf-skill\r\ndescription: Uses Windows line endings\r\n---\r\nBody content.\r\n"
        skill = Skill.from_string(raw)
        assert skill.name == "crlf-skill"
        assert skill.description == "Uses Windows line endings"

    def test_content_is_empty_string_when_nothing_follows_frontmatter(self):
        raw = "---\nname: no-content-skill\n---\n"
        skill = Skill.from_string(raw)
        assert skill.content == ""

    def test_content_containing_additional_triple_dash_is_preserved_as_content(self):
        # split("---", 2) caps at 3 segments, so a '---' inside the body
        # (e.g. a markdown horizontal rule) stays part of `content`, not
        # treated as a new delimiter. This locks in that documented behavior.
        raw = "---\nname: hr-in-body\n---\nIntro text.\n\n---\n\nSection after a horizontal rule."
        skill = Skill.from_string(raw)
        assert skill.name == "hr-in-body"
        assert "---" in skill.content
        assert "Section after a horizontal rule." in skill.content

    def test_frontmatter_line_without_colon_is_ignored(self):
        raw = "---\nname: no-colon-line\nthis line has no colon and should be skipped\n---\nBody."
        skill = Skill.from_string(raw)
        assert skill.name == "no-colon-line"

    def test_extra_unrecognized_fields_do_not_raise(self):
        # Fields beyond name/description/version are parsed into `metadata`
        # internally but simply dropped when constructing the Skill.
        raw = "---\nname: extra-fields-skill\nauthor: someone\ntags: risk, finance\n---\nBody."
        skill = Skill.from_string(raw)
        assert skill.name == "extra-fields-skill"
        assert skill.description == ""


# =============================================================================
# 4. from_file
# =============================================================================

class TestSkillFromFile:

    def test_loads_valid_skill_file(self, tmp_path):
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text(
            make_skill_md(name="file-loaded-skill", description="Loaded from disk.", version="1.2.0", content="File body."),
            encoding="utf-8"
        )
        skill = Skill.from_file(skill_file)

        assert skill.name == "file-loaded-skill"
        assert skill.description == "Loaded from disk."
        assert skill.version == "1.2.0"
        assert skill.content == "File body."

    def test_missing_file_raises_file_not_found(self, tmp_path):
        missing_path = tmp_path / "does_not_exist" / "SKILL.md"
        with pytest.raises(FileNotFoundError, match="Skill configuration file not found"):
            Skill.from_file(missing_path)

    def test_malformed_file_content_raises_value_error(self, tmp_path):
        # from_file should propagate from_string's validation, not swallow it
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text("no frontmatter at all here", encoding="utf-8")
        with pytest.raises(ValueError, match="must begin with a '---' frontmatter boundary"):
            Skill.from_file(skill_file)

    def test_reads_utf8_content_correctly(self, tmp_path):
        # Explicit encoding="utf-8" handling for non-ASCII content — common
        # in legal/EU-focused skills (§ symbols, accented characters, etc.)
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text(
            make_skill_md(
                name="unicode-skill",
                description="Handles Article § 5 GDPR — café, naïve, 中文 test.",
                content="Ensure UTF-8 chars like é, ü, § survive round-trip."
            ),
            encoding="utf-8"
        )
        skill = Skill.from_file(skill_file)

        assert "§" in skill.description
        assert "中文" in skill.description
        assert "é" in skill.content

    def test_accepts_path_object_not_just_string(self, tmp_path):
        # Signature is typed as Path — confirm passing a Path works, since
        # presets.py and the README examples both construct Path objects.
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text(make_skill_md(name="path-object-skill"), encoding="utf-8")

        assert isinstance(skill_file, Path)
        skill = Skill.from_file(skill_file)
        assert skill.name == "path-object-skill"


# =============================================================================
# 5. Dataclass-level behavior
# =============================================================================

class TestSkillDataclassBehavior:

    def test_direct_construction_without_parsing(self):
        # Skill should remain usable as a plain dataclass, independent of
        # from_string/from_file — e.g. for constructing skills programmatically.
        skill = Skill(name="direct", description="Built without parsing.", version="0.0.1", content="Raw content.")
        assert skill.name == "direct"
        assert skill.description == "Built without parsing."
        assert skill.version == "0.0.1"
        assert skill.content == "Raw content."

    def test_equality_compares_by_value(self):
        a = Skill(name="same", description="d", version="1.0.0", content="c")
        b = Skill(name="same", description="d", version="1.0.0", content="c")
        c = Skill(name="different", description="d", version="1.0.0", content="c")

        assert a == b
        assert a != c

    def test_parsed_skill_equals_directly_constructed_equivalent(self):
        raw = make_skill_md(name="parity-check", description="desc", version="9.9.9", content="body text")
        parsed = Skill.from_string(raw)
        direct = Skill(name="parity-check", description="desc", version="9.9.9", content="body text")

        assert parsed == direct