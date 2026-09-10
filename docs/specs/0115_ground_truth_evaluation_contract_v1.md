# SPEC-0115 — Ground Truth Evaluation Contract v1

> Especificação técnica dos contratos de dados puros, imutáveis e em memória para representação
> formal de verdade de referência rotulada e explicitamente estabelecida (Ground Truth) no Agent Lab Pascoal.

---

## Metadados

| Campo | Valor |
|---|---|
| **Identificador** | `SPEC-0115` |
| **Status** | `PROPOSED` |
| **Issue relacionada** | `#115` |
| **Título da Issue** | `Ground Truth Evaluation Contract v1` |
| **Branch funcional** | `feature/issue-115-ground-truth-evaluation-contract` |
| **Responsável** | `Jk-Pascoal` |
| **Data de criação** | `2026-09-10` |
| **Última atualização** | `2026-09-10` |
| **Baseline de entrada** | `661 testes aprovados` (100% GREEN) |
| **Runner oficial** | `python -m unittest discover -s tests -v` (Python 3.11) |

---

## 1. Contexto

Em 10/09/2026, o Roadmap do **Agent Lab Pascoal** inicia formalmente a frente evolutiva:
**"Ground truth e benchmark"**, cujo objetivo estratégico é estabelecer dataset rotulado e métricas de *precision/recall/F1* para:
1. conformidade de regras cadastrais;
2. detecção de duplicidades;
3. recomendações algorítmicas de governança.

O baseline integrado na branch `main` conta com **661 testes aprovados** (100% GREEN) após a conclusão das trilhas fundamentais de ciclo de vida de workflows, persistência append-only, consistência dual-write, proveniência de revisões de material, assunção de revisão (`HumanReviewClaim`) e liberação de revisão (`HumanReviewClaimRelease`).

### Reconhecimento da Metrologia Embrionária Legada
Os módulos `src/agent_lab/data_io.py` (com a dataclass `LabeledMaterial`) e `src/agent_lab/baseline.py` (com `evaluate_baseline` e `BaselineReport`) constituem a metrologia embrionária legada do laboratório, criada na fase preliminar de exploração para testes sintéticos simples.

**Diretriz de governança obrigatória:**
`data_io.py`, `LabeledMaterial` e `baseline.py` **NÃO** devem ser removidos, alterados ou adaptados nesta Issue #115.
Esta Issue cria a **NOVA fundação tipada e canônica de ground truth** em módulo dedicado (`src/agent_lab/ground_truth.py`). A migração, adaptação e eventual substituição do benchmark legado constituirão uma decisão arquitetural posterior formal.

---

## 2. Problema, evidências e impacto

### Problema
O Agent Lab Pascoal não dispõe de um contrato formal, tipado, imutável e auditável para representar a "verdade de referência" (Ground Truth) contra a qual regras determinísticas, motores de duplicidade e pipelines de governança devem ser aferidos.

O Ground Truth deve ser uma referência estabelecida independentemente da predição (`prediction/runtime`) sob teste. Isso não significa necessariamente externo à organização, mas sim referência estabelecida com critério próprio de gabarito sem circularidade com o sistema sob avaliação.

A abordagem legada em `data_io.py` apresenta limitações conceituais severas:
1. Reduz o gabarito esperado a uma string plana (`expected_issue: str`), forçando tarefas de naturezas estatísticas distintas (regras cadastrais vs. duplicidade) a competirem pelo mesmo campo;
2. Trata duplicidade como atributo intrínseco de um material isolado, gerando ambiguidade sobre qual é o par duplicado;
3. Não possui distinção entre a identidade do caso experimental (`evaluation_case_id`) e a anotação emitida (`ground_truth_id`);
4. Carece de proveniência formal (quem anotou, quando, com base em qual norma/fixture documental e com qual fundamentação técnica).

### Evidências
1. Em `data_io.py`: `LabeledMaterial` possui apenas `record: MaterialRecord` e `expected_issue: str`, aceitando strings soltas como `"VALID"` ou `"POSSIBLE_DUPLICATE"`;
2. Em `baseline.py`: a avaliação de duplicidade é inferida de forma aproximada pela presença da string `POSSIBLE_DUPLICATE` em `predicted_labels` de um único material, sem identificar o par relacional `(material_a, material_b)`;
3. Inexistência de um contrato que modele a recomendação algorítmica esperada de governança (`GovernanceDecision`) com rastreabilidade auditável.

