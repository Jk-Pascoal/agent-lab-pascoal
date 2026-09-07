from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from agent_lab.human_review import VerifiedSpecialistIdentity
from agent_lab.workflow import GovernanceWorkflow, WorkflowStatus


@dataclass(frozen=True, slots=True)
class HumanReviewClaim:
    claim_id: str
    workflow_id: str
    specialist: VerifiedSpecialistIdentity
    claimed_at: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.claim_id, str):
            raise TypeError("claim_id must be a string")

        if not self.claim_id.strip():
            raise ValueError("claim_id must not be empty")

        if not isinstance(self.workflow_id, str):
            raise TypeError("workflow_id must be a string")

        if not self.workflow_id.strip():
            raise ValueError("workflow_id must not be empty")

        if not isinstance(self.specialist, VerifiedSpecialistIdentity):
            raise TypeError("specialist must be a VerifiedSpecialistIdentity")

        if not isinstance(self.claimed_at, datetime):
            raise TypeError("claimed_at must be a datetime")

        if self.claimed_at.tzinfo is None or self.claimed_at.utcoffset() is None:
            raise ValueError("claimed_at must be timezone-aware")

        if self.specialist.verified_at > self.claimed_at:
            raise ValueError(
                "specialist verification must not be after claimed_at"
            )


@dataclass(frozen=True, slots=True)
class HumanReviewClaimRelease:
    release_id: str
    claim_id: str
    workflow_id: str
    released_by: VerifiedSpecialistIdentity
    released_at: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.release_id, str):
            raise TypeError("release_id must be a string")

        sanitized_release_id = self.release_id.strip()
        if not sanitized_release_id:
            raise ValueError("release_id must not be empty")

        if self.release_id != sanitized_release_id:
            object.__setattr__(self, "release_id", sanitized_release_id)

        if not isinstance(self.claim_id, str):
            raise TypeError("claim_id must be a string")

        if not self.claim_id.strip():
            raise ValueError("claim_id must not be empty")

        if not isinstance(self.workflow_id, str):
            raise TypeError("workflow_id must be a string")

        if not self.workflow_id.strip():
            raise ValueError("workflow_id must not be empty")

        if not isinstance(self.released_by, VerifiedSpecialistIdentity):
            raise TypeError("released_by must be a VerifiedSpecialistIdentity")

        if not isinstance(self.released_at, datetime):
            raise TypeError("released_at must be a datetime")

        if self.released_at.tzinfo is None or self.released_at.utcoffset() is None:
            raise ValueError("released_at must be timezone-aware")

        if self.released_by.verified_at > self.released_at:
            raise ValueError(
                "released_by verification must not be after released_at"
            )


def claim_pending_human_review(
    workflow: GovernanceWorkflow,
    *,
    claim_id: str,
    specialist: VerifiedSpecialistIdentity,
    claimed_at: datetime,
) -> HumanReviewClaim:
    if not isinstance(workflow, GovernanceWorkflow):
        raise TypeError("workflow must be a GovernanceWorkflow")

    if workflow.status is not WorkflowStatus.PENDING_HUMAN_REVIEW:
        raise ValueError("workflow must be pending human review")

    if claimed_at < workflow.opened_at:
        raise ValueError(
            "claimed_at must not be before workflow opened_at"
        )

    return HumanReviewClaim(
        claim_id=claim_id,
        workflow_id=workflow.workflow_id,
        specialist=specialist,
        claimed_at=claimed_at,
    )


def release_human_review_claim(
    workflow: GovernanceWorkflow,
    claim: HumanReviewClaim,
    *,
    release_id: str,
    releasing_specialist: VerifiedSpecialistIdentity,
    released_at: datetime,
) -> HumanReviewClaimRelease:
    if not isinstance(workflow, GovernanceWorkflow):
        raise TypeError("workflow must be a GovernanceWorkflow")

    if not isinstance(claim, HumanReviewClaim):
        raise TypeError("claim must be a HumanReviewClaim")

    if not isinstance(releasing_specialist, VerifiedSpecialistIdentity):
        raise TypeError(
            "releasing_specialist must be a VerifiedSpecialistIdentity"
        )

    if not isinstance(released_at, datetime):
        raise TypeError("released_at must be a datetime")

    if released_at.tzinfo is None or released_at.utcoffset() is None:
        raise ValueError("released_at must be timezone-aware")

    if workflow.workflow_id != claim.workflow_id:
        raise ValueError("workflow_id mismatch between workflow and claim")

    if workflow.status is not WorkflowStatus.PENDING_HUMAN_REVIEW:
        raise ValueError("workflow must be pending human review to release claim")

    is_same_principal = (
        releasing_specialist.specialist_id == claim.specialist.specialist_id
        and releasing_specialist.identity_provider
        == claim.specialist.identity_provider
        and releasing_specialist.identity_subject
        == claim.specialist.identity_subject
    )

    if not is_same_principal:
        raise ValueError(
            "releasing specialist stable principal must match claimant stable principal"
        )

    if released_at < claim.claimed_at:
        raise ValueError("released_at must not be before claim claimed_at")

    return HumanReviewClaimRelease(
        release_id=release_id,
        claim_id=claim.claim_id,
        workflow_id=claim.workflow_id,
        released_by=releasing_specialist,
        released_at=released_at,
    )
