# SR-001 Baseline B — Tranche 01: Registro de Custódia da Caracterização Sucessora (Harness v2)

> Documento de custódia e registro histórico da primeira Successor-Harness Comparative Characterization
> da Tranche 01 do Baseline B (SR-001 / Issue #158), executada em 02/10/2026 via Gate 4 autorizado.

---

## Metadados da Execução

| Campo | Valor |
|---|---|
| **Investigação experimental** | `SR-001 / Scale Reconnaissance v1` (Pressão Arquitetural P-07) |
| **Componente avaliado** | `Baseline B — Tranche 01 (Qualidade Semântica)` |
| **Classificação formal** | `SUCCESSOR-HARNESS COMPARATIVE CHARACTERIZATION` |
| **Data e hora da execução (UTC)** | `2026-10-02T12:15:01.992095+00:00` (~09:15 BRT) |
| **Run ID** | `RUN-T01-20261002T121501Z-36C8BA8A` |
| **Harness experimental utilizado** | `experiments/sr001_baseline_b_harness_v2.py` (v2 integrado) |
| **SHA-256 do Harness v2 (LF)** | `cfcee60f0049d7d3709d5c5a6c1d34c2a28dcfc75c1d5d6801a57a445dc18f9f` |
| **Mecanismo de acionamento** | Invocação modular efêmera autorizada via Gate 4 (zero edits em código) |
| **Arquivo de checkpoint original** | `experiments/checkpoints/sr001_baseline_b_eval_01_RUN-T01-20261002T121501Z-36C8BA8A.json` |
| **Protocolo de persistência** | Resiliente atômico **H-034** (`.tmp` $\rightarrow$ `flush()` $\rightarrow$ `fsync()` $\rightarrow$ `os.replace()`) |
| **Arquivo de evidência versionado** | `experiments/evidence/sr001_baseline_b_tranche_01_successor_harness_v2_characterization.json` |
| **SHA-256 da evidência (cópia exata LF)** | `f77d5f542c6e1bfd213142075d9fb8c4320ac345de995531a142d57c01c0ef29` |
| **Tamanho da evidência** | `20.050 bytes` (cópia byte-a-byte idêntica) |
| **Amostra avaliada** | `10 pares` (5 positivos e 5 hard negatives; 20 materiais congelados) |
| **Relação com a Observation #1** | **Não substitui, não reproduz retroativamente e não reexecuta.** A primeira observação v1 (`ec2c509...`) permanece imutável e preservada *observed-as-run*. |
| **Decisão Humana Pós-Execução** | **`PLAN T02`** (planejamento futuro de nova tranche independente) |

---

## 1. Cadeia de Custódia dos Artefatos FROZEN

A caracterização operou em modo estritamente somente-leitura sobre os três arquivos imutáveis da Tranche 01 congelada:

* **Catálogo (`experiments/baseline_b/draft_tranche_01_catalog.csv`):**  
  `ba82fce8903888255f8f9be0f97c7c2838b1f3d9733ef1a891aedbc6cf1be003` (20 materiais cadastrais únicos);
* **Ground Truth (`experiments/baseline_b/draft_tranche_01_ground_truth.json`):**  
  `8eb6758ddcf68f3e4cf48ead8ad4a24c8adcf526983c72db1460a21ebe5249ef` (10 pares auditados: 5P / 5HN);
* **Manifesto (`experiments/baseline_b/draft_tranche_01_manifest.json`):**  
  `686e98328a47673f492301894faf0d265d48c782c53c51fc6f69fe1f5dc9468a` (10 casos em correspondência biunívoca 1:1, `status == "DRAFT"`, `freeze_state == "FROZEN"`).

---

## 2. Fatos Experimentais da Caracterização Sucessora

### 2.1 Tabela de Casos Observados (Segregação Quadripartite)

| Case ID | Estrato | Classe | GT (`is_dup`) | Candidate Selection (`is_cand`) | Outcome Seleção | Unconditioned Detector | Conditioned Detector |
|---|---|---|:---:|:---:|:---:|:---:|:---:|
| `CASE-SR001-B-T01-001` | `FASTENERS` | `P-ABBR` | `True` | `True` (Fam 2) | **`POSITIVE_RETAINED`** | `TP` | `TP` |
| `CASE-SR001-B-T01-002` | `FASTENERS` | `HN-DIM` | `False` | `True` (Fam 2) | **`NEGATIVE_RETAINED`** | **`FP`** | **`FP`** |
| `CASE-SR001-B-T01-003` | `VALVES` | `P-WORD-ORDER` | `True` | `True` (Fam 2) | **`POSITIVE_RETAINED`** | `TP` | `TP` |
| `CASE-SR001-B-T01-004` | `VALVES` | `HN-MAT` | `False` | `True` (Fam 2) | **`NEGATIVE_RETAINED`** | **`FP`** | **`FP`** |
| `CASE-SR001-B-T01-005` | `BEARINGS` | `P-PN-FORMAT` | `True` | `True` (Fam 2) | **`POSITIVE_RETAINED`** | `TP` | `TP` |
| `CASE-SR001-B-T01-006` | `BEARINGS` | `HN-VAR` | `False` | `True` (Fam 2) | **`NEGATIVE_RETAINED`** | **`FP`** | **`FP`** |
| `CASE-SR001-B-T01-007` | `ELECTRICAL` | `P-UNIT-SYN` | `True` | `True` (Fam 2) | **`POSITIVE_RETAINED`** | `TP` | `TP` |
| `CASE-SR001-B-T01-008` | `ELECTRICAL` | `HN-PN` | `False` | `True` (Fam 2) | **`NEGATIVE_RETAINED`** | **`FP`** | **`FP`** |
| `CASE-SR001-B-T01-009` | `GENERAL` | `P-NOISE` | `True` | `True` (Fam 2) | **`POSITIVE_RETAINED`** | `TP` | `TP` |
| `CASE-SR001-B-T01-010` | `GENERAL` | `HN-UNT` | `False` | `False` | **`NEGATIVE_DROPPED`** | **`TN`** | *N/A (podado)* |

---

## 3. Métricas Metrológicas Segregadas

### 3.1 Bloco 1 — Candidate Selection (Filtro Combinatório Experimental)
* Positivos no Ground Truth: **$5$**
* Duplicatas preservadas (**`POSITIVE_RETAINED`**): **$5$**
* Falsos negativos de seleção (**`POSITIVE_DROPPED`**): **$0$**
* Não-duplicatas retidas (**`NEGATIVE_RETAINED`**): **$4$**
* Não-duplicatas podadas (**`NEGATIVE_DROPPED`**): **$1$**
* **Candidate Pair Recall ($\text{Recall}_{\text{block}}$):** **$5/5 = 100.0\%$**
* **Candidate Pair Miss Rate:** **$0.0\%$**
* **Challenge-Set Retention Rate:** **$9/10 = 90.0\%$**
* **Challenge-Set Reduction Ratio:** **$1/10 = 10.0\%$**  
  *(Ressalva canônica obrigatória: a taxa de redução na amostra de desafio de 10 pares não se confunde com o Reduction Ratio de ~99.1% catalog-wide apurado no Baseline A).*

### 3.2 Bloco 2 — Detector Incondicional (Baseline Intrínseco sobre Todos os Pares)
* Verdadeiros Positivos ($TP$): **$5$**
* Falsos Positivos ($FP$): **$4$**
* Verdadeiros Negativos ($TN$): **$1$** (`HN-UNT`)
* Falsos Negativos ($FN$): **$0$**
* **Precision:** **$5 / (5 + 4) = 5/9 \approx 55.6\%$** ($0.5556$)
* **Recall:** **$5 / (5 + 0) = 5/5 = 100.0\%$** ($1.0000$)
* **F1-Score:** **$0.7143$**

### 3.3 Bloco 3 — Detector Condicionado aos Candidatos (Pares Retidos pelo Blocking)
* Pares submetidos ao detector: **$9$ pares** ($is\_candidate = \text{True}$)
* Verdadeiros Positivos ($TP$): **$5$**
* Falsos Positivos ($FP$): **$4$**
* Verdadeiros Negativos ($TN$): **$0$** (o par `HN-UNT` foi descartado no blocking prévio)
* Falsos Negativos ($FN$): **$0$**
* **Precision ($\text{Precision}_{\text{det}|\text{cand}}$):** **$5/9 \approx 55.6\%$**
* **Recall ($\text{Recall}_{\text{det}|\text{cand}}$):** **$5/5 = 100.0\%$**
* **F1-Score ($\text{F1}_{\text{det}|\text{cand}}$):** **$0.7143$**

### 3.4 Bloco 4 — Pipeline End-to-End (Blocking $\rightarrow$ Detector)
* **Overall Pipeline Recall ($\text{Recall}_{\text{pipeline}}$):** **$100.0\%$** ($1.0 \times 1.0 = 1.0$)
* **Challenge-Set Reduction Ratio:** **$10.0\%$**
* **Ponto Bidimensional $(\text{Reduction Ratio}, \text{Overall Pipeline Recall})$:** **$(0.1000, 1.0000)$**

---

## 4. Inventário Crítico (`POSITIVE_DROPPED` ou `FP`)

Total de casos no inventário crítico: **4 casos** (zero positivos perdidos pelo blocking; 4 falsos positivos semânticos):

1. **`CASE-SR001-B-T01-002` (`FASTENERS` / `HN-DIM`):** M10x30 vs M10x40. Retido pelo blocking (`FAMILY_2`); detector declarou duplicata por sobreposição de tokens e números (`FP`).
2. **`CASE-SR001-B-T01-004` (`VALVES` / `HN-MAT`):** ASTM A216 WCB vs ASTM A351 CF8M. Retido pelo blocking (`FAMILY_2`); detector declarou duplicata por tolerância lexical (`FP`).
3. **`CASE-SR001-B-T01-006` (`BEARINGS` / `HN-VAR`):** Vedação 2RS1 contato vs blindagem 2Z. Retido pelo blocking (`FAMILY_2`); detector declarou duplicata ignorando sufixos técnicos (`FP`).
4. **`CASE-SR001-B-T01-008` (`ELECTRICAL` / `HN-PN`):** Sensor óptico O5D100 vs O5D150. Retido pelo blocking (`FAMILY_2`); detector declarou duplicata por part number prefix-match (`FP`).

*Casos `POSITIVE_DROPPED`:* **Zero.**

---

## 5. Interpretação Canônica e Limites Epistemológicos

### Formulação Canônica Permitida:
> *"Na Tranche 01 congelada, contendo 5 positivos e 5 hard negatives, nenhum positivo foi perdido pelo Candidate Selection ou pelo detector downstream. Quatro dos cinco hard negatives foram classificados como duplicatas, indicando vulnerabilidade exploratória de precision/discriminação frente a variações dimensionais, metalúrgicas, sufixos de vedação e famílias correlatas de part number."*

### Interpretações Expressamente Vedadas:
* **NÃO** generalizar o recall para a população industrial ou para o catálogo de 100k SKUs;
* **NÃO** afirmar "H3 confirmada" (o recall dos positivos observados foi 100%, sem perda observada na amostra $n=5$ positivos);
* **NÃO** converter redução estrutural combinatória em alegação de preservação semântica;
* **NÃO** declarar o blocking como "validado no produto" (o blocking permanece hipótese exploratória desacoplada do código de produção);
* **NÃO** promover qualquer resultado desta caracterização a KPI ou meta do projeto.

---

## 6. Próxima Âncora: Deliberação PLAN T02

A decisão humana registrada para esta sessão é **`PLAN T02`**.
Isso estabelece que o próximo passo racional da investigação experimental será o **planejamento de uma nova tranche independente (Tranche 02)** com maior poder observacional (30 a 40 pares) e estratificação representativa, sob autorização humana específica.

Nenhum arquivo de Tranche 02 foi criado ou iniciado nesta sessão.