### Impacto
Sem contratos rigorosos de ground truth:
- Métricas futuras de *precision*, *recall* e *F1* serão calculadas sobre bases ambíguas e unidades estatísticas distorcidas;
- Risco de contaminação conceitual entre predição volátil e gabarito estabelecido;
- Impossibilidade de auditar a origem e a autoria das anotações de referência;
- Incapacidade de suportar benchmarking científico reprodutível.

---

## 3. Objetivo

Introduzir o módulo `src/agent_lab/ground_truth.py` no Agent Lab Pascoal, contendo contratos de dados puros em memória (`frozen=True, slots=True`, zero I/O) para a representação explícita, imutável, determinística e auditável do ground truth, contemplando:
1. O modelo de proveniência mínima explícita e auditável para v1 (`LabelProvenance`);
2. O contrato de ground truth para regras cadastrais a nível de material individual (`MaterialRuleGroundTruth`);
3. O contrato de ground truth para duplicidade cadastral a nível de par não-direcional de materiais (`DuplicatePairGroundTruth`);
4. O contrato de ground truth para a recomendação algorítmica esperada do sistema (`DecisionRecommendationGroundTruth`).

---

## 4. Escopo

### Incluído
- Criação do módulo `src/agent_lab/ground_truth.py`;
- Enum `LabelProvenance` com as modalidades `SPECIALIST_CURATED` e `SYNTHETIC_SPECIFIED`;
- Validação explícita de `provenance` como instância de `LabelProvenance` (rejeitando strings avulsas com `TypeError`);
- Dataclass imutável `MaterialRuleGroundTruth` com validação defensiva fail-closed;
- Dataclass imutável `DuplicatePairGroundTruth` com validação defensiva fail-closed;
- Dataclass imutável `DecisionRecommendationGroundTruth` com validação defensiva fail-closed;
- Validação estrita de tipos com `TypeError` inequívoco e validação de regras de negócio/estrutura com `ValueError` inequívoco;
- Normalização interna de strings com `.strip()` e rejeição de vazios/whitespace-only com `ValueError`;
- Segregação mandatória de unidades estatísticas (regras = material; duplicidade = par ordenado $A < B$; decisão = material);
- Bloqueio explícito de `IssueType.POSSIBLE_DUPLICATE` em `MaterialRuleGroundTruth` (`ValueError`);
- Canonicidade determinística de `expected_issue_types` normalizada por `IssueType.value`, permitindo entradas válidas fora de ordem;
- Definição de duplicidade em MDM como equivalência cadastral de entidade governada (não restrita a mesmo item físico);
- Exigência de ordenação canônica estrita `material_id_a < material_id_b` e anti-auto-referência em `DuplicatePairGroundTruth` (`ValueError`);
- Distinção semântica entre `evaluation_case_id` e `ground_truth_id` nos três contratos (sem forçar desigualdade textual artificial);
- Regras de proveniência atreladas a `VerifiedSpecialistIdentity` para curadoria de especialista;
- Compulsoriedade de `source_reference` e `rationale` em todas as anotações;
- Exportação pública dos novos símbolos em `src/agent_lab/__init__.py`;
- Bateria de testes unitários defensivos em `tests/test_ground_truth.py`;
- Preservação integral do baseline atual de 661 testes GREEN.

### Fora do escopo
- Cálculo matemático de métricas: *precision*, *recall*, *F1*, *accuracy*, *confusion matrix* ou *weighted cost calculation*;
- Datasets volumosos de teste ou massas de dados de benchmark;
- Persistência durável em JSONL, bancos relacionais ou NoSQL;
- Parsers ou leitores de CSV, Excel, SQL ou Parquet;
- Alteração, adaptação ou remoção da metrologia legada (`data_io.py`, `LabeledMaterial`, `baseline.py`);
- Fábricas de conveniência (ex.: `create_duplicate_pair_ground_truth()`);
- Algoritmos de matching ou tuning de thresholds de similaridade;
- Alteração das regras em `rules.py` ou do motor em `duplicates.py`;
- Alteração do pipeline de decisão ou evidências (`decision.py`, `evidence.py`);
- Active Claim Projection ou Active Claim Policy;
- Interfaces de usuário (Streamlit/UI), endpoints REST ou CLI;
- Benchmarks de concorrência ou escala P-07;
- Consenso entre múltiplos anotadores ou quórum de painel (`CONSENSUS_PANEL`);
- Adjudicação histórica atrelada a logs operacionais (`HISTORICAL_ADJUDICATED`);
- Versionamento dinâmico ou mutações de ground truth.

---

## 5. Responsabilidade humana e limites do agente

No Agent Lab Pascoal, a IA recomenda, o especialista humano decide, a auditoria preserva o percurso e o lifecycle preserva o estado operacional.

