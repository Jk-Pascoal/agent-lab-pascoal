from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from agent_lab.decision import DecisionRecommendation
from agent_lab.domain import GovernanceDecision, IssueSeverity, IssueType
from agent_lab.evidence import EvidenceSource, GovernanceEvidence
from agent_lab.workflow_events import WorkflowOpened
from agent_lab.workflow_repository import (
    JsonlWorkflowLifecycleRepository,
    WorkflowLifecycleRepository,
)
from agent_lab.workflow_serialization import workflow_opened_to_record


class JsonlWorkflowLifecycleRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.file_path = Path(self.temp_dir.name) / "workflow_lifecycle.jsonl"
        self.repository = JsonlWorkflowLifecycleRepository(self.file_path)
        self.opened_at = datetime(
            2026,
            8,
            19,
            8,
            30,
            0,
            tzinfo=timezone.utc,
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def build_event(
        self,
        *,
        event_id: str = "evt-open-001",
        workflow_id: str = "wf-mat-001-01",
        material_id: str = "MAT-001",
        opened_at: datetime | None = None,
    ) -> WorkflowOpened:
        evidence = (
            GovernanceEvidence(
                material_id=material_id,
                source=EvidenceSource.RULE,
                issue_type=IssueType.MISSING_CRITICAL_FIELD,
                observation="Campo obrigatório não informado.",
                severity=IssueSeverity.WARNING,
            ),
        )
        recommendation = DecisionRecommendation(
            material_id=material_id,
            decision=GovernanceDecision.REVIEW,
            evidence=evidence,
            rationale=f"Recomendação REVIEW para {material_id}",
            requires_human_decision=True,
        )
        return WorkflowOpened(
            event_id=event_id,
            workflow_id=workflow_id,
            recommendation=recommendation,
            opened_at=opened_at or self.opened_at,
        )

    def test_nonexistent_file_returns_empty_collection(self) -> None:
        self.assertEqual(self.repository.list_all_opened(), ())

    def test_empty_file_returns_empty_collection(self) -> None:
        self.file_path.touch()

        self.assertEqual(self.repository.list_all_opened(), ())

    def test_append_opened_persists_event_as_single_json_line(self) -> None:
        event = self.build_event()
        self.repository.append_opened(event)

        lines = self.file_path.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 1)

        record = json.loads(lines[0])
        self.assertEqual(record, workflow_opened_to_record(event))
        self.assertEqual(record["schema_version"], 1)
        self.assertEqual(record["event_id"], "evt-open-001")
        self.assertEqual(record["workflow_id"], "wf-mat-001-01")
        self.assertEqual(record["opened_at"], "2026-08-19T08:30:00+00:00")
        self.assertEqual(record["recommendation"]["material_id"], "MAT-001")
        self.assertEqual(record["recommendation"]["decision"], "REVIEW")
        self.assertIs(record["recommendation"]["requires_human_decision"], True)

    def test_new_repository_instance_recovers_persisted_event(self) -> None:
        event = self.build_event()
        self.repository.append_opened(event)

        reopened = JsonlWorkflowLifecycleRepository(self.file_path)
        self.assertEqual(reopened.list_all_opened(), (event,))

    def test_get_opened_by_id_returns_existing_event(self) -> None:
        event = self.build_event(event_id="evt-open-001")
        self.repository.append_opened(event)

        retrieved = self.repository.get_opened_by_id("evt-open-001")
        self.assertEqual(retrieved, event)

    def test_get_opened_by_id_returns_none_for_missing_id(self) -> None:
        self.assertIsNone(self.repository.get_opened_by_id("non-existent-id"))

    def test_get_opened_by_workflow_id_returns_existing_event(self) -> None:
        event = self.build_event(
            event_id="evt-open-001",
            workflow_id="wf-mat-001-01",
        )
        self.repository.append_opened(event)

        retrieved = self.repository.get_opened_by_workflow_id("wf-mat-001-01")
        self.assertEqual(retrieved, event)

    def test_get_opened_by_workflow_id_returns_none_for_missing_workflow_id(
        self,
    ) -> None:
        self.assertIsNone(
            self.repository.get_opened_by_workflow_id("non-existent-wf")
        )

    def test_list_opened_by_material_filters_and_preserves_recording_order(
        self,
    ) -> None:
        event1 = self.build_event(
            event_id="evt-open-001",
            workflow_id="wf-001",
            material_id="MAT-001",
            opened_at=datetime(2026, 8, 19, 12, 0, tzinfo=timezone.utc),
        )
        event2 = self.build_event(
            event_id="evt-open-002",
            workflow_id="wf-002",
            material_id="MAT-002",
            opened_at=datetime(2026, 8, 19, 11, 0, tzinfo=timezone.utc),
        )
        event3 = self.build_event(
            event_id="evt-open-003",
            workflow_id="wf-003",
            material_id="MAT-001",
            opened_at=datetime(2026, 8, 19, 10, 0, tzinfo=timezone.utc),
        )

        self.repository.append_opened(event1)
        self.repository.append_opened(event2)
        self.repository.append_opened(event3)

        results = self.repository.list_opened_by_material("MAT-001")
        self.assertEqual(results, (event1, event3))

    def test_list_all_opened_preserves_recording_order(self) -> None:
        event_late = self.build_event(
            event_id="evt-open-001",
            workflow_id="wf-001",
            material_id="MAT-001",
            opened_at=datetime(2026, 8, 19, 14, 0, tzinfo=timezone.utc),
        )
        event_early = self.build_event(
            event_id="evt-open-002",
            workflow_id="wf-002",
            material_id="MAT-002",
            opened_at=datetime(2026, 8, 19, 8, 0, tzinfo=timezone.utc),
        )

        self.repository.append_opened(event_late)
        self.repository.append_opened(event_early)

        results = self.repository.list_all_opened()
        self.assertEqual(results, (event_late, event_early))

    def test_append_opened_rejects_non_workflow_opened_instance(self) -> None:
        cases = ["not-an-event", None, 123, dict(), tuple()]
        for invalid_input in cases:
            with self.subTest(invalid_input=invalid_input):
                with self.assertRaises(ValueError):
                    self.repository.append_opened(invalid_input)  # type: ignore[arg-type]

    def test_query_methods_reject_non_string_identifiers(self) -> None:
        invalid_ids = [123, None, True, [], {}]

        for bad_id in invalid_ids:
            with self.subTest(query="get_opened_by_id", bad_id=bad_id):
                with self.assertRaises(ValueError):
                    self.repository.get_opened_by_id(bad_id)  # type: ignore[arg-type]

            with self.subTest(
                query="get_opened_by_workflow_id", bad_id=bad_id
            ):
                with self.assertRaises(ValueError):
                    self.repository.get_opened_by_workflow_id(bad_id)  # type: ignore[arg-type]

            with self.subTest(
                query="list_opened_by_material", bad_id=bad_id
            ):
                with self.assertRaises(ValueError):
                    self.repository.list_opened_by_material(bad_id)  # type: ignore[arg-type]

    def test_public_api_does_not_expose_update_or_delete(self) -> None:
        forbidden_methods = ("update", "delete", "remove", "pop", "clear")

        for method_name in forbidden_methods:
            with self.subTest(
                target="JsonlWorkflowLifecycleRepository", method=method_name
            ):
                self.assertFalse(hasattr(self.repository, method_name))
            with self.subTest(
                target="WorkflowLifecycleRepository", method=method_name
            ):
                self.assertFalse(
                    hasattr(WorkflowLifecycleRepository, method_name)
                )


if __name__ == "__main__":
    unittest.main()
