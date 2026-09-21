# SPEC-0141 — Ground Truth Decision Recommendation Benchmark Use Case v1

> Especificação técnica do caso de uso da camada de aplicação para orquestração e execução
> ponta a ponta de benchmark de recomendações de governança contra Ground Truth no Agent Lab Pascoal.

---

## Metadados

| Campo | Valor |
|---|---|
| **Identificador** | `SPEC-0141` |
| **Status** | `PROPOSED` |
| **Issue relacionada** | `#141` |
| **Título da Issue** | `Ground Truth Decision Recommendation Benchmark Use Case v1` |
| **Branch documental** | `docs/issue-141-decision-recommendation-benchmark-use-case` |
| **Responsável** | `Jk-Pascoal` |
| **Data de criação** | `2026-09-21` |
| **Última atualização** | `2026-09-21` |
| **Domínio** | Governança de materiais industriais PDM/BOM e Master Data |
| **Camada arquitetural** | Camada de Aplicação (`Application Layer`) |
| **Baseline de entrada** | `1015 testes aprovados` (100% GREEN) |
| **Impacto SemVer** | `MINOR` (puramente aditivo, release formal permanece `v0.1.0`) |
| **Runner oficial** | `python -m unittest discover -s tests -v` (Python 3.11) |

---

## 1. Contexto

