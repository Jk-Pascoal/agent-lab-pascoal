from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum

from agent_lab.human_review_claim import HumanReviewClaim, HumanReviewClaimRelease


class HumanReviewClaimFactState(str, Enum):
    NO_CLAIM = "NO_CLAIM"
    SINGLE_CLAIM = "SINGLE_CLAIM"
    MULTIPLE_CLAIMS = "MULTIPLE_CLAIMS"


@dataclass(frozen=True, slots=True)
class HumanReviewClaimState:
    workflow_id: str
    claims: tuple[HumanReviewClaim, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.workflow_id, str) or isinstance(self.workflow_id, bool):
            raise TypeError("workflow_id must be a string")
        sanitized_wf = self.workflow_id.strip()
        if not sanitized_wf:
            raise ValueError("workflow_id must not be empty or whitespace")
        if self.workflow_id != sanitized_wf:
            object.__setattr__(self, "workflow_id", sanitized_wf)

        if not isinstance(self.claims, tuple):
            raise TypeError("claims must be a tuple")

        for idx, claim in enumerate(self.claims):
            if not isinstance(claim, HumanReviewClaim) or isinstance(claim, bool):
                raise TypeError(
                    f"claim at index {idx} must be a HumanReviewClaim instance"
                )
            if claim.workflow_id != sanitized_wf:
                raise ValueError(
                    f"claim at index {idx} has workflow_id {claim.workflow_id!r}, "
                    f"expected {sanitized_wf!r}"
                )

    @property
    def claim_count(self) -> int:
        return len(self.claims)

    @property
    def state(self) -> HumanReviewClaimFactState:
        if self.claim_count == 0:
            return HumanReviewClaimFactState.NO_CLAIM
        if self.claim_count == 1:
            return HumanReviewClaimFactState.SINGLE_CLAIM
        return HumanReviewClaimFactState.MULTIPLE_CLAIMS

    @property
    def is_unclaimed(self) -> bool:
        return self.state is HumanReviewClaimFactState.NO_CLAIM

    @property
    def has_claims(self) -> bool:
        return self.claim_count > 0

    @property
    def has_multiple_claims(self) -> bool:
        return self.state is HumanReviewClaimFactState.MULTIPLE_CLAIMS

    @property
    def sole_claim(self) -> HumanReviewClaim | None:
        if self.state is HumanReviewClaimFactState.SINGLE_CLAIM:
            return self.claims[0]
        return None


def project_human_review_claim_state(
    workflow_id: str,
    claims: Sequence[HumanReviewClaim],
) -> HumanReviewClaimState:
    if not isinstance(workflow_id, str) or isinstance(workflow_id, bool):
        raise TypeError("workflow_id must be a string")
    sanitized_wf = workflow_id.strip()
    if not sanitized_wf:
        raise ValueError("workflow_id must not be empty or whitespace")

    if not isinstance(claims, Sequence) or isinstance(claims, (str, bytes, bytearray)):
        raise TypeError("claims must be a Sequence of HumanReviewClaim")

    for idx, claim in enumerate(claims):
        if not isinstance(claim, HumanReviewClaim) or isinstance(claim, bool):
            raise TypeError(
                f"claim at index {idx} must be a HumanReviewClaim instance, "
                f"got {type(claim).__name__}"
            )

    filtered = [c for c in claims if c.workflow_id == sanitized_wf]
    sorted_claims = sorted(
        filtered,
        key=lambda claim: (claim.claimed_at, claim.claim_id),
    )
    return HumanReviewClaimState(workflow_id=sanitized_wf, claims=tuple(sorted_claims))


