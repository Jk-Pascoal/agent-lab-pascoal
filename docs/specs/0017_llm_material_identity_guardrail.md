# SPEC 0017 — Consistência de `material_id` na fronteira LLM

## Metadados

| Campo | Valor |
| --- | --- |
| Identificador | `SPEC-0017` |
| Status | `Aprovada` |
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
Pydantic e JSON Schema. A Issue #17 adiciona uma garantia adicional: a saída
validada precisa continuar se referindo ao mesmo material recebido como entrada.

A `SPEC-0015` já havia registrado essa consistência como questão em aberto. A
Issue #17 transforma a pendência em um guardrail testável e auditável.

## 2. Problema, evidências e impacto

### Problema

`analyze_material()` recebe um `MaterialRecord`, chama o provider, valida o JSON
retornado e produz um `GovernanceAgentOutput`.

Antes desta Issue, uma resposta como:

```text
entrada.material_id = MAT-0015
saída.material_id   = MAT-9999
```

podia ser aceita caso o JSON estivesse estruturalmente correto.

Esse é um erro semântico de identidade, não um erro de schema.

### Evidências

Estado observado antes da implementação:

- `MaterialRecord.material_id` existia na entrada;
- `GovernanceAgentOutput.material_id` existia na saída;
- `parse_governance_agent_output()` validava a estrutura;
- `analyze_material()` retornava o resultado validado sem comparar os IDs;
- baseline local em `2026-08-10`: `31/31` testes aprovados;
- nenhum teste exigia igualdade entre o identificador de entrada e saída.

Evidência do RED:

```text
Ran 8 tests in 0.008s
FAILED (failures=1)

AssertionError: ValueError not raised
```

O RED comprovou que uma resposta estruturalmente válida com `material_id`
divergente era aceita.

### Impacto

Sem o guardrail, uma recomendação poderia ser:

- sintaticamente válida;
- estruturalmente válida;
- aprovada pelo Pydantic;
- compatível com o JSON Schema;

e ainda assim pertencer a outro material.

Isso ameaçava:

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

Comportamento esperado e implementado:

```text
MAT-0015 → MAT-0015 → aceita
MAT-0015 → MAT-9999 → rejeita
```

O incremento permanece pequeno, determinístico e independente de fornecedor.

## 4. Escopo

### Incluído

- comparar `material_id` de entrada e saída;
- executar a comparação após o parsing Pydantic;
- rejeitar respostas divergentes;
- criar uma exceção explícita para mismatch;
- criar TDD RED para demonstrar a lacuna;
- criar teste para identidade preservada;
- criar teste para auditabilidade de `expected` e `received`;
- criar teste garantindo ausência de retry;
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

## 7. Implementação técnica

### Visão geral

Fluxo implementado:

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

### Exceção

Foi criada em `src/agent_lab/llm_service.py`:

```python
class MaterialIdentityMismatchError(ValueError):
    ...
```

A exceção preserva:

- `expected`;
- `received`.

Mensagem observável:

```text
Material identity mismatch: expected 'MAT-0015', received 'MAT-9999'.
```

### Regra implementada

Após o parsing estrutural:

```python
result = parse_governance_agent_output(raw_json)
```

a fronteira compara:

```python
result.material_id != material.material_id
```

Quando houver divergência, lança `MaterialIdentityMismatchError`.

Quando houver igualdade, retorna normalmente o `GovernanceAgentOutput`.

### Comparação

A comparação é estrita.

Não são aplicados:

- `strip()`;
- `lower()`;
- `upper()`;
- remoção de hífen;
- regex;
- fuzzy matching.

### Arquivos alterados

- `src/agent_lab/llm_service.py`
- `tests/test_llm_service.py`

### Arquivos não alterados

- `src/agent_lab/domain.py`;
- `src/agent_lab/llm_schema.py`;
- `src/agent_lab/llm_provider.py`;
- `src/agent_lab/validator.py`;
- regras determinísticas PDM/BOM;
- workflows do GitHub Actions.

## 8. Estratégia de testes e TDD

### Baseline

Baseline observado em `2026-08-10`:

```text
Ran 31 tests
OK
```

### RED

Foi adicionado primeiro um teste para `material_id` divergente.

Resultado observado:

```text
Ran 8 tests in 0.008s
FAILED (failures=1)

AssertionError: ValueError not raised
```

Isso demonstrou que o guardrail ainda não existia.

### GREEN inicial

Após a implementação mínima:

```text
Ran 8 tests in 0.008s
OK
```

Regressão inicial:

```text
Ran 32 tests in 0.029s
OK
```

### GREEN final

Foram adicionados testes adicionais para:

- auditabilidade de `expected`;
- auditabilidade de `received`;
- ausência de retry automático.

Resultado final observado:

```text
Ran 34 tests in 0.026s
OK
```

### Testes da Issue #17

- `T-01` — ID divergente é rejeitado. ✅
- `T-02` — ID preservado continua aceito. ✅
- `T-03` — erro informa esperado e recebido. ✅
- `T-04` — JSON malformado continua rejeitado. ✅
- `T-05` — JSON estruturalmente inválido continua rejeitado. ✅
- `T-06` — provider continua sendo chamado uma única vez. ✅
- `T-07` — regressão dos 31 testes existentes. ✅

## 9. Gates de qualidade

### Gates locais concluídos

- baseline `31/31`; ✅
- RED comportamental registrado; ✅
- GREEN específico registrado; ✅
- regressão completa `34/34`; ✅
- nenhum SDK novo; ✅
- nenhuma chamada de rede; ✅
- nenhuma credencial; ✅
- nenhuma regra PDM/BOM alterada; ✅
- alteração limitada aos arquivos previstos; ✅
- revisão local antes do commit; ✅

### Gate remoto pendente

No Pull Request ainda será necessário:

- GitHub Actions executado;
- `Testes / Python 3.11` aprovado;
- required check satisfeito;
- revisão final;
- merge na `main`.

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

- não há provider real;
- não há avaliação de qualidade semântica completa;
- fabricante e part number não são validados;
- evidências ainda podem estar incorretas;
- não há detecção geral de alucinação;
- não há retry ou fallback.

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

- [x] existe validação explícita entre `material_id` de entrada e saída;
- [x] a comparação ocorre depois da validação Pydantic;
- [x] identificadores iguais continuam aceitos;
- [x] identificadores diferentes são rejeitados;
- [x] existe uma exceção explícita para divergência;
- [x] a exceção informa esperado e recebido;
- [x] o identificador não é corrigido silenciosamente;
- [x] não existe retry automático;
- [x] JSON malformado continua rejeitado;
- [x] JSON estruturalmente inválido continua rejeitado;
- [x] a regra continua independente de provider;
- [x] nenhum SDK externo foi adicionado;
- [x] nenhuma chamada de rede foi necessária;
- [x] nenhum contrato Pydantic foi alterado;
- [x] existe TDD RED demonstrando a ausência do guardrail;
- [x] existe teste para divergência de identidade;
- [x] existe teste para identidade preservada;
- [x] os 31 testes anteriores continuam aprovados;
- [x] os novos testes estão aprovados;
- [ ] GitHub Actions / Python 3.11 está aprovado;
- [x] nenhum segredo ou credencial foi adicionado;
- [x] nenhum dado empresarial real foi utilizado;
- [x] nenhuma regra determinística PDM/BOM foi alterada;
- [x] riscos e limitações estão registrados;
- [x] a decisão final permanece humana;
- [ ] o Pull Request referencia a Issue #17 e esta SPEC.

## 14. Questões em aberto

1. **Provider real**
   - permanece fora desta Issue;
   - será tratado em incremento posterior.

2. **Normalização de identificadores**
   - comparação atual é estrita;
   - qualquer normalização futura exige Issue própria.

3. **Outros guardrails semânticos**
   - fabricante, part number, descrição e evidências permanecem candidatos
     futuros, caso surjam evidências de risco.

## 15. Histórico de decisões

| Data | Decisão | Motivo | Responsável |
| --- | --- | --- | --- |
| `2026-08-10` | Criar `SPEC-0017` | Transformar pendência da `SPEC-0015` em guardrail testável | Jakson Pascoal |
| `2026-08-10` | Tratar `material_id` como invariância semântica | Identidade do objeto é pré-condição de rastreabilidade | Jakson Pascoal |
| `2026-08-10` | Executar guardrail após Pydantic | Primeiro estrutura, depois semântica de identidade | Jakson Pascoal |
| `2026-08-10` | Rejeitar mismatch em vez de corrigir | Correção silenciosa esconderia erro do provider | Jakson Pascoal |
| `2026-08-10` | Não implementar retry | Mantém escopo mínimo e determinístico | Jakson Pascoal |
| `2026-08-10` | Usar comparação estrita | Identidade deve ser explícita | Jakson Pascoal |
| `2026-08-10` | Registrar RED comportamental | `ValueError not raised` provou que a saída de outro material era aceita | Jakson Pascoal |
| `2026-08-10` | Implementar `MaterialIdentityMismatchError` | Separar erro semântico de identidade de erro estrutural | Jakson Pascoal |
| `2026-08-10` | Validar GREEN final com 34 testes | Os 31 testes anteriores e 3 novos testes ficaram aprovados | Jakson Pascoal |
| `2026-08-10` | Commitar implementação funcional | Commit `7e1c992` registra o guardrail e seus testes | Jakson Pascoal |

## 16. Rastreabilidade

### Issue

```text
Issue #17
[QUALITY] Garantir consistência do material_id na fronteira LLM
```

### Commits já registrados

```text
ab4487a  Documenta guardrail de identidade do material
7e1c992  Adiciona guardrail de identidade do material
```

### Pull Request

O Pull Request deverá conter:

```text
Closes #17
```

e referenciar:

```text
SPEC-0017
docs/specs/0017_llm_material_identity_guardrail.md
```

### Fluxo

```text
Issue #17                 ✅
   ↓
SPEC-0017                 ✅
   ↓
branch                    ✅
   ↓
TDD RED                   ✅
   ↓
guardrail mínimo          ✅
   ↓
GREEN 34/34               ✅
   ↓
commit funcional          ✅
   ↓
atualização da SPEC       ← agora
   ↓
push
   ↓
Pull Request
   ↓
GitHub Actions
   ↓
review
   ↓
merge
```
