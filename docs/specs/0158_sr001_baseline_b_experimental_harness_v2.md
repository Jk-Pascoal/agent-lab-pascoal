# SPEC-0158-HARNESS-V2 — SR-001 Baseline B: Experimental Harness v2 Specification

> Especificação arquitetural, metrológica e metodológica do harness experimental sucessor (v2)
> para avaliação da qualidade semântica de materiais no âmbito da investigação SR-001 (Issue #158).

---

## Metadados

| Campo | Valor |
|---|---|
| **Identificador** | `SPEC-0158-HARNESS-V2` |
| **Status** | `PROPOSED` |
| **Issue relacionada** | `#158` |
| **Título da Issue** | `SR-001 — Scale Reconnaissance v1` |
| **Investigação experimental** | `SR-001 / Scale Reconnaissance v1` |
| **Pressão arquitetural** | `P-07 (Industrial Load / Scale Validation)` |
| **Branch documental** | `docs/issue-158-baseline-b-harness-v2-spec` |
| **Responsável** | `Jk-Pascoal` |
| **Data de criação** | `2026-09-30` |
| **Última atualização** | `2026-09-30` |
| **Domínio** | Metrologia Experimental / Governança de Catálogo PDM/BOM |
| **Camada arquitetural** | Metrologia Experimental e Harness Desacoplado |
| **Baseline de entrada** | `1194 testes aprovados` (100% GREEN via `unittest`) |
| **Impacto funcional** | `ZERO — investigação experimental sem impacto no Roadmap ou KPI da PoC v0.1.0` |
| **Runner oficial** | `python -m unittest discover -s tests -v` (Python 3.11) |

---

## 1. Contexto e Motivação Científica

### 1.1 Consolidação da Primeira Observação da Tranche 01 (PR #167 / PR #168)
A investigação experimental **SR-001 (Issue #158)** analisa o comportamento computacional e semântico da governança de catálogo antes de qualquer otimização estrutural.

Em 29/09/2026, executou-se a primeira observação histórica da Tranche 01 do Baseline B (amostra exploratória de 10 pares: 5 positivos e 5 *hard negatives*), cujos artefatos e evidências foram formalmente consolidados na `main` via PR #167 (merge `ee6cccb`) e reconciliados no `docs/PROJECT_COMPASS.md` via PR #168 (merge `781134f`). Os resultados observados foram:
- **Candidate Blocking:** reteve 5/5 positivos ($100\%$ de retenção positiva de candidatos) e 9/10 pares do *challenge set*;
- **Detector Heurístico (`is_possible_duplicate`):** identificou 5/5 positivos ($TP=5$), mas classificou incorretamente 4 de 5 *hard negatives* como duplicatas ($FP=4$), com apenas 1 verdadeiro negativo ($TN=1$ em `HN-UNT`) e zero falsos negativos ($FN=0$), resultando em Precision de $5/9 \approx 55.6\%$, Recall de $100\%$ e F1 de $0.7143$.

Essa primeira observação foi preservada em sua totalidade como fato histórico *observed-as-run* em `experiments/sr001_baseline_b_tranche_01.py` e `docs/experiments/SR-001_baseline_b_tranche_01_first_observation.md`.

### 1.2 Limitações de Instrumentação Identificadas no Harness v1
A auditoria técnica da execução pioneira revelou que o harness v1 possui limitações instrumentais que devem ser aprimoradas para avaliações futuras:
1. **Nomenclatura inadequada para Candidate Blocking:** uso de termos como `CANDIDATE_TP` e `CANDIDATE_FP`, confundindo filtragem combinatória com classificação semântica;
2. **Avaliação desacoplada e incondicional do detector:** o detector downstream foi invocado para todos os pares indiscriminadamente, sem estruturar a medição do pipeline condicional em dois estágios;
3. **Materialização ad-hoc das regras de blocking:** lógica combinatória implementada de forma dispersa no script;
4. **Acoplamento rígido à Tranche 01:** asserções estáticas amarradas a 20 materiais e 10 pares, impedindo reuso paramétrico para novas tranches auditadas.

### 1.3 As Três Emendas Epistemológicas Obrigatórias
Antes de qualquer especificação técnica, incorporam-se formalmente as seguintes premissas epistemológicas:

#### Emenda 1 — Separação Estrita de Evidências sobre Blocking
$$\mathbf{Redu\text{ç}\tilde{a}o\ Estrutural\ (Baseline\ A) \neq Preserva\text{ç}\tilde{a}o\ Sem\hat{a}ntica\ (Baseline\ B)}$$
Fica expressamente vedado o uso de formulações como *"blocking comprovado com alta retenção de positivos"*. É mandatório separar:
- A **redução estrutural/computacional do espaço de candidatos** observada no Baseline A ($\approx 99.09\%$ a $99.16\%$ no intervalo experimental $N \in \{250, \dots, 2000\}$), mensurada estritamente sobre cardinalidade combinatória;
- O **sinal exploratório pontual de retenção de positivos** observado na Tranche 01 ($5/5$ positivos retidos na amostra auditada de 10 pares).
*Nenhuma dessas evidências isoladas ou combinadas autoriza alegação de validade semântica industrial ou extrapolação para catálogos de 100k SKUs.*

#### Emenda 2 — Caracterização Comparativa vs. Imutabilidade da Primeira Observação
Qualquer futura execução da Tranche 01 sob o novo harness v2 **NÃO constitui e NÃO poderá ser chamada de reexecução** da primeira observação.
Trata-se formalmente de uma:
$$\mathbf{SUCCESSOR\text{-}HARNESS\ COMPARATIVE\ CHARACTERIZATION}$$
com novo timestamp UTC, novo hash de evidência, novo arquivo de saída e rastreabilidade segregada, preservando 100% intacta e sem sobrescrita a Primeira Observação *observed-as-run*.

#### Emenda 3 — Rigor na Justificativa Amostral de Tranches Subsequentes
Rejeita-se a formulação genérica de *"3 a 4 casos por classe taxonômica"*. Fixa-se a justificativa canônica:
> *"Volumes entre 30 e 40 pares permitem múltiplas observações por estrato industrial e por famílias críticas de perturbação, conforme matriz de alocação previamente definida, auditada humanamente e congelada criptograficamente."*

---

## 2. Relação com a SPEC-0158 e Documentos Fundacionais

A governança do laboratório preserva uma estrita distinção hierárquica entre a especificação metodológica e a especificação de software de instrumentação:

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ SPEC-0158 (docs/specs/0158_sr001_baseline_b_semantic_quality_pilot_v1.md)   │
│ -> Define a METODOLOGIA global do Baseline B:                               │
│    - Strict Material Identity Policy (identidade vs intercambialidade);     │
│    - Taxonomia de perturbações P (P-ABBR, etc.) e HN (HN-DIM, etc.);        │
│    - 5 Estratos industriais de desafio;                                     │
│    - Processo de curadoria, auditoria em 6 etapas e FREEZE criptográfico.   │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼ (Implementado instrumentalmente por)
┌─────────────────────────────────────────────────────────────────────────────┐
│ SPEC-0158-HARNESS-V2 (Este Documento)                                       │
│ -> Define a ENGENHARIA DE INSTRUMENTAÇÃO METROLÓGICA (Harness v2):          │
│    - Arquitetura de software experimental desacoplada em experiments/;      │
│    - Contratos e dataclasses de execução em memória;                        │
│    - Nomenclatura correta de retenção combinatória;                         │
│    - Metrologia segregada (Selection, Unconditioned, Conditioned, Pipeline);│
│    - Carga paramétrica e verificação dinâmica de integridade SHA-256.       │
└─────────────────────────────────────────────────────────────────────────────┘
```

A presente especificação não altera, não revoga e não flexibiliza nenhum princípio da SPEC-0158, atuando como seu instrumental executivo sucessor.

---

## 3. Princípio de Imutabilidade Histórica

1. **Harness v1 (`experiments/sr001_baseline_b_tranche_01.py`):**
   Permanece congelado como *observed-as-run*. Nenhuma linha de código, comentário ou identificador será modificado;
2. **Primeira Observação Histórica (`experiments/evidence/sr001_baseline_b_tranche_01_first_observation.json`):**
   Preserva-se com hash SHA-256 `ec2c509f60aa842a36a1cdc4462af46db6fbdc60573a18a8d38f6d3ec3105645`. Inviolável;
3. **Documento de Custódia (`docs/experiments/SR-001_baseline_b_tranche_01_first_observation.md`):**
   Preserva o registro fiel do *Process Deviation* e dos fatos observados em 29/09/2026;
4. **Artefatos FROZEN da Tranche 01:**
   `draft_tranche_01_catalog.csv` (`ba82fce...`), `draft_tranche_01_ground_truth.json` (`8eb6758...`) e `draft_tranche_01_manifest.json` (`686e983...`) permanecem intocados. Proíbe-se qualquer retificação de rótulos ou descrições para "adequar" os dados aos resultados.

---

## 4. Separação Quadripartite dos Domínios do Sistema

Para eliminar ambiguidades conceituais e garantir pureza metrológica, o harness v2 estrutura a execução em quatro camadas funcionais rigorosamente isoladas:

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. GROUND TRUTH REFERENCIAL (Fato Auditado sob Strict Material Identity)    │
│    is_duplicate: bool                                                       │
│    -> Fato cadastral imutável estabelecido por especialista humano.         │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 2. CANDIDATE SELECTION (Filtro Combinatório Experimental P-07)              │
│    is_candidate: bool | matched_families: tuple[str, ...]                   │
│    -> Decisão topológica de pré-filtragem para redução do espaço cartesiano │
│       de pares, baseada na união deduplicada das Famílias 1                 │
│       (PN/Fabricante) e 2 (Grupo/Categoria).                                │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ (Se is_candidate = True)
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 3. DETECTOR HEURÍSTICO DOWNSTREAM (duplicates.py de Produção)               │
│    is_possible_duplicate: bool                                              │
│    -> Hipótese diagnóstica do produto avaliada sobre o par retido.          │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 4. METROLOGIA E MÉTRICAS ESTRATIFICADAS (Harness Metrology Engine)          │
│    -> Computação isolada de métricas de Seleção, Detector Incondicional,    │
│       Detector Condicional e Pipeline Ponta a Ponta.                        │
└─────────────────────────────────────────────────────────────────────────────┘
```

Fica terminantemente estabelecido que:
$$\text{Ground Truth Fact} \neq \text{Candidate Selection Gate} \neq \text{Detector Heuristic Hypothesis}$$

---

## 5. Taxonomia Canônica e Nomenclatura de Decisão

### 5.1 Nomenclatura de Candidate Selection (Retenção vs. Descarte)
Fica formalmente banido o uso de `CANDIDATE_TP`, `CANDIDATE_FP`, `CANDIDATE_TN` e `CANDIDATE_FN`.

A confrontação entre o Ground Truth (`gt.is_duplicate`) e a decisão de Candidate Selection (`cand.is_candidate`) adota obrigatoriamente a seguinte matriz terminológica:

| Ground Truth (`is_dup`) | Candidate Selection (`is_cand`) | Nomenclatura Canônica | Significado Metrológico |
|:---:|:---:|:---|:---|
| `True` | `True` | **`POSITIVE_RETAINED`** | Duplicata verdadeira preservada no espaço de candidatos para análise posterior. |
| `True` | `False` | **`POSITIVE_DROPPED`** | **Falso Negativo Crítico de Seleção** (duplicata verdadeira descartada precocemente pelo blocking). |
| `False` | `True` | **`NEGATIVE_RETAINED`** | Par não-duplicado retido pelo blocking e submetido ao detector downstream. |
| `False` | `False` | **`NEGATIVE_DROPPED`** | Par não-duplicado podado com sucesso, reduzindo esforço computacional. |

### 5.2 Nomenclatura de Classificação do Detector Semântico
Os termos clássicos da matriz de confusão aplicam-se **exclusivamente** ao julgamento semântico do detector (`is_possible_duplicate`):
- **`TP` (Verdadeiro Positivo):** $is\_duplicate = \text{True} \land is\_possible\_duplicate = \text{True}$
- **`FP` (Falso Positivo):** $is\_duplicate = \text{False} \land is\_possible\_duplicate = \text{True}$
- **`TN` (Verdadeiro Negativo):** $is\_duplicate = \text{False} \land is\_possible\_duplicate = \text{False}$
- **`FN` (Falso Negativo):** $is\_duplicate = \text{True} \land is\_possible\_duplicate = \text{False}$

---

## 6. Métricas Metrológicas Segregadas

O harness v2 calculará e reportará quatro blocos independentes de métricas:

### 6.1 Bloco 1 — Métricas de Candidate Selection
Avaliam a capacidade do filtro combinatório de reter duplicatas verdadeiras:
1. **Candidate Pair Recall ($\text{Recall}_{\text{block}}$):**
   $$\text{Recall}_{\text{block}} = \frac{\text{POSITIVE\_RETAINED}}{\text{POSITIVE\_RETAINED} + \text{POSITIVE\_DROPPED}}$$
2. **Candidate Pair Miss Rate ($\text{MissRate}_{\text{block}}$):**
   $$\text{MissRate}_{\text{block}} = \frac{\text{POSITIVE\_DROPPED}}{\text{POSITIVE\_RETAINED} + \text{POSITIVE\_DROPPED}} = 1 - \text{Recall}_{\text{block}}$$
3. **Challenge-Set Retention Rate:**
   $$\text{RetentionRate}_{\text{challenge}} = \frac{\text{Pares Retidos (POSITIVE\_RETAINED + NEGATIVE\_RETAINED)}}{\text{Total de Pares no Challenge Set}}$$
4. **Challenge-Set Reduction Ratio:**
   $$\text{ReductionRatio}_{\text{challenge}} = 1 - \text{RetentionRate}_{\text{challenge}}$$
   *(Ressalva obrigatória: a taxa de redução na amostra de desafio não se confunde com o Reduction Ratio catalog-wide do Baseline A).*

### 6.2 Bloco 2 — Métricas do Detector Incondicional (Baseline Intrínseco)
Caracteriza a performance bruta do detector heurístico de produto (`is_possible_duplicate`) executado isoladamente sobre **todos** os pares do dataset de teste:
- $TP_{\text{uncond}}$, $FP_{\text{uncond}}$, $TN_{\text{uncond}}$, $FN_{\text{uncond}}$;
- $\text{Precision}_{\text{uncond}} = \frac{TP_{\text{uncond}}}{TP_{\text{uncond}} + FP_{\text{uncond}}}$;
- $\text{Recall}_{\text{uncond}} = \frac{TP_{\text{uncond}}}{TP_{\text{uncond}} + FN_{\text{uncond}}}$;
- $F1_{\text{uncond}} = \frac{2 \cdot \text{Precision}_{\text{uncond}} \cdot \text{Recall}_{\text{uncond}}}{\text{Precision}_{\text{uncond}} + \text{Recall}_{\text{uncond}}}$.

### 6.3 Bloco 3 — Métricas do Detector Condicionado aos Candidatos
Mede a eficácia do detector quando inserido no pipeline em dois estágios, avaliado **exclusivamente sobre os pares retidos pelo candidate blocking** ($is\_candidate = \text{True}$):
- $TP_{\text{cond}}$, $FP_{\text{cond}}$, $TN_{\text{cond}}$, $FN_{\text{cond}}$;
- $\text{Precision}_{\text{det}|\text{cand}} = \frac{TP_{\text{cond}}}{TP_{\text{cond}} + FP_{\text{cond}}}$;
- $\text{Recall}_{\text{det}|\text{cand}} = \frac{TP_{\text{cond}}}{TP_{\text{cond}} + FN_{\text{cond}}}$;
- $F1_{\text{det}|\text{cand}} = \frac{2 \cdot \text{Precision}_{\text{det}|\text{cand}} \cdot \text{Recall}_{\text{det}|\text{cand}}}{\text{Precision}_{\text{det}|\text{cand}} + \text{Recall}_{\text{det}|\text{cand}}}$.

### 6.4 Bloco 4 — Métricas End-to-End do Pipeline Ponta a Ponta
Mede o comportamento do sistema completo ($\text{Candidate Blocking} \rightarrow \text{Detector Downstream}$):
1. **Overall Pipeline Recall ($\text{Recall}_{\text{pipeline}}$):**
   $$\text{Recall}_{\text{pipeline}} = \text{Recall}_{\text{block}} \times \text{Recall}_{\text{det}|\text{cand}}$$
   *(Se o blocking descartar um positivo, $\text{Recall}_{\text{pipeline}}$ penaliza o sistema diretamente).*
2. **Plano Bidimensional Explícito:**
   Preserva-se a representação bidimensional sem fórmulas combinadas artificiais:
   $$(\text{Reduction Ratio}, \text{Overall Pipeline Recall})$$

---

## 7. Arquitetura e Contratos de Tipagem do Harness v2

O harness v2 será implementado no arquivo isolado `experiments/sr001_baseline_b_harness_v2.py`.

### 7.1 Tipos e Estruturas de Dados em Memória (Zero I/O)
```python
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

class CandidateSelectionOutcome(str, Enum):
    POSITIVE_RETAINED = "POSITIVE_RETAINED"
    POSITIVE_DROPPED = "POSITIVE_DROPPED"
    NEGATIVE_RETAINED = "NEGATIVE_RETAINED"
    NEGATIVE_DROPPED = "NEGATIVE_DROPPED"

class DetectorOutcome(str, Enum):
    TRUE_POSITIVE = "TP"
    FALSE_POSITIVE = "FP"
    TRUE_NEGATIVE = "TN"
    FALSE_NEGATIVE = "FN"

@dataclass(frozen=True, slots=True)
class CandidateSelectionDecision:
    is_candidate: bool
    matched_families: tuple[str, ...]  # ex.: ("FAMILY_1",) ou ("FAMILY_2",) ou ("FAMILY_1", "FAMILY_2")
    family_1_key: tuple[str, str] | None
    family_2_key: tuple[str, str] | None

@dataclass(frozen=True, slots=True)
class CaseObservationV2:
    evaluation_case_id: str
    stratum: str
    challenge_class: str
    material_id_a: str
    material_id_b: str
    ground_truth_is_duplicate: bool
    selection_decision: CandidateSelectionDecision
    selection_outcome: CandidateSelectionOutcome
    unconditioned_detector_prediction: bool
    unconditioned_detector_outcome: DetectorOutcome
    conditioned_detector_prediction: bool | None  # None se descartado pelo blocking
    conditioned_detector_outcome: DetectorOutcome | None

@dataclass(frozen=True, slots=True)
class TrancheDescriptor:
    tranche_id: str
    catalog_path: Path
    ground_truth_path: Path
    manifest_path: Path
    expected_catalog_sha256: str
    expected_ground_truth_sha256: str
    expected_manifest_sha256: str
    expected_material_count: int
    expected_pair_count: int
```

### 7.2 Lógica Pura de Candidate Blocking
A lógica combinatória de blocking experimental deve espelhar estritamente a união teórica definida no Baseline A e na Seção 6 da SPEC-0158:
- **Família 1 (PN/Fabricante):** $p_1(r) = (\text{norm}(pn), \text{norm}(mfg))$ se ambos não-vazios;
- **Família 2 (Grupo/Categoria):** $p_2(r) = (\text{norm}(group), cat\_tok)$ se $cat\_tok \neq ""$;
- **Decisão:** $is\_candidate(A, B) = True \iff (p_1(A) \neq None \land p_1(A) == p_1(B)) \lor (p_2(A) \neq None \land p_2(A) == p_2(B))$.

---

## 8. Validação Estrita de Hashes, Cardinalidades e Manifestos

1. **Leitura Normalizada em Bytes LF:**
   Todos os arquivos de texto (`.csv`, `.json`) devem ser lidos e verificados utilizando o hash SHA-256 dos bytes normalizados em LF (`replace(b"\r\n", b"\n")`), garantindo invariância cross-platform (Windows vs. Linux);
2. **Confrontação Dinâmica com o Manifesto:**
   O harness deve carregar o manifesto congelado (`manifest.json`), validar se os metadados de controle declaram `status == "DRAFT"`, `freeze_state == "FROZEN"`, e comparar os hashes calculados contra os hashes registrados no próprio manifesto;
3. **Validação de Integridade Referencial:**
   - Todo `material_id` presente no Ground Truth deve existir no Catálogo (falha com `AssertionError`);
   - Todo `evaluation_case_id` presente no Ground Truth deve possuir correspondência biunívoca ($1:1$) no manifesto.

---

## 9. Suporte Paramétrico a Múltiplas Tranches

Diferente do v1, o harness v2 aceitará parâmetros de execução via linha de comando ou invocação modular:
- **Modo Tranche Única:** Avaliação de uma tranche específica (ex.: `--tranche 01` ou `--tranche 02`);
- **Modo Agregado (Multi-Tranche):** Avaliação simultânea de todas as tranches auditadas e congeladas, computando:
  * Métricas consolidadas globais;
  * Estratificação por tranche;
  * Estratificação por estrato industrial;
  * Estratificação por classe taxonômica.

---

## 10. Política de Evidências, Versionamento e Checkpoints

1. **Imutabilidade e Não-Sobrescrita:**
   Cada execução do harness v2 gera um artefato de evidência nomeado com identificador único de execução:
   `experiments/checkpoints/sr001_baseline_b_eval_<tranche>_<run_id>.json`
2. **Registro de Proveniência Completo no Envelope:**
   O JSON de saída conterá obrigatoriamente:
   - Identificador do harness (`SR001-BASELINE-B-HARNESS-V2`);
   - Hash SHA-256 do próprio script do harness no momento da execução;
   - Hashes SHA-256 (LF) dos dados de entrada (catálogo, ground truth, manifesto);
   - Timestamp ISO 8601 em UTC (`timezone.utc`);
   - Breakdown completo por classe e estrato;
   - Inventário exaustivo de todos os casos onde ocorreu `POSITIVE_DROPPED` ou `FP`.

---

## 11. Determinismo, Tolerância a Falhas e Stop Conditions

### Stop Conditions Mandatórias:
A execução do harness v2 será interrompida imediatamente caso:
1. **Divergência de Hash:** Qualquer hash SHA-256 de arquivo de entrada divergir do esperado;
2. **Violação de Invariante de Dados:** Ausência de par, ID órfão ou inconsistência relacional;
3. **Não-Determinismo do Payload Científico:** Sob os mesmos artefatos de entrada, mesma versão/hash do harness e mesma configuração, duas execuções devem produzir resultados científicos idênticos — decisões de Candidate Selection, predições do detector, outcomes, contagens e métricas —, desconsiderando campos de proveniência necessariamente variáveis (como `run_id` e timestamp), sem exigir igualdade byte-a-byte dos arquivos de evidência;
4. **Violação do Baseline:** Qualquer arquivo em `src/agent_lab/` ou `tests/` for modificado durante o processo.

---

## 12. Limites Epistemológicos e Afirmações Vedadas

Permanecem ativas e inegociáveis as seguintes proibições epistemológicas:
1. **Vedado generalizar para 100k SKUs:** Nenhuma métrica obtida em tranches de dezenas de pares sustenta claims de performance ou precisão para catálogos industriais de 100k itens;
2. **Vedado afirmar "H3 confirmada":** A Hipótese H3 (variação do recall conforme perturbação) permanece sob investigação e não pode ser declarada confirmada sem evidência de variação sistemática do recall entre classes de perturbação, incluindo ocorrência de falsos negativos em positivos auditados;
3. **Vedado declarar "blocking estrutural validado no produto":** O blocking experimental mensura apenas uma hipótese topológica combinatória isolada em script experimental;
4. **Vedado equiparar retenção combinatória a recall semântico:** $\text{Candidate Retention} \neq \text{Semantic Recall}$.

---

## 13. Gates Humanos antes de Qualquer Execução

Nenhuma linha de código experimental será acionada sem o cumprimento cumulativo dos seguintes gates de governança:

- [ ] **Gate 1:** Revisão e aprovação formal desta especificação (`SPEC-0158-HARNESS-V2`) via PR documental integrada na `main`;
- [ ] **Gate 2:** Implementação do script segregado `experiments/sr001_baseline_b_harness_v2.py` em conformidade estrita com esta SPEC;
- [ ] **Gate 3:** Validação de formatação e baseline canônico via `git diff --check` e `python -m unittest discover -s tests -v` (1194/1194 GREEN);
- [ ] **Gate 4:** Emissão de decisão humana formal (*HUMAN GO*) em sessão dedicada para acionamento do runner experimental.

---

## 14. Explicitamente FORA DE ESCOPO

Ficam estrita e formalmente definidos como fora do escopo desta especificação:
1. **Código de Produção:** Nenhuma linha de código em `src/agent_lab/` será alterada;
2. **Testes de Produção:** Nenhuma linha em `tests/` será alterada (baseline 1194 GREEN mantido);
3. **Otimização do Detector:** Proibida qualquer alteração de regras ou pesos em `duplicates.py`;
4. **Implementação de Produto:** Proibida a introdução de `CandidatePairSelector` ou classes de blocking em `src/`;
5. **Geração da Tranche 02:** Proibida a criação de dados, materiais ou manifestos de Tranche 02 nesta etapa;
6. **Dataset Global de 200 Pares:** Permanece fora de escopo;
7. **Execução Experimental:** Proibida a execução de medições ou harnesses nesta fase documental.
