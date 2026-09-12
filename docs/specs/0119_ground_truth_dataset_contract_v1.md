# SPEC-0119 — Ground Truth Dataset Contract v1

> Especificação técnica dos contratos de dados puros, imutáveis e em memória para coleções
> estruturadas, tipadas e determinísticas de verdade de referência (Ground Truth Datasets) no Agent Lab Pascoal.

---

## Metadados

| Campo | Valor |
|---|---|
| **Identificador** | `SPEC-0119` |
| **Status** | `PROPOSED` |
| **Issue relacionada** | `#119` |
| **Título da Issue** | `Ground Truth Dataset Contract v1` |
| **Branch funcional** | `feature/issue-119-ground-truth-dataset-contract` |
| **Responsável** | `Jk-Pascoal` |
| **Data de criação** | `2026-09-12` |
| **Última atualização** | `2026-09-12` |
| **Baseline de entrada** | `720 testes aprovados` (100% GREEN) |
| **Runner oficial** | `python -m unittest discover -s tests -v` (Python 3.11) |

---

## 1. Contexto

Na Issue #115 (SPEC-0115), o Agent Lab Pascoal inaugurou formalmente a frente evolutiva **"Ground truth e benchmark"**, introduzindo no módulo `src/agent_lab/ground_truth.py` os contratos atômicos de dados puros em memória para a representação de verdade de referência rotulada e auditável:
1. `MaterialRuleGroundTruth` (conformidade cadastral de material individual);
2. `DuplicatePairGroundTruth` (equivalência relacional de par não-direcional de materiais);
3. `DecisionRecommendationGroundTruth` (recomendação algorítmica esperada de governança);
4. `LabelProvenance` (enum de proveniência com curadoria de especialista ou especificação sintética).

A integração da Issue #115 elevou o baseline do repositório para **720 testes aprovados** (100% GREEN).

Com os contratos atômicos consolidados e validados na branch `main`, a etapa seguinte da frente de metrologia consiste em definir como essas instâncias individuais de gabarito são organizadas e agrupadas para fins de avaliação sistemática: os **Datasets de Ground Truth**.

### Diretriz de Preservação e Isolamento da Metrologia Legada
Assim como deliberado na Issue #115, a metrologia embrionária legada presente em `src/agent_lab/data_io.py` (`LabeledMaterial`) e `src/agent_lab/baseline.py` (`evaluate_baseline`, `BaselineReport`) **NÃO** deve ser alterada, removida ou adaptada nesta Issue. Os novos contratos de dataset constituem a fundação canônica formal em memória, sem qualquer acoplamento com o código legado.

---

## 2. Problema, evidências e impacto

### Problema
Atualmente, o sistema dispõe de contratos rigorosos para instâncias atômicas de ground truth, mas carece de um contrato formal, tipado e imutável para representar **conjuntos (datasets)** de avaliação.

Sem contratos formais de dataset:
1. Conjuntos amostrais de benchmark tenderiam a ser agregados como tuplas ou listas Python genéricas (`tuple[Any, ...]`), desprovidas de validação de homogeneidade tipada;
2. Inexistência de uma identidade canônica estável para o dataset (`dataset_id`), inviabilizando a rastreabilidade da referência amostral utilizada em um experimento;
3. Não há garantias formais contra gabaritos duplicados ou concorrentes para um mesmo caso de teste dentro de um mesmo dataset de avaliação;
4. Não há ordenação canônica determinística garantida sobre a coleção, permitindo variações arbitrárias de iteração dependentes da ordem em que os elementos foram empilhados;
5. Corre-se o risco de desenvolvedores acoplarem prematuramente estruturas de dados de dataset com mecanismos de I/O (CSV, JSONL, Parquet) ou com runners de cálculo de métricas.