No contexto de Ground Truth e Avaliação:
1. **Ground Truth é referência independente e estabelecida:** O gabarito não é inferido pelo modelo nem pelo sistema sob teste; é uma referência rotulada e explicitamente estabelecida, atribuída por especialista humano verificado (`SPECIALIST_CURATED`) ou fixada por especificação técnica formal controlada (`SYNTHETIC_SPECIFIED`), com independência da predição avaliada.
2. **Avaliação não é execução:** O contrato de ground truth existe exclusivamente para metrologia e benchmark. Ele não concede autorização operacional para aprovação de materiais, não altera `GovernanceWorkflow` e não emite `AuditEvent`.
3. **Preservação de `requires_human_decision = True`:** O pipeline sob avaliação continua submetido à compulsoriedade da decisão humana em produção, independentemente dos resultados de benchmark.

---

## 6. Requisitos

### Requisitos Funcionais
- `RF-01` — Definir o enum `LabelProvenance(StrEnum)` com os membros `SPECIALIST_CURATED` e `SYNTHETIC_SPECIFIED`.
- `RF-02` — Definir o dataclass imutável `MaterialRuleGroundTruth(frozen=True, slots=True)` contendo:
  - `evaluation_case_id: str`
  - `ground_truth_id: str`
  - `material_id: str`
  - `expected_issue_types: tuple[IssueType, ...]`
  - `provenance: LabelProvenance`
  - `source_reference: str`
  - `annotator: VerifiedSpecialistIdentity | None`
  - `labeled_at: datetime`
  - `rationale: str`
- `RF-03` — Em `MaterialRuleGroundTruth`, a ordem de `expected_issue_types` não possui significado epistemológico. A validação e normalização devem:
  - a) validar que `expected_issue_types` seja obrigatoriamente uma tuple; qualquer outro tipo de coleção ou valor deve ser rejeitado com `TypeError`;
  - b) validar que cada elemento seja uma instância de `IssueType`, rejeitando elementos de tipo inválido com `TypeError`;
  - c) rejeitar expressamente `IssueType.POSSIBLE_DUPLICATE` com `ValueError`;
  - d) rejeitar duplicidades internas de `IssueType` com `ValueError`;
  - e) normalizar deterministicamente a tupla em ordem lexicográfica ascendente por `item.value`, garantindo que entradas válidas fora de ordem sejam aceitas e resultem na representação canônica ordenada;
  - f) permitir tupla vazia `()` representando formalmente material conforme (`VALID`).
- `RF-04` — Definir o dataclass imutável `DuplicatePairGroundTruth(frozen=True, slots=True)` contendo:
  - `evaluation_case_id: str`
  - `ground_truth_id: str`
  - `material_id_a: str`
  - `material_id_b: str`
  - `is_duplicate: bool`
  - `provenance: LabelProvenance`
  - `source_reference: str`
  - `annotator: VerifiedSpecialistIdentity | None`
  - `labeled_at: datetime`
  - `rationale: str`
  O campo `is_duplicate` expressa a assertiva relacional indicando se os dois registros representam a mesma entidade cadastral/material governada sob o critério de benchmark (aplicável a materiais físicos, consumíveis, peças ou itens de catálogo).
- `RF-05` — Em `DuplicatePairGroundTruth`, validar que `is_duplicate` seja do tipo booleano estrito (`isinstance(is_duplicate, bool)`), rejeitando valores não-booleanos com `TypeError`. Rejeitar auto-referência (`material_id_a == material_id_b`) com `ValueError` e exigir representação canônica estrita `material_id_a < material_id_b`, falhando de forma *fail-closed* com `ValueError` caso `material_id_a >= material_id_b`.
- `RF-06` — Definir o dataclass imutável `DecisionRecommendationGroundTruth(frozen=True, slots=True)` contendo:
  - `evaluation_case_id: str`
  - `ground_truth_id: str`
  - `material_id: str`
  - `expected_recommendation: GovernanceDecision`
  - `provenance: LabelProvenance`
  - `source_reference: str`
  - `annotator: VerifiedSpecialistIdentity | None`
  - `labeled_at: datetime`
  - `rationale: str`
  Validar que `expected_recommendation` seja instância de `GovernanceDecision`, rejeitando outros tipos (inclusive `HumanDecision`) com `TypeError`.
