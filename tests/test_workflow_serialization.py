from __future__ import annotations

import unittest
from datetime import datetime, timezone

from agent_lab.decision import DecisionRecommendation
from agent_lab.domain import GovernanceDecision, IssueSeverity, IssueType
from agent_lab.evidence import EvidenceSource, GovernanceEvidence
from agent_lab.human_review import (
    CorrectionRequest,
    HumanDecision,
    HumanReview,
    VerifiedSpecialistIdentity,
)
from agent_lab.workflow_events import WorkflowConcluded, WorkflowOpened
from agent_lab.workflow_serialization import (
    SCHEMA_VERSION_V1,
    workflow_concluded_from_record,
    workflow_concluded_to_record,
    workflow_event_from_record,
    workflow_event_to_record,
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

        self.verified_at = datetime(
            2026,
            8,
            19,
            8,
            0,
            0,
            tzinfo=timezone.utc,
        )
        self.reviewed_at = datetime(
            2026,
            8,
            19,
            9,
            15,
            0,
            tzinfo=timezone.utc,
        )
        self.identity = VerifiedSpecialistIdentity(
            specialist_id="spec-042",
            identity_provider="CORP_IDP",
            identity_subject="analyst@company.com",
            verification_id="ver-auth-987",
            verified_at=self.verified_at,
        )
        self.corrections = (
            CorrectionRequest(
                field_name="description",
                reason="Texto fora do padrão PDM",
                suggested_value="PARAFUSO SEXTAVADO M8X20 A2-70",
            ),
            CorrectionRequest(
                field_name="base_unit",
                reason="Unidade inválida no cadastro de entrada",
                suggested_value="UN",
            ),
        )
        self.concluded_review = HumanReview(
            review_id="rev-mat-001-001",
            material_id="MAT-001",
            system_recommendation=GovernanceDecision.REVIEW,
            human_decision=HumanDecision.REQUEST_CORRECTION,
            reviewer_identity=self.identity,
            reviewed_at=self.reviewed_at,
            justification="Correção necessária na descrição curta e unidade de medida.",
            corrections=self.corrections,
        )
        self.concluded_event = WorkflowConcluded(
            event_id="evt-conc-001",
            workflow_id="wf-mat-001-01",
            review=self.concluded_review,
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

    def test_workflow_concluded_serialization_produces_expected_record(
        self,
    ) -> None:
        record = workflow_concluded_to_record(self.concluded_event)

        self.assertIsInstance(record, dict)
        self.assertEqual(record["schema_version"], 1)
        self.assertEqual(record["event_type"], "WORKFLOW_CONCLUDED")
        self.assertEqual(record["event_id"], "evt-conc-001")
        self.assertEqual(record["workflow_id"], "wf-mat-001-01")
        self.assertNotIn("concluded_at", record)

        review_dict = record["review"]
        self.assertIsInstance(review_dict, dict)
        self.assertEqual(review_dict["review_id"], "rev-mat-001-001")
        self.assertEqual(review_dict["material_id"], "MAT-001")
        self.assertEqual(review_dict["system_recommendation"], "REVIEW")
        self.assertEqual(review_dict["human_decision"], "REQUEST_CORRECTION")
        self.assertEqual(
            review_dict["reviewed_at"], "2026-08-19T09:15:00+00:00"
        )
        self.assertEqual(
            review_dict["justification"],
            "Correção necessária na descrição curta e unidade de medida.",
        )

        identity_dict = review_dict["reviewer_identity"]
        self.assertIsInstance(identity_dict, dict)
        self.assertEqual(identity_dict["specialist_id"], "spec-042")
        self.assertEqual(identity_dict["identity_provider"], "CORP_IDP")
        self.assertEqual(
            identity_dict["identity_subject"], "analyst@company.com"
        )
        self.assertEqual(identity_dict["verification_id"], "ver-auth-987")
        self.assertEqual(
            identity_dict["verified_at"], "2026-08-19T08:00:00+00:00"
        )

        corrections_list = review_dict["corrections"]
        self.assertIsInstance(corrections_list, list)
        self.assertEqual(len(corrections_list), 2)
        self.assertEqual(
            corrections_list[0],
            {
                "field_name": "description",
                "reason": "Texto fora do padrão PDM",
                "suggested_value": "PARAFUSO SEXTAVADO M8X20 A2-70",
            },
        )
        self.assertEqual(
            corrections_list[1],
            {
                "field_name": "base_unit",
                "reason": "Unidade inválida no cadastro de entrada",
                "suggested_value": "UN",
            },
        )

    def test_workflow_concluded_round_trip_preserves_full_human_review(
        self,
    ) -> None:
        record = workflow_concluded_to_record(self.concluded_event)
        restored = workflow_concluded_from_record(record)

        self.assertEqual(restored, self.concluded_event)
        self.assertEqual(restored.event_id, self.concluded_event.event_id)
        self.assertEqual(restored.workflow_id, self.concluded_event.workflow_id)

        # Review attributes
        self.assertEqual(
            restored.review.review_id, self.concluded_review.review_id
        )
        self.assertEqual(
            restored.review.material_id, self.concluded_review.material_id
        )
        self.assertEqual(
            restored.review.system_recommendation,
            self.concluded_review.system_recommendation,
        )
        self.assertEqual(
            restored.review.human_decision,
            self.concluded_review.human_decision,
        )
        self.assertEqual(
            restored.review.reviewed_at, self.concluded_review.reviewed_at
        )
        self.assertEqual(
            restored.review.justification, self.concluded_review.justification
        )

        # Identity attributes
        self.assertEqual(
            restored.review.reviewer_identity.specialist_id,
            self.identity.specialist_id,
        )
        self.assertEqual(
            restored.review.reviewer_identity.identity_provider,
            self.identity.identity_provider,
        )
        self.assertEqual(
            restored.review.reviewer_identity.identity_subject,
            self.identity.identity_subject,
        )
        self.assertEqual(
            restored.review.reviewer_identity.verification_id,
            self.identity.verification_id,
        )
        self.assertEqual(
            restored.review.reviewer_identity.verified_at,
            self.identity.verified_at,
        )

        # Corrections collection and items
        self.assertEqual(
            restored.review.corrections, self.concluded_review.corrections
        )
        self.assertEqual(
            len(restored.review.corrections), len(self.corrections)
        )
        for original_corr, restored_corr in zip(
            self.corrections, restored.review.corrections, strict=True
        ):
            self.assertEqual(restored_corr, original_corr)
            self.assertEqual(restored_corr.field_name, original_corr.field_name)
            self.assertEqual(restored_corr.reason, original_corr.reason)
            self.assertEqual(
                restored_corr.suggested_value, original_corr.suggested_value
            )

    def test_workflow_concluded_to_record_rejects_non_workflow_concluded_instance(
        self,
    ) -> None:
        cases = ["not-an-event", None, 123, dict(), tuple(), self.event]
        for invalid_input in cases:
            with self.subTest(invalid_input=invalid_input):
                with self.assertRaises(ValueError):
                    workflow_concluded_to_record(invalid_input)  # type: ignore[arg-type]

    def test_workflow_event_to_record_dispatches_workflow_opened_preserving_legacy_format(
        self,
    ) -> None:
        record = workflow_event_to_record(self.event)
        self.assertEqual(record, workflow_opened_to_record(self.event))
        self.assertNotIn("event_type", record)

    def test_workflow_event_to_record_dispatches_workflow_concluded(
        self,
    ) -> None:
        record = workflow_event_to_record(self.concluded_event)
        self.assertEqual(
            record, workflow_concluded_to_record(self.concluded_event)
        )
        self.assertEqual(record["event_type"], "WORKFLOW_CONCLUDED")

    def test_workflow_event_to_record_rejects_unknown_object(self) -> None:
        cases = ["not-an-event", None, 123, dict(), tuple(), object()]
        for invalid_input in cases:
            with self.subTest(invalid_input=invalid_input):
                with self.assertRaises(ValueError):
                    workflow_event_to_record(invalid_input)  # type: ignore[arg-type]

    def test_workflow_event_from_record_reads_legacy_workflow_opened_when_event_type_absent(
        self,
    ) -> None:
        record = workflow_opened_to_record(self.event)
        self.assertNotIn("event_type", record)

        restored = workflow_event_from_record(record)
        self.assertEqual(restored, self.event)
        self.assertIsInstance(restored, WorkflowOpened)

    def test_workflow_event_from_record_reads_workflow_concluded_when_event_type_is_workflow_concluded(
        self,
    ) -> None:
        record = workflow_concluded_to_record(self.concluded_event)
        self.assertEqual(record["event_type"], "WORKFLOW_CONCLUDED")

        restored = workflow_event_from_record(record)
        self.assertEqual(restored, self.concluded_event)
        self.assertIsInstance(restored, WorkflowConcluded)

    def test_workflow_event_from_record_explicitly_rejects_event_type_workflow_opened(
        self,
    ) -> None:
        record = dict(workflow_opened_to_record(self.event))
        record["event_type"] = "WORKFLOW_OPENED"

        with self.assertRaises(ValueError):
            workflow_event_from_record(record)

    def test_workflow_event_from_record_rejects_explicit_null_event_type_on_legacy_opened_payload(
        self,
    ) -> None:
        record = dict(workflow_opened_to_record(self.event))
        record["event_type"] = None

        with self.assertRaises(ValueError):
            workflow_event_from_record(record)

    def test_workflow_event_from_record_rejects_other_invalid_event_types(
        self,
    ) -> None:
        base_record = workflow_concluded_to_record(self.concluded_event)
        cases = ["", "UNKNOWN", "WORKFLOW_CLOSED", 123, True, [], {}]
        for invalid_type in cases:
            with self.subTest(invalid_type=invalid_type):
                record = dict(base_record)
                record["event_type"] = invalid_type
                with self.assertRaises(ValueError):
                    workflow_event_from_record(record)

    def test_workflow_event_from_record_rejects_non_mapping_input(
        self,
    ) -> None:
        cases = ["str", None, [1, 2], 123, True]
        for invalid_input in cases:
            with self.subTest(invalid_input=invalid_input):
                with self.assertRaises(ValueError):
                    workflow_event_from_record(invalid_input)  # type: ignore[arg-type]

    def test_workflow_concluded_from_record_rejects_missing_review_structural_fields(
        self,
    ) -> None:
        valid_record = workflow_concluded_to_record(self.concluded_event)
        review_fields = [
            "review_id",
            "material_id",
            "system_recommendation",
            "human_decision",
            "reviewer_identity",
            "reviewed_at",
            "justification",
            "corrections",
        ]
        for field_name in review_fields:
            with self.subTest(missing_review_field=field_name):
                record = dict(valid_record)
                record["review"] = dict(valid_record["review"])
                del record["review"][field_name]
                with self.assertRaises(ValueError):
                    workflow_concluded_from_record(record)

        # Decision de schema: justification=None and corrections=[] are valid when keys are present
        approve_review = HumanReview(
            review_id="rev-app-001",
            material_id="MAT-001",
            system_recommendation=GovernanceDecision.APPROVE,
            human_decision=HumanDecision.APPROVE,
            reviewer_identity=self.identity,
            reviewed_at=self.reviewed_at,
            justification=None,
            corrections=(),
        )
        approve_event = WorkflowConcluded(
            event_id="evt-app-001",
            workflow_id="wf-mat-001-01",
            review=approve_review,
        )
        approve_record = workflow_concluded_to_record(approve_event)
        self.assertIsNone(approve_record["review"]["justification"])
        self.assertEqual(approve_record["review"]["corrections"], [])
        restored_approve = workflow_concluded_from_record(approve_record)
        self.assertEqual(restored_approve, approve_event)

    def test_workflow_concluded_from_record_rejects_missing_reviewer_identity_fields(
        self,
    ) -> None:
        valid_record = workflow_concluded_to_record(self.concluded_event)
        identity_fields = [
            "specialist_id",
            "identity_provider",
            "identity_subject",
            "verification_id",
            "verified_at",
        ]
        for field_name in identity_fields:
            with self.subTest(missing_identity_field=field_name):
                record = dict(valid_record)
                record["review"] = dict(valid_record["review"])
                record["review"]["reviewer_identity"] = dict(
                    valid_record["review"]["reviewer_identity"]
                )
                del record["review"]["reviewer_identity"][field_name]
                with self.assertRaises(ValueError):
                    workflow_concluded_from_record(record)

    def test_workflow_concluded_from_record_rejects_invalid_corrections_structure(
        self,
    ) -> None:
        valid_record = workflow_concluded_to_record(self.concluded_event)

        # corrections non-list
        record_bad_corrections = dict(valid_record)
        record_bad_corrections["review"] = dict(valid_record["review"])
        record_bad_corrections["review"]["corrections"] = "not-a-list"
        with self.assertRaises(ValueError):
            workflow_concluded_from_record(record_bad_corrections)

        # item non-mapping
        record_bad_item = dict(valid_record)
        record_bad_item["review"] = dict(valid_record["review"])
        record_bad_item["review"]["corrections"] = ["not-a-mapping"]
        with self.assertRaises(ValueError):
            workflow_concluded_from_record(record_bad_item)

        # missing fields in correction item
        corr_fields = ["field_name", "reason", "suggested_value"]
        for field_name in corr_fields:
            with self.subTest(missing_corr_field=field_name):
                record = dict(valid_record)
                record["review"] = dict(valid_record["review"])
                item = dict(valid_record["review"]["corrections"][0])
                del item[field_name]
                record["review"]["corrections"] = [item]
                with self.assertRaises(ValueError):
                    workflow_concluded_from_record(record)

        # suggested_value is None but key is present -> valid
        record_null_sug = dict(valid_record)
        record_null_sug["review"] = dict(valid_record["review"])
        item_null_sug = dict(valid_record["review"]["corrections"][0])
        item_null_sug["suggested_value"] = None
        record_null_sug["review"]["corrections"] = [item_null_sug]

        corr_null_sug = (
            CorrectionRequest(
                field_name=item_null_sug["field_name"],
                reason=item_null_sug["reason"],
                suggested_value=None,
            ),
        )
        rev_null_sug = HumanReview(
            review_id=self.concluded_review.review_id,
            material_id=self.concluded_review.material_id,
            system_recommendation=self.concluded_review.system_recommendation,
            human_decision=self.concluded_review.human_decision,
            reviewer_identity=self.concluded_review.reviewer_identity,
            reviewed_at=self.concluded_review.reviewed_at,
            justification=self.concluded_review.justification,
            corrections=corr_null_sug,
        )
        evt_null_sug = WorkflowConcluded(
            event_id=self.concluded_event.event_id,
            workflow_id=self.concluded_event.workflow_id,
            review=rev_null_sug,
        )
        restored = workflow_concluded_from_record(record_null_sug)
        self.assertEqual(restored, evt_null_sug)

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
