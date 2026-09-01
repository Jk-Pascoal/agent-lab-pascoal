from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from agent_lab.human_review import VerifiedSpecialistIdentity
from agent_lab.human_review_claim import HumanReviewClaim
from agent_lab.human_review_claim_repository import (
    DuplicateHumanReviewClaimError,
    HumanReviewClaimCorruptionError,
    HumanReviewClaimPersistenceError,
    HumanReviewClaimRepository,
    JsonlHumanReviewClaimRepository,
)
from agent_lab.human_review_claim_serialization import human_review_claim_to_record


class JsonlHumanReviewClaimRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_path = Path(self.temp_dir.name) / "claims.jsonl"
        self.repo = JsonlHumanReviewClaimRepository(self.repo_path)

        self.specialist_1 = VerifiedSpecialistIdentity(
            specialist_id="SPEC-001",
            identity_provider="CORPORATE_IDP",
            identity_subject="user-12345",
            verification_id="VER-001",
            verified_at=datetime(2026, 8, 31, 10, 0, 0, tzinfo=timezone.utc),
        )
        self.specialist_2 = VerifiedSpecialistIdentity(
            specialist_id="SPEC-002",
            identity_provider="CORPORATE_IDP",
            identity_subject="user-67890",
            verification_id="VER-002",
            verified_at=datetime(2026, 8, 31, 10, 0, 0, tzinfo=timezone.utc),
        )
        self.claim_1 = HumanReviewClaim(
            claim_id="CLM-001",
            workflow_id="WF-001",
            specialist=self.specialist_1,
            claimed_at=datetime(2026, 8, 31, 10, 5, 0, tzinfo=timezone.utc),
        )
        self.claim_2 = HumanReviewClaim(
            claim_id="CLM-002",
            workflow_id="WF-002",
            specialist=self.specialist_2,
            claimed_at=datetime(2026, 8, 31, 10, 10, 0, tzinfo=timezone.utc),
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_repository_protocol_conformance(self) -> None:
        self.assertTrue(
            isinstance(
                JsonlHumanReviewClaimRepository(self.repo_path),
                HumanReviewClaimRepository,
            )
        )
        self.assertTrue(
            issubclass(
                JsonlHumanReviewClaimRepository,
                HumanReviewClaimRepository,
            )
        )

    def test_non_existent_file_returns_empty_collections(self) -> None:
        non_existent_path = Path(self.temp_dir.name) / "non_existent.jsonl"
        repo = JsonlHumanReviewClaimRepository(non_existent_path)

        self.assertEqual(repo.list_all(), ())
        self.assertIsNone(repo.get_by_id("CLM-001"))
        self.assertEqual(repo.list_by_workflow_id("WF-001"), ())

    def test_empty_zero_byte_file_returns_empty_collections(self) -> None:
        self.repo_path.touch()

        self.assertEqual(self.repo.list_all(), ())
        self.assertIsNone(self.repo.get_by_id("CLM-001"))
        self.assertEqual(self.repo.list_by_workflow_id("WF-001"), ())

    def test_append_creates_parent_directories_and_persists_jsonl_record(self) -> None:
        nested_path = Path(self.temp_dir.name) / "nested" / "dir" / "claims.jsonl"
        repo = JsonlHumanReviewClaimRepository(nested_path)

        repo.append(self.claim_1)

        self.assertTrue(nested_path.exists())
        self.assertEqual(repo.list_all(), (self.claim_1,))
        self.assertEqual(repo.get_by_id("CLM-001"), self.claim_1)
        self.assertEqual(repo.list_by_workflow_id("WF-001"), (self.claim_1,))

    def test_append_calls_flush_and_fsync(self) -> None:
        call_order: list[str] = []
        real_open = open

        def tracking_open(*args, **kwargs):
            handle = real_open(*args, **kwargs)
            original_flush = handle.flush
            original_fileno = handle.fileno

            def tracking_flush():
                call_order.append("flush")
                return original_flush()

            def tracking_fileno():
                call_order.append("fileno")
                return original_fileno()

            handle.flush = tracking_flush  # type: ignore[method-assign]
            handle.fileno = tracking_fileno  # type: ignore[method-assign]
            return handle

        with patch("agent_lab.human_review_claim_repository.os.fsync") as mock_fsync:
            mock_fsync.side_effect = lambda fd: call_order.append(f"fsync:{fd}")
            with patch("builtins.open", side_effect=tracking_open):
                self.repo.append(self.claim_1)

            mock_fsync.assert_called_once()
            file_descriptor = mock_fsync.call_args[0][0]
            self.assertIsInstance(file_descriptor, int)
            self.assertIn("flush", call_order)
            self.assertIn("fileno", call_order)
            self.assertIn(f"fsync:{file_descriptor}", call_order)
            flush_idx = call_order.index("flush")
            fsync_idx = call_order.index(f"fsync:{file_descriptor}")
            self.assertLess(flush_idx, fsync_idx)

    def test_append_rejects_non_human_review_claim_instance(self) -> None:
        invalid_claims = [None, {}, "claim", 123, True, False, self.specialist_1]
        for invalid_claim in invalid_claims:
            with self.subTest(invalid_claim=invalid_claim):
                with self.assertRaises(ValueError):
                    self.repo.append(invalid_claim)  # type: ignore[arg-type]

    def test_append_rejects_duplicate_claim_id(self) -> None:
        self.repo.append(self.claim_1)

        claim_duplicate = HumanReviewClaim(
            claim_id="CLM-001",
            workflow_id="WF-002",
            specialist=self.specialist_2,
            claimed_at=datetime(2026, 8, 31, 10, 15, 0, tzinfo=timezone.utc),
        )

        with self.assertRaises(DuplicateHumanReviewClaimError) as ctx:
            self.repo.append(claim_duplicate)

        self.assertTrue(
            issubclass(
                DuplicateHumanReviewClaimError,
                HumanReviewClaimPersistenceError,
            )
        )
        self.assertIn("CLM-001", str(ctx.exception))

        # Asserts physical integrity: file still has exactly 1 line and unchanged content
        with open(self.repo_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        self.assertEqual(len(lines), 1)
        self.assertEqual(self.repo.list_all(), (self.claim_1,))

    def test_append_allows_and_preserves_multiple_claims_for_same_workflow_id(
        self,
    ) -> None:
        claim_wf1_a = HumanReviewClaim(
            claim_id="CLM-001",
            workflow_id="WF-001",
            specialist=self.specialist_1,
            claimed_at=datetime(2026, 8, 31, 10, 5, 0, tzinfo=timezone.utc),
        )
        claim_wf1_b = HumanReviewClaim(
            claim_id="CLM-002",
            workflow_id="WF-001",
            specialist=self.specialist_2,
            claimed_at=datetime(2026, 8, 31, 10, 10, 0, tzinfo=timezone.utc),
        )

        self.repo.append(claim_wf1_a)
        self.repo.append(claim_wf1_b)

        wf_claims = self.repo.list_by_workflow_id("WF-001")
        self.assertEqual(wf_claims, (claim_wf1_a, claim_wf1_b))
        self.assertEqual(self.repo.list_all(), (claim_wf1_a, claim_wf1_b))

    def test_list_methods_preserve_strict_physical_append_order(self) -> None:
        # Deliberately non-chronological timestamps: 10:30 -> 10:05 -> 10:20
        claim_1 = HumanReviewClaim(
            claim_id="CLM-001",
            workflow_id="WF-001",
            specialist=self.specialist_1,
            claimed_at=datetime(2026, 8, 31, 10, 30, 0, tzinfo=timezone.utc),
        )
        claim_2 = HumanReviewClaim(
            claim_id="CLM-002",
            workflow_id="WF-001",
            specialist=self.specialist_2,
            claimed_at=datetime(2026, 8, 31, 10, 5, 0, tzinfo=timezone.utc),
        )
        claim_3 = HumanReviewClaim(
            claim_id="CLM-003",
            workflow_id="WF-001",
            specialist=self.specialist_1,
            claimed_at=datetime(2026, 8, 31, 10, 20, 0, tzinfo=timezone.utc),
        )

        self.repo.append(claim_1)
        self.repo.append(claim_2)
        self.repo.append(claim_3)

        self.assertEqual(self.repo.list_all(), (claim_1, claim_2, claim_3))
        self.assertEqual(
            self.repo.list_by_workflow_id("WF-001"),
            (claim_1, claim_2, claim_3),
        )

    def test_get_by_id_returns_exact_claim_or_none(self) -> None:
        self.repo.append(self.claim_1)
        self.repo.append(self.claim_2)

        self.assertEqual(self.repo.get_by_id("CLM-001"), self.claim_1)
        self.assertEqual(self.repo.get_by_id("CLM-002"), self.claim_2)
        self.assertIsNone(self.repo.get_by_id("CLM-999"))

    def test_get_by_id_rejects_empty_or_invalid_claim_id(self) -> None:
        invalid_ids = ["", "   ", "\t\n", None, 123, True, False]
        for invalid_id in invalid_ids:
            with self.subTest(claim_id=invalid_id):
                with self.assertRaises(ValueError):
                    self.repo.get_by_id(invalid_id)  # type: ignore[arg-type]

    def test_list_by_workflow_id_returns_only_matching_workflow_claims(
        self,
    ) -> None:
        claim_wf1_a = HumanReviewClaim(
            claim_id="CLM-001",
            workflow_id="WF-001",
            specialist=self.specialist_1,
            claimed_at=datetime(2026, 8, 31, 10, 5, 0, tzinfo=timezone.utc),
        )
        claim_wf2 = HumanReviewClaim(
            claim_id="CLM-002",
            workflow_id="WF-002",
            specialist=self.specialist_2,
            claimed_at=datetime(2026, 8, 31, 10, 10, 0, tzinfo=timezone.utc),
        )
        claim_wf1_b = HumanReviewClaim(
            claim_id="CLM-003",
            workflow_id="WF-001",
            specialist=self.specialist_1,
            claimed_at=datetime(2026, 8, 31, 10, 15, 0, tzinfo=timezone.utc),
        )

        self.repo.append(claim_wf1_a)
        self.repo.append(claim_wf2)
        self.repo.append(claim_wf1_b)

        self.assertEqual(
            self.repo.list_by_workflow_id("WF-001"),
            (claim_wf1_a, claim_wf1_b),
        )
        self.assertEqual(
            self.repo.list_by_workflow_id("WF-002"),
            (claim_wf2,),
        )
        self.assertEqual(
            self.repo.list_by_workflow_id("WF-003"),
            (),
        )

    def test_list_by_workflow_id_rejects_empty_or_invalid_workflow_id(
        self,
    ) -> None:
        invalid_ids = ["", "   ", "\t\n", None, 123, True, False]
        for invalid_id in invalid_ids:
            with self.subTest(workflow_id=invalid_id):
                with self.assertRaises(ValueError):
                    self.repo.list_by_workflow_id(invalid_id)  # type: ignore[arg-type]

    def test_fail_closed_on_empty_line_at_line_two(self) -> None:
        valid_record = human_review_claim_to_record(self.claim_1)
        with open(self.repo_path, "w", encoding="utf-8") as f:
            f.write(f"{json.dumps(valid_record)}\n")
            f.write("   \n")
            f.write(f"{json.dumps(valid_record)}\n")

        with self.assertRaises(HumanReviewClaimCorruptionError) as ctx:
            self.repo.list_all()

        self.assertEqual(ctx.exception.line_number, 2)
        self.assertTrue(
            issubclass(
                HumanReviewClaimCorruptionError,
                HumanReviewClaimPersistenceError,
            )
        )

    def test_fail_closed_on_malformed_json_at_line_two(self) -> None:
        valid_record = human_review_claim_to_record(self.claim_1)
        with open(self.repo_path, "w", encoding="utf-8") as f:
            f.write(f"{json.dumps(valid_record)}\n")
            f.write('{"schema_version": 1, "claim_id": \n')

        with self.assertRaises(HumanReviewClaimCorruptionError) as ctx:
            self.repo.list_all()

        self.assertEqual(ctx.exception.line_number, 2)

    def test_fail_closed_on_non_object_json_at_line_two(self) -> None:
        valid_record = human_review_claim_to_record(self.claim_1)
        with open(self.repo_path, "w", encoding="utf-8") as f:
            f.write(f"{json.dumps(valid_record)}\n")
            f.write('["not", "a", "json", "object"]\n')

        with self.assertRaises(HumanReviewClaimCorruptionError) as ctx:
            self.repo.list_all()

        self.assertEqual(ctx.exception.line_number, 2)

    def test_fail_closed_on_invalid_schema_or_contract_at_line_two(self) -> None:
        valid_record = human_review_claim_to_record(self.claim_1)
        invalid_record = {"schema_version": 1, "claim_id": "CLM-002"}  # missing fields
        with open(self.repo_path, "w", encoding="utf-8") as f:
            f.write(f"{json.dumps(valid_record)}\n")
            f.write(f"{json.dumps(invalid_record)}\n")

        with self.assertRaises(HumanReviewClaimCorruptionError) as ctx:
            self.repo.list_all()

        self.assertEqual(ctx.exception.line_number, 2)

    def test_fail_closed_on_corrupted_file_during_append(self) -> None:
        with open(self.repo_path, "w", encoding="utf-8") as f:
            f.write("corrupted line 1\n")

        with self.assertRaises(HumanReviewClaimCorruptionError) as ctx:
            self.repo.append(self.claim_1)

        self.assertEqual(ctx.exception.line_number, 1)


if __name__ == "__main__":
    unittest.main()
