# SPEC-0129 — Ground Truth Material Rule Evaluator v1

> Especificação técnica da camada de avaliação pura, determinística e em memória para aferição
> de predições de regras cadastrais de materiais (`IssueType`) contra referências de Ground Truth no Agent Lab Pascoal.

---

## Metadados

| Campo | Valor |
|---|---|
| **Identificador** | `SPEC-0129` |
| **Status** | `PROPOSED` |
| **Issue relacionada** | `#129` |
| **Título da Issue** | `Ground Truth Material Rule Evaluator v1` |
| **Branch documental** | `docs/issue-129-material-rule-ground-truth-evaluator-spec` |
| **Branch funcional planejada** | `feature/issue-129-ground-truth-material-rule-evaluator` |
| **Responsável** | `Jk-Pascoal` |
| **Data de criação** | `2026-09-17` |
| **Última atualização** | `2026-09-17` |
| **Baseline de entrada** | `830 testes aprovados` (100% GREEN) |
| **Baseline planejado** | `830 + N testes aprovados` (100% GREEN) |
| **Runner oficial** | `python -m unittest discover -s tests -v` (Python 3.11) |

---

## 1. Contexto

Nas Issues #115 (SPEC-0115) e #119 (SPEC-0119), o Agent Lab Pascoal inaugurou a frente evolutiva **"Ground truth e benchmark"**, estabelecendo no módulo `src/agent_lab/ground_truth.py`:
1. Os contratos atômicos de dados puros: `LabelProvenance`, `MaterialRuleGroundTruth`, `DuplicatePairGroundTruth` e `DecisionRecommendationGroundTruth`;
2. Os contratos para coleções canônicas de avaliação: `MaterialRuleGroundTruthDataset`, `DuplicatePairGroundTruthDataset` e `DecisionRecommendationGroundTruthDataset`.

Na Issue subsequente #124 (SPEC-0124), foi introduzida no módulo `src/agent_lab/ground_truth_evaluation.py` a primeira camada de avaliação pura em memória: o avaliador de recomendações de decisão (`evaluate_decision_recommendation` e `evaluate_decision_recommendations`), consolidando um baseline de **830 testes aprovados** (100% GREEN) na branch `main`.

A etapa presente dá continuidade à esteira de metrologia determinística do laboratório, focando na avaliação de regras cadastrais de materiais (`MaterialRuleGroundTruth` e `MaterialRuleGroundTruthDataset`).

Diferente da recomendação algorítmica de governança — que opera sobre um escalar único e mutuamente exclusivo (`GovernanceDecision: APPROVE | REVIEW | REJECT`) —, a verificação de regras cadastrais opera sobre um **conjunto multirrótulo** de defeitos (`expected_issue_types: tuple[IssueType, ...]`), exigindo uma semântica de conjuntos formalmente definida para exatidão, falsos positivos e falsos negativos.

---

## 2. Problema, evidências e impacto

### Problema
O Agent Lab Pascoal possui os contratos de dados para gabaritos de regras cadastrais (`MaterialRuleGroundTruth` e `MaterialRuleGroundTruthDataset`), mas não dispõe de uma camada formal, pura, determinística e imutável para comparar predições de regras de conformidade contra os gabaritos de referência em memória, validar integridade relacional, calcular diagnósticos detalhados de conjuntos e emitir relatórios canônicos consolidados.

### Evidências
1. `MaterialRuleGroundTruth` define `expected_issue_types: tuple[IssueType, ...]`, com ordenação canônica interna e rejeição fail-closed de duplicatas, mas não existe função ou read-model no sistema capaz de comparar predições de regras contra essa expectativa;
2. Natureza multirrótulo não-escalar: um material pode não apresentar nenhum defeito de regra (`expected_issue_types = ()`), apresentar um defeito (`(IssueType.INVALID_UNIT,)`), ou múltiplos defeitos simultâneos (`(IssueType.INVALID_UNIT, IssueType.MISSING_CRITICAL_FIELD)`);
3. Risco de avaliações ad-hoc: scripts externos ou testes isolados tendem a comparar listas diretamente sem canonicalização, tornando a comparação sensível à ordem das regras disparadas ou permitindo correções silenciosas de predições malformadas;
4. Ambiguidade de pareamento: `material_id` identifica o item cadastral do domínio PDM/BOM, enquanto `evaluation_case_id` identifica o caso de benchmark. Pareamentos implícitos criam risco de associar predições aos gabaritos errados quando um material é testado sob diferentes cenários sintéticos ou históricos;
5. Ausência de tratamento explícito para conjuntos vazios, duplicidades de entrada e violação de fronteiras de unidades estatísticas (ex.: inserção acidental de `IssueType.POSSIBLE_DUPLICATE`).

### Impacto
Sem um avaliador canônico formal:
- Avaliações de acurácia de regras serão discrepantes e não auditáveis entre diferentes execuções;
- Erros de falsos positivos (alarmes falsos) e falsos negativos (defeitos não detectados) não serão discriminados no nível de cada caso;
- Risco de aceitar silenciosamente predições com dados duplicados ou malformados, mascarando falhas estruturais nos componentes upstream;
- Violação do princípio arquitetural de segregação estrita entre predição (`Prediction`), gabarito (`Ground Truth`), coleções (`Dataset`) e métricas (`Metric`).

