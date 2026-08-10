# SPEC 0017 — Consistência de `material_id` na fronteira LLM

## Metadados

| Campo | Valor |
| --- | --- |
| Identificador | `SPEC-0017` |
| Status | `Proposta` |
| Issue relacionada | `#17` — `[QUALITY] Garantir consistência do material_id na fronteira LLM` |
| Responsável | Jakson Pascoal (`Jk-Pascoal`) |
| Data de criação | `2026-08-10` |
| Última atualização | `2026-08-10` |
| Área | Agentes / LLM estruturado / Guardrails |

## 1. Contexto

O Agent Lab Pascoal já possui uma fronteira estruturada para execução de LLM:

```text
MaterialRecord
      ↓
build_governance_prompt()
      ↓
LLMProvider
      ↓
JSON bruto
      ↓
parse_governance_agent_output()
      ↓
GovernanceAgentOutput
      ↓
revisão humana
```

A fronteira garante validade sintática e estrutural da resposta, reutilizando
Pydantic e JSON Schema. Ainda não existe, porém, uma validação explícita que
garanta que o `material_id` retornado corresponde ao mesmo material recebido
como entrada.

A `SPEC-0015` já registrou essa consistência como questão em aberto. A Issue #17
transforma a pendência em um guardrail testável.

## 2. Problema, evidências e impacto

### Problema

Hoje, `analyze_material()` recebe um `MaterialRecord`, chama o provider, valida
o JSON retornado e devolve diretamente um `GovernanceAgentOutput`.

Assim, uma resposta como:

```text
entrada.material_id = MAT-0015
saída.material_id   = MAT-9999
```

pode ser aceita caso o JSON esteja estruturalmente correto.

Esse é um erro semântico de identidade, não um erro de schema.

### Evidências

O estado atual possui:

- `MaterialRecord.material_id` na entrada;
- `GovernanceAgentOutput.material_id` na saída;
- `parse_governance_agent_output()` para validação estrutural;
- `analyze_material()` retornando diretamente o resultado validado;
- 31 testes automatizados aprovados;
- nenhum teste que exija igualdade entre o identificador de entrada e saída;
- nenhuma comparação explícita entre os dois identificadores.

### Impacto

Sem esse guardrail, uma recomendação pode ser:

- sintaticamente válida;
- estruturalmente válida;
- aprovada pelo Pydantic;
- compatível com o JSON Schema;

e ainda assim pertencer a outro material.

Isso ameaça:

- rastreabilidade;
- auditabilidade;
- associação correta de evidências;
- confiança do especialista;
- segurança de decisões futuras sobre PDM/BOM.

## 3. Objetivo

Garantir a invariância:

```text
MaterialRecord.material_id
==
GovernanceAgentOutput.material_id
```

Comportamento esperado:

```text
MAT-0015 → MAT-0015 → aceita
MAT-0015 → MAT-9999 → rejeita
```

O incremento deve permanecer pequeno, determinístico e independente de
fornecedor.

## 4. Escopo

### Incluído

- comparar `material_id` de entrada e saída;
- executar a comparação após o parsing Pydantic;
- rejeitar respostas divergentes;
- criar uma exceção explícita para mismatch;
- criar TDD RED para demonstrar a lacuna;
- criar teste para identidade preservada;
- preservar os 31 testes existentes;
- documentar riscos e limitações.

### Fora do escopo

- OpenAI, Anthropic, Gemini ou outro provider real;
- API keys e chamadas HTTP;
- retry, fallback ou streaming;
- RAG, embeddings, tool calling ou memória;
- validação semântica completa de descrição;
- fabricante ou part number;
- fuzzy matching de IDs;
- normalização automática de `material_id`;
- correção silenciosa do identificador;
- decisão automática de cadastro;
- alteração das regras determinísticas PDM/BOM.

## 5. Responsabilidade humana e limites do agente

O guardrail apenas garante que a saída validada se refere ao mesmo identificador
de material informado na entrada.

Mesmo com identidade correta, a resposta ainda pode:

- interpretar incorretamente o material;
- produzir evidências fracas;
- apresentar confiança mal calibrada;
- sugerir uma decisão inadequada.

Portanto:

```text
identidade correta ≠ análise correta
```

A decisão final continua sob responsabilidade humana.

## 6. Requisitos

### Requisitos funcionais

- `RF-01` — Comparar `material.material_id` com `result.material_id`.
- `RF-02` — Executar a comparação depois de
  `parse_governance_agent_output(raw_json)`.
- `RF-03` — IDs iguais devem permitir retorno normal.
- `RF-04` — IDs diferentes devem interromper o fluxo.
- `RF-05` — A divergência deve gerar uma exceção explícita.
- `RF-06` — A exceção deve permitir identificar esperado e recebido.
- `RF-07` — O código não deve corrigir silenciosamente o ID.
- `RF-08` — O código não deve fazer retry automático.
- `RF-09` — JSON malformado deve continuar sendo rejeitado antes do guardrail.
- `RF-10` — JSON estruturalmente inválido deve continuar sendo rejeitado antes
  do guardrail.

