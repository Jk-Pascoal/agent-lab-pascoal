# SPEC-0124 — Ground Truth Decision Recommendation Evaluator v1

> Especificação técnica da camada de avaliação pura, determinística e em memória para aferição
> de recomendações algorítmicas de governança contra referências de Ground Truth no Agent Lab Pascoal.

---

## Metadados

| Campo | Valor |
|---|---|
| **Identificador** | `SPEC-0124` |
| **Status** | `APPROVED` |
| **Issue relacionada** | `#124` |
| **Título da Issue** | `Ground Truth Decision Recommendation Evaluator v1` |
| **Branch funcional** | `feature/issue-124-ground-truth-decision-recommendation-evaluator` (a ser criada na fase funcional) |
| **Responsável** | `Jk-Pascoal` |
| **Data de criação** | `2026-09-15` |
| **Última atualização** | `2026-09-15` |
| **Baseline de entrada** | `776 testes aprovados` (100% GREEN) |
| **Runner oficial** | `python -m unittest discover -s tests -v` (Python 3.11) |

---

## 1. Contexto

Nas Issues #115 (SPEC-0115) e #119 (SPEC-0119), o Agent Lab Pascoal inaugurou a frente evolutiva **"Ground truth e benchmark"**, introduzindo no módulo `src/agent_lab/ground_truth.py`:
1. Os contratos atômicos de dados puros: `MaterialRuleGroundTruth`, `DuplicatePairGroundTruth`, `DecisionRecommendationGroundTruth` e `LabelProvenance`;
2. Os contratos de coleções canônicas de avaliação: `MaterialRuleGroundTruthDataset`, `DuplicatePairGroundTruthDataset` e `DecisionRecommendationGroundTruthDataset`.

A integração desses incrementos elevou o baseline consolidado na branch `main` para **776 testes aprovados** (100% GREEN).

Com os contratos atômicos e coleções canônicas de gabarito formalizados e validados, a etapa seguinte consiste em transformar essas estruturas de dados em instrumentos ativos de aferição metrológica determinística. O primeiro avaliador da esteira foca na avaliação da recomendação algorítmica de governança (`DecisionRecommendation`) em relação à verdade de referência estabelecida (`DecisionRecommendationGroundTruth`).

---

## 2. Problema, evidências e impacto

### Problema
O sistema dispõe de contratos para a recomendação gerada pelo pipeline (`DecisionRecommendation`) e para a expectativa auditada de governança (`DecisionRecommendationGroundTruth` / `DecisionRecommendationGroundTruthDataset`), mas não possui uma camada canônica, determinística e imutável para comparar predições contra gabaritos e emitir diagnósticos avaliativos.

### Evidências
1. Não existe função pura no sistema que receba `DecisionRecommendation` e `DecisionRecommendationGroundTruth` e valide sua correspondência estrutural e categórica;
2. Não existe read-model imutável para representar o resultado atômico de uma comparação (`match` vs. `mismatch`) nem o sumário consolidado de um lote de avaliação;
3. Ambiguidade de pareamento: `material_id` identifica a entidade cadastral de domínio, enquanto `evaluation_case_id` identifica o caso experimental. Pareamentos implícitos ou ad-hoc criam risco de associar predições aos casos errados quando o mesmo material participa de múltiplos cenários de teste;
4. Risco de não-determinismo na agregação e na ordenação de resultados de avaliação;
5. Ausência de comportamento explícito e matematicamente rigoroso para conjuntos vazios de avaliação.

### Impacto
Sem um avaliador determinístico formal:
- Avaliações de exatidão de recomendações seriam dispersas em scripts não-governados;
- Risco de associações incorretas entre predição e caso de teste sem bloqueio fail-closed;
- Impossibilidade de produzir benchmarks comparativos reprodutíveis e auditáveis;
- Violação do princípio de segregação entre fatos do domínio, gabaritos e métricas.

---

## 3. Objetivo

