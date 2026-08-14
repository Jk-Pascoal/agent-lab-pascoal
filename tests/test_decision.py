import unittest
from dataclasses import FrozenInstanceError

from agent_lab.decision import DecisionRecommendation, recommend_decision
from agent_lab.domain import GovernanceDecision, IssueSeverity, IssueType
from agent_lab.evidence import (
    EvidenceCollection,
    EvidenceSource,
    GovernanceEvidence,
)


class EvidenceToDecisionPipelineTests(unittest.TestCase):
    def _evidence(
        self,
        *,
        severity: IssueSeverity,
        issue_type: IssueType,
        observation: str,
        source: EvidenceSource = EvidenceSource.RULE,
    ) -> GovernanceEvidence:
        return GovernanceEvidence(
            material_id="MAT-0030",
            source=source,
            issue_type=issue_type,
            severity=severity,
            observation=observation,
        )

    def _collection(
        self,
        *evidence: GovernanceEvidence,
    ) -> EvidenceCollection:
        return EvidenceCollection(
            material_id="MAT-0030",
            evidence=tuple(evidence),
        )

    def test_empty_evidence_collection_recommends_approve(self) -> None:
        result = recommend_decision(self._collection())

        self.assertEqual(result.decision, GovernanceDecision.APPROVE)
        self.assertTrue(result.rationale)

    def test_warning_evidence_recommends_review(self) -> None:
        warning = self._evidence(
            severity=IssueSeverity.WARNING,
            issue_type=IssueType.SUSPICIOUS_UNIT,
            observation="Material líquido cadastrado em unidade de peça",
        )

        result = recommend_decision(self._collection(warning))

        self.assertEqual(result.decision, GovernanceDecision.REVIEW)
        self.assertTrue(result.rationale)

    def test_blocking_evidence_recommends_reject(self) -> None:
        blocking = self._evidence(
            severity=IssueSeverity.BLOCKING,
            issue_type=IssueType.MISSING_CRITICAL_FIELD,
            observation="Campo obrigatório ausente: description_short",
        )

        result = recommend_decision(self._collection(blocking))

        self.assertEqual(result.decision, GovernanceDecision.REJECT)
        self.assertTrue(result.rationale)

    def test_reject_precedes_review(self) -> None:
        warning = self._evidence(
            severity=IssueSeverity.WARNING,
            issue_type=IssueType.POSSIBLE_DUPLICATE,
            observation="Possível material duplicado identificado",
            source=EvidenceSource.DUPLICATE,
        )
        blocking = self._evidence(
            severity=IssueSeverity.BLOCKING,
            issue_type=IssueType.INVALID_STATUS,
            observation="Status não reconhecido",
        )

        result = recommend_decision(self._collection(warning, blocking))

        self.assertEqual(result.decision, GovernanceDecision.REJECT)

    def test_evidence_order_does_not_change_decision_or_rationale(self) -> None:
        warning = self._evidence(
            severity=IssueSeverity.WARNING,
            issue_type=IssueType.MISSING_TECHNICAL_ATTRIBUTE,
            observation="Atributo técnico ausente",
        )
        blocking = self._evidence(
            severity=IssueSeverity.BLOCKING,
            issue_type=IssueType.INVALID_UNIT,
            observation="Unidade não reconhecida",
        )

        first = recommend_decision(self._collection(warning, blocking))
        second = recommend_decision(self._collection(blocking, warning))

        self.assertEqual(first.decision, second.decision)
        self.assertEqual(first.rationale, second.rationale)

    def test_result_preserves_material_id_and_evidence(self) -> None:
        warning = self._evidence(
            severity=IssueSeverity.WARNING,
            issue_type=IssueType.AMBIGUOUS_DESCRIPTION,
            observation="Descrição ambígua",
        )
        collection = self._collection(warning)

        result = recommend_decision(collection)

        self.assertEqual(result.material_id, collection.material_id)
        self.assertEqual(result.evidence, collection.evidence)

    def test_result_requires_human_decision(self) -> None:
        result = recommend_decision(self._collection())

        self.assertTrue(result.requires_human_decision)

    def test_decision_recommendation_is_immutable(self) -> None:
        result = recommend_decision(self._collection())

        self.assertIsInstance(result, DecisionRecommendation)
        with self.assertRaises(FrozenInstanceError):
            result.decision = GovernanceDecision.REJECT


if __name__ == "__main__":
    unittest.main()
