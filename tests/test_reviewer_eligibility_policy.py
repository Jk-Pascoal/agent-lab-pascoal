from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
import unittest

from agent_lab.human_review import VerifiedSpecialistIdentity
from agent_lab.human_review_claim import HumanReviewClaim
from agent_lab.human_review_claim_projection import HumanReviewClaimState

from agent_lab.reviewer_eligibility_policy import (
    ReviewerEligibilityDecision,
    ReviewerEligibilityStatus,
)


class ReviewerEligibilityContractsTests(unittest.TestCase):
    def test_status_enum_members_and_values(self) -> None:
        expected_members = {
            "ELIGIBLE": "ELIGIBLE",
            "CLAIM_REQUIRED": "CLAIM_REQUIRED",
            "CLAIMANT_MISMATCH": "CLAIMANT_MISMATCH",
            "MULTIPLE_CLAIMS_CONFLICT": "MULTIPLE_CLAIMS_CONFLICT",
        }
        self.assertEqual(
            {
                name: member.value
                for name, member in ReviewerEligibilityStatus.__members__.items()
            },
            expected_members,
        )
        self.assertEqual(len(ReviewerEligibilityStatus.__members__), 4)

    def test_decision_valid_construction_and_attribute_access(self) -> None:
        decision = ReviewerEligibilityDecision(
            status=ReviewerEligibilityStatus.ELIGIBLE
        )
        self.assertIsInstance(decision, ReviewerEligibilityDecision)
        self.assertEqual(decision.status, ReviewerEligibilityStatus.ELIGIBLE)

    def test_decision_constructor_rejects_redundant_arguments(self) -> None:
        with self.assertRaises(TypeError):
            ReviewerEligibilityDecision(  # type: ignore[call-arg]
                status=ReviewerEligibilityStatus.ELIGIBLE,
                is_eligible=True,
            )

        with self.assertRaises(TypeError):
            ReviewerEligibilityDecision(  # type: ignore[call-arg]
                status=ReviewerEligibilityStatus.ELIGIBLE,
                reason="Redundant reason argument",
            )

    def test_decision_constructor_rejects_invalid_status_types(self) -> None:
        invalid_statuses = [
            "ELIGIBLE",
            True,
            False,
            None,
            object(),
            123,
            [],
        ]
        for invalid in invalid_statuses:
            with self.subTest(invalid=invalid):
                with self.assertRaises(TypeError):
                    ReviewerEligibilityDecision(status=invalid)  # type: ignore[arg-type]

    def test_decision_is_eligible_is_strictly_derived_property(self) -> None:
        eligible_decision = ReviewerEligibilityDecision(
            status=ReviewerEligibilityStatus.ELIGIBLE
        )
        self.assertIs(eligible_decision.is_eligible, True)

        ineligible_statuses = [
            ReviewerEligibilityStatus.CLAIM_REQUIRED,
            ReviewerEligibilityStatus.CLAIMANT_MISMATCH,
            ReviewerEligibilityStatus.MULTIPLE_CLAIMS_CONFLICT,
        ]
        for status in ineligible_statuses:
            with self.subTest(status=status):
                decision = ReviewerEligibilityDecision(status=status)
                self.assertIs(decision.is_eligible, False)

    def test_decision_reason_is_strictly_derived_non_empty_string(self) -> None:
        for status in ReviewerEligibilityStatus:
            with self.subTest(status=status):
                decision = ReviewerEligibilityDecision(status=status)
                self.assertIsInstance(decision.reason, str)
                self.assertTrue(bool(decision.reason.strip()))

    def test_decision_immutability(self) -> None:
        decision = ReviewerEligibilityDecision(
            status=ReviewerEligibilityStatus.ELIGIBLE
        )
        with self.assertRaises(FrozenInstanceError):
            decision.status = ReviewerEligibilityStatus.CLAIM_REQUIRED  # type: ignore[misc]

    def test_decision_uses_slots_and_has_no_dict(self) -> None:
        decision = ReviewerEligibilityDecision(
            status=ReviewerEligibilityStatus.ELIGIBLE
        )
        self.assertFalse(hasattr(decision, "__dict__"))


class ReviewerEligibilityEvaluationTests(unittest.TestCase):
    def test_no_claim_requires_claim_before_reviewer_is_eligible(self) -> None:
        from agent_lab.reviewer_eligibility_policy import (
            evaluate_reviewer_claim_eligibility,
        )

        claim_state = HumanReviewClaimState(
            workflow_id="WF-001",
            claims=(),
        )

        reviewer_identity = VerifiedSpecialistIdentity(
            specialist_id="SPEC-001",
            identity_provider="CORP_IDP",
            identity_subject="subject-001",
            verification_id="VER-001",
            verified_at=datetime(2026, 9, 5, 12, 0, tzinfo=timezone.utc),
        )

        decision = evaluate_reviewer_claim_eligibility(
            claim_state,
            reviewer_identity,
        )

        self.assertEqual(
            decision.status,
            ReviewerEligibilityStatus.CLAIM_REQUIRED,
        )
        self.assertIs(decision.is_eligible, False)

    def test_single_claim_matching_stable_principal_is_eligible(self) -> None:
        from agent_lab.reviewer_eligibility_policy import (
            evaluate_reviewer_claim_eligibility,
        )

        claimant_identity = VerifiedSpecialistIdentity(
            specialist_id="SPEC-001",
            identity_provider="CORP_IDP",
            identity_subject="subject-001",
            verification_id="VER-001",
            verified_at=datetime(
                2026, 9, 5, 12, 0, tzinfo=timezone.utc
            ),
        )

        reviewer_identity = VerifiedSpecialistIdentity(
            specialist_id="SPEC-001",
            identity_provider="CORP_IDP",
            identity_subject="subject-001",
            verification_id="VER-001",
            verified_at=datetime(
                2026, 9, 5, 12, 0, tzinfo=timezone.utc
            ),
        )

        claim = HumanReviewClaim(
            claim_id="CLM-001",
            workflow_id="WF-001",
            specialist=claimant_identity,
            claimed_at=datetime(
                2026, 9, 5, 12, 5, tzinfo=timezone.utc
            ),
        )

        claim_state = HumanReviewClaimState(
            workflow_id="WF-001",
            claims=(claim,),
        )

        decision = evaluate_reviewer_claim_eligibility(
            claim_state,
            reviewer_identity,
        )

        self.assertEqual(
            decision.status,
            ReviewerEligibilityStatus.ELIGIBLE,
        )
        self.assertIs(decision.is_eligible, True)


if __name__ == "__main__":
    unittest.main()