### Requisitos de qualidade

- `RQ-01` — Nenhum SDK externo deve ser adicionado.
- `RQ-02` — Nenhuma chamada de rede deve ocorrer nos testes.
- `RQ-03` — Nenhuma API key deve ser necessária.
- `RQ-04` — O guardrail deve ter escopo mínimo.
- `RQ-05` — Nenhum contrato Pydantic existente deve ser alterado.
- `RQ-06` — Nenhuma regra PDM/BOM deve ser alterada.
- `RQ-07` — Os 31 testes existentes devem permanecer aprovados.
- `RQ-08` — Os novos testes devem ser determinísticos.
- `RQ-09` — Nenhum dado empresarial real deve ser utilizado.
- `RQ-10` — A decisão final deve permanecer humana.

## 7. Proposta técnica

### Visão geral

Fluxo proposto:

```text
MaterialRecord
      ↓
LLMProvider
      ↓
JSON bruto
      ↓
Pydantic
      ↓
GovernanceAgentOutput
      ↓
guardrail de identidade
      ↓
IDs iguais?
  ┌──────┴──────┐
  ↓             ↓
 sim           não
  ↓             ↓
return        exceção
```

### Exceção proposta

Criar em `llm_service.py`:

```python
class MaterialIdentityMismatchError(ValueError):
    ...
```

Mensagem conceitual:

```text
Material identity mismatch: expected 'MAT-0015', received 'MAT-9999'.
```

A exceção específica diferencia falha semântica de falha estrutural.

### Implementação mínima

Mudança conceitual em `analyze_material()`:

```python
result = parse_governance_agent_output(raw_json)

if result.material_id != material.material_id:
    raise MaterialIdentityMismatchError(
        expected=material.material_id,
        received=result.material_id,
    )

return result
```

### Comparação

A comparação será estrita.

Não serão aplicados nesta Issue:

- `strip()`;
- `lower()`;
- `upper()`;
- remoção de hífen;
- regex;
- fuzzy matching.

Se normalização de identificadores for necessária, deverá existir uma Issue
própria.

### Arquivos previstos

- `src/agent_lab/llm_service.py`
  - adicionar exceção;
  - adicionar comparação de identidade.

- `tests/test_llm_service.py`
  - adicionar RED para mismatch;
  - adicionar teste de identidade preservada;
  - preservar testes existentes.

- `docs/specs/0017_llm_material_identity_guardrail.md`
  - esta especificação.

Não são previstas alterações em:

- `src/agent_lab/domain.py`;
- `src/agent_lab/llm_schema.py`;
- `src/agent_lab/llm_provider.py`;
- `src/agent_lab/validator.py`.

## 8. Estratégia de testes e TDD

### Baseline

Baseline já observado em 10/08/2026:

```text
Ran 31 tests
OK
```

### Vermelho

Primeiro criar um teste que demonstre a ausência do guardrail.

Exemplo conceitual:

```python
def test_rejects_output_for_different_material_id(self):
    mismatched_output = {
        **VALID_OUTPUT,
        "material_id": "MAT-9999",
    }
    provider = FakeLLMProvider(json.dumps(mismatched_output))

    with self.assertRaises(MaterialIdentityMismatchError):
        analyze_material(self.material, provider)
```

Antes da implementação, o teste deverá falhar porque o código atual aceita uma
resposta estruturalmente válida com ID divergente.

Evidência esperada:

```text
MaterialIdentityMismatchError not raised
```

### Verde

Implementar apenas:

1. parsing existente;
2. comparação de IDs;
3. exceção em caso de mismatch;
4. retorno normal quando os IDs forem iguais.

### Regressão

Executar:

```powershell
python -m unittest discover -s tests -p "test_llm_service.py" -v
python -m unittest discover -s tests -p "test_*.py" -v
```

### Testes previstos

- `T-01` — ID divergente é rejeitado.
- `T-02` — ID preservado continua aceito.
- `T-03` — erro informa esperado e recebido.
- `T-04` — JSON malformado continua rejeitado.
- `T-05` — JSON estruturalmente inválido continua rejeitado.
- `T-06` — provider continua sendo chamado uma única vez.
- `T-07` — regressão dos 31 testes existentes.

## 9. Gates de qualidade