- `RF-07` — Nos três contratos, validar que todos os campos textuais (`evaluation_case_id`, `ground_truth_id`, `material_id`, `material_id_a`, `material_id_b`, `source_reference`, `rationale`) sejam obrigatoriamente do tipo `str` (rejeitando outros tipos com `TypeError`), rejeitar strings vazias ou compostas unicamente por whitespace com `ValueError`, e normalizar internamente com `.strip()`.
- `RF-08` — Nos três contratos, validar explicitamente que `provenance` seja uma instância de `LabelProvenance` (`isinstance(provenance, LabelProvenance)`), rejeitando outros tipos e strings soltas equivalentes com `TypeError`.
- `RF-09` — Nos três contratos, validar as regras de proveniência:
  - se `provenance == LabelProvenance.SPECIALIST_CURATED`:
    - `annotator` não pode ser `None` (rejeição com `ValueError`);
    - `annotator` deve ser obrigatoriamente instância de `VerifiedSpecialistIdentity` (rejeição de outros tipos com `TypeError`);
    - `annotator.verified_at <= labeled_at` (rejeição de verificação posterior ao rótulo com `ValueError`).
  - se `provenance == LabelProvenance.SYNTHETIC_SPECIFIED`:
    - `annotator` deve ser obrigatoriamente `None` (rejeição de qualquer valor presente com `ValueError`).
- `RF-10` — Nos três contratos, exigir que `labeled_at` seja obrigatoriamente do tipo `datetime` (rejeitando outros tipos com `TypeError`) e explicitamente timezone-aware (`tzinfo is not None` e `utcoffset() is not None`), rejeitando timestamps naive com `ValueError`.
- `RF-11` — Exportar publicamente `LabelProvenance`, `MaterialRuleGroundTruth`, `DuplicatePairGroundTruth` e `DecisionRecommendationGroundTruth` no módulo raiz `src/agent_lab/__init__.py`.

### Requisitos de Qualidade e Integridade (Política Inequívoca de Exceções)
- `RQ-01` — **Imutabilidade estrita:** Todos os contratos devem ser congelados com `frozen=True` e `slots=True`, impedindo qualquer mutação de atributos pós-instanciação.
- `RQ-02` — **Política Inequívoca de Exceções:**
  - **`TypeError`:** lançado exclusivamente para violações de tipo em argumentos fornecidos (ex.: campo textual não `str`; `is_duplicate` não `bool`; `expected_recommendation` não `GovernanceDecision`; `provenance` não `LabelProvenance`; `annotator` não `VerifiedSpecialistIdentity` quando fornecido; `expected_issue_types` não sendo `tuple` ou contendo elemento não `IssueType`; `labeled_at` não `datetime`).
  - **`ValueError`:** lançado exclusivamente para violações estruturais, temporais ou semânticas de negócio (ex.: string vazia ou whitespace-only; inclusão de `IssueType.POSSIBLE_DUPLICATE` em regras; duplicidade interna em `expected_issue_types`; auto-referência `material_id_a == material_id_b`; ordenação não-canônica `material_id_a >= material_id_b`; timestamp naive; `annotator is None` em `SPECIALIST_CURATED`; `annotator is not None` em `SYNTHETIC_SPECIFIED`; `annotator.verified_at > labeled_at`).
  Nenhuma formulação ambígua do tipo `TypeError/ValueError` é permitida.
- `RQ-03` — **Pureza em memória (Zero I/O):** Nenhuma operação de I/O em disco, rede ou banco de dados deve ocorrer durante a instanciação e validação dos contratos.
- `RQ-04` — **Isolamento de regressão:** O baseline existente de 661 testes deve permanecer 100% GREEN sem qualquer alteração comportamental.

---

## 7. Proposta técnica

### Visão geral
O módulo `src/agent_lab/ground_truth.py` introduz a representação explícita de verdade de referência no Agent Lab Pascoal.

A arquitetura respeita a segregação das três unidades estatísticas fundamentais do sistema:

```text
┌───────────────────────────────────────────────────────────────────────────────────┐
│                                 LabelProvenance                                   │
│                     SPECIALIST_CURATED  |  SYNTHETIC_SPECIFIED                    │
└─────────────────────────────────────────┬─────────────────────────────────────────┘
                                          │
         ┌────────────────────────────────┼────────────────────────────────┐
         ▼                                ▼                                ▼
┌───────────────────────────────┐ ┌───────────────────────────────┐ ┌──────────────────────────────────────┐
│    MaterialRuleGroundTruth    │ │   DuplicatePairGroundTruth    │ │ DecisionRecommendationGroundTruth    │
├───────────────────────────────┤ ├───────────────────────────────┤ ├──────────────────────────────────────┤
│ evaluation_case_id: str       │ │ evaluation_case_id: str       │ │ evaluation_case_id: str              │
│ ground_truth_id: str          │ │ ground_truth_id: str          │ │ ground_truth_id: str                 │
│ material_id: str              │ │ material_id_a: str            │ │ material_id: str                     │
│ expected_issue_types:         │ │ material_id_b: str            │ │ expected_recommendation:             │
│   tuple[IssueType, ...]       │ │ is_duplicate: bool            │ │   GovernanceDecision                 │
│ provenance: LabelProvenance   │ │ provenance: LabelProvenance   │ │ provenance: LabelProvenance          │
│ source_reference: str         │ │ source_reference: str         │ │ source_reference: str                │
│ annotator:                    │ │ annotator:                    │ │ annotator:                           │
│   VerifiedSpecialistIdentity? │ │   VerifiedSpecialistIdentity? │ │   VerifiedSpecialistIdentity?        │
│ labeled_at: datetime          │ │ labeled_at: datetime          │ │ labeled_at: datetime                 │
│ rationale: str                │ │ rationale: str                │ │ rationale: str                       │
└───────────────────────────────┘ └───────────────────────────────┘ └──────────────────────────────────────┘
```

### Correções Normativas Obrigatórias

#### A. Identidade
`evaluation_case_id` e `ground_truth_id` possuem papéis semânticos e ontológicos distintos:
- `evaluation_case_id` identifica a amostra experimental estável;
- `ground_truth_id` identifica a emissão do gabarito produzido.
Não deve ser criada invariante artificial forçando diferença textual entre os dois identificadores (`evaluation_case_id != ground_truth_id`). Cada campo opera em seu namespace semântico próprio.

#### B. Normalização de Strings
Seguindo o padrão consolidado do projeto:
- Exigir `str` (rejeitar outros tipos com `TypeError`);
- Rejeitar vazio ou somente whitespace com `ValueError`;
- Normalizar internamente com `.strip()`.
Não se deve exigir que o chamador forneça previamente `value.strip() == value`.

#### C. Duplicidade em MDM
- Em `MaterialRuleGroundTruth`, `IssueType.POSSIBLE_DUPLICATE` é expressamente proibido em `expected_issue_types` (`ValueError`). Duplicidade nesta metrologia pertence exclusivamente à unidade `DuplicatePairGroundTruth`.
- Dois registros são considerados duplicados quando, sob o critério de identidade adotado no benchmark, representam a mesma entidade cadastral/material governada (aplicável a materiais físicos, consumíveis, peças ou itens de catálogo mestre).
- `DuplicatePairGroundTruth` representa a unidade relacional não-direcional $\{A, B\}$. Auto-referência (`material_id_a == material_id_b`) é proibida (`ValueError`). A representação canônica exige `material_id_a < material_id_b`. Pares invertidos ou iguais falham de forma *fail-closed* (`ValueError`).
- Nenhuma fábrica de conveniência (`create_duplicate_pair_ground_truth()`) deve ser incluída nesta v1, mantendo o contrato estrito.

#### D. Canonicidade de `expected_issue_types`
`expected_issue_types` deve ser `tuple[IssueType, ...]`. A ordem dos elementos não possui significado epistemológico.
- Todos os itens são previamente validados quanto a tipo (`expected_issue_types` sendo obrigatoriamente `tuple` e cada elemento sendo `IssueType` via `TypeError`), proibição de `POSSIBLE_DUPLICATE` (`ValueError`) e ausência de duplicidades (`ValueError`).
- A tupla final armazenada é deterministicamente normalizada por ordenação ascendente de `item.value`.
- Entradas válidas fora de ordem são aceitas e resultam na representação canônica ordenada.
- Tupla vazia `()` representa formalmente material conforme (`VALID`).

#### E. Proveniência Mínima Explícita e Auditável para v1
- `SPECIALIST_CURATED`: `annotator` é obrigatório, deve ser `VerifiedSpecialistIdentity` e `annotator.verified_at <= labeled_at`.
- `SYNTHETIC_SPECIFIED`: `annotator` deve ser obrigatoriamente `None`.
- `source_reference`: obrigatório e não-vazio, identificando a fonte documental, especificação ou fixture que sustenta a anotação.
- `rationale`: obrigatório e não-vazio, explicando a justificativa técnica circunstanciada do rótulo.

#### F. Ontologia e Distinções Conceituais
O sistema deve preservar explicitamente:
- `Ground Truth ≠ Prediction`
- `MaterialRuleGroundTruth ≠ GovernanceEvidence`
- `DuplicatePairGroundTruth ≠ POSSIBLE_DUPLICATE como simples rótulo material-level`
- `DecisionRecommendationGroundTruth ≠ DecisionRecommendation produzida em runtime`
- `DecisionRecommendationGroundTruth ≠ HumanDecision`
- `DecisionRecommendationGroundTruth ≠ HumanReview`
- `Ground Truth ≠ AuditEvent`
- `Dataset ≠ Metric`
- `Evaluation Contract ≠ Benchmark Result`

