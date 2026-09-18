# SPEC-0133 — Ground Truth Duplicate Pair Evaluator v1

> Especificação técnica da camada de avaliação pura, determinística e em memória para aferição
> de predições de duplicidade cadastral de pares de materiais contra referências de Ground Truth no Agent Lab Pascoal.

---

## Metadados

| Campo | Valor |
|---|---|
| **Identificador** | `SPEC-0133` |
| **Status** | `PROPOSED` |
| **Issue relacionada** | `#133` |
| **Título da Issue** | `Ground Truth Duplicate Pair Evaluator v1` |
| **Branch documental** | `docs/issue-133-ground-truth-duplicate-pair-evaluator-spec` |
| **Responsável** | `Jk-Pascoal` |
| **Data de criação** | `2026-09-18` |
| **Última atualização** | `2026-09-18` |
| **Domínio** | Governança de materiais industriais PDM/BOM e Master Data |
| **Camada arquitetural** | Metrologia e Avaliação de Ground Truth (pura em memória, zero-I/O) |
| **Baseline de entrada** | `883 testes aprovados` (100% GREEN) |
| **Baseline esperado** | `883 + novos testes da Issue #133` (100% GREEN) |
| **Impacto SemVer** | `MINOR` (release formal permanece `v0.1.0`) |
| **Runner oficial** | `python -m unittest discover -s tests -v` (Python 3.11) |

---

## 1. Contexto

A frente evolutiva **"Ground truth e benchmark"** do Agent Lab Pascoal foi formalizada a partir das Issues #115 (SPEC-0115) e #119 (SPEC-0119), estabelecendo no módulo `src/agent_lab/ground_truth.py` a tríade fundamental de contratos de gabarito para governança cadastral:

1. **Material Rules:** conformidade cadastral determinística a nível de material individual (`MaterialRuleGroundTruth` e `MaterialRuleGroundTruthDataset`);
2. **Duplicate Pairs:** detecção de duplicidade/equivalência a nível de par relacional não-direcional de materiais (`DuplicatePairGroundTruth` e `DuplicatePairGroundTruthDataset`);
3. **Decision Recommendations:** recomendação algorítmica de governança a nível de decisão de workflow (`DecisionRecommendationGroundTruth` e `DecisionRecommendationGroundTruthDataset`).

Nas etapas subsequentes, a esteira de metrologia avançou implementando os avaliadores puros em memória no módulo `src/agent_lab/ground_truth_evaluation.py`:
- **Issue #124 (SPEC-0124):** avaliador de recomendações de governança (`evaluate_decision_recommendation` e `evaluate_decision_recommendations`), elevando o baseline para 830 testes 100% GREEN;
- **Issue #129 (SPEC-0129):** avaliador multirrótulo de regras cadastrais de materiais (`evaluate_material_rule` e `evaluate_material_rules`), elevando o baseline consolidado para 883 testes 100% GREEN.

Atualmente, o pilar de **Duplicate Pairs** dispõe de contratos de domínio atômico (`DuplicatePairGroundTruth`) e de dataset canônico (`DuplicatePairGroundTruthDataset`), mas ainda **não possui a camada correspondente de avaliação pura em memória**.

Essa ausência mantém incompleta a tríade metrológica projetada para o laboratório. A presente SPEC formaliza a especificação técnica para o avaliador de pares duplicados, completando a fundação em memória da frente de Ground Truth antes de avançar para persistência ou runners de benchmark.

---

## 2. Problema, evidências e impacto

### Problema
O Agent Lab Pascoal dispõe de contratos formais de gabarito para duplicidades (`DuplicatePairGroundTruth` e `DuplicatePairGroundTruthDataset`), mas não possui contratos tipados para representar predições binárias de pares (`DuplicatePairPrediction`), nem funções puras e relatórios consolidados em memória para avaliar se as predições de duplicidade coincidem com o gabarito estabelecido.

### Evidências
1. Em `src/agent_lab/ground_truth.py`, `DuplicatePairGroundTruth` define a expectativa binária `is_duplicate: bool` sobre o par canônico `(material_id_a, material_id_b)` com a invariante `material_id_a < material_id_b`, mas não há em todo o sistema uma estrutura de dados de predição correspondente;
2. Em `src/agent_lab/ground_truth_evaluation.py`, existem avaliadores para `DecisionRecommendation` e `MaterialRule`, porém não existe nenhuma estrutura ou função para avaliar pares duplicados;
3. O código legado em `src/agent_lab/baseline.py` e `src/agent_lab/data_io.py` modela duplicidade como string plana associada a um único material (`expected_issue = "POSSIBLE_DUPLICATE"`), violando a semântica relacional de par e impedindo testes metrológicos auditáveis e reprodutíveis;
4. Na função de custo de governança do laboratório (Seção 8 do COMPASS), duplicidade não detectada tem peso crítico 5:1 contra revisões desnecessárias. A ausência de um avaliador puro impede a mensuração objetiva de acertos em pares.