---

## 3. Objetivo

Introduzir no módulo `src/agent_lab/ground_truth_evaluation.py` a camada pura de domínio e metrologia em memória (zero-I/O) para avaliação determinística de predições de regras cadastrais de materiais contra `MaterialRuleGroundTruth` e `MaterialRuleGroundTruthDataset`:

1. Definir o contrato imutável de predição `MaterialRulePrediction(material_id, predicted_issue_types)` com rejeição fail-closed estrita de duplicatas;
2. Definir o contrato imutável de resultado atômico `MaterialRuleCaseEvaluation` com semântica de conjuntos explícita (`is_match`, `is_mismatch`, `false_positives`, `false_negatives`, `true_positives`);
3. Definir o contrato imutável de relatório consolidado `MaterialRuleEvaluationReport` com rastreabilidade compulsória de `dataset_id`, ordenação canônica e métricas derivadas puras sem arredondamento interno;
4. Implementar a função pura atômica `evaluate_material_rule(ground_truth, prediction)`;
5. Implementar a função pura de lote `evaluate_material_rules(dataset, predictions: Mapping[str, MaterialRulePrediction])` indexada estritamente por `evaluation_case_id`;
6. Formalizar a semântica rigorosa de avaliação de conjuntos para casos limítrofes (ambos vazios, esperado vazio, previsto vazio, rejeição de entradas duplicadas e independência de ordem);
7. Exportar publicamente os novos símbolos canônicos no pacote raiz `src/agent_lab/__init__.py`;
8. Garantir 100% de preservação do baseline pré-existente de 830 testes GREEN.

---

## 4. Escopo

### Incluído
- Contrato imutável de entrada `MaterialRulePrediction` (`frozen=True, slots=True`);
- Contrato imutável de diagnóstico de caso `MaterialRuleCaseEvaluation` (`frozen=True, slots=True`);
- Contrato imutável de relatório de avaliação `MaterialRuleEvaluationReport` (`frozen=True, slots=True`);
- Função pura `evaluate_material_rule(ground_truth: MaterialRuleGroundTruth, prediction: MaterialRulePrediction) -> MaterialRuleCaseEvaluation`;
- Função pura de lote `evaluate_material_rules(dataset: MaterialRuleGroundTruthDataset, predictions: Mapping[str, MaterialRulePrediction]) -> MaterialRuleEvaluationReport`;
- Pareamento determinístico por `evaluation_case_id`;
- Validação relacional fail-closed por `material_id` (`ValueError` em caso de divergência);
- Semântica de conjuntos estrita:
  - Exact set match: `is_match = True` se e somente se o conjunto de tipos previstos for idêntico ao conjunto de tipos esperados;
  - Falsos positivos (`false_positives`): elementos previstos que não pertencem ao esperado, expostos externamente como tupla canônica ordenada por `item.value`;
  - Falsos negativos (`false_negatives`): elementos esperados que não foram previstos, expostos externamente como tupla canônica ordenada por `item.value`;
  - Verdadeiros positivos (`true_positives`): elementos presentes tanto em previstos quanto em esperados, expostos externamente como tupla canônica ordenada por `item.value`;
  - Conjuntos vazios: se esperado for vazio e previsto for vazio, `is_match = True`, `is_clean_match = True`, e FP/FN/TP são tuplas vazias `()`;
  - Entradas duplicadas na predição: **rejeitadas fail-closed com `ValueError`**; nenhuma correção ou deduplicação silenciosa é realizada no contrato de predição;
  - Ordenação da predição: a ordem fornecida é semanticamente irrelevante para o conjunto, mas a representação interna e exposta é deterministicamente canonicalizada como `tuple` ordenada por `item.value` após a validação de unicidade;
- Bloqueio estrito fail-closed de `IssueType.POSSIBLE_DUPLICATE` em `MaterialRulePrediction` (`ValueError`), preservando a segregação de unidades estatísticas estabelecida na SPEC-0115;
- Rastreabilidade de linhagem: `ground_truth_id` preservado no caso individual e `dataset_id` obrigatório no relatório de lote;
- Ordenação determinística de casos no relatório por tupla `(evaluation_case_id, ground_truth_id)`;
- Semântica explícita de dataset vazio (`accuracy = None`, `exact_match_ratio = None`, `is_empty = True`);
- Cálculo de exatidão (`accuracy` e `exact_match_ratio`) como divisão direta de ponto flutuante `matched_cases / total_cases` sem arredondamento interno;
- Bateria de testes unitários defensivos em `tests/test_ground_truth_evaluation.py`;
- Exportação canônica no pacote raiz `src/agent_lab/__init__.py`.

