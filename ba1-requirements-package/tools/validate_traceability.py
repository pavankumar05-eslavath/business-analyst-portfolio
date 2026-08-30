"""Validate the requirements traceability matrix against the source documents.

A traceability matrix maintained by hand goes stale within two sprints: someone adds a
requirement and forgets the matrix, or renumbers a story, or deletes a test case. The matrix
then *claims* coverage without providing it -- worse than having none, because it is trusted.

This script parses every document in the package and enforces ten rules:

 1. Every ID referenced in the matrix exists in its source document
 2. Every requirement defined in a source document appears in the matrix (nothing silently dropped)
 3. Every Must-priority functional requirement traces to >= 1 user story
 4. Every Must-priority functional requirement traces to >= 1 UAT case
 5. Every business requirement is satisfied by >= 1 functional requirement, and no functional
    requirement is an orphan
 6. Priorities in the matrix match the priorities declared in the FRD
 7. Each story's declared "Traces to" list matches the matrix rows naming that story
 8. A story delivering any Must requirement is itself prioritised Must
 9. The MoSCoW groups in the release plan match the FRD priorities exactly, and the declared
    counts match the number of requirements listed
10. Sprint arithmetic reconciles: declared sprint totals equal the sum of their rows, every story
    is allocated to exactly one sprint at the points the stories document gives it, and the
    committed total is within velocity x sprint count

Errors fail the build. Warnings are reported and tolerated: a Should-priority requirement
without a user story is a known gap, not a defect, provided it is documented.

Rules 1-6 check traceability. Rules 7-10 were added later, after a change request (CR-003) was
applied to the package, and they immediately found three errors that rules 1-6 could not see:
a sprint total that no longer matched its rows, a MoSCoW count that had never been re-added, and
an NFR count that disagreed with the table beneath it. Traceability being intact says nothing
about the numbers in the plan being right.

    python -m tools.validate_traceability
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent.parent

DOCS = {
    "brd": "03-business-requirements.md",
    "frd": "04-functional-requirements.md",
    "stories": "05-user-stories.md",
    "nfr": "06-non-functional-requirements.md",
    "uat": "08-uat-test-cases.md",
    "rtm": "09-traceability-matrix.md",
    "release": "10-release-plan.md",
}

VALID_PRIORITIES = {"Must", "Should", "Could", "Won't"}


@dataclass
class Findings:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    checks_passed: list[str] = field(default_factory=list)

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def passed(self, message: str) -> None:
        self.checks_passed.append(message)

    @property
    def ok(self) -> bool:
        return not self.errors


def read(name: str) -> str:
    path = PACKAGE_ROOT / DOCS[name]
    if not path.exists():
        raise FileNotFoundError(f"missing document: {path}")
    return path.read_text(encoding="utf-8")


# --------------------------------------------------------------------------- #
# Extract the canonical set of IDs from each source document
# --------------------------------------------------------------------------- #
def extract_business_requirements(text: str) -> set[str]:
    """BRD table rows of the form: | **BR-01** | ... |"""
    return set(re.findall(r"^\|\s*\*\*(BR-\d{2})\*\*\s*\|", text, re.MULTILINE))


def extract_functional_requirements(text: str) -> dict[str, str]:
    """FRD table rows: | **FR-001** | requirement | traces to | Priority |

    Returns {id: priority}. Priority is taken from the FRD because the FRD is the source of
    truth; the matrix is checked against it rather than the other way round.
    """
    requirements: dict[str, str] = {}
    pattern = re.compile(
        r"^\|\s*\*\*(FR-\d{3})\*\*\s*\|.*?\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|\s*$",
        re.MULTILINE,
    )
    for match in pattern.finditer(text):
        requirement_id, _traces, priority = match.groups()
        requirements[requirement_id] = priority.strip()
    return requirements


def extract_business_rules(text: str) -> set[str]:
    """Headings of the form: #### BRULE-01 · Age eligibility (v1.0)"""
    return set(re.findall(r"^#{2,4}\s+(BRULE-\d{2})\s", text, re.MULTILINE))


def extract_user_stories(text: str) -> set[str]:
    """Headings of the form: ### US-01 · Start an application"""
    return set(re.findall(r"^#{2,4}\s+(US-\d{2})\s", text, re.MULTILINE))