@dataclass(frozen=True, slots=True)
class ReleaseAwareClaimState:
    workflow_id: str
    all_claims: tuple[HumanReviewClaim, ...]
    releases: tuple[HumanReviewClaimRelease, ...]
    unreleased_claims: tuple[HumanReviewClaim, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.workflow_id, str) or isinstance(self.workflow_id, bool):
            raise TypeError("workflow_id must be a string")
        sanitized_wf = self.workflow_id.strip()
        if not sanitized_wf:
            raise ValueError("workflow_id must not be empty or whitespace")
        if self.workflow_id != sanitized_wf:
            object.__setattr__(self, "workflow_id", sanitized_wf)

        if not isinstance(self.all_claims, tuple):
            raise TypeError("all_claims must be a tuple")
        if not isinstance(self.releases, tuple):
            raise TypeError("releases must be a tuple")
        if not isinstance(self.unreleased_claims, tuple):
            raise TypeError("unreleased_claims must be a tuple")

        for idx, claim in enumerate(self.all_claims):
            if not isinstance(claim, HumanReviewClaim) or isinstance(claim, bool):
                raise TypeError(
                    f"claim at index {idx} in all_claims must be a HumanReviewClaim instance"
                )
            if claim.workflow_id != sanitized_wf:
                raise ValueError(
                    f"claim at index {idx} in all_claims has workflow_id {claim.workflow_id!r}, "
                    f"expected {sanitized_wf!r}"
                )

        for idx, release in enumerate(self.releases):
            if not isinstance(release, HumanReviewClaimRelease) or isinstance(release, bool):
                raise TypeError(
                    f"release at index {idx} in releases must be a HumanReviewClaimRelease instance"
                )
            if release.workflow_id != sanitized_wf:
                raise ValueError(
                    f"release at index {idx} in releases has workflow_id {release.workflow_id!r}, "
                    f"expected {sanitized_wf!r}"
                )

        for idx, claim in enumerate(self.unreleased_claims):
            if not isinstance(claim, HumanReviewClaim) or isinstance(claim, bool):
                raise TypeError(
                    f"claim at index {idx} in unreleased_claims must be a HumanReviewClaim instance"
                )
            if claim.workflow_id != sanitized_wf:
                raise ValueError(
                    f"claim at index {idx} in unreleased_claims has workflow_id {claim.workflow_id!r}, "
                    f"expected {sanitized_wf!r}"
                )

    @property
    def all_claims_count(self) -> int:
        return len(self.all_claims)

    @property
    def releases_count(self) -> int:
        return len(self.releases)

    @property
    def unreleased_claim_count(self) -> int:
        return len(self.unreleased_claims)

    @property
    def unreleased_claim_state(self) -> HumanReviewClaimFactState:
        if self.unreleased_claim_count == 0:
            return HumanReviewClaimFactState.NO_CLAIM
        if self.unreleased_claim_count == 1:
            return HumanReviewClaimFactState.SINGLE_CLAIM
        return HumanReviewClaimFactState.MULTIPLE_CLAIMS

    @property
    def sole_unreleased_claim(self) -> HumanReviewClaim | None:
        if self.unreleased_claim_state is HumanReviewClaimFactState.SINGLE_CLAIM:
            return self.unreleased_claims[0]
        return None

    @property
    def has_unreleased_claims(self) -> bool:
        return self.unreleased_claim_count > 0

    @property
    def has_no_unreleased_claims(self) -> bool:
        return self.unreleased_claim_count == 0

    @property
    def has_multiple_unreleased_claims(self) -> bool:
        return self.unreleased_claim_state is HumanReviewClaimFactState.MULTIPLE_CLAIMS


def project_release_aware_claim_state(
    workflow_id: str,
    claims: Sequence[HumanReviewClaim],
    releases: Sequence[HumanReviewClaimRelease],
) -> ReleaseAwareClaimState:
    if not isinstance(workflow_id, str) or isinstance(workflow_id, bool):
        raise TypeError("workflow_id must be a string")
    sanitized_wf = workflow_id.strip()
    if not sanitized_wf:
        raise ValueError("workflow_id must not be empty or whitespace")

    if not isinstance(claims, Sequence) or isinstance(claims, (str, bytes, bytearray)):
        raise TypeError("claims must be a Sequence of HumanReviewClaim")

    if not isinstance(releases, Sequence) or isinstance(releases, (str, bytes, bytearray)):
        raise TypeError("releases must be a Sequence of HumanReviewClaimRelease")

    for idx, claim in enumerate(claims):
        if not isinstance(claim, HumanReviewClaim) or isinstance(claim, bool):
            raise TypeError(
                f"claim at index {idx} must be a HumanReviewClaim instance, "
                f"got {type(claim).__name__}"
            )

    for idx, release in enumerate(releases):
        if not isinstance(release, HumanReviewClaimRelease) or isinstance(release, bool):
            raise TypeError(
                f"release at index {idx} must be a HumanReviewClaimRelease instance, "
                f"got {type(release).__name__}"
            )

    filtered_claims = [c for c in claims if c.workflow_id == sanitized_wf]
    sorted_claims = sorted(
        filtered_claims,
        key=lambda claim: (claim.claimed_at, claim.claim_id),
    )

    filtered_releases = [r for r in releases if r.workflow_id == sanitized_wf]
    sorted_releases = sorted(
        filtered_releases,
        key=lambda release: (release.released_at, release.release_id),
    )

    claims_by_id = {c.claim_id: c for c in sorted_claims}
    for release in sorted_releases:
        claim = claims_by_id.get(release.claim_id)
        if claim is None:
            raise ValueError(
                f"Orphan release '{release.release_id}' references unknown claim_id "
                f"'{release.claim_id}' for workflow '{sanitized_wf}'"
            )
        if release.released_at < claim.claimed_at:
            raise ValueError(
                f"Release '{release.release_id}' released_at ({release.released_at}) "
                f"cannot be before claim claimed_at ({claim.claimed_at})"
            )

    released_claim_ids = {r.claim_id for r in sorted_releases}
    unreleased = [c for c in sorted_claims if c.claim_id not in released_claim_ids]

    return ReleaseAwareClaimState(
        workflow_id=sanitized_wf,
        all_claims=tuple(sorted_claims),
        releases=tuple(sorted_releases),
        unreleased_claims=tuple(unreleased),
    )