Antes do Pull Request:

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
git diff --check
git status -sb
```

Com arquivos staged:

```powershell
git diff --cached --check
git diff --cached --stat
git diff --cached
```

No Pull Request:

- GitHub Actions executado;
- `Testes / Python 3.11` aprovado;
- required check satisfeito;
- revisão humana concluída.

Critérios mínimos:

- RED registrado;
- GREEN específico registrado;
- regressão completa aprovada;
- nenhuma chamada de rede;
- nenhuma credencial;
- nenhum SDK novo;
- nenhuma regra PDM/BOM alterada;
- alteração limitada aos arquivos previstos.

## 10. Riscos e limitações

| Risco ou limitação | Probabilidade | Impacto | Mitigação |
| --- | --- | --- | --- |
| Confundir identidade correta com análise correta | Alta | Alto | Documentar o limite do guardrail |
| Transformar `llm_service` em camada de regras de negócio | Média | Médio | Limitar a mudança à identidade |
| Corrigir silenciosamente o ID | Baixa | Alto | Rejeitar mismatch |
| Normalizar IDs implicitamente | Baixa | Médio | Comparação exata |
| Retry esconder falha do provider | Baixa | Médio | Não implementar retry |
| Erro genérico dificultar auditoria | Média | Médio | Usar exceção específica |

### Limitações restantes

Mesmo após o incremento:

- não haverá provider real;
- não haverá avaliação de qualidade semântica;
- fabricante e part number não serão validados;
- evidências poderão estar incorretas;
- não haverá detecção geral de alucinação;
- não haverá retry ou fallback.

## 11. Plano de reversão

Em caso de regressão:

1. não mergear enquanto os checks estiverem falhando;
2. corrigir na branch da Issue;
3. se já mergeado, reverter o Pull Request;
4. restaurar `analyze_material()` ao comportamento anterior;
5. remover a exceção e os testes associados junto com a reversão;
6. executar a suíte completa;
7. confirmar que contratos e regras determinísticas permaneceram intactos.

## 12. Versionamento e release

### Impacto SemVer

`PATCH`

Justificativa: trata-se de correção compatível de uma lacuna de validação em uma
capacidade já existente.

### Publicação prevista

- versão planejada: `Unreleased`;
- criação de tag: não;
- criação de GitHub Release: não;
- atualização do `CHANGELOG.md`: conforme política vigente.

## 13. Critérios de aceite

- [ ] existe validação explícita entre `material_id` de entrada e saída;
- [ ] a comparação ocorre depois da validação Pydantic;
- [ ] identificadores iguais continuam aceitos;
- [ ] identificadores diferentes são rejeitados;
- [ ] existe uma exceção explícita para divergência;
- [ ] a exceção informa esperado e recebido;
- [ ] o identificador não é corrigido silenciosamente;
- [ ] não existe retry automático;
- [ ] JSON malformado continua rejeitado;
- [ ] JSON estruturalmente inválido continua rejeitado;
- [ ] a regra continua independente de provider;
- [ ] nenhum SDK externo foi adicionado;
- [ ] nenhuma chamada de rede foi necessária;
- [ ] nenhum contrato Pydantic foi alterado;
- [ ] existe TDD RED demonstrando a ausência do guardrail;
- [ ] existe teste para divergência de identidade;
- [ ] existe teste para identidade preservada;
- [ ] os 31 testes anteriores continuam aprovados;
- [ ] os novos testes estão aprovados;
- [ ] GitHub Actions / Python 3.11 está aprovado;
- [ ] nenhum segredo ou credencial foi adicionado;
- [ ] nenhum dado empresarial real foi utilizado;
- [ ] nenhuma regra determinística PDM/BOM foi alterada;
- [ ] riscos e limitações estão registrados;
- [ ] a decisão final permanece humana;
- [ ] o Pull Request referencia a Issue #17 e esta SPEC.

## 14. Questões em aberto

1. **Nome da exceção**
   - proposta: `MaterialIdentityMismatchError`.

2. **Local da exceção**
   - proposta: `src/agent_lab/llm_service.py`.

3. **Atributos do erro**
   - avaliar se `expected` e `received` devem ser atributos;
   - no mínimo, ambos devem estar disponíveis na mensagem.

4. **Comparação estrita**
   - decisão inicial: igualdade exata;
   - qualquer normalização futura exige Issue própria.

## 15. Histórico de decisões

| Data | Decisão | Motivo | Responsável |
| --- | --- | --- | --- |
| `2026-08-10` | Criar `SPEC-0017` | Transformar pendência da `SPEC-0015` em guardrail testável | Jakson Pascoal |
| `2026-08-10` | Tratar `material_id` como invariância semântica | Identidade do objeto é pré-condição de rastreabilidade | Jakson Pascoal |
| `2026-08-10` | Executar guardrail após Pydantic | Primeiro estrutura, depois semântica de identidade | Jakson Pascoal |
| `2026-08-10` | Rejeitar mismatch em vez de corrigir | Correção silenciosa esconderia erro do provider | Jakson Pascoal |
| `2026-08-10` | Não implementar retry | Mantém escopo mínimo e determinístico | Jakson Pascoal |
| `2026-08-10` | Usar comparação estrita | Identidade deve ser explícita | Jakson Pascoal |

## 16. Rastreabilidade

Esta SPEC implementa:

```text
Issue #17
[QUALITY] Garantir consistência do material_id na fronteira LLM
```

O Pull Request deverá conter:

```text
Closes #17
```

e referenciar:

```text
SPEC-0017
docs/specs/0017_llm_material_identity_guardrail.md
```

Fluxo previsto:

```text
Issue #17
   ↓
SPEC-0017
   ↓
branch
   ↓
TDD RED
   ↓
guardrail mínimo
   ↓
GREEN
   ↓
regressão
   ↓
PR
   ↓
Actions
   ↓
review
   ↓
merge
```