### Impacto
Sem o avaliador canônico de pares duplicados:
- Permanece uma lacuna na esteira de Ground Truth, deixando a modalidade de duplicidade como a única sem instrumento de avaliação em memória;
- Há risco de avaliações ad-hoc em scripts dispersos sem validação canônica de ordenação de par, permitindo pares invertidos `(B, A)` ou auto-pares `(A, A)`;
- Impossibilidade de avançar com segurança para loaders externos, persistência de datasets e orquestradores de benchmark unificados;
- Impossibilidade de aposentar futuramente a metrologia legada sem antes dispor do avaliador correspondente na nova arquitetura.

---

## 3. Objetivo

Introduzir no módulo `src/agent_lab/ground_truth_evaluation.py` a camada pura de metrologia e avaliação em memória (zero-I/O) para avaliação determinística de predições de pares de materiais contra `DuplicatePairGroundTruth` e `DuplicatePairGroundTruthDataset`:

1. **Definir o contrato imutável de predição `DuplicatePairPrediction`**, encapsulando `material_id_a`, `material_id_b` e `is_duplicate: bool`, com validações fail-closed estritas (sanitização `.strip()`, anti-auto-par, e ordenação canônica `material_id_a < material_id_b`);
2. **Definir o contrato imutável de resultado de caso `DuplicatePairCaseEvaluation`**, diagnosticando individualmente a correspondência (`is_match` e `is_mismatch`) e preservando a linhagem do caso (`evaluation_case_id`, `ground_truth_id`, `material_id_a`, `material_id_b`, `expected_is_duplicate`, `predicted_is_duplicate`);
3. **Definir o contrato imutável de relatório em lote `DuplicatePairEvaluationReport`**, contendo `dataset_id: str` obrigatório, ordenação canônica determinística de casos por `(evaluation_case_id, ground_truth_id)` e métricas puras de exact-match (`accuracy`);
4. **Implementar a função pura atômica `evaluate_duplicate_pair(ground_truth, prediction) -> DuplicatePairCaseEvaluation`**, com validação relacional estrita de `material_id_a` e `material_id_b`;
5. **Implementar a função pura de lote `evaluate_duplicate_pairs(dataset, predictions: Mapping[str, DuplicatePairPrediction]) -> DuplicatePairEvaluationReport`**, indexada estritamente por `evaluation_case_id` com paridade exata 1:1;
6. **Formalizar o comportamento explícito para dataset vazio** (`total_cases == 0`, `accuracy = None`, `is_empty = True`, `is_perfect_match = False`);
7. **Exportar canonicamente os novos símbolos** no pacote raiz `src/agent_lab/__init__.py`;
8. **Preservar 100% dos 883 testes GREEN existentes**.

---

## 4. Escopo

### Incluído
- Dataclass imutável `DuplicatePairPrediction` (`frozen=True, slots=True`);
- Dataclass imutável `DuplicatePairCaseEvaluation` (`frozen=True, slots=True`);
- Dataclass imutável `DuplicatePairEvaluationReport` (`frozen=True, slots=True`);
- Função pura `evaluate_duplicate_pair(ground_truth: DuplicatePairGroundTruth, prediction: DuplicatePairPrediction) -> DuplicatePairCaseEvaluation`;
- Função pura `evaluate_duplicate_pairs(dataset: DuplicatePairGroundTruthDataset, predictions: Mapping[str, DuplicatePairPrediction]) -> DuplicatePairEvaluationReport`;
- Validação defensiva fail-closed de tipos nominais (`TypeError`) e de integridade relacional/estrutural (`ValueError`);
- Exigência estrita de pareamento no batch via `Mapping[str, DuplicatePairPrediction]` indexado exclusivamente por `evaluation_case_id` com paridade 1:1;
- Ordenação canônica determinística dos casos no relatório por `(evaluation_case_id, ground_truth_id)`;
- Semântica matemática explícita para dataset vazio (`accuracy = None`);
- Cálculo de exatidão (`accuracy`) por divisão de ponto flutuante `matched_cases / total_cases` sem arredondamento interno;
- Exportações canônicas em `src/agent_lab/__init__.py` e inclusão em `__all__`;
- Bateria completa de testes unitários defensivos em `tests/test_ground_truth_evaluation.py`.