### Fora de escopo
- Avaliador de duplicidades (`DuplicatePairGroundTruth` e `DuplicatePairGroundTruthDataset`);
- Persistência em disco, JSONL, SQLite ou bancos de dados;
- Loaders ou parsers de dados externos (CSV, JSONL, Parquet, Excel);
- Factories ou adapters de conversão de ocorrências brutas para `MaterialRulePrediction` (ex.: `from_issues(...)`), que permanecem como responsabilidade do chamador ou para evolução futura;
- Execução de regras de validação durante a avaliação (o avaliador consome predições já emitidas, sem invocar `run_rules` ou motores);
- Execução de modelos de linguagem (LLM);
- Benchmark runner, orquestração de testes massivos ou CLI;
- Métricas agregadas de Precision, Recall e F1 multiclasse em macro/micro averaging (reservadas para SPEC dedicada de agregação estatística);
- Matrizes de confusão e relatórios visuais;
- Calibração de thresholds, sensibilidade e pesos;
- Consenso e adjudicação de anotações discordantes;
- Interfaces gráficas (UI/Streamlit), APIs REST ou CLI;
- Integração com ERP/PDM corporativo;
- Alteração ou remoção da metrologia legada (`src/agent_lab/baseline.py`, `src/agent_lab/data_io.py`).

---

## 5. Responsabilidade humana e limites do agente

No Agent Lab Pascoal:
- `MaterialRulePrediction` é a asserção diagnóstica formalizada emitida por uma regra ou agente sobre inconformidades de catálogo em um material;
- `MaterialRuleGroundTruth` é o gabarito normativo aprovado por curadoria especializada (`SPECIALIST_CURATED`) ou fixture controlada de especificação (`SYNTHETIC_SPECIFIED`);
- O avaliador determinístico atua puramente como instrumento de medição metrológica. Ele não altera materiais, não executa mutações em cadastros e não dispensa a deliberação do especialista de governança humana sobre o catálogo de materiais.

---

## 6. Requisitos

### Requisitos funcionais

- `RF-01` — Definir o dataclass imutável `MaterialRulePrediction(material_id: str, predicted_issue_types: tuple[IssueType, ...])` com `frozen=True, slots=True`.
- `RF-02` — Validar `MaterialRulePrediction`:
  - `material_id` deve ser `str` não-vazia e sanitizada via `.strip()`, rejeitando tipos inválidos com `TypeError` e vazios/whitespace com `ValueError`;
  - `predicted_issue_types` deve ser `tuple`, rejeitando outros contêineres com `TypeError`;
  - todos os elementos de `predicted_issue_types` devem ser instâncias de `IssueType`, rejeitando outros tipos com `TypeError`;
  - `IssueType.POSSIBLE_DUPLICATE` não é permitido em `predicted_issue_types`, falhando fail-closed com `ValueError`;
  - **rejeitar fail-closed qualquer duplicata em `predicted_issue_types` com `ValueError`** (`len(predicted_issue_types) != len(set(predicted_issue_types))`), sem realizar deduplicação ou correção silenciosa;
  - canonicalizar deterministicamente a representação interna pós-validação como tupla ordenada por `item.value`.
- `RF-03` — Definir o dataclass imutável `MaterialRuleCaseEvaluation` com `frozen=True, slots=True` contendo:
  - `evaluation_case_id: str`
  - `ground_truth_id: str`
  - `material_id: str`
  - `expected_issue_types: tuple[IssueType, ...]`
  - `predicted_issue_types: tuple[IssueType, ...]`
- `RF-04` — Validar `MaterialRuleCaseEvaluation`:
  - campos textuais (`evaluation_case_id`, `ground_truth_id`, `material_id`) devem ser `str` não-vazias e sanitizadas (`TypeError` / `ValueError`);
  - `expected_issue_types` e `predicted_issue_types` devem ser `tuple` contendo apenas instâncias de `IssueType` válidos sem `POSSIBLE_DUPLICATE`, sem duplicatas e canonicalizados em ordem crescente por `item.value`.
- `RF-05` — Expor propriedades puras derivadas em `MaterialRuleCaseEvaluation`:
  - `is_match -> bool`: verdadeiro se e somente se `predicted_issue_types == expected_issue_types`;
  - `is_mismatch -> bool`: inverso de `is_match` (`not is_match`);
  - `false_positives -> tuple[IssueType, ...]`: elementos em `predicted_issue_types` que não estão em `expected_issue_types`, expostos como tupla canônica ordenada por `item.value`;
  - `false_negatives -> tuple[IssueType, ...]`: elementos em `expected_issue_types` que não estão em `predicted_issue_types`, expostos como tupla canônica ordenada por `item.value`;
  - `true_positives -> tuple[IssueType, ...]`: elementos presentes tanto em `predicted_issue_types` quanto em `expected_issue_types`, expostos como tupla canônica ordenada por `item.value`;
  - `has_false_positives -> bool`: `len(false_positives) > 0`;
  - `has_false_negatives -> bool`: `len(false_negatives) > 0`;
  - `is_clean_match -> bool`: `is_match and len(expected_issue_types) == 0`;
  - `is_defect_match -> bool`: `is_match and len(expected_issue_types) > 0`.
- `RF-06` — Implementar a função pura atômica `evaluate_material_rule(ground_truth: MaterialRuleGroundTruth, prediction: MaterialRulePrediction) -> MaterialRuleCaseEvaluation`:
  - validar nominalmente os tipos de entrada (`TypeError`);
  - validar fail-closed correspondência relacional `prediction.material_id == ground_truth.material_id`, rejeitando divergências com `ValueError`;
  - emitir `MaterialRuleCaseEvaluation` com pareamento dos metadados de `ground_truth` e conjuntos canonicalizados.
