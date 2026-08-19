from __future__ import annotations

import unittest
from datetime import datetime, timezone

from agent_lab.decision import DecisionRecommendation
from agent_lab.domain import GovernanceDecision, IssueSeverity, IssueType
from agent_lab.evidence import EvidenceSource, GovernanceEvidence
from agent_lab.workflow_events import WorkflowOpened
from agent_lab.workflow_serialization import (
    SCHEMA_VERSION_V1,
    workflow_opened_from_record,
    workflow_opened_to_record,
)


class WorkflowSerializationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.opened_at = datetime(
            2026,
            8,
            19,
            8,
            30,
            0,
            tzinfo=timezone.utc,
        )
        self.evidence = (
            GovernanceEvidence(
                material_id="MAT-001",
                source=EvidenceSource.RULE,
                issue_type=IssueType.MISSING_CRITICAL_FIELD,
                observation="Campo obrigatório não informado.",
                severity=IssueSeverity.WARNING,
            ),
            GovernanceEvidence(
                material_id="MAT-001",
                source=EvidenceSource.LLM,
                issue_type=IssueType.AMBIGUOUS_DESCRIPTION,
                observation="Descrição com termos ambíguos.",
                severity=IssueSeverity.WARNING,
            ),
        )
        self.recommendation = DecisionRecommendation(
            material_id="MAT-001",
            decision=GovernanceDecision.REVIEW,
            evidence=self.evidence,
            rationale="Recomendação REVIEW: 2 evidência(s) requer(em) análise humana.",
            requires_human_decision=True,
        )
        self.event = WorkflowOpened(
            event_id="evt-open-001",
            workflow_id="wf-mat-001-01",
            recommendation=self.recommendation,
            opened_at=self.opened_at,
        )

    def test_schema_version_constant_is_one(self) -> None:
        self.assertEqual(SCHEMA_VERSION_V1, 1)

    def test_serialization_produces_expected_record_structure_and_values(
        self,
    ) -> None:
        record = workflow_opened_to_record(self.event)

        self.assertIsInstance(record, dict)
        self.assertEqual(record["schema_version"], 1)
        self.assertEqual(record["event_id"], "evt-open-001")
        self.assertEqual(record["workflow_id"], "wf-mat-001-01")
        self.assertEqual(record["opened_at"], "2026-08-19T08:30:00+00:00")

        rec_dict = record["recommendation"]
        self.assertIsInstance(rec_dict, dict)
        self.assertEqual(rec_dict["material_id"], "MAT-001")
        self.assertEqual(rec_dict["decision"], "REVIEW")
        self.assertEqual(
            rec_dict["rationale"],
            "Recomendação REVIEW: 2 evidência(s) requer(em) análise humana.",
        )
        self.assertIs(rec_dict["requires_human_decision"], True)

        evidence_list = rec_dict["evidence"]
        self.assertIsInstance(evidence_list, list)
        self.assertEqual(len(evidence_list), 2)
        self.assertEqual(
            evidence_list[0],
            {
                "material_id": "MAT-001",
                "source": "RULE",
                "issue_type": "MISSING_CRITICAL_FIELD",
                "observation": "Campo obrigatório não informado.",
                "severity": "WARNING",
            },
        )
        self.assertEqual(
            evidence_list[1],
            {
                "material_id": "MAT-001",
                "source": "LLM",
                "issue_type": "AMBIGUOUS_DESCRIPTION",
                "observation": "Descrição com termos ambíguos.",
                "severity": "WARNING",
            },
        )

    def test_round_trip_preserves_valid_workflow_opened_and_recommendation(
        self,
    ) -> None:
        record = workflow_opened_to_record(self.event)
        restored = workflow_opened_from_record(record)

        self.assertEqual(restored, self.event)
        self.assertEqual(restored.event_id, self.event.event_id)
        self.assertEqual(restored.workflow_id, self.event.workflow_id)
        self.assertEqual(restored.opened_at, self.event.opened_at)
        self.assertEqual(restored.recommendation, self.event.recommendation)
        self.assertEqual(
            restored.recommendation.material_id,
            self.event.recommendation.material_id,
        )
        self.assertEqual(
            restored.recommendation.decision,
            self.event.recommendation.decision,
        )
        self.assertEqual(
            restored.recommendation.rationale,
            self.event.recommendation.rationale,
        )
        self.assertEqual(
            restored.recommendation.requires_human_decision,
            self.event.recommendation.requires_human_decision,
        )
        self.assertEqual(
            restored.recommendation.evidence,
            self.event.recommendation.evidence,
        )
        self.assertEqual(
            len(restored.recommendation.evidence),
            len(self.event.recommendation.evidence),
        )
        for original_item, restored_item in zip(
            self.event.recommendation.evidence,
            restored.recommendation.evidence,
            strict=True,
        ):
            self.assertEqual(restored_item, original_item)
            self.assertIsInstance(restored_item.source, EvidenceSource)
            self.assertIsInstance(restored_item.issue_type, IssueType)
            self.assertIsInstance(restored_item.severity, IssueSeverity)

    def test_to_record_rejects_non_workflow_opened_instance(self) -> None:
        cases = ["not-an-event", None, 123, dict(), tuple()]
        for invalid_input in cases:
            with self.subTest(invalid_input=invalid_input):
                with self.assertRaises(ValueError):
                    workflow_opened_to_record(invalid_input)  # type: ignore[arg-type]

    def test_from_record_rejects_non_mapping_input(self) -> None:
        cases = ["not-a-mapping", None, [1, 2, 3], 123, True]
        for invalid_input in cases:
            with self.subTest(invalid_input=invalid_input):
                with self.assertRaises(ValueError):
                    workflow_opened_from_record(invalid_input)  # type: ignore[arg-type]

    def test_from_record_rejects_missing_or_invalid_schema_version(self) -> None:
        valid_record = workflow_opened_to_record(self.event)

        # Missing schema_version
        record_missing = dict(valid_record)
        del record_missing["schema_version"]
        with self.assertRaises(ValueError):
            workflow_opened_from_record(record_missing)

        # Unsupported schema_version number
        record_wrong_version = dict(valid_record)
        record_wrong_version["schema_version"] = 2
        with self.assertRaises(ValueError):
            workflow_opened_from_record(record_wrong_version)

        # Boolean schema_version (bool is subclass of int in Python)
        record_bool_version = dict(valid_record)
        record_bool_version["schema_version"] = True
        with self.assertRaises(ValueError):
            workflow_opened_from_record(record_bool_version)

        # Non-integer schema_version
        record_str_version = dict(valid_record)
        record_str_version["schema_version"] = "1"
        with self.assertRaises(ValueError):
            workflow_opened_from_record(record_str_version)

    def test_from_record_rejects_invalid_or_naive_opened_at(self) -> None:
        valid_record = workflow_opened_to_record(self.event)

        # Naive datetime string (no timezone)
        record_naive = dict(valid_record)
        record_naive["opened_at"] = "2026-08-19T08:30:00"
        with self.assertRaises(ValueError):
            workflow_opened_from_record(record_naive)

        # Non-ISO format string
        record_invalid_str = dict(valid_record)
        record_invalid_str["opened_at"] = "19/08/2026 08:30:00"
        with self.assertRaises(ValueError):
            workflow_opened_from_record(record_invalid_str)

        # Non-string opened_at
        record_non_str = dict(valid_record)
        record_non_str["opened_at"] = 123456789
        with self.assertRaises(ValueError):
            workflow_opened_from_record(record_non_str)

    def test_from_record_rejects_invalid_recommendation_decision(self) -> None:
        valid_record = workflow_opened_to_record(self.event)
        record = dict(valid_record)
        record["recommendation"] = dict(valid_record["recommendation"])
        record["recommendation"]["decision"] = "INVALID_DECISION"

        with self.assertRaises(ValueError):
            workflow_opened_from_record(record)

    def test_from_record_rejects_invalid_requires_human_decision(self) -> None:
        valid_record = workflow_opened_to_record(self.event)

        # requires_human_decision is False
        record_false = dict(valid_record)
        record_false["recommendation"] = dict(valid_record["recommendation"])
        record_false["recommendation"]["requires_human_decision"] = False
        with self.assertRaises(ValueError):
            workflow_opened_from_record(record_false)

        # requires_human_decision is non-bool
        record_non_bool = dict(valid_record)
        record_non_bool["recommendation"] = dict(valid_record["recommendation"])
        record_non_bool["recommendation"]["requires_human_decision"] = "True"
        with self.assertRaises(ValueError):
            workflow_opened_from_record(record_non_bool)

    def test_from_record_rejects_invalid_evidence_fields_and_enums(self) -> None:
        valid_record = workflow_opened_to_record(self.event)

        # Invalid evidence source
        record_bad_source = dict(valid_record)
        record_bad_source["recommendation"] = dict(valid_record["recommendation"])
        record_bad_source["recommendation"]["evidence"] = [
            {
                "material_id": "MAT-001",
                "source": "UNKNOWN_SOURCE",
                "issue_type": "MISSING_CRITICAL_FIELD",
                "observation": "Obs",
                "severity": "WARNING",
            }
        ]
        with self.assertRaises(ValueError):
            workflow_opened_from_record(record_bad_source)

        # Invalid issue_type
        record_bad_issue = dict(valid_record)
        record_bad_issue["recommendation"] = dict(valid_record["recommendation"])
        record_bad_issue["recommendation"]["evidence"] = [
            {
                "material_id": "MAT-001",
                "source": "RULE",
                "issue_type": "NOT_A_REAL_ISSUE_TYPE",
                "observation": "Obs",
                "severity": "WARNING",
            }
        ]
        with self.assertRaises(ValueError):
            workflow_opened_from_record(record_bad_issue)

        # Invalid severity
        record_bad_severity = dict(valid_record)
        record_bad_severity["recommendation"] = dict(valid_record["recommendation"])
        record_bad_severity["recommendation"]["evidence"] = [
            {
                "material_id": "MAT-001",
                "source": "RULE",
                "issue_type": "MISSING_CRITICAL_FIELD",
                "observation": "Obs",
                "severity": "CATASTROPHIC",
            }
        ]
        with self.assertRaises(ValueError):
            workflow_opened_from_record(record_bad_severity)

        # Evidence not a list/sequence of mappings
        record_bad_ev_type = dict(valid_record)
        record_bad_ev_type["recommendation"] = dict(valid_record["recommendation"])
        record_bad_ev_type["recommendation"]["evidence"] = "not-a-list"
        with self.assertRaises(ValueError):
            workflow_opened_from_record(record_bad_ev_type)

    def test_from_record_rejects_non_string_textual_fields(self) -> None:
        # Envelope fields non-string
        for field_name in ("event_id", "workflow_id"):
            with self.subTest(envelope_field=field_name):
                valid_record = workflow_opened_to_record(self.event)
                record = dict(valid_record)
                record[field_name] = 123
                with self.assertRaises(ValueError):
                    workflow_opened_from_record(record)

        # Recommendation fields non-string
        for field_name in ("material_id", "rationale"):
            with self.subTest(recommendation_field=field_name):
                valid_record = workflow_opened_to_record(self.event)
                record = dict(valid_record)
                record["recommendation"] = dict(
                    valid_record["recommendation"]
                )
                record["recommendation"][field_name] = 123
                with self.assertRaises(ValueError):
                    workflow_opened_from_record(record)

        # Evidence fields non-string
        for field_name in ("material_id", "observation"):
            with self.subTest(evidence_field=field_name):
                valid_record = workflow_opened_to_record(self.event)
                record = dict(valid_record)
                record["recommendation"] = dict(
                    valid_record["recommendation"]
                )
                ev_dict = dict(record["recommendation"]["evidence"][0])
                ev_dict[field_name] = 123
                record["recommendation"]["evidence"] = [ev_dict]
                with self.assertRaises(ValueError):
                    workflow_opened_from_record(record)

    def test_from_record_rejects_non_mapping_nested_structures(self) -> None:
        # recommendation is not a Mapping
        for bad_rec in ("not-a-mapping", 123, True, ["not-a-mapping"]):
            with self.subTest(bad_rec=bad_rec):
                valid_record = workflow_opened_to_record(self.event)
                record = dict(valid_record)
                record["recommendation"] = bad_rec
                with self.assertRaises(ValueError):
                    workflow_opened_from_record(record)

        # individual evidence item is not a Mapping
        for bad_item in ("not-a-mapping", 123, True, ["nested-list"]):
            with self.subTest(bad_item=bad_item):
                valid_record = workflow_opened_to_record(self.event)
                record = dict(valid_record)
                record["recommendation"] = dict(
                    valid_record["recommendation"]
                )
                record["recommendation"]["evidence"] = [bad_item]
                with self.assertRaises(ValueError):
                    workflow_opened_from_record(record)

    def test_from_record_rejects_missing_required_fields_in_envelope(self) -> None:
        required_envelope_fields = [
            "event_id",
            "workflow_id",
            "opened_at",
            "recommendation",
        ]
        for field_name in required_envelope_fields:
            with self.subTest(missing_field=field_name):
                valid_record = workflow_opened_to_record(self.event)
                record = dict(valid_record)
                del record[field_name]
                with self.assertRaises(ValueError):
                    workflow_opened_from_record(record)

    def test_from_record_rejects_missing_required_fields_in_recommendation_and_evidence(
        self,
    ) -> None:
        # Missing recommendation fields
        rec_fields = [
            "material_id",
            "decision",
            "rationale",
            "requires_human_decision",
            "evidence",
        ]
        for field_name in rec_fields:
            with self.subTest(missing_rec_field=field_name):
                valid_record = workflow_opened_to_record(self.event)
                record = dict(valid_record)
                record["recommendation"] = dict(
                    valid_record["recommendation"]
                )
                del record["recommendation"][field_name]
                with self.assertRaises(ValueError):
                    workflow_opened_from_record(record)

        # Missing evidence fields
        ev_fields = [
            "material_id",
            "source",
            "issue_type",
            "observation",
            "severity",
        ]
        for field_name in ev_fields:
            with self.subTest(missing_evidence_field=field_name):
                valid_record = workflow_opened_to_record(self.event)
                record = dict(valid_record)
                record["recommendation"] = dict(
                    valid_record["recommendation"]
                )
                ev_dict = dict(record["recommendation"]["evidence"][0])
                del ev_dict[field_name]
                record["recommendation"]["evidence"] = [ev_dict]
                with self.assertRaises(ValueError):
                    workflow_opened_from_record(record)

    def test_from_record_rejects_evidence_material_id_mismatching_recommendation(
        self,
    ) -> None:
        valid_record = workflow_opened_to_record(self.event)
        record = dict(valid_record)
        record["recommendation"] = dict(valid_record["recommendation"])
        bad_evidence = dict(record["recommendation"]["evidence"][0])
        bad_evidence["material_id"] = "MAT-999"
        record["recommendation"]["evidence"] = [bad_evidence]

        with self.assertRaises(ValueError):
            workflow_opened_from_record(record)


if __name__ == "__main__":
    unittest.main()