Introduzir a camada pura de domínio/metrologia em memória (zero-I/O) para avaliar recomendações de decisão contra ground truth no Agent Lab Pascoal:
1. `evaluate_decision_recommendation`: função pura que compara um `DecisionRecommendation` contra um `DecisionRecommendationGroundTruth`, validando correspondência estrutural de `material_id` e emitindo `DecisionRecommendationCaseEvaluation`;
2. `evaluate_decision_recommendations`: função pura que avalia um mapeamento explícito de predições contra um `DecisionRecommendationGroundTruthDataset`, validando correspondência biunívoca estrita por `evaluation_case_id` (paridade exata 1:1, sem chaves faltantes nem excedentes), verificando consistência de `material_id` e produzindo `DecisionRecommendationEvaluationReport`;
3. Contratos de dados imutáveis `DecisionRecommendationCaseEvaluation` e `DecisionRecommendationEvaluationReport` (`frozen=True, slots=True`), fornecendo diagnóstico discriminado de match/mismatch, contagens agregadas, taxa de exact-match (accuracy), `dataset_id` obrigatório e ordenação canônica determinística independente da ordem de entrada.

---

## 4. Escopo

### Incluído
- Criação do módulo `src/agent_lab/ground_truth_evaluation.py`;
- Dataclass imutável `DecisionRecommendationCaseEvaluation` (`frozen=True, slots=True`);
- Dataclass imutável `DecisionRecommendationEvaluationReport` (`frozen=True, slots=True`) com `dataset_id: str` obrigatório;
- Função pura `evaluate_decision_recommendation(ground_truth, prediction)`;
- Função pura batch `evaluate_decision_recommendations(dataset, predictions)` aceitando estritamente `Mapping[str, DecisionRecommendation]` indexado por `evaluation_case_id`;
- Validação defensiva fail-closed: `TypeError` para tipos nominais inválidos e `ValueError` para chaves faltantes, chaves excedentes e divergências de `material_id`;
- Ordenação canônica determinística compulsória no relatório por `(evaluation_case_id, ground_truth_id)`;
- Semântica formal e explícita para dataset vazio (`accuracy = None`, `is_empty = True`);
- Propriedades puras derivadas sem redundância de estado: `is_match`, `is_mismatch`, `total_cases`, `matched_cases`, `mismatched_cases`, `accuracy`, `is_empty`, `is_perfect_match`, `matches`, `mismatches`;
- Exportação canônica no pacote raiz `src/agent_lab/__init__.py`;
- Bateria de testes unitários defensivos em `tests/test_ground_truth_evaluation.py`;
- Preservação estrita dos 776 testes GREEN existentes.

### Fora de escopo
- Suporte a `Sequence[DecisionRecommendation]` na API batch (eliminado para evitar pareamento implícito por `material_id`);
- Persistência em disco (JSONL, SQLite, etc.);
- Loaders ou parsers externos (CSV, JSONL, Parquet, Excel);
- Dependências de bibliotecas externas (scikit-learn, pandas, numpy, scipy);
- Métricas estatísticas de Precision, Recall e F1 (fora de escopo até a definição formal de classe positiva para decisões ternárias de governança);
- Matrizes de confusão e relatórios gráficos;
- Avaliação de regras materiais individuais (`MaterialRuleGroundTruth`) ou duplicidades (`DuplicatePairGroundTruth`);
- Alteração ou adaptação da metrologia legada (`baseline.py`, `data_io.py`);
- Alteração no pipeline de decisão em produção (`decision.py`).

---

## 5. Responsabilidade humana e limites do agente

No Agent Lab Pascoal:
- `DecisionRecommendation` é uma hipótese algorítmica emitida pelo sistema, com `requires_human_decision = True` compulsório;
- `DecisionRecommendationGroundTruth` é o gabarito normativo auditável, sustentado por autoridade de especialista verificado (`SPECIALIST_CURATED`) ou fixture sintética controlada (`SYNTHETIC_SPECIFIED`);
- O avaliador determinístico apenas calcula a concordância exata entre a recomendação gerada e o gabarito. Ele não substitui a revisão humana e não concede autoridade operacional a recomendações automáticas.

---

## 6. Requisitos