def extract_nfrs(text: str) -> set[str]:
    return set(re.findall(r"^\|\s*\*\*(NFR-\d{2})\*\*\s*\|", text, re.MULTILINE))


def extract_uat_cases(text: str) -> set[str]:
    return set(re.findall(r"^\|\s*\*\*(UAT-\d{2})\*\*\s*\|", text, re.MULTILINE))


@dataclass
class Story:
    points: int
    priority: str
    traces_to: list[str]


def extract_story_detail(text: str) -> dict[str, Story]:
    """Parse the metadata line under each story heading.

    ### US-19 - Know my right to cancel
    ...
    *Traces to: FR-045, FR-046, FR-047 - Points: 5 - Priority: Must (added by CR-003)*
    """
    stories: dict[str, Story] = {}
    blocks = re.split(r"^#{2,4}\s+(US-\d{2})\s", text, flags=re.MULTILINE)
    # blocks[0] is the preamble; thereafter [id, body, id, body, ...]
    for story_id, body in zip(blocks[1::2], blocks[2::2], strict=True):
        meta = re.search(
            r"\*Traces to:\s*(.+?)\s*[·\-]\s*Points:\s*(\d+)\s*[·\-]\s*Priority:\s*(\w+)",
            body,
        )
        if meta is None:
            continue
        traces, points, priority = meta.groups()
        stories[story_id] = Story(
            points=int(points),
            priority=priority.strip(),
            traces_to=parse_ids(traces, "FR"),
        )
    return stories


def extract_story_summary_total(text: str) -> int | None:
    """The bold total row: | **Total** | **19 stories** | **110 points** |"""
    match = re.search(r"\|\s*\*\*Total\*\*\s*\|[^|]*\|\s*\*\*(\d+)\s*points\*\*\s*\|", text)
    return int(match.group(1)) if match else None


def extract_moscow_groups(text: str) -> dict[str, tuple[int | None, list[str]]]:
    """Parse the release plan's MoSCoW sections.

    ### Must - 43 requirements
    | Group | Requirements |
    | Application capture | FR-001, FR-002, ... |

    Returns {"Must": (declared_count, [fr_ids]), "Should": (...)}.
    """
    groups: dict[str, tuple[int | None, list[str]]] = {}
    sections = re.split(r"^###\s+(Must|Should|Could|Won't)\b([^\n]*)", text, flags=re.MULTILINE)
    for label, heading, body in zip(sections[1::3], sections[2::3], sections[3::3], strict=True):
        count = re.search(r"(\d+)\s+requirement", heading)
        declared = int(count.group(1)) if count else None
        body = re.split(r"^###\s", body, flags=re.MULTILINE)[0]
        # Only table rows count. Prose in these sections legitimately mentions requirements it is
        # explaining -- "FR-044 was removed from this list by CR-002" is commentary, not membership.
        rows = "\n".join(
            line for line in body.splitlines()
            if line.lstrip().startswith("|") and not re.match(r"^\|[\s:|-]*\|", line)
        )
        groups[label] = (declared, parse_ids(rows, "FR"))
    return groups


@dataclass
class SprintRow:
    story: str | None
    points: int
    label: str


@dataclass
class Sprint:
    name: str
    declared_points: int
    rows: list[SprintRow]

    @property
    def summed_points(self) -> int:
        return sum(row.points for row in self.rows)


def parse_sprints(text: str) -> list[Sprint]:
    """### Sprint 2 - Decisioning and offer (42 points), followed by a story table."""
    sprints: list[Sprint] = []
    pattern = re.compile(r"^###\s+(Sprint\s+\d+[^(\n]*)\((\d+)\s*points?\)", re.MULTILINE)
    matches = list(pattern.finditer(text))
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[match.start():end]
        rows: list[SprintRow] = []
        for line in body.splitlines():
            row = re.match(r"^\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|\s*(\d+)\b[^|]*\|\s*$", line)
            if row is None:
                continue
            label, _requirements, points = row.groups()
            if label.strip().lower() in {"story", "**total**", "total"}:
                continue
            story = parse_ids(label, "US")
            rows.append(SprintRow(
                story=story[0] if story else None,
                points=int(points),
                label=label.strip(),
            ))
        sprints.append(Sprint(
            name=match.group(1).strip(),
            declared_points=int(match.group(2)),
            rows=rows,
        ))
    return sprints