### Evidências
1. No módulo `src/agent_lab/ground_truth.py`, existem exclusivamente classes para itens individuais (`MaterialRuleGroundTruth`, `DuplicatePairGroundTruth`, `DecisionRecommendationGroundTruth`);
2. Inexiste qualquer tipo formal no domínio que represente uma coleção validada de gabaritos com identidade própria;
3. Na ausência deste contrato, testes de benchmark futuros precisariam recorrer a coleções heterogêneas soltas ou reescrever validações defensivas ad-hoc em cada ponto de consumo.

### Impacto
- Risco de inconsistência e não-reprodutibilidade metodológica em benchmarks futuros;
- Risco de contaminação estatística por duplicidades inadvertidas de casos experimentais dentro do mesmo experimento;
- Impossibilidade de referenciar formalmente um dataset por identificador canônico estável;
- Degradação da integridade arquitetural do subsistema de metrologia.

---

## 3. Objetivo

Introduzir contratos de dados puros em memória (`frozen=True, slots=True`, zero I/O) no subsistema de Ground Truth do Agent Lab Pascoal para representar coleções estruturadas, homogêneas, tipadas, imutáveis e deterministicamente ordenadas de gabaritos:
1. `MaterialRuleGroundTruthDataset` — coleção tipada de `MaterialRuleGroundTruth`;
2. `DuplicatePairGroundTruthDataset` — coleção tipada de `DuplicatePairGroundTruth`;
3. `DecisionRecommendationGroundTruthDataset` — coleção tipada de `DecisionRecommendationGroundTruth`.

---

## 4. Semântica de Dataset e Decisões Explícitas v1

### 4.1 Semântica de Dataset no Agent Lab Pascoal
No Agent Lab Pascoal, um **Ground Truth Dataset** é uma coleção tipada, imutável e homogênea de verdades de referência atômicas estabelecidas para uma unidade estatística específica de avaliação.

O dataset possui uma identidade canônica própria (`dataset_id`) e preserva uma sequência canônica determinística de itens (`items`).

### 4.2 Três Datasets Tipados
Para preservar a segregação estrita das unidades estatísticas estabelecidas na SPEC-0115:
- **`MaterialRuleGroundTruthDataset`**: agrupa exclusivamente gabaritos de regras cadastrais de materiais (`MaterialRuleGroundTruth`);
- **`DuplicatePairGroundTruthDataset`**: agrupa exclusivamente gabaritos de pares relacionais de duplicidade (`DuplicatePairGroundTruth`);
- **`DecisionRecommendationGroundTruthDataset`**: agrupa exclusivamente gabaritos de recomendações algorítmicas de governança (`DecisionRecommendationGroundTruth`).

Não são permitidos datasets mistos ou heterogêneos. Cada classe de dataset valida fail-closed que todos os elementos contidos pertencem ao tipo canônico correspondente.

### 4.3 Campos Mínimos Canônicos
Cada dataset é composto exclusivamente por dois campos:
- **`dataset_id: str`**: identificador canônico textual não-vazio do dataset (ex.: `"DS-MAT-RULES-V1"`, `"DS-DUP-PAIRS-2026-09"`);
- **`items: tuple[GroundTruth, ...]`**: tupla imutável contendo zero ou mais instâncias do respectivo contrato atômico.

### 4.4 Unicidade de `ground_truth_id`
Dentro de um dataset, cada elemento deve possuir um `ground_truth_id` estritamente único. A tentativa de instanciar um dataset contendo dois ou mais itens com o mesmo `ground_truth_id` (após normalização) resulta obrigatoriamente em `ValueError`.

### 4.5 Unicidade de `evaluation_case_id` como Decisão Explícita e Nova de v1
> [!IMPORTANT]
> **DECISÃO EXPLÍCITA V1:**
> A exigência de que cada item em um dataset possua um `evaluation_case_id` único é uma **regra NOVA e deliberada** do Dataset Contract v1. Ela **NÃO** é uma consequência automática da SPEC-0115.

