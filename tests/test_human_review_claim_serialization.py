from datetime import datetime, timedelta, timezone
import unittest

from agent_lab.human_review import VerifiedSpecialistIdentity
from agent_lab.human_review_claim import HumanReviewClaim
from agent_lab.human_review_claim_serialization import (
    SCHEMA_VERSION_V1,
    human_review_claim_from_record,
    human_review_claim_to_record,
)


class HumanReviewClaimSerializationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.verified_at = datetime(
            2026,
            8,
            31,
            10,
            0,
            0,
            tzinfo=timezone.utc,
        )
        self.claimed_at = datetime(
            2026,
            8,
            31,
            10,
            5,
            0,
            tzinfo=timezone.utc,
        )
        self.specialist = VerifiedSpecialistIdentity(
            specialist_id="SPEC-001",
            identity_provider="CORPORATE_IDP",
            identity_subject="user-12345",
            verification_id="VER-001",
            verified_at=self.verified_at,
        )
        self.claim = HumanReviewClaim(
            claim_id="CLM-001",
            workflow_id="WF-001",
            specialist=self.specialist,
            claimed_at=self.claimed_at,
        )
        self.canonical_payload: dict[str, object] = {
            "schema_version": 1,
            "claim_id": "CLM-001",
            "workflow_id": "WF-001",
            "specialist": {
                "specialist_id": "SPEC-001",
                "identity_provider": "CORPORATE_IDP",
                "identity_subject": "user-12345",
                "verification_id": "VER-001",
                "verified_at": "2026-08-31T10:00:00+00:00",
            },
            "claimed_at": "2026-08-31T10:05:00+00:00",
        }

    def test_schema_version_constant_is_one(self) -> None:
        self.assertEqual(SCHEMA_VERSION_V1, 1)

    def test_to_record_produces_canonical_versioned_dictionary(self) -> None:
        record = human_review_claim_to_record(self.claim)
        self.assertEqual(record, self.canonical_payload)

    def test_to_record_rejects_non_human_review_claim_instance(self) -> None:
        invalid_inputs = [None, {}, "claim", 123, self.specialist]
        for invalid_input in invalid_inputs:
            with self.subTest(invalid_input=invalid_input):
                with self.assertRaises(ValueError):
                    human_review_claim_to_record(invalid_input)  # type: ignore[arg-type]

    def test_round_trip_preserves_valid_claim(self) -> None:
        record = human_review_claim_to_record(self.claim)
        reconstituted = human_review_claim_from_record(record)
        self.assertEqual(reconstituted, self.claim)
        self.assertEqual(reconstituted.claim_id, "CLM-001")
        self.assertEqual(reconstituted.workflow_id, "WF-001")
        self.assertEqual(reconstituted.specialist, self.specialist)
        self.assertEqual(reconstituted.claimed_at, self.claimed_at)

    def test_round_trip_with_non_utc_timezone(self) -> None:
        tz_brt = timezone(timedelta(hours=-3))
        verified_at_brt = datetime(2026, 8, 31, 7, 0, 0, tzinfo=tz_brt)
        claimed_at_brt = datetime(2026, 8, 31, 7, 5, 0, tzinfo=tz_brt)

        specialist_brt = VerifiedSpecialistIdentity(
            specialist_id="SPEC-BRT",
            identity_provider="CORP-IDP-BR",
            identity_subject="user-br-789",
            verification_id="VER-BR-001",
            verified_at=verified_at_brt,
        )
        claim_brt = HumanReviewClaim(
            claim_id="CLM-BRT-001",
            workflow_id="WF-BRT-001",
            specialist=specialist_brt,
            claimed_at=claimed_at_brt,
        )

        record = human_review_claim_to_record(claim_brt)
        self.assertEqual(record["claimed_at"], "2026-08-31T07:05:00-03:00")
        self.assertEqual(
            record["specialist"]["verified_at"],  # type: ignore[index]
            "2026-08-31T07:00:00-03:00",
        )

        reconstituted = human_review_claim_from_record(record)
        self.assertEqual(reconstituted, claim_brt)
        self.assertEqual(
            reconstituted.claimed_at.utcoffset(),
            timedelta(hours=-3),
        )
        self.assertEqual(
            reconstituted.specialist.verified_at.utcoffset(),
            timedelta(hours=-3),
        )

    def test_from_record_rejects_non_mapping_input(self) -> None:
        invalid_records = [None, "not a mapping", 123, [1, 2, 3], True]
        for invalid_record in invalid_records:
            with self.subTest(invalid_record=invalid_record):
                with self.assertRaises(ValueError):
                    human_review_claim_from_record(invalid_record)  # type: ignore[arg-type]

    def test_from_record_rejects_missing_or_invalid_schema_version(self) -> None:
        invalid_versions = [
            {},  # missing
            {"schema_version": None},
            {"schema_version": "1"},
            {"schema_version": True},  # bool is subtype of int, must be strictly rejected
            {"schema_version": False},
            {"schema_version": 0},
            {"schema_version": 2},
            {"schema_version": 99},
        ]
        for base in invalid_versions:
            payload = dict(self.canonical_payload)
            if "schema_version" not in base:
                payload.pop("schema_version", None)
            else:
                payload["schema_version"] = base["schema_version"]  # type: ignore[assignment]
            with self.subTest(version=base.get("schema_version")):
                with self.assertRaises(ValueError):
                    human_review_claim_from_record(payload)

    def test_from_record_rejects_missing_required_envelope_fields(self) -> None:
        required_fields = ["claim_id", "workflow_id", "specialist", "claimed_at"]
        for field in required_fields:
            payload = dict(self.canonical_payload)
            payload.pop(field)
            with self.subTest(missing_field=field):
                with self.assertRaises(ValueError):
                    human_review_claim_from_record(payload)

    def test_from_record_rejects_empty_or_whitespace_strings_in_envelope(self) -> None:
        string_fields = ["claim_id", "workflow_id"]
        invalid_values = ["", "   ", "\t\n", None, 123]
        for field in string_fields:
            for val in invalid_values:
                payload = dict(self.canonical_payload)
                payload[field] = val  # type: ignore[assignment]
                with self.subTest(field=field, value=val):
                    with self.assertRaises(ValueError):
                        human_review_claim_from_record(payload)

    def test_from_record_rejects_non_mapping_specialist(self) -> None:
        invalid_specialists = [None, "invalid", 123, ["SPEC-001"], True]
        for inv_spec in invalid_specialists:
            payload = dict(self.canonical_payload)
            payload["specialist"] = inv_spec  # type: ignore[assignment]
            with self.subTest(specialist=inv_spec):
                with self.assertRaises(ValueError):
                    human_review_claim_from_record(payload)

    def test_from_record_rejects_missing_specialist_fields(self) -> None:
        required_specialist_fields = [
            "specialist_id",
            "identity_provider",
            "identity_subject",
            "verification_id",
            "verified_at",
        ]
        for field in required_specialist_fields:
            spec_dict = dict(self.canonical_payload["specialist"])  # type: ignore[arg-type]
            spec_dict.pop(field)
            payload = dict(self.canonical_payload)
            payload["specialist"] = spec_dict
            with self.subTest(missing_field=field):
                with self.assertRaises(ValueError):
                    human_review_claim_from_record(payload)

    def test_from_record_rejects_empty_or_invalid_specialist_string_fields(self) -> None:
        string_fields = [
            "specialist_id",
            "identity_provider",
            "identity_subject",
            "verification_id",
        ]
        invalid_values = ["", "   ", "\t", None, 123, True]
        for field in string_fields:
            for val in invalid_values:
                spec_dict = dict(self.canonical_payload["specialist"])  # type: ignore[arg-type]
                spec_dict[field] = val
                payload = dict(self.canonical_payload)
                payload["specialist"] = spec_dict
                with self.subTest(field=field, value=val):
                    with self.assertRaises(ValueError):
                        human_review_claim_from_record(payload)

    def test_from_record_rejects_invalid_or_naive_claimed_at(self) -> None:
        invalid_claimed_ats = [
            "",
            "   ",
            "not-a-datetime",
            "2026-08-31T10:05:00",  # naive timestamp without timezone
            12345,
            None,
        ]
        for val in invalid_claimed_ats:
            payload = dict(self.canonical_payload)
            payload["claimed_at"] = val  # type: ignore[assignment]
            with self.subTest(claimed_at=val):
                with self.assertRaises(ValueError):
                    human_review_claim_from_record(payload)

    def test_from_record_rejects_invalid_or_naive_specialist_verified_at(self) -> None:
        invalid_verified_ats = [
            "",
            "   ",
            "not-a-datetime",
            "2026-08-31T10:00:00",  # naive timestamp without timezone
            12345,
            None,
        ]
        for val in invalid_verified_ats:
            spec_dict = dict(self.canonical_payload["specialist"])  # type: ignore[arg-type]
            spec_dict["verified_at"] = val
            payload = dict(self.canonical_payload)
            payload["specialist"] = spec_dict
            with self.subTest(verified_at=val):
                with self.assertRaises(ValueError):
                    human_review_claim_from_record(payload)

    def test_from_record_rejects_specialist_verified_at_after_claimed_at(self) -> None:
        spec_dict = dict(self.canonical_payload["specialist"])  # type: ignore[arg-type]
        spec_dict["verified_at"] = "2026-08-31T10:10:00+00:00"  # 10:10 is after claimed_at 10:05
        payload = dict(self.canonical_payload)
        payload["specialist"] = spec_dict
        with self.assertRaises(ValueError):
            human_review_claim_from_record(payload)

    def test_from_record_rejects_unknown_root_fields(self) -> None:
        payload = dict(self.canonical_payload)
        payload["unexpected_field"] = "x"
        with self.assertRaises(ValueError):
            human_review_claim_from_record(payload)

    def test_from_record_rejects_unknown_specialist_fields(self) -> None:
        spec_dict = dict(self.canonical_payload["specialist"])  # type: ignore[arg-type]
        spec_dict["role"] = "Senior PDM Specialist"  # unknown field in specialist
        payload = dict(self.canonical_payload)
        payload["specialist"] = spec_dict
        with self.assertRaises(ValueError):
            human_review_claim_from_record(payload)


if __name__ == "__main__":
    unittest.main()