### Contratos de Dados Candidatos

```python
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from .domain import GovernanceDecision, IssueType
from .human_review import VerifiedSpecialistIdentity


class LabelProvenance(StrEnum):
    """Modalidade formal de proveniência do rótulo de ground truth."""

    SPECIALIST_CURATED = "SPECIALIST_CURATED"
    SYNTHETIC_SPECIFIED = "SYNTHETIC_SPECIFIED"


@dataclass(frozen=True, slots=True)
class MaterialRuleGroundTruth:
    """Gabarito de avaliação para regras cadastrais a nível de material individual."""

    evaluation_case_id: str
    ground_truth_id: str
    material_id: str
    expected_issue_types: tuple[IssueType, ...]
    provenance: LabelProvenance
    source_reference: str
    annotator: VerifiedSpecialistIdentity | None
    labeled_at: datetime
    rationale: str

    def __post_init__(self) -> None:
        ...


@dataclass(frozen=True, slots=True)
class DuplicatePairGroundTruth:
    """Gabarito de avaliação para duplicidade a nível de par não-direcional de materiais."""

    evaluation_case_id: str
    ground_truth_id: str
    material_id_a: str
    material_id_b: str
    is_duplicate: bool
    provenance: LabelProvenance
    source_reference: str
    annotator: VerifiedSpecialistIdentity | None
    labeled_at: datetime
    rationale: str

    def __post_init__(self) -> None:
        ...


@dataclass(frozen=True, slots=True)
class DecisionRecommendationGroundTruth:
    """Gabarito de avaliação para a recomendação algorítmica esperada de governança."""

    evaluation_case_id: str
    ground_truth_id: str
    material_id: str
    expected_recommendation: GovernanceDecision
    provenance: LabelProvenance
    source_reference: str
    annotator: VerifiedSpecialistIdentity | None
    labeled_at: datetime
    rationale: str

    def __post_init__(self) -> None:
        ...
```

### Arquivos previstos
- `src/agent_lab/ground_truth.py` — novo módulo contendo `LabelProvenance` e os 3 contratos de ground truth;
- `src/agent_lab/__init__.py` — exportação pública canônica dos 4 símbolos;
- `tests/test_ground_truth.py` — suíte de testes unitários defensivos para validação das invariantes;
- `docs/specs/0115_ground_truth_evaluation_contract_v1.md` — esta especificação técnica.

---

## 8. Estratégia de testes e TDD

A estratégia de testes seguirá rigorosamente o fluxo de micro-TDD do Agent Lab Pascoal:

### Vermelho (RED)
1. Criar `tests/test_ground_truth.py` exercitando os novos contratos antes da implementação do módulo `src/agent_lab/ground_truth.py`;
2. Executar `python -m unittest tests/test_ground_truth.py -v` e comprovar falha por ausência do módulo/classes (`ModuleNotFoundError` / `ImportError`).

### Verde (GREEN)
1. Implementar `src/agent_lab/ground_truth.py` com dataclasses congeladas, validações em `__post_init__` e normalização defensiva de strings via `.strip()`;
2. Exportar símbolos em `src/agent_lab/__init__.py`;
3. Executar o teste específico até que 100% dos novos testes passem.

### Regressão
Executar a suíte canônica completa:
```powershell
python -m unittest discover -s tests -v
```
Confirmar que todos os 661 testes anteriores continuam GREEN, totalizando `661 + N` testes aprovados.

### Cenários de teste previstos
1. **`MaterialRuleGroundTruth` válido:**
   - com tupla de `expected_issue_types` válida;
   - com tupla de `expected_issue_types` fornecida fora de ordem, comprovando normalização determinística por `IssueType.value`;
   - com tupla vazia `()` representando material conforme (`VALID`);
   - modalidade `SPECIALIST_CURATED` com `VerifiedSpecialistIdentity` e `verified_at <= labeled_at`;
   - modalidade `SYNTHETIC_SPECIFIED` com `annotator=None`.