*Justificativa epistemológica e metodológica:*
Na SPEC-0115, `evaluation_case_id` foi definido como a identidade da amostra experimental, enquanto `ground_truth_id` é a identidade do rótulo produzido. Em termos puramente teóricos, um mesmo caso de teste poderia receber múltiplos rótulos por diferentes avaliadores ou fontes.
Contudo, no **Dataset Contract v1**, a semântica operacional é a de representar **um único gabarito canônico por caso experimental** dentro de cada conjunto tipado de benchmark.
Cenários complexos como consenso multi-anotador, quóruns de painel deliberativo (`CONSENSUS_PANEL`) ou histórico de adjudicações concorrentes continuam expressamente fora de escopo e poderão exigir novas abstrações de dataset em evoluções futuras.
Portanto, no v1:
- Se houver dois ou mais itens com o mesmo `evaluation_case_id` dentro do mesmo dataset, o contrato falha imediatamente com `ValueError`.

### 4.6 Dataset Vazio Permitido (`items == ()`) e Separação `Dataset != Metric`
> [!NOTE]
> **DECISÃO SOBRE DATASET VAZIO:**
> O contrato de dataset v1 permite explicitamente coleções vazias (`items == ()`).

*Justificativa arquitetural:*
**`Dataset != Metric`**.
Um dataset é uma estrutura de dados de domínio puramente declarativa. Uma coleção vazia de gabaritos é estruturalmente válida e coerente como modelo de dados (análoga a uma tabela vazia ou uma tupla vazia de `expected_issue_types == ()` em `MaterialRuleGroundTruth`).
A restrição de que uma avaliação requer amostras ($N \ge 1$) para o cálculo estatístico de *precision*, *recall*, *F1* ou matriz de confusão pertence exclusivamente à camada futura de cálculo de métricas ou ao runner de benchmark. Rejeitar dataset vazio no nível de dados misturaria indevidamente a definição da estrutura com a execução do cálculo.

### 4.7 Ordenação Canônica Determinística
Para eliminar qualquer dependência de ordem na criação do dataset e garantir representação determinística independente da ordem de entrada:
- A tupla `items` fornecida pelo chamador é deterministicamente ordenada pela tupla de chave canônica:
  `(item.evaluation_case_id, item.ground_truth_id)`.
- Entradas válidas contendo itens fornecidos fora de ordem devem ser aceitas e normalizadas para a representação canônica ordenada.
- Como `evaluation_case_id` já é único em v1, a chave composta `(item.evaluation_case_id, item.ground_truth_id)` estabelece uma regra canônica completa, robusta e inequívoca.

### 4.8 Imutabilidade e Pureza em Memória
- Todos os datasets utilizam `@dataclass(frozen=True, slots=True)`;
- Tentativa de mutação pós-instanciação levanta `FrozenInstanceError`;
- O campo `items` é armazenado internamente como `tuple`;
- Nenhuma operação de I/O em disco, rede ou banco de dados ocorre durante a instanciação e validação dos datasets.

---

## 5. Escopo

### Incluído
- Definição das dataclasses imutáveis:
  - `MaterialRuleGroundTruthDataset`
  - `DuplicatePairGroundTruthDataset`
  - `DecisionRecommendationGroundTruthDataset`
- Validação estrita de tipos com `TypeError` inequívoco:
  - `dataset_id` deve ser obrigatoriamente `str`;
  - `items` deve ser obrigatoriamente `tuple`;
  - cada item em `items` deve ser estritamente do tipo correspondente (`MaterialRuleGroundTruth`, `DuplicatePairGroundTruth` ou `DecisionRecommendationGroundTruth`);
- Validação estrutural com `ValueError` inequívoco:
  - `dataset_id` não pode ser vazio ou composto unicamente por whitespace;
  - `ground_truth_id` não pode ser duplicado entre itens do dataset;
  - `evaluation_case_id` não pode ser duplicado entre itens do dataset;