### Requisitos funcionais
- `RF-01` — Comparar `DecisionRecommendation` contra `DecisionRecommendationGroundTruth`, emitindo `DecisionRecommendationCaseEvaluation`;
- `RF-02` — Validar que `prediction.material_id == ground_truth.material_id` em cada caso individual, rejeitando divergências com `ValueError`;
- `RF-03` — Discriminar categoricamente acerto (`is_match`) e erro (`is_mismatch`) para as três decisões possíveis (`APPROVE`, `REVIEW`, `REJECT`);
- `RF-04` — Executar avaliação em lote sobre `DecisionRecommendationGroundTruthDataset` consumindo exclusivamente `Mapping[str, DecisionRecommendation]` onde cada chave é um `evaluation_case_id`;
- `RF-05` — Rejeitar com `ValueError` mapeamentos com chaves faltantes em relação ao dataset;
- `RF-06` — Rejeitar com `ValueError` mapeamentos com chaves excedentes em relação ao dataset;
- `RF-07` — Validar que `prediction.material_id == ground_truth.material_id` para cada par obtido por `evaluation_case_id`, rejeitando inconsistências com `ValueError`;
- `RF-08` — Ordenar deterministicamente os casos no relatório pela chave canônica `(evaluation_case_id, ground_truth_id)`, independente da ordem das chaves no mapeamento de entrada;
- `RF-09` — Exigir `dataset_id: str` obrigatório no relatório, assegurando rastreabilidade da coleção de origem;
- `RF-10` — Tratar formalmente coleções vazias: se o dataset possuir `items == ()` e o mapeamento de predições for vazio `{}` (ou `mapping` vazio), retornar relatório com `total_cases = 0`, `matched_cases = 0`, `mismatched_cases = 0`, `is_empty = True`, `is_perfect_match = False` e `accuracy = None`.

### Requisitos de qualidade
- `RQ-01` — **Zero I/O:** execução estritamente em memória sem efeitos colaterais em disco, rede ou processos externos;
- `RQ-02` — **Imutabilidade estrita:** estruturas definidas com `@dataclass(frozen=True, slots=True)` sem `__dict__`;
- `RQ-03` — **Ausência de estado derivado redundante:** contagens e taxas calculadas em tempo real via `@property` a partir da tupla fundamental `cases`;
- `RQ-04` — **Fail-closed:** validações estritas de tipo (`TypeError`) e de integridade relacional (`ValueError`);
- `RQ-05` — **Isolamento de dependências:** utilização exclusiva da biblioteca padrão do Python 3.11.

---

## 7. Proposta técnica

### 7.1 Visão geral

O avaliador opera como uma camada pura de metrologia:

```text
Ground Truth + Prediction -> Evaluation Result
```

Distinção fundamental de autoridade relacional:
- `material_id` identifica a entidade de domínio;
- `evaluation_case_id` identifica o caso experimental no dataset.

Ao exigir `Mapping[str, DecisionRecommendation]` indexado por `evaluation_case_id`, o avaliador garante pareamento metrológico inequívoco, permitindo inclusive que o mesmo material participe de múltiplos casos experimentais distintos sem risco de colisão ou ambiguidade.

### 7.2 Fluxo esperado

```text
[Dataset + Predictions Mapping]
             ↓
Validação nominal de tipos (TypeError)
             ↓
Validação de paridade estrita de chaves: keys == dataset.case_ids (ValueError)
             ↓
Para cada item do dataset:
   Obtém pred = predictions[item.evaluation_case_id]
   Valida pred.material_id == item.material_id (ValueError)
   Avalia case: evaluate_decision_recommendation(item, pred)
             ↓
Ordenação determinística por (evaluation_case_id, ground_truth_id)
             ↓
Retorno de DecisionRecommendationEvaluationReport(dataset_id=dataset.dataset_id, cases=tuple(...))
```

### 7.3 Contratos de dados

