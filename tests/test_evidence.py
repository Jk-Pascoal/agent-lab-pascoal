import unittest
from dataclasses import FrozenInstanceError

from agent_lab.domain import IssueType
from agent_lab.evidence import (
    EvidenceCollection,
    EvidenceSource,
    GovernanceEvidence,
)


class GovernanceEvidenceTests(unittest.TestCase):
    def test_creates_valid_governance_evidence(self):
        evidence = GovernanceEvidence(
            material_id="MAT-00125",
            source=EvidenceSource.RULE,
            issue_type=IssueType.SUSPICIOUS_UNIT,
            observation="Unidade informada apresenta inconsistência.",
        )

        self.assertEqual(evidence.material_id, "MAT-00125")
        self.assertEqual(evidence.source, EvidenceSource.RULE)
        self.assertEqual(evidence.issue_type, IssueType.SUSPICIOUS_UNIT)
        self.assertEqual(
            evidence.observation,
            "Unidade informada apresenta inconsistência.",
        )

    def test_rejects_empty_material_id(self):
        with self.assertRaises(ValueError):
            GovernanceEvidence(
                material_id="",
                source=EvidenceSource.RULE,
                issue_type=IssueType.SUSPICIOUS_UNIT,
                observation="Unidade informada apresenta inconsistência.",
            )

    def test_rejects_empty_observation(self):
        with self.assertRaises(ValueError):
            GovernanceEvidence(
                material_id="MAT-00125",
                source=EvidenceSource.RULE,
                issue_type=IssueType.SUSPICIOUS_UNIT,
                observation="",
            )

    def test_governance_evidence_is_immutable(self):
        evidence = GovernanceEvidence(
            material_id="MAT-00125",
            source=EvidenceSource.RULE,
            issue_type=IssueType.SUSPICIOUS_UNIT,
            observation="Unidade informada apresenta inconsistência.",
        )

        with self.assertRaises(FrozenInstanceError):
            evidence.observation = "Observação alterada."

    def test_collects_multiple_evidence_for_same_material(self):
        first_evidence = GovernanceEvidence(
            material_id="MAT-00125",
            source=EvidenceSource.RULE,
            issue_type=IssueType.SUSPICIOUS_UNIT,
            observation="Unidade informada apresenta inconsistência.",
        )

        second_evidence = GovernanceEvidence(
            material_id="MAT-00125",
            source=EvidenceSource.DUPLICATE,
            issue_type=IssueType.POSSIBLE_DUPLICATE,
            observation="Possível material duplicado identificado.",
        )

        collection = EvidenceCollection(
            material_id="MAT-00125",
            evidence=(first_evidence, second_evidence),
        )

        self.assertEqual(collection.material_id, "MAT-00125")
        self.assertEqual(len(collection.evidence), 2)
        self.assertEqual(collection.evidence[0], first_evidence)
        self.assertEqual(collection.evidence[1], second_evidence)

    def test_rejects_evidence_from_different_material(self):
        valid_evidence = GovernanceEvidence(
            material_id="MAT-00125",
            source=EvidenceSource.RULE,
            issue_type=IssueType.SUSPICIOUS_UNIT,
            observation="Unidade informada apresenta inconsistência.",
        )

        foreign_evidence = GovernanceEvidence(
            material_id="MAT-99999",
            source=EvidenceSource.DUPLICATE,
            issue_type=IssueType.POSSIBLE_DUPLICATE,
            observation="Evidência pertence a outro material.",
        )

        with self.assertRaises(ValueError):
            EvidenceCollection(
                material_id="MAT-00125",
                evidence=(valid_evidence, foreign_evidence),
            )

    def test_rejects_empty_collection_material_id(self):
        with self.assertRaises(ValueError):
            EvidenceCollection(
                material_id="",
                evidence=(),
            )

    def test_rejects_uncontrolled_source_value(self):
        with self.assertRaises(ValueError):
            GovernanceEvidence(
                material_id="MAT-00125",
                source="RULE",
                issue_type=IssueType.SUSPICIOUS_UNIT,
                observation="Unidade informada apresenta inconsistência.",
            )

    def test_rejects_uncontrolled_issue_type_value(self):
        with self.assertRaises(ValueError):
            GovernanceEvidence(
                material_id="MAT-00125",
                source=EvidenceSource.RULE,
                issue_type="SUSPICIOUS_UNIT",
                observation="Unidade informada apresenta inconsistência.",
            )

    def test_allows_empty_collection_for_valid_material(self):
        collection = EvidenceCollection(
            material_id="MAT-00125",
            evidence=(),
        )

        self.assertEqual(collection.material_id, "MAT-00125")
        self.assertEqual(collection.evidence, ())

    def test_evidence_collection_is_immutable(self):
        collection = EvidenceCollection(
            material_id="MAT-00125",
            evidence=(),
        )

        with self.assertRaises(FrozenInstanceError):
            collection.material_id = "MAT-99999"

    def test_evidence_contract_has_no_governance_decision(self):
        self.assertNotIn("decision", GovernanceEvidence.__dataclass_fields__)
        self.assertNotIn("decision", EvidenceCollection.__dataclass_fields__)


if __name__ == "__main__":
    unittest.main()