- Normalização de `dataset_id` com `.strip()`;
- Ordenação canônica determinística interna de `items` por `(evaluation_case_id, ground_truth_id)`;
- Suporte a dataset vazio (`items == ()`);
- Exportação canônica pública dos novos contratos em `src/agent_lab/__init__.py`;
- Suíte de testes unitários defensivos cobrindo o modelo nominal, tipos inválidos, duplicidades, ordenação e imutabilidade;
- Preservação integral do baseline de 720 testes GREEN.

### Fora de escopo (Out of Scope)
Explicitamente **NÃO** incluir no v1:
- Metadados acessórios não essenciais: `name`, `description`, `created_at`, `version`;
- Métodos auxiliares de conveniência ou lookups: `find_by_case_id()`, `find_by_ground_truth_id()`, índices secundários ou dicionários internos;
- Sobrescrita de `__getitem__`, fatiamento (`slices`), operadores de conjunto (`union`, `difference`);
- Filtros, particionamento amostral, validação cruzada ou divisão de dados (`splits` treino/teste/validação);
- Loaders, parsers ou serializadores de arquivo: CSV, JSONL, Parquet, Excel ou SQLite;
- Persistência e operações de I/O em disco ou rede;
- Cálculo matemático de métricas: *precision*, *recall*, *F1*, *accuracy*, matriz de confusão ou custos ponderados;
- Thresholds de similaridade ou runners de benchmark;
- Binding de predições de runtime com ground truth (`prediction binding`);
- Alteração, adaptação ou migração da metrologia legada (`data_io.py`, `baseline.py`);
- Alteração dos contratos individuais integrados na Issue #115 (`MaterialRuleGroundTruth`, `DuplicatePairGroundTruth`, `DecisionRecommendationGroundTruth`, `LabelProvenance`).

---

## 6. Responsabilidade humana e limites do agente

No Agent Lab Pascoal, a IA recomenda, o especialista humano decide, a auditoria preserva o percurso e o lifecycle preserva o estado operacional.

No contexto de Datasets de Ground Truth:
1. **Datasets de referência são estruturas declarativas estáticas:** Os datasets definem o conjunto canônico sobre o qual modelos e pipelines serão submetidos a teste. Eles não produzem julgamento, não computam performance e não alteram o estado operacional de workflows de governança;
2. **Independência epistemológica:** O agrupamento de amostras em datasets de avaliação não contamina os critérios de conformidade cadastral e não confere autorização para desativar a governança humana de materiais em produção;
3. **Preservação de `requires_human_decision = True`:** O pipeline governado sob teste de benchmark continua submetido à compulsoriedade da decisão humana.

---

## 7. Requisitos

### Requisitos Funcionais
- `RF-01` — Definir a dataclass imutável `MaterialRuleGroundTruthDataset(frozen=True, slots=True)` contendo os campos `dataset_id: str` e `items: tuple[MaterialRuleGroundTruth, ...]`.
- `RF-02` — Definir a dataclass imutável `DuplicatePairGroundTruthDataset(frozen=True, slots=True)` contendo os campos `dataset_id: str` e `items: tuple[DuplicatePairGroundTruth, ...]`.
- `RF-03` — Definir a dataclass imutável `DecisionRecommendationGroundTruthDataset(frozen=True, slots=True)` contendo os campos `dataset_id: str` e `items: tuple[DecisionRecommendationGroundTruth, ...]`.
- `RF-04` — Nos três contratos, validar que `dataset_id` seja obrigatoriamente do tipo `str` (rejeitando outros tipos com `TypeError`), rejeitar strings vazias ou compostas unicamente por whitespace com `ValueError`, e normalizar internamente com `.strip()`.
- `RF-05` — Nos três contratos, validar que `items` seja obrigatoriamente uma instância de `tuple` (rejeitando outros contêineres como `list` ou `set` com `TypeError`).
- `RF-06` — Nos três contratos, validar que cada item contido em `items` seja estritamente uma instância da classe de ground truth esperada pelo dataset, rejeitando elementos heterogêneos ou de tipo incorreto com `TypeError`.
- `RF-07` — Nos três contratos, permitir formalmente a tupla vazia `items == ()`.
- `RF-08` — Nos três contratos, rejeitar com `ValueError` a presença de itens que possuam o mesmo `ground_truth_id` dentro do dataset.
- `RF-09` — Nos três contratos, rejeitar com `ValueError` a presença de itens que possuam o mesmo `evaluation_case_id` dentro do dataset v1 (decisão explícita de v1: um gabarito canônico por caso experimental).
- `RF-10` — Nos três contratos, ordenar deterministicamente os itens internos pela tupla de chave composta `(item.evaluation_case_id, item.ground_truth_id)`, aceitando itens válidos fornecidos fora de ordem e garantindo representação canônica armazenada ordenada.
- `RF-11` — Exportar publicamente `MaterialRuleGroundTruthDataset`, `DuplicatePairGroundTruthDataset` e `DecisionRecommendationGroundTruthDataset` no módulo raiz `src/agent_lab/__init__.py`.

