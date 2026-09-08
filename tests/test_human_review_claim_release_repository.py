from datetime import datetime, timezone
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from agent_lab.human_review import VerifiedSpecialistIdentity
from agent_lab.human_review_claim import HumanReviewClaimRelease
from agent_lab.human_review_claim_release_repository import (
    DuplicateHumanReviewClaimReleaseError,
    HumanReviewClaimReleaseCorruptionError,
    HumanReviewClaimReleasePersistenceError,
    HumanReviewClaimReleaseRepository,
    JsonlHumanReviewClaimReleaseRepository,
)
from agent_lab.human_review_claim_release_serialization import (
    human_review_claim_release_to_record,
)


class JsonlHumanReviewClaimReleaseRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_path = Path(self.temp_dir.name) / "releases.jsonl"
        self.repo = JsonlHumanReviewClaimReleaseRepository(self.repo_path)

        self.specialist_1 = VerifiedSpecialistIdentity(
            specialist_id="SPEC-001",
            identity_provider="CORPORATE_IDP",
            identity_subject="user-12345",
            verification_id="VER-001",
            verified_at=datetime(2026, 9, 8, 10, 0, 0, tzinfo=timezone.utc),
        )
        self.specialist_2 = VerifiedSpecialistIdentity(
            specialist_id="SPEC-002",
            identity_provider="CORPORATE_IDP",
            identity_subject="user-67890",
            verification_id="VER-002",
            verified_at=datetime(2026, 9, 8, 10, 0, 0, tzinfo=timezone.utc),
        )
        self.release_1 = HumanReviewClaimRelease(
            release_id="REL-001",
            claim_id="CLM-001",
            workflow_id="WF-001",
            released_by=self.specialist_1,
            released_at=datetime(2026, 9, 8, 10, 5, 0, tzinfo=timezone.utc),
        )
        self.release_2 = HumanReviewClaimRelease(
            release_id="REL-002",
            claim_id="CLM-002",
            workflow_id="WF-002",
            released_by=self.specialist_2,
            released_at=datetime(2026, 9, 8, 10, 10, 0, tzinfo=timezone.utc),
        )
        self.release_3 = HumanReviewClaimRelease(
            release_id="REL-003",
            claim_id="CLM-001",
            workflow_id="WF-001",
            released_by=self.specialist_1,
            released_at=datetime(2026, 9, 8, 10, 15, 0, tzinfo=timezone.utc),
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_repository_protocol_conformance(self) -> None:
        self.assertTrue(
            isinstance(
                JsonlHumanReviewClaimReleaseRepository(self.repo_path),
                HumanReviewClaimReleaseRepository,
            )
        )
        self.assertTrue(
            issubclass(
                JsonlHumanReviewClaimReleaseRepository,
                HumanReviewClaimReleaseRepository,
            )
        )

    def test_append_and_reconstitution_across_repository_instances(
        self,
    ) -> None:
        self.repo.append(self.release_1)

        repo2 = JsonlHumanReviewClaimReleaseRepository(self.repo_path)
        self.assertEqual(repo2.list_all(), (self.release_1,))
        self.assertEqual(repo2.get_by_id(self.release_1.release_id), self.release_1)

    def test_non_existent_file_returns_empty_collections(self) -> None:
        non_existent_path = Path(self.temp_dir.name) / "non_existent.jsonl"
        repo = JsonlHumanReviewClaimReleaseRepository(non_existent_path)

        self.assertEqual(repo.list_all(), ())
        self.assertIsNone(repo.get_by_id("REL-001"))
        self.assertEqual(repo.list_by_claim_id("CLM-001"), ())
        self.assertEqual(repo.list_by_workflow_id("WF-001"), ())

    def test_empty_zero_byte_file_returns_empty_collections(self) -> None:
        self.repo_path.touch()

        self.assertEqual(self.repo.list_all(), ())
        self.assertIsNone(self.repo.get_by_id("REL-001"))
        self.assertEqual(self.repo.list_by_claim_id("CLM-001"), ())
        self.assertEqual(self.repo.list_by_workflow_id("WF-001"), ())

    def test_append_creates_parent_directories_and_persists_records(self) -> None:
        nested_path = Path(self.temp_dir.name) / "nested" / "dir" / "releases.jsonl"
        repo = JsonlHumanReviewClaimReleaseRepository(nested_path)

        repo.append(self.release_1)

        self.assertTrue(nested_path.exists())
        self.assertEqual(repo.list_all(), (self.release_1,))
        self.assertEqual(repo.get_by_id("REL-001"), self.release_1)

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

        with patch("agent_lab.human_review_claim_release_repository.os.fsync") as mock_fsync:
            mock_fsync.side_effect = lambda fd: call_order.append(f"fsync:{fd}")
            with patch("builtins.open", side_effect=tracking_open):
                self.repo.append(self.release_1)

        self.assertIn("flush", call_order)
        self.assertTrue(any(item.startswith("fsync:") for item in call_order))
        flush_idx = call_order.index("flush")
        fsync_idx = next(i for i, item in enumerate(call_order) if item.startswith("fsync:"))
        self.assertLess(flush_idx, fsync_idx)

    def test_append_rejects_non_human_review_claim_release_instance(self) -> None:
        nested_parent = Path(self.temp_dir.name) / "uncreated_parent"
        nested_file = nested_parent / "releases.jsonl"
        repo = JsonlHumanReviewClaimReleaseRepository(nested_file)

        invalid_releases = [None, {}, "string", 123, True, False, self.specialist_1]
        for invalid in invalid_releases:
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    repo.append(invalid)  # type: ignore[arg-type]
                self.assertFalse(nested_file.exists())
                self.assertFalse(nested_parent.exists())

    def test_append_rejects_duplicate_release_id_without_writing(self) -> None:
        self.repo.append(self.release_1)
        bytes_before = self.repo_path.read_bytes()

        duplicate_release = HumanReviewClaimRelease(
            release_id="REL-001",
            claim_id="CLM-DIFFERENT",
            workflow_id="WF-DIFFERENT",
            released_by=self.specialist_2,
            released_at=datetime(2026, 9, 8, 10, 20, 0, tzinfo=timezone.utc),
        )

        with self.assertRaises(DuplicateHumanReviewClaimReleaseError) as ctx:
            self.repo.append(duplicate_release)

        self.assertIn("REL-001", str(ctx.exception))
        self.assertEqual(self.repo.list_all(), (self.release_1,))
        self.assertEqual(self.repo_path.read_bytes(), bytes_before)

    def test_append_allows_multiple_releases_for_same_claim_and_workflow(self) -> None:
        self.repo.append(self.release_1)
        self.repo.append(self.release_3)

        self.assertEqual(self.repo.list_by_claim_id("CLM-001"), (self.release_1, self.release_3))
        self.assertEqual(self.repo.list_by_workflow_id("WF-001"), (self.release_1, self.release_3))
        self.assertEqual(self.repo.list_all(), (self.release_1, self.release_3))

    def test_queries_preserve_physical_append_order(self) -> None:
        self.repo.append(self.release_2)
        self.repo.append(self.release_1)
        self.repo.append(self.release_3)

        self.assertEqual(self.repo.list_all(), (self.release_2, self.release_1, self.release_3))

    def test_queries_preserve_non_chronological_physical_append_order(self) -> None:
        # release_3 has released_at=10:15
        # release_1 has released_at=10:05
        # Both share claim_id="CLM-001" and workflow_id="WF-001"
        self.repo.append(self.release_3)
        self.repo.append(self.release_1)

        self.assertEqual(
            self.repo.list_all(),
            (self.release_3, self.release_1),
        )
        self.assertEqual(
            self.repo.list_by_claim_id("CLM-001"),
            (self.release_3, self.release_1),
        )
        self.assertEqual(
            self.repo.list_by_workflow_id("WF-001"),
            (self.release_3, self.release_1),
        )

    def test_query_methods_reject_invalid_id_arguments(self) -> None:
        invalid_ids = [None, 123, True, False, "", "   ", "\t\n", object()]
        for invalid_id in invalid_ids:
            with self.subTest(invalid_id=invalid_id):
                with self.assertRaises(ValueError):
                    self.repo.get_by_id(invalid_id)  # type: ignore[arg-type]
                with self.assertRaises(ValueError):
                    self.repo.list_by_claim_id(invalid_id)  # type: ignore[arg-type]
                with self.assertRaises(ValueError):
                    self.repo.list_by_workflow_id(invalid_id)  # type: ignore[arg-type]

    def test_queries_preserve_exact_identity_without_stripping_search_term(self) -> None:
        release_with_spaces = HumanReviewClaimRelease(
            release_id="REL-SPACES-001",
            claim_id="  CLM-EXACT-001  ",
            workflow_id="  WF-EXACT-001  ",
            released_by=self.specialist_1,
            released_at=datetime(2026, 9, 8, 10, 5, 0, tzinfo=timezone.utc),
        )
        self.repo.append(release_with_spaces)

        self.assertEqual(
            self.repo.list_by_claim_id("  CLM-EXACT-001  "),
            (release_with_spaces,),
        )
        self.assertEqual(self.repo.list_by_claim_id("CLM-EXACT-001"), ())

        self.assertEqual(
            self.repo.list_by_workflow_id("  WF-EXACT-001  "),
            (release_with_spaces,),
        )
        self.assertEqual(self.repo.list_by_workflow_id("WF-EXACT-001"), ())

    def test_fail_closed_on_empty_or_whitespace_line_at_line_two(self) -> None:
        rec1 = human_review_claim_release_to_record(self.release_1)
        with open(self.repo_path, "w", encoding="utf-8") as f:
            f.write(f"{json.dumps(rec1)}\n")
            f.write("   \n")
            f.write(f"{json.dumps(rec1)}\n")

        with self.assertRaises(HumanReviewClaimReleaseCorruptionError) as ctx:
            self.repo.list_all()

        self.assertEqual(ctx.exception.line_number, 2)
        self.assertTrue(
            issubclass(
                HumanReviewClaimReleaseCorruptionError,
                HumanReviewClaimReleasePersistenceError,
            )
        )

    def test_fail_closed_on_malformed_json_at_line_two(self) -> None:
        rec1 = human_review_claim_release_to_record(self.release_1)
        with open(self.repo_path, "w", encoding="utf-8") as f:
            f.write(f"{json.dumps(rec1)}\n")
            f.write('{"schema_version": 1, "release_id": \n')

        with self.assertRaises(HumanReviewClaimReleaseCorruptionError) as ctx:
            self.repo.list_all()

        self.assertEqual(ctx.exception.line_number, 2)

    def test_fail_closed_on_non_object_json_at_line_two(self) -> None:
        rec1 = human_review_claim_release_to_record(self.release_1)
        with open(self.repo_path, "w", encoding="utf-8") as f:
            f.write(f"{json.dumps(rec1)}\n")
            f.write('["not", "a", "json", "object"]\n')

        with self.assertRaises(HumanReviewClaimReleaseCorruptionError) as ctx:
            self.repo.list_all()

        self.assertEqual(ctx.exception.line_number, 2)

    def test_fail_closed_on_schema_violation_at_line_two(self) -> None:
        rec1 = human_review_claim_release_to_record(self.release_1)
        invalid_rec = {"schema_version": 1, "release_id": "REL-002"}
        with open(self.repo_path, "w", encoding="utf-8") as f:
            f.write(f"{json.dumps(rec1)}\n")
            f.write(f"{json.dumps(invalid_rec)}\n")

        with self.assertRaises(HumanReviewClaimReleaseCorruptionError) as ctx:
            self.repo.list_all()

        self.assertEqual(ctx.exception.line_number, 2)

    def test_fail_closed_on_duplicate_release_id_in_persisted_file(self) -> None:
        rec1 = human_review_claim_release_to_record(self.release_1)
        with open(self.repo_path, "w", encoding="utf-8") as f:
            f.write(f"{json.dumps(rec1)}\n")
            f.write(f"{json.dumps(rec1)}\n")

        with self.assertRaises(HumanReviewClaimReleaseCorruptionError) as ctx:
            self.repo.list_all()

        self.assertEqual(ctx.exception.line_number, 2)

    def test_fail_closed_on_invalid_utf8_encoding_at_line_two(self) -> None:
        rec1 = human_review_claim_release_to_record(self.release_1)
        valid_bytes = json.dumps(rec1).encode("utf-8") + b"\n"
        invalid_bytes = b"\xff\xfe\x80\n"
        self.repo_path.write_bytes(valid_bytes + invalid_bytes)

        with self.assertRaises(HumanReviewClaimReleaseCorruptionError) as ctx:
            self.repo.list_all()

        self.assertEqual(ctx.exception.line_number, 2)
        self.assertIn("Invalid UTF-8", str(ctx.exception))

        with self.assertRaises(HumanReviewClaimReleaseCorruptionError):
            self.repo.append(self.release_2)

        self.assertEqual(self.repo_path.read_bytes(), valid_bytes + invalid_bytes)

    def test_append_after_last_valid_json_without_trailing_newline(self) -> None:
        rec1 = human_review_claim_release_to_record(self.release_1)
        initial_bytes = json.dumps(rec1).encode("utf-8")
        self.repo_path.write_bytes(initial_bytes)

        self.assertEqual(self.repo.list_all(), (self.release_1,))

        self.repo.append(self.release_2)

        self.assertEqual(self.repo.list_all(), (self.release_1, self.release_2))
        self.assertEqual(self.repo.get_by_id("REL-001"), self.release_1)
        self.assertEqual(self.repo.get_by_id("REL-002"), self.release_2)

        current_bytes = self.repo_path.read_bytes()
        self.assertTrue(current_bytes.startswith(initial_bytes))
        rec2 = human_review_claim_release_to_record(self.release_2)
        expected_bytes = initial_bytes + b"\n" + json.dumps(rec2).encode("utf-8") + b"\n"
        self.assertEqual(current_bytes, expected_bytes)

    def test_append_after_last_valid_json_with_isolated_cr_preserves_prefix(self) -> None:
        rec1 = human_review_claim_release_to_record(self.release_1)
        initial_bytes = json.dumps(rec1).encode("utf-8") + b"\r"
        self.repo_path.write_bytes(initial_bytes)

        self.assertEqual(self.repo.list_all(), (self.release_1,))

        self.repo.append(self.release_2)

        self.assertEqual(self.repo.list_all(), (self.release_1, self.release_2))
        self.assertEqual(self.repo.get_by_id("REL-001"), self.release_1)
        self.assertEqual(self.repo.get_by_id("REL-002"), self.release_2)

        current_bytes = self.repo_path.read_bytes()
        self.assertTrue(current_bytes.startswith(initial_bytes))
        rec2 = human_review_claim_release_to_record(self.release_2)
        expected_bytes = initial_bytes + b"\n" + json.dumps(rec2).encode("utf-8") + b"\n"
        self.assertEqual(current_bytes, expected_bytes)

    def test_append_after_last_valid_json_with_crlf_and_lf(self) -> None:
        rec1 = human_review_claim_release_to_record(self.release_1)
        rec2 = human_review_claim_release_to_record(self.release_2)

        # Case 1: with LF
        self.repo_path.write_bytes(json.dumps(rec1).encode("utf-8") + b"\n")
        self.repo.append(self.release_2)
        self.assertEqual(self.repo.list_all(), (self.release_1, self.release_2))
        self.assertEqual(
            self.repo_path.read_bytes(),
            json.dumps(rec1).encode("utf-8") + b"\n" + json.dumps(rec2).encode("utf-8") + b"\n",
        )

        # Case 2: with CRLF
        self.repo_path.write_bytes(json.dumps(rec1).encode("utf-8") + b"\r\n")
        self.repo.append(self.release_2)
        self.assertEqual(self.repo.list_all(), (self.release_1, self.release_2))
        self.assertEqual(
            self.repo_path.read_bytes(),
            json.dumps(rec1).encode("utf-8") + b"\r\n" + json.dumps(rec2).encode("utf-8") + b"\n",
        )

    def test_corruption_after_matching_record_aborts_all_queries(self) -> None:
        rec1 = human_review_claim_release_to_record(self.release_1)
        corrupted_content = f"{json.dumps(rec1)}\nMALFORMED JSON\n"
        self.repo_path.write_text(corrupted_content, encoding="utf-8")

        with self.assertRaises(HumanReviewClaimReleaseCorruptionError) as ctx:
            self.repo.list_all()
        self.assertEqual(ctx.exception.line_number, 2)

        with self.assertRaises(HumanReviewClaimReleaseCorruptionError) as ctx:
            self.repo.get_by_id("REL-001")
        self.assertEqual(ctx.exception.line_number, 2)

        with self.assertRaises(HumanReviewClaimReleaseCorruptionError) as ctx:
            self.repo.list_by_claim_id("CLM-001")
        self.assertEqual(ctx.exception.line_number, 2)

        with self.assertRaises(HumanReviewClaimReleaseCorruptionError) as ctx:
            self.repo.list_by_workflow_id("WF-001")
        self.assertEqual(ctx.exception.line_number, 2)

    def test_append_on_corrupted_file_raises_corruption_error_and_does_not_write(self) -> None:
        corrupted_content = "CORRUPTED LINE\n"
        self.repo_path.write_text(corrupted_content, encoding="utf-8")

        with self.assertRaises(HumanReviewClaimReleaseCorruptionError) as ctx:
            self.repo.append(self.release_1)

        self.assertEqual(ctx.exception.line_number, 1)
        self.assertEqual(
            self.repo_path.read_text(encoding="utf-8"),
            corrupted_content,
        )

    def test_read_and_write_io_errors_wrapped_in_persistence_error(self) -> None:
        rec1 = human_review_claim_release_to_record(self.release_1)
        self.repo_path.write_text(json.dumps(rec1) + "\n", encoding="utf-8")

        # 1. Read IO error
        read_error = OSError("Disk read failure")
        with patch("builtins.open", side_effect=read_error):
            with self.assertRaises(HumanReviewClaimReleasePersistenceError) as ctx:
                self.repo.list_all()
            self.assertIn("Disk read failure", str(ctx.exception))
            self.assertIs(ctx.exception.__cause__, read_error)

        # 2. Write IO error (only when opening in append mode 'a')
        real_open = open
        write_error = OSError("Disk full")
        append_opened = False

        def open_with_write_failure(*args, **kwargs):
            nonlocal append_opened
            mode = kwargs.get("mode") or (args[1] if len(args) > 1 else "r")
            if mode == "a":
                append_opened = True
                raise write_error
            return real_open(*args, **kwargs)

        with patch("builtins.open", side_effect=open_with_write_failure):
            with self.assertRaises(HumanReviewClaimReleasePersistenceError) as ctx:
                self.repo.append(self.release_2)
            self.assertIn("Disk full", str(ctx.exception))
            self.assertIs(ctx.exception.__cause__, write_error)
            self.assertTrue(append_opened)

    def test_append_flush_failure_is_reported_as_persistence_error(self) -> None:
        real_open = open
        flush_error = OSError("Flush failed on disk")
        flush_reached = False

        def open_with_flush_failure(*args, **kwargs):
            handle = real_open(*args, **kwargs)
            mode = kwargs.get("mode") or (args[1] if len(args) > 1 else "r")
            if mode == "a":
                def failing_flush():
                    nonlocal flush_reached
                    flush_reached = True
                    raise flush_error

                handle.flush = failing_flush  # type: ignore[method-assign]
            return handle

        with patch("builtins.open", side_effect=open_with_flush_failure):
            with self.assertRaises(HumanReviewClaimReleasePersistenceError) as ctx:
                self.repo.append(self.release_1)

            self.assertIn("Flush failed on disk", str(ctx.exception))
            self.assertIs(ctx.exception.__cause__, flush_error)
            self.assertTrue(flush_reached)

    def test_append_fsync_failure_is_reported_as_persistence_error(self) -> None:
        fsync_error = OSError("Fsync failed on controller")
        fsync_reached = False

        def failing_fsync(fd: int) -> None:
            nonlocal fsync_reached
            fsync_reached = True
            raise fsync_error

        with patch(
            "agent_lab.human_review_claim_release_repository.os.fsync",
            side_effect=failing_fsync,
        ):
            with self.assertRaises(HumanReviewClaimReleasePersistenceError) as ctx:
                self.repo.append(self.release_1)

            self.assertIn("Fsync failed on controller", str(ctx.exception))
            self.assertIs(ctx.exception.__cause__, fsync_error)
            self.assertTrue(fsync_reached)


if __name__ == "__main__":
    unittest.main()
