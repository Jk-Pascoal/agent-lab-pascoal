import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

from agent_lab.audit import (
    AuditEvent,
    AuditEventType,
    HumanReviewResult,
    record_human_review,
)
from agent_lab.domain import GovernanceDecision
from agent_lab.human_review import CorrectionRequest, HumanDecision


class AuditEventTests(unittest.TestCase):
    def setUp(self):
        self.occurred_at = datetime(
            2026,
            8,
            15,
            14,
            0,
            tzinfo=timezone.utc,
        )

    def build_event(self, **overrides):
        values = {
            "event_id": "event-001",
            "event_type": AuditEventType.HUMAN_REVIEW_RECORDED,
            "material_id": "MAT-001",
            "actor_id": "specialist-001",
            "occurred_at": self.occurred_at,
            "review_id": "review-001",
            "metadata": {
                "system_recommendation": "REVIEW",
                "human_decision": "REQUEST_CORRECTION",
                "agrees_with_system": True,
            },
        }
        values.update(overrides)
        return AuditEvent(**values)

    def test_creates_valid_audit_event(self):
        event = self.build_event()

        self.assertEqual(event.event_id, "event-001")
        self.assertEqual(
            event.event_type,
            AuditEventType.HUMAN_REVIEW_RECORDED,
        )
        self.assertEqual(event.material_id, "MAT-001")
        self.assertEqual(event.actor_id, "specialist-001")
        self.assertEqual(event.review_id, "review-001")
        self.assertEqual(event.occurred_at, self.occurred_at)

    def test_rejects_blank_identifiers(self):
        for field_name in (
            "event_id",
            "material_id",
            "actor_id",
            "review_id",
        ):
            with self.subTest(field_name=field_name):
                with self.assertRaises(ValueError):
                    self.build_event(**{field_name: "   "})

    def test_rejects_naive_timestamp(self):
        with self.assertRaises(ValueError):
            self.build_event(
                occurred_at=datetime(2026, 8, 15, 14, 0),
            )

    def test_copies_and_freezes_metadata(self):
        source = {"agrees_with_system": True}

        event = self.build_event(metadata=source)
        source["agrees_with_system"] = False

        self.assertTrue(event.metadata["agrees_with_system"])
        with self.assertRaises(TypeError):
            event.metadata["agrees_with_system"] = False

    def test_is_immutable(self):
        event = self.build_event()

        with self.assertRaises(FrozenInstanceError):
            event.actor_id = "specialist-002"


class RecordHumanReviewTests(unittest.TestCase):
    def setUp(self):
        self.reviewed_at = datetime(
            2026,
            8,
            15,
            14,
            30,
            tzinfo=timezone.utc,
        )
        self.correction = CorrectionRequest(
            field_name="unit_of_measure",
            reason="Padronizar unidade de medida.",
            suggested_value="PC",
        )

    def record(self, **overrides):
        values = {
            "event_id": "event-001",
            "review_id": "review-001",
            "material_id": "MAT-001",
            "system_recommendation": GovernanceDecision.REVIEW,
            "human_decision": HumanDecision.REQUEST_CORRECTION,
            "reviewer_id": "specialist-001",
            "reviewed_at": self.reviewed_at,
            "justification": "Corrigir unidade antes da aprovação.",
            "corrections": (self.correction,),
        }
        values.update(overrides)
        return record_human_review(**values)

    def test_returns_review_and_correlated_audit_event(self):
        result = self.record()

        self.assertIsInstance(result, HumanReviewResult)
        self.assertEqual(result.review.review_id, "review-001")
        self.assertEqual(result.audit_event.review_id, "review-001")
        self.assertEqual(
            result.audit_event.material_id,
            result.review.material_id,
        )
        self.assertEqual(
            result.audit_event.actor_id,
            result.review.reviewer_id,
        )
        self.assertEqual(
            result.audit_event.occurred_at,
            result.review.reviewed_at,
        )

    def test_preserves_original_system_recommendation(self):
        result = self.record(
            system_recommendation=GovernanceDecision.APPROVE,
            human_decision=HumanDecision.REJECT,
            justification="Conflito de classificação encontrado.",
            corrections=(),
        )

        self.assertEqual(
            result.review.system_recommendation,
            GovernanceDecision.APPROVE,
        )
        self.assertFalse(result.review.agrees_with_system)
        self.assertEqual(
            result.audit_event.metadata["system_recommendation"],
            "APPROVE",
        )

    def test_audit_metadata_records_human_decision_and_agreement(self):
        result = self.record()

        self.assertEqual(
            result.audit_event.metadata["human_decision"],
            "REQUEST_CORRECTION",
        )
        self.assertTrue(
            result.audit_event.metadata["agrees_with_system"]
        )

    def test_invalid_review_does_not_produce_a_result(self):
        with self.assertRaises(ValueError):
            self.record(
                human_decision=HumanDecision.REJECT,
                justification="   ",
                corrections=(),
            )

    def test_result_is_immutable(self):
        result = self.record()

        with self.assertRaises(FrozenInstanceError):
            result.review = None


if __name__ == "__main__":
    unittest.main()