### Requisitos de Qualidade e Integridade (Política Inequívoca de Exceções)
- `RQ-01` — **Imutabilidade estrita:** Todos os datasets devem ser congelados com `frozen=True` e `slots=True`, impedindo qualquer mutação de atributos pós-instanciação (`FrozenInstanceError`).
- `RQ-02` — **Política Inequívoca de Exceções:**
  - **`TypeError`:** lançado exclusivamente para violações de tipo nos argumentos fornecidos:
    - `dataset_id` não sendo `str`;
    - `items` não sendo `tuple`;
    - qualquer elemento em `items` que não seja uma instância da respectiva classe atômica esperada.
  - **`ValueError`:** lançado exclusivamente para violações estruturais e semânticas de integridade:
    - `dataset_id` vazio ou composto unicamente por whitespace;
    - colisão de `ground_truth_id` entre itens do dataset;
    - colisão de `evaluation_case_id` entre itens do dataset.
  Nenhuma formulação ambígua do tipo `TypeError/ValueError` é permitida.
- `RQ-03` — **Pureza em memória (Zero I/O):** Nenhuma operação de I/O em disco, rede ou banco de dados deve ocorrer durante a instanciação e validação dos datasets.
- `RQ-04` — **Isolamento de regressão:** O baseline existente de 720 testes deve permanecer 100% GREEN sem qualquer alteração comportamental.

---

## 8. Proposta técnica

### Visão geral dos contratos
Os contratos residem no subsistema de Ground Truth (`src/agent_lab/ground_truth.py`), complementando as definições atômicas da Issue #115:

```python
@dataclass(frozen=True, slots=True)
class MaterialRuleGroundTruthDataset:
    """Coleção tipada, imutável e determinística de gabaritos de regras cadastrais."""

    dataset_id: str
    items: tuple[MaterialRuleGroundTruth, ...]

    def __post_init__(self) -> None:
        ...


@dataclass(frozen=True, slots=True)
class DuplicatePairGroundTruthDataset:
    """Coleção tipada, imutável e determinística de gabaritos de pares duplicados."""

    dataset_id: str
    items: tuple[DuplicatePairGroundTruth, ...]

    def __post_init__(self) -> None:
        ...


@dataclass(frozen=True, slots=True)
class DecisionRecommendationGroundTruthDataset:
    """Coleção tipada, imutável e determinística de gabaritos de recomendação de governança."""

    dataset_id: str
    items: tuple[DecisionRecommendationGroundTruth, ...]

    def __post_init__(self) -> None:
        ...
```

### Arquivos previstos
- `src/agent_lab/ground_truth.py` — extensão do módulo contendo os 3 novos contratos de dataset;
- `src/agent_lab/__init__.py` — exportação pública canônica dos 3 novos símbolos e atualização de `__all__`;
- `tests/test_ground_truth.py` — bateria de testes unitários defensivos exercitando as novas classes e suas invariantes;
- `docs/specs/0119_ground_truth_dataset_contract_v1.md` — esta especificação técnica.

