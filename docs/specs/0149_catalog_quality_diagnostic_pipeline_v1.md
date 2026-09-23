# SPEC-0149 — Catalog Quality Diagnostic Pipeline v1

> Especificação técnica do primeiro pipeline determinístico de domínio e boundary de aplicação
> para diagnóstico consolidado de qualidade cadastral sobre coleções de materiais no Agent Lab Pascoal.

---

## Metadados

| Campo | Valor |
|---|---|
| **Identificador** | `SPEC-0149` |
| **Status** | `IMPLEMENTED` |
| **Issue relacionada** | `#149` |
| **Título da Issue** | `Catalog Quality Diagnostic Pipeline v1` |
| **Branch documental** | `docs/issue-149-catalog-quality-diagnostic-pipeline-closeout` |
| **Responsável** | `Jk-Pascoal` |
| **Data de criação** | `2026-09-23` |
| **Última atualização** | `2026-09-23` |
| **Data de integração** | `2026-09-23` |
| **Domínio** | Governança de materiais industriais PDM/BOM e Master Data |
| **Camada arquitetural** | Domínio e Camada de Aplicação (`Domain Layer`, `Application Layer`) |
| **Baseline de entrada** | `1102 testes aprovados` (100% GREEN) |
| **Baseline final integrado** | `1173 testes aprovados` (100% GREEN) |
| **PR documental de aprovação** | `#150` — merge commit `469122514b8b8bc1339295558fe043af5882cba5` |
| **PR funcional integrada** | `#151` — merge commit `89b844e1097f36cbc7d17551bc7b7517fa9402d4` |
| **PR documental de closeout** | `A ser aberto contra main` |
| **Impacto SemVer** | `MINOR — novas capacidades públicas aditivas de diagnóstico em lote; release formal permanece v0.1.0` |
| **Runner oficial** | `python -m unittest discover -s tests -v` (Python 3.11) |

---

## 1. Contexto

