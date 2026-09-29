# SR-001 Baseline B — Tranche 01: Registro de Custódia da Primeira Observação

> Documento de custódia e registro histórico da primeira observação experimental
> da Tranche 01 do Baseline B (SR-001 / Issue #158), executada em 29/09/2026.

---

## Metadados da Execução

| Campo | Valor |
|---|---|
| **Investigação experimental** | `SR-001 / Scale Reconnaissance v1` (Pressão P-07) |
| **Componente avaliado** | `Baseline B — Tranche 01 (Qualidade Semântica)` |
| **Data e hora da execução** | `2026-09-29T14:06:37.888227+00:00` (~11:06 BRT) |
| **Branch da execução** | `experiment/issue-158-baseline-b-tranche-01-evaluation` |
| **Harness experimental utilizado** | `experiments/sr001_baseline_b_tranche_01.py` |
| **Arquivo de evidência original** | `experiments/checkpoints/sr001_baseline_b_tranche_01_evidence.json` |
| **Arquivo de evidência versionado** | `experiments/evidence/sr001_baseline_b_tranche_01_first_observation.json` |
| **SHA-256 da evidência (cópia exata)** | `ec2c509f60aa842a36a1cdc4462af46db6fbdc60573a18a8d38f6d3ec3105645` |
| **Tamanho da evidência** | `7.720 bytes` |
| **Tamanho da amostra avaliada** | `10 pares` (5 positivos e 5 hard negatives; 20 materiais) |
| **Status da observação** | `PRIMEIRA OBSERVAÇÃO CONGELADA — ZERO REEXECUÇÃO` |

---

## 1. Registro de Desvio de Processo (*Process Deviation*)

A primeira execução do harness experimental ocorreu na transição entre o planejamento e a auditoria antes da emissão formal do HUMAN GO final específico para acionamento do script.

Este fato é registrado formalmente como uma **Process Deviation** de governança de sessões, e não como uma invalidação dos dados:
- O harness operou em modo estritamente somente-leitura sobre os três arquivos imutáveis congelados;
- A primeira observação foi preservada exatamente como ocorreu, sem qualquer repetição, ajuste retroativo ou substituição;
- **Zero reexecuções foram realizadas.**

---

## 2. Cadeia de Custódia dos Artefatos FROZEN

A execução operou sobre os três arquivos canônicos da Tranche 01 integrados na `main` via PR #165, cujos hashes SHA-256 permaneceram rigorosamente intactos:

* **Catálogo (`experiments/baseline_b/draft_tranche_01_catalog.csv`):**  
  `ba82fce8903888255f8f9be0f97c7c2838b1f3d9733ef1a891aedbc6cf1be003`
* **Ground Truth (`experiments/baseline_b/draft_tranche_01_ground_truth.json`):**  
  `8eb6758ddcf68f3e4cf48ead8ad4a24c8adcf526983c72db1460a21ebe5249ef`
* **Manifesto (`experiments/baseline_b/draft_tranche_01_manifest.json`):**  
  `686e98328a47673f492301894faf0d265d48c782c53c51fc6f69fe1f5dc9468a`

---

## 3. Fatos Experimentais da Primeira Observação

### 3.1 Tabela de Casos Observados

| Case ID | Estrato | Classe | GT (`is_dup`) | Candidate (`is_cand`) | Detector (`is_pos_dup`) | Classificação |
|---|---|---|:---:|:---:|:---:|:---:|
| `CASE-SR001-B-T01-001` | `FASTENERS` | `P-ABBR` | `True` | `True` | `True` | **TP** |
| `CASE-SR001-B-T01-002` | `FASTENERS` | `HN-DIM` | `False` | `True` | `True` | **FP** |
| `CASE-SR001-B-T01-003` | `VALVES` | `P-WORD-ORDER` | `True` | `True` | `True` | **TP** |
| `CASE-SR001-B-T01-004` | `VALVES` | `HN-MAT` | `False` | `True` | `True` | **FP** |
| `CASE-SR001-B-T01-005` | `BEARINGS` | `P-PN-FORMAT` | `True` | `True` | `True` | **TP** |
| `CASE-SR001-B-T01-006` | `BEARINGS` | `HN-VAR` | `False` | `True` | `True` | **FP** |
| `CASE-SR001-B-T01-007` | `ELECTRICAL` | `P-UNIT-SYN` | `True` | `True` | `True` | **TP** |
| `CASE-SR001-B-T01-008` | `ELECTRICAL` | `HN-PN` | `False` | `True` | `True` | **FP** |
| `CASE-SR001-B-T01-009` | `GENERAL` | `P-NOISE` | `True` | `True` | `True` | **TP** |
| `CASE-SR001-B-T01-010` | `GENERAL` | `HN-UNT` | `False` | `False` | `False` | **TN** |

### 3.2 Métricas Consolidadas

* **Candidate Blocking:**
  - Positivos totais no Ground Truth: $5$
  - Positivos retidos pelo blocking: **$5/5 = 100.0\%$**
  - Positivos descartados pelo blocking: **$0/5 = 0.0\%$**
  - Pares retidos no Challenge Set: $9/10$
* **Detector Heurístico (`is_possible_duplicate`):**
  - Verdadeiros Positivos (TP): **$5$**
  - Falsos Positivos (FP): **$4$**
  - Verdadeiros Negativos (TN): **$1$**
  - Falsos Negativos (FN): **$0$**
  - **Precision:** **$5 / (5 + 4) = 5/9 \approx 55.6\%$**
  - **Recall:** **$5 / (5 + 0) = 5/5 = 100.0\%$**
  - **F1-Score:** **$0.7143$**

---

## 4. Interpretação Canônica dos Resultados

1. **A Tranche 01 NÃO confirma a Hipótese H3 em relação à variação de recall:**  
   O recall observado sobre os cinco positivos foi de $5/5$ ($100\%$). A evidência desta tranche exploratória não demonstra perda de recall para as cinco perturbações positivas testadas.
2. **Vulnerabilidade severa de precision/discriminação observada:**  
   O detector apresentou **$4/5$ ($80\%$) de Falsos Positivos** sobre os hard negatives. A regra heurística ingênua baseada em `shared_numbers >= 2` falhou ao distinguir materiais com alta sobreposição numérica nas seguintes classes:
   - `HN-DIM` (dimensões divergentes M10x30 vs M10x40);
   - `HN-MAT` (metalurgia divergente ASTM A216 WCB vs ASTM A351 CF8M);
   - `HN-VAR` (vedação divergente 2RS1 contato vs 2Z blindagem);
   - `HN-PN` (modelo divergente O5D100 tempo de trânsito vs O5D150 supressão de fundo).
3. **Único hard negative corretamente discriminado:**  
   Apenas `HN-UNT` (peça avulsa `ELEMENTO` vs conjunto `KIT`) resultou em Verdadeiro Negativo (TN), pois os category tokens diferiram, retirando o par tanto do bloco de candidatos quanto da rota lexical do detector.
4. **Candidate Blocking pontual:**  
   Nenhum dos cinco positivos congelados foi descartado pelo blocking nesta amostra ($5/5$).
5. **Limites Formais de Generalização:**  
   É expressamente vedado generalizar os resultados desta tranche de 10 casos para:
   - A população industrial geral;
   - O conjunto piloto global de 200 pares;
   - Catálogos de 100k SKUs;
   - Recall ou precision operacional de produção.
6. **Afirmações Vedadas:**
   - NÃO declarar: *"H3 confirmada"*;
   - NÃO declarar: *"ausência de circularidade comprovada"*;
   - NÃO declarar: *"blocking estrutural validado"*.

---

## 5. Limitações Conhecidas do Harness (Observed-as-Run)

O harness `experiments/sr001_baseline_b_tranche_01.py` é preservado exatamente no estado em que executou a primeira observação (*observed-as-run*), com as seguintes limitações documentadas:
1. **Materialização Local do Blocking:** A função de blocking foi implementada localmente no harness porque o produto não expõe uma API pública canônica `is_candidate_pair(a, b)`. A semântica foi derivada das definições combinatórias do Baseline A e da Seção 6 da SPEC-0158.
2. **Nomenclatura Interna de Blocking:** O código utiliza os rótulos `CANDIDATE_TP`, `CANDIDATE_FP`, `CANDIDATE_TN` e `CANDIDATE_FN`. Reconhece-se que a semântica mais adequada seria `POSITIVE_RETAINED`, `POSITIVE_DROPPED`, `NEGATIVE_RETAINED` e `NEGATIVE_DROPPED`.
3. **Proibição de Ajuste Retroativo:** O código NÃO será editado nesta versão para preservar a correspondência histórica estrita com a primeira observação. Qualquer eventual aprimoramento de nomenclatura ou arquitetura deverá ser realizado em versão sucessora segregada.