---

## 9. Estratégia de testes e micro-TDD

A implementação futura seguirá rigorosamente o micro-TDD do Agent Lab Pascoal:

### Vermelho (RED)
1. Elaborar testes unitários em `tests/test_ground_truth.py` cobrindo o comportamento esperado dos 3 datasets antes da implementação;
2. Executar o teste e comprovar falha por ausência das classes (`ImportError` / `AttributeError`).

### Verde (GREEN)
1. Implementar os contratos em `src/agent_lab/ground_truth.py` com dataclasses congeladas, validações fail-closed e normalização determinística;
2. Exportar os novos símbolos em `src/agent_lab/__init__.py`;
3. Executar o teste específico até aprovação de 100% dos novos casos.

### Regressão
Executar a suíte canônica completa:
```powershell
python -m unittest discover -s tests -v
```
Garantir que os 720 testes preexistentes permaneçam GREEN, totalizando `720 + N` testes aprovados.

### Cenários de teste previstos
1. **Casos Nominais Válidos:**
   - Criação de dataset com múltiplos itens válidos;
   - Criação de dataset vazio (`items == ()`) para cada um dos 3 tipos;
   - Sanitização de `dataset_id` com espaços laterais (`.strip()`);
   - Normalização determinística de itens fornecidos fora de ordem canônica `(evaluation_case_id, ground_truth_id)`.
2. **Violações de Tipo (`TypeError`):**
   - `dataset_id` não-string (ex.: inteiro, lista, `None`);
   - `items` fornecido como lista (`list`), conjunto (`set`) ou gerador;
   - `items` contendo elementos de tipo incompatível (ex.: strings, dicionários, tipo de ground truth trocado);
   - Mistura de tipos entre os datasets (ex.: `DuplicatePairGroundTruth` em `MaterialRuleGroundTruthDataset`).
3. **Violações Estruturais e de Integridade (`ValueError`):**
   - `dataset_id` vazio (`""`) ou composto apenas por whitespace (`"   "`);
   - Duplicidade de `ground_truth_id` dentro do dataset;
   - Duplicidade de `evaluation_case_id` dentro do dataset (regra v1 de um gabarito por caso).
4. **Imutabilidade:**
   - Tentativa de alteração de atributos em instâncias de dataset gerando `FrozenInstanceError`.

---

## 10. Gates de qualidade

Antes da submissão de Pull Request futuro:

```powershell
python -m unittest discover -s tests -v
git diff --check
git status -sb
```

Critérios de aprovação:
- Suíte completa 100% GREEN (sem skips e sem warnings anômalos);
- `git diff --check` sem nenhum erro de formatação ou trailing whitespace;
- Nenhuma modificação em arquivos não-autorizados (`data_io.py`, `baseline.py`, `rules.py`, `duplicates.py`, `decision.py`, `PROJECT_COMPASS.md`, SPEC 0115).

---

## 11. Riscos epistemológicos e estatísticos

| Risco ou limitação | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| **Contaminação cruzada de tipos** | Média | Alto | Tipagem nominal estrita com `isinstance` validando cada elemento de `items` fail-closed com `TypeError`. |
| **Gabaritos concorrentes ambíguos** | Média | Alto | Regra explícita de v1 exigindo `evaluation_case_id` único no dataset, barrando ambiguidade com `ValueError`. |
| **Não-determinismo de iteração** | Média | Médio | Ordenação canônica compulsória em `__post_init__` por `(evaluation_case_id, ground_truth_id)`. |
| **Acoplamento prematuro com I/O** | Baixa | Alto | Blindagem com contratos puros em memória, zero I/O, zero serializadores nesta etapa. |
| **Confusão entre Dataset e Métrica** | Baixa | Médio | Separação mandatória `Dataset != Metric`, permitindo coleção vazia como contrato estruturalmente íntegro. |

---

## 12. Plano de reversão

