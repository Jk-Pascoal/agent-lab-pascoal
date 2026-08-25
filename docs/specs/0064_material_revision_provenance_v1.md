# SPEC-0064 — Material Revision Provenance v1

> Especificação técnica do contrato de domínio puro e em memória para representação
> de revisões factuais de materiais e sua proveniência temporal/estrutural no Agent Lab Pascoal.

## Metadados

| Campo | Valor |
| --- | --- |
| Identificador | `SPEC-0064` |
| Status | `Implementada, Validada e Integrada na main` |
| Issue relacionada | `#64` |
| Responsável | `Jk-Pascoal` |
| Data de criação | `2026-08-25` |
| Última atualização | `2026-08-25` |

---

## 1. Contexto

O Agent Lab Pascoal é um sistema experimental de engenharia para governança de materiais industriais PDM/BOM. O baseline atual integrado na branch `main` possui **320 testes aprovados** (`unittest`, Python 3.11) e consolida:

- validação determinística e estruturação de cadastros brutos (`MaterialRecord`);
- fronteira LLM tipada com guardrail de identidade (`MaterialIdentityMismatchError`);
- Evidence Engine multiorigem (`RULE`, `VALIDATION`, `DUPLICATE`, `LLM`);
- recommendation pipeline com compulsoriedade constitucional de `requires_human_decision = True`;
- identidade verificável de especialista (`VerifiedSpecialistIdentity`);
- deliberação humana estruturada via `HumanReview` (`APPROVE`, `REJECT`, `REQUEST_CORRECTION`);
- prescrição de correção estruturada (`CorrectionRequest`);
- ciclo de vida temporal de governança em memória (`GovernanceWorkflow`);
- persistência append-only de abertura e conclusão de workflow (`WorkflowOpened`, `WorkflowConcluded`);
- auditoria desacoplada append-only (`AuditEvent`, `JsonlAuditRepository`);
- verificação determinística de consistência dual-write (`verify_dual_write_consistency`, `verify_repositories_consistency`);
- abertura e persistência de ciclo sucessor de governança pós-correção com vínculo de linhagem (`open_correction_follow_up`, `schema_version = 2` na Issue #61).

Baseline oficial verificado:

```text
Ran 320 tests in 1.024s
OK
```

Runner oficial:

```powershell
python -m unittest discover -s tests -v
```

---

## 2. Problema, evidências e impacto

### Problema

Atualmente, o domínio representa dados cadastrais brutos através de instâncias de `MaterialRecord`. No entanto, `MaterialRecord` é um snapshot pontual sem identidade de revisão, sem timestamp e sem linhagem de dados:

1. Dois snapshots diferentes contendo o mesmo `material_id` são tratados como objetos isolados e desconexos;
2. O domínio não consegue expressar qual snapshot precedeu outro;
3. O domínio não registra qual instante explícito foi declarado para o estabelecimento/registro factual de uma nova revisão;
4. Não há como associar uma revisão factual ao contexto de uma `HumanReview` anterior sem acoplar indevidamente o dado cadastral à lógica do workflow;
5. Há o risco arquitetural de tentar tratar `CorrectionRequest` (uma intenção/prescrição humana) como se fosse um patch executável ou o próprio dado cadastral, confundindo promessa/intenção com fato/acontecimento.

### Evidências

1. Em `src/agent_lab/domain.py`, `MaterialRecord` possui apenas campos de atributos brutos (`material_id`, `description_short`, `long_description`, etc.), sem identificador de revisão, timestamp ou referência a predecessor.
2. Em `src/agent_lab/human_review.py`, `CorrectionRequest` define prescrições (`field_name`, `reason`, `suggested_value`), mas inexiste entidade de domínio que represente o cadastro revisado que o mundo real produziu após a intervenção.
3. Não existe contrato ou módulo no projeto para `MaterialRevision`.

### Impacto

- Impossibilidade de rastrear a evolução factual de um cadastro de material ao longo do tempo no domínio;
- Risco de acoplamento indevido ou tentativas futuras de criar mutações automáticas *in-place* sobre `MaterialRecord`;
- Fragilidade na preparação do HITL operacional (onde analistas precisarão inspecionar revisões sucessivas e comparar estados factuais antes e depois de intervenções).

---

## 3. Hipótese

A criação de um contrato de domínio imutável, puro e em memória (`MaterialRevision`), localizado em módulo dedicado (`src/agent_lab/material_revision.py`), permitirá representar revisões sucessivas de um material e sua proveniência associada de forma limpa e desacoplada, preservando a imutabilidade estrita de `MaterialRecord` e mantendo `CorrectionRequest` em seu papel exclusivo de prescrição normativa humana.

---

## 4. Objetivo

Definir e implementar o contrato de domínio puro, síncrono e em memória `MaterialRevision` e a operação pura de sucessão factual `create_successor_revision`, garantindo:

1. Representação imutável de revisões de cadastro com `revision_id`, `record: MaterialRecord`, `revised_at` timezone-aware explícito, `predecessor_revision_id` e `source_review_id`;
2. Derivação da propriedade `material_id` diretamente de `record.material_id` (fonte única da verdade);
3. Validação defensiva completa de validade estrutural local e validade de transição de sucessão;
4. Operação pura `create_successor_revision` para vincular snapshots factuais sucessivos do mesmo material;
5. Nenhuma mutação de objetos anteriores e nenhuma execução/interpretação automática de `CorrectionRequest`;
6. Preservação integral do baseline de 320 testes existentes.

---

## 5. Escopo

### Incluído

- Criação do módulo dedicado `src/agent_lab/material_revision.py`;
- Definição do dataclass congelado `MaterialRevision` (`slots=True`, `frozen=True`);
- Propriedade derivada `material_id` proveniente de `record.material_id`;
- Validação estrita de que `record.material_id` é string não-vazia após `strip()`, sem modificar o valor original de `record`;
- Validação de que `revision_id` é string não-vazia sanitizada via `strip()`;
- Validação de que `revised_at` é `datetime` timezone-aware fornecido explicitamente;
- Validação de que `predecessor_revision_id`, quando presente, é string não-vazia sanitizada e diferente de `revision_id`;
- Validação de que `source_review_id`, quando presente, é string não-vazia sanitizada e exige a presença de `predecessor_revision_id`;
- Criação da função pura `create_successor_revision(predecessor, *, revision_id, record, revised_at, source_review_id=None) -> MaterialRevision`;
- Validação em `create_successor_revision` de compatibilidade exata de `material_id` (`record.material_id == predecessor.material_id`) e monotonicidade temporal declarada (`revised_at >= predecessor.revised_at`);
- Suíte completa de testes unitários em `tests/test_material_revision.py`.

### Fora do escopo

- Execução, aplicação ou interpretação automática de `CorrectionRequest` (`apply_corrections`, patching);
- Verificação ou prova de cumprimento de correções (`correction_applied`, `correction_status`);
- Armazenamento ou persistência de `diff`, `changed_fields` ou `revision_number`;
- Mutação de instâncias de `MaterialRecord` ou `MaterialRevision`;
- Validação de `source_review_id` contra repositório de `HumanReview` ou auditoria nesta v1;
- Inserção de `revision_id` ou `MaterialRevision` em `DecisionRecommendation` (fronteira futura);
- Alterações em `EvidenceCollection`, `GovernanceWorkflow`, `WorkflowOpened` ou `WorkflowConcluded`;
- Persistência em arquivo JSONL ou repositório de `MaterialRevision`;
- Mudança de `schema_version` existente;
- Reexecução automática de regras, normalização ou LLM;
- Filas operacionais, claim, SLA, UI, RBAC ou integração com ERP.

---

## 6. Responsabilidade humana e limites do agente

- O especialista humano prescreve alterações através de `CorrectionRequest` em `src/agent_lab/human_review.py`;
- O mundo factual (ERP, operador cadastral, carga de dados) produz um novo estado cadastral (`MaterialRecord`);
- `MaterialRevision` registra formalmente esse novo estado factual no domínio com sua proveniência associada;
- A presença de `source_review_id` expressa associação de proveniência com uma deliberação humana anterior, mas **não** substitui a avaliação do novo estado, não prova existência da review no repositório nesta v1 e não comprova que a prescrição do especialista foi cumprida.

---

## 7. Requisitos

### Requisitos funcionais

- `RF-01` — `MaterialRevision` deve aceitar e encapsular `revision_id: str`, `record: MaterialRecord`, `revised_at: datetime`, `predecessor_revision_id: str | None = None` e `source_review_id: str | None = None`.
- `RF-02` — `MaterialRevision` deve expor a propriedade `material_id` retornando exatamente `self.record.material_id`.
- `RF-03` — `MaterialRevision` deve suportar o cenário **Root Revision** quando `predecessor_revision_id=None` e `source_review_id=None`.
- `RF-04` — `MaterialRevision` deve suportar o cenário **Derived Revision** quando `predecessor_revision_id` for informado e `source_review_id=None`.
- `RF-05` — `MaterialRevision` deve suportar o cenário **Review-Associated Derived Revision** quando ambos `predecessor_revision_id` e `source_review_id` forem informados.
- `RF-06` — `MaterialRevision` deve rejeitar qualquer instância com `predecessor_revision_id=None` e `source_review_id` preenchido.
- `RF-07` — A função pura `create_successor_revision` deve construir uma nova `MaterialRevision` derivada a partir de um predecessor e de um novo `MaterialRecord` factual já fornecido.
- `RF-08` — `create_successor_revision` deve rejeitar se `record.material_id != predecessor.material_id` (comparação exata).
- `RF-09` — `create_successor_revision` deve rejeitar se `revised_at < predecessor.revised_at` (onde `revised_at == predecessor.revised_at` é aceito).

### Requisitos de qualidade

- `RQ-01` — **Imutabilidade estrita:** `MaterialRevision` deve ser imutável (`frozen=True`, `slots=True`).
- `RQ-02` — **Validação defensiva de tipos e campos:** Argumentos com tipos ou valores inválidos devem levantar exceções conforme a taxonomia formal de erros.
- `RQ-03` — **Sanitização de identificadores de contrato:** `revision_id`, `predecessor_revision_id` e `source_review_id` devem ser validados e armazenados após `strip()`. Strings vazias ou contendo apenas espaços devem ser rejeitadas.
- `RQ-04` — **Não-mutação e não-normalização de `MaterialRecord`:** `record.material_id` vazio ou composto apenas de whitespace deve ser rejeitado, mas o valor bruto do `MaterialRecord` jamais deve ser normalizado ou reescrito silenciosamente.
- `RQ-05` — **Anti-auto-referência:** `predecessor_revision_id` idêntico a `revision_id` após sanitização deve ser rejeitado.
- `RQ-06` — **Explicitude temporal:** `revised_at` deve ser obrigatoriamente timezone-aware e fornecido explicitamente pelo chamador. `MaterialRevision` não gera timestamps implicitamente.
- `RQ-07` — **Desacoplamento e não-regressão:** Nenhuma classe ou função existente do Agent Lab deve sofrer alteração de comportamento, mantendo o baseline de 320 testes verde.

---

## 8. Proposta técnica

### 8.1 Localização arquitetural

O contrato será implementado em módulo dedicado:
```text
src/agent_lab/material_revision.py
```

**Justificativa:**
- `src/agent_lab/domain.py` concentra modelos brutos e enums do domínio cadastral (`MaterialRecord`, `GovernanceDecision`, etc.);
- `MaterialRevision` introduz conceitos de identidade temporal e proveniência de dados;
- O isolamento em módulo próprio segue o padrão arquitetural consolidado do laboratório (`human_review.py`, `workflow.py`, `evidence.py`, `decision.py`).

### 8.2 Distinção Formal: Validade Estrutural $\times$ Validade de Transição

O domínio opera com duas fronteiras complementares e distintas de validação:

```text
┌────────────────────────────────────────────────────────┐
│             A. VALIDADE ESTRUTURAL LOCAL               │
│       (Verificável no __post_init__ do dataclass)      │
├────────────────────────────────────────────────────────┤
│ • revision_id: str válida e não-branca                 │
│ • record: instância de MaterialRecord                  │
│ • record.material_id: str válida e não-branca          │
│ • revised_at: datetime timezone-aware explícito        │
│ • predecessor_revision_id: str válida quando presente  │
│ • anti-auto-referência: predecessor != revision_id     │
│ • source_review_id: str válida quando presente         │
│ • coerência local: source_review_id exige predecessor  │
│ • material_id derivado exclusivamente de record        │
└────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│            B. VALIDADE DE TRANSIÇÃO / SUCESSÃO         │
│        (Verificável somente em create_successor)       │
├────────────────────────────────────────────────────────┤
│ • predecessor: instância de MaterialRevision           │
│ • record: instância de MaterialRecord                  │
│ • identidade exata: record.material_id == pred.mat_id  │
│ • sucessor.revision_id != predecessor.revision_id      │
│ • monotonicidade temporal: revised_at >= pred.rev_at   │
│ • vínculo determinístico: pred_id = pred.revision_id   │
│ • não-mutação: predecessor e record intactos           │
└────────────────────────────────────────────────────────┘
```

> **Limitação Estrutural Reconhecida:** Um `MaterialRevision` construído diretamente com `predecessor_revision_id` contém apenas um identificador opaco e não possui a instância do predecessor em memória. Logo, a validação de igualdade cadastral e monotonicidade temporal entre revisões pertence exclusivamente à operação de transição (`create_successor_revision`), que recebe ambos os objetos.

### 8.3 Comparação de `material_id` e Não-Normalização de Dados Brutos

Em `create_successor_revision`, a verificação de pertencimento ao mesmo material lógico utiliza **comparação exata de string** (`record.material_id != predecessor.material_id`).

**Regras específicas:**
- `strip()` é utilizado exclusivamente para verificar se `record.material_id` é não-vazio/não-branco;
- O valor bruto armazenado em `MaterialRecord` **não é reescrito nem normalizado**;
- A comparação entre predecessor e sucessor usa igualdade exata (`==`) do valor armazenado;
- Caso dois registros possuam identificadores como `"MAT-001"` e `" MAT-001 "`, eles são tratados como distintos na operação de sucessão.

### 8.4 Sanitização de Identificadores de Contrato $\times$ Dados Brutos

A sanitização com `strip()` aplica-se **exclusivamente aos identificadores do contrato de revisão** (`revision_id`, `predecessor_revision_id`, `source_review_id`):
- `revision_id = "  REV-002  "` $\rightarrow$ armazenado como `"REV-002"`;
- `record.material_id = " MAT-001 "` $\rightarrow$ preservado estritamente como `" MAT-001 "`.

### 8.5 Monotonicidade Temporal Declarada

A regra `revised_at >= predecessor.revised_at` aplicada em `create_successor_revision`:
- Representa a coerência temporal da linhagem declarada no domínio;
- Permite explicitamente a igualdade temporal (`revised_at == predecessor.revised_at`), respeitando cenários de lote onde múltiplas revisões compartilham o mesmo timestamp declarado;
- **Não prova** o instante físico exato da alteração no ERP, a ordem de commits externos ou causalidade física no mundo real.

### 8.6 Semântica de `source_review_id`

`source_review_id` expressa que a revisão factual declara associação de proveniência com determinada `HumanReview`:
- Não é validado contra o repositório de `HumanReview` nesta v1;
- Não prova que a deliberação humana foi `REQUEST_CORRECTION`;
- Não prova cumprimento ou aplicação das `CorrectionRequest`.

### 8.7 Taxonomia Formal de Erros

Alinhada aos padrões consolidados do Agent Lab (`workflow.py`, `human_review.py`):

1. **No dataclass `MaterialRevision` (`__post_init__`):**
   - Lança `ValueError` para todas as violações de invariantes estruturais (incluindo tipo inválido de `revision_id`, `record`, `revised_at`, `predecessor_revision_id`, `source_review_id`, strings em branco, `record.material_id` vazio/branco, datetime naive, auto-referência e `source_review_id` sem `predecessor_revision_id`).
2. **Na função `create_successor_revision`:**
   - Lança `TypeError` se `predecessor` não for instância de `MaterialRevision`;
   - Lança `ValueError` para violações de invariantes da sucessão (divergência de `material_id`, `revised_at` anterior ao predecessor, ou falhas na instanciação do sucessor).

### 8.8 Contratos de dados

```python
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from agent_lab.domain import MaterialRecord


def _require_non_blank(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-blank string")
    return value.strip()


def _require_aware_datetime(value: datetime, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value


@dataclass(frozen=True, slots=True)
class MaterialRevision:
    """Immutable factual revision of a material record with explicit provenance."""

    revision_id: str
    record: MaterialRecord
    revised_at: datetime
    predecessor_revision_id: str | None = None
    source_review_id: str | None = None

    def __post_init__(self) -> None:
        sanitized_revision_id = _require_non_blank(self.revision_id, "revision_id")
        object.__setattr__(self, "revision_id", sanitized_revision_id)

        if not isinstance(self.record, MaterialRecord):
            raise ValueError("record must be a MaterialRecord")

        if not isinstance(self.record.material_id, str) or not self.record.material_id.strip():
            raise ValueError("record.material_id must be a non-blank string")

        _require_aware_datetime(self.revised_at, "revised_at")

        if self.predecessor_revision_id is not None:
            sanitized_predecessor = _require_non_blank(
                self.predecessor_revision_id, "predecessor_revision_id"
            )
            if sanitized_predecessor == sanitized_revision_id:
                raise ValueError("predecessor_revision_id must differ from revision_id")
            object.__setattr__(self, "predecessor_revision_id", sanitized_predecessor)

        if self.source_review_id is not None:
            if self.predecessor_revision_id is None:
                raise ValueError(
                    "source_review_id requires predecessor_revision_id to be present"
                )
            sanitized_source_review_id = _require_non_blank(
                self.source_review_id, "source_review_id"
            )
            object.__setattr__(self, "source_review_id", sanitized_source_review_id)

    @property
    def material_id(self) -> str:
        return self.record.material_id


def create_successor_revision(
    predecessor: MaterialRevision,
    *,
    revision_id: str,
    record: MaterialRecord,
    revised_at: datetime,
    source_review_id: str | None = None,
) -> MaterialRevision:
    """Create a new MaterialRevision linked to an existing predecessor revision.

    Validates that the successor belongs to the same material as the predecessor
    and establishes the predecessor_revision_id linkage.
    """
    if not isinstance(predecessor, MaterialRevision):
        raise TypeError("predecessor must be a MaterialRevision")
    if not isinstance(record, MaterialRecord):
        raise ValueError("record must be a MaterialRecord")
    if record.material_id != predecessor.material_id:
        raise ValueError(
            f"successor record.material_id '{record.material_id}' must match predecessor material_id '{predecessor.material_id}'"
        )
    validated_revised_at = _require_aware_datetime(revised_at, "revised_at")
    if validated_revised_at < predecessor.revised_at:
        raise ValueError("successor revised_at cannot be earlier than predecessor revised_at")

    return MaterialRevision(
        revision_id=revision_id,
        record=record,
        revised_at=validated_revised_at,
        predecessor_revision_id=predecessor.revision_id,
        source_review_id=source_review_id,
    )
```

---

## 9. Arquivos previstos

1. `src/agent_lab/material_revision.py` — Implementação do contrato `MaterialRevision` e da função `create_successor_revision`;
2. `tests/test_material_revision.py` — Testes unitários do novo módulo;
3. `docs/specs/0064_material_revision_provenance_v1.md` — Esta especificação integrada ao repositório.

---

## 10. Estratégia de testes e TDD

### Fase Vermelho (RED)
Criar `tests/test_material_revision.py` contendo testes que importam `src/agent_lab/material_revision.py` antes de sua criação. A execução deve falhar com `ModuleNotFoundError` ou `ImportError`.

### Fase Verde (GREEN)
Implementar `src/agent_lab/material_revision.py` contendo as validações e classes especificadas até que todos os novos testes passem.

### Fase Regressão (REGRESSION)
Executar a suíte completa com `python -m unittest discover -s tests -v` e confirmar que o baseline avança a partir do baseline pré-incremento de **320 testes aprovados**, mantendo 100% de sucesso.

### Testes planejados

#### Grupo 1: Testes do Contrato `MaterialRevision` (Validade Estrutural Local)
- Instanciação de **Root Revision** válida (`predecessor=None`, `source_review=None`);
- Instanciação de **Derived Revision** estruturalmente válida com `predecessor_revision_id`;
- Instanciação de **Review-Associated Derived Revision** estruturalmente válida com `predecessor_revision_id` e `source_review_id`;
- Propriedade `material_id` delegada a `record.material_id`;
- Sanitização de `revision_id` via `strip()`;
- Sanitização de `predecessor_revision_id` via `strip()`;
- Sanitização de `source_review_id` via `strip()`;
- `MaterialRecord` bruto não é normalizado/mutado internamente;
- Rejeição de `revision_id` não-string, vazio ou whitespace (`ValueError`);
- Rejeição de `record` não-MaterialRecord (`ValueError`);
- Rejeição de `record.material_id` vazio ou whitespace (`ValueError`);
- Rejeição de `revised_at` não-datetime ou naive (`ValueError`);
- Rejeição de `predecessor_revision_id` vazio ou whitespace (`ValueError`);
- Rejeição de auto-referência `predecessor_revision_id == revision_id` (`ValueError`);
- Rejeição de `source_review_id` sem `predecessor_revision_id` (`ValueError`);
- Rejeição de `source_review_id` vazio ou whitespace (`ValueError`);
- Imutabilidade comprovada (`FrozenInstanceError` em tentativa de mutação).

#### Grupo 2: Testes da Transição `create_successor_revision` (Validade de Sucessão)
- Sucessor válido com mesmo `material_id` e preenchimento determinístico de `predecessor_revision_id`;
- Sucessor válido informando `source_review_id`;
- Sucessor com `revised_at == predecessor.revised_at` é aceito (boundary temporal);
- Rejeição de `predecessor` que não seja instância de `MaterialRevision` (`TypeError`);
- Rejeição de `record` que não seja instância de `MaterialRecord` (`ValueError`);
- Rejeição de sucessor com `material_id` divergente (`ValueError`);
- Rejeição de sucessor com `revised_at < predecessor.revised_at` (`ValueError`);
- Predecessor permanece estritamente inalterado;
- Novo `MaterialRecord` permanece estritamente inalterado;
- Ausência total de dependência ou interpretação de `CorrectionRequest`.

---

## 11. Gates de qualidade

Comandos mandatórios a executar antes da submissão do Pull Request:

```powershell
python -m unittest discover -s tests -v
git diff --check
git status -sb
```

Critérios de aprovação:
- 100% dos testes aprovados (baseline 320 + novos testes);
- `git diff --check` limpo (sem whitespace trailing);
- Working tree limpa após commits;
- Nenhum contrato de workflow, auditoria ou persistência existente alterado.

---

## 12. Riscos e limitações

| Risco ou limitação | Probabilidade | Impacto | Mitigação |
| --- | --- | --- | --- |
| Confundir `MaterialRevision` com mutação de `MaterialRecord` | Baixa | Alto | Modelagem explícita com encapsulamento de `MaterialRecord` imutável e testes que comprovam não-mutação |
| Supor que `source_review_id` valida deliberação no repositório | Média | Médio | Documentação explícita de que `source_review_id` é proveniência declarada sem I/O ou consultas no domínio |
| Acoplamento prematuro com `DecisionRecommendation` | Baixa | Alto | Manter a integração `MaterialRevision` $\rightarrow$ `DecisionRecommendation` explicitamente fora do escopo desta SPEC |

---

## 13. Plano de reversão

Como o incremento é estritamente isolado em módulo de domínio puro sem persistência em disco ou alterações em schemas existentes:
1. Reverter o merge commit na branch `main` via `git revert`;
2. A remoção de `src/agent_lab/material_revision.py` e `tests/test_material_revision.py` restaura imediatamente o estado anterior com 320 testes aprovados, sem necessidade de migração de dados.

---

## 14. Versionamento e release

### Impacto SemVer
- Classificação: `MINOR`
- Justificativa: Introdução de novas capacidades e contratos de domínio imutáveis (`MaterialRevision`), totalmente compatíveis com as interfaces anteriores e sem alteração dos contratos vigentes.

### Publicação prevista
- Versão planejada: `Unreleased` (consolidação de incremento técnico);
- Criação de tag: Não;
- Criação de GitHub Release: Não;
- Atualização de `CHANGELOG.md`: Sim (na conclusão do ciclo de engenharia).

---

## 15. Critérios de aceite

- [x] Módulo `src/agent_lab/material_revision.py` implementado conforme especificação;
- [x] Testes unitários em `tests/test_material_revision.py` criados e aprovados cobrindo validade estrutural e validade de transição;
- [x] Suíte completa de testes aprovada a partir do baseline pré-incremento de 320 testes via `python -m unittest discover -s tests -v`;
- [x] Imutabilidade de `MaterialRecord` e `MaterialRevision` comprovada por testes;
- [x] `material_id` derivado exclusivamente de `record.material_id`;
- [x] Rejeição de `record.material_id` vazio/whitespace sem mutação do registro bruto;
- [x] Rejeição de `source_review_id` sem `predecessor_revision_id`;
- [x] `create_successor_revision` valida compatibilidade exata de `material_id` e monotonicidade temporal (`revised_at >= predecessor.revised_at`);
- [x] Nenhum contrato existente (`DecisionRecommendation`, `EvidenceCollection`, `GovernanceWorkflow`, `AuditEvent`, `WorkflowOpened`, `WorkflowConcluded`) modificado;
- [x] Gates de qualidade executados sem pendências;
- [x] Responsabilidade humana e distinção ontológica preservadas;
- [x] SPEC integrada em `docs/specs/0064_material_revision_provenance_v1.md`.

---

## 16. Questões em aberto

- `Nenhuma` — Todas as decisões técnicas, regras de proveniência, distinções de validade e fronteiras de escopo foram formalmente decididas e aprovadas.

---

## 17. Histórico de decisões

| Data | Decisão | Motivo | Responsável |
| --- | --- | --- | --- |
| 2026-08-25 | Criação de `MaterialRevision` como fato em vez de `CorrectionApplied` como verbo | Separar a intenção humana (`CorrectionRequest`) do estado factual do cadastro (`MaterialRevision`) | Jk-Pascoal |
| 2026-08-25 | Adoção de `source_review_id` em vez de `triggering_review_id` | Expressar proveniência/associação declarada sem alegações de causalidade comprovada | Jk-Pascoal |
| 2026-08-25 | Módulo dedicado `src/agent_lab/material_revision.py` | Evitar inflar `domain.py` e manter separação de responsabilidades | Jk-Pascoal |
| 2026-08-25 | Distinção entre Validade Estrutural e Validade de Transição | Reconhecer que o dataclass isolado não acessa o predecessor; regras de sucessão pertencem a `create_successor_revision` | Jk-Pascoal |
| 2026-08-25 | Rejeição de `record.material_id` vazio em `MaterialRevision` sem normalização bruta | Permitir correlação no domínio sem alterar o dado cadastral bruto original | Jk-Pascoal |
| 2026-08-25 | Comparação exata de string para `material_id` em `create_successor_revision` | Preservar a fonte da verdade sem coerções implícitas | Jk-Pascoal |
| 2026-08-25 | Monotonicidade temporal declarada com suporte a igualdade (`>=`) | Garantir coerência cronológica declarada sem inventar precisão temporal inexistente na fonte | Jk-Pascoal |
| 2026-08-25 | Taxonomia de erros alinhada (`TypeError` para predecessor, `ValueError` para invariantes) | Manter consistência com `workflow.py` e `human_review.py` | Jk-Pascoal |
| 2026-08-25 | Não alteração de `DecisionRecommendation` nesta v1 | Isolar o contrato de revisão cadastral antes de conectá-lo ao pipeline avaliador | Jk-Pascoal |
| 2026-08-25 | SPEC-0064 aprovada para implementação | Revisão humana concluiu que contrato, invariantes, limites e estratégia TDD estão suficientemente definidos para iniciar RED | Jk-Pascoal |

---

## 18. Fechamento de Implementação e Evidências das Fatias

- **Status:** Implementação concluída, validada e integrada na branch `main` via PR #65 (merge commit `41c68a0833663d5d08510a443277053d76d72e97`).
- **Issue:** #64 funcionalmente concluída e integrada na main; fechamento formal pendente da integração deste closeout documental.
- **PR:** #65
- **Merge commit:** `41c68a0833663d5d08510a443277053d76d72e97`
- **Commit funcional:** `88c897f`
- **Commit documental inicial:** `8cbb273`
- **Baseline de entrada:** 320 testes
- **Novos testes:** 27
- **Baseline integrado:** 347 testes

### Evidências e Limites de Domínio

1. **`MaterialRevision` imutável:** Implementada como representação factual pura em memória com proveniência declarada.
2. **`create_successor_revision` pura:** Implementada com validação estrita de tipos, identidade exata de `material_id` e monotonicidade temporal declarada.
3. **Distinção ontológica inegociável:** `CorrectionRequest ≠ MaterialRevision`. Nenhuma transformação automática (`apply_corrections`, patching) entre intenção normativa e fato cadastral.
4. **Semântica declarada de `source_review_id`:** Associação contextual que não comprova causalidade física, existência de deliberação no repositório, deliberação `REQUEST_CORRECTION` ou cumprimento de correções.
5. **Fora do escopo preservado:** Inexistência de persistência/repositório JSONL de `MaterialRevision`, sem `revision_number`/`diff` persistidos, sem alterações em `GovernanceWorkflow` ou `DecisionRecommendation`, e sem integrações com ERP ou LLM.