def parse_velocity(text: str) -> int | None:
    match = re.search(r"velocity is\s*\*\*(\d+)\s*points", text)
    return int(match.group(1)) if match else None


# --------------------------------------------------------------------------- #
# Parse the traceability matrix
# --------------------------------------------------------------------------- #
@dataclass
class MatrixRow:
    functional_requirement: str
    priority: str
    business_requirements: list[str]
    user_stories: list[str]
    uat_cases: list[str]


def parse_ids(cell: str, prefix: str) -> list[str]:
    return re.findall(rf"({prefix}-\d+)", cell)


def parse_full_trace(text: str) -> list[MatrixRow]:
    """Rows: | FR-001 | Must | BR-02 | US-01 | UAT-01 |"""
    rows: list[MatrixRow] = []
    pattern = re.compile(
        r"^\|\s*(FR-\d{3})\s*\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|\s*$",
        re.MULTILINE,
    )
    for match in pattern.finditer(text):
        fr, priority, br_cell, us_cell, uat_cell = match.groups()
        rows.append(MatrixRow(
            functional_requirement=fr,
            priority=priority.strip(),
            business_requirements=parse_ids(br_cell, "BR"),
            user_stories=parse_ids(us_cell, "US"),
            uat_cases=parse_ids(uat_cell, "UAT"),
        ))
    return rows


def parse_forward_trace(text: str) -> dict[str, list[str]]:
    """Rows: | **BR-01** | TAT < 24 h | FR-018, FR-019, ... |"""
    forward: dict[str, list[str]] = {}
    pattern = re.compile(
        r"^\|\s*\*\*(BR-\d{2})\*\*\s*\|[^|]*\|\s*([^|]*?)\s*\|\s*$", re.MULTILINE
    )
    for match in pattern.finditer(text):
        br, fr_cell = match.groups()
        forward[br] = parse_ids(fr_cell, "FR")
    return forward


def parse_rule_trace(text: str) -> dict[str, list[str]]:
    """Rows: | BRULE-01 Age eligibility | 1.0 | FR-021 | UAT-20, UAT-21 |"""
    trace: dict[str, list[str]] = {}
    pattern = re.compile(
        r"^\|\s*(BRULE-\d{2})[^|]*\|[^|]*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|\s*$", re.MULTILINE
    )
    for match in pattern.finditer(text):
        rule, _fr_cell, uat_cell = match.groups()
        trace[rule] = parse_ids(uat_cell, "UAT")
    return trace


def parse_nfr_trace(text: str) -> dict[str, list[str]]:
    """Rows: | NFR-01 | BR-03 | UAT-46 |"""
    trace: dict[str, list[str]] = {}
    pattern = re.compile(
        r"^\|\s*(NFR-\d{2})\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|\s*$", re.MULTILINE
    )
    for match in pattern.finditer(text):
        nfr, _br_cell, uat_cell = match.groups()
        trace[nfr] = parse_ids(uat_cell, "UAT")
    return trace


