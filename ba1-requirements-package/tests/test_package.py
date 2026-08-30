"""Tests for the requirements package.

Two kinds of test here, and the distinction matters:

1. **Package tests** assert the documents are internally consistent. These are the real deliverable
   -- they fail if someone edits a document and forgets its dependents.
2. **Validator tests** assert the validator itself detects breakage. A validator that always passes
   is indistinguishable from no validator, so each rule is proven to fail on a mutated document.

The second kind is the reason this file exists. `make validate` passing tells you the package is
consistent *if you trust the validator*. These tests are what earn that trust.
"""

from __future__ import annotations

import re

import pytest

from tools import validate_traceability as vt

# --------------------------------------------------------------------------- #
# 1. The package is consistent
# --------------------------------------------------------------------------- #


@pytest.fixture(scope="module")
def result():
    return vt.validate()


def test_package_has_no_errors(result):
    findings, _ = result
    assert findings.errors == [], "\n".join(findings.errors)


def test_only_the_documented_gap_is_warned(result):
    """GAP-01 is the single accepted warning. A second one means an undocumented gap appeared."""
    findings, _ = result
    assert len(findings.warnings) == 1, findings.warnings
    assert "FR-041" in findings.warnings[0]


def test_all_rules_actually_ran(result):
    """Guards against a rule silently disappearing during a refactor."""
    findings, _ = result
    assert len(findings.checks_passed) == 13, findings.checks_passed


def test_counts_are_as_baselined(result):
    _, counts = result
    assert counts["business requirements"] == (8, 8)
    assert counts["functional requirements"] == (47, 47)
    assert counts["business rules"] == (8, 8)
    assert counts["user stories"] == (19, 19)
    assert counts["UAT cases"] == (53, 53)


def test_story_points_reconcile_with_the_sprint_plan(result):
    """110 story points + 1 unstoried point for FR-041 (GAP-01) = 111 allocated."""
    _, counts = result
    story_points, allocated = counts["story points"]
    assert story_points == 110
    assert allocated == 111
    assert allocated - story_points == 1


def test_committed_work_is_within_capacity():
    release = vt.read("release")
    velocity = vt.parse_velocity(release)
    sprints = vt.parse_sprints(release)
    assert velocity == 38
    assert len(sprints) == 3
    committed = sum(sprint.summed_points for sprint in sprints)
    assert committed == 111
    assert committed <= velocity * len(sprints)


def test_change_requests_are_reflected_in_the_frd():
    """CR-002 promoted FR-044 to Must; CR-003 added FR-045 to FR-047. All four must be Must."""
    priorities = vt.extract_functional_requirements(vt.read("frd"))
    for requirement in ("FR-044", "FR-045", "FR-046", "FR-047"):
        assert priorities[requirement] == "Must", requirement


def test_gap_03_requirements_now_have_acceptance_criteria():
    """The four Must requirements that had a matrix row and a UAT case but no scenario."""
    stories = vt.extract_story_detail(vt.read("stories"))
    declared = {fr for detail in stories.values() for fr in detail.traces_to}
    for requirement in ("FR-006", "FR-010", "FR-012", "FR-020"):
        assert requirement in declared, requirement


def test_every_business_rule_is_versioned():
    """A rule without a version cannot be reconstructed under FR-043."""
    frd = vt.read("frd")
    headings = re.findall(r"^#{2,4}\s+(BRULE-\d{2})[^\n]*?\(v(\d+\.\d+)", frd, re.MULTILINE)
    assert len(headings) == 8
    assert dict(headings)["BRULE-04"] == "1.2", "CR-002 should have taken BRULE-04 to v1.2"


# --------------------------------------------------------------------------- #
# 2. The validator detects breakage
# --------------------------------------------------------------------------- #


@pytest.fixture
def documents(monkeypatch):
    """Let a test mutate a document in memory and re-run validation against it."""
    cache = {name: vt.read(name) for name in vt.DOCS}
    monkeypatch.setattr(vt, "read", lambda name: cache[name])
    return cache


def errors_after(documents, name, old, new) -> list[str]:
    assert old in documents[name], f"fixture text not found in {name}: {old!r}"
    documents[name] = documents[name].replace(old, new, 1)
    findings, _ = vt.validate()
    return findings.errors


def test_detects_a_requirement_dropped_from_the_matrix(documents):
    errors = errors_after(
        documents, "rtm", "| FR-047 | Must | BR-05, BR-06 | US-19 | UAT-52 |", ""
    )
    assert any("FR-047" in e and "absent from the matrix" in e for e in errors)


def test_detects_a_dangling_uat_reference(documents):
    errors = errors_after(documents, "rtm", "| FR-001 | Must | BR-02 | US-01 | UAT-01 |",
                          "| FR-001 | Must | BR-02 | US-01 | UAT-99 |")
    assert any("UAT-99" in e and "no such UAT case" in e for e in errors)