### Fora de escopo (Não objetivos)
- Suporte a `Sequence[DuplicatePairPrediction]`, tuplas ou listas na API batch (eliminado para exigir pareamento explícito e biunívoco por `evaluation_case_id`);
- Persistência em disco ou banco de dados (JSONL, SQLite, etc.);
- Loaders ou parsers de fixtures externas (CSV, JSONL, Parquet, Excel);
- Bibliotecas externas (scikit-learn, pandas, numpy, scipy);
- Métricas estatísticas agregadas de Precision, Recall, F1, especificidade, AUC ou curvas ROC/PR;
- Matrizes de confusão e relatórios gráficos;
- Scores de similaridade contínuos (`similarity_score: float`), thresholds ou distâncias textuais;
- Algoritmos de clustering de duplicidades ou detecção de componentes conexos;
- Chamadas a motores de similaridade, embeddings ou LLMs;
- Integração com o pipeline de governança (`EvidenceCollection`, `DecisionRecommendation`);
- Calibração de thresholds e consenso/adjudicação multi-anotador;
- Interface com o usuário (UI/Streamlit), CLI ou endpoints REST;
- Alteração ou remoção do benchmark legado (`src/agent_lab/baseline.py`, `src/agent_lab/data_io.py`).

---

## 5. Responsabilidade humana e limites do agente

- O agente automatizado compara estritamente gabaritos contra predições em memória segundo regras de exatidão categórica;
- O avaliador não decide se dois materiais são de fato equivalentes na fábrica ou no ERP: ele afere se o sistema previu exatamente o que o gabarito estabelecido prescreve;
- Métricas de acerto não concedem autoridade operacional para fundir cadastros automaticamente;
- O Ground Truth permanece como autoridade epistemológica auditável e imutável.

---

## 6. Princípios arquiteturais e separações conceituais

Em estrita consonância com o `PROJECT_COMPASS.md`, a presente especificação consolida os seguintes princípios:

1. **`Ground Truth ≠ Prediction`**: o gabarito (`DuplicatePairGroundTruth`) é uma expectativa de referência rotulada com proveniência e justificativa; a predição (`DuplicatePairPrediction`) é o resultado emitido por um motor de avaliação sob teste. Eles não compartilham tipos nominais nem responsabilidades;
2. **`Dataset ≠ Metric`**: a coleção canônica (`DuplicatePairGroundTruthDataset`) preserva os dados de referência; o relatório (`DuplicatePairEvaluationReport`) calcula o diagnóstico metrológico resultante da comparação contra predições;
3. **`Evaluation Contract ≠ Benchmark Result`**: o contrato define as regras de aferição atômica e em lote; o resultado do benchmark é a instância concreta gerada para um conjunto experimental;
4. **`evaluation_case_id` (identidade experimental) $\neq$ `(material_id_a, material_id_b)` (identidade relacional do par)**:
   - `evaluation_case_id` identifica unicamente o teste/cenário experimental;
   - `(material_id_a, material_id_b)` identifica a entidade relacional de domínio;
   - `ground_truth_id` identifica a anotação/gabarito de referência;
   - `dataset_id` identifica a coleção canônica agregadora;
   A independência entre esses quatro identificadores é estritamente mantida;
5. **Pureza arquitetural e zero I/O**: a camada de avaliação opera exclusivamente em memória sobre estruturas imutáveis (`frozen=True, slots=True`), sem I/O, sem efeitos colaterais e sem mutação das instâncias de entrada;
6. **Isolamento da metrologia legada**: os módulos legados `data_io.py` e `baseline.py` permanecem 100% inalterados.

---

## 7. Decisões semânticas fundamentais

### A. Unidade estatística: Par não-direcional canônico
Em Master Data Management (MDM) e governança PDM/BOM, a duplicidade entre dois materiais é uma relação binária simétrica (não-direcional): se $A$ é duplicata de $B$, $B$ é duplicata de $A$.

Para eliminar ambiguidades combinatórias e garantir canonicidade relacional estrita:
- A unidade avaliada é o **par canônico não-direcional ordenado**: `(material_id_a, material_id_b)` com `material_id_a < material_id_b`;
- Não é permitida representação invertida `(material_id_b, material_id_a)`;
- Não é permitida auto-relação `material_id_a == material_id_b`;
- **A camada de avaliação rejeita fail-closed pares invertidos ou auto-pares com `ValueError`**. Em nenhuma hipótese o sistema inverte ou canonicaliza silenciosamente um par malformado na predição;
- A duplicidade pertence estritamente ao par e jamais a um material individual.

### B. Contrato de predição: `DuplicatePairPrediction`
```python
@dataclass(frozen=True, slots=True)
class DuplicatePairPrediction:
    material_id_a: str
    material_id_b: str
    is_duplicate: bool
```
Regras semânticas:
- `material_id_a` e `material_id_b` devem ser strings nominais (`TypeError` para outros tipos, inclusive booleanos);
- Devem ser sanitizados com `.strip()`, rejeitando strings vazias ou compostas exclusivamente por whitespace com `ValueError`;
- `material_id_a != material_id_b`: auto-pares disfarçados ou explícitos são rejeitados com `ValueError("material_id_a and material_id_b must be different")`;
- `material_id_a < material_id_b`: ordenação lexicográfica ascendente obrigatória. Pares com `material_id_a > material_id_b` são rejeitados com `ValueError("material_id_a must be less than material_id_b")`;
- `is_duplicate` deve ser estritamente uma instância de `bool` (`TypeError` para qualquer outro tipo). **Valores inteiros como `0` ou `1` são expressamente rejeitados com `TypeError`**;
- Imutabilidade comprovada: `frozen=True, slots=True`, rejeitando mutações posteriores com `FrozenInstanceError`.