- `RF-07` — Definir o dataclass imutável `MaterialRuleEvaluationReport` com `frozen=True, slots=True` contendo:
  - `dataset_id: str`
  - `cases: tuple[MaterialRuleCaseEvaluation, ...]`
- `RF-08` — Validar `MaterialRuleEvaluationReport`:
  - `dataset_id` deve ser `str` não-vazia e sanitizada via `.strip()` (`TypeError` / `ValueError`);
  - `cases` deve ser `tuple` de instâncias `MaterialRuleCaseEvaluation` (`TypeError`);
  - rejeitar `evaluation_case_id` duplicado em `cases` com `ValueError`;
  - ordenar deterministicamente `cases` pela tupla canônica `(c.evaluation_case_id, c.ground_truth_id)`.
- `RF-09` — Expor propriedades puras derivadas em `MaterialRuleEvaluationReport`:
  - `total_cases -> int`: contagem total de casos avaliados (`len(cases)`);
  - `matched_cases -> int`: número de casos com exatidão completa (`is_match == True`);
  - `mismatched_cases -> int`: `total_cases - matched_cases`;
  - `accuracy -> float | None`: taxa de exatidão de conjunto (`matched_cases / total_cases`), calculada sem arredondamento interno e retornando `None` se `total_cases == 0`;
  - `exact_match_ratio -> float | None`: alias semântico idêntico para `accuracy`, retornando exatamente o mesmo valor sem arredondamento;
  - `total_false_positives -> int`: soma de falsos positivos ocorridos em todos os casos (`sum(len(c.false_positives) for c in cases)`);
  - `total_false_negatives -> int`: soma de falsos negativos ocorridos em todos os casos (`sum(len(c.false_negatives) for c in cases)`);
  - `total_true_positives -> int`: soma de verdadeiros positivos ocorridos em todos os casos (`sum(len(c.true_positives) for c in cases)`);
  - `is_empty -> bool`: verdadeiro se `total_cases == 0`;
  - `is_perfect_match -> bool`: verdadeiro se `total_cases > 0 and matched_cases == total_cases`;
  - `matches -> tuple[MaterialRuleCaseEvaluation, ...]`: tupla dos casos com `is_match == True`;
  - `mismatches -> tuple[MaterialRuleCaseEvaluation, ...]`: tupla dos casos com `is_mismatch == True`.
- `RF-10` — Implementar a função pura de lote `evaluate_material_rules(dataset: MaterialRuleGroundTruthDataset, predictions: Mapping[str, MaterialRulePrediction]) -> MaterialRuleEvaluationReport`:
  - validar nominalmente tipos de entrada (`TypeError`);
  - validar que todas as chaves de `predictions` sejam `str` não-booleanas (`TypeError`);
  - validar que todos os valores de `predictions` sejam `MaterialRulePrediction` (`TypeError`);
  - validar paridade estrita biunívoca 1:1 entre as chaves de `predictions` e os `evaluation_case_id` de `dataset.items`;
  - rejeitar chaves faltantes com `ValueError`;
  - rejeitar chaves excedentes com `ValueError`;
  - para cada item do dataset, obter a predição correspondente, validar coerência de `material_id` e delegar à função atômica `evaluate_material_rule`;
  - retornar `MaterialRuleEvaluationReport` ordenado e validado.
- `RF-11` — Tratar formalmente datasets vazios:
  - se `dataset.items == ()` e `predictions` for um mapeamento vazio `{}`, retornar relatório com `total_cases = 0`, `matched_cases = 0`, `mismatched_cases = 0`, `accuracy = None`, `exact_match_ratio = None`, `total_false_positives = 0`, `total_false_negatives = 0`, `total_true_positives = 0`, `is_empty = True`, `is_perfect_match = False`, `matches = ()` e `mismatches = ()`.
- `RF-12` — Exportar publicamente no pacote raiz `src/agent_lab/__init__.py`:
  - `MaterialRulePrediction`
  - `MaterialRuleCaseEvaluation`
  - `MaterialRuleEvaluationReport`
  - `evaluate_material_rule`
  - `evaluate_material_rules`

### Requisitos de qualidade

- `RQ-01` — **Zero I/O:** execução exclusivamente em memória sem interações com disco, rede, subprocessos ou threads.
- `RQ-02` — **Imutabilidade estrita:** todas as estruturas implementadas como `@dataclass(frozen=True, slots=True)` sem dicionário interno mutável (`__dict__`).
- `RQ-03` — **Determinismo canônico:** ordens de apresentação de tuplas, listas ou iterações externas não afetam o resultado final; a ordenação interna é compulsória por chaves estáveis.
- `RQ-04` — **Fail-closed:** separação rigorosa entre `TypeError` (tipos nominais incorretos) e `ValueError` (anomalias estruturais, relacionais, de dados, duplicatas ou regras de negócio).
- `RQ-05` — **Isolamento de dependências:** utilização exclusiva da biblioteca padrão do Python 3.11.

---

## 7. Proposta técnica

