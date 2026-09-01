from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from agent_lab.human_review_claim import HumanReviewClaim
from agent_lab.human_review_claim_serialization import (
    human_review_claim_from_record,
    human_review_claim_to_record,
)


class HumanReviewClaimPersistenceError(Exception):
    """Base exception for all human review claim persistence errors."""


class DuplicateHumanReviewClaimError(HumanReviewClaimPersistenceError):
    """Raised when attempting to append a claim with an already existing claim_id."""


class HumanReviewClaimCorruptionError(HumanReviewClaimPersistenceError):
    """Raised when encountering corrupted JSONL data or schema violations."""

    def __init__(self, message: str, *, line_number: int) -> None:
        super().__init__(message)
        self.line_number = line_number


@runtime_checkable
class HumanReviewClaimRepository(Protocol):
    """Abstract protocol for append-only human review claim persistence."""

    def append(self, claim: HumanReviewClaim) -> None:
        """Append a HumanReviewClaim to the repository fail-closed."""
        ...

    def get_by_id(self, claim_id: str) -> HumanReviewClaim | None:
        """Retrieve a HumanReviewClaim by exact claim_id or return None."""
        ...

    def list_by_workflow_id(
        self, workflow_id: str
    ) -> tuple[HumanReviewClaim, ...]:
        """Return all persisted claims for a given workflow_id in physical append order."""
        ...

    def list_all(self) -> tuple[HumanReviewClaim, ...]:
        """Return all persisted claims in physical append order."""
        ...


def _require_valid_id(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or isinstance(value, bool):
        raise ValueError(
            f"{field_name} must be a string, got {type(value).__name__}"
        )
    trimmed = value.strip()
    if not trimmed:
        raise ValueError(f"{field_name} must not be empty or whitespace")
    return trimmed


class JsonlHumanReviewClaimRepository:
    """Append-only local JSONL implementation of HumanReviewClaimRepository."""

    def __init__(self, path: Path) -> None:
        self._path = Path(path)

    @property
    def path(self) -> Path:
        return self._path

    def append(self, claim: HumanReviewClaim) -> None:
        """Append a claim to the JSONL repository ensuring durability and unique claim_id."""
        if not isinstance(claim, HumanReviewClaim) or isinstance(claim, bool):
            raise ValueError("claim must be a HumanReviewClaim instance")

        existing_claims = self.list_all()
        for existing in existing_claims:
            if existing.claim_id == claim.claim_id:
                raise DuplicateHumanReviewClaimError(
                    f"HumanReviewClaim with claim_id {claim.claim_id!r} already exists"
                )

        self._path.parent.mkdir(parents=True, exist_ok=True)
        record = human_review_claim_to_record(claim)
        line = json.dumps(record)

        with open(self._path, "a", encoding="utf-8") as file:
            file.write(f"{line}\n")
            file.flush()
            os.fsync(file.fileno())

    def get_by_id(self, claim_id: str) -> HumanReviewClaim | None:
        """Retrieve a claim by its exact claim_id or return None."""
        valid_id = _require_valid_id(claim_id, "claim_id")
        for claim in self.list_all():
            if claim.claim_id == valid_id:
                return claim
        return None

    def list_by_workflow_id(
        self, workflow_id: str
    ) -> tuple[HumanReviewClaim, ...]:
        """Return all persisted claims for a given workflow_id in physical append order."""
        valid_workflow_id = _require_valid_id(workflow_id, "workflow_id")
        return tuple(
            claim
            for claim in self.list_all()
            if claim.workflow_id == valid_workflow_id
        )

    def list_all(self) -> tuple[HumanReviewClaim, ...]:
        """Return all claims in strict physical append order, fail-closed."""
        if not self._path.exists():
            return ()

        if self._path.stat().st_size == 0:
            return ()

        claims: list[HumanReviewClaim] = []
        with open(self._path, "r", encoding="utf-8") as file:
            for line_number, raw_line in enumerate(file, start=1):
                stripped = raw_line.strip()
                if not stripped:
                    raise HumanReviewClaimCorruptionError(
                        f"Empty or whitespace line detected at line {line_number}",
                        line_number=line_number,
                    )

                try:
                    record = json.loads(raw_line)
                except json.JSONDecodeError as exc:
                    raise HumanReviewClaimCorruptionError(
                        f"Malformed JSON at line {line_number}: {exc}",
                        line_number=line_number,
                    ) from exc

                if not isinstance(record, dict):
                    raise HumanReviewClaimCorruptionError(
                        f"Expected JSON object at line {line_number}, got {type(record).__name__}",
                        line_number=line_number,
                    )

                try:
                    claim = human_review_claim_from_record(record)
                except ValueError as exc:
                    raise HumanReviewClaimCorruptionError(
                        f"Invalid claim record at line {line_number}: {exc}",
                        line_number=line_number,
                    ) from exc

                claims.append(claim)

        return tuple(claims)