2. **`MaterialRuleGroundTruth` inválido:**
   - passagem de coleção que não seja `tuple` (ex.: `list`, `set`) para `expected_issue_types` (`TypeError`);
   - tentativa de incluir `IssueType.POSSIBLE_DUPLICATE` em `expected_issue_types` (`ValueError`);
   - itens que não sejam `IssueType` (`TypeError`);
   - duplicatas internas em `expected_issue_types` (`ValueError`);
   - campo textual não `str` (`TypeError`);
   - strings vazias ou somente whitespace em campos textuais (`ValueError`);
   - `provenance` não `LabelProvenance` (`TypeError`);
   - timestamp não `datetime` (`TypeError`);
   - timestamp naive (`ValueError`);
   - `SPECIALIST_CURATED` com `annotator=None` (`ValueError`);
   - `SPECIALIST_CURATED` com `annotator` de tipo incorreto (`TypeError`);
   - `SPECIALIST_CURATED` com `verified_at > labeled_at` (`ValueError`);
   - `SYNTHETIC_SPECIFIED` com `annotator` preenchido (`ValueError`).
3. **`DuplicatePairGroundTruth` válido:**
   - par com `material_id_a < material_id_b` e `is_duplicate=True`;
   - par com `material_id_a < material_id_b` e `is_duplicate=False`.
4. **`DuplicatePairGroundTruth` inválido:**
   - auto-referência `material_id_a == material_id_b` (`ValueError`);
   - par invertido `material_id_a > material_id_b` (`ValueError`);
   - par com igualdade `material_id_a == material_id_b` (`ValueError`);
   - `is_duplicate` que não seja booleano estrito (`TypeError`);
   - campo textual não `str` (`TypeError`);
   - strings vazias ou somente whitespace em campos textuais (`ValueError`);
   - `provenance` não `LabelProvenance` (`TypeError`);
   - timestamp não `datetime` (`TypeError`);
   - timestamp naive (`ValueError`);
   - violações de proveniência e annotator idênticas às demais entidades.
5. **`DecisionRecommendationGroundTruth` válido:**
   - para cada membro de `GovernanceDecision` (`APPROVE`, `REVIEW`, `REJECT`).
6. **`DecisionRecommendationGroundTruth` inválido:**
   - `expected_recommendation` que não seja `GovernanceDecision` (inclusive `HumanDecision` deve levantar `TypeError`);
   - campo textual não `str` (`TypeError`);
   - strings vazias ou somente whitespace em campos textuais (`ValueError`);
   - `provenance` não `LabelProvenance` (`TypeError`);
   - timestamp não `datetime` (`TypeError`);
   - timestamp naive (`ValueError`);
   - violações de proveniência e annotator idênticas às demais entidades.
7. **Imutabilidade:**
   - tentativa de atribuir ou modificar campos em qualquer das instâncias deve levantar `FrozenInstanceError`.

---

## 9. Gates de qualidade

Antes da submissão do Pull Request, os seguintes comandos devem ser executados e validados:

```powershell
python -m unittest discover -s tests -v
git diff --check
git status -sb
```

Critérios de aprovação dos gates:
- Suíte completa 100% GREEN (sem skips, sem warnings inesperados);
- `git diff --check` sem nenhum erro de trailing whitespace ou quebras de linha impróprias;
- Alterações restritas aos arquivos autorizados na SPEC;
- Nenhuma alteração em `data_io.py`, `baseline.py`, `rules.py`, `duplicates.py`, `decision.py`, `evidence.py` ou `PROJECT_COMPASS.md`.

---

## 10. Riscos epistemológicos e estatísticos

| Risco ou limitação | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| **Contaminação de escopo (duplicidade em regras)** | Média | Alto | Bloqueio explícito de `IssueType.POSSIBLE_DUPLICATE` em `MaterialRuleGroundTruth` via `ValueError` em tempo de instanciação. |
| **Distorção combinatória em duplicidade** | Alta | Alto | Exigência fail-closed da ordenação canônica $A < B$, impedindo que pares espelhados $(B, A)$ gerem dupla contagem ou assimetria no espaço amostral. |
| **Confusão entre recomendação e decisão humana** | Média | Alto | Nomeação estrita como `DecisionRecommendationGroundTruth` com tipo de destino `GovernanceDecision`, recusando formalmente `HumanDecision` com `TypeError`. |
| **Falsa proveniência ou anotação sem autoria** | Média | Médio | Validação condicional que obriga `VerifiedSpecialistIdentity` para anotações humanas e proíbe annotator para anotações sintéticas, combinada com `source_reference` e `rationale` compulsórios. |
| **Quebra acidental do baseline legado** | Baixa | Alto | Declaração explícita de que `data_io.py` e `baseline.py` não devem ser modificados nesta Issue. |

---

## 11. Plano de reversão