### C. Contrato de avaliação de caso: `DuplicatePairCaseEvaluation`
```python
@dataclass(frozen=True, slots=True)
class DuplicatePairCaseEvaluation:
    evaluation_case_id: str
    ground_truth_id: str
    material_id_a: str
    material_id_b: str
    expected_is_duplicate: bool
    predicted_is_duplicate: bool
```
Propriedades derivadas puras:
- `@property is_match(self) -> bool`: `self.predicted_is_duplicate == self.expected_is_duplicate`;
- `@property is_mismatch(self) -> bool`: `not self.is_match`.

Tabela Verdade Completa:

| Expected `is_duplicate` | Predicted `is_duplicate` | `is_match` | `is_mismatch` | Natureza Estatística Subjacente |
|---|---|---|---|---|
| `False` | `False` | `True` | `False` | True Negative (TN) |
| `False` | `True` | `False` | `True` | False Positive (FP) |
| `True` | `False` | `False` | `True` | False Negative (FN) |
| `True` | `True` | `True` | `False` | True Positive (TP) |

> [!IMPORTANT]
> **Deliberação de API pública:**
> Embora o problema seja matematicamente binário e a tabela verdade acima reconheça os quatro estados estatísticos fundamentais, **nesta v1 esses estados NÃO devem ser expostos como propriedades ou métricas agregadas (TP, FP, FN, TN) na API pública**. A API pública de v1 fornece exatidão categórica (`is_match`, `is_mismatch`, `accuracy`, `matched_cases`, `mismatched_cases`). Métricas agregadas de Precision, Recall e F1 pertencem a uma etapa posterior formal de benchmark.

### D. Validação relacional estrita em `evaluate_duplicate_pair`
```python
def evaluate_duplicate_pair(
    ground_truth: DuplicatePairGroundTruth,
    prediction: DuplicatePairPrediction,
) -> DuplicatePairCaseEvaluation:
    ...
```
Invariantes relacionais:
- Rejeição de tipos inválidos: `ground_truth` deve ser `DuplicatePairGroundTruth` e `prediction` deve ser `DuplicatePairPrediction` (`TypeError`);
- Correspondência relacional biunívoca:
  ```python
  if (
      prediction.material_id_a != ground_truth.material_id_a
      or prediction.material_id_b != ground_truth.material_id_b
  ):
      raise ValueError(
          f"material pair mismatch: prediction has "
          f"({prediction.material_id_a!r}, {prediction.material_id_b!r}), "
          f"ground_truth has ({ground_truth.material_id_a!r}, {ground_truth.material_id_b!r})"
      )
  ```
- **Tratamento de par invertido e validação relacional:**
  - Uma predição com par invertido, por exemplo `("B", "A")` quando a forma canônica seria `("A", "B")`, é rejeitada já durante a construção de `DuplicatePairPrediction` por violar `material_id_a < material_id_b`. Logo, essa instância inválida sequer alcança `evaluate_duplicate_pair`;
  - A validação relacional em `evaluate_duplicate_pair` permanece estritamente necessária para proteger contra divergências entre pares individualmente válidos. Exemplo:
    - Ground Truth: `("MAT-001", "MAT-003")`
    - Prediction válida estruturalmente: `("MAT-001", "MAT-002")`
    Ambas respeitam a forma canônica individualmente (`a < b`), porém representam pares de domínio diferentes. Nesse caso, `evaluate_duplicate_pair(...)` rejeita com `ValueError` por disparidade de par material (*material pair mismatch*);
  - Preservam-se os princípios: nenhuma equivalência por conjunto, nenhuma inversão silenciosa e nenhuma canonicalização silenciosa.

### E. API Batch: `evaluate_duplicate_pairs`
```python
def evaluate_duplicate_pairs(
    dataset: DuplicatePairGroundTruthDataset,
    predictions: Mapping[str, DuplicatePairPrediction],
) -> DuplicatePairEvaluationReport:
    ...
```
Regras de coordenação do lote:
- `dataset` deve ser `DuplicatePairGroundTruthDataset` (`TypeError`);
- `predictions` deve ser `Mapping[str, DuplicatePairPrediction]` (`TypeError` para `Sequence`, `list`, `tuple` ou outros tipos);
- Validação nominal de chaves e valores:
  - cada chave deve ser `str` não-booleana (`TypeError`);
  - cada valor deve ser `DuplicatePairPrediction` (`TypeError`);