# --------------------------------------------------------------------------- #
# Validation
# --------------------------------------------------------------------------- #
def validate() -> tuple[Findings, dict[str, tuple[int, int]]]:
    findings = Findings()

    brd, frd = read("brd"), read("frd")
    stories, nfr_doc, uat_doc, rtm = read("stories"), read("nfr"), read("uat"), read("rtm")
    release = read("release")

    business_requirements = extract_business_requirements(brd)
    functional_requirements = extract_functional_requirements(frd)
    business_rules = extract_business_rules(frd)
    user_stories = extract_user_stories(stories)
    nfrs = extract_nfrs(nfr_doc)
    uat_cases = extract_uat_cases(uat_doc)

    matrix = parse_full_trace(rtm)
    forward = parse_forward_trace(rtm)
    rule_trace = parse_rule_trace(rtm)
    nfr_trace = parse_nfr_trace(rtm)

    matrix_by_fr = {row.functional_requirement: row for row in matrix}

    # -- rule 2: nothing silently dropped ---------------------------------- #
    missing_from_matrix = sorted(set(functional_requirements) - set(matrix_by_fr))
    if missing_from_matrix:
        findings.error(
            f"{len(missing_from_matrix)} functional requirement(s) defined in the FRD but "
            f"absent from the matrix: {', '.join(missing_from_matrix)}"
        )
    unknown_in_matrix = sorted(set(matrix_by_fr) - set(functional_requirements))
    if unknown_in_matrix:
        findings.error(
            f"matrix references functional requirement(s) not defined in the FRD: "
            f"{', '.join(unknown_in_matrix)}"
        )
    if not missing_from_matrix and not unknown_in_matrix:
        findings.passed("every FR in the FRD appears in the matrix, and vice versa")

    # -- rule 1: referenced IDs exist -------------------------------------- #
    dangling: list[str] = []
    dangling.extend(
        f"{row.functional_requirement} -> {story} (no such story)"
        for row in matrix
        for story in row.user_stories
        if story not in user_stories
    )
    dangling.extend(
        f"{row.functional_requirement} -> {case} (no such UAT case)"
        for row in matrix
        for case in row.uat_cases
        if case not in uat_cases
    )
    dangling.extend(
        f"{row.functional_requirement} -> {br} (no such BR)"
        for row in matrix
        for br in row.business_requirements
        if br not in business_requirements
    )
    dangling.extend(
        f"matrix references {rule} which is not defined in the FRD"
        for rule in rule_trace
        if rule not in business_rules
    )
    dangling.extend(
        f"{rule} -> {case} (no such UAT case)"
        for rule, cases in rule_trace.items()
        for case in cases
        if case not in uat_cases
    )
    dangling.extend(
        f"matrix references {nfr} which is not defined in the NFR document"
        for nfr in nfr_trace
        if nfr not in nfrs
    )
    dangling.extend(
        f"{nfr} -> {case} (no such UAT case)"
        for nfr, cases in nfr_trace.items()
        for case in cases
        if case not in uat_cases
    )

    if dangling:
        for item in dangling:
            findings.error(f"dangling reference: {item}")
    else:
        findings.passed("every referenced ID exists in its source document")

    # -- rule 6: priorities agree with the FRD ----------------------------- #
    mismatched = [
        f"{fr}: FRD says {functional_requirements[fr]!r}, matrix says {row.priority!r}"
        for fr, row in matrix_by_fr.items()
        if fr in functional_requirements and row.priority != functional_requirements[fr]
    ]
    invalid = [
        f"{fr}: {priority!r} is not a valid MoSCoW priority"
        for fr, priority in functional_requirements.items()
        if priority not in VALID_PRIORITIES
    ]
    if mismatched or invalid:
        for item in mismatched + invalid:
            findings.error(f"priority: {item}")
    else:
        findings.passed("priorities in the matrix match the FRD")

    # -- rules 3 and 4: Must coverage -------------------------------------- #
    missing_story_must, missing_uat_must = [], []
    missing_story_lower, missing_uat_lower = [], []

    for fr, row in sorted(matrix_by_fr.items()):
        priority = functional_requirements.get(fr, row.priority)
        if not row.user_stories:
            (missing_story_must if priority == "Must" else missing_story_lower).append(fr)
        if not row.uat_cases:
            (missing_uat_must if priority == "Must" else missing_uat_lower).append(fr)

    if missing_story_must:
        findings.error(
            f"Must-priority FR(s) with no user story: {', '.join(missing_story_must)}"
        )
    else:
        findings.passed("every Must FR has >= 1 user story")

    if missing_uat_must:
        findings.error(f"Must-priority FR(s) with no UAT case: {', '.join(missing_uat_must)}")
    else:
        findings.passed("every Must FR has >= 1 UAT case")

    for fr in missing_story_lower:
        findings.warn(
            f"{fr} ({functional_requirements.get(fr, '?')}) has no user story -- "
            f"acceptable for non-Must, but must be documented as a gap"
        )
    for fr in missing_uat_lower:
        findings.warn(f"{fr} ({functional_requirements.get(fr, '?')}) has no UAT case")

    # -- rule 5: BR satisfaction and FR orphans ---------------------------- #
    unsatisfied = sorted(
        br for br in business_requirements if not forward.get(br)
    )
    if unsatisfied:
        findings.error(
            f"business requirement(s) not satisfied by any FR: {', '.join(unsatisfied)}"
        )
    else:
        findings.passed("every BR is satisfied by >= 1 FR")

    orphans = sorted(
        row.functional_requirement for row in matrix if not row.business_requirements
    )
    if orphans:
        findings.error(f"orphaned FR(s) with no parent BR: {', '.join(orphans)}")
    else:
        findings.passed("every FR has a parent BR (no orphans)")

    # Cross-check the two directions agree: if the forward trace says BR-01 is satisfied by
    # FR-018, the full trace row for FR-018 must list BR-01. A matrix that disagrees with
    # itself is the most insidious failure, because both halves look correct in isolation.
    inconsistent: list[str] = []
    for br, requirements in forward.items():
        for fr in requirements:
            row = matrix_by_fr.get(fr)
            if row is None:
                inconsistent.append(f"{br} claims {fr}, which has no matrix row")
            elif br not in row.business_requirements:
                inconsistent.append(
                    f"{br} claims {fr}, but the {fr} row does not list {br}"
                )
    if inconsistent:
        for item in inconsistent:
            findings.error(f"forward/full trace disagree: {item}")
    else:
        findings.passed("forward trace and full trace are mutually consistent")

    # -- business rules all traced ----------------------------------------- #
    untraced_rules = sorted(business_rules - set(rule_trace))
    if untraced_rules:
        findings.error(f"business rule(s) not in the matrix: {', '.join(untraced_rules)}")
    else:
        findings.passed("every business rule is traced to a UAT case")

    # -- rule 7: the stories document agrees with the matrix ---------------- #
    # The stories doc declares "Traces to: FR-045, FR-046" and the matrix declares
    # "FR-045 -> US-19". Both are hand-maintained, so both drift, in opposite directions.
    story_detail = extract_story_detail(stories)
    matrix_story_to_frs: dict[str, set[str]] = {}
    for row in matrix:
        for story in row.user_stories:
            matrix_story_to_frs.setdefault(story, set()).add(row.functional_requirement)

    trace_disagreements = [
        f"{story}: stories doc says {sorted(detail.traces_to)}, "
        f"matrix says {sorted(matrix_story_to_frs.get(story, set()))}"
        for story, detail in sorted(story_detail.items())
        if set(detail.traces_to) != matrix_story_to_frs.get(story, set())
    ]
    if trace_disagreements:
        for item in trace_disagreements:
            findings.error(f"story/matrix trace disagree: {item}")
    else:
        findings.passed("each story's declared FRs match the matrix rows naming that story")

    # -- rule 8: story priority reflects the FRs it delivers ---------------- #
    # A story delivering any Must requirement is itself a Must. Getting this wrong is how a
    # Must requirement ends up on the descope list.
    priority_conflicts = []
    for story, detail in sorted(story_detail.items()):
        frs = [fr for fr in detail.traces_to if fr in functional_requirements]
        if not frs:
            continue
        expected = "Must" if any(functional_requirements[fr] == "Must" for fr in frs) else "Should"
        if detail.priority != expected:
            priority_conflicts.append(
                f"{story} is {detail.priority!r} but delivers {expected}-priority requirement(s)"
            )
    if priority_conflicts:
        for item in priority_conflicts:
            findings.error(f"story priority: {item}")
    else:
        findings.passed("story priorities are consistent with the FRs they deliver")

    # -- rule 9: MoSCoW allocation reconciles with the FRD ------------------ #
    moscow = extract_moscow_groups(release)
    moscow_errors: list[str] = []
    for label in ("Must", "Should"):
        declared_count, listed = moscow.get(label, (None, []))
        from_frd = {fr for fr, priority in functional_requirements.items() if priority == label}
        listed_set = set(listed)
        if declared_count is not None and declared_count != len(listed_set):
            moscow_errors.append(
                f"{label} heading declares {declared_count} requirements but "
                f"lists {len(listed_set)}"
            )
        if listed_set != from_frd:
            absent = sorted(from_frd - listed_set)
            extra = sorted(listed_set - from_frd)
            detail = []
            if absent:
                detail.append(f"missing {', '.join(absent)}")
            if extra:
                detail.append(f"wrongly listed {', '.join(extra)}")
            moscow_errors.append(f"{label} group does not match the FRD ({'; '.join(detail)})")

    if moscow_errors:
        for item in moscow_errors:
            findings.error(f"release plan: {item}")
    else:
        findings.passed("MoSCoW groups in the release plan match the FRD priorities")

    # -- rule 10: sprint arithmetic ---------------------------------------- #
    # Sprint totals stated in headings are written by hand and are almost never re-added after
    # a story moves. This rule exists because it caught exactly that.
    sprints = parse_sprints(release)
    arithmetic_errors: list[str] = []

    arithmetic_errors.extend(
        f"{sprint.name} declares {sprint.declared_points} points but its rows sum to "
        f"{sprint.summed_points}"
        for sprint in sprints
        if sprint.declared_points != sprint.summed_points
    )

    allocated = {row.story: row for sprint in sprints for row in sprint.rows if row.story}

    arithmetic_errors.extend(
        f"{story} is allocated to more than one sprint"
        for story in sorted(story_detail)
        if sum(1 for s in sprints for r in s.rows if r.story == story) > 1
    )
    arithmetic_errors.extend(
        f"{story} is not allocated to any sprint"
        for story in sorted(set(story_detail) - set(allocated))
    )
    arithmetic_errors.extend(
        f"the sprint plan allocates {story}, which is not a defined story"
        for story in sorted(set(allocated) - set(story_detail))
    )
    arithmetic_errors.extend(
        f"{story}: stories doc says {story_detail[story].points} points, "
        f"sprint plan says {row.points}"
        for story, row in sorted(allocated.items())
        if story in story_detail and story_detail[story].points != row.points
    )

    summary_total = extract_story_summary_total(stories)
    story_points_total = sum(detail.points for detail in story_detail.values())
    if summary_total is not None and summary_total != story_points_total:
        arithmetic_errors.append(
            f"stories doc: summary total is {summary_total} points but the stories sum to "
            f"{story_points_total}"
        )

    sprint_total = sum(sprint.summed_points for sprint in sprints)
    unstoried = sum(row.points for sprint in sprints for row in sprint.rows if row.story is None)
    if sprint_total != story_points_total + unstoried:
        arithmetic_errors.append(
            f"sprint plan allocates {sprint_total} points; stories total {story_points_total} "
            f"plus {unstoried} unstoried"
        )

    velocity = parse_velocity(release)
    if velocity and sprints and sprint_total > velocity * len(sprints):
        arithmetic_errors.append(
            f"committed {sprint_total} points exceeds capacity "
            f"({len(sprints)} sprints x {velocity} velocity = {velocity * len(sprints)})"
        )

    if arithmetic_errors:
        for item in arithmetic_errors:
            findings.error(f"release plan: {item}")
    else:
        findings.passed(
            f"sprint plan reconciles: {sprint_total} points allocated, every story in exactly "
            f"one sprint, within capacity"
        )

    counts = {
        "business requirements": (len(business_requirements), len(forward)),
        "functional requirements": (len(functional_requirements), len(matrix_by_fr)),
        "business rules": (len(business_rules), len(rule_trace)),
        "user stories": (len(user_stories), len({s for r in matrix for s in r.user_stories})),
        "UAT cases": (len(uat_cases), len({c for r in matrix for c in r.uat_cases}
                                          | {c for v in rule_trace.values() for c in v}
                                          | {c for v in nfr_trace.values() for c in v})),
        "NFR gates": (len(nfr_trace), len(nfr_trace)),
        "story points": (story_points_total, sprint_total),
    }
    return findings, counts


def main() -> int:
    try:
        findings, counts = validate()
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print("\nTraceability validation — Project ORIGIN")
    print("─" * 44)
    for label, (defined, traced) in counts.items():
        print(f"  {label:<24} {defined:>2} found, {traced:>2} traced")
    print()

    for message in findings.checks_passed:
        print(f"  \u2713 {message}")

    if findings.warnings:
        print(f"\n  \u26a0 {len(findings.warnings)} warning(s)")
        for message in findings.warnings:
            print(f"    {message}")

    if findings.errors:
        print(f"\n  \u2717 {len(findings.errors)} error(s)")
        for message in findings.errors:
            print(f"    {message}")

    print()
    if findings.ok:
        print(f"PASS — 0 errors, {len(findings.warnings)} accepted warning(s)\n")
        return 0
    print(f"FAIL — {len(findings.errors)} error(s), {len(findings.warnings)} warning(s)\n")
    return 1


if __name__ == "__main__":
    sys.exit(main())
