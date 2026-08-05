import json
import unittest

from pydantic import ValidationError

from agent_lab.llm_schema import (
    GovernanceAgentOutput,
    governance_agent_output_schema,
    parse_governance_agent_output,
)


VALID_OUTPUT = {
    "material_id": "MAT-0002",
    "decision": "REVIEW",
    "confidence": 0.82,
    "issues": ["POSSIBLE_DUPLICATE"],
    "summary": "O material pode estar duplicado.",
    "evidence": ["Descrição e fabricante semelhantes."],
}


class GovernanceAgentOutputTests(unittest.TestCase):
    def test_accepts_valid_structured_output(self) -> None:
        output = GovernanceAgentOutput.model_validate(VALID_OUTPUT)

        self.assertEqual(output.material_id, "MAT-0002")
        self.assertEqual(output.decision.value, "REVIEW")
        self.assertEqual(
            output.issues[0].value,
            "POSSIBLE_DUPLICATE",
        )

    def test_parses_valid_json_output(self) -> None:
        raw_json = json.dumps(VALID_OUTPUT)

        output = parse_governance_agent_output(raw_json)

        self.assertEqual(output.material_id, "MAT-0002")
        self.assertEqual(output.decision.value, "REVIEW")

    def test_rejects_malformed_json(self) -> None:
        malformed_json = '{"material_id": "MAT-0002",'

        with self.assertRaises(ValidationError):
            parse_governance_agent_output(malformed_json)

    def test_rejects_confidence_above_one(self) -> None:
        invalid_output = {
            **VALID_OUTPUT,
            "confidence": 1.10,
        }

        with self.assertRaises(ValidationError):
            GovernanceAgentOutput.model_validate(invalid_output)

    def test_rejects_unexpected_fields(self) -> None:
        invalid_output = {
            **VALID_OUTPUT,
            "invented_field": "informação não permitida",
        }

        with self.assertRaises(ValidationError):
            GovernanceAgentOutput.model_validate(invalid_output)

    def test_exports_schema_with_required_fields(self) -> None:
        schema = governance_agent_output_schema()

        expected_required_fields = {
            "material_id",
            "decision",
            "confidence",
            "issues",
            "summary",
            "evidence",
        }

        self.assertEqual(
            set(schema["required"]),
            expected_required_fields,
        )
        self.assertFalse(schema["additionalProperties"])

    def test_schema_preserves_domain_constraints(self) -> None:
        schema = governance_agent_output_schema()

        confidence_schema = schema["properties"]["confidence"]
        decision_schema = schema["$defs"]["GovernanceDecision"]

        self.assertEqual(confidence_schema["minimum"], 0.0)
        self.assertEqual(confidence_schema["maximum"], 1.0)
        self.assertEqual(
            decision_schema["enum"],
            ["APPROVE", "REVIEW", "REJECT"],
        )


if __name__ == "__main__":
    unittest.main()