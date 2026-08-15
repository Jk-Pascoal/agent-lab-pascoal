# SPEC 0033 — Human-in-the-Loop v1 e trilha de auditoria

- **Status:** Implementada
- **Issue:** #33
- **Branch:** `feat/33-human-in-the-loop-v1`
- **Data:** 2026-08-15
- **Escopo:** domínio, serviço de aplicação, auditoria em memória e testes

## 1. Contexto

O Agent Lab Pascoal já transforma regras determinísticas e evidências estruturadas em recomendações de governança `APPROVE`, `REVIEW` e `REJECT`. A recomendação automática, contudo, não representa a decisão final sobre um cadastro PDM/BOM.

Em um processo real de Master Data, a autoridade decisória permanece com o especialista aprovador. O sistema deve preservar o que recomendou, registrar o que o humano decidiu e manter evidências suficientes para reconstruir o percurso entre os dois estados.

Esta SPEC define a primeira versão dessa camada de Human-in-the-Loop.

## 2. Objetivo

Implementar contratos imutáveis e auditáveis para registrar a revisão humana de uma recomendação automática, garantindo:

- separação entre recomendação do sistema e decisão final humana;
- identificação do especialista responsável;
- registro temporal da ação;
- justificativa quando exigida pelo domínio;
- correções solicitadas de forma estruturada;
- detecção de concordância ou divergência humano–sistema;
- produção de uma trilha de auditoria append-only em memória.

## 3. Não objetivos

Esta versão não implementa:

- interface gráfica;
- autenticação ou autorização;
- persistência em banco de dados;
- integração com ERP ou plataforma Master Data;
- filas, SLA, escalonamento ou notificações;
- assinatura digital;
- workflow industrial completo;
- métricas agregadas de desempenho humano–IA.

## 4. Princípios de domínio

1. **A IA recomenda; o humano decide.**
2. **A recomendação original nunca é sobrescrita.**
3. **A decisão final não apaga o percurso que a produziu.**
4. **Registros concluídos são imutáveis.**
5. **Divergências são dados de governança, não erros a ocultar.**
6. **O histórico deve ser explícito, e não inferido apenas do estado final.**
7. **Concordância humano–IA não equivale automaticamente à verdade.**

## 5. Vocabulário

### 5.1 Recomendação automática

Resultado produzido pelo pipeline existente, contendo a decisão recomendada e suas evidências. Continua usando `GovernanceDecision` com os valores:

- `APPROVE`
- `REVIEW`
- `REJECT`

### 5.2 Ação humana

Ação operacional realizada pelo especialista durante a revisão:

- `APPROVE`: aprovar o cadastro;
- `REJECT`: reprovar o cadastro;
- `REQUEST_CORRECTION`: devolver para correção.

`REQUEST_CORRECTION` não deve ser confundido com a recomendação automática `REVIEW`. A primeira é uma ação humana; a segunda é uma classificação do sistema.

### 5.3 Revisão humana

Registro imutável que vincula uma recomendação automática à ação do especialista, à justificativa, ao instante da decisão e às correções solicitadas.

### 5.4 Evento de auditoria

Representação imutável de um fato já ocorrido. Eventos são acrescentados ao histórico e não modificados retroativamente.

## 6. Contratos propostos

### 6.1 `HumanDecision`

Enumeração independente de `GovernanceDecision`:

```python
class HumanDecision(str, Enum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    REQUEST_CORRECTION = "REQUEST_CORRECTION"
```

### 6.2 `CorrectionRequest`

Representa uma correção solicitada pelo especialista.

Campos mínimos:

| Campo | Tipo | Regra |
|---|---|---|
| `field_name` | `str` | obrigatório e não vazio |
| `reason` | `str` | obrigatório e não vazio |
| `suggested_value` | `str \| None` | opcional |

O objeto deve ser imutável.

### 6.3 `HumanReview`

Campos mínimos:

| Campo | Tipo | Regra |
|---|---|---|
| `review_id` | `str` | obrigatório e não vazio |
| `material_id` | `str` | obrigatório e não vazio |
| `system_recommendation` | `GovernanceDecision` | recomendação original preservada |
| `human_decision` | `HumanDecision` | decisão final humana |
| `reviewer_id` | `str` | obrigatório e não vazio |
| `reviewed_at` | `datetime` | obrigatório e timezone-aware |
| `justification` | `str \| None` | condicionada às regras de negócio |
| `corrections` | `tuple[CorrectionRequest, ...]` | coleção imutável |

Propriedade derivada:

```python
agrees_with_system: bool
```

Mapeamento inicial de concordância:

| Recomendação do sistema | Decisão humana | Concordância |
|---|---|---|
| `APPROVE` | `APPROVE` | `True` |
| `REJECT` | `REJECT` | `True` |
| `REVIEW` | `REQUEST_CORRECTION` | `True` |
| qualquer outra combinação | — | `False` |

Esse mapeamento é uma convenção operacional da v1 e deve permanecer isolado para futura revisão.

### 6.4 `AuditEvent`

Campos mínimos:

| Campo | Tipo | Regra |
|---|---|---|
| `event_id` | `str` | obrigatório e não vazio |
| `event_type` | `AuditEventType` | tipo estruturado do evento |
| `material_id` | `str` | agregado auditado |
| `actor_id` | `str` | responsável pela ação |
| `occurred_at` | `datetime` | obrigatório e timezone-aware |
| `review_id` | `str` | referência à revisão humana |
| `metadata` | estrutura imutável | dados complementares sem objetos mutáveis |

Tipo inicial de evento:

```python
class AuditEventType(str, Enum):
    HUMAN_REVIEW_RECORDED = "HUMAN_REVIEW_RECORDED"
```

## 7. Invariantes

1. Identificadores textuais não podem ser vazios ou conter apenas espaços.
2. `reviewed_at` e `occurred_at` devem conter timezone.
3. `REJECT` exige justificativa não vazia.
4. `REQUEST_CORRECTION` exige justificativa não vazia.
5. `REQUEST_CORRECTION` exige ao menos uma correção estruturada.
6. `APPROVE` não pode conter solicitações de correção.
7. A recomendação original deve permanecer acessível após a revisão.
8. Revisões e eventos devem ser imutáveis.
9. Coleções internas devem ser representadas por estruturas imutáveis.
10. Um evento de auditoria deve referenciar exatamente a revisão que o originou.

## 8. Serviço de aplicação

Criar uma função ou serviço com responsabilidade única, por exemplo:

```python
record_human_review(...)
```

Responsabilidades:

1. receber a recomendação existente e os dados da revisão;
2. validar os invariantes;
3. construir `HumanReview`;
4. construir `AuditEvent` correspondente;
5. devolver ambos sem persistir ou mutar a recomendação recebida.

Saída proposta:

```python
@dataclass(frozen=True)
class HumanReviewResult:
    review: HumanReview
    audit_event: AuditEvent
```

O serviço não deve:

- recalcular a recomendação automática;
- alterar evidências;
- autenticar o especialista;
- salvar dados;
- publicar mensagens externas.

## 9. Fluxo

1. O pipeline produz a recomendação automática.
2. O especialista consulta recomendação e evidências.
3. O especialista escolhe uma ação humana.
4. O domínio valida identidade, timestamp, justificativa e correções.
5. O sistema cria uma revisão humana imutável.
6. O sistema cria o evento de auditoria correspondente.
7. Recomendação, revisão e evento permanecem distinguíveis.

## 10. Estratégia TDD

### 10.1 Testes de contrato

- cria decisão humana válida;
- rejeita identificadores vazios;
- aceita timestamp timezone-aware;
- rejeita timestamp naive;
- impede mutação de `CorrectionRequest`;
- impede mutação de `HumanReview`;
- impede mutação de `AuditEvent`.

### 10.2 Testes de regras

- `APPROVE` humano concorda com `APPROVE` automático;
- `REJECT` humano concorda com `REJECT` automático;
- `REQUEST_CORRECTION` concorda com `REVIEW` automático;
- combinações diferentes registram divergência;
- `REJECT` sem justificativa falha;
- `REQUEST_CORRECTION` sem justificativa falha;
- `REQUEST_CORRECTION` sem correções falha;
- `APPROVE` com correções falha.

### 10.3 Testes de integração

- recomendação automática é preservada após aprovação humana;
- recomendação automática é preservada após divergência humana;
- revisão produz evento de auditoria correlacionado;
- material, responsável, instante e revisão são rastreáveis;
- suite anterior de 70 testes permanece aprovada.

## 11. Organização sugerida

```text
src/agent_lab/
├── human_review.py
└── audit.py

tests/
├── test_human_review.py
└── test_human_review_integration.py
```

A separação em dois módulos é sugerida, não obrigatória. A implementação deve priorizar coesão, baixo acoplamento e consistência com o projeto existente.

## 12. Critérios de aceite

- [ ] Existe contrato explícito para decisão e revisão humana.
- [ ] Decisão humana e recomendação automática usam conceitos separados.
- [ ] A recomendação automática original é preservada.
- [ ] Especialista e timestamp são obrigatórios.
- [ ] Timestamps exigem timezone.
- [ ] Divergências podem ser identificadas sem apagar nenhuma decisão.
- [ ] Reprovações e solicitações de correção exigem justificativa.
- [ ] Solicitações de correção são estruturadas.
- [ ] Revisões e eventos são imutáveis.
- [ ] Cada revisão produz um evento de auditoria correlacionado.
- [ ] Testes cobrem concordância, divergência e estados inválidos.
- [ ] Os 70 testes anteriores continuam aprovados.

## 13. Riscos e limitações

### Riscos

- confundir `REVIEW` automático com `REQUEST_CORRECTION` humano;
- misturar recomendação e decisão em um único estado;
- criar falsa sensação de auditoria sem persistência durável;
- usar texto livre como única fonte para análises futuras;
- acoplar prematuramente o domínio à interface ou ao banco;
- transformar concordância humano–IA em medida de verdade;
- endurecer regras antes de validar exceções industriais reais.

### Limitações

- auditoria apenas estrutural e em memória;
- identidade declarativa, sem autenticação;
- ausência de controle de concorrência e versionamento persistente;
- ausência de fila e estados intermediários do workflow;
- cenários validados com dados controlados, sem benchmark industrial real;
- taxonomia de justificativas ainda não normalizada.

### Mitigações

- manter a v1 restrita ao domínio e aos invariantes;
- aplicar TDD antes da implementação;
- preservar contratos separados e imutáveis;
- documentar convenções temporárias, especialmente o mapeamento de concordância;
- adiar persistência e integrações até estabilizar o núcleo.

## 14. Decisões adiadas

- repositório e banco de dados para auditoria;
- event sourcing completo;
- versionamento otimista;
- taxonomia de motivos e correções;
- permissões por papel;
- múltiplos níveis de aprovação;
- reabertura ou supersessão de revisões;
- métricas de override, precisão e concordância;
- interface do especialista aprovador;
- integração com fila de injeção no ERP.

## 15. Definição de pronto

A implementação estará pronta quando os contratos, invariantes, serviço e evento de auditoria descritos nesta SPEC estiverem implementados; os novos testes estiverem aprovados; os 70 testes anteriores permanecerem verdes; e a documentação refletir eventuais decisões técnicas tomadas durante o desenvolvimento.

## 16. Resultado da implementação

Implementação concluída em 2026-08-15 com os seguintes componentes:

- `src/agent_lab/human_review.py`:
  - `HumanDecision`;
  - `CorrectionRequest`;
  - `HumanReview`;
  - validações de identidade, timestamp, justificativa e correções;
  - cálculo de concordância humano–sistema;
  - contratos e coleções imutáveis.
- `src/agent_lab/audit.py`:
  - `AuditEventType`;
  - `AuditEvent`;
  - congelamento defensivo e recursivo dos metadados;
  - `HumanReviewResult`;
  - `record_human_review`;
  - validação da correlação entre revisão humana e evento.
- `tests/test_human_review.py`:
  - 20 testes de contrato, invariantes, concordância e divergência.
- `tests/test_human_review_integration.py`:
  - 10 testes de auditoria e integração.

Baseline final:

```text
Ran 100 tests in 0.047s
OK
```

Os 70 testes anteriores permaneceram aprovados e 30 novos testes foram acrescentados sem regressões.

## 17. Validação

Executar:

```powershell
python -m unittest discover -s tests -v
```

Resultado esperado: todos os testes anteriores e novos aprovados, sem regressões.