#### 7.3.1 `DecisionRecommendationCaseEvaluation`
```python
@dataclass(frozen=True, slots=True)
class DecisionRecommendationCaseEvaluation:
    """Resultado imutável da avaliação determinística de um caso individual."""

    evaluation_case_id: str
    ground_truth_id: str
    material_id: str
    expected_decision: GovernanceDecision
    predicted_decision: GovernanceDecision

    def __post_init__(self) -> None:
        text_fields = ("evaluation_case_id", "ground_truth_id", "material_id")
        for field_name in text_fields:
            object.__setattr__(
                self,
                field_name,
                _normalize_required_text(getattr(self, field_name), field_name),
            )

        if not isinstance(self.expected_decision, GovernanceDecision):
            raise TypeError("expected_decision must be a GovernanceDecision")

        if not isinstance(self.predicted_decision, GovernanceDecision):
            raise TypeError("predicted_decision must be a GovernanceDecision")

    @property
    def is_match(self) -> bool:
        return self.predicted_decision == self.expected_decision

    @property
    def is_mismatch(self) -> bool:
        return not self.is_match
```

#### 7.3.2 `DecisionRecommendationEvaluationReport`
```python
@dataclass(frozen=True, slots=True)
class DecisionRecommendationEvaluationReport:
    """Relatório estruturado e imutável da avaliação em lote de recomendações."""

    dataset_id: str
    cases: tuple[DecisionRecommendationCaseEvaluation, ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "dataset_id",
            _normalize_required_text(self.dataset_id, "dataset_id"),
        )

        if not isinstance(self.cases, tuple):
            raise TypeError("cases must be a tuple")

        case_ids: set[str] = set()
        for idx, item in enumerate(self.cases):
            if not isinstance(item, DecisionRecommendationCaseEvaluation):
                raise TypeError(
                    f"cases[{idx}] must be a DecisionRecommendationCaseEvaluation instance"
                )
            if item.evaluation_case_id in case_ids:
                raise ValueError(
                    f"duplicate evaluation_case_id in cases: {item.evaluation_case_id!r}"
                )
            case_ids.add(item.evaluation_case_id)

        canonical = tuple(
            sorted(
                self.cases,
                key=lambda c: (c.evaluation_case_id, c.ground_truth_id),
            )
        )
        object.__setattr__(self, "cases", canonical)

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
    def is_empty(self) -> bool:
        return self.total_cases == 0

    @property
    def is_perfect_match(self) -> bool:
        return self.total_cases > 0 and self.matched_cases == self.total_cases

    @property
    def matches(self) -> tuple[DecisionRecommendationCaseEvaluation, ...]:
        return tuple(c for c in self.cases if c.is_match)

    @property
    def mismatches(self) -> tuple[DecisionRecommendationCaseEvaluation, ...]:
        return tuple(c for c in self.cases if c.is_mismatch)
```

#### 7.3.3 Funções de Avaliação
```python
def evaluate_decision_recommendation(
    ground_truth: DecisionRecommendationGroundTruth,
    prediction: DecisionRecommendation,
) -> DecisionRecommendationCaseEvaluation:
    """Compara deterministicamente uma predição contra um gabarito individual."""
    if not isinstance(ground_truth, DecisionRecommendationGroundTruth):
        raise TypeError("ground_truth must be a DecisionRecommendationGroundTruth")

    if not isinstance(prediction, DecisionRecommendation):
        raise TypeError("prediction must be a DecisionRecommendation")

    if prediction.material_id != ground_truth.material_id:
        raise ValueError(
            f"material_id mismatch: prediction has {prediction.material_id!r}, "
            f"ground_truth has {ground_truth.material_id!r}"
        )

    return DecisionRecommendationCaseEvaluation(
        evaluation_case_id=ground_truth.evaluation_case_id,
        ground_truth_id=ground_truth.ground_truth_id,
        material_id=ground_truth.material_id,
        expected_decision=ground_truth.expected_recommendation,
        predicted_decision=prediction.decision,
    )


def evaluate_decision_recommendations(
    dataset: DecisionRecommendationGroundTruthDataset,
    predictions: Mapping[str, DecisionRecommendation],
) -> DecisionRecommendationEvaluationReport:
    """Avalia em lote um conjunto de predições indexado por evaluation_case_id."""
    if not isinstance(dataset, DecisionRecommendationGroundTruthDataset):
        raise TypeError("dataset must be a DecisionRecommendationGroundTruthDataset")

    if not isinstance(predictions, Mapping):
        raise TypeError("predictions must be a Mapping[str, DecisionRecommendation]")

    dataset_case_ids = {item.evaluation_case_id for item in dataset.items}
    pred_case_ids = set(predictions.keys())

    missing = dataset_case_ids - pred_case_ids
    if missing:
        raise ValueError(
            f"missing predictions for evaluation_case_id(s): {sorted(missing)!r}"
        )

    extra = pred_case_ids - dataset_case_ids
    if extra:
        raise ValueError(
            f"unexpected predictions for evaluation_case_id(s) not in dataset: {sorted(extra)!r}"
        )

    evaluated_cases: list[DecisionRecommendationCaseEvaluation] = []
    for item in dataset.items:
        pred = predictions[item.evaluation_case_id]
        if not isinstance(pred, DecisionRecommendation):
            raise TypeError(
                f"prediction for evaluation_case_id {item.evaluation_case_id!r} "
                f"must be a DecisionRecommendation, got {type(pred).__name__}"
            )
        evaluated = evaluate_decision_recommendation(item, pred)
        evaluated_cases.append(evaluated)

    return DecisionRecommendationEvaluationReport(
        dataset_id=dataset.dataset_id,
        cases=tuple(evaluated_cases),
    )
```

