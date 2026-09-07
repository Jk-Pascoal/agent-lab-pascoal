from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

from agent_lab.decision import DecisionRecommendation
from agent_lab.domain import GovernanceDecision
from agent_lab.human_review import (
    HumanDecision,
    HumanReview,
    VerifiedSpecialistIdentity,
)
from agent_lab.human_review_claim import (
    HumanReviewClaim,
    HumanReviewClaimRelease,
    claim_pending_human_review,
)
from agent_lab.workflow import (
    GovernanceWorkflow,
    WorkflowStatus,
    conclude_governance_workflow,
)


class HumanReviewClaimTests(unittest.TestCase):
    def setUp(self) -> None:
        self.opened_at = datetime(
            2026,
            8,
            31,
            9,
            0,
            0,
            tzinfo=timezone.utc,
        )
        self.verified_at = datetime(
            2026,
            8,
            31,
            8,
            30,
            0,
            tzinfo=timezone.utc,
        )
        self.claimed_at = datetime(
            2026,
            8,
            31,
            9,
            15,
            0,
            tzinfo=timezone.utc,
        )
        self.recommendation = DecisionRecommendation(
            material_id="MAT-0001",
            decision=GovernanceDecision.APPROVE,
            evidence=(),
            rationale="Recomendação de teste",
            requires_human_decision=True,
        )
        self.specialist = VerifiedSpecialistIdentity(
            specialist_id="spec-001",
            identity_provider="corp-idp",
            identity_subject="specialist@corp.local",
            verification_id="ver-12345",
            verified_at=self.verified_at,
        )
        self.workflow = GovernanceWorkflow(
            workflow_id="WF-001",
            recommendation=self.recommendation,
            opened_at=self.opened_at,
        )

    def test_claim_pending_human_review_success(self) -> None:
        claim = claim_pending_human_review(
            self.workflow,
            claim_id="CLAIM-001",
            specialist=self.specialist,
            claimed_at=self.claimed_at,
        )

        self.assertIsInstance(claim, HumanReviewClaim)
        self.assertEqual(claim.claim_id, "CLAIM-001")
        self.assertEqual(claim.workflow_id, self.workflow.workflow_id)
        self.assertEqual(claim.specialist, self.specialist)
        self.assertEqual(claim.claimed_at, self.claimed_at)
        self.assertEqual(
            self.workflow.status, WorkflowStatus.PENDING_HUMAN_REVIEW
        )
        self.assertIsNone(self.workflow.review)

    def test_claim_rejects_empty_claim_id(self) -> None:
        with self.assertRaises(ValueError):
            claim_pending_human_review(
                self.workflow,
                claim_id="",
                specialist=self.specialist,
                claimed_at=self.claimed_at,
            )

    def test_claim_rejects_whitespace_claim_id(self) -> None:
        with self.assertRaises(ValueError):
            claim_pending_human_review(
                self.workflow,
                claim_id="   ",
                specialist=self.specialist,
                claimed_at=self.claimed_at,
            )

    def test_human_review_claim_rejects_empty_workflow_id(self) -> None:
        with self.assertRaises(ValueError):
            HumanReviewClaim(
                claim_id="CLAIM-001",
                workflow_id="",
                specialist=self.specialist,
                claimed_at=self.claimed_at,
            )

    def test_human_review_claim_rejects_invalid_specialist_type(self) -> None:
        with self.assertRaises(TypeError):
            HumanReviewClaim(
                claim_id="CLAIM-001",
                workflow_id="WF-001",
                specialist="invalid-specialist",  # type: ignore[arg-type]
                claimed_at=self.claimed_at,
            )

    def test_human_review_claim_rejects_invalid_claimed_at_type(self) -> None:
        with self.assertRaises(TypeError):
            HumanReviewClaim(
                claim_id="CLAIM-001",
                workflow_id="WF-001",
                specialist=self.specialist,
                claimed_at="invalid-datetime",  # type: ignore[arg-type]
            )

    def test_human_review_claim_rejects_naive_claimed_at(self) -> None:
        naive_claimed_at = datetime(
            2026,
            8,
            31,
            9,
            15,
            0,
        )

        with self.assertRaises(ValueError):
            HumanReviewClaim(
                claim_id="CLAIM-001",
                workflow_id="WF-001",
                specialist=self.specialist,
                claimed_at=naive_claimed_at,
            )

    def test_human_review_claim_rejects_specialist_verified_after_claim(
        self,
    ) -> None:
        specialist = VerifiedSpecialistIdentity(
            specialist_id="spec-002",
            identity_provider="corp-idp",
            identity_subject="late@corp.local",
            verification_id="ver-late",
            verified_at=datetime(
                2026,
                8,
                31,
                9,
                30,
                0,
                tzinfo=timezone.utc,
            ),
        )

        with self.assertRaises(ValueError):
            HumanReviewClaim(
                claim_id="CLAIM-001",
                workflow_id="WF-001",
                specialist=specialist,
                claimed_at=self.claimed_at,
            )

    def test_human_review_claim_allows_specialist_verified_at_claimed_at(
        self,
    ) -> None:
        specialist = VerifiedSpecialistIdentity(
            specialist_id="spec-003",
            identity_provider="corp-idp",
            identity_subject="boundary@corp.local",
            verification_id="ver-boundary",
            verified_at=self.claimed_at,
        )

        claim = HumanReviewClaim(
            claim_id="CLAIM-001",
            workflow_id="WF-001",
            specialist=specialist,
            claimed_at=self.claimed_at,
        )

        self.assertEqual(claim.specialist, specialist)
        self.assertEqual(claim.claimed_at, self.claimed_at)

    def test_claim_rejects_claimed_at_before_opened_at(self) -> None:
        claimed_at = datetime(
            2026,
            8,
            31,
            8,
            45,
            0,
            tzinfo=timezone.utc,
        )

        with self.assertRaises(ValueError):
            claim_pending_human_review(
                self.workflow,
                claim_id="CLAIM-001",
                specialist=self.specialist,
                claimed_at=claimed_at,
            )

    def test_claim_allows_claimed_at_equal_to_opened_at(self) -> None:
        specialist = VerifiedSpecialistIdentity(
            specialist_id="spec-004",
            identity_provider="corp-idp",
            identity_subject="opening-boundary@corp.local",
            verification_id="ver-opening-boundary",
            verified_at=self.workflow.opened_at,
        )

        claim = claim_pending_human_review(
            self.workflow,
            claim_id="CLAIM-001",
            specialist=specialist,
            claimed_at=self.workflow.opened_at,
        )

        self.assertEqual(claim.claimed_at, self.workflow.opened_at)
        self.assertEqual(claim.workflow_id, self.workflow.workflow_id)

    def test_claim_rejects_reviewed_workflow(self) -> None:
        reviewed_at = datetime(
            2026,
            8,
            31,
            9,
            30,
            0,
            tzinfo=timezone.utc,
        )
        review = HumanReview(
            review_id="REV-001",
            material_id=self.recommendation.material_id,
            system_recommendation=self.recommendation.decision,
            human_decision=HumanDecision.APPROVE,
            reviewer_identity=self.specialist,
            reviewed_at=reviewed_at,
        )
        reviewed_workflow = conclude_governance_workflow(self.workflow, review)
        claimed_at = datetime(
            2026,
            8,
            31,
            9,
            45,
            0,
            tzinfo=timezone.utc,
        )

        with self.assertRaises(ValueError):
            claim_pending_human_review(
                reviewed_workflow,
                claim_id="CLAIM-001",
                specialist=self.specialist,
                claimed_at=claimed_at,
            )

    def test_claim_rejects_invalid_workflow_type(self) -> None:
        with self.assertRaises(TypeError):
            claim_pending_human_review(
                "invalid-workflow",  # type: ignore[arg-type]
                claim_id="CLAIM-001",
                specialist=self.specialist,
                claimed_at=self.claimed_at,
            )

    def test_human_review_claim_symbols_are_publicly_exported(self) -> None:
        import agent_lab

        self.assertIs(agent_lab.HumanReviewClaim, HumanReviewClaim)
        self.assertIs(
            agent_lab.claim_pending_human_review,
            claim_pending_human_review,
        )

    def test_human_review_claim_rejects_invalid_claim_id_type(self) -> None:
        with self.assertRaises(TypeError):
            HumanReviewClaim(
                claim_id=123,  # type: ignore[arg-type]
                workflow_id="WF-001",
                specialist=self.specialist,
                claimed_at=self.claimed_at,
            )

    def test_human_review_claim_rejects_invalid_workflow_id_type(self) -> None:
        with self.assertRaises(TypeError):
            HumanReviewClaim(
                claim_id="CLAIM-001",
                workflow_id=123,  # type: ignore[arg-type]
                specialist=self.specialist,
                claimed_at=self.claimed_at,
            )

    def test_human_review_claim_rejects_whitespace_workflow_id(self) -> None:
        with self.assertRaises(ValueError):
            HumanReviewClaim(
                claim_id="CLAIM-001",
                workflow_id="   ",
                specialist=self.specialist,
                claimed_at=self.claimed_at,
            )

    def test_human_review_claim_is_immutable(self) -> None:
        claim = HumanReviewClaim(
            claim_id="CLAIM-001",
            workflow_id="WF-001",
            specialist=self.specialist,
            claimed_at=self.claimed_at,
        )

        with self.assertRaises(FrozenInstanceError):
            claim.claim_id = "CLAIM-002"  # type: ignore[misc]


class HumanReviewClaimReleaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.verified_at = datetime(
            2026,
            9,
            7,
            8,
            30,
            0,
            tzinfo=timezone.utc,
        )
        self.released_at = datetime(
            2026,
            9,
            7,
            9,
            0,
            0,
            tzinfo=timezone.utc,
        )
        self.specialist = VerifiedSpecialistIdentity(
            specialist_id="spec-001",
            identity_provider="corp-idp",
            identity_subject="specialist@corp.local",
            verification_id="ver-12345",
            verified_at=self.verified_at,
        )

    def test_nominal_creation_and_fields(self) -> None:
        release = HumanReviewClaimRelease(
            release_id="REL-001",
            claim_id="CLAIM-001",
            workflow_id="WF-001",
            released_by=self.specialist,
            released_at=self.released_at,
        )

        self.assertIsInstance(release, HumanReviewClaimRelease)
        self.assertEqual(release.release_id, "REL-001")
        self.assertEqual(release.claim_id, "CLAIM-001")
        self.assertEqual(release.workflow_id, "WF-001")
        self.assertEqual(release.released_by, self.specialist)
        self.assertEqual(release.released_at, self.released_at)

    def test_is_immutable_and_slots(self) -> None:
        release = HumanReviewClaimRelease(
            release_id="REL-001",
            claim_id="CLAIM-001",
            workflow_id="WF-001",
            released_by=self.specialist,
            released_at=self.released_at,
        )

        with self.assertRaises(FrozenInstanceError):
            release.release_id = "REL-002"  # type: ignore[misc]

        self.assertFalse(hasattr(release, "__dict__"))
        self.assertTrue(hasattr(release, "__slots__"))
        self.assertEqual(
            set(release.__slots__),
            {
                "release_id",
                "claim_id",
                "workflow_id",
                "released_by",
                "released_at",
            },
        )

    def test_sanitizes_only_release_id(self) -> None:
        release = HumanReviewClaimRelease(
            release_id="  REL-001  ",
            claim_id="CLAIM-001",
            workflow_id="WF-001",
            released_by=self.specialist,
            released_at=self.released_at,
        )
        self.assertEqual(release.release_id, "REL-001")
        self.assertEqual(release.claim_id, "CLAIM-001")
        self.assertEqual(release.workflow_id, "WF-001")
        self.assertEqual(release.released_by, self.specialist)
        self.assertEqual(release.released_at, self.released_at)

        for invalid_id in ("", "   ", "\t\n"):
            with self.assertRaises(ValueError):
                HumanReviewClaimRelease(
                    release_id=invalid_id,
                    claim_id="CLAIM-001",
                    workflow_id="WF-001",
                    released_by=self.specialist,
                    released_at=self.released_at,
                )

        for invalid_type in (None, 123, True, False, ["REL-001"]):
            with self.assertRaises(TypeError):
                HumanReviewClaimRelease(
                    release_id=invalid_type,  # type: ignore[arg-type]
                    claim_id="CLAIM-001",
                    workflow_id="WF-001",
                    released_by=self.specialist,
                    released_at=self.released_at,
                )

    def test_preserves_claim_id_and_workflow_id_without_strip(self) -> None:
        raw_claim_id = "  CLAIM-001  "
        raw_workflow_id = "  WF-001  "
        release = HumanReviewClaimRelease(
            release_id="REL-001",
            claim_id=raw_claim_id,
            workflow_id=raw_workflow_id,
            released_by=self.specialist,
            released_at=self.released_at,
        )
        self.assertEqual(release.claim_id, raw_claim_id)
        self.assertEqual(release.workflow_id, raw_workflow_id)

        for invalid_claim_id in ("", "   ", "\t"):
            with self.assertRaises(ValueError):
                HumanReviewClaimRelease(
                    release_id="REL-001",
                    claim_id=invalid_claim_id,
                    workflow_id="WF-001",
                    released_by=self.specialist,
                    released_at=self.released_at,
                )

        for invalid_wf_id in ("", "   ", "\t"):
            with self.assertRaises(ValueError):
                HumanReviewClaimRelease(
                    release_id="REL-001",
                    claim_id="CLAIM-001",
                    workflow_id=invalid_wf_id,
                    released_by=self.specialist,
                    released_at=self.released_at,
                )

        for invalid_type in (None, 123, True, False, ["ID"]):
            with self.assertRaises(TypeError):
                HumanReviewClaimRelease(
                    release_id="REL-001",
                    claim_id=invalid_type,  # type: ignore[arg-type]
                    workflow_id="WF-001",
                    released_by=self.specialist,
                    released_at=self.released_at,
                )
            with self.assertRaises(TypeError):
                HumanReviewClaimRelease(
                    release_id="REL-001",
                    claim_id="CLAIM-001",
                    workflow_id=invalid_type,  # type: ignore[arg-type]
                    released_by=self.specialist,
                    released_at=self.released_at,
                )

    def test_validates_released_by(self) -> None:
        for invalid_specialist in (None, "spec-001", 123, True, False, object()):
            with self.assertRaises(TypeError):
                HumanReviewClaimRelease(
                    release_id="REL-001",
                    claim_id="CLAIM-001",
                    workflow_id="WF-001",
                    released_by=invalid_specialist,  # type: ignore[arg-type]
                    released_at=self.released_at,
                )

    def test_validates_released_at_timezone_aware(self) -> None:
        for invalid_date in (None, "2026-09-07T09:00:00Z", 123, True):
            with self.assertRaises(TypeError):
                HumanReviewClaimRelease(
                    release_id="REL-001",
                    claim_id="CLAIM-001",
                    workflow_id="WF-001",
                    released_by=self.specialist,
                    released_at=invalid_date,  # type: ignore[arg-type]
                )

        naive_dt = datetime(2026, 9, 7, 9, 0, 0)
        with self.assertRaises(ValueError):
            HumanReviewClaimRelease(
                release_id="REL-001",
                claim_id="CLAIM-001",
                workflow_id="WF-001",
                released_by=self.specialist,
                released_at=naive_dt,
            )

    def test_validates_released_by_verified_at_consistency(self) -> None:
        future_verified_specialist = VerifiedSpecialistIdentity(
            specialist_id="spec-001",
            identity_provider="corp-idp",
            identity_subject="specialist@corp.local",
            verification_id="ver-12345",
            verified_at=datetime(2026, 9, 7, 9, 30, 0, tzinfo=timezone.utc),
        )

        with self.assertRaises(ValueError):
            HumanReviewClaimRelease(
                release_id="REL-001",
                claim_id="CLAIM-001",
                workflow_id="WF-001",
                released_by=future_verified_specialist,
                released_at=self.released_at,
            )

        boundary_release = HumanReviewClaimRelease(
            release_id="REL-001",
            claim_id="CLAIM-001",
            workflow_id="WF-001",
            released_by=self.specialist,
            released_at=self.verified_at,
        )
        self.assertEqual(
            boundary_release.released_at, boundary_release.released_by.verified_at
        )


if __name__ == "__main__":
    unittest.main()