### 7.1 Semântica de Avaliação de Conjuntos (Set Evaluation Semantics)

Seja $E = \text{set}(expected\_issue\_types)$ o conjunto de regras violadas segundo o gabarito.
Seja $P = \text{set}(predicted\_issue\_types)$ o conjunto de regras violadas reportadas pela predição.

A tabela formaliza o comportamento determinístico para todos os cenários operacionais:

| Cenário | Condição Matemática | `is_match` | `true_positives` | `false_positives` | `false_negatives` | Semântica de Domínio |
|---|---|:---:|:---:|:---:|:---:|---|
| **Ambos vazios** | $E = \emptyset \land P = \emptyset$ | `True` | `()` | `()` | `()` | Material íntegro no gabarito; sistema não apontou defeitos. Acerto limpo (`is_clean_match`). |
| **Acerto exato com defeitos** | $E = P \neq \emptyset$ | `True` | tuple(sorted(E)) | `()` | `()` | Sistema detectou exatamente o mesmo conjunto de defeitos do gabarito (`is_defect_match`). |
| **Gabarito vazio, predição com defeitos** | $E = \emptyset \land P \neq \emptyset$ | `False` | `()` | tuple(sorted(P)) | `()` | Material íntegro; sistema disparou alarmes falsos (todos os previstos são FP). |
| **Gabarito com defeitos, predição vazia** | $E \neq \emptyset \land P = \emptyset$ | `False` | `()` | `()` | tuple(sorted(E)) | Material defeituoso; sistema não detectou nenhum problema (todos os esperados são FN). |
| **Interseção parcial** | $E \cap P \neq \emptyset \land E \neq P$ | `False` | tuple(sorted(E ∩ P)) | tuple(sorted(P \ E)) | tuple(sorted(E \ P)) | Sistema acertou alguns defeitos (TP), mas gerou alarmes falsos adicionais (FP) e deixou de capturar outros (FN). |
| **Disjunção total** | $E \cap P = \emptyset \land E \neq \emptyset \land P \neq \emptyset$ | `False` | `()` | tuple(sorted(P)) | tuple(sorted(E)) | Erro completo de tipificação; nenhum defeito esperado foi identificado, e todos os reportados eram incorretos. |

#### Política estrita de duplicatas e canonicalização
- Em `MaterialRulePrediction`, **duplicatas são estritamente proibidas** e geram `ValueError`. Não ocorre deduplicação silenciosa. O contrato exige que o chamador forneça uma asserção de predição categórica já consolidada e válida.
- A ordem de inserção original em `predicted_issue_types` é semanticamente irrelevante para a semântica de conjunto, mas a representação interna armazenada e exposta é sempre canonicalizada como uma tupla ordenada pelo valor textual de `IssueType` (`item.value`), garantindo determinismo estrito nas comparações de tupla (`==`).
- Os diagnósticos de conjunto (`false_positives`, `false_negatives`, `true_positives`) são sempre expostos externamente como `tuple[IssueType, ...]` ordenados deterministicamente por `item.value`, nunca expondo conjuntos mutáveis (`set`) ou representações sensíveis à ordem.

### 7.2 Fluxo arquitetural

```text
[Dataset: MaterialRuleGroundTruthDataset]     [Predictions: Mapping[str, MaterialRulePrediction]]
                     │                                              │
                     └──────────────────────┬───────────────────────┘
                                            ▼
                          evaluate_material_rules (Batch)
                                            │
               ┌────────────────────────────┴────────────────────────────┐
               ▼                                                         ▼
    Validação de Tipos (TypeError)                           Validação 1:1 de Chaves
                                                          Missing / Extra Keys (ValueError)
                                                                         │
                                            ┌────────────────────────────┘
                                            ▼
                           Para cada item do dataset:
                           pred = predictions[case_id]
                                            │
                                            ▼
                               evaluate_material_rule (Atômica)
                                            │
                                            ├─► Validação pred.material_id == item.material_id (ValueError)
                                            ├─► Comparação de conjuntos (P vs E)
                                            └─► Retorna MaterialRuleCaseEvaluation
                                            │
                                            ▼
                        Ordenação Canônica determinística dos casos:
                            (evaluation_case_id, ground_truth_id)
                                            │
                                            ▼
                       Retorno: MaterialRuleEvaluationReport
```

### 7.3 Contratos de Dados e Funções