### 7.4 Arquivos previstos
- `src/agent_lab/ground_truth_evaluation.py` — implementação dos novos contratos e funções de avaliação;
- `src/agent_lab/__init__.py` — exportação pública canônica dos novos contratos e funções;
- `tests/test_ground_truth_evaluation.py` — suíte de testes unitários defensivos;
- `docs/specs/0124_ground_truth_decision_recommendation_evaluator_v1.md` — esta especificação técnica.

---

## 8. Estratégia de testes e TDD

### Vermelho (RED)
Construção de testes em `tests/test_ground_truth_evaluation.py` exercitando:
1. Instanciação nominal e propriedades de `DecisionRecommendationCaseEvaluation`;
2. Avaliação atômica `evaluate_decision_recommendation` com matches e mismatches para `APPROVE`, `REVIEW` e `REJECT`;
3. Bloqueio fail-closed de `material_id` divergente;
4. Instanciação nominal e propriedades de `DecisionRecommendationEvaluationReport` com `dataset_id` obrigatório;
5. Avaliação em lote `evaluate_decision_recommendations` com mapping de predições por `evaluation_case_id`;
6. Bloqueio fail-closed para chaves faltantes, chaves excedentes e tipos inválidos;
7. Comportamento determinístico para dataset vazio (`accuracy = None`);
8. Independência da ordem das chaves de entrada;
9. Imutabilidade (`FrozenInstanceError`);
10. Exportação canônica em `src/agent_lab/__init__.py`.

### Verde (GREEN)
Implementação estritamente suficiente em `src/agent_lab/ground_truth_evaluation.py` e atualização de exports em `src/agent_lab/__init__.py`.

### Regressão
Execução da suíte canônica completa:
```powershell
python -m unittest discover -s tests -v
```
Garantia de 776 + N testes GREEN (100% aprovados).

---

## 9. Gates de qualidade

```powershell
python -m unittest discover -s tests -v
git diff --check
git status -sb
```

Critérios mínimos:
- 100% dos testes aprovados;
- Zero avisos de whitespace em `git diff --check`;
- Modificação restrita aos arquivos previstos;
- Sem dependências externas introduzidas.

---

## 10. Riscos e limitações

| Risco ou limitação | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| **Pareamento incorreto por material_id** | Média | Alto | Mitigado pela remoção do pareamento implícito por sequência e adoção estrita de mapping por `evaluation_case_id`. |
| **Divisão por zero em dataset vazio** | Média | Médio | Mitigado pela definição formal de `@property accuracy -> float | None` retornando `None` se `total_cases == 0`. |
| **Descompasso interno entre métricas** | Baixa | Alto | Mitigado pela eliminação de campos redundantes, usando `@property` sobre o fato atômico `cases`. |
| **Não-determinismo na iteração** | Média | Médio | Mitigado pela ordenação canônica compulsória por `(evaluation_case_id, ground_truth_id)` no relatório. |
| **Ambiguidade de classes em métricas binárias** | Alta | Médio | Foco estrito em exact-match categórico e acurácia; Precision/Recall/F1 excluídos de v1. |

