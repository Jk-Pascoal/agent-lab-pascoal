from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from agent_lab.human_review_claim import HumanReviewClaimRelease
from agent_lab.human_review_claim_release_serialization import (
    human_review_claim_release_from_record,
    human_review_claim_release_to_record,
)


class HumanReviewClaimReleasePersistenceError(Exception):
    """Base exception for all human review claim release persistence errors."""


class DuplicateHumanReviewClaimReleaseError(
    HumanReviewClaimReleasePersistenceError
):
    """Raised when attempting to append a release with an already existing release_id."""


class HumanReviewClaimReleaseCorruptionError(
    HumanReviewClaimReleasePersistenceError
):
    """Raised when encountering corrupted JSONL data or schema violations in storage."""

    def __init__(self, message: str, *, line_number: int) -> None:
        super().__init__(message)
        self.line_number = line_number


@runtime_checkable
class HumanReviewClaimReleaseRepository(Protocol):
    """Abstract protocol for append-only human review claim release persistence."""

    def append(self, release: HumanReviewClaimRelease) -> None:
        """Persist a HumanReviewClaimRelease fail-closed and durably."""
        ...

    def get_by_id(self, release_id: str) -> HumanReviewClaimRelease | None:
        """Retrieve a HumanReviewClaimRelease by exact release_id or return None."""
        ...

    def list_all(self) -> tuple[HumanReviewClaimRelease, ...]:
        """Return all persisted releases in physical append order."""
        ...


def _require_valid_id(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or isinstance(value, bool):
        raise ValueError(
            f"{field_name} must be a string, got {type(value).__name__}"
        )
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty or whitespace")
    return value


class JsonlHumanReviewClaimReleaseRepository:
    """Append-only local JSONL implementation of HumanReviewClaimReleaseRepository."""

    def __init__(self, path: Path) -> None:
        self._path = Path(path)

    @property
    def path(self) -> Path:
        return self._path

    def append(self, release: HumanReviewClaimRelease) -> None:
        """Append a release ensuring durability, full file validation, and unique release_id."""
        if not isinstance(release, HumanReviewClaimRelease) or isinstance(
            release, bool
        ):
            raise ValueError(
                "release must be a HumanReviewClaimRelease instance"
            )

        existing_releases = self.list_all()
        for existing in existing_releases:
            if existing.release_id == release.release_id:
                raise DuplicateHumanReviewClaimReleaseError(
                    f"HumanReviewClaimRelease with release_id {release.release_id!r} already exists"
                )

        record = human_review_claim_release_to_record(release)
        line = json.dumps(record)

        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._path, "a", encoding="utf-8") as file:
                file.write(f"{line}\n")
                file.flush()
                os.fsync(file.fileno())
        except OSError as exc:
            raise HumanReviewClaimReleasePersistenceError(
                f"Failed to write release to {self._path}: {exc}"
            ) from exc

    def get_by_id(self, release_id: str) -> HumanReviewClaimRelease | None:
        """Retrieve a release by its exact release_id or return None."""
        valid_id = _require_valid_id(release_id, "release_id")
        for release in self.list_all():
            if release.release_id == valid_id:
                return release
        return None

    def list_all(self) -> tuple[HumanReviewClaimRelease, ...]:
        """Return all releases in strict physical append order, fail-closed."""
        try:
            if not self._path.exists():
                return ()

            if self._path.stat().st_size == 0:
                return ()
        except OSError as exc:
            raise HumanReviewClaimReleasePersistenceError(
                f"Failed to inspect file {self._path}: {exc}"
            ) from exc

        releases: list[HumanReviewClaimRelease] = []
        seen_release_ids: set[str] = set()

        try:
            with open(self._path, "r", encoding="utf-8") as file:
                for line_number, raw_line in enumerate(file, start=1):
                    stripped = raw_line.strip()
                    if not stripped:
                        raise HumanReviewClaimReleaseCorruptionError(
                            f"Empty or whitespace line detected at line {line_number}",
                            line_number=line_number,
                        )

                    try:
                        record = json.loads(raw_line)
                    except json.JSONDecodeError as exc:
                        raise HumanReviewClaimReleaseCorruptionError(
                            f"Malformed JSON at line {line_number}: {exc}",
                            line_number=line_number,
                        ) from exc

                    if not isinstance(record, dict):
                        raise HumanReviewClaimReleaseCorruptionError(
                            f"Expected JSON object at line {line_number}, got {type(record).__name__}",
                            line_number=line_number,
                        )

                    try:
                        release = human_review_claim_release_from_record(record)
                    except ValueError as exc:
                        raise HumanReviewClaimReleaseCorruptionError(
                            f"Invalid claim release record at line {line_number}: {exc}",
                            line_number=line_number,
                        ) from exc

                    if release.release_id in seen_release_ids:
                        raise HumanReviewClaimReleaseCorruptionError(
                            f"Duplicate release_id '{release.release_id}' detected at line {line_number}",
                            line_number=line_number,
                        )
                    seen_release_ids.add(release.release_id)

                    releases.append(release)
        except OSError as exc:
            raise HumanReviewClaimReleasePersistenceError(
                f"Failed to read file {self._path}: {exc}"
            ) from exc

        return tuple(releases)