```python
@dataclass(frozen=True, slots=True)
class MaterialRulePrediction:
    """Predição de regras cadastrais de materiais associada a um material_id."""

    material_id: str
    predicted_issue_types: tuple[IssueType, ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "material_id",
            _normalize_required_text(self.material_id, "material_id"),
        )
        if not isinstance(self.predicted_issue_types, tuple):
            raise TypeError("predicted_issue_types must be a tuple")

        for item in self.predicted_issue_types:
            if not isinstance(item, IssueType):
                raise TypeError("predicted_issue_types must contain only IssueType instances")

        if IssueType.POSSIBLE_DUPLICATE in self.predicted_issue_types:
            raise ValueError("POSSIBLE_DUPLICATE is not permitted in MaterialRulePrediction")

        if len(self.predicted_issue_types) != len(set(self.predicted_issue_types)):
            raise ValueError("predicted_issue_types must not contain duplicates")

        canonical = tuple(sorted(self.predicted_issue_types, key=lambda item: item.value))
        object.__setattr__(self, "predicted_issue_types", canonical)


@dataclass(frozen=True, slots=True)
class MaterialRuleCaseEvaluation:
    """Resultado imutável da avaliação de regras cadastrais de um caso individual."""

    evaluation_case_id: str
    ground_truth_id: str
    material_id: str
    expected_issue_types: tuple[IssueType, ...]
    predicted_issue_types: tuple[IssueType, ...]

    def __post_init__(self) -> None: ...

    @property
    def is_match(self) -> bool:
        return self.predicted_issue_types == self.expected_issue_types

    @property
    def is_mismatch(self) -> bool:
        return not self.is_match

    @property
    def false_positives(self) -> tuple[IssueType, ...]:
        expected_set = set(self.expected_issue_types)
        fp = [item for item in self.predicted_issue_types if item not in expected_set]
        return tuple(sorted(fp, key=lambda item: item.value))

    @property
    def false_negatives(self) -> tuple[IssueType, ...]:
        predicted_set = set(self.predicted_issue_types)
        fn = [item for item in self.expected_issue_types if item not in predicted_set]
        return tuple(sorted(fn, key=lambda item: item.value))

    @property
    def true_positives(self) -> tuple[IssueType, ...]:
        expected_set = set(self.expected_issue_types)
        tp = [item for item in self.predicted_issue_types if item in expected_set]
        return tuple(sorted(tp, key=lambda item: item.value))

    @property
    def has_false_positives(self) -> bool:
        return len(self.false_positives) > 0

    @property
    def has_false_negatives(self) -> bool:
        return len(self.false_negatives) > 0

    @property
    def is_clean_match(self) -> bool:
        return self.is_match and len(self.expected_issue_types) == 0

    @property
    def is_defect_match(self) -> bool:
        return self.is_match and len(self.expected_issue_types) > 0


@dataclass(frozen=True, slots=True)
class MaterialRuleEvaluationReport:
    """Relatório estruturado e imutável da avaliação em lote de regras cadastrais."""

    dataset_id: str
    cases: tuple[MaterialRuleCaseEvaluation, ...]

    def __post_init__(self) -> None: ...

    @property
    def total_cases(self) -> int:
        return len(self.cases)

    @property
    def matched_cases(self) -> int:
        return sum(1 for c in self.cases if c.is_match)

    @property
    def mismatched_cases(self) -> int:
        return self.total_cases - self.matched_cases

    @property
    def accuracy(self) -> float | None:
        if self.total_cases == 0:
            return None
        return self.matched_cases / self.total_cases

    @property
    def exact_match_ratio(self) -> float | None:
        return self.accuracy

    @property
    def total_false_positives(self) -> int:
        return sum(len(c.false_positives) for c in self.cases)

    @property
    def total_false_negatives(self) -> int:
        return sum(len(c.false_negatives) for c in self.cases)

    @property
    def total_true_positives(self) -> int:
        return sum(len(c.true_positives) for c in self.cases)

    @property
    def is_empty(self) -> bool:
        return self.total_cases == 0

    @property
    def is_perfect_match(self) -> bool:
        return self.total_cases > 0 and self.matched_cases == self.total_cases

    @property
    def matches(self) -> tuple[MaterialRuleCaseEvaluation, ...]:
        return tuple(c for c in self.cases if c.is_match)

    @property
    def mismatches(self) -> tuple[MaterialRuleCaseEvaluation, ...]:
        return tuple(c for c in self.cases if c.is_mismatch)


def evaluate_material_rule(
    ground_truth: MaterialRuleGroundTruth,
    prediction: MaterialRulePrediction,
) -> MaterialRuleCaseEvaluation: ...


def evaluate_material_rules(
    dataset: MaterialRuleGroundTruthDataset,
    predictions: Mapping[str, MaterialRulePrediction],
) -> MaterialRuleEvaluationReport: ...
```

### 7.4 Arquivos previstos

- `src/agent_lab/ground_truth_evaluation.py` — implementação de `MaterialRulePrediction`, `MaterialRuleCaseEvaluation`, `MaterialRuleEvaluationReport`, `evaluate_material_rule` e `evaluate_material_rules`;
- `src/agent_lab/__init__.py` — exportação canônica dos novos contratos e funções na raiz do pacote;
- `tests/test_ground_truth_evaluation.py` — suíte de testes unitários defensivos para a avaliação de regras;
- `docs/specs/0129_ground_truth_material_rule_evaluator_v1.md` — esta especificação técnica formal.

---

## 8. Estratégia de testes e TDD

A implementação seguirá o ciclo rigoroso TDD em slices incrementais:

### Slice 1 — Contrato `MaterialRulePrediction`
- Instanciação nominal, sanitização `.strip()` de `material_id`;
- Rejeição de vazios/whitespace com `ValueError`;
- Validação de `predicted_issue_types` como `tuple` contendo apenas `IssueType` (`TypeError`);
- Bloqueio estrito de `IssueType.POSSIBLE_DUPLICATE` com `ValueError`;
- **Rejeição fail-closed de duplicatas em `predicted_issue_types` com `ValueError`**;
- Canonicalização por ordenação de `item.value` após validação de unicidade;
- Imutabilidade (`FrozenInstanceError`).

