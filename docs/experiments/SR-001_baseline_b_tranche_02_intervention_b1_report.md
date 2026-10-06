# SR-001 Baseline B — Tranche 02: Registro de Custódia da Intervenção Experimental B1 (PN Conflict Probe)

> **Documento de Custódia e Registro Científico de Execução Experimental**  
> Avaliação controlada e segregada da intervenção contrafactual **B1** (*Structured Part-Number Disagreement / PN Conflict*) sobre o challenge set histórico fixo da Tranche 02 congelada (`SR-001 / Issue #158`).  
> **Classificação Formal:** `B1 ISOLADO — VALID EXPERIMENT / SAFETY GOAL FAILED / NOT ELIGIBLE FOR PRODUCTION`  
> **Data de Execução:** `2026-10-06`  
> **Alterações em Código de Produção:** Nenhuma (`src/agent_lab/` 100% intocado)  
> **Alterações em Testes de Produção:** Nenhuma (`tests/` 100% intocado)  
> **Alterações em Dados Congelados:** Nenhuma (Catálogo, Ground Truth e Manifesto 100% intocados)  

---

## Metadados da Execução

| Campo | Valor |
|---|---|
| **Investigação Experimental** | `SR-001 / Scale Reconnaissance v1` (Pressão Arquitetural P-07) |
| **Componente Avaliado** | `Baseline B — Tranche 02: Intervenção B1 Isolada (Dimensão B)` |
| **Status Científico Formal** | `VALID EXPERIMENT / SAFETY GOAL FAILED / NOT ELIGIBLE FOR PRODUCTION` |
| **Data e Hora da Execução (UTC)** | `2026-10-06T12:55:00+00:00` |
| **Git HEAD de Execução** | `33c8de9d9cebf037ab33dfb191d813a89a03a3c4` |
| **Branch Dedicada** | `agent/issue-158-sr001-b1-pn-conflict-probe` |
| **Run ID** | `RUN-B1-T02-20261006T125500Z-7E4A10B1` |
| **Módulo Experimental Utilizado** | [`experiments/sr001_b1_pn_conflict_probe.py`](../../experiments/sr001_b1_pn_conflict_probe.py) |
| **Arquivo de Evidência Científica** | [`experiments/evidence/sr001_baseline_b_tranche_02_intervention_b1.json`](../../experiments/evidence/sr001_baseline_b_tranche_02_intervention_b1.json) |
| **Amostra Avaliada** | `40 pares` (20 positivos e 20 hard negatives; 80 materiais sintéticos industriais) |

---

## 1. Cadeia de Custódia dos Artefatos FROZEN da Tranche 02

A execução consumiu de forma estritamente somente-leitura (*read-only*) os três arquivos congelados da Tranche 02:

* **Catálogo (`experiments/baseline_b/draft_tranche_02_catalog.csv`):**  
  SHA-256 LF: `74e1389f66fd14155dba1b3be9b16ef2ef9fe79b04e16232d2c2fb142e1c218b` (80 materiais sintéticos industriais);
* **Ground Truth (`experiments/baseline_b/draft_tranche_02_ground_truth.json`):**  
  SHA-256 LF: `052bd6fec3f165cea9cdbf686cb961af4eccf962f4689d938a00fdc459b92008` (40 pares auditados: 20P / 20HN);
* **Manifesto (`experiments/baseline_b/draft_tranche_02_manifest.json`):**  
  SHA-256 LF: `cab0732e83594111522e5edfd8c4bc1ff310c4be2df0b1d4c282b40a4f48a88b` (40 casos em correspondência 1:1, `freeze_state == "FROZEN"`).

---

## 2. Invariantes Epistemológicos e Governança Científica

