"""TDD RED da Issue #27: integração da saída LLM ao Evidence Engine."""

import unittest

from agent_lab.domain import GovernanceDecision, IssueType
from agent_lab.evidence import EvidenceSource
from agent_lab.llm_schema import GovernanceAgentOutput

# Import intencional da capacidade especificada na SPEC 0027.
# No estágio RED, este símbolo ainda não existe em main.
from agent_lab.evidence import build_llm_evidence_collection


class LLMEvidenceIntegrationTests(unittest.TestCase):
    """Especifica a ponte GovernanceAgentOutput -> EvidenceCollection."""

    def _output(
        self,
        *,
        material_id: str = "MAT-0027",
        issues: tuple[IssueType, ...] = (IssueType.SUSPICIOUS_UNIT,),
        evidence: tuple[str, ...] = ("Unidade LT diverge do padrão L.",),
        decision: GovernanceDecision = GovernanceDecision.REVIEW,
        confidence: float = 0.91,
    ) -> GovernanceAgentOutput:
        return GovernanceAgentOutput(
            material_id=material_id,
            decision=decision,
            confidence=confidence,
            issues=issues,
            summary="Análise sintética para teste da integração.",
            evidence=evidence,
        )

    def test_single_llm_issue_becomes_structured_evidence(self) -> None:
        output = self._output()

        collection = build_llm_evidence_collection(output)

        self.assertEqual(collection.material_id, "MAT-0027")
        self.assertEqual(len(collection.evidence), 1)

        item = collection.evidence[0]
        self.assertEqual(item.material_id, "MAT-0027")
        self.assertIs(item.source, EvidenceSource.LLM)
        self.assertIs(item.issue_type, IssueType.SUSPICIOUS_UNIT)
        self.assertEqual(item.observation, "Unidade LT diverge do padrão L.")

    def test_multiple_llm_issues_preserve_order(self) -> None:
        output = self._output(
            issues=(
                IssueType.SUSPICIOUS_UNIT,
                IssueType.AMBIGUOUS_DESCRIPTION,
            ),
            evidence=(
                "Unidade LT diverge do padrão L.",
                "Descrição não identifica inequivocamente o material.",
            ),
        )

        collection = build_llm_evidence_collection(output)

        self.assertEqual(
            tuple(item.issue_type for item in collection.evidence),
            (
                IssueType.SUSPICIOUS_UNIT,
                IssueType.AMBIGUOUS_DESCRIPTION,
            ),
        )
        self.assertEqual(
            tuple(item.observation for item in collection.evidence),
            (
                "Unidade LT diverge do padrão L.",
                "Descrição não identifica inequivocamente o material.",
            ),
        )
        self.assertTrue(
            all(item.source is EvidenceSource.LLM for item in collection.evidence)
        )

    def test_no_llm_issues_produces_empty_collection(self) -> None:
        output = self._output(issues=(), evidence=())

        collection = build_llm_evidence_collection(output)

        self.assertEqual(collection.material_id, "MAT-0027")
        self.assertEqual(collection.evidence, ())

    def test_material_identity_is_preserved(self) -> None:
        output = self._output(material_id="MAT-IDENTITY-27")

        collection = build_llm_evidence_collection(output)

        self.assertEqual(collection.material_id, output.material_id)
        self.assertTrue(
            all(
                item.material_id == output.material_id
                for item in collection.evidence
            )
        )

    def test_decision_and_confidence_do_not_change_evidence_contract(self) -> None:
        review = self._output(
            decision=GovernanceDecision.REVIEW,
            confidence=0.10,
        )
        reject = self._output(
            decision=GovernanceDecision.REJECT,
            confidence=0.99,
        )

        review_collection = build_llm_evidence_collection(review)
        reject_collection = build_llm_evidence_collection(reject)

        self.assertEqual(review_collection, reject_collection)

    def test_issue_and_evidence_cardinality_must_match(self) -> None:
        output = self._output(
            issues=(
                IssueType.SUSPICIOUS_UNIT,
                IssueType.AMBIGUOUS_DESCRIPTION,
            ),
            evidence=("Somente uma observação.",),
        )

        with self.assertRaises(ValueError):
            build_llm_evidence_collection(output)


if __name__ == "__main__":
    unittest.main()