---

## 11. Plano de reversão

Por se tratar de adição de módulo independente em camada de domínio:
1. Reverter o commit de implementação na branch ou o merge do PR na `main`;
2. A remoção de `src/agent_lab/ground_truth_evaluation.py` e seus testes restaura imediatamente o baseline anterior de 776 testes GREEN sem impacto nos demais módulos.

---

## 12. Versionamento e release

### Impacto SemVer
- `MINOR` — adição de nova capacidade de avaliação sem quebra de contratos existentes.

### Publicação prevista
- Versão planejada: `Unreleased`;
- Criação de tag: Não;
- Criação de GitHub Release: Não;
- Atualização do `PROJECT_COMPASS.md`: Apenas no closeout documental após conclusão da implementação funcional.

---

## 13. Critérios de aceite (Acceptance Criteria)

- [ ] SPEC técnica formal aprovada e consolidada;
- [ ] Implementação de `DecisionRecommendationCaseEvaluation` com `frozen=True, slots=True`;
- [ ] Implementação de `DecisionRecommendationEvaluationReport` com `frozen=True, slots=True` e `dataset_id: str` obrigatório;
- [ ] Implementação da função pura `evaluate_decision_recommendation(ground_truth, prediction)`;
- [ ] Implementação da função pura `evaluate_decision_recommendations(dataset, predictions)` consumindo exclusivamente `Mapping[str, DecisionRecommendation]`;
- [ ] Validação fail-closed estrita para tipos inválidos (`TypeError`), `material_id` mismatch (`ValueError`), chaves faltantes (`ValueError`) e chaves excedentes (`ValueError`);
- [ ] Ordenação determinística compulsória de `cases` por `(evaluation_case_id, ground_truth_id)` comprovada;
- [ ] Semântica formal de coleção vazia (`accuracy is None`, `is_empty is True`, `total_cases == 0`) comprovada;
- [ ] Imutabilidade estrita dos read-models comprovada com `FrozenInstanceError`;
- [ ] Exportações canônicas adicionadas a `src/agent_lab/__init__.py`;
- [ ] Bateria de testes unitários defensivos implementada em `tests/test_ground_truth_evaluation.py`;
- [ ] Baseline integrado de 776 testes mantido 100% GREEN (776 + novos testes);
- [ ] `git diff --check` aprovado sem trailing whitespace.

---

## 14. Questões em aberto

`Nenhuma`. Os dois ajustes arquiteturais (obrigatoriedade de `dataset_id` e restrição da API batch a `Mapping[str, DecisionRecommendation]` indexado por `evaluation_case_id`) foram formalizados e sanados em 15/09/2026.

---

## 15. Histórico de decisões

| Data | Decisão | Motivo | Responsável |
|---|---|---|---|
| `2026-09-15` | Adoção estrita de `Mapping[str, DecisionRecommendation]` para avaliação batch | Eliminar pareamento implícito por `material_id`; o mesmo material pode participar de múltiplos casos experimentais, tornando `evaluation_case_id` a única chave inequívoca. | `Jk-Pascoal` |
| `2026-09-15` | `dataset_id: str` obrigatório em `DecisionRecommendationEvaluationReport` | Preservar a linhagem explícita entre o relatório de avaliação e a coleção de gabaritos avaliada. | `Jk-Pascoal` |
| `2026-09-15` | Exclusão de Precision, Recall e F1 na v1 de recomendação | `GovernanceDecision` é ternária (`APPROVE`, `REVIEW`, `REJECT`). Sem definição de classe positiva e averaging, exact-match (accuracy) é a única métrica matematicamente neutra. | `Jk-Pascoal` |
| `2026-09-15` | `@property accuracy -> float | None` com `None` para dataset vazio | Evitar divisão por zero e não fabricar valor arbitrário (0.0 ou 1.0) para conjuntos sem casos. | `Jk-Pascoal` |