- **Paridade 1:1 estrita por `evaluation_case_id`**:
  - Chaves esperadas: `{item.evaluation_case_id for item in dataset.items}`;
  - Chaves fornecidas: `set(predictions.keys())`;
  - Chaves faltantes (`missing = expected - provided`): levantam `ValueError` fail-closed acusando as chaves ausentes ordenadas;
  - Chaves excedentes (`extra = provided - expected`): levantam `ValueError` fail-closed acusando as chaves inesperadas ordenadas;
- Validação relacional para cada caso pareado: verificação estrita de `material_id_a` e `material_id_b` via delegação à função atômica `evaluate_duplicate_pair`;
- O resultado é empacotado em `DuplicatePairEvaluationReport`.

### F. Relatório consolidado: `DuplicatePairEvaluationReport`
```python
@dataclass(frozen=True, slots=True)
class DuplicatePairEvaluationReport:
    dataset_id: str
    cases: tuple[DuplicatePairCaseEvaluation, ...]
```
Propriedades e semântica:
- `dataset_id` é obrigatório, normalizado via `.strip()` e não-vazio (`ValueError`);
- `cases` é validado como `tuple`, com rejeição de elementos não-`DuplicatePairCaseEvaluation` (`TypeError`) e bloqueio fail-closed de duplicidades de `evaluation_case_id` (`ValueError`);
- **Ordenação canônica determinística compulsória**:
  ```python
  canonical = tuple(
      sorted(
          self.cases,
          key=lambda c: (c.evaluation_case_id, c.ground_truth_id),
      )
  )
  ```
  garantindo independência total da ordem das chaves do dicionário de entrada;
- Propriedades derivadas sem duplicação de estado:
  - `total_cases: int`: contagem total de casos (`len(self.cases)`);
  - `matched_cases: int`: soma de casos onde `is_match == True`;
  - `mismatched_cases: int`: `self.total_cases - self.matched_cases`;
  - `accuracy: float | None`: `self.matched_cases / self.total_cases` se `total_cases > 0`, senão `None`;
  - `is_empty: bool`: `self.total_cases == 0`;
  - `is_perfect_match: bool`: `self.total_cases > 0 and self.matched_cases == self.total_cases`;
  - `matches: tuple[DuplicatePairCaseEvaluation, ...]`: tupla de casos com match;
  - `mismatches: tuple[DuplicatePairCaseEvaluation, ...]`: tupla de casos com mismatch.

### G. Semântica para Coleção Vazia
Quando `dataset.items == ()` e `predictions == {}`:
- `total_cases = 0`;
- `matched_cases = 0`;
- `mismatched_cases = 0`;
- `accuracy = None` (evita divisão por zero e recusa inventar 0.0 ou 1.0 para conjuntos vazios);
- `is_empty = True`;
- `is_perfect_match = False`;
- `matches = ()`;
- `mismatches = ()`.

### H. Política Fail-Closed Estrita
Nenhum dado com anomalia estrutural ou relacional é silenciosamente consertado:
- Par invertido $\rightarrow$ `ValueError`;
- Auto-par $\rightarrow$ `ValueError`;
- Tipo nominado incorreto (ex.: inteiro em `is_duplicate`, int/float em IDs) $\rightarrow$ `TypeError`;
- Chave de predição ausente ou excedente no batch $\rightarrow$ `ValueError`;
- Disparidade de `material_id_a` ou `material_id_b` entre predição e gabarito $\rightarrow$ `ValueError`;
- Duplicata de `evaluation_case_id` no relatório $\rightarrow$ `ValueError`.

---

## 8. Arquitetura da solução

### Fluxo Metrológico de Avaliação em Lote

```text
DuplicatePairGroundTruthDataset (em memória)
+
predictions: Mapping[str, DuplicatePairPrediction] (indexado por evaluation_case_id)
        │
        ▼
evaluate_duplicate_pairs(...)
        │
        ├─► Validação de tipos nominais (Dataset e Mapping)
        ├─► Paridade 1:1 de chaves por evaluation_case_id (rejeição de missing/extra com ValueError)
        │
        ▼ Para cada item do dataset:
pareamento biunívoco via predictions[item.evaluation_case_id]
        │
        ▼
evaluate_duplicate_pair(item, prediction)
        │
        ├─► Validação relacional fail-closed:
        │     prediction.material_id_a == item.material_id_a
        │     E prediction.material_id_b == item.material_id_b
        │
        ├─► Comparação categórica:
        │     is_match = (predicted_is_duplicate == expected_is_duplicate)
        │
        ▼
DuplicatePairCaseEvaluation (imutável)
        │
        ▼
Agregação de casos e ordenação canônica compulsória por (evaluation_case_id, ground_truth_id)
        │
        ▼
DuplicatePairEvaluationReport (imutável)
        ├─ dataset_id
        ├─ cases (ordenados deterministicamente)
        ├─ total_cases / matched_cases / mismatched_cases
        ├─ accuracy (None se vazio)
        └─ is_empty / is_perfect_match / matches / mismatches
```

---

## 9. Arquivos e módulos envolvidos

### Arquivos a serem modificados na implementação:
1. `src/agent_lab/ground_truth_evaluation.py`:
   - Adição de `DuplicatePairPrediction`;
   - Adição de `DuplicatePairCaseEvaluation`;
   - Adição de `DuplicatePairEvaluationReport`;
   - Implementação de `evaluate_duplicate_pair`;
   - Implementação de `evaluate_duplicate_pairs`;
   - Imports necessários de `DuplicatePairGroundTruth` e `DuplicatePairGroundTruthDataset` a partir de `agent_lab.ground_truth`.
2. `src/agent_lab/__init__.py`:
   - Import e exportação pública canônica dos 5 novos símbolos;
   - Inclusão em `__all__`.
3. `tests/test_ground_truth_evaluation.py`:
   - Implementação das classes de testes unitários defensivos para cada um dos slices.
4. `docs/specs/0133_ground_truth_duplicate_pair_evaluator_v1.md`:
   - Atualização de status de `PROPOSED` para `IMPLEMENTED` após a conclusão do ciclo TDD e closeout.

> [!NOTE]
> Nenhum novo módulo de produção será criado. A evolução ocorre de forma coesa e simétrica dentro do módulo existente `ground_truth_evaluation.py`.

---

## 10. Estratégia de implementação (TDD em Slices)

A implementação futura seguirá rigorosamente o micro-TDD em 6 fatias verticais sequenciais:

### Slice 1 — `DuplicatePairPrediction`
- **Testes unitários nominais:**
  - `test_nominal_construction_and_fields`: instanciação com campos válidos (`material_id_a="MAT-001"`, `material_id_b="MAT-002"`, `is_duplicate=True/False`);
  - `test_string_fields_normalized_with_strip`: sanitização de whitespace ao redor de `material_id_a` e `material_id_b`;
  - `test_immutability_frozen_instance`: rejeição de mutação com `FrozenInstanceError`;
- **Testes defensivos fail-closed:**
  - `test_rejects_non_string_material_ids`: rejeição de int, float, bool, None com `TypeError`;
  - `test_rejects_empty_or_whitespace_material_ids`: rejeição de `""`, `"   "`, `"\t\n"` com `ValueError`;
  - `test_rejects_self_pair_equal_ids`: rejeição de `material_id_a == material_id_b` com `ValueError`;
  - `test_rejects_inverted_pair_order`: rejeição estrita de `material_id_a > material_id_b` com `ValueError` (sem inversão silenciosa);
  - `test_rejects_non_bool_is_duplicate`: rejeição de `int` (`0`, `1`), `str` (`"True"`, `"False"`), `None` com `TypeError`.

### Slice 2 — `DuplicatePairCaseEvaluation`
- **Testes unitários nominais:**
  - `test_nominal_construction_and_fields`: validação de atributos `evaluation_case_id`, `ground_truth_id`, `material_id_a`, `material_id_b`, `expected_is_duplicate`, `predicted_is_duplicate`;
  - `test_string_fields_normalized_with_strip`: sanitização de whitespace nos 4 campos textuais;
  - `test_immutability_frozen_instance`: rejeição de mutação com `FrozenInstanceError`;
  - `test_truth_table_matches_and_mismatches`:
    - `(False, False) -> is_match=True, is_mismatch=False`;
    - `(False, True) -> is_match=False, is_mismatch=True`;
    - `(True, False) -> is_match=False, is_mismatch=True`;
    - `(True, True) -> is_match=True, is_mismatch=False`;
- **Testes defensivos fail-closed:**
  - `test_rejects_non_string_fields`: `TypeError` para argumentos não-str ou booleanos nos IDs;
  - `test_rejects_empty_or_whitespace_fields`: `ValueError` para strings vazias;
  - `test_rejects_non_bool_expectations_and_predictions`: `TypeError` para `int`, `str`, `None`.

### Slice 3 — `evaluate_duplicate_pair`
- **Testes unitários nominais:**
  - `test_evaluates_matching_duplicate_pair`: comparação atômica retornando `is_match=True`;
  - `test_evaluates_mismatching_duplicate_pair`: comparação atômica retornando `is_match=False`;
  - `test_preserves_case_and_ground_truth_lineage`: integridade dos IDs de linhagem no retorno;
- **Testes defensivos fail-closed:**
  - `test_rejects_invalid_ground_truth_type`: `TypeError` se não for `DuplicatePairGroundTruth`;
  - `test_rejects_invalid_prediction_type`: `TypeError` se não for `DuplicatePairPrediction`;
  - `test_rejects_material_id_a_mismatch`: `ValueError` se `prediction.material_id_a != ground_truth.material_id_a`;
  - `test_rejects_material_id_b_mismatch`: `ValueError` se `prediction.material_id_b != ground_truth.material_id_b`;
  - `test_rejects_both_material_ids_mismatch`: `ValueError` em caso de incompatibilidade total.