### Slice 2 — Contrato `MaterialRuleCaseEvaluation`
- Instanciação nominal e normalização de strings;
- Validação de tuplas de `IssueType` canonicalizadas e rejeição de duplicatas;
- Propriedades de conjunto como `tuple[IssueType, ...]`: `is_match`, `is_mismatch`, `false_positives`, `false_negatives`, `true_positives`;
- Propriedades booleanas: `has_false_positives`, `has_false_negatives`, `is_clean_match`, `is_defect_match`;
- Matriz completa de cenários: ambos vazios, esperado vazio, previsto vazio, interseção parcial, disjunção total;
- Imutabilidade (`FrozenInstanceError`).

### Slice 3 — Função `evaluate_material_rule`
- Comparação atômica entre `MaterialRuleGroundTruth` e `MaterialRulePrediction`;
- Validação fail-closed de tipos (`TypeError`);
- Validação fail-closed de divergência de `material_id` (`ValueError`);
- Pareamento de `evaluation_case_id` e `ground_truth_id`.

### Slice 4 — Contrato `MaterialRuleEvaluationReport`
- Instanciação nominal com `dataset_id: str` obrigatório;
- Rejeição de `evaluation_case_id` duplicados em `cases` (`ValueError`);
- Ordenação canônica determinística por `(evaluation_case_id, ground_truth_id)`;
- Métricas derivadas puras: `total_cases`, `matched_cases`, `mismatched_cases`, `accuracy` e `exact_match_ratio` sem arredondamento, somatórios de FP/FN/TP;
- Comportamento formal para relatório vazio (`accuracy is None`, `exact_match_ratio is None`, `is_empty is True`);
- Imutabilidade (`FrozenInstanceError`).

### Slice 5 — Função `evaluate_material_rules` (Batch)
- Consumo estrito de `Mapping[str, MaterialRulePrediction]` indexado por `evaluation_case_id`;
- Validação fail-closed de chaves faltantes (`ValueError`);
- Validação fail-closed de chaves excedentes (`ValueError`);
- Validação relacional de `material_id` para cada item;
- Independência da ordem de inserção do mapping de entrada;
- Avaliação com mapping vazio `{}` contra dataset vazio (`items = ()`).

### Slice 6 — Integração e Exports Canônicos
- Atualização e verificação de exports em `src/agent_lab/__init__.py`;
- Verificação da suíte completa de testes:
  ```powershell
  python -m unittest discover -s tests -v
  ```
- Garantia de 830 + N testes GREEN (100% aprovados).

---

## 9. Gates de qualidade

Comandos mandatórios de verificação pré-merge:

```powershell
python -m unittest discover -s tests -v
git diff --check
git status -sb
```

Critérios de aprovação:
- 100% dos testes da suíte aprovados sem falhas ou erros;
- `git diff --check` limpo (zero trailing whitespace ou problemas de formato);
- Nenhuma dependência externa adicionada;
- Segregação de unidades estatísticas preservada.

---

## 10. Riscos e limitações

| Risco ou limitação | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| **Confusão entre unidades estatísticas (Regras vs. Duplicidade)** | Média | Alto | Bloqueio estrito fail-closed de `IssueType.POSSIBLE_DUPLICATE` em `MaterialRulePrediction` com `ValueError`. |
| **Aceitação silenciosa de predições com anomalias** | Média | Alto | Rejeição fail-closed de duplicatas em `predicted_issue_types` com `ValueError`, impedindo deduplicação silenciosa. |
| **Distorção de acurácia por multiplicidade de defeitos por material** | Baixa | Médio | Documentação clara de que `accuracy` representa *Exact Match Ratio* (acerto integral do conjunto) e não micro-averaging multirrótulo. |
| **Pareamento indevido por material_id** | Média | Alto | Pareamento compulsório por `evaluation_case_id` na API batch, utilizando `material_id` apenas como checagem relacional de consistência. |
| **Divisão por zero em dataset vazio** | Baixa | Médio | Definição formal de `accuracy -> float | None` retornando `None` quando `total_cases == 0`. |
| **Inconsistência na ordem de apresentação dos defeitos** | Baixa | Baixo | Canonicalização determinística obrigatória por `IssueType.value` em todas as representações públicas expostas como tuplas. |

---

## 11. Plano de reversão

Por se tratar de adição modular e incremental em `src/agent_lab/ground_truth_evaluation.py`:
1. Reverter os commits do incremento ou o merge do PR na branch `main`;
2. A remoção dos novos contratos restaura o baseline estável de 830 testes GREEN sem qualquer efeito colateral nas demais capacidades do sistema.

---

## 12. Versionamento e release

### Impacto SemVer
- `MINOR` — introdução de nova capacidade metrológica de avaliação de regras sem quebra de contratos de domínio vigentes.

### Publicação prevista
- Status: `Unreleased`;
- Tag: Não aplicável nesta etapa;
- Release formal: Permanece `v0.1.0` até consolidação formal da frente de benchmark.

