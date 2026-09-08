import copy
from datetime import datetime, timedelta, timezone
import unittest

from agent_lab.human_review import VerifiedSpecialistIdentity
from agent_lab.human_review_claim import HumanReviewClaimRelease
from agent_lab.human_review_claim_release_serialization import (
    SCHEMA_VERSION_V1,
    human_review_claim_release_from_record,
    human_review_claim_release_to_record,
)


class HumanReviewClaimReleaseSerializationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.verified_at = datetime(
            2026,
            9,
            8,
            10,
            0,
            0,
            tzinfo=timezone.utc,
        )
        self.released_at = datetime(
            2026,
            9,
            8,
            10,
            5,
            0,
            tzinfo=timezone.utc,
        )
        self.released_by = VerifiedSpecialistIdentity(
            specialist_id="SPEC-001",
            identity_provider="CORPORATE_IDP",
            identity_subject="user-12345",
            verification_id="VER-001",
            verified_at=self.verified_at,
        )
        self.release = HumanReviewClaimRelease(
            release_id="REL-001",
            claim_id="CLM-001",
            workflow_id="WF-001",
            released_by=self.released_by,
            released_at=self.released_at,
        )
        self.expected_canonical_record: dict[str, object] = {
            "schema_version": 1,
            "release_id": "REL-001",
            "claim_id": "CLM-001",
            "workflow_id": "WF-001",
            "released_by": {
                "specialist_id": "SPEC-001",
                "identity_provider": "CORPORATE_IDP",
                "identity_subject": "user-12345",
                "verification_id": "VER-001",
                "verified_at": "2026-09-08T10:00:00+00:00",
            },
            "released_at": "2026-09-08T10:05:00+00:00",
        }

    def test_schema_version_constant_is_one(self) -> None:
        self.assertEqual(SCHEMA_VERSION_V1, 1)
        self.assertIs(type(SCHEMA_VERSION_V1), int)

    def test_round_trip_preserves_contractual_values_and_schema_version(
        self,
    ) -> None:
        record = human_review_claim_release_to_record(self.release)

        self.assertIsInstance(record, dict)
        self.assertIs(type(record["schema_version"]), int)
        self.assertEqual(record["schema_version"], 1)
        self.assertEqual(record["schema_version"], SCHEMA_VERSION_V1)
        self.assertEqual(record["release_id"], "REL-001")
        self.assertEqual(record["claim_id"], "CLM-001")
        self.assertEqual(record["workflow_id"], "WF-001")
        self.assertEqual(record, self.expected_canonical_record)

        reconstituted = human_review_claim_release_from_record(record)

        self.assertIsInstance(reconstituted, HumanReviewClaimRelease)
        self.assertEqual(reconstituted.release_id, self.release.release_id)
        self.assertEqual(reconstituted.claim_id, self.release.claim_id)
        self.assertEqual(reconstituted.workflow_id, self.release.workflow_id)
        self.assertEqual(reconstituted.released_by, self.release.released_by)
        self.assertEqual(reconstituted.released_at, self.release.released_at)
        self.assertEqual(reconstituted, self.release)

    def test_from_record_reads_canonical_serialized_payload(self) -> None:
        reconstituted = human_review_claim_release_from_record(
            self.expected_canonical_record
        )
        self.assertEqual(reconstituted, self.release)

    def test_to_record_rejects_non_human_review_claim_release_instances(
        self,
    ) -> None:
        invalid_instances = (
            None,
            "not-a-release",
            123,
            True,
            False,
            object(),
            self.released_by,
        )
        for invalid in invalid_instances:
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    human_review_claim_release_to_record(
                        invalid  # type: ignore[arg-type]
                    )

    def test_from_record_rejects_non_mapping_payload(self) -> None:
        invalid_payloads = (
            None,
            "payload",
            123,
            True,
            False,
            [1, 2],
            (1, 2),
            object(),
        )
        for invalid in invalid_payloads:
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    human_review_claim_release_from_record(
                        invalid  # type: ignore[arg-type]
                    )

    def test_from_record_rejects_invalid_or_missing_schema_version(
        self,
    ) -> None:
        invalid_versions = (
            True,
            False,
            1.0,
            "1",
            None,
            0,
            2,
            -1,
            999,
        )
        for val in invalid_versions:
            with self.subTest(version=val):
                payload = copy.deepcopy(self.expected_canonical_record)
                payload["schema_version"] = val
                with self.assertRaises(ValueError) as ctx:
                    human_review_claim_release_from_record(payload)
                self.assertIn("schema_version", str(ctx.exception))

        # Test missing schema_version
        payload = copy.deepcopy(self.expected_canonical_record)
        del payload["schema_version"]
        with self.assertRaises(ValueError) as ctx:
            human_review_claim_release_from_record(payload)
        self.assertIn("schema_version", str(ctx.exception))

    def test_from_record_rejects_missing_root_fields(self) -> None:
        fields = (
            "schema_version",
            "release_id",
            "claim_id",
            "workflow_id",
            "released_by",
            "released_at",
        )
        for field_name in fields:
            with self.subTest(missing_field=field_name):
                payload = copy.deepcopy(self.expected_canonical_record)
                del payload[field_name]
                with self.assertRaises(ValueError) as ctx:
                    human_review_claim_release_from_record(payload)
                self.assertIn("Missing required field(s)", str(ctx.exception))
                self.assertIn(field_name, str(ctx.exception))

    def test_from_record_rejects_unknown_root_fields(self) -> None:
        payload = copy.deepcopy(self.expected_canonical_record)
        payload["extra_root_field"] = "unexpected"
        with self.assertRaises(ValueError) as ctx:
            human_review_claim_release_from_record(payload)
        self.assertIn("Unknown field(s) detected", str(ctx.exception))
        self.assertIn("extra_root_field", str(ctx.exception))

    def test_from_record_rejects_mixed_type_unknown_root_fields_without_type_error(
        self,
    ) -> None:
        payload = copy.deepcopy(self.expected_canonical_record)
        payload[123] = "numeric-key"
        payload["alpha_key"] = "alpha-val"
        with self.assertRaises(ValueError) as ctx:
            human_review_claim_release_from_record(payload)
        self.assertIn("Unknown field(s) detected", str(ctx.exception))

    def test_from_record_rejects_missing_released_by_fields(self) -> None:
        fields = (
            "specialist_id",
            "identity_provider",
            "identity_subject",
            "verification_id",
            "verified_at",
        )
        for field_name in fields:
            with self.subTest(missing_field=field_name):
                payload = copy.deepcopy(self.expected_canonical_record)
                rel_by = dict(payload["released_by"])  # type: ignore[arg-type]
                del rel_by[field_name]
                payload["released_by"] = rel_by
                with self.assertRaises(ValueError) as ctx:
                    human_review_claim_release_from_record(payload)
                self.assertIn("Missing required specialist field(s)", str(ctx.exception))
                self.assertIn(field_name, str(ctx.exception))

    def test_from_record_rejects_unknown_released_by_fields(self) -> None:
        payload = copy.deepcopy(self.expected_canonical_record)
        rel_by = dict(payload["released_by"])  # type: ignore[arg-type]
        rel_by["extra_specialist_field"] = "unexpected"
        payload["released_by"] = rel_by
        with self.assertRaises(ValueError) as ctx:
            human_review_claim_release_from_record(payload)
        self.assertIn("Unknown specialist field(s) detected", str(ctx.exception))
        self.assertIn("extra_specialist_field", str(ctx.exception))

    def test_from_record_rejects_mixed_type_unknown_released_by_fields_without_type_error(
        self,
    ) -> None:
        payload = copy.deepcopy(self.expected_canonical_record)
        rel_by = dict(payload["released_by"])  # type: ignore[arg-type]
        rel_by[999] = "numeric-spec-key"
        rel_by["alpha_spec_key"] = "alpha-spec-val"
        payload["released_by"] = rel_by
        with self.assertRaises(ValueError) as ctx:
            human_review_claim_release_from_record(payload)
        self.assertIn("Unknown specialist field(s) detected", str(ctx.exception))

    def test_from_record_rejects_non_mapping_released_by(self) -> None:
        invalid_specialists = (
            None,
            "not-a-map",
            123,
            True,
            False,
            [1, 2],
            (1, 2),
            object(),
        )
        for invalid in invalid_specialists:
            with self.subTest(released_by=invalid):
                payload = copy.deepcopy(self.expected_canonical_record)
                payload["released_by"] = invalid
                with self.assertRaises(ValueError):
                    human_review_claim_release_from_record(payload)

    def test_from_record_rejects_empty_whitespace_or_invalid_type_strings(
        self,
    ) -> None:
        invalid_values = ("", "   ", "\t\n", None, 123, True, False, object(), ["a"])

        root_str_fields = ("release_id", "claim_id", "workflow_id")
        for field_name in root_str_fields:
            for invalid in invalid_values:
                with self.subTest(field=field_name, value=invalid):
                    payload = copy.deepcopy(self.expected_canonical_record)
                    payload[field_name] = invalid
                    with self.assertRaises(ValueError):
                        human_review_claim_release_from_record(payload)

        spec_str_fields = (
            "specialist_id",
            "identity_provider",
            "identity_subject",
            "verification_id",
        )
        for field_name in spec_str_fields:
            for invalid in invalid_values:
                with self.subTest(specialist_field=field_name, value=invalid):
                    payload = copy.deepcopy(self.expected_canonical_record)
                    rel_by = dict(payload["released_by"])  # type: ignore[arg-type]
                    rel_by[field_name] = invalid
                    payload["released_by"] = rel_by
                    with self.assertRaises(ValueError):
                        human_review_claim_release_from_record(payload)

    def test_from_record_rejects_invalid_timestamps(self) -> None:
        invalid_datetimes = (
            "",
            "   ",
            "not-a-date",
            "2026/09/08 10:00:00",
            123,
            True,
            False,
            None,
            [2026, 9, 8],
        )
        for invalid in invalid_datetimes:
            with self.subTest(released_at=invalid):
                payload = copy.deepcopy(self.expected_canonical_record)
                payload["released_at"] = invalid
                with self.assertRaises(ValueError):
                    human_review_claim_release_from_record(payload)

            with self.subTest(verified_at=invalid):
                payload = copy.deepcopy(self.expected_canonical_record)
                rel_by = dict(payload["released_by"])  # type: ignore[arg-type]
                rel_by["verified_at"] = invalid
                payload["released_by"] = rel_by
                with self.assertRaises(ValueError):
                    human_review_claim_release_from_record(payload)

    def test_from_record_rejects_naive_timestamps(self) -> None:
        naive_str = "2026-09-08T10:05:00"
        payload = copy.deepcopy(self.expected_canonical_record)
        payload["released_at"] = naive_str
        with self.assertRaises(ValueError) as ctx:
            human_review_claim_release_from_record(payload)
        self.assertIn("timezone-aware", str(ctx.exception))

        payload = copy.deepcopy(self.expected_canonical_record)
        rel_by = dict(payload["released_by"])  # type: ignore[arg-type]
        rel_by["verified_at"] = naive_str
        payload["released_by"] = rel_by
        with self.assertRaises(ValueError) as ctx:
            human_review_claim_release_from_record(payload)
        self.assertIn("timezone-aware", str(ctx.exception))

    def test_from_record_rejects_verified_at_after_released_at(self) -> None:
        payload = copy.deepcopy(self.expected_canonical_record)
        rel_by = dict(payload["released_by"])  # type: ignore[arg-type]
        rel_by["verified_at"] = "2026-09-08T10:10:00+00:00"
        payload["released_by"] = rel_by
        payload["released_at"] = "2026-09-08T10:05:00+00:00"

        with self.assertRaises(ValueError) as ctx:
            human_review_claim_release_from_record(payload)
        self.assertIn("released_by verification must not be after released_at", str(ctx.exception))

    def test_from_record_allows_verified_at_equal_to_released_at(self) -> None:
        same_timestamp = "2026-09-08T10:05:00+00:00"
        payload = copy.deepcopy(self.expected_canonical_record)
        rel_by = dict(payload["released_by"])  # type: ignore[arg-type]
        rel_by["verified_at"] = same_timestamp
        payload["released_by"] = rel_by
        payload["released_at"] = same_timestamp

        reconstituted = human_review_claim_release_from_record(payload)
        self.assertEqual(reconstituted.released_by.verified_at, reconstituted.released_at)

    def test_preserves_claim_id_and_workflow_id_exact_identity_with_outer_spaces(
        self,
    ) -> None:
        release_with_spaces = HumanReviewClaimRelease(
            release_id="  REL-SPACES-001  ",
            claim_id="  CLM-EXACT-001  ",
            workflow_id="  WF-EXACT-001  ",
            released_by=self.released_by,
            released_at=self.released_at,
        )

        record = human_review_claim_release_to_record(release_with_spaces)

        # release_id was sanitized by HumanReviewClaimRelease.__post_init__
        self.assertEqual(record["release_id"], "REL-SPACES-001")
        # claim_id and workflow_id preserved exact identity without strip
        self.assertEqual(record["claim_id"], "  CLM-EXACT-001  ")
        self.assertEqual(record["workflow_id"], "  WF-EXACT-001  ")

        reconstituted = human_review_claim_release_from_record(record)
        self.assertEqual(reconstituted.release_id, "REL-SPACES-001")
        self.assertEqual(reconstituted.claim_id, "  CLM-EXACT-001  ")
        self.assertEqual(reconstituted.workflow_id, "  WF-EXACT-001  ")
        self.assertEqual(reconstituted, release_with_spaces)

    def test_round_trip_preserves_non_utc_timezone_offset_and_microseconds(
        self,
    ) -> None:
        tz_sp = timezone(timedelta(hours=-3))
        dt_verified = datetime(2026, 9, 8, 7, 0, 0, 123456, tzinfo=tz_sp)
        dt_released = datetime(2026, 9, 8, 7, 5, 0, 654321, tzinfo=tz_sp)

        specialist = VerifiedSpecialistIdentity(
            specialist_id="SPEC-BR",
            identity_provider="CORP_IDP",
            identity_subject="user-sp",
            verification_id="VER-SP",
            verified_at=dt_verified,
        )
        release = HumanReviewClaimRelease(
            release_id="REL-SP-001",
            claim_id="CLM-SP-001",
            workflow_id="WF-SP-001",
            released_by=specialist,
            released_at=dt_released,
        )

        record = human_review_claim_release_to_record(release)

        # Verify serialized representation preserves offset (-03:00) and microseconds
        self.assertEqual(record["released_at"], dt_released.isoformat())
        self.assertIn("-03:00", str(record["released_at"]))
        self.assertIn("654321", str(record["released_at"]))

        rel_by_record = record["released_by"]
        self.assertIsInstance(rel_by_record, dict)
        self.assertEqual(rel_by_record["verified_at"], dt_verified.isoformat())
        self.assertIn("-03:00", str(rel_by_record["verified_at"]))
        self.assertIn("123456", str(rel_by_record["verified_at"]))

        reconstituted = human_review_claim_release_from_record(record)
        self.assertEqual(reconstituted, release)
        self.assertEqual(reconstituted.released_at.utcoffset(), dt_released.utcoffset())
        self.assertEqual(reconstituted.released_at.microsecond, 654321)
        self.assertEqual(reconstituted.released_by.verified_at.microsecond, 123456)

    def test_from_record_does_not_mutate_input_mapping(self) -> None:
        payload = copy.deepcopy(self.expected_canonical_record)
        frozen_copy = copy.deepcopy(payload)

        human_review_claim_release_from_record(payload)

        self.assertEqual(payload, frozen_copy)


if __name__ == "__main__":
    unittest.main()
