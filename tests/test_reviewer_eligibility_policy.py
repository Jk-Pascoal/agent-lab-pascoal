from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
import unittest

from agent_lab.human_review import VerifiedSpecialistIdentity
from agent_lab.human_review_claim import HumanReviewClaim
from agent_lab.human_review_claim_projection import (
    HumanReviewClaimFactState,
    HumanReviewClaimState,
)

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

    def test_single_claim_specialist_id_mismatch_is_claimant_mismatch(self) -> None:
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
            specialist_id="SPEC-002",
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
            ReviewerEligibilityStatus.CLAIMANT_MISMATCH,
        )
        self.assertIs(decision.is_eligible, False)

    def test_single_claim_identity_provider_mismatch_is_claimant_mismatch(self) -> None:
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
            identity_provider="EXTERNAL_IDP",
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
            ReviewerEligibilityStatus.CLAIMANT_MISMATCH,
        )
        self.assertIs(decision.is_eligible, False)

    def test_single_claim_identity_subject_mismatch_is_claimant_mismatch(self) -> None:
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
            identity_subject="subject-002",
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
            ReviewerEligibilityStatus.CLAIMANT_MISMATCH,
        )
        self.assertIs(decision.is_eligible, False)

    def test_single_claim_different_verification_id_preserves_eligibility(self) -> None:
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
            verification_id="VER-002",
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

    def test_single_claim_different_verified_at_preserves_eligibility(self) -> None:
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
                2026, 9, 5, 12, 2, tzinfo=timezone.utc
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

    def test_multiple_claims_with_different_principals_are_conflict(self) -> None:
        from agent_lab.reviewer_eligibility_policy import (
            evaluate_reviewer_claim_eligibility,
        )

        claimant_1 = VerifiedSpecialistIdentity(
            specialist_id="SPEC-001",
            identity_provider="CORP_IDP",
            identity_subject="subject-001",
            verification_id="VER-001",
            verified_at=datetime(
                2026, 9, 5, 12, 0, tzinfo=timezone.utc
            ),
        )

        claimant_2 = VerifiedSpecialistIdentity(
            specialist_id="SPEC-002",
            identity_provider="CORP_IDP",
            identity_subject="subject-002",
            verification_id="VER-002",
            verified_at=datetime(
                2026, 9, 5, 12, 0, tzinfo=timezone.utc
            ),
        )

        reviewer_identity = VerifiedSpecialistIdentity(
            specialist_id="SPEC-001",
            identity_provider="CORP_IDP",
            identity_subject="subject-001",
            verification_id="VER-003",
            verified_at=datetime(
                2026, 9, 5, 12, 1, tzinfo=timezone.utc
            ),
        )

        claim_1 = HumanReviewClaim(
            claim_id="CLM-001",
            workflow_id="WF-001",
            specialist=claimant_1,
            claimed_at=datetime(
                2026, 9, 5, 12, 5, tzinfo=timezone.utc
            ),
        )

        claim_2 = HumanReviewClaim(
            claim_id="CLM-002",
            workflow_id="WF-001",
            specialist=claimant_2,
            claimed_at=datetime(
                2026, 9, 5, 12, 6, tzinfo=timezone.utc
            ),
        )

        claim_state = HumanReviewClaimState(
            workflow_id="WF-001",
            claims=(claim_1, claim_2),
        )

        decision = evaluate_reviewer_claim_eligibility(
            claim_state,
            reviewer_identity,
        )

        self.assertEqual(
            decision.status,
            ReviewerEligibilityStatus.MULTIPLE_CLAIMS_CONFLICT,
        )
        self.assertIs(decision.is_eligible, False)

    def test_multiple_claims_same_principal_remain_conflict(self) -> None:
        from agent_lab.reviewer_eligibility_policy import (
            evaluate_reviewer_claim_eligibility,
        )

        identity_1 = VerifiedSpecialistIdentity(
            specialist_id="SPEC-001",
            identity_provider="CORP_IDP",
            identity_subject="subject-001",
            verification_id="VER-001",
            verified_at=datetime(
                2026, 9, 5, 12, 0, tzinfo=timezone.utc
            ),
        )

        identity_2 = VerifiedSpecialistIdentity(
            specialist_id="SPEC-001",
            identity_provider="CORP_IDP",
            identity_subject="subject-001",
            verification_id="VER-002",
            verified_at=datetime(
                2026, 9, 5, 12, 1, tzinfo=timezone.utc
            ),
        )

        reviewer_identity = VerifiedSpecialistIdentity(
            specialist_id="SPEC-001",
            identity_provider="CORP_IDP",
            identity_subject="subject-001",
            verification_id="VER-003",
            verified_at=datetime(
                2026, 9, 5, 12, 2, tzinfo=timezone.utc
            ),
        )

        claim_1 = HumanReviewClaim(
            claim_id="CLM-001",
            workflow_id="WF-001",
            specialist=identity_1,
            claimed_at=datetime(
                2026, 9, 5, 12, 5, tzinfo=timezone.utc
            ),
        )

        claim_2 = HumanReviewClaim(
            claim_id="CLM-002",
            workflow_id="WF-001",
            specialist=identity_2,
            claimed_at=datetime(
                2026, 9, 5, 12, 6, tzinfo=timezone.utc
            ),
        )

        claim_state = HumanReviewClaimState(
            workflow_id="WF-001",
            claims=(claim_1, claim_2),
        )

        self.assertEqual(
            claim_state.state,
            HumanReviewClaimFactState.MULTIPLE_CLAIMS,
        )

        decision = evaluate_reviewer_claim_eligibility(
            claim_state,
            reviewer_identity,
        )

        self.assertEqual(
            decision.status,
            ReviewerEligibilityStatus.MULTIPLE_CLAIMS_CONFLICT,
        )
        self.assertIs(decision.is_eligible, False)

    def test_evaluate_rejects_invalid_claim_state(self) -> None:
        from agent_lab.reviewer_eligibility_policy import (
            evaluate_reviewer_claim_eligibility,
        )

        valid_reviewer_identity = VerifiedSpecialistIdentity(
            specialist_id="SPEC-001",
            identity_provider="CORP_IDP",
            identity_subject="subject-001",
            verification_id="VER-001",
            verified_at=datetime(2026, 9, 5, 12, 0, tzinfo=timezone.utc),
        )

        invalid_claim_states = [
            None,
            "WF-001",
            True,
            False,
            123,
            object(),
            [],
        ]

        for invalid in invalid_claim_states:
            with self.subTest(invalid=invalid):
                with self.assertRaises(TypeError):
                    evaluate_reviewer_claim_eligibility(
                        invalid,  # type: ignore[arg-type]
                        valid_reviewer_identity,
                    )

    def test_evaluate_rejects_invalid_reviewer_identity(self) -> None:
        from agent_lab.reviewer_eligibility_policy import (
            evaluate_reviewer_claim_eligibility,
        )

        claim_state = HumanReviewClaimState(
            workflow_id="WF-001",
            claims=(),
        )

        invalid_reviewer_identities = [
            None,
            "SPEC-001",
            True,
            False,
            123,
            object(),
            [],
        ]

        for invalid in invalid_reviewer_identities:
            with self.subTest(invalid=invalid):
                with self.assertRaises(TypeError):
                    evaluate_reviewer_claim_eligibility(
                        claim_state,
                        invalid,  # type: ignore[arg-type]
                    )


class ReviewerEligibilityPublicExportTests(unittest.TestCase):
    def test_package_root_exports_reviewer_eligibility_symbols(self) -> None:
        from agent_lab import (
            ReviewerEligibilityDecision,
            ReviewerEligibilityStatus,
            evaluate_reviewer_claim_eligibility,
        )
        from agent_lab.reviewer_eligibility_policy import (
            ReviewerEligibilityDecision as ModuleDecision,
            ReviewerEligibilityStatus as ModuleStatus,
            evaluate_reviewer_claim_eligibility as ModuleEvaluate,
        )

        self.assertIs(
            ReviewerEligibilityDecision,
            ModuleDecision,
        )
        self.assertIs(
            ReviewerEligibilityStatus,
            ModuleStatus,
        )
        self.assertIs(
            evaluate_reviewer_claim_eligibility,
            ModuleEvaluate,
        )


if __name__ == "__main__":
    unittest.main()
