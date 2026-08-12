"""Orquestração determinística das regras de governança."""

from .domain import (
    GovernanceAssessment,
    GovernanceDecision,
    GovernanceIssue,
    IssueSeverity,
    IssueType,
    MaterialRecord,
)
from .duplicates import find_duplicate_candidates
from .evidence import build_evidence_collection
from .metrics import completeness_score
from .normalization import normalize_text
from .rules import run_rules


class DeterministicGovernanceValidator:
    """Baseline auditável que não utiliza modelos probabilísticos."""

    def analyze(
        self,
        record: MaterialRecord,
        existing_records: list[MaterialRecord] | None = None,
    ) -> GovernanceAssessment:
        existing_records = existing_records or []
        issues = run_rules(record)
        duplicates = find_duplicate_candidates(record, existing_records)

        if duplicates:
            issues.append(
                GovernanceIssue(
                    issue_type=IssueType.POSSIBLE_DUPLICATE,
                    field_name="description_short",
                    message="Material semelhante a registro existente",
                )
            )

        decision = self._decision(issues)
        evidence_collection = build_evidence_collection(
            material_id=record.material_id,
            issues=issues,
        )

        return GovernanceAssessment(
            material_id=record.material_id,
            completeness=completeness_score(record),
            confidence=self._confidence(decision, issues),
            decision=decision,
            normalized_description=normalize_text(record.description_short),
            suggested_group=normalize_text(record.material_group),
            issues=tuple(issues),
            duplicate_candidates=duplicates,
            evidence=tuple(issue.message for issue in issues),
            evidence_collection=evidence_collection,
        )

    def analyze_all(
        self,
        records: list[MaterialRecord],
    ) -> list[GovernanceAssessment]:
        assessments: list[GovernanceAssessment] = []
        existing_records: list[MaterialRecord] = []
        for record in records:
            assessments.append(self.analyze(record, existing_records))
            existing_records.append(record)
        return assessments

    @staticmethod
    def _decision(issues: list[GovernanceIssue]) -> GovernanceDecision:
        if any(issue.severity == IssueSeverity.BLOCKING for issue in issues):
            return GovernanceDecision.REJECT
        if issues:
            return GovernanceDecision.REVIEW
        return GovernanceDecision.APPROVE

    @staticmethod
    def _confidence(
        decision: GovernanceDecision,
        issues: list[GovernanceIssue],
    ) -> float:
        if decision == GovernanceDecision.APPROVE:
            return 0.95
        if decision == GovernanceDecision.REJECT:
            return 0.98
        return max(0.55, 0.85 - (0.08 * len(issues)))