Por se tratar de um incremento puramente aditivo em módulo isolado:
1. Reverter os commits na branch funcional ou reverter o PR de integração na `main`;
2. A remoção das 3 classes e seus respectivos testes restabelece de imediato o baseline de 720 testes GREEN.

---

## 13. Versionamento e release

### Impacto SemVer
- Candidato a `MINOR`, a ser consolidado no fechamento de release.

### Publicação prevista
- Versão planejada: `Unreleased`;
- Criação de tag: Não;
- Atualização do `PROJECT_COMPASS.md`: Apenas no closeout documental após a integração e merge do PR.

---

## 14. Critérios de aceite (Acceptance Criteria)

- [ ] Issue #119 criada no GitHub e vinculada a esta SPEC;
- [ ] Branch funcional dedicada `feature/issue-119-ground-truth-dataset-contract` criada a partir da `main`;
- [ ] Especificação técnica `SPEC-0119` documentada e aprovada prévia à implementação;
- [ ] Classes `MaterialRuleGroundTruthDataset`, `DuplicatePairGroundTruthDataset` e `DecisionRecommendationGroundTruthDataset` implementadas com `frozen=True, slots=True`;
- [ ] Sanitização defensiva de `dataset_id` com `.strip()` e rejeição de strings vazias ou whitespace (`ValueError`);
- [ ] Validação estrita de tipos com `TypeError` para `dataset_id`, contêiner `items` e cada elemento individual de `items`;
- [ ] Suporte a datasets vazios (`items == ()`) validado;
- [ ] Verificação de unicidade de `ground_truth_id` dentro do dataset com `ValueError`;
- [ ] Verificação de unicidade de `evaluation_case_id` dentro do dataset com `ValueError` (decisão v1);
- [ ] Ordenação determinística de `items` por `(evaluation_case_id, ground_truth_id)` validada;
- [ ] Imutabilidade estrita pós-instanciação comprovada com `FrozenInstanceError`;
- [ ] Exportação pública canônica dos 3 novos contratos em `src/agent_lab/__init__.py`;
- [ ] Bateria de testes unitários defensivos implementada em `tests/test_ground_truth.py`;
- [ ] Baseline de 720 testes mantido 100% GREEN (totalizando 720 + N testes);
- [ ] `git diff --check` aprovado sem trailing whitespace;
- [ ] Nenhum arquivo fora do escopo funcional modificado.

---

## 15. Questões em aberto

- `Nenhuma`. A proposta mínima, decisões de unicidade de caso experimental e permissão de dataset vazio foram sanadas e aprovadas no Architectural Alignment de 12/09/2026.

---

## 16. Histórico de decisões

| Data | Decisão | Motivo | Responsável |
|---|---|---|---|
| `2026-09-12` | Aprovação do Architectural Alignment para Ground Truth Dataset Contract v1 | Estruturar formalmente a agregação de gabaritos em coleções tipadas para a frente de metrologia. | `Jk-Pascoal` |
| `2026-09-12` | Decisão explícita v1: unicidade de `evaluation_case_id` dentro do dataset | Garantir exatamente um gabarito canônico por caso experimental em v1, deixando modelos multi-anotador para evoluções futuras. | `Jk-Pascoal` |
| `2026-09-12` | Decisão sobre dataset vazio: permitir `items == ()` no contrato v1 | Princípio `Dataset != Metric`: coleção vazia é estruturalmente válida; rejeição por falta de amostras cabe à camada estatística. | `Jk-Pascoal` |
| `2026-09-12` | Ordenação determinística compulsória por `(evaluation_case_id, ground_truth_id)` | Eliminar variação arbitrária na iteração e garantir representação determinística independente da ordem de entrada. | `Jk-Pascoal` |
| `2026-09-12` | Exclusão estrita de loaders, I/O, métricas e lookups em v1 | Preservar a pureza de dados em memória e evitar acoplamento prematuro. | `Jk-Pascoal` |
