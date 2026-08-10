import json
import unittest

from pydantic import ValidationError

from agent_lab.domain import MaterialRecord
from agent_lab.llm_schema import (
    GovernanceAgentOutput,
    governance_agent_output_schema,
)
from agent_lab.llm_service import (
    analyze_material,
    build_governance_prompt,
)


VALID_OUTPUT = {
    "material_id": "MAT-0015",
    "decision": "REVIEW",
    "confidence": 0.84,
    "issues": ["AMBIGUOUS_DESCRIPTION"],
    "summary": "O material requer revisão humana.",
    "evidence": ["A descrição curta não informa especificação técnica suficiente."],
}


class FakeLLMProvider:
    """Provider controlado para testar a fronteira sem rede ou credenciais."""

    def __init__(self, response: str) -> None:
        self.response = response
        self.last_prompt: str | None = None
        self.last_schema: dict[str, object] | None = None
        self.calls = 0

    def generate(
        self,
        *,
        prompt: str,
        response_schema: dict[str, object],
    ) -> str:
        self.calls += 1
        self.last_prompt = prompt
        self.last_schema = response_schema
        return self.response


class GovernanceLLMServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.material = MaterialRecord(
            material_id="MAT-0015",
            description_short="BOMBA CENTRIFUGA",
            long_description="Bomba centrífuga para água de processo",
            unit="UN",
            manufacturer="FABRICANTE TESTE",
            manufacturer_part_number="BC-100",
            material_group="BOMBAS",
            status="ATIVO",
        )

    def test_analyze_material_returns_validated_output(self) -> None:
        provider = FakeLLMProvider(json.dumps(VALID_OUTPUT))

        result = analyze_material(self.material, provider)

        self.assertIsInstance(result, GovernanceAgentOutput)
        self.assertEqual(result.material_id, "MAT-0015")
        self.assertEqual(result.decision.value, "REVIEW")
        self.assertEqual(result.confidence, 0.84)
        self.assertEqual(provider.calls, 1)

    def test_provider_receives_material_fields_in_prompt(self) -> None:
        provider = FakeLLMProvider(json.dumps(VALID_OUTPUT))

        analyze_material(self.material, provider)

        self.assertIsNotNone(provider.last_prompt)
        assert provider.last_prompt is not None

        expected_values = (
            "MAT-0015",
            "BOMBA CENTRIFUGA",
            "Bomba centrífuga para água de processo",
            "UN",
            "FABRICANTE TESTE",
            "BC-100",
            "BOMBAS",
            "ATIVO",
        )

        for value in expected_values:
            with self.subTest(value=value):
                self.assertIn(value, provider.last_prompt)

    def test_provider_receives_existing_json_schema(self) -> None:
        provider = FakeLLMProvider(json.dumps(VALID_OUTPUT))

        analyze_material(self.material, provider)

        self.assertEqual(
            provider.last_schema,
            governance_agent_output_schema(),
        )

    def test_malformed_json_from_provider_is_rejected(self) -> None:
        provider = FakeLLMProvider(
            '{"material_id": "MAT-0015",'
        )

        with self.assertRaises(ValidationError):
            analyze_material(self.material, provider)

    def test_structurally_invalid_json_from_provider_is_rejected(self) -> None:
        invalid_output = {
            **VALID_OUTPUT,
            "confidence": 1.50,
        }
        provider = FakeLLMProvider(json.dumps(invalid_output))

        with self.assertRaises(ValidationError):
            analyze_material(self.material, provider)

    def test_prompt_is_deterministic_for_same_material(self) -> None:
        first_prompt = build_governance_prompt(self.material)
        second_prompt = build_governance_prompt(self.material)

        self.assertEqual(first_prompt, second_prompt)

    def test_prompt_preserves_empty_material_fields(self) -> None:
        material = MaterialRecord(
            material_id="MAT-EMPTY",
            description_short="ITEM SEM DETALHES",
        )

        prompt = build_governance_prompt(material)

        expected_field_names = (
            "material_id",
            "description_short",
            "long_description",
            "unit",
            "manufacturer",
            "manufacturer_part_number",
            "material_group",
            "status",
        )

        for field_name in expected_field_names:
            with self.subTest(field_name=field_name):
                self.assertIn(field_name, prompt)


if __name__ == "__main__":
    unittest.main()