O Agent Lab Pascoal consolidou progressivamente sua esteira metrológica de **Ground Truth & Benchmark**:
1. **Contratos atômicos de domínio puro (Issue #115 / SPEC-0115):** formalização de `MaterialRuleGroundTruth`, `DuplicatePairGroundTruth`, `DecisionRecommendationGroundTruth` e `LabelProvenance`;
2. **Coleções canônicas de avaliação (Issue #119 / SPEC-0119):** contêineres imutáveis `MaterialRuleGroundTruthDataset`, `DuplicatePairGroundTruthDataset` e `DecisionRecommendationGroundTruthDataset`;
3. **Avaliadores metrológicos determinísticos em memória (Issues #124, #129 e #133):** rotinas puras de aferição para recomendações (`SPEC-0124`), regras de materiais (`SPEC-0129`) e pares duplicados (`SPEC-0133`);
4. **Serialização atômica versionada (Issue #137 / SPEC-0137):** serialização pura em memória com `schema_version = 1`, closed-schema e fail-closed para os contratos atômicos, elevando o baseline integrado para **1015 testes aprovados (100% GREEN)**.

Paralelamente, o sistema dispõe de um pipeline funcional de governança que transforma registros brutos (`MaterialRecord`) em evidências estruturadas (`EvidenceCollection`) através do `DeterministicGovernanceValidator` e culmina na recomendação determinística `DecisionRecommendation` via `recommend_decision`.

Entretanto, as duas pontas permanecem desacopladas operacionalmente: não existe uma fronteira na camada de aplicação que receba casos experimentais de teste, coordene a execução do pipeline de recomendação, correlacione as predições geradas com os gabaritos e delegue a avaliação metrológica para o avaliador oficial.

Esta especificação define a primeira fatia vertical de benchmark ponta a ponta, restrita exclusivamente ao domínio de `DecisionRecommendation`.

---

## 2. Problema, evidências e impacto

### Problema
O Agent Lab dispõe de contratos de gabarito (`DecisionRecommendationGroundTruthDataset`), de um avaliador determinístico em lote (`evaluate_decision_recommendations`) e de um pipeline funcional produtivo que emite `DecisionRecommendation`, mas **não possui um caso de uso na camada de aplicação que orquestre a execução do pipeline sobre casos de teste e entregue o relatório oficial de avaliação**.

### Evidências
1. Inexistência de módulo orquestrador em `src/agent_lab` para acionar a avaliação em lote do pipeline de governança contra datasets de ground truth;
2. Os testes existentes em `tests/test_ground_truth_evaluation.py` exercitam `evaluate_decision_recommendations` fornecendo dicionários artificiais estáticos `Mapping[str, DecisionRecommendation]`, sem executar o pipeline real de regras e evidências;
3. Não há contrato explícito para representar um caso experimental de benchmark antes do processamento, forçando scripts eventuais a usar dicionários ad-hoc ou criar acoplamentos indevidos;
4. Risco de acoplamento relacional incorreto: ausência de um padrão para associar o `MaterialRecord` ao seu `evaluation_case_id`, gerando o risco de implementações futuras inferirem ou derivarem implicitamente o `evaluation_case_id` a partir do `material_id`.

### Impacto
Sem este boundary de aplicação:
- Inviabiliza-se a medição automatizada e auditável da acurácia do pipeline do Agent Lab;
- A frente metrológica permanece restrita a testes unitários isolados, sem comprovação empírica do valor do agente sobre dados cadastrais;
- Há risco de duplicação da lógica de avaliação dentro de scripts e pontos de entrada ad-hoc;
- Não se cumpre o princípio fundamental de engenharia do projeto (registrado no `README.md` e no `PROJECT_COMPASS.md`): *"A IA só entra onde demonstrar ganho mensurável sobre uma solução mais simples"*.

---

## 3. Objetivo

Introduzir na camada de aplicação o caso de uso `RunDecisionRecommendationBenchmarkUseCase` e o contrato de dados imutável `DecisionRecommendationBenchmarkCase`:
1. Receber um `DecisionRecommendationGroundTruthDataset` canônico e uma sequência de casos experimentais `DecisionRecommendationBenchmarkCase`;
2. Coordenar a execução do pipeline de governança sem duplicar ou reaprender regras de negócio;
3. Associar deterministicamente cada predição produzida ao seu respectivo `evaluation_case_id`;
4. Construir o mapeamento canônico `Mapping[str, DecisionRecommendation]` indexado por `evaluation_case_id`;
5. Delegar a aferição metrológica a `evaluate_decision_recommendations(dataset, predictions)`;
6. Retornar a estrutura oficial e imutável `DecisionRecommendationEvaluationReport`;
7. Garantir que `evaluation_case_id` (identidade experimental) e `material_id` (identidade de domínio) sejam tratados como identidades semanticamente independentes (onde nenhuma pode ser inferida da outra, permitindo-se coincidência textual quando fornecida explicitamente), com execução estritamente em memória (zero-I/O) e validação fail-closed.

---

## 4. Resposta aos 8 Critérios do PROJECT_COMPASS (§ 15)

1. **Qual limitação atual resolve?**
   Resolve a ausência de um orquestrador de aplicação que execute o pipeline real de recomendação de governança sobre uma bateria de testes e entregue o relatório oficial consolidado de benchmark.
2. **Qual evidência demonstra que a limitação importa agora?**
   Toda a esteira metrológica em memória (contratos, datasets, avaliadores e serialização) está pronta e validada por 354 testes GREEN específicos, mas permanece inativa em relação ao pipeline produtivo de materiais. Esta Issue fecha a primeira fatia vertical útil do benchmark.
3. **Qual é a menor entrega vertical testável?**
   O caso de uso `RunDecisionRecommendationBenchmarkUseCase` focado estritamente em `DecisionRecommendation`, operando em memória, consumindo `DecisionRecommendationBenchmarkCase` e delegando para `evaluate_decision_recommendations`.
4. **Quais invariantes existentes deve preservar?**
   - `Ground Truth != Prediction`
   - `Dataset != Metric`
   - `Evaluation Contract != Benchmark Result`
   - `evaluation_case_id` e `material_id` são identidades semanticamente independentes; nenhuma pode ser inferida ou derivada da outra;
   - Coincidência textual entre os valores de `evaluation_case_id` e `material_id` é perfeitamente válida e não constitui erro quando fornecida de forma explícita;
   - `Domain contract != Application coordination`
   - `Application coordena; Pipeline produz; Evaluator mede`
   - Fail-closed estrito e zero tolerância a reparos silenciosos;
   - Imutabilidade (`frozen=True, slots=True`) e pureza em memória (zero-I/O).
5. **O que ficará explicitamente fora do escopo?**
   Persistência em disco, loaders externos (JSONL/CSV), benchmark de regras materiais (`MaterialRuleGroundTruth`) ou duplicidades (`DuplicatePairGroundTruth`), métricas estatísticas (Precision/Recall/F1), dashboards, interface gráfica, concorrência e LLM remota.
6. **Como saberemos que a implementação funcionou?**
   Quando uma suíte abrangente de testes de aplicação comprovar: execução nominal com 100% de acerto gerando `accuracy = 1.0`, detecção correta de mismatches, rejeição fail-closed de disparidades de `material_id`, rejeição de casos faltantes/excedentes/duplicados, preservação do comportamento de dataset vazio e zero regressão no baseline de 1015 testes.
7. **Quantos novos riscos operacionais ela introduz?**
   Não introduz novos riscos de escrita ou efeitos operacionais sobre os fluxos produtivos; introduz riscos limitados de coordenação e correlação experimental, mitigados pelas validações propostas.
8. **A nova camada pode ser removida ou substituída sem corromper o domínio?**
   Sim. O use case reside estritamente na camada de aplicação. Sua remoção não afeta entidades de domínio, regras cadastrais, repositórios de auditoria ou contratos de lifecycle.

---

## 5. Princípios Arquiteturais e Responsabilidades

### 5.1 Princípio de Coordenação de Aplicação

```text
┌───────────────────────────────────────────────────────────────────────────────────┐
│ APPLICATION USE CASE: RunDecisionRecommendationBenchmarkUseCase                   │
│                                                                                   │
│  1. Recebe:                                                                       │
│     - dataset: DecisionRecommendationGroundTruthDataset                           │
│     - cases: Sequence[DecisionRecommendationBenchmarkCase]                        │
│                                                                                   │
│  2. Valida:                                                                       │
│     - Tipos nominais de fronteira (TypeError)                                     │
│     - Unicidade estrita de evaluation_case_id na entrada (ValueError)             │
│                                                                                   │
│  3. Coordena Pipeline (Pipeline produz):                                          │
│     Para cada case in cases:                                                      │
│       prediction = pipeline(case.material)                                        │
│       Valida prediction.material_id == case.material.material_id (ValueError)    │
│       predictions[case.evaluation_case_id] = prediction                           │
│                                                                                   │
│  4. Delega Metrologia (Evaluator mede):                                           │
│     report = evaluate_decision_recommendations(dataset, predictions)              │
│                                                                                   │
│  5. Retorna:                                                                      │
│     DecisionRecommendationEvaluationReport (Oficial, canônico e imutável)         │
└───────────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Responsabilidades Permitidas
- Validar tipos estruturais dos argumentos de entrada na camada de aplicação;
- Garantir a unicidade dos `evaluation_case_id` fornecidos na entrada;
- Invocar o pipeline de recomendação determinístico para cada caso;
- Montar o `Mapping[str, DecisionRecommendation]` estruturado;
- Repassar a avaliação integralmente para `evaluate_decision_recommendations`;
- Retornar a instância de `DecisionRecommendationEvaluationReport`.

### 5.3 Responsabilidades Proibidas
- **Proibido recalcular a métrica:** o use case não calcula `accuracy`, não conta `matched_cases` e não itera sobre `is_match`;
- **Proibido mutar entidades:** nem o dataset nem as entradas podem ser modificados;
- **Proibido inferir ou derivar `evaluation_case_id` a partir de `material_id`:** a associação deve ser estritamente explícita através do contrato do caso experimental (embora valores textuais coincidentes sejam permitidos quando declarados explicitamente);
- **Proibido realizar I/O:** sem leitura ou gravação de arquivos em disco ou chamadas de rede;
- **Proibido inventar novas regras de governança:** a lógica de emissão da recomendação pertence ao pipeline (`validator.py` e `decision.py`);
- **Proibido tolerar dados inconsistentes:** falhas de tipo ou correspondência levantam exceções imediatas (*fail-closed*).

---

## 6. Questão Arquitetural Central: Independência Semântica de Identidades

### 6.1 Problema
Como o use case deve receber a entrada do pipeline associada a um `evaluation_case_id` sem inferir nem assumir equivalência semântica com a entidade cadastral (`material_id`), preservando ao mesmo tempo a validade de coincidências textuais explícitas?

Princípios canônicos:
- `evaluation_case_id` é uma identidade experimental metrológica;
- `material_id` é uma identidade cadastral de domínio;
- São identidades semanticamente independentes: nenhuma pode ser inferida ou derivada da outra;
- Coincidência textual entre seus valores (ex.: `evaluation_case_id = "MAT-001"` e `material.material_id = "MAT-001"`) é perfeitamente válida e não constitui erro, desde que fornecida explicitamente;
- O mesmo material pode participar de múltiplos casos de teste com diferentes `evaluation_case_id` (ex.: `"CASE-01"`, `"CASE-02"` para o mesmo material `"MAT-001"`).

### 6.2 Análise das Alternativas

| Critério | Opção A: Contrato Explícito (`DecisionRecommendationBenchmarkCase`) | Opção B: Mapeamento Externo (`Mapping[str, MaterialRecord]`) | Opção C: Tuplas Primitivas (`tuple[str, MaterialRecord]`) |
|---|---|---|---|
| **Tipagem Nominal** | Estrita (`isinstance`) | Parcial (Mapping genérico) | Fraca (tupla genérica) |
| **Detecção de Duplicatas** | **Fail-Closed Imediato:** duplicatas em sequência geram `ValueError` explícito | **Silenciosa:** literais de dicionário Python `{k: v1, k: v2}` sobrescrevem chaves sem aviso | Exige validação manual de tupla |
| **Documentação Semântica** | Autoexplicativa via dataclass com `slots=True, frozen=True` | Depende de anotações de tipo | Ambígua quanto ao significado posicional |
| **Independência Semântica** | **Total:** `evaluation_case_id` é declarado explicitamente ao lado de `material: MaterialRecord`, sem inferência | Total | Total |
| **Desacoplamento de Gabarito** | Total: o caso não conhece a expectativa (`expected_recommendation`) | Total | Total |

### 6.3 Decisão Justificada
**Adota-se a Opção A (`DecisionRecommendationBenchmarkCase`).**
A introdução de um dataclass imutável dedicado:
1. Garante que `evaluation_case_id` (string canônica não-vazia) e `material` (`MaterialRecord`) sejam fornecidos explicitamente, impedindo qualquer dedução implícita de identidade;
2. Suporta de forma natural a coincidência textual (ex.: `evaluation_case_id="MAT-001"` com `material.material_id="MAT-001"`), visto que cada campo possui semântica e validação próprias;
3. Permite que a entrada seja uma sequência (`Sequence[DecisionRecommendationBenchmarkCase]`), possibilitando ao use case detectar e rejeitar duplicatas de `evaluation_case_id` de forma *fail-closed* (evitando a sobrescrita silenciosa inerente a literais de dicionário em Python);
4. Preserva `MaterialRecord` estritamente livre de metadados experimentais;
5. Preserva `DecisionRecommendation` estritamente livre de metadados experimentais;
6. Mantém o caso de teste cego em relação ao resultado esperado (que reside exclusivamente no Ground Truth Dataset).

---

## 7. Proposta Técnica

### 7.1 Módulo da Aplicação
Criar `src/agent_lab/decision_recommendation_benchmark_use_case.py`.

### 7.2 Contrato de Dados: `DecisionRecommendationBenchmarkCase`
```python
@dataclass(frozen=True, slots=True)
class DecisionRecommendationBenchmarkCase:
    """Caso experimental que associa uma identidade de teste ao registro a ser processado."""

    evaluation_case_id: str
    material: MaterialRecord

    def __post_init__(self) -> None:
        if not isinstance(self.evaluation_case_id, str) or isinstance(self.evaluation_case_id, bool):
            raise TypeError("evaluation_case_id must be a str")

        if not self.evaluation_case_id or self.evaluation_case_id != self.evaluation_case_id.strip():
            raise ValueError("evaluation_case_id must be a non-empty canonical string without outer whitespace")

        if not isinstance(self.material, MaterialRecord):
            raise TypeError("material must be a MaterialRecord")
```

### 7.3 Assinatura e Injeção no Caso de Uso: `RunDecisionRecommendationBenchmarkUseCase`
```python
# TypeAlias para o pipeline de recomendação
RecommendationPipeline = Callable[[MaterialRecord], DecisionRecommendation]

def _default_deterministic_pipeline(material: MaterialRecord) -> DecisionRecommendation:
    assessment = DeterministicGovernanceValidator().analyze(material)
    if assessment.evidence_collection is None:
        raise ValueError(f"Evidence collection missing for material '{material.material_id}'")
    return recommend_decision(assessment.evidence_collection)


class RunDecisionRecommendationBenchmarkUseCase:
    """Caso de uso de aplicação que orquestra a execução de benchmark de recomendações."""

    def __init__(
        self,
        pipeline: RecommendationPipeline | None = None,
    ) -> None:
        self._pipeline: RecommendationPipeline = (
            pipeline if pipeline is not None else _default_deterministic_pipeline
        )

    def execute(
        self,
        dataset: DecisionRecommendationGroundTruthDataset,
        cases: Sequence[DecisionRecommendationBenchmarkCase],
    ) -> DecisionRecommendationEvaluationReport:
        ...
```

### 7.4 Algoritmo de Execução
1. **Validação defensiva de argumentos:**
   - `isinstance(dataset, DecisionRecommendationGroundTruthDataset)` $\rightarrow$ `TypeError`;
   - `isinstance(cases, Sequence)` e não string/bytes $\rightarrow$ `TypeError`;
2. **Validação de integridade dos casos experimentais:**
   - Cada item de `cases` deve ser `isinstance(item, DecisionRecommendationBenchmarkCase)` $\rightarrow$ `TypeError`;
   - Validação de unicidade de `evaluation_case_id` em `cases`: se houver duplicatas $\rightarrow$ `ValueError`;
3. **Execução do pipeline de recomendação:**
   - Para cada `case` em `cases`:
     - `pred = self._pipeline(case.material)`
     - Se `not isinstance(pred, DecisionRecommendation)` $\rightarrow$ `TypeError`;
     - Se `pred.material_id != case.material.material_id` $\rightarrow$ `ValueError`;
     - Armazena em dicionário temporário `predictions[case.evaluation_case_id] = pred`;
4. **Delegação da aferição metrológica:**
   - Invoca `evaluate_decision_recommendations(dataset, predictions)`;
   - Observação: `evaluate_decision_recommendations` já aplica as invariantes consolidadas na SPEC-0124 (paridade 1:1 entre chaves do dataset e predições, rejeição de chaves faltantes ou extras, validação de consistência de `material_id` contra o gabarito, ordenação canônica e tratamento de dataset vazio);
5. **Retorno:**
   - Retorna o `DecisionRecommendationEvaluationReport` resultante.

---

## 8. Escopo

### Incluído
- Módulo `src/agent_lab/decision_recommendation_benchmark_use_case.py`;
- Dataclass imutável `DecisionRecommendationBenchmarkCase` (`frozen=True, slots=True`);
- Classe de caso de uso `RunDecisionRecommendationBenchmarkUseCase` com suporte a injeção e pipeline padrão determinístico;
- Validações defensivas nominais e fail-closed de tipos e integridade relacional;
- Exportação canônica dos novos símbolos em `src/agent_lab/__init__.py` e inclusão em `__all__`;
- Suíte abrangente de testes unitários e de integração em `tests/test_decision_recommendation_benchmark_use_case.py`;
- Preservação estrita dos 1015 testes GREEN existentes.

### Fora de Escopo
- Benchmark runners para regras de materiais (`MaterialRuleGroundTruth`) ou duplicidades (`DuplicatePairGroundTruth`);
- Persistência em disco de datasets, casos experimentais ou relatórios de benchmark;
- Loaders de arquivos externos (JSONL, CSV, Parquet, SQLite);
- Métricas estatísticas de Precision, Recall e F1 multiclasse;
- Matrizes de confusão e calibração de thresholds;
- Interface gráfica (Streamlit), REST APIs ou CLI;
- Execução concorrente, assíncrona ou multiprocesso;
- Integração com provedores remotos de LLM;
- Modificações na camada de domínio existente (`ground_truth.py`, `ground_truth_evaluation.py`) ou no baseline legado (`baseline.py`, `data_io.py`).

---

## 9. Estratégia de Testes e TDD

A implementação funcional seguirá TDD em micro-slices rigorosos.

### Cenários Previstos de Teste
1. **Contrato `DecisionRecommendationBenchmarkCase`:**
   - Instanciação válida com campos canônicos;
   - Coincidência textual válida: instanciação com `evaluation_case_id == material.material_id` aceita normalmente quando fornecida explicitamente;
   - Rejeição de `evaluation_case_id` não-string ou booleano (`TypeError`);
   - Rejeição de `evaluation_case_id` vazio ou com espaços nas bordas (`ValueError`);
   - Rejeição de `material` que não seja `MaterialRecord` (`TypeError`);
   - Imutabilidade comprovada (`FrozenInstanceError`).
2. **Execução Nominal do Caso de Uso (Default Pipeline):**
   - Execução de conjunto de teste onde as predições geradas coincidem com o gabarito $\rightarrow$ `accuracy == 1.0`, `is_perfect_match is True`;
   - Execução com casos onde `evaluation_case_id` é textualmente idêntico a `material.material_id`, confirmando que a igualdade de strings é aceita e que o use case não deriva valores;
   - Execução de conjunto com defeitos intencionais $\rightarrow$ relatório registra `mismatches` e acurácia parcial precisa;
   - Ordenação canônica determinística preservada no relatório independente da ordem da sequência de entrada.
3. **Validações Defensivas e Fail-Closed:**
   - Argumento `dataset` inválido $\rightarrow$ `TypeError`;
   - Argumento `cases` inválido (não-sequência, string, bytes) $\rightarrow$ `TypeError`;
   - Elementos em `cases` que não são `DecisionRecommendationBenchmarkCase` $\rightarrow$ `TypeError`;
   - `evaluation_case_id` duplicado na sequência de entrada $\rightarrow$ `ValueError`;
   - Incompatibilidade relacional: pipeline retorna predição cujo `material_id` diverge do `material.material_id` do caso $\rightarrow$ `ValueError`;
   - Pipeline customizado retorna objeto não-`DecisionRecommendation` $\rightarrow$ `TypeError`;
   - Casos faltantes em relação ao dataset $\rightarrow$ propagação fail-closed de `ValueError` emitido pelo evaluator;
   - Casos excedentes em relação ao dataset $\rightarrow$ propagação fail-closed de `ValueError` emitido pelo evaluator;
   - Divergência entre o `material_id` do caso e o `material_id` do gabarito $\rightarrow$ propagação fail-closed de `ValueError` emitido pelo evaluator.
4. **Tratamento de Dataset Vazio:**
   - Dataset vazio (`items == ()`) e lista vazia de casos `cases == ()` $\rightarrow$ retorna relatório com `total_cases == 0`, `accuracy is None` e `is_empty is True`.
5. **Injeção de Dependência:**
   - Suporte a pipeline customizado simulado via injeção de callable, comprovando desacoplamento;
   - Pipeline padrão utiliza deterministicamente o `DeterministicGovernanceValidator` integrado com `recommend_decision`.
6. **Exportação Pública Canônica:**
   - `DecisionRecommendationBenchmarkCase` e `RunDecisionRecommendationBenchmarkUseCase` devidamente expostos em `src/agent_lab/__init__.py` e `__all__`.

---

## 10. Gates de Qualidade

```powershell
python -m unittest discover -s tests -v
git diff --check
git status -sb
```

Critérios mínimos para aceitação:
- 100% dos testes aprovados (1015 + novos testes);
- Zero avisos de whitespace em `git diff --check`;
- Modificação restrita aos arquivos previstos;
- Nenhuma dependência externa introduzida (apenas Python 3.11 stdlib).

---

## 11. Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| **Inferência implícita de `evaluation_case_id` a partir de `material_id`** | Baixa | Alto | Mitigado pela exigência do contrato `DecisionRecommendationBenchmarkCase`, que exige o fornecimento explícito de ambas as identidades, permitindo igualdade textual sem inferência automática. |
| **Sobrescrita silenciosa de casos duplicados** | Baixa | Alto | Mitigado pela recusa de mapeamentos literais como entrada primária e validação fail-closed de unicidade sobre a sequência de casos. |
| **Duplicação de lógica do evaluator** | Baixa | Médio | Mitigado pela delegação estrita a `evaluate_decision_recommendations`, proibindo recálculo de acurácia no use case. |
| **Divergência entre predição e caso** | Média | Alto | Validação explícita de que `prediction.material_id == case.material.material_id` antes da montagem do mapeamento. |

---

## 12. Plano de Reversão

Por ser uma adição modular na camada de aplicação:
1. Reverter o merge commit do PR da Issue #141;
2. A exclusão de `src/agent_lab/decision_recommendation_benchmark_use_case.py` e de seus testes restaura imediatamente o baseline anterior de 1015 testes GREEN, sem qualquer impacto colateral no restante do laboratório.

---

## 13. Versionamento e Release

- **Impacto SemVer:** `MINOR` (adição puramente aditiva e retrocompatível na camada de aplicação);
- **Publicação:** Não há tag ou release vinculada diretamente a este ciclo individual (a release formal permanece `v0.1.0`);
- **Atualização do Compass:** A ser realizada no closeout documental após a integração funcional.

---

## 14. Critérios de Aceite (Acceptance Criteria)

- [ ] SPEC técnica aprovada e consolidada (`SPEC-0141`);
- [ ] Criação do módulo `src/agent_lab/decision_recommendation_benchmark_use_case.py`;
- [ ] Implementação de `DecisionRecommendationBenchmarkCase` imutável com `slots=True, frozen=True`;
- [ ] Implementação de `RunDecisionRecommendationBenchmarkUseCase` com suporte a injeção e pipeline padrão determinístico;
- [ ] Validações fail-closed para argumentos inválidos, casos duplicados e divergências de `material_id`;
- [ ] Delegação estrita da metrologia a `evaluate_decision_recommendations`;
- [ ] Preservação formal da independência semântica entre `evaluation_case_id` e `material_id`, com suporte comprovado a valores textuais coincidentes fornecidos explicitamente;
- [ ] Suporte determinístico a datasets vazios;
- [ ] Exportação pública em `src/agent_lab/__init__.py` e inclusão em `__all__`;
- [ ] Suíte completa de testes unitários e de integração aprovada;
- [ ] Suíte de regressão completa (1015 + novos testes) 100% GREEN;
- [ ] `git diff --check` limpo sem trailing whitespace.

---

## 15. Questões em Aberto

`Nenhuma`. A separação entre identidade experimental e identidade cadastral, o contrato tipado de caso de teste e a arquitetura de coordenação do pipeline foram integralmente delimitados e resolvidos.

---

## 16. Histórico de Decisões

| Data | Decisão | Motivo | Responsável |
|---|---|---|---|
| `2026-09-21` | Criação de `DecisionRecommendationBenchmarkCase` como contrato nominal primário | Evitar sobrescrita silenciosa de chaves inerente a literais de dicionário Python e formalizar a independência semântica entre `evaluation_case_id` e `material_id` sem inferências implícitas. | `Jk-Pascoal` |
| `2026-09-21` | Suporte a injeção de pipeline com default determinístico | Permitir execução imediata zero-configuração via `DeterministicGovernanceValidator` e `recommend_decision`, mantendo testabilidade desacoplada com mocks/fakes. | `Jk-Pascoal` |
| `2026-09-21` | Delegação compulsória a `evaluate_decision_recommendations` | Cumprir o princípio "Application coordena; Pipeline produz; Evaluator mede", impedindo duplicação de regras metrológicas no use case. | `Jk-Pascoal` |
| `2026-09-21` | Restrição do escopo da Issue #141 a `DecisionRecommendation` | Entregar a menor fatia vertical ponta a ponta testável sem expandir escopo para múltiplos domínios simultaneamente. | `Jk-Pascoal` |