O **Agent Lab Pascoal** estabeleceu em seu núcleo de governança de materiais industriais um conjunto consolidado de componentes de validação, similaridade determinística e deliberação humana em memória:
1. **Regras e Validação Determinística:** O módulo `src/agent_lab/rules.py` aplica verificações estruturais e técnicas em registros cadastrais (`MaterialRecord`), gerando `GovernanceIssue` com severidades tipadas (`BLOCKING`, `WARNING`, `INFO`);
2. **Detecção de Duplicidades:** O módulo `src/agent_lab/duplicates.py` define o comparador semântico determinístico `is_possible_duplicate(incoming, existing)` e o seletor `find_duplicate_candidates(incoming, existing_records)`;
3. **Orquestração de Evidências e Avaliação Unitária:** A classe `DeterministicGovernanceValidator` em `src/agent_lab/validator.py` compõe regras e duplicidades, constrói a `EvidenceCollection` tipada e emite o `GovernanceAssessment` individual contendo uma `GovernanceDecision` sistêmica (`APPROVE`, `REVIEW`, `REJECT`), que representa a recomendação do sistema e nunca uma decisão humana final;
4. **Trilhas Append-Only e Human-in-the-Loop:** Ciclo de vida (`GovernanceWorkflow`), auditoria (`AuditEvent`), assunção (`HumanReviewClaim`), liberação (`HumanReviewClaimRelease`) e revisões cadastrais (`MaterialRevision`) operam com persistência durável em JSONL e leitura release-aware (Issue #145).

Baseline de entrada verificado e auditado na branch `main`:
```text
Ran 1102 tests in 3.006s
OK
```

Paralelamente, a **Seção 14 do `PROJECT_COMPASS.md`** (*Esteira evolutiva*) define como sua primeira frente oficial e prioritária:
> `PoC vendável de diagnóstico de qualidade cadastral`

Até a Issue #145, o sistema operava predominantemente sobre avaliações per-material ou sobre benchmarks sintéticos unitários. A transição para um laboratório capaz de diagnosticar bases cadastrais e apoiar decisões em escala industrial exige um boundary vertical voltado ao nível de catálogo fechado.

---

## 2. Problema, Evidências e Impacto

### 2.1 Problema
O Agent Lab Pascoal não dispõe de um pipeline de domínio nem de um caso de uso na camada de aplicação capaz de receber uma coleção fechada de materiais (`Sequence[MaterialRecord]`), executar a análise de governança com simetria catalog-wide e emitir um relatório executivo estruturado e determinístico (`CatalogQualityReport`).

### 2.2 Evidências no Código Real
1. O método existente `DeterministicGovernanceValidator.analyze_all(records: list[MaterialRecord])` em `src/agent_lab/validator.py` foi desenhado como um baseline streaming/sequencial: ele compara o registro $N$ apenas contra os registros precedentes $1 \dots N-1$. Isso gera uma **assimetria direcional** na detecção de duplicidades: se `MAT-0001` e `MAT-0002` são idênticos, `MAT-0001` não aponta candidatos e não recebe a issue `POSSIBLE_DUPLICATE`, enquanto `MAT-0002` aponta `MAT-0001`. Em um diagnóstico de catálogo fechado, ambos são mutuamente duplicatas;
2. `analyze_all()` retorna uma lista desarticulada `list[GovernanceAssessment]`, sem nenhuma estrutura de relatório executivo de catálogo;
3. Inexistência de um read-model imutável que sintetize métricas agregadas da coleção (total de registros, registros limpos, registros com issues impeditivas, distribuição de severidades e tipos, e pares canônicos de duplicidade);
4. Inexistência de um boundary de aplicação (`DiagnoseCatalogQualityUseCase`) que forneça um ponto estável para futuros adaptadores de ingestão (como leitores de arquivos CSV/Excel).

### 2.3 Impacto
* Ausência do elo fundamental para viabilizar a PoC vendável de diagnóstico cadastral;
* Análises ad-hoc obrigariam scripts e adaptadores externos a reimplementar contagens e tentar resolver assimetrias de duplicidade fora do domínio;
* Risco de violação do princípio de que *Application coordena; Pipeline produz*.

---

## 3. Objetivo

Desenvolver e integrar no Agent Lab Pascoal o primeiro vertical determinístico de diagnóstico de qualidade de catálogo, compreendendo:
1. **Read-Model de Domínio `CatalogQualityReport`:** dataclass imutável armazenando exclusivamente `catalog_id` e a tupla canônica de `assessments`, validando de forma fail-closed a integridade estrutural de `assessment.material_id`, bem como a integridade relacional simétrica de `duplicate_candidates`, derivando todas as métricas, contagens e pares duplicados via `@property` puras com mappings imutáveis (`MappingProxyType`);
2. **Pipeline de Domínio `diagnose_catalog_quality`:** função pura em memória que valida as precondições estruturais de `material_id` e a unicidade do catálogo, ordena os registros lexicograficamente e reutiliza uma única instância de `DeterministicGovernanceValidator` para executar `analyze(record, other_records)` para cada item contra todos os demais registros do catálogo fechado em lista compatível (`list[MaterialRecord]`), garantindo simetria absoluta e preservação integral de `GovernanceIssue(POSSIBLE_DUPLICATE)` e `EvidenceSource.DUPLICATE`;
3. **Application Boundary `DiagnoseCatalogQualityUseCase`:** caso de uso de aplicação para coordenação da borda de entrada, validação estrutural de tipos e elementos, injeção opcional de pipeline via protocolo tipado `CatalogDiagnosticPipeline` (com suporte a argumento keyword-only) e validação fail-closed da saída do pipeline injetado (tipo, `catalog_id` e casamento de identidades de materiais).

Toda a capacidade opera estritamente em memória (zero-I/O), com determinismo absoluto, validação *fail-closed* e zero mutação de entidades existentes.

---

## 4. Resposta aos 8 Critérios do PROJECT_COMPASS (§ 15)

1. **Qual limitação atual resolve?**
   Resolve a ausência de um boundary de diagnóstico de catálogo fechado e a assimetria na detecção de duplicidades herdada do processamento sequencial de `analyze_all()`.
2. **Qual evidência demonstra que a limitação importa agora?**
   A esteira evolutiva do Compass elenca a *PoC vendável de diagnóstico de qualidade cadastral* como sua prioridade nº 1. Com a frente de governança HITL consolidada até a Issue #145, o diagnóstico de coleções é o pré-requisito lógico direto para conectar dados industriais.
3. **Qual é a menor entrega vertical testável?**
   O read-model `CatalogQualityReport`, o pipeline puro `diagnose_catalog_quality` e o boundary fino `DiagnoseCatalogQualityUseCase` operando em memória sobre `Sequence[MaterialRecord]`.
4. **Quais invariantes existentes deve preservar?**
   - `Application coordena; Pipeline produz; Evaluator mede`;
   - `MaterialRecord` é imutável (`frozen=True, slots=True`) e nunca é mutado ou sanitizado silenciosamente;
   - Pureza estrita em memória (zero-I/O físico);
   - Determinismo absoluto: a ordem de entrada dos registros no catálogo não altera o resultado;
   - Não inventar decisão humana nem abrir instâncias de `GovernanceWorkflow`;
   - Manter 100% intactos o comportamento e a assinatura de `DeterministicGovernanceValidator.analyze_all()`.
5. **O que ficará explicitamente fora do escopo?**
   Leitura física de arquivos (CSV, Excel), dependências externas (pandas/polars), bancos de dados (SQL), integrações ERP, UI/Streamlit, REST APIs, otimizações prematuras de similaridade (blocking, ANN, embeddings), paralelismo/multiprocessing e alteração de código legado.
6. **Como saberemos que a implementação funcionou?**
   Quando uma suíte abrangente de testes unitários e de integração comprovar: validações fail-closed, relatório vazio coerente, contagens exatas por severidade e tipo, simetria comprovada de candidatos a duplicidade ($A \rightarrow B$ e $B \rightarrow A$), rejeição explícita de relações assimétricas ou órfãs, derivação lexicográfica canônica de `duplicate_pairs` ($a < b$), invariância à permutação de entrada e zero regressão no baseline de 1102 testes GREEN.
7. **Quantos novos riscos operacionais introduz?**
   Mínimos. Todo o processamento é em memória e determinístico, sem I/O e sem concorrência.
8. **A nova camada pode ser removida ou substituída sem corromper o domínio?**
   Sim. O pipeline e o read-model compõem os contratos fundamentais existentes (`MaterialRecord`, `GovernanceAssessment`) sem mutá-los.

---

## 5. Arquitetura e Contratos Detalhados

### 5.1 Diagrama de Camadas e Fluxo de Execução

```text
Camada de Aplicação (Application Layer):
Caller (CLI / Teste / Futuro CSV Adapter)
        │
        ▼
DiagnoseCatalogQualityUseCase.execute(catalog, *, catalog_id)
        │  [Validação de borda: collections.abc.Sequence[MaterialRecord], catalog_id]
        ▼
Protocol: CatalogDiagnosticPipeline
        │
        ▼
Camada de Domínio (Domain Layer):
diagnose_catalog_quality(catalog, *, catalog_id)
        │
        ├─► Validação estrutural prévia de cada record.material_id:
        │       str obrigatória, não-vazia, sem whitespace externo (ValueError/TypeError)
        ├─► Validação fail-closed: unicidade de material_id (ValueError se colisão)
        ├─► Ordenação canônica: sorted_catalog = tuple(sorted(catalog, key=material_id))
        │
        ├─► validator = DeterministicGovernanceValidator()  (instância única reutilizada)
        ├─► Para cada record R em sorted_catalog:
        │       other_records: list[MaterialRecord] = [m for m in sorted_catalog if m.material_id != R.material_id]
        │       assessment = validator.analyze(R, other_records)
        │
        └─► CatalogQualityReport(catalog_id=normalized_catalog_id, assessments=tuple(assessments))
                    │  [__post_init__ valida ordenação, unicidade, integridade de IDs e simetria]
                    │
                    ├──► @property duplicate_pairs: tuple[tuple[str, str], ...] (derivado limpo)
                    ├──► @property total_records, clean_records_count, ...
                    └──► @property issues_by_severity, issues_by_type (MappingProxyType)
        │
        ▼
DiagnoseCatalogQualityUseCase (Validação de Saída da Borda):
        ├─► Valida se result é CatalogQualityReport (TypeError)
        ├─► Valida se result.catalog_id == canonical_catalog_id (ValueError)
        └─► Valida se result.assessments material_ids casam 1:1 com catalog material_ids (ValueError)
```

---

### 5.2 Read-Model de Domínio: `CatalogQualityReport`

Módulo: `src/agent_lab/catalog_quality.py`

#### 5.2.1 Estrutura e Fatos Mínimos Armazenados
O relatório armazena **estritamente dois fatos fundamentais**, tornando impossível o descompasso interno entre dados armazenados e métricas derivadas:

```python
@dataclass(frozen=True, slots=True)
class CatalogQualityReport:
    catalog_id: str
    assessments: tuple[GovernanceAssessment, ...]
```

#### 5.2.2 Validações em `__post_init__` (Estritamente Fail-Closed)
1. **`catalog_id`:**
   - Deve ser estritamente `str` (rejeita não-`str` e `bool` com `TypeError`);
   - Normalizado via `.strip()`;
   - Não pode ser vazio ou conter apenas whitespace (rejeição com `ValueError`);
   - Gravado imutável via `object.__setattr__(self, "catalog_id", normalized_id)`.
2. **`assessments`:**
   - Deve ser estritamente `tuple` (rejeita listas, sets ou geradores com `TypeError`);
   - Todos os elementos devem ser instâncias de `GovernanceAssessment` (`TypeError` caso contrário);
   - **Integridade estrutural de `assessment.material_id`:** Antes de ordenação, unicidade ou validação relacional, valida para cada `assessment`:
     - `assessment.material_id` deve ser `str` (rejeita não-`str` e `bool` com `TypeError`);
     - Não pode ser vazio ou composto exclusivamente por whitespace (rejeição com `ValueError`);
     - Deve estar em forma canônica sem whitespace externo: `assessment.material_id == assessment.material_id.strip()`. Presença de whitespace externo levanta `ValueError` imediatamente;
   - Deve respeitar a ordem canônica lexicográfica ascendente por `material_id` (`material_id ASC`), rejeitando tuplas desordenadas com `ValueError`;
   - Deve respeitar a unicidade estrita de `material_id`, rejeitando repetições com `ValueError`;
   - Tupla vazia `()` é perfeitamente válida para representar catálogo vazio.
3. **Integridade Relacional Estrita de `duplicate_candidates` (Fail-Closed):**
   Para cada `assessment` em `self.assessments`:
   - `assessment.duplicate_candidates` deve ser uma `tuple` de strings (rejeição com `TypeError`);
   - **Anti-auto-referência:** nenhum candidato pode ser igual ao próprio `assessment.material_id` (rejeição com `ValueError`);
   - **Anti-órfão:** todo `candidate_id` deve existir no conjunto de `material_id` dos assessments do relatório (rejeição com `ValueError`);
   - **Unicidade interna:** `duplicate_candidates` não pode conter identificadores duplicados (rejeição com `ValueError`);
   - **Ordenação canônica:** `duplicate_candidates` deve estar ordenado lexicograficamente ascendente (rejeição com `ValueError`);
   - **Simetria relacional compulsória:** para todo `candidate_id` presente em `A.duplicate_candidates`, o identificador `A.material_id` deve estar obrigatoriamente presente nos `duplicate_candidates` do assessment correspondente àquele candidato. Relações assimétricas ($A \rightarrow B$ sem $B \rightarrow A$) levantam imediatamente `ValueError`.

#### 5.2.3 Propriedades Derivadas (`@property`)
Todas as métricas são computadas sob demanda sobre `self.assessments`:

* **`total_records -> int`:** `len(self.assessments)`
* **`is_empty -> bool`:** `self.total_records == 0`
* **`clean_records_count -> int`:** contagem de assessments onde `len(assessment.issues) == 0`.
* **`records_with_blocking_issues_count -> int`:** contagem de assessments que possuem ao menos uma issue com `severity == IssueSeverity.BLOCKING`.
* **`records_with_non_blocking_issues_count -> int`:** contagem de assessments que possuem issues (`len(assessment.issues) > 0`), mas nenhuma delas possui severidade `BLOCKING` (apenas `WARNING` e/ou `INFO`).
  *(Nota de domínio: o nome reflete estritamente a taxonomia de severidade, eliminando o termo ambíguo "review" que pertence ao fluxo HITL).*
* **`duplicate_candidate_records_count -> int`:** contagem de assessments com `len(assessment.duplicate_candidates) > 0`.
* **`total_issues_count -> int`:** soma total de issues em todos os assessments (`sum(len(a.issues) for a in self.assessments)`).
* **`issues_by_severity -> Mapping[IssueSeverity, int]`:** mapeamento read-only de cada `IssueSeverity` presente para sua contagem de ocorrências, encapsulado defensivamente em `types.MappingProxyType`. Chaves com contagem zero não figuram no mapeamento. Se vazio, retorna `MappingProxyType({})`.
* **`issues_by_type -> Mapping[IssueType, int]`:** mapeamento read-only de cada `IssueType` presente para sua contagem de ocorrências, encapsulado em `types.MappingProxyType`. Se vazio, retorna `MappingProxyType({})`.
* **`clean_records_ratio -> float | None`:** proporção de registros limpos (`clean_records_count / total_records`). Se `is_empty`, retorna estritamente `None`.
* **`average_completeness -> float | None`:** média aritmética de completude (`sum(a.completeness for a in self.assessments) / total_records`). Se `is_empty`, retorna estritamente `None`.

#### 5.2.4 Derivação Canônica de `duplicate_pairs` e `duplicate_pairs_count`
Como a integridade relacional simétrica e anti-órfã é estritamente garantida no `__post_init__`, a propriedade `duplicate_pairs` não necessita de filtragens defensivas silenciosas. Ela é derivada diretamente:
```python
@property
def duplicate_pairs(self) -> tuple[tuple[str, str], ...]:
    pairs: set[tuple[str, str]] = set()
    for assessment in self.assessments:
        m_id = assessment.material_id
        for candidate_id in assessment.duplicate_candidates:
            if m_id < candidate_id:
                pairs.add((m_id, candidate_id))
    return tuple(sorted(pairs))

@property
def duplicate_pairs_count(self) -> int:
    return len(self.duplicate_pairs)
```
Invariantes garantidas:
- Menor ID sempre na primeira posição ($material\_id\_a < material\_id\_b$);
- Unicidade de cada par (eliminando duplicações via `set`);
- Ordenação canônica estável e lexicográfica garantida por `sorted()`;
- Se `is_empty`, retorna `()`.

---

### 5.3 Pipeline de Domínio: `diagnose_catalog_quality`

Módulo: `src/agent_lab/catalog_quality.py`

#### 5.3.1 Assinatura e Contrato
```python
def diagnose_catalog_quality(
    catalog: Sequence[MaterialRecord],
    *,
    catalog_id: str,
) -> CatalogQualityReport:
```

#### 5.3.2 Regras de Execução e Responsabilidades
1. **Validação defensiva de entrada (*fail-closed*):**
   - `catalog` deve ser uma `collections.abc.Sequence` (rejeita não-`Sequence`, e rejeita explicitamente `str`, `bytes`, `bytearray` com `TypeError`);
   - Todos os elementos devem ser instâncias de `MaterialRecord` (`TypeError` para elementos inválidos);
   - `catalog_id` deve ser string não-vazia após `.strip()` (`TypeError` para não-string/bool, `ValueError` para string vazia);
2. **Precondição estrutural estrita sobre `material_id`:**
   - Antes de qualquer ordenação ou teste de unicidade, inspeciona o `material_id` de cada registro:
     - Deve ser `str` (rejeita `bool` e não-`str` com `TypeError`);
     - Não pode ser vazio ou composto exclusivamente por whitespace (`ValueError`);
     - Deve estar em forma canônica: `record.material_id == record.material_id.strip()`. Presença de whitespace externo levanta `ValueError` imediatamente. Como `MaterialRecord` é um registro bruto imutável, o pipeline **não muta nem sanitiza silenciosamente** a entidade recebida.
3. **Validação de unicidade de identidade:**
   - O pipeline itera sobre os materiais coletando `seen_ids: set[str]`. Se encontrar repetição de `material_id`, interrompe imediatamente levantando `ValueError(f"duplicate material_id in catalog: {record.material_id!r}")`.
4. **Ordenação canônica de entrada:**
   - Cria uma tupla ordenada `sorted_catalog = tuple(sorted(catalog, key=lambda r: r.material_id))`.
5. **Análise de catálogo fechado com instância única reutilizada:**
   - Instancia o validador uma única vez antes do loop:
     `validator = DeterministicGovernanceValidator()`
   - Para cada registro `record` em `sorted_catalog`:
     - Constrói a lista de referência com todos os demais itens do catálogo ordenado:
       `other_records: list[MaterialRecord] = [m for m in sorted_catalog if m.material_id != record.material_id]`
     - Invoca a análise determinística:
       `assessment = validator.analyze(record, other_records)`
     - *Compatibilidade estrita de tipo:* `other_records` é uma `list[MaterialRecord]`, satisfazendo perfeitamente a anotação `existing_records: list[MaterialRecord] | None` de `DeterministicGovernanceValidator.analyze()`, sem exigir alteração de assinatura ou coerção no validator.
   - Como `sorted_catalog` está ordenado por `material_id ASC`, `other_records` preserva a ordem lexicográfica. Consequentemente, `find_duplicate_candidates()` retorna a tupla de candidatos naturalmente ordenada.
   - Como $A$ é testado contra $B$ e $B$ é testado contra $A$, ambos recebem o candidato correspondente, ambos emitem a issue `POSSIBLE_DUPLICATE` e ambos geram a evidência com `EvidenceSource.DUPLICATE`.
6. **Construção do Relatório:**
   - Retorna `CatalogQualityReport(catalog_id=catalog_id.strip(), assessments=tuple(assessments))`.

---

### 5.4 Camada de Aplicação: `DiagnoseCatalogQualityUseCase`

Módulo: `src/agent_lab/catalog_quality_use_case.py`

#### 5.4.1 Protocolo Estrutural de Injeção
Para suportar parâmetros keyword-only de forma type-safe em conformidade com Python 3.11, define-se o protocolo:

```python
from collections.abc import Sequence
from typing import Protocol

class CatalogDiagnosticPipeline(Protocol):
    """Protocolo estrutural para pipelines de diagnóstico de qualidade de catálogo."""

    def __call__(
        self,
        catalog: Sequence[MaterialRecord],
        *,
        catalog_id: str,
    ) -> CatalogQualityReport:
        ...
```

#### 5.4.2 Caso de Uso e Validação de Saída da Borda
```python
class DiagnoseCatalogQualityUseCase:
    """Caso de uso para coordenação da análise de qualidade de catálogo."""

    def __init__(
        self,
        pipeline: CatalogDiagnosticPipeline | None = None,
    ) -> None:
        self._pipeline = pipeline if pipeline is not None else diagnose_catalog_quality

    def execute(
        self,
        catalog: Sequence[MaterialRecord],
        *,
        catalog_id: str,
    ) -> CatalogQualityReport:
        # Validação estrutural de borda na entrada
        if not isinstance(catalog, Sequence) or isinstance(catalog, (str, bytes, bytearray)):
            raise TypeError("catalog must be a Sequence of MaterialRecord, excluding str and bytes")
        for record in catalog:
            if not isinstance(record, MaterialRecord):
                raise TypeError("all items in catalog must be MaterialRecord instances")
        if not isinstance(catalog_id, str) or isinstance(catalog_id, bool):
            raise TypeError("catalog_id must be a str")

        canonical_catalog_id = catalog_id.strip()
        if not canonical_catalog_id:
            raise ValueError("catalog_id must not be empty or whitespace")

        # Delegação estrita ao pipeline produtor
        result = self._pipeline(catalog, catalog_id=canonical_catalog_id)

        # Validação defensiva de borda na saída do pipeline (fronteira de confiança)
        if not isinstance(result, CatalogQualityReport):
            raise TypeError(
                f"pipeline return must be a CatalogQualityReport, got {type(result).__name__}"
            )
        if result.catalog_id != canonical_catalog_id:
            raise ValueError(
                f"pipeline returned report with mismatched catalog_id: expected {canonical_catalog_id!r}, "
                f"got {result.catalog_id!r}"
            )

        expected_material_ids = tuple(sorted(record.material_id for record in catalog))
        actual_material_ids = tuple(assessment.material_id for assessment in result.assessments)
        if actual_material_ids != expected_material_ids:
            raise ValueError(
                f"pipeline returned report with mismatched material_ids: expected {expected_material_ids!r}, "
                f"got {actual_material_ids!r}"
            )

        return result
```

---

### 5.5 Política Canônica Unificada de Normalização de `catalog_id`

Para impedir qualquer divergência ou semântica ambígua entre os pontos de entrada:
* **Regra canônica:** deve ser `str` (rejeita não-`str` e `bool` com `TypeError`), normalizada via `.strip()`, e não pode ser vazia ou conter exclusivamente whitespace (rejeição com `ValueError`);
* **Autodefesa em múltiplas camadas:**
  - `CatalogQualityReport.__post_init__` aplica essa regra ao ser construído diretamente;
  - `diagnose_catalog_quality` aplica essa regra ao ser invocado diretamente;
  - `DiagnoseCatalogQualityUseCase.execute` aplica essa regra na borda da aplicação antes de delegar ao pipeline e valida a paridade no retorno.

---

## 6. Complexidade Computacional e Justificativa

* **Complexidade no v1:** A análise de duplicidades contra todos os demais registros executa $n$ chamadas de `analyze()`, cada uma inspecionando $n-1$ registros, resultando em complexidade temporal de $O(n^2)$.
* **Decisão deliberada:** Esta complexidade é aceita conscientemente no primeiro slice vertical em prol da correção semântica perfeita, determinismo e reutilização estrita dos componentes canônicos sem alteração de código legado;
* **Ficam expressamente fora de escopo no v1:**
  - Blocking ou particionamento heurístico de candidatos;
  - Índices invertidos de similaridade;
  - Busca vetorial (ANN), embeddings ou modelos semânticos;
  - Multiprocessing, multithreading ou processamento assíncrono;
  - Caching ou otimizações prematuras de performance.

---

## 7. Preservação das Capacidades e Módulos Existentes

Fica expressamente estabelecido que esta Issue **não altera**:
* `src/agent_lab/rules.py` (funções de regra continuam canônicas e inalteradas);
* `src/agent_lab/duplicates.py` (funções `is_possible_duplicate` e `find_duplicate_candidates` continuam inalteradas; nenhuma nova função é adicionada neste módulo);
* `src/agent_lab/validator.py` (`DeterministicGovernanceValidator.analyze()` e `analyze_all()` permanecem 100% inalterados);
* `src/agent_lab/evidence.py` (`build_evidence_collection` continua inalterado);
* `src/agent_lab/baseline.py` e `src/agent_lab/data_io.py` permanecem 100% inalterados.

A funcionalidade é obtida puramente através de **composição de alto nível** nos dois novos módulos:
- `src/agent_lab/catalog_quality.py`
- `src/agent_lab/catalog_quality_use_case.py`

Ambos terão seus símbolos públicos canônicos exportados no pacote raiz `src/agent_lab/__init__.py`.

---

## 8. Estratégia de Testes e Slices de TDD

A implementação futura será conduzida estritamente através de micro-TDD distribuído em 3 slices funcionais:

### Slice 1 — Read-Model `CatalogQualityReport` (`tests/test_catalog_quality.py`)
1. Construção nominal com campos congelados e `slots=True`;
2. Validação fail-closed de `catalog_id` (não-str, bool, vazio, sanitização com `strip()`);
3. Validação fail-closed de `assessments` (não-tupla, itens que não sejam `GovernanceAssessment`);
4. **Validações estruturais de `assessment.material_id`:**
   - Rejeição de `assessment.material_id` não-string ou booleano com `TypeError`;
   - Rejeição de `assessment.material_id` vazio ou whitespace com `ValueError`;
   - Rejeição de `assessment.material_id` com whitespace externo (`assessment.material_id != assessment.material_id.strip()`) com `ValueError`;
5. Validação fail-closed de ordenação de `assessments` (rejeição de tupla desordenada por `material_id`);
6. Validação fail-closed de unicidade de `material_id` em `assessments`;
7. **Validações relacionais fail-closed de `duplicate_candidates`:**
   - Rejeição de candidato órfão (candidate_id ausente nos assessments) com `ValueError`;
   - Rejeição de auto-referência (candidate_id == assessment.material_id) com `ValueError`;
   - Rejeição de candidatos duplicados em `duplicate_candidates` com `ValueError`;
   - Rejeição de candidatos desordenados em `duplicate_candidates` com `ValueError`;
   - Rejeição de assimetria relacional ($A \rightarrow B$ sem $B \rightarrow A$) com `ValueError`;
8. Catálogo vazio: `total_records == 0`, `is_empty is True`, contagens em zero, `clean_records_ratio is None`, `average_completeness is None`, `duplicate_pairs == ()`;
9. Catálogo com itens mistos: contagens exatas de limpos, impeditivos (`BLOCKING`) e não-impeditivos (`WARNING`/`INFO`);
10. Derivação canônica de `duplicate_pairs` a partir de relações previamente validadas (sem auto-relações), com menor ID primeiro ($a < b$), unicidade e ordenação lexicográfica;
11. Mappings de severidade e tipos de issue encapsulados em `MappingProxyType`, provando rejeição de mutações in-place (`TypeError`).

### Slice 2 — Pipeline de Domínio `diagnose_catalog_quality` (`tests/test_catalog_quality.py`)
1. Validação fail-closed da sequência de entrada (não-Sequence de `collections.abc`, rejeição de str/bytes, itens inválidos);
2. **Precondições estritas de `material_id`:**
   - Rejeição de `material_id` não-string ou booleano com `TypeError`;
   - Rejeição de `material_id` vazio ou whitespace com `ValueError`;
   - Rejeição de `material_id` com whitespace externo (`record.material_id != record.material_id.strip()`) com `ValueError`;
3. Validação fail-closed de unicidade de `material_id` no catálogo (`ValueError` com ID indicado);
4. Catálogo vazio produzindo `CatalogQualityReport` vazio válido;
5. Execução com catálogo limpo (registros aprovados sem issues);
6. Execução com catálogo contendo violações determinísticas de regras (unit, status, missing critical fields);
7. Comprovação da simetria de duplicidades: para registros $A$ e $B$ duplicados, verificar que $A$ tem $B$ em `duplicate_candidates` e $B$ tem $A$, ambos possuem `POSSIBLE_DUPLICATE` em `issues`, e ambos contêm a evidência em `evidence_collection`;
8. Comprovação de invariância à ordem física de entrada: permutações arbitrárias da sequência de entrada geram relatórios idênticos;
9. Teste de caracterização de regressão: comprovar que `DeterministicGovernanceValidator().analyze_all()` mantém inalterado seu comportamento sequencial legado.

### Slice 3 — Application Use Case `DiagnoseCatalogQualityUseCase` (`tests/test_catalog_quality_use_case.py`)
1. Validações defensivas na borda de aplicação:
   - Rejeição de tipo não-`Sequence` e exclusão de str/bytes com `TypeError`;
   - Rejeição de elemento que não seja `MaterialRecord` dentro de `catalog` com `TypeError`;
   - Rejeição de `catalog_id` não-string ou vazio com `TypeError`/`ValueError`;
2. Execução nominal utilizando o pipeline default `diagnose_catalog_quality`;
3. Execução utilizando pipeline customizado injetado via `CatalogDiagnosticPipeline`;
4. Validação defensiva da saída do pipeline injetado:
   - Rejeição com `TypeError` se retorno não for `CatalogQualityReport`;
   - Rejeição com `ValueError` se retorno contiver `catalog_id` divergente do solicitado;
   - Rejeição com `ValueError` se assessments retornados tiverem mismatch de identidades em relação ao catálogo de entrada (assessment faltante, assessment extra, conjunto divergente de material_ids);
   - Resultado correto e perfeitamente casado aceito sem erros;
5. Propagação fail-closed de exceções originadas pelo pipeline;
6. Teste de integração vertical de ponta a ponta simulando um catálogo industrial representativo em memória.

---

## 9. Não Objetivos (Explicitamente Fora de Escopo)

* **I/O e Formatos Físicos:** Leitura ou escrita de arquivos CSV, Excel, Parquet, JSONL ou SQLite;
* **Bibliotecas Externas:** Dependência de pandas, polars, openpyxl ou similares;
* **Persistência de Relatório:** Repositórios ou armazenamento de `CatalogQualityReport` em disco;
* **Mecanismos de ML / IA:** Chamadas a LLMs, prompts ou inferência probabilística;
* **Governança Operacional HITL:** Criação ou mutação de `GovernanceWorkflow`, `HumanReview` ou `HumanReviewClaim`;
* **Metrologia de Avaliação:** Métricas de Ground Truth (Precision, Recall, F1) ou datasets rotulados;
* **Interface e Conectores:** UI Streamlit, endpoints REST, nova CLI ou conexão ERP;
* **Release de Versão:** Preparação ou publicação de release formal `v0.2.0`.

---

## 10. Definition of Done (DoD)

- [x] **Fase Documental:** SPEC-0149 elaborada e aprovada em Pull Request documental na branch `docs/issue-149-catalog-quality-diagnostic-pipeline` (PR #150, merge `469122514b8b8bc1339295558fe043af5882cba5`) sem código funcional.
- [x] **Fase de Implementação:** Branch funcional `feature/issue-149-catalog-quality-diagnostic-pipeline` criada a partir da `main` após aprovação documental.
- [x] **Micro-TDD:** Implementação dos 3 slices funcionais conduzida estritamente via micro-TDD RED $\rightarrow$ GREEN (+71 testes).
- [x] **Regressão e Baseline:** Suíte completa aprovada com 100% GREEN via `python -m unittest discover -s tests -v`, com baseline canônico incrementado de 1102 para 1173 testes aprovados (1173/1173 GREEN).
- [x] **Qualidade de Código:** Conformidade estrita com `git diff --check`, zero trailing whitespace estrutural e revisão de diff.
- [x] **PR Funcional:** Pull Request funcional #151 revisado e integrado na `main` (merge `89b844e1097f36cbc7d17551bc7b7517fa9402d4`) com CI GREEN obrigatório.
- [ ] **PR de Closeout Documental:** SPEC-0149 marcada como `IMPLEMENTED`, `PROJECT_COMPASS.md` reconciliado com o novo baseline e novas capacidades registradas (em andamento nesta branch documental).
- [ ] **Fechamento e Higiene:** Issue #149 formalmente encerrada (`Issue #149 CLOSED / COMPLETED`) e todas as branches de trabalho excluídas no local e remoto.

---

## 11. Registro de Implementação e Fechamento Funcional

### 11.1 Integração na main
- **PR Funcional:** [#151](https://github.com/Jk-Pascoal/agent-lab-pascoal/pull/151) (*feat: add catalog quality diagnostic pipeline*)
- **Merge Commit:** `89b844e1097f36cbc7d17551bc7b7517fa9402d4`
- **Baseline de Entrada:** `1102/1102 GREEN`
- **Incremento:** `+71 testes`
  - `+58` em `tests/test_catalog_quality.py`
  - `+13` em `tests/test_catalog_quality_use_case.py`
- **Baseline Final Integrado:** `1173/1173 GREEN` (0 failures, 0 errors, 0 skips)

### 11.2 Commits funcionais — Micro-TDD
- `ddf3a7c` — `feat: add catalog quality report slice 1a`
- `84ed6ea` — `feat: enforce catalog assessment identity invariants`
- `99c9b6b` — `feat: enforce catalog duplicate relation invariants`
- `766be59` — `feat: add catalog quality scalar metrics`
- `f4abe65` — `feat: add catalog quality issue distributions`
- `398385e` — `test: harden catalog quality read model metrics`
- `e0fc4cd` — `feat: add catalog quality diagnostic pipeline`
- `e6e6654` — `feat: add catalog quality diagnostic use case`

### 11.3 Entregas e capacidades da v1
A implementação da Issue #149 entrega formalmente:
- **`CatalogQualityReport`:**
  - Read-Model imutável (`frozen=True`, `slots=True`);
  - Invariantes estruturais rigorosas de catálogo, assessments ordenados e integridade relacional simétrica de duplicidades;
  - Métricas puramente derivadas sem recálculo mutável;
  - Distribuições imutáveis (`MappingProxyType`) por severidade (`issues_by_severity`) e por tipo de issue (`issues_by_type`);
  - Pares únicos de duplicidades (`duplicate_pairs`) e contagem deduplicada de pares (`duplicate_pairs_count`);
  - Indicadores executivos escalares: taxa de registros limpos (`clean_records_ratio`) e completude média cadastral (`average_completeness`).
- **`diagnose_catalog_quality`:**
  - Pipeline puro em memória que processa uma coleção fechada de materiais (`Sequence[MaterialRecord]`);
  - Ordenação canônica determinística por `material_id`;
  - Análise simétrica de cada registro contra todos os demais registros do catálogo fechado, garantindo a detecção integral de candidatos a duplicidade;
  - Preservação estrita do comportamento sequencial legado de `DeterministicGovernanceValidator.analyze_all()`.
- **`CatalogDiagnosticPipeline`:**
  - Protocolo estrutural de injeção tipado para interoperabilidade e extensibilidade de pipelines de diagnóstico.
- **`DiagnoseCatalogQualityUseCase`:**
  - Validação defensiva na borda da aplicação (rejeição de tipos não-`Sequence`, exclusão de `str`, `bytes` e `bytearray`, e validação de instâncias `MaterialRecord`);
  - Canonicalização antecipada de `catalog_id` via `.strip()` antes da delegação ao pipeline;
  - Suporte a pipeline injetável com default determinístico (`diagnose_catalog_quality`);
  - Validação rigorosa na fronteira de confiança de saída (`trust boundary`), exigindo retorno de `CatalogQualityReport`, paridade de `catalog_id` e casamento exato das identidades dos assessments contra o catálogo de entrada;
  - Propagação fail-closed de exceções do pipeline sem mascaramento ou interceptação.
- **Exports Públicos Canônicos:**
  - Os quatro símbolos exportados no pacote raiz `agent_lab` e declarados em `__all__`: `CatalogDiagnosticPipeline`, `CatalogQualityReport`, `DiagnoseCatalogQualityUseCase` e `diagnose_catalog_quality`.
- **Pureza e Não-Regressão:**
  - Zero I/O física (sem persistência em disco, sem banco de dados, sem rede);
  - Zero dependências externas novas (zero pandas/polars/openpyxl);
  - Zero alteração em componentes legados protegidos (`validator.py`, `rules.py`, `duplicates.py`, `evidence.py`, `baseline.py`, `data_io.py`).
- **Avanço Estratégico:**
  - Entrega do núcleo computacional puro de domínio e aplicação que viabiliza a frente prioritária de `PoC vendável de diagnóstico de qualidade cadastral`, sem extrapolar para ingestão física de arquivos, UIs ou integrações externas.