### Slice 4 — `DuplicatePairEvaluationReport`
- **Testes unitários nominais:**
  - `test_nominal_report_properties`: validação de `total_cases`, `matched_cases`, `mismatched_cases`, `accuracy`, `is_empty`, `is_perfect_match`, `matches`, `mismatches`;
  - `test_dataset_id_normalized_with_strip`: sanitização de whitespace em `dataset_id`;
  - `test_immutability_frozen_instance`: rejeição de mutação com `FrozenInstanceError`;
  - `test_canonical_ordering_by_evaluation_case_id_and_ground_truth_id`: garantia de reordenação determinística de tupla de entrada desordenada;
  - `test_empty_report_behavior`: dataset vazio com `total_cases=0`, `accuracy=None`, `is_empty=True`, `is_perfect_match=False`, `matches=()`, `mismatches=()`;
  - `test_perfect_match_report`: 100% de acertos com `accuracy=1.0` e `is_perfect_match=True`;
  - `test_zero_accuracy_report`: 0% de acertos com `accuracy=0.0` e `is_perfect_match=False`;
- **Testes defensivos fail-closed:**
  - `test_rejects_non_string_dataset_id`: `TypeError` para tipo inválido;
  - `test_rejects_empty_dataset_id`: `ValueError` para string vazia ou whitespace;
  - `test_rejects_non_tuple_cases`: `TypeError` se `cases` não for tupla;
  - `test_rejects_non_case_evaluation_element`: `TypeError` para elemento inválido na tupla;
  - `test_rejects_duplicate_evaluation_case_id`: `ValueError` se houver colisão de `evaluation_case_id`.

### Slice 5 — `evaluate_duplicate_pairs`
- **Testes unitários nominais:**
  - `test_evaluates_empty_dataset_and_predictions`: avaliação de lote vazio retornando relatório vazio com `accuracy=None`;
  - `test_evaluates_batch_with_matches_and_mismatches`: lote com múltiplos casos calculando métricas agregadas corretas;
  - `test_preserves_dataset_id_lineage`: `report.dataset_id == dataset.dataset_id`;
  - `test_input_mapping_order_independence`: mappings em diferentes ordens produzem relatórios canonicamente idênticos;
- **Testes defensivos fail-closed:**
  - `test_rejects_non_dataset_argument`: `TypeError` se primeiro argumento não for `DuplicatePairGroundTruthDataset`;
  - `test_rejects_non_mapping_predictions`: `TypeError` se predições forem lista, tupla, set ou outro tipo;
  - `test_rejects_invalid_mapping_key_type`: `TypeError` se chave não for `str` ou for `bool`;
  - `test_rejects_invalid_mapping_value_type`: `TypeError` se valor não for `DuplicatePairPrediction`;
  - `test_rejects_missing_predictions_keys`: `ValueError` com chaves ausentes se faltar predição para algum caso do dataset;
  - `test_rejects_extra_predictions_keys`: `ValueError` com chaves excedentes se houver predição sem caso correspondente no dataset;
  - `test_rejects_material_id_divergence_in_batch`: `ValueError` se para um determinado `evaluation_case_id` houver disparidade de `material_id_a` ou `material_id_b`.

### Slice 6 — Exports Públicos e Regressão Completa
- `test_public_exports_in_agent_lab_package`: confirmação de importabilidade dos 5 novos símbolos no pacote raiz `src/agent_lab/__init__.py`;
- `test_all_contains_new_symbols`: confirmação da presença em `__all__`;
- Execução integral da suíte de testes comprovando `883 + novos testes` aprovados (100% GREEN).

---

## 11. Gates de verificação e prontidão

Ao longo do ciclo de implementação e na abertura do futuro PR, os seguintes gates devem ser 100% cumpridos:

1. **Gate de Suíte Oficial:**
   ```powershell
   python -m unittest discover -s tests -v
   ```
   Deve passar com zero erros, zero falhas e zero skips, atingindo rigorosamente:
   `883 + novos testes da Issue #133` (100% GREEN).
2. **Gate de Integridade Documental:**
   ```powershell
   git diff --check
   ```
   Deve retornar limpo, sem trailing whitespaces ou conflitos de quebra de linha.
3. **Gate de Estado Operacional:**
   ```powershell
   git status -sb
   ```
   Durante o desenvolvimento, `git status -sb` é utilizado para verificar que somente arquivos pertencentes ao incremento estão alterados.

   No gate final pré-PR / pós-commit:
   - working tree deve estar limpa;
   - branch deve ser a branch correta do incremento;
   - não devem existir alterações não relacionadas à Issue #133.

---

## 12. Impacto de versionamento (SemVer)