def test_detects_a_priority_mismatch_between_matrix_and_frd(documents):
    errors = errors_after(documents, "rtm", "| FR-045 | Must | BR-05, BR-06 | US-19 | UAT-52 |",
                          "| FR-045 | Should | BR-05, BR-06 | US-19 | UAT-52 |")
    assert any("FR-045" in e and "priority" in e for e in errors)


def test_detects_a_must_requirement_with_no_user_story(documents):
    errors = errors_after(documents, "rtm", "| FR-046 | Must | BR-05, BR-08 | US-19 | UAT-53 |",
                          "| FR-046 | Must | BR-05, BR-08 | — | UAT-53 |")
    assert any("no user story" in e and "FR-046" in e for e in errors)


def test_detects_an_orphaned_requirement(documents):
    errors = errors_after(documents, "rtm", "| FR-042 | Must | BR-08 | US-17 | UAT-43 |",
                          "| FR-042 | Must | — | US-17 | UAT-43 |")
    assert any("orphan" in e and "FR-042" in e for e in errors)


def test_detects_forward_and_full_trace_disagreeing(documents):
    """The insidious one: both halves look right when read in isolation."""
    errors = errors_after(documents, "rtm", "| **BR-07** | Underwriter efficiency | FR-022,",
                          "| **BR-07** | Underwriter efficiency | FR-042, FR-022,")
    assert any("forward/full trace disagree" in e and "FR-042" in e for e in errors)


def test_detects_a_story_whose_traces_disagree_with_the_matrix(documents):
    errors = errors_after(
        documents, "stories",
        "*Traces to: FR-045, FR-046, FR-047 · Points: 5 · Priority: Must (added by CR-003)*",
        "*Traces to: FR-045, FR-046 · Points: 5 · Priority: Must (added by CR-003)*",
    )
    assert any("story/matrix trace disagree" in e and "US-19" in e for e in errors)


def test_detects_a_story_underprioritised_against_its_requirements(documents):
    errors = errors_after(
        documents, "stories",
        "*Traces to: FR-044 · Points: 3 · Priority: Must (raised from Should by CR-002)*",
        "*Traces to: FR-044 · Points: 3 · Priority: Should*",
    )
    assert any("story priority" in e and "US-18" in e for e in errors)


def test_detects_a_stale_moscow_count(documents):
    """The defect this rule was written for: a count nobody re-added."""
    errors = errors_after(documents, "release", "### Must — 43 requirements",
                          "### Must — 34 requirements")
    assert any("Must heading declares 34" in e for e in errors)


def test_detects_a_requirement_in_the_wrong_moscow_group(documents):
    errors = errors_after(documents, "release", "| Automation monitoring *(CR-002)* | FR-044 |", "")
    assert any("Must group does not match the FRD" in e and "FR-044" in e for e in errors)


def test_detects_a_sprint_total_that_no_longer_matches_its_rows(documents):
    """The arithmetic defect that was actually present in this package."""
    errors = errors_after(documents, "release", "### Sprint 2 — Decisioning and offer (42 points)",
                          "### Sprint 2 — Decisioning and offer (39 points)")
    assert any("declares 39 points but its rows sum to 42" in e for e in errors)


def test_detects_a_story_allocated_to_no_sprint(documents):
    errors = errors_after(documents, "release",
                          "| US-12 Prevent unilateral override | FR-035 | 5 |", "")
    assert any("US-12 is not allocated to any sprint" in e for e in errors)


def test_detects_points_disagreeing_between_stories_and_sprint_plan(documents):
    errors = errors_after(documents, "release",
                          "| US-19 Know my right to cancel | FR-045, FR-046, FR-047 | 5 *(CR-003)* |",
                          "| US-19 Know my right to cancel | FR-045, FR-046, FR-047 | 8 *(CR-003)* |")
    assert any("US-19" in e and "5 points, sprint plan says 8" in e for e in errors)


def test_detects_overcommitment_beyond_velocity(documents):
    errors = errors_after(documents, "release", "velocity is **38 points", "velocity is **30 points")
    assert any("exceeds capacity" in e for e in errors)


def test_detects_a_stale_story_summary_total(documents):
    errors = errors_after(documents, "stories", "| **Total** | **19 stories** | **110 points** |",
                          "| **Total** | **19 stories** | **105 points** |")
    assert any("summary total is 105 points" in e for e in errors)


def test_a_missing_document_is_reported_not_crashed(monkeypatch):
    monkeypatch.setitem(vt.DOCS, "rtm", "99-does-not-exist.md")
    with pytest.raises(FileNotFoundError):
        vt.validate()