---

## 13. Critérios de aceite (Acceptance Criteria)

- [ ] SPEC técnica formal aprovada pelo arquiteto humano;
- [ ] Implementação de `MaterialRulePrediction` com `frozen=True, slots=True`, rejeição fail-closed de duplicatas e bloqueio de `POSSIBLE_DUPLICATE`;
- [ ] Implementação de `MaterialRuleCaseEvaluation` com `frozen=True, slots=True` e semântica de conjuntos (`false_positives`, `false_negatives`, `true_positives`, `is_match`, `is_clean_match`, `is_defect_match`);
- [ ] Implementação de `MaterialRuleEvaluationReport` com `frozen=True, slots=True`, `dataset_id` compulsório e ordenação canônica;
- [ ] Implementação de `evaluate_material_rule(ground_truth, prediction)`;
- [ ] Implementação de `evaluate_material_rules(dataset, predictions)` aceitando estritamente `Mapping[str, MaterialRulePrediction]`;
- [ ] Validação fail-closed estrita para tipos nominais (`TypeError`), divergência de `material_id` (`ValueError`), duplicatas de `IssueType` (`ValueError`), chaves faltantes (`ValueError`) e chaves excedentes (`ValueError`);
- [ ] Semântica explícita de coleção vazia (`accuracy is None`, `exact_match_ratio is None`, `is_empty is True`);
- [ ] Cálculo de `accuracy` / `exact_match_ratio` sem arredondamento interno;
- [ ] Independência de ordem comprovada por testes;
- [ ] Exportações canônicas adicionadas a `src/agent_lab/__init__.py`;
- [ ] Bateria de testes unitários defensivos implementada em `tests/test_ground_truth_evaluation.py`;
- [ ] Baseline integrado de 830 testes mantido 100% GREEN (830 + N novos testes);
- [ ] `git diff --check` aprovado sem trailing whitespace.

---

## 14. Decisões arquiteturais tomadas

| Data | Decisão | Motivo | Responsável |
|---|---|---|---|
| `2026-09-17` | Criação de contrato dedicado `MaterialRulePrediction(material_id, predicted_issue_types)` | Permite validação relacional por `material_id` antes da comparação e isola a predição da camada de avaliação. | `Jk-Pascoal` |
| `2026-09-17` | Bloqueio fail-closed de `IssueType.POSSIBLE_DUPLICATE` em `MaterialRulePrediction` | Preserva a segregação das unidades estatísticas estabelecida na SPEC-0115 (duplicidade é avaliada via pares não-direcionais em `DuplicatePairGroundTruth`). | `Jk-Pascoal` |
| `2026-09-17` | Rejeição fail-closed de duplicatas em `predicted_issue_types` com `ValueError` | O contrato de predição representa uma asserção categórica já válida. Deduplicação e normalização pertencem a futuras factories explícitas (ex.: `from_issues(...)`), evitando correções silenciosas de predições malformadas. | `Jk-Pascoal` |
| `2026-09-17` | Exposição de `false_positives`, `false_negatives` e `true_positives` como tuplas imutáveis ordenadas | Garante imutabilidade estrita e determinismo absoluto nas representações públicas de conjunto, evitando mutabilidade de `set` ou sensibilidade à ordem de chegada. | `Jk-Pascoal` |
| `2026-09-17` | Formalização de `is_clean_match` e `is_defect_match` | Distingue com precisão semântica casos onde o sistema acertou a ausência completa de defeitos daqueles em que acertou os defeitos efetivamente existentes. | `Jk-Pascoal` |
| `2026-09-17` | Exclusão de métricas agregadas multiclasse (Precision/Recall/F1 macro/micro) em v1 | O relatório foca na exatidão de conjunto (*Exact Match Ratio*) e na contagem agregada de FP/FN/TP. Agregações estatísticas por classe exigem convenções formais de suporte que cabem em uma SPEC subsequente de métricas. | `Jk-Pascoal` |
| `2026-09-17` | `accuracy` e `exact_match_ratio` calculados sem arredondamento interno | Preserva a precisão matemática total de ponto flutuante, delegando arredondamento para a camada de apresentação quando aplicável. | `Jk-Pascoal` |

---

## 15. Dúvidas arquiteturais remanescentes

1. **Agregação futura de Precision/Recall/F1 por IssueType:**
   - No relatório consolidado de v1, são expostas as contagens brutas (`total_true_positives`, `total_false_positives`, `total_false_negatives`) e a taxa de exatidão do conjunto (`accuracy` / `exact_match_ratio`).
   - Para v2, deve-se deliberar se métricas como Precision/Recall/F1 por classe de `IssueType` serão computadas no próprio relatório ou em uma função utilitária dedicada de métricas (`src/agent_lab/metrics.py`).
2. **Conexão futura com `GovernanceAssessment`:**
   - Na v1, o contrato aceita estritamente `MaterialRulePrediction`.
   - Pode-se avaliar no futuro um método de conveniência de borda (ex.: `MaterialRulePrediction.from_assessment(assessment: GovernanceAssessment)`) para extrair os `issue_type` das `issues` do assessment, excluindo duplicidades. Na v1, isso permanece responsabilidade do chamador.