- **Impacto previsto:** `MINOR`;
- **Justificativa:** Introdução de nova capacidade metrológica pública e aditiva em memória (`DuplicatePairPrediction`, `DuplicatePairCaseEvaluation`, `DuplicatePairEvaluationReport`, `evaluate_duplicate_pair`, `evaluate_duplicate_pairs`), sem quebra ou mutação de contratos existentes no ecossistema;
- **Release formal atual:** Permanece `v0.1.0` (o merge da Issue fecha o incremento funcional, sem queima de release).

---

## 13. Riscos e mitigações

| Risco Identificado | Severidade | Estratégia de Mitigação |
|---|---|---|
| Confusão entre par relacional não-direcional e material individual | Alta | Definição formal de unidade estatística: par obrigatório `(material_id_a, material_id_b)`. Proibição de tratamento de duplicidade a nível de material individual. |
| Aceitação ou inversão silenciosa de par invertido `(B, A)` | Média | Validação estrita e fail-closed `material_id_a < material_id_b` levantando `ValueError`. Nenhuma correção ou reordenação silenciosa é permitida. |
| Auto-par cadastral `(A, A)` | Alta | Validação estrita `material_id_a != material_id_b` levantando `ValueError`. |
| Confusão entre `evaluation_case_id` e identificadores de materiais | Alta | `evaluation_case_id` é chave única experimental no mapping de predições e no dataset; `(material_id_a, material_id_b)` identifica a entidade relacional de domínio. |
| Mistura prematura de métricas estatísticas agregadas (Precision/Recall/F1) | Média | A v1 foca exclusivamente em exatidão categórica (`accuracy`, `is_match`, `is_mismatch`). Métricas de benchmark multiclasses/binárias permanecem explicitamente adiadas. |
| Acoplamento acidental a motores de similaridade, embeddings ou LLM | Alta | A camada de avaliação opera puramente sobre os contratos `DuplicatePairPrediction` e `DuplicatePairGroundTruth`, sem importação ou invocação de algoritmos de similaridade. |
| Regressão dos avaliadores existentes (#124 e #129) | Baixa | A implementação é puramente aditiva no módulo `ground_truth_evaluation.py`, com execução contínua do baseline de 883 testes. |

---

## 14. Decisões deliberadamente adiadas

Ficam expressamente adiadas para incrementos futuros:
1. Métricas de Precision, Recall e F1 para duplicidades;
2. Exposição de TP, FP, FN, TN como API pública agregada;
3. Matriz de confusão e relatórios estatísticos visuais;
4. Métricas de especificidade, curvas ROC e curvas Precision-Recall;
5. Calibração de thresholds de similaridade;
6. Inclusão de scores contínuos de confiança ou similaridade em predições;
7. Algoritmos de clustering, blocagem ou componentes conexos para pares de duplicidade;
8. Persistência em disco/banco de dados de predições e avaliações;
9. Loaders externos de datasets e fixtures (CSV, JSONL, Parquet);
10. Benchmark runner / orquestrador de execução de pipelines contra gabaritos;
11. Consenso e adjudicação multi-anotador;
12. Integração com o pipeline de governança (`GovernanceAssessment` / `DecisionRecommendation`);
13. Migração, adaptação ou desativação da metrologia legada (`baseline.py`, `data_io.py`).

---

## 15. Critérios de aceite da SPEC

- [ ] SPEC técnica formal elaborada e em conformidade com a Issue #133;
- [ ] Implementação de `DuplicatePairPrediction`, `DuplicatePairCaseEvaluation` e `DuplicatePairEvaluationReport` com `frozen=True, slots=True` e `dataset_id: str` obrigatório;
- [ ] Implementação de `evaluate_duplicate_pair` e `evaluate_duplicate_pairs`;
- [ ] Validações defensivas fail-closed para tipos nominais (`TypeError`), disparidade relacional de `material_id_a`/`material_id_b` (`ValueError`), auto-pares (`ValueError`), pares invertidos (`ValueError`), chaves faltantes e excedentes (`ValueError`);
- [ ] Ordenação canônica determinística compulsória dos casos no relatório garantida por `(evaluation_case_id, ground_truth_id)`;
- [ ] Semântica explícita de coleção vazia (`accuracy is None`, `is_empty is True`, `total_cases == 0`) comprovada;
- [ ] Imutabilidade estrita dos novos contratos comprovada com `FrozenInstanceError`;
- [ ] Exportações canônicas adicionadas a `src/agent_lab/__init__.py` e `__all__`;
- [ ] Bateria abrangente de testes unitários defensivos implementada em `tests/test_ground_truth_evaluation.py` cobrindo todos os 6 slices;
- [ ] Baseline de 883 testes mantido 100% GREEN (`883 + novos testes da Issue #133`);
- [ ] `git diff --check` aprovado sem trailing whitespace;
- [ ] Status atualizado para `IMPLEMENTED` após a conclusão do ciclo TDD.
