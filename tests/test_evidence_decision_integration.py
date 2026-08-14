import unittest

from agent_lab.decision import recommend_decision
from agent_lab.domain import (
    GovernanceDecision,
    GovernanceIssue,
    IssueSeverity,
    IssueType,
)
from agent_lab.evidence import (
    EvidenceSource,
    build_evidence_collection,
    build_llm_evidence_collection,
)
from agent_lab.llm_schema import GovernanceAgentOutput


class EvidenceDecisionIntegrationTests(unittest.TestCase):
    def test_blocking_rule_severity_is_preserved_and_recommends_reject(
        self,
    ) -> None:
        issue = GovernanceIssue(
            issue_type=IssueType.MISSING_CRITICAL_FIELD,
            field_name="description_short",
            message="Campo obrigatório ausente: description_short",
            severity=IssueSeverity.BLOCKING,
        )

        collection = build_evidence_collection(
            material_id="MAT-0030",
            issues=[issue],
        )
        result = recommend_decision(collection)

        self.assertEqual(
            collection.evidence[0].severity,
            IssueSeverity.BLOCKING,
        )
        self.assertEqual(result.decision, GovernanceDecision.REJECT)

    def test_warning_rule_severity_is_preserved_and_recommends_review(
        self,
    ) -> None:
        issue = GovernanceIssue(
            issue_type=IssueType.SUSPICIOUS_UNIT,
            field_name="unit",
            message="Material líquido cadastrado em unidade de peça",
            severity=IssueSeverity.WARNING,
        )

        collection = build_evidence_collection(
            material_id="MAT-0030",
            issues=[issue],
        )
        result = recommend_decision(collection)

        self.assertEqual(
            collection.evidence[0].severity,
            IssueSeverity.WARNING,
        )
        self.assertEqual(result.decision, GovernanceDecision.REVIEW)

    def test_llm_reject_is_not_promoted_to_automatic_rejection(self) -> None:
        output = GovernanceAgentOutput(
            material_id="MAT-0030",
            decision=GovernanceDecision.REJECT,
            confidence=0.99,
            issues=(IssueType.MISSING_CRITICAL_FIELD,),
            evidence=("A LLM indicou possível ausência de campo crítico.",),
            summary="Possível ausência de campo crítico; revisão humana necessária.",
        )

        collection = build_llm_evidence_collection(output)
        result = recommend_decision(collection)

        self.assertEqual(collection.evidence[0].source, EvidenceSource.LLM)
        self.assertEqual(
            collection.evidence[0].severity,
            IssueSeverity.WARNING,
        )
        self.assertEqual(result.decision, GovernanceDecision.REVIEW)
        self.assertTrue(result.requires_human_decision)


if __name__ == "__main__":
    unittest.main()