Por se tratar de um incremento puramente aditivo em módulo isolado (`src/agent_lab/ground_truth.py`), a reversão pode ser efetuada atomicamente via Git:
1. Reverter o merge commit do PR na branch `main`;
2. A exclusão de `src/agent_lab/ground_truth.py` e de `tests/test_ground_truth.py` restabelece o baseline de 661 testes sem nenhum efeito colateral em arquivos existentes.

---

## 12. Versionamento e release

### Impacto SemVer
- Potencial impacto SemVer: candidato a `MINOR`, a ser decidido na consolidação de release.

### Publicação prevista
- Versão planejada: `Unreleased`. O próximo marco e versionamento formal serão decididos em planejamento e closeout posterior.
- Criação de tag: Não (nenhuma tag nesta Issue).
- Atualização do `PROJECT_COMPASS.md`: Apenas no closeout documental após merge da Issue #115.

---

## 13. Critérios de aceite

- [ ] Issue #115 criada no GitHub e vinculada a esta SPEC;
- [ ] Branch `feature/issue-115-ground-truth-evaluation-contract` criada a partir de `aeef2f2`;
- [ ] Módulo `src/agent_lab/ground_truth.py` implementado contendo `LabelProvenance`, `MaterialRuleGroundTruth`, `DuplicatePairGroundTruth` e `DecisionRecommendationGroundTruth`;
- [ ] Separação estrita de escopo: `POSSIBLE_DUPLICATE` proibido em `MaterialRuleGroundTruth` com `ValueError`;
- [ ] Canonicidade determinística de `expected_issue_types` validada e normalizada por `IssueType.value`;
- [ ] Duplicidade canônica fail-closed $A < B$ validada em `DuplicatePairGroundTruth` com `ValueError`;
- [ ] Proveniência mínima explícita e auditável para v1 validada com `VerifiedSpecialistIdentity` condicional e validação de tipo estrito de `provenance` com `TypeError`;
- [ ] Compulsoriedade de `source_reference` e `rationale` validada;
- [ ] `evaluation_case_id` e `ground_truth_id` presentes e distintos conceitualmente nos 3 contratos;
- [ ] Testes unitários defensivos em `tests/test_ground_truth.py` cobrindo cenários válidos, inválidos e imutabilidade;
- [ ] Baseline de 661 testes anteriores mantido 100% GREEN;
- [ ] `git diff --check` aprovado sem trailing whitespace;
- [ ] Nenhum código de `data_io.py`, `baseline.py`, `rules.py`, `duplicates.py`, `decision.py` ou `PROJECT_COMPASS.md` alterado;
- [ ] Revisão humana prévia da SPEC aprovada antes de qualquer implementação.

---

## 14. Questões em aberto

- `Nenhuma`. Todas as decisões normativas e correções arquiteturais foram saneadas e aprovadas no Architectural Alignment Gate de 10/09/2026.

---

## 15. Histórico de decisões

| Data | Decisão | Motivo | Responsável |
|---|---|---|---|
| `2026-09-10` | Aprovação do Architectural Alignment Gate para Ground Truth Evaluation Contract v1 | Abertura formal da frente de Ground truth e benchmark no Roadmap. | `Jk-Pascoal` |
| `2026-09-10` | Proibição de `IssueType.POSSIBLE_DUPLICATE` em `MaterialRuleGroundTruth` | Regras operam na unidade material individual; duplicidade é relação de par. | `Jk-Pascoal` |
| `2026-09-10` | Simplificação da proveniência para `SPECIALIST_CURATED` e `SYNTHETIC_SPECIFIED` | `CONSENSUS_PANEL` e `HISTORICAL_ADJUDICATED` exigem modelagem multi-anotador futura. | `Jk-Pascoal` |
| `2026-09-10` | Renomeação para `DecisionRecommendationGroundTruth` avaliando `GovernanceDecision` | Evitar confusão com a decisão humana final soberana (`HumanDecision`). | `Jk-Pascoal` |
| `2026-09-10` | Segregação entre `evaluation_case_id` e `ground_truth_id` nos três contratos | Preservar a identidade do caso experimental separada da anotação produzida. | `Jk-Pascoal` |
| `2026-09-10` | Preservação intocada da metrologia legada (`data_io.py` / `baseline.py`) | Evitar acoplamento prematuro e manter migração para etapa posterior formal. | `Jk-Pascoal` |
| `2026-09-10` | Revisão documental pré-TDD: ground truth não restrito a humano, separação canônica de expected_issue_types e política inequívoca de exceções | Blindagem metrológica e eliminação de ambiguidades antes do primeiro teste RED. | `Jk-Pascoal` |
