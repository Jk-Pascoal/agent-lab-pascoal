# SPEC-0137 — Ground Truth Atomic Serialization v1

> Especificação técnica da camada de serialização versionada, determinística, pura em memória
> e fail-closed para os três contratos atômicos de Ground Truth no Agent Lab Pascoal.

---

## Metadados

| Campo | Valor |
|---|---|
| **Identificador** | `SPEC-0137` |
| **Status** | `IMPLEMENTED` |
| **Issue relacionada** | `#137` |
| **Título da Issue** | `Ground Truth Atomic Serialization v1` |
| **Branch documental** | `docs/issue-137-ground-truth-atomic-serialization` |
| **Branch de closeout** | `docs/issue-137-ground-truth-atomic-serialization-closeout` |
| **Branch funcional** | `feature/issue-137-ground-truth-atomic-serialization` (integrada via PR #139) |
| **PR funcional** | `#139` |
| **Merge commit** | `e8b2e41` |
| **Responsável** | `Jk-Pascoal` |
| **Data de criação** | `2026-09-19` |
| **Última atualização** | `2026-09-20` |
| **Domínio** | Governança de materiais industriais PDM/BOM e Master Data |
| **Camada arquitetural** | Serialização Versionada (zero-I/O, pura em memória) |
| **Baseline de entrada** | `936 testes aprovados` (100% GREEN) |
| **Baseline final integrado** | `1015 testes aprovados` (100% GREEN) |
| **Impacto SemVer** | `MINOR` (puramente aditivo, release formal permanece `v0.1.0`) |
| **Runner oficial** | `python -m unittest discover -s tests -v` (Python 3.11) |

---

## 1. Contexto

A frente evolutiva **"Ground truth e benchmark"** do Agent Lab Pascoal consolidou nas etapas anteriores:

1. **Contratos atômicos de dados puros (Issue #115 / SPEC-0115):** módulo `src/agent_lab/ground_truth.py`, estabelecendo `MaterialRuleGroundTruth`, `DuplicatePairGroundTruth`, `DecisionRecommendationGroundTruth`, `LabelProvenance` e o acoplamento auditável a `VerifiedSpecialistIdentity`;
2. **Coleções canônicas de avaliação (Issue #119 / SPEC-0119):** módulo `src/agent_lab/ground_truth.py`, estabelecendo `MaterialRuleGroundTruthDataset`, `DuplicatePairGroundTruthDataset` e `DecisionRecommendationGroundTruthDataset`;
3. **Tríade metrológica de avaliadores em memória (Issues #124, #129 e #133):** módulo `src/agent_lab/ground_truth_evaluation.py`, implementando a avaliação determinística pura em memória de recomendações de governança (`SPEC-0124`), regras cadastrais de materiais (`SPEC-0129`) e pares duplicados (`SPEC-0133`), consolidando a suíte oficial em **936 testes 100% GREEN**.

Atualmente, todos os contratos atômicos de Ground Truth operam exclusivamente como estruturas de dados imutáveis em memória.

Na arquitetura do Agent Lab Pascoal, a evolução da maturidade de entidades persistíveis obedece ao percurso canônico consagrado em `WorkflowLifecycle`, `MaterialRevision`, `HumanReviewClaim` e `HumanReviewClaimRelease`:

```text
Domain Contract
      ↓
Versioned Serialization (pura em memória, schema_version = 1, fail-closed)
      ↓
future Persistent Append-Only Repository (I/O, durabilidade física, integridade de linhas)
      ↓
future Projections & Use Cases / Benchmark Loaders & Runners
```

Antes de introduzir repositórios em disco (JSONL), mecanismos de persistência de datasets completos ou loaders de fixtures externas (CSV/JSONL/Parquet), faz-se necessária a formalização da **serialização versionada dos três contratos atômicos de Ground Truth**.

---

## 2. Problema, evidências e impacto

### Problema
O sistema dispõe de contratos de dados em memória ricos e validados para gabaritos de verdade de referência, mas **não possui uma camada canônica e versionada para transformar essas entidades em representações de registro intermediárias (`dict[str, object]`) e reconstruí-las a partir de mapeamentos serializados com garantia estrita de integridade**.

### Evidências
1. Inexistência do módulo `src/agent_lab/ground_truth_serialization.py`;
2. Inexistência de funções bidirecionais de round-trip (`to_record` / `from_record`) para `MaterialRuleGroundTruth`, `DuplicatePairGroundTruth` e `DecisionRecommendationGroundTruth`;
3. Ambiguidade potencial em representações serializadas ad-hoc: ausência de definição canônica de discriminador de tipo (`record_type`), formato de timestamps (`labeled_at`, `verified_at`), representação de coleções de enums (`expected_issue_types`) e representação de identidade de especialista opcional (`annotator`);
4. Risco de coerção ou reparo silencioso caso leitores futuros aceitem registros textuais malformados sem validação de canonicalidade estrita.

### Impacto
Sem a camada de serialização versionada atômica:
- Não é possível avançar com segurança para a persistência append-only em arquivos JSONL de Ground Truth;
- Inviabiliza-se a construção de loaders estruturados que leiam registros de auditoria e fixtures persistidas após reinicialização de processos;
- Há risco de divergências na reconstrução de fusos horários e offsets de `labeled_at` e `annotator.verified_at`;
- Viola-se a separação arquitetural mandatória entre contrato de domínio, representação versionada de serialização e repositório físico.

---

## 3. Objetivo

Estabelecer no novo módulo `src/agent_lab/ground_truth_serialization.py` a camada de **serialização versionada, pura em memória (zero-I/O), determinística e fail-closed** para os três contratos atômicos de Ground Truth do Agent Lab Pascoal:

1. **Definir `schema_version = 1`** como versão canônica de schema;
2. **Definir discriminadores explícitos de `record_type`**:
   - `"MATERIAL_RULE_GROUND_TRUTH"`
   - `"DUPLICATE_PAIR_GROUND_TRUTH"`
   - `"DECISION_RECOMMENDATION_GROUND_TRUTH"`
3. **Fornecer seis APIs públicas específicas e tipadas** de serialização e desserialização atômica:
   - `material_rule_ground_truth_to_record` / `material_rule_ground_truth_from_record`;
   - `duplicate_pair_ground_truth_to_record` / `duplicate_pair_ground_truth_from_record`;
   - `decision_recommendation_ground_truth_to_record` / `decision_recommendation_ground_truth_from_record`;
4. **Garantir round-trip semanticamente lossless para os campos contratuais (`object -> record -> object`)**, preservando identidade, valores, timestamps timezone-aware com offset UTC representado em ISO 8601, identidade de especialista e integridade semântica;
5. **Implementar política estrita de canonicalidade na desserialização (*fail-closed*)**: a desserialização valida a representação canônica e recusa terminantemente reparar representações não-canônicas (strings com whitespace externo ou listas de enums fora de ordem disparam `ValueError`);
6. **Implementar política estrita de *closed-schema***: rejeição imediata com `ValueError` de campos desconhecidos, ausentes, nulos indevidos, strings vazias e inconsistências relacionais;
7. **Preservar a pureza arquitetural**: zero I/O, sem acesso a disco ou rede, utilizando exclusivamente a biblioteca padrão do Python 3.11;
8. **Preservar 100% dos 936 testes GREEN existentes**.

---

## 4. Escopo

### Incluído
- Criação do módulo `src/agent_lab/ground_truth_serialization.py`;
- Constantes canônicas de versão e discriminadores:
  - `SCHEMA_VERSION_V1: int = 1` (com escopo estrito de módulo em `agent_lab.ground_truth_serialization`)
  - `RECORD_TYPE_MATERIAL_RULE_GROUND_TRUTH: str = "MATERIAL_RULE_GROUND_TRUTH"`
  - `RECORD_TYPE_DUPLICATE_PAIR_GROUND_TRUTH: str = "DUPLICATE_PAIR_GROUND_TRUTH"`
  - `RECORD_TYPE_DECISION_RECOMMENDATION_GROUND_TRUTH: str = "DECISION_RECOMMENDATION_GROUND_TRUTH"`
- Seis funções públicas específicas de serialização e desserialização atômica;
- Serialização versionada de `MaterialRuleGroundTruth` com `expected_issue_types` serializado como lista canônica de strings ordenadas por `.value`;
- Validação fail-closed em `material_rule_ground_truth_from_record` de que `expected_issue_types` é lista de strings sem duplicatas, sem `POSSIBLE_DUPLICATE` e já na ordem canônica estrita por `IssueType.value`;
- Serialização versionada de `DuplicatePairGroundTruth` preservando a ordenação canônica `material_id_a < material_id_b` e o booleano estrito `is_duplicate`;
- Serialização versionada de `DecisionRecommendationGroundTruth` preservando a decisão de governança `expected_recommendation` como string representativa do enum;
- Serialização canônica de `VerifiedSpecialistIdentity` quando `provenance == SPECIALIST_CURATED`, e exigência estrita de `annotator: None` quando `provenance == SYNTHETIC_SPECIFIED`;
- Preservação do timestamp timezone-aware e do offset UTC representado em ISO 8601 (`labeled_at` e `verified_at`);
- Validação relacional temporal: `annotator.verified_at <= labeled_at`;
- Canonicalidade estrita de strings em `from_record`: exigência de `isinstance(val, str) and not isinstance(val, bool) and val != "" and val == val.strip()`, sem aplicação de `.strip()` corretivo;
- Validação nominal estrita de tipos na entrada das funções (`TypeError` para instâncias de domínio inválidas em `to_record`, `ValueError` para registros corrompidos/inválidos em `from_record`);
- Bateria completa de testes unitários defensivos e de round-trip em `tests/test_ground_truth_serialization.py`;
- Exportação canônica dos 9 símbolos públicos em `src/agent_lab/__init__.py` e inclusão em `__all__` (com `SCHEMA_VERSION_V1` mantido com escopo de módulo por governança arquitetural).

### Fora de escopo (Não objetivos)
- Dispatchers polimórficos (`ground_truth_to_record`, `ground_truth_from_record`), que permanecem expressamente diferidos até que surja necessidade arquitetural concreta;
- Serialização de coleções ou datasets (`MaterialRuleGroundTruthDataset`, `DuplicatePairGroundTruthDataset`, `DecisionRecommendationGroundTruthDataset`);
- Persistência em disco, arquivos JSONL ou bancos de dados;
- Criação de protocolos de repositório (`GroundTruthRepository`) ou implementações em disco;
- Chamadas de durabilidade física (`flush`, `os.fsync`);
- Loaders de arquivos externos (CSV, JSONL, Parquet, SQLite);
- Serialização de predições (`MaterialRulePrediction`, `DuplicatePairPrediction`);
- Serialização de relatórios de avaliação (`*EvaluationReport`);
- Métricas estatísticas de benchmark (Precision, Recall, F1);
- Benchmark runner / orquestração de testes;
- Adaptadores de predição do pipeline de governança;
- Alteração ou remoção da metrologia legada (`baseline.py`, `data_io.py`);
- UI, CLI ou APIs REST.

---

## 5. Responsabilidade humana e limites do agente

- A serialização versionada não altera dados nem interpreta o significado substantivo do gabarito: atua estritamente como mecanismo determinístico de codificação e decodificação entre instâncias em memória e registros intermediários;
- Nenhuma correção silenciosa é efetuada: se um registro serializado apresentar anomalia estrutural, temporal ou de canonicalidade textual, a desserialização falha imediatamente (*fail-closed*);
- A proveniência humana (`SPECIALIST_CURATED`) é preservada de ponta a ponta sem degradação ou substituição sintética.

---

## 6. Princípios arquiteturais e separações conceituais

Em conformidade com as diretrizes do `PROJECT_COMPASS.md`:

```text
┌─────────────────────────┐       to_record       ┌─────────────────────────┐
│     Domain Contract     │ ────────────────────► │     Versioned Record    │
│  (MaterialRuleGT, etc.) │ ◄──────────────────── │    (dict[str, object])  │
└─────────────────────────┘      from_record      └─────────────────────────┘
            │                                                  │
            │ (Memória Pura / Zero-I/O)                         │ (Intermediário Canônico)
            ▼                                                  ▼
┌─────────────────────────┐                       ┌─────────────────────────┐
│  Evaluators & Metrics   │                       │   future Repositories   │
│   (Accuracy, CaseEval)  │                       │   (JSONL Durável / I/O) │
└─────────────────────────┘                       └─────────────────────────┘
```

1. **`Ground Truth ≠ Prediction`**: o gabarito representa a verdade normativo-auditável com proveniência e justificativa; ele não se confunde com predições ou hipóteses emitidas por motores;
2. **`Dataset ≠ Metric`**: o dataset canônico é coleção de referências; métricas são diagnósticos derivados calculados sobre resultados de avaliação;
3. **`Domain Contract ≠ Persistence`**: contratos de domínio expressam invariantes de negócio; serializers governam a representação estruturada intermediária de intercâmbio;
4. **`Serialization ≠ Repository`**: a serialização é uma função pura e determinística em memória que converte entre objetos e dicionários canônicos; repositórios governam operações físicas de append, consulta e I/O durável em disco;
5. **`Atomic Ground Truth ≠ Ground Truth Dataset`**: esta especificação foca estritamente nos três contratos atômicos individuais, mantendo coleções fora de escopo;
6. **`Desserialização valida representação canônica; não repara representação não-canônica`**: o `to_record` sempre emite dados canônicos; o `from_record` valida a canonicalidade e rejeita registros malformados com `ValueError`. Nenhuma normalização silenciosa (`.strip()` em strings corrompidas ou `sorted()` em listas de enums fora de ordem) é permitida;
7. **Autocontenção modular**: o módulo `ground_truth_serialization.py` implementa seus próprios helpers internos de validação, evitando acoplamento ou importação de rotinas privadas de outros módulos de serialização.

---

## 7. Decisões arquiteturais fundamentais

### Decisão A — Discriminador Canônico de Tipo (`record_type`)
Todo registro serializado de Ground Truth atômico deve conter a chave compulsória `record_type`:

| Tipo de Ground Truth | Valor de `record_type` |
|---|---|
| `MaterialRuleGroundTruth` | `"MATERIAL_RULE_GROUND_TRUTH"` |
| `DuplicatePairGroundTruth` | `"DUPLICATE_PAIR_GROUND_TRUTH"` |
| `DecisionRecommendationGroundTruth` | `"DECISION_RECOMMENDATION_GROUND_TRUTH"` |

**Justificativa:**
- Permite validação precoce de tipo de registro no envelope antes de inspecionar campos de payload;
- Assegura rastreabilidade explícita do contrato serializado;
- Facilita futuras persistências heterogêneas sem introduzir ambiguidades estruturais.

### Decisão B — APIs Públicas Estritamente Específicas na v1
A v1 expõe exclusivamente as seis APIs específicas:
- `material_rule_ground_truth_to_record` / `material_rule_ground_truth_from_record`;
- `duplicate_pair_ground_truth_to_record` / `duplicate_pair_ground_truth_from_record`;
- `decision_recommendation_ground_truth_to_record` / `decision_recommendation_ground_truth_from_record`.

Dispatchers polimórficos (`ground_truth_to_record` e `ground_truth_from_record`) são **deliberadamente excluídos da v1**.

**Justificativa:**
Não se deve antecipar um consumidor polimórfico ou repositório JSONL misto ainda inexistente. APIs específicas garantem tipagem nominal estrita e impedem acoplamentos prematuros. A criação de dispatchers genéricos será reavaliada no futuro caso surja uma necessidade concreta comprovada.

### Decisão C — Canonicalidade Estrita no `from_record` (Sem Reparo Silencioso)
Para todos os campos textuais (`str`):
- O chamador do `from_record` deve fornecer strings já canônicas;
- Validação: `isinstance(val, str) and not isinstance(val, bool) and val != "" and val == val.strip()`;
- Se `val != val.strip()` (presença de espaços, tabs ou quebras de linha nas extremidades), levantar `ValueError`.

Para `expected_issue_types` em `MaterialRuleGroundTruth`:
- Deve ser uma `list` contendo instâncias de `str`;
- Não deve conter duplicatas;
- Não deve conter `POSSIBLE_DUPLICATE`;
- Deve estar rigorosamente ordenada de forma canônica por `IssueType(item).value`;
- Se a lista estiver fora da ordem canônica, levantar `ValueError`. Não efetuar `sorted()` silencioso durante a desserialização.

### Decisão D — Autocontenção e Isolamento Modular
O módulo `ground_truth_serialization.py` **não deve importar funções privadas com prefixo sublinhado (`_...`)** de outros módulos de serialização do projeto.

O módulo declarará internamente suas próprias rotinas utilitárias:
- `_require_canonical_non_empty_str(value, field_name)`;
- `_parse_iso_datetime(value, field_name)`;
- `_parse_specialist(data)`;
- `_format_specialist(specialist)`.

### Decisão E — Escopo de `SCHEMA_VERSION_V1` e Exposição Top-Level Reconciliada

Originalmente, planejou-se exportar `SCHEMA_VERSION_V1` no nível do pacote raiz `agent_lab`.

Entretanto, durante a integração e regressão global do Slice 4, constatou-se que promover `SCHEMA_VERSION_V1` ao namespace raiz conflita diretamente com invariantes arquiteturais prévias do laboratório, estabelecidas pelas suítes de `HumanReviewClaim` e `HumanReviewClaimRelease`, que exigem expressamente que `SCHEMA_VERSION_V1` **não** seja exportado em `agent_lab` nem conste em `__all__`.

Como múltiplos módulos de serialização do Agent Lab possuem sua própria constante `SCHEMA_VERSION_V1 = 1`, um atributo raiz `agent_lab.SCHEMA_VERSION_V1` seria semanticamente ambíguo.

**Decisão arquitetural final:**

- `SCHEMA_VERSION_V1: int = 1` permanece pertencente ao contrato do módulo `agent_lab.ground_truth_serialization`, não sendo reexportado no pacote raiz nem incluído em `__all__`;
- o namespace público de `src/agent_lab/__init__.py` expõe exclusivamente os **9 símbolos não-ambíguos**: os 3 discriminadores `RECORD_TYPE_*` e as 6 funções específicas de conversão.

---

## 8. Especificação dos schemas de registro (`schema_version = 1`)

### 8.1 Schema de `MaterialRuleGroundTruth`

Campos da raiz do registro (`record_type = "MATERIAL_RULE_GROUND_TRUTH"`):

| Campo | Tipo no Registro | Regra de Serialização / Desserialização |
|---|---|---|
| `schema_version` | `int` | Obrigatório. Deve ser exatamente `1`. |
| `record_type` | `str` | Obrigatório. Deve ser exatamente `"MATERIAL_RULE_GROUND_TRUTH"`. |
| `ground_truth_id` | `str` | String canônica não-vazia (`val == val.strip()`). |
| `evaluation_case_id` | `str` | String canônica não-vazia (`val == val.strip()`). |
| `material_id` | `str` | String canônica não-vazia (`val == val.strip()`). |
| `expected_issue_types` | `list[str]` | Lista de strings correspondentes a `item.value` de cada `IssueType`. `to_record` emite ordenada canonicamente por `.value`. `from_record` valida que a lista já está ordenada canonicamente, sem duplicatas e sem `"POSSIBLE_DUPLICATE"`. Lista fora de ordem gera `ValueError`. Tupla vazia serializa como lista vazia `[]`. |
| `provenance` | `str` | String correspondente a `LabelProvenance.value` (`"SPECIALIST_CURATED"` ou `"SYNTHETIC_SPECIFIED"`). |
| `source_reference` | `str` | String canônica não-vazia (`val == val.strip()`). |
| `annotator` | `dict[str, object] \| None` | Obrigatório se `provenance == SPECIALIST_CURATED`; deve ser estritamente `None` se `SYNTHETIC_SPECIFIED`. Segue o sub-schema de `VerifiedSpecialistIdentity`. |
| `labeled_at` | `str` | Timestamp timezone-aware e offset UTC representado em ISO 8601 (`dt.isoformat()`). Rejeição fail-closed se naive. |
| `rationale` | `str` | String canônica não-vazia (`val == val.strip()`). |

### 8.2 Schema de `DuplicatePairGroundTruth`

Campos da raiz do registro (`record_type = "DUPLICATE_PAIR_GROUND_TRUTH"`):

| Campo | Tipo no Registro | Regra de Serialização / Desserialização |
|---|---|---|
| `schema_version` | `int` | Obrigatório. Deve ser exatamente `1`. |
| `record_type` | `str` | Obrigatório. Deve ser exatamente `"DUPLICATE_PAIR_GROUND_TRUTH"`. |
| `ground_truth_id` | `str` | String canônica não-vazia (`val == val.strip()`). |
| `evaluation_case_id` | `str` | String canônica não-vazia (`val == val.strip()`). |
| `material_id_a` | `str` | String canônica não-vazia (`val == val.strip()`). |
| `material_id_b` | `str` | String canônica não-vazia (`val == val.strip()`). Invariante fail-closed: `material_id_a < material_id_b`. |
| `is_duplicate` | `bool` | Booleano estrito (`True` ou `False`). Rejeita inteiros `0` ou `1`. |
| `provenance` | `str` | String correspondente a `LabelProvenance.value` (`"SPECIALIST_CURATED"` ou `"SYNTHETIC_SPECIFIED"`). |
| `source_reference` | `str` | String canônica não-vazia (`val == val.strip()`). |
| `annotator` | `dict[str, object] \| None` | Obrigatório se `SPECIALIST_CURATED`; `None` se `SYNTHETIC_SPECIFIED`. Sub-schema de `VerifiedSpecialistIdentity`. |
| `labeled_at` | `str` | Timestamp timezone-aware e offset UTC representado em ISO 8601. Rejeição fail-closed se naive. |
| `rationale` | `str` | String canônica não-vazia (`val == val.strip()`). |

### 8.3 Schema de `DecisionRecommendationGroundTruth`

Campos da raiz do registro (`record_type = "DECISION_RECOMMENDATION_GROUND_TRUTH"`):

| Campo | Tipo no Registro | Regra de Serialização / Desserialização |
|---|---|---|
| `schema_version` | `int` | Obrigatório. Deve ser exatamente `1`. |
| `record_type` | `str` | Obrigatório. Deve ser exatamente `"DECISION_RECOMMENDATION_GROUND_TRUTH"`. |
| `ground_truth_id` | `str` | String canônica não-vazia (`val == val.strip()`). |
| `evaluation_case_id` | `str` | String canônica não-vazia (`val == val.strip()`). |
| `material_id` | `str` | String canônica não-vazia (`val == val.strip()`). |
| `expected_recommendation` | `str` | String correspondente a `GovernanceDecision.value` (`"APPROVE"`, `"REVIEW"`, `"REJECT"`). |
| `provenance` | `str` | String correspondente a `LabelProvenance.value` (`"SPECIALIST_CURATED"` ou `"SYNTHETIC_SPECIFIED"`). |
| `source_reference` | `str` | String canônica não-vazia (`val == val.strip()`). |
| `annotator` | `dict[str, object] \| None` | Obrigatório se `SPECIALIST_CURATED`; `None` se `SYNTHETIC_SPECIFIED`. Sub-schema de `VerifiedSpecialistIdentity`. |
| `labeled_at` | `str` | Timestamp timezone-aware e offset UTC representado em ISO 8601. Rejeição fail-closed se naive. |
| `rationale` | `str` | String canônica não-vazia (`val == val.strip()`). |

### 8.4 Sub-schema de `VerifiedSpecialistIdentity` (`annotator`)

Quando presente, o sub-dicionário `annotator` possui validação *closed-schema* estrita:

| Campo | Tipo | Regra |
|---|---|---|
| `specialist_id` | `str` | String canônica não-vazia (`val == val.strip()`). |
| `identity_provider` | `str` | String canônica não-vazia (`val == val.strip()`). |
| `identity_subject` | `str` | String canônica não-vazia (`val == val.strip()`). |
| `verification_id` | `str` | String canônica não-vazia (`val == val.strip()`). |
| `verified_at` | `str` | Timestamp timezone-aware e offset UTC representado em ISO 8601. |

Campos ausentes, campos extras ou strings com whitespace externo geram `ValueError` imediato.

---

## 9. Regras de normalização, temporalidade e validação fail-closed

### 9.1 Política *Closed-Schema*
Cada tipo de registro define um conjunto fechado de chaves raiz permitidas:
- Qualquer chave ausente $\rightarrow$ `ValueError(f"Missing required field(s): {missing}")`;
- Qualquer chave extra/desconhecida $\rightarrow$ `ValueError(f"Unknown field(s) detected: {unknown}")`.

### 9.2 Canonicalidade de Strings no `from_record`
- A função `to_record` emite strings limpas a partir dos objetos de domínio;
- A função `from_record` **não** efetua `.strip()` reparador;
- Se qualquer campo textual apresentar `val != val.strip()` ou `len(val.strip()) == 0`, levanta-se `ValueError`.

### 9.3 Canonicalidade de `expected_issue_types`
- No `to_record`: a lista é emitida ordenada canonicamente por `IssueType.value`;
- No `from_record`:
  - `expected_issue_types` deve ser uma `list` de `str`;
  - todos os elementos devem pertencer a `IssueType` e não podem ser `POSSIBLE_DUPLICATE`;
  - não pode haver elementos duplicados;
  - os elementos devem já estar estritamente na ordem canônica ascendente por `IssueType(item).value`;
  - se a lista fornecida estiver fora da ordem canônica, levanta-se `ValueError`.

### 9.4 Precisão Temporal
- Em `to_record`, `labeled_at` e `annotator.verified_at` provêm dos objetos de domínio como instâncias de `datetime` obrigatoriamente timezone-aware;
- No record serializado (`dict[str, object]`), `labeled_at` e `verified_at` são codificados estritamente como strings no formato ISO 8601 (`dt.isoformat()`);
- Em `from_record`, essas strings devem ser parseadas via `datetime.fromisoformat(...)`;
- O `datetime` reconstruído deve possuir `tzinfo` e `utcoffset()` válidos e não-nulos;
- Timestamps em formato ISO 8601 sem offset (naive) devem ser rejeitados fail-closed com `ValueError`;
- Preserva-se o instante temporal e o offset em relação ao UTC; não se promete nem se exige a preservação da identidade interna de classe ou nome de fuso (`ZoneInfo` / `tzname`), visto que a representação textual ISO 8601 codifica o deslocamento numérico UTC;
- Invariante cronológica relacional: quando `provenance == SPECIALIST_CURATED` e `annotator is not None`, é mandatório que `annotator.verified_at <= labeled_at`. Violações levantam `ValueError`.

### 9.5 Validação de Enums
- Valores desconhecidos para `provenance`, `expected_issue_types` ou `expected_recommendation` geram `ValueError`;
- `IssueType.POSSIBLE_DUPLICATE` é expressamente proibido em `expected_issue_types` de `MaterialRuleGroundTruth` (levantando `ValueError`).

### 9.6 Validação Relacional de Duplicidade
- Em `DuplicatePairGroundTruth`, auto-pares (`material_id_a == material_id_b`) ou pares invertidos (`material_id_a >= material_id_b`) são rejeitados com `ValueError`. Nenhuma ordenação silenciosa é efetuada no momento da desserialização.

---

## 10. API pública implementada

No módulo `src/agent_lab/ground_truth_serialization.py`:

```python
# Constantes públicas
SCHEMA_VERSION_V1: int = 1
RECORD_TYPE_MATERIAL_RULE_GROUND_TRUTH: str = "MATERIAL_RULE_GROUND_TRUTH"
RECORD_TYPE_DUPLICATE_PAIR_GROUND_TRUTH: str = "DUPLICATE_PAIR_GROUND_TRUTH"
RECORD_TYPE_DECISION_RECOMMENDATION_GROUND_TRUTH: str = "DECISION_RECOMMENDATION_GROUND_TRUTH"

# Serializadores específicos
def material_rule_ground_truth_to_record(
    ground_truth: MaterialRuleGroundTruth,
) -> dict[str, object]: ...

def material_rule_ground_truth_from_record(
    record: Mapping[str, object],
) -> MaterialRuleGroundTruth: ...

def duplicate_pair_ground_truth_to_record(
    ground_truth: DuplicatePairGroundTruth,
) -> dict[str, object]: ...

def duplicate_pair_ground_truth_from_record(
    record: Mapping[str, object],
) -> DuplicatePairGroundTruth: ...

def decision_recommendation_ground_truth_to_record(
    ground_truth: DecisionRecommendationGroundTruth,
) -> dict[str, object]: ...

def decision_recommendation_ground_truth_from_record(
    record: Mapping[str, object],
) -> DecisionRecommendationGroundTruth: ...
```

Exportações públicas canônicas em `src/agent_lab/__init__.py`:
- Exatamente as 6 funções específicas e os 3 discriminadores `RECORD_TYPE_*` (totalizando 9 novos símbolos não-ambíguos) exportados e incluídos em `__all__`;
- `SCHEMA_VERSION_V1` permanece module-scoped em `agent_lab.ground_truth_serialization.SCHEMA_VERSION_V1` e deliberadamente ausente de `agent_lab.__init__` para evitar colisão semântica com outros serializers do laboratório.

---

## 11. Arquivos e módulos envolvidos

1. `src/agent_lab/ground_truth_serialization.py` (módulo implementado);
2. `src/agent_lab/__init__.py` (exportação canônica dos 9 símbolos não-ambíguos e inclusão em `__all__`);
3. `tests/test_ground_truth_serialization.py` (nova suíte de testes unitários defensivos);
4. `docs/specs/0137_ground_truth_atomic_serialization_v1.md` (esta especificação técnica).

---

## 12. Estratégia de implementação executada (TDD em Slices)

A execução funcional na branch de implementação `feature/issue-137-ground-truth-atomic-serialization` seguiu rigorosamente o ciclo de micro-TDD em 4 slices atômicos, complementados pela reconciliação documental pré-PR:

- **Slice 1 — Serialização de `MaterialRuleGroundTruth` (Commit `38875f1`):**
  - Implementação dos helpers internos autocontidos (`_require_canonical_non_empty_str`, `_parse_iso_datetime`, `_parse_specialist`, `_format_specialist`);
  - `material_rule_ground_truth_to_record` com emissão ordenada de `expected_issue_types`;
  - `material_rule_ground_truth_from_record` com validação closed-schema, integridade de `annotator`, `schema_version`, `record_type`, canonicalidade estrita de strings e validação de ordem canônica em `expected_issue_types`;
  - Testes de round-trip para proveniência `SPECIALIST_CURATED` e `SYNTHETIC_SPECIFIED`;
  - Testes defensivos de rejeição fail-closed (strings com espaços nas pontas, listas de enums desordenadas, etc.).
- **Slice 2 — Serialização de `DuplicatePairGroundTruth` (Commit `a852879`):**
  - `duplicate_pair_ground_truth_to_record` e `duplicate_pair_ground_truth_from_record`;
  - Validação estrita de `is_duplicate: bool`, strings canônicas e ordenação relacional `material_id_a < material_id_b`;
  - Testes de round-trip e testes defensivos fail-closed.
- **Slice 3 — Serialização de `DecisionRecommendationGroundTruth` (Commit `ea72def`):**
  - `decision_recommendation_ground_truth_to_record` e `decision_recommendation_ground_truth_from_record`;
  - Validação estrita do enum `expected_recommendation` (`GovernanceDecision`) e strings canônicas (com rejeição de instâncias de `StrEnum` no payload serializado);
  - Testes de round-trip e testes defensivos fail-closed.
- **Slice 4 — Integração de Exports Públicos e Regressão Global (Commit `23151c2`):**
  - Exportação canônica dos 9 novos símbolos não-ambíguos em `src/agent_lab/__init__.py`;
  - Inclusão dos 9 símbolos em `__all__`;
  - Preservação de `SCHEMA_VERSION_V1` com escopo estrito de módulo em `agent_lab.ground_truth_serialization`;
  - Execução da suíte completa de testes elevando o baseline para 1015 testes 100% GREEN.
- **Reconciliação Documental Pré-PR (Commit `41638e5`):**
  - Reconciliação formal da SPEC-0137 documentando o escopo de módulo de `SCHEMA_VERSION_V1` e os 9 exports top-level (Decisão E).

A implementação foi integrada na `main` através do PR funcional #139 (merge commit `e8b2e41`).

---

## 13. Estratégia de testes implementada

Os testes implementados em `tests/test_ground_truth_serialization.py` cobrem:

1. **Testes de Round-Trip Nominal (semanticamente lossless para os campos contratuais):**
   - Round-trip para cada um dos 3 tipos com `LabelProvenance.SPECIALIST_CURATED` (com `VerifiedSpecialistIdentity`);
   - Round-trip para cada um dos 3 tipos com `LabelProvenance.SYNTHETIC_SPECIFIED` (`annotator=None`);
   - Equivalência semântica contratual: `reconstructed = from_record(to_record(obj))` preserva todos os campos contratuais do objeto original;
   - Para campos `datetime` (`labeled_at` e `annotator.verified_at`), validação explícita de:
     - mesmo instante temporal (`reconstructed.labeled_at == obj.labeled_at`);
     - mesmo offset UTC (`reconstructed.labeled_at.utcoffset() == obj.labeled_at.utcoffset()`);
     - timezone-aware preservado (`reconstructed.labeled_at.tzinfo is not None`);
   - A igualdade completa de dataclass (`reconstructed == obj`) é testada para fusos com offset explícito padrão (`timezone.utc` ou `timezone(timedelta(...))`), sem assumir como requisito universal a preservação de identidade interna de `ZoneInfo`/`tzname`.
2. **Testes Defensivos Fail-Closed de Canonicalidade:**
   - Strings com whitespace inicial ou final (`" MAT-001"`, `"MAT-001 "`) rejeitadas com `ValueError`;
   - Listas de `expected_issue_types` fora da ordem canônica rejeitadas com `ValueError`;
   - Listas de `expected_issue_types` contendo duplicatas ou `POSSIBLE_DUPLICATE` rejeitadas com `ValueError`.
3. **Testes Defensivos Fail-Closed Estruturais e de Tipos:**
   - Entrada não-Mapping (`list`, `str`, `int`, `bool`, `None`) $\rightarrow$ `ValueError`;
   - `schema_version` ausente, inválida, diferente de 1 ou booleana $\rightarrow$ `ValueError`;
   - `record_type` ausente, inválido ou divergente do esperado pela função específica $\rightarrow$ `ValueError`;
   - Campos obrigatórios ausentes $\rightarrow$ `ValueError`;
   - Campos extras na raiz ou no sub-dicionário de specialist $\rightarrow$ `ValueError`;
   - Strings vazias ou puramente de whitespace $\rightarrow$ `ValueError`;
   - Timestamps naive ou formato ISO inválido $\rightarrow$ `ValueError`;
   - Enums inválidos ou desconhecidos $\rightarrow$ `ValueError`;
   - Anomalias de domínio: `annotator.verified_at > labeled_at`, par invertido ou auto-par em duplicidades $\rightarrow$ `ValueError`.

---

## 14. Critérios de aceite

- [x] Módulo `src/agent_lab/ground_truth_serialization.py` criado e contendo as 4 constantes canônicas e 6 funções públicas específicas;
- [x] Round-trip comprovadamente lossless para os campos contratuais dos três contratos atômicos:
  - `MaterialRuleGroundTruth`;
  - `DuplicatePairGroundTruth`;
  - `DecisionRecommendationGroundTruth`;
- [x] Validações *closed-schema* e *fail-closed* implementadas para todos os campos raiz e para o sub-schema `annotator`;
- [x] Validação estrita de canonicalidade de strings no `from_record`, rejeitando qualquer string com whitespace externo;
- [x] Validação estrita de canonicalidade em `expected_issue_types` no `from_record`, rejeitando listas fora de ordem canônica;
- [x] Preservação de timestamp timezone-aware e offset UTC representado em ISO 8601;
- [x] Invariante relacional temporal `annotator.verified_at <= labeled_at` garantida;
- [x] Suíte unitária implementada em `tests/test_ground_truth_serialization.py` com cobertura exaustiva de caminhos nominais e defensivos (79 testes aprovados);
- [x] Exportação canônica dos 9 símbolos públicos não-ambíguos (3 constantes `RECORD_TYPE_*` e 6 funções específicas) em `src/agent_lab/__init__.py` e inclusão em `__all__`, com `SCHEMA_VERSION_V1` mantido com escopo de módulo e ausente de `agent_lab` e `agent_lab.__all__`;
- [x] Baseline oficial mantido 100% GREEN (1015/1015 testes aprovados em `python -m unittest discover -s tests -v`, com 0 failures, 0 errors, 0 skips);
- [x] `git diff --check` aprovado sem trailing whitespace;
- [x] Escopo negativo estritamente preservado (zero dispatchers polimórficos, zero repositories de Ground Truth, zero serialização de datasets e zero I/O em disco).