```text
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                             INVARIANTES EPISTEMOLÓGICOS CENTRAIS                            │
├─────────────────────────────────────────────────────────────────────────────────────────────┤
│  1. ORIGINAL T02 OBSERVATION (HISTÓRICA)  ≠  INTERVENTION EXPERIMENT (CONTROLES A / B)      │
│  2. POST-HOC SENSITIVITY PROBE            ≠  INDEPENDENT VALIDATION  ≠  GENERALIZATION EV.  │
│  3. CANDIDATE CONFLICTING SIGNAL          ≠  APPROVED PRODUCTION VETO POLICY                │
│  4. GROUND TRUTH DEFINITION               ≠  DETECTOR IMPLEMENTATION                        │
│  5. CANONICAL PRODUCT REPOSITORY (src/)   ≠  ISOLATED EXPERIMENTAL HARNESS (experiments/)   │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

1. **Preservação Histórica:** A primeira observação cega (`RUN-T02-20261003T130713Z-5D78EB04`) permanece imutável como fato histórico documentado em [`SR-001_baseline_b_tranche_02_first_observation.md`](SR-001_baseline_b_tranche_02_first_observation.md).
2. **Segregação Estrita de Escopo:** B1 é um experimento contrafactual e **NÃO** constitui regra de produção. Zero linhas em `src/agent_lab/` foram alteradas.
3. **Isolamento Dimensional:** B1 foi executado sem qualquer composição com B2, B3, B4 ou B5, sem flexibilização de Candidate Selection (zero A1), sem avanço para T03 e sem calibração ou tuning exploratório.

---

## 3. Prova Rigorosa de Controle B0 (Reprodução Histórica T02)

Antes de avaliar os efeitos de B1, o módulo experimental comprovou a reprodução exata dos dados da T02 original:

### 3.1 Prova Par-a-Par nos 40/40 Casos Reais
Para todos os 40 pares reais do catálogo congelado:
$$\text{direct\_prediction} = \text{is\_possible\_duplicate}(A, B)$$
$$(\text{reconstructed\_prediction}, \text{reconstructed\_route}) = \text{detect\_original\_decision}(A, B)$$
$$\text{direct\_prediction} \equiv \text{reconstructed\_prediction} \equiv \text{obs.prediction\_original} \quad (\mathbf{100.0\% \text{ de concordância em 40/40 pares}})$$

### 3.2 Matrizes de Confusão do Controle B0

* **Avaliação Incondicional (40 pares):**
  * $\text{TP} = 19$, $\text{FP} = 17$, $\text{TN} = 3$, $\text{FN} = 1$
  * $\text{Precision} = 19/36 \approx 52.78\%$ ($0.5277777778$)
  * $\text{Recall} = 19/20 = 95.00\%$ ($0.9500000000$)
  * $\text{F1} \approx 0.6786$ ($0.6785714286$)

* **Avaliação Condicionada (39 candidatos retidos pelo filtro de bloqueio):**
  * $\text{TP} = 19$, $\text{FP} = 17$, $\text{TN} = 3$, $\text{FN} = 0$
  * $\text{Precision} = 52.78\%$, $\text{Recall} = 100.00\%$, $\text{F1} \approx 0.6909$

A divergência entre B0 e a observação histórica foi rigorosamente igual a **zero**.

---

## 4. Definição Operacional da Intervenção B1

A intervenção B1 atua estritamente como um sinal inibidor negativo contrafactual aplicado exclusivamente sobre predições positivas provenientes da **Rota 2**:

$$\text{pn\_conflict}(A, B) \iff \text{norm\_pn}(A) \ne \text{""} \;\land\; \text{norm\_pn}(B) \ne \text{""} \;\land\; \text{norm\_pn}(A) \ne \text{norm\_pn}(B)$$

$$\text{prediction}_{B1} = \begin{cases} 
\text{False}, & \text{se } \text{prediction}_{\text{orig}} = \text{True} \;\land\; \text{route}_{\text{orig}} = \text{ROUTE\_2} \;\land\; \text{pn\_conflict}(A, B) = \text{True} \\
\text{prediction}_{\text{orig}}, & \text{caso contrário.}
\end{cases}$$

* **Normalização Reutilizada:** Utiliza estritamente `normalize_text()` canônica do produto.
* **Rota 1 Intocada:** Decisões positivas da Rota 1 permanecem inalteradas.
* **Predições Negativas Intocadas:** Pares originalmente negativos não sofrem interferência.

---

## 5. Fatos Experimentais da Execução B1

### 5.1 Matriz Comparativa de Resultados (B0 vs B1)

| Métrica Metrológica | Controle B0 (T02) | Intervenção B1 Isolada | Variação Absoluta ($\Delta$) | Efeito Observado no Challenge Set T02 |
|---|:---:|:---:|:---:|---|
| **True Positives (TP)** | $19$ | $12$ | $-7$ | **7 duplicatas verdadeiras sacrificadas** |
| **False Positives (FP)** | $17$ | $0$ | $-17$ | **17 falsos positivos suprimidos** |
| **True Negatives (TN)** | $3$ | $20$ | $+17$ | $100\%$ dos hard negatives rejeitados |
| **False Negatives (FN)** | $1$ | $8$ | $+7$ | Aumento de falsos descartes pelo detector |
| **Precision (Incondicional)** | $52.78\%$ | $100.00\%$ | $+47.22\ \text{p.p.}$ | Eliminação de alarmes falsos |
| **Recall (Incondicional)** | $95.00\%$ | $60.00\%$ | $-35.00\ \text{p.p.}$ | **Degradação crítica da cobertura** |
| **F1-Score (Incondicional)** | $0.6786$ | $0.7500$ | $+0.0714$ | Trade-off dominado pela precisão |
| **Recall Condicionado** | $100.00\%$ | $63.16\%$ | $-36.84\ \text{p.p.}$ | Perda de cobertura downstream |

### 5.2 Caracterização dos Pares Conflitantes

* **Total de pares com `pn_conflict == True`:** **$27$ pares** (de 40).
* **Distribuição dos conflitos frente ao baseline B0:**
  * $17$ eram Falsos Positivos no B0 ($100\%$ convertidos em Verdadeiros Negativos);
  * $7$ eram Verdadeiros Positivos no B0 ($100\%$ convertidos em Falsos Negativos);
  * $3$ eram Verdadeiros Negativos no B0 (permaneceram Verdadeiros Negativos: `CASE-021`, `CASE-022`, `CASE-040`);
  * $0$ eram Falsos Negativos no B0.
* **Total de decisões alteradas pela sonda:** **$24$ decisões**.

---

## 6. Inventário Exaustivo das 24 Decisões Alteradas

| Evaluation Case ID | Estrato | Classe | GT | Rota B0 | PN Normalizado A | PN Normalizado B | B0 | B1 | Natureza da Decisão Alterada |
|---|---|---|:---:|:---:|---|---|:---:|:---:|---|
| `CASE-SR001-B-T02-001` | `FASTENERS` | `P-SEPARATOR` | `True` | `ROUTE_2` | `DIN 912 M12X45 12 9` | `DIN912M1245129` | `TP` | `FN` | **Sacrifício Colateral (TP $\rightarrow$ FN)** |
| `CASE-SR001-B-T02-005` | `FASTENERS` | `HN-DIM` | `False` | `ROUTE_2` | `931 12 060` | `931 12 070` | `FP` | `TN` | Supressão de Falso Positivo |
| `CASE-SR001-B-T02-006` | `FASTENERS` | `HN-MAT` | `False` | `ROUTE_2` | `933 08 025 88` | `933 08 025 A4` | `FP` | `TN` | Supressão de Falso Positivo |
| `CASE-SR001-B-T02-007` | `FASTENERS` | `HN-VAR` | `False` | `ROUTE_2` | `975 M20 STD` | `976 M20 FINO` | `FP` | `TN` | Supressão de Falso Positivo |
| `CASE-SR001-B-T02-008` | `FASTENERS` | `HN-DISTINCT` | `False` | `ROUTE_2` | `AD 616` | `AK 616` | `FP` | `TN` | Supressão de Falso Positivo |
| `CASE-SR001-B-T02-009` | `VALVES` | `P-PN-STRUCTURAL`| `True` | `ROUTE_2` | `LCC800 015` | `SPIRAX LCC 800 15` | `TP` | `FN` | **Sacrifício Colateral (TP $\rightarrow$ FN)** |
| `CASE-SR001-B-T02-010` | `VALVES` | `P-SEPARATOR` | `True` | `ROUTE_2` | `GL 150 WCB 050` | `GL150WCB050` | `TP` | `FN` | **Sacrifício Colateral (TP $\rightarrow$ FN)** |
| `CASE-SR001-B-T02-013` | `VALVES` | `HN-DIM` | `False` | `ROUTE_2` | `GT 150 WCB 080` | `GT 150 WCB 100` | `FP` | `TN` | Supressão de Falso Positivo |
| `CASE-SR001-B-T02-014` | `VALVES` | `HN-MAT` | `False` | `ROUTE_2` | `FIG12 CI 050` | `FIG16 CS 050` | `FP` | `TN` | Supressão de Falso Positivo |
| `CASE-SR001-B-T02-015` | `VALVES` | `HN-VAR` | `False` | `ROUTE_2` | `F150 FB 050` | `F150 RB 050` | `FP` | `TN` | Supressão de Falso Positivo |
| `CASE-SR001-B-T02-016` | `VALVES` | `HN-DISTINCT` | `False` | `ROUTE_2` | `TD52 015` | `FT14 015` | `FP` | `TN` | Supressão de Falso Positivo |
| `CASE-SR001-B-T02-017` | `BEARINGS` | `P-PN-STRUCTURAL`| `True` | `ROUTE_2` | `22212 E` | `SKF 22212E` | `TP` | `FN` | **Sacrifício Colateral (TP $\rightarrow$ FN)** |
| `CASE-SR001-B-T02-018` | `BEARINGS` | `P-SEPARATOR` | `True` | `ROUTE_2` | `32008 X` | `32008X` | `TP` | `FN` | **Sacrifício Colateral (TP $\rightarrow$ FN)** |
| `CASE-SR001-B-T02-023` | `BEARINGS` | `HN-VAR` | `False` | `ROUTE_2` | `22214 E` | `22214 EK` | `FP` | `TN` | Supressão de Falso Positivo |
| `CASE-SR001-B-T02-024` | `BEARINGS` | `HN-DISTINCT` | `False` | `ROUTE_2` | `H 311` | `AHX 311` | `FP` | `TN` | Supressão de Falso Positivo |
| `CASE-SR001-B-T02-025` | `ELECTRICAL`| `P-PN-STRUCTURAL`| `True` | `ROUTE_2` | `3RV2011 4BA10` | `SIEMENS 3RV20114BA10` | `TP` | `FN` | **Sacrifício Colateral (TP $\rightarrow$ FN)** |
| `CASE-SR001-B-T02-026` | `ELECTRICAL`| `P-SEPARATOR` | `True` | `ROUTE_2` | `LRD 3353` | `LRD3353` | `TP` | `FN` | **Sacrifício Colateral (TP $\rightarrow$ FN)** |
| `CASE-SR001-B-T02-029` | `ELECTRICAL`| `HN-DIM` | `False` | `ROUTE_2` | `AFUMEX 16 AZ` | `AFUMEX 25 AZ` | `FP` | `TN` | Supressão de Falso Positivo |
| `CASE-SR001-B-T02-030` | `ELECTRICAL`| `HN-MAT` | `False` | `ROUTE_2` | `NBR5597 1POL GF` | `NBR5597 1POL AL` | `FP` | `TN` | Supressão de Falso Positivo |
| `CASE-SR001-B-T02-031` | `ELECTRICAL`| `HN-VAR` | `False` | `ROUTE_2` | `PSS24 W 5` | `PSS24 W 5 EX` | `FP` | `TN` | Supressão de Falso Positivo |
| `CASE-SR001-B-T02-032` | `ELECTRICAL`| `HN-DISTINCT` | `False` | `ROUTE_2` | `060G1113` | `060G1115` | `FP` | `TN` | Supressão de Falso Positivo |
| `CASE-SR001-B-T02-037` | `GENERAL` | `HN-DIM` | `False` | `ROUTE_2` | `B60` | `B62` | `FP` | `TN` | Supressão de Falso Positivo |
| `CASE-SR001-B-T02-038` | `GENERAL` | `HN-MAT` | `False` | `ROUTE_2` | `DKB 0400 NBR` | `DKB 0400 TPU` | `FP` | `TN` | Supressão de Falso Positivo |
| `CASE-SR001-B-T02-039` | `GENERAL` | `HN-VAR` | `False` | `ROUTE_2` | `913 CG 3 150` | `913 CGI 3 150` | `FP` | `TN` | Supressão de Falso Positivo |

---

## 7. Desempenho por Modo de Falha Empírico (FM-1 a FM-4)

$$\text{Taxa de Supressão de FP} = \frac{\text{FP}_{\text{suprimidos}}}{\text{FP}_{\text{total}}}$$

* **FM-1: Divergência Dimensional (`HN-DIM`):** $4/4$ FPs suprimidos ($100.0\%$).
* **FM-2: Divergência de Materialidade (`HN-MAT`):** $4/4$ FPs suprimidos ($100.0\%$).
* **FM-3: Variante Construtiva / Montagem (`HN-VAR`):** $5/5$ FPs suprimidos ($100.0\%$).
* **FM-4: Subtipo / Princípio Físico (`HN-DISTINCT`):** $4/4$ FPs suprimidos ($100.0\%$).
* **Total Geral:** **$17/17$ FPs suprimidos** ($\mathbf{100.0\%}$).

---

## 8. Avaliação da Meta de Segurança e Conclusão Epistemológica

### 8.1 Avaliação Metrológica da Meta de Segurança
* **Meta de Segurança Canônica:** $\Delta\text{Recall}_P = \text{Recall}_P(B_0) - \text{Recall}_P(B_1) = 0$.
* **Valor Observado:** $\Delta\text{Recall}_P = 0.95 - 0.60 = \mathbf{+0.35}\ (35.00\ \text{pontos percentuais})$.
* **Status Formal:** **SAFETY GOAL FAILED**.

### 8.2 Deliberação Epistemológica e Causal

1. **Evidência Observada:**  
   A aplicação de uma regra de veto contrafactual baseada estritamente na desigualdade de part numbers normalizados por `normalize_text` (`norm_pn(A) != norm_pn(B)`) eliminou todos os falsos positivos da Rota 2 no challenge set T02, mas causou um sacrifício massivo e inaceitável de duplicatas reais (7 de 19 TPs sacrificados, queda de 35,00 pontos percentuais no Recall incondicional (95% → 60%)).
2. **Insuficiência Operacional:**  
   O experimento demonstra conclusivamente que **a desigualdade textual após `normalize_text` é insuficiente para distinguir conflito substantivo de part number de variação superficial de formatação ou prefixos**.
3. **Casos Vulneráveis Identificados:**  
   O sacrifício concentrou-se integralmente em:
   * `P-SEPARATOR` (4 casos: `CASE-001`, `CASE-010`, `CASE-018`, `CASE-026`): part numbers idênticos sob o ponto de vista de engenharia, porém com espaços ou delimitadores variados que `normalize_text` não equaliza entre blocos alfanuméricos contíguos (ex.: `DIN912M1245129` vs `DIN 912 M12X45 12 9`);
   * `P-PN-STRUCTURAL` (3 casos: `CASE-009`, `CASE-017`, `CASE-025`): part numbers que incorporam o nome do fabricante como prefixo ou variação estrutural de catálogo (ex.: `SKF 22212E` vs `22212 E`).
4. **Delimitação Epistemológica Rigorosa:**  
   Não se afirma e não se alega que um subsistema específico de normalização de part number seja condição necessária já comprovada para a arquitetura de produção. Registra-se estritamente o fato empírico de que o operador ingênuo $B_1$ avaliado neste experimento é inviável para uso produtivo.
5. **Decisão Arquitetural:**  
   **B1 ISOLADO NÃO É ELEGÍVEL PARA PRODUÇÃO (`NOT ELIGIBLE FOR PRODUCTION`).**

---

## 9. Registro de Custódia e Não-Mutação

* **Nenhum arquivo em `src/agent_lab/` foi alterado.**
* **Nenhum arquivo em `tests/` foi alterado.**
* **Nenhum dataset congelado foi alterado.**
* **Nenhum commit foi realizado.**
* **Nenhum push foi executado.**
* **Nenhum pull request foi aberto.**
* **Sessão encerrada em HARD STOP HUMANO, com alterações restritas aos artefatos experimentais e documentais autorizados; código de produto, testes canônicos e artefatos FROZEN permaneceram intocados.**
