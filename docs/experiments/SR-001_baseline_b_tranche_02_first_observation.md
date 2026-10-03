# SR-001 Baseline B — Tranche 02: Registro de Custódia da Primeira Observação (Harness v2)

> Documento de custódia e registro histórico da primeira observação cega (*observed-as-run*)
> da Tranche 02 do Baseline B (SR-001 / Issue #158), executada em 03/10/2026 via autorização formal humana.

---

## Metadados da Execução

| Campo | Valor |
|---|---|
| **Investigação experimental** | `SR-001 / Scale Reconnaissance v1` (Pressão Arquitetural P-07) |
| **Componente avaliado** | `Baseline B — Tranche 02 (Qualidade Semântica Expandida)` |
| **Classificação formal** | `FIRST BLIND TRANCHE OBSERVATION (OBSERVED-AS-RUN)` |
| **Data e hora da execução (UTC)** | `2026-10-03T13:07:13.536135+00:00` (~10:07 BRT) |
| **Git HEAD de Execução** | `973eadb019289fb002aa4022a494663a24edd243` (`main`) |
| **Run ID** | `RUN-T02-20261003T130713Z-5D78EB04` |
| **Harness experimental utilizado** | `experiments/sr001_baseline_b_harness_v2.py` (v2 integrado) |
| **SHA-256 do Harness v2 (LF)** | `cfcee60f0049d7d3709d5c5a6c1d34c2a28dcfc75c1d5d6801a57a445dc18f9f` |
| **Mecanismo de acionamento** | Execução única cega autorizada (zero tuning, zero rerun, zero alterações) |
| **Arquivo de checkpoint original** | `experiments/checkpoints/sr001_baseline_b_tranche_02_RUN-T02-20261003T130713Z-5D78EB04.json` |
| **Arquivo de evidência versionado** | `experiments/evidence/sr001_baseline_b_tranche_02_first_observation.json` |
| **SHA-256 da evidência (cópia exata LF)** | `311b680e3d4c76c11ea11ea5c7dac8bcca6593f6f48b7c2d5a29135b61f7853c` |
| **Tamanho da evidência** | `58.151 bytes` (cópia byte-a-byte idêntica) |
| **Amostra avaliada** | `40 pares` (20 positivos e 20 hard negatives; 80 materiais sintéticos congelados) |

---

## 1. Cadeia de Custódia dos Artefatos FROZEN

A execução consumiu de forma estritamente somente-leitura os três arquivos congelados da Tranche 02:

* **Catálogo (`experiments/baseline_b/draft_tranche_02_catalog.csv`):**  
  `74e1389f66fd14155dba1b3be9b16ef2ef9fe79b04e16232d2c2fb142e1c218b` (80 materiais sintéticos industriais);
* **Ground Truth (`experiments/baseline_b/draft_tranche_02_ground_truth.json`):**  
  `052bd6fec3f165cea9cdbf686cb961af4eccf962f4689d938a00fdc459b92008` (40 pares auditados: 20P / 20HN);
* **Manifesto (`experiments/baseline_b/draft_tranche_02_manifest.json`):**  
  `cab0732e83594111522e5edfd8c4bc1ff310c4be2df0b1d4c282b40a4f48a88b` (40 casos em correspondência 1:1, `status == "DRAFT"`, `freeze_state == "FROZEN"`, `freeze_sha256 == "052bd6fec3f165cea9cdbf686cb961af4eccf962f4689d938a00fdc459b92008"`).

---

## 2. Fatos Experimentais da Observação T02 (Tabela Canônica dos 40 Casos)

| Case ID | Estrato | Classe | Descrição Curta A | Descrição Curta B | GT | CS Outcome | Det Uncond | Det Cond |
|---|---|---|---|---|:---:|:---:|:---:|:---:|
| `CASE-SR001-B-T02-001` | `FASTENERS` | `P-SEPARATOR` | `PARAFUSO ALLEN C/C DIN 912 M12X45 ACO 12.9 FOSF` | `PARAFUSO ALLEN CC DIN912 M12-45 CL12.9 FOSFAT` | `P` | **`POSITIVE_RETAINED`** | **`TP`** | **`TP`** |
| `CASE-SR001-B-T02-002` | `FASTENERS` | `P-MFG-MISSING` | `PRISIONEIRO ROSCA CONTINUA ASTM A193 B7 3/4 POL X 150 MM` | `ESTOJO PRISIONEIRO ASTM A193 B7 3/4 X 150 MM` | `P` | **`POSITIVE_DROPPED`** | **`FN`** | **`N/A (podado)`** |
| `CASE-SR001-B-T02-003` | `FASTENERS` | `P-ABBR` | `PORCA SEXTAVADA PESADA DIN 934 M16 ACO GRAU 8 BICROMATIZADA` | `PC SEXT PESADA DIN934 M-16 G8 BICROM` | `P` | **`POSITIVE_RETAINED`** | **`TP`** | **`TP`** |
| `CASE-SR001-B-T02-004` | `FASTENERS` | `P-CROSS-GRP` | `ARRUELA DE TRAVAMENTO POR CUNHA NORD-LOCK NL12 ACO CARBONO` | `ARRUELA TRAVA POR CUNHA NORD-LOCK NL12 M12 ACO CARBONO` | `P` | **`POSITIVE_RETAINED`** | **`TP`** | **`TP`** |
| `CASE-SR001-B-T02-005` | `FASTENERS` | `HN-DIM` | `PARAFUSO SEXTAVADO DIN 931 M12X60 ACO 8.8 ZB RP` | `PARAFUSO SEXTAVADO DIN 931 M12X70 ACO 8.8 ZB RP` | `HN` | **`NEGATIVE_RETAINED`** | **`FP`** | **`FP`** |
| `CASE-SR001-B-T02-006` | `FASTENERS` | `HN-MAT` | `PARAFUSO SEXTAVADO DIN 933 M8X25 ACO CARBONO 8.8 ZB` | `PARAFUSO SEXTAVADO DIN 933 M8X25 ACO INOXIDAVEL A4-70` | `HN` | **`NEGATIVE_RETAINED`** | **`FP`** | **`FP`** |
| `CASE-SR001-B-T02-007` | `FASTENERS` | `HN-VAR` | `BARRA ROSCADA 1000 MM DIN 975 M20 PASSO NORMAL 2.5 MM` | `BARRA ROSCADA 1000 MM DIN 976-1 M20 PASSO FINO 1.5 MM` | `HN` | **`NEGATIVE_RETAINED`** | **`FP`** | **`FP`** |
| `CASE-SR001-B-T02-008` | `FASTENERS` | `HN-DISTINCT` | `REBITE DE REPUXO POP ALUMINIO/ACO 4.8X16 CABECA ABAULADA` | `REBITE DE REPUXO POP ALUMINIO/ACO 4.8X16 CABECA ESCAREADA` | `HN` | **`NEGATIVE_RETAINED`** | **`FP`** | **`FP`** |
| `CASE-SR001-B-T02-009` | `VALVES` | `P-PN-STRUCTURAL` | `VALVULA DE RETENCAO PISTAO CLASSE 800 DN 1/2 POL NPT A105` | `VALVULA RETENCAO LIFT CHECK CL800 1/2 NPT CORPO FORJADO` | `P` | **`POSITIVE_RETAINED`** | **`TP`** | **`TP`** |
| `CASE-SR001-B-T02-010` | `VALVES` | `P-SEPARATOR` | `VALVULA GLOBO FLANGEADA CLASSE 150 DN 2 POL WCB HASTE ASC` | `VALVULA GLOBO 2 POL FLANGEADA 150# CORPO WCB HASTE ASC` | `P` | **`POSITIVE_RETAINED`** | **`TP`** | **`TP`** |
| `CASE-SR001-B-T02-011` | `VALVES` | `P-ABBR` | `VALVULA BORBOLETA WAFER DN 100 CLASSE 150 CORPO FOFO DISCO CF8M` | `VLV BORB WF DN100 4 POL CL150 NOD DISCO INOX VED EPDM ALAV` | `P` | **`POSITIVE_RETAINED`** | **`TP`** | **`TP`** |
| `CASE-SR001-B-T02-012` | `VALVES` | `P-CROSS-GRP` | `VALVULA DE SEGURANCA E ALIVIO BRONZE 1/2 NPT X 1 NPT 8 BAR` | `VALVULA SEGURANCA ALIVIO MOLA 1/2 X 1 NPT CORPO BRONZE 8 BAR` | `P` | **`POSITIVE_RETAINED`** | **`TP`** | **`TP`** |
| `CASE-SR001-B-T02-013` | `VALVES` | `HN-DIM` | `VALVULA GAVETA FLANGEADA CLASSE 150 DN 3 POL WCB HASTE ASC` | `VALVULA GAVETA FLANGEADA CLASSE 150 DN 4 POL WCB HASTE ASC` | `HN` | **`NEGATIVE_RETAINED`** | **`FP`** | **`FP`** |
| `CASE-SR001-B-T02-014` | `VALVES` | `HN-MAT` | `FILTRO TIPO Y FLANGEADO CLASSE 150 DN 50 CORPO FERRO FUNDIDO` | `FILTRO TIPO Y FLANGEADO CLASSE 150 DN 50 CORPO ACO CARBONO` | `HN` | **`NEGATIVE_RETAINED`** | **`FP`** | **`FP`** |
| `CASE-SR001-B-T02-015` | `VALVES` | `HN-VAR` | `VALVULA ESFERA FLANGEADA CLASSE 150 DN 50 PASSAGEM PLENA WCB` | `VALVULA ESFERA FLANGEADA CLASSE 150 DN 50 PASSAGEM REDUZIDA WCB` | `HN` | **`NEGATIVE_RETAINED`** | **`FP`** | **`FP`** |
| `CASE-SR001-B-T02-016` | `VALVES` | `HN-DISTINCT` | `PURGADOR DE VAPOR TERMODINAMICO 1/2 POL NPT TD52 SPIRAX SARCO` | `PURGADOR DE VAPOR BOIA TERMOSTATICA 1/2 POL NPT FT14 SPIRAX SARCO` | `HN` | **`NEGATIVE_RETAINED`** | **`FP`** | **`FP`** |
| `CASE-SR001-B-T02-017` | `BEARINGS` | `P-PN-STRUCTURAL` | `ROLAMENTO AUTOCOMPENSADOR DE ROLOS SKF 22212 E` | `ROLAMENTO ROLOS AUTOCOMPENSADOR 22212 E SKF 60X110X28` | `P` | **`POSITIVE_RETAINED`** | **`TP`** | **`TP`** |
| `CASE-SR001-B-T02-018` | `BEARINGS` | `P-SEPARATOR` | `ROLAMENTO DE ROLOS CONICOS TIMKEN 32008X 40X68X19 MM` | `ROLAMENTO ROLOS CONICOS 32008X TIMKEN 40X68X19` | `P` | **`POSITIVE_RETAINED`** | **`TP`** | **`TP`** |
| `CASE-SR001-B-T02-019` | `BEARINGS` | `P-MFG-MISSING` | `ROLAMENTO CONTATO ANGULAR SKF 7206 BEP 30X62X16 MM` | `ROLAMENTO ESFERAS CONTATO ANGULAR 7206 BEP 30X62X16` | `P` | **`POSITIVE_RETAINED`** | **`TP`** | **`TP`** |
| `CASE-SR001-B-T02-020` | `BEARINGS` | `P-TRUNCATED` | `CAIXA DE MANCAL BIPARTIDA SKF SNL 511-609 P/ EIXO 50 MM` | `CAIXA DE MANCAL BIPARTIDA SKF SNL 511-60` | `P` | **`POSITIVE_RETAINED`** | **`TP`** | **`TP`** |
| `CASE-SR001-B-T02-021` | `BEARINGS` | `HN-DIM` | `ROLAMENTO RIGIDO DE ESFERAS 6305 25X62X17 MM SKF` | `ROLAMENTO RIGIDO DE ESFERAS 6306 30X72X19 MM SKF` | `HN` | **`NEGATIVE_RETAINED`** | **`TN`** | **`TN`** |
| `CASE-SR001-B-T02-022` | `BEARINGS` | `HN-MAT` | `ROLAMENTO LINEAR PILLOW BLOCK ABERTO EIXO 20 MM ACO CROMO` | `ROLAMENTO LINEAR PILLOW BLOCK ABERTO EIXO 20 MM ACO INOX` | `HN` | **`NEGATIVE_RETAINED`** | **`TN`** | **`TN`** |
| `CASE-SR001-B-T02-023` | `BEARINGS` | `HN-VAR` | `ROLAMENTO AUTOCOMPENSADOR ROLOS 22214 E FURO CILINDRICO` | `ROLAMENTO AUTOCOMPENSADOR ROLOS 22214 EK FURO CONICO 1:12` | `HN` | **`NEGATIVE_RETAINED`** | **`FP`** | **`FP`** |
| `CASE-SR001-B-T02-024` | `BEARINGS` | `HN-DISTINCT` | `BUCHA DE FIXACAO COMPLETA COM PORCA E ARRUELA H 311` | `BUCHA DE DESMONTAGEM COM ROSCA DE EXTRACAO AHX 311` | `HN` | **`NEGATIVE_RETAINED`** | **`FP`** | **`FP`** |
| `CASE-SR001-B-T02-025` | `ELECTRICAL` | `P-PN-STRUCTURAL` | `DISJUNTOR-MOTOR TERMOMAGNETICO 16 A 20A 50KA SIEMENS 3RV2011-4BA10` | `DISJUNTOR MOTOR 3RV2 16-20A SIEMENS SIRIUS S00` | `P` | **`POSITIVE_RETAINED`** | **`TP`** | **`TP`** |
| `CASE-SR001-B-T02-026` | `ELECTRICAL` | `P-SEPARATOR` | `RELE DE SOBRECARGA TERMICO BIMETALICO 23 A 32A SCHNEIDER LRD3353` | `RELE TERMICO DE PROTECAO 23-32A SCHNEIDER TESYS LRD3353` | `P` | **`POSITIVE_RETAINED`** | **`TP`** | **`TP`** |
| `CASE-SR001-B-T02-027` | `ELECTRICAL` | `P-MFG-MISSING` | `SENSOR INDUTIVO M18 SALIENTE PNP NA CABO 2M BALLUFF BES 516` | `SENSOR PROXIMIDADE INDUTIVO M18 DIST SENSORA 8MM PNP NA` | `P` | **`POSITIVE_RETAINED`** | **`TP`** | **`TP`** |
| `CASE-SR001-B-T02-028` | `ELECTRICAL` | `P-TRUNCATED` | `INVERSOR DE FREQUENCIA WEG CFW500 5CV 380V 10A COM IHM` | `INVERSOR DE FREQUENCIA WEG CFW500 5CV 38` | `P` | **`POSITIVE_RETAINED`** | **`TP`** | **`TP`** |
| `CASE-SR001-B-T02-029` | `ELECTRICAL` | `HN-DIM` | `CABO DE POTENCIA COBRE HEPR 1KV UNIPOLAR SECAO 16 MM2 AZUL` | `CABO DE POTENCIA COBRE HEPR 1KV UNIPOLAR SECAO 25 MM2 AZUL` | `HN` | **`NEGATIVE_RETAINED`** | **`FP`** | **`FP`** |
| `CASE-SR001-B-T02-030` | `ELECTRICAL` | `HN-MAT` | `ELETRODUTO RIGIDO ROSCAVEL NBR 5597 1 POL GALVANIZADO A FOGO` | `ELETRODUTO RIGIDO ROSCAVEL NBR 5597 1 POL ALUMINIO COBRE-FREE` | `HN` | **`NEGATIVE_RETAINED`** | **`FP`** | **`FP`** |
| `CASE-SR001-B-T02-031` | `ELECTRICAL` | `HN-VAR` | `FONTE CHAVEADA TRILHO DIN 24VCC 5A 120W ENTRADA BIVOLT` | `FONTE CHAVEADA TRILHO DIN 24VCC 5A 120W ATEX CONFORMAL COATING` | `HN` | **`NEGATIVE_RETAINED`** | **`FP`** | **`FP`** |
| `CASE-SR001-B-T02-032` | `ELECTRICAL` | `HN-DISTINCT` | `TRANSMISSOR DE PRESSAO INDUSTRIAL 4-20MA 0 A 10 BAR MBS 3000` | `TRANSMISSOR DE PRESSAO INDUSTRIAL 4-20MA 0 A 25 BAR MBS 3000` | `HN` | **`NEGATIVE_RETAINED`** | **`FP`** | **`FP`** |
| `CASE-SR001-B-T02-033` | `GENERAL` | `P-MFG-MISSING` | `CORREIA SINCRONIZADA GATES POWERGRIP GT3 1040-8M-30` | `CORREIA DENTADA SINCRONA 1040 8M 30MM 130 DENTES` | `P` | **`POSITIVE_RETAINED`** | **`TP`** | **`TP`** |
| `CASE-SR001-B-T02-034` | `GENERAL` | `P-ABBR` | `ANEL ORING AS568-222 FLUOROELASTOMERO VITON 75 SHORE A` | `O-RING AS 568 222 FKM 75SH A PARKER` | `P` | **`POSITIVE_RETAINED`** | **`TP`** | **`TP`** |
| `CASE-SR001-B-T02-035` | `GENERAL` | `P-CROSS-GRP` | `MANGUEIRA HIDRAULICA 2 TRAMAS ACO SAE 100 R2AT 3/8 POL` | `MANGUEIRA ALTA PRESSAO HIDRAULICA 3/8 R2AT DUPLA TRAMA` | `P` | **`POSITIVE_RETAINED`** | **`TP`** | **`TP`** |
| `CASE-SR001-B-T02-036` | `GENERAL` | `P-TRUNCATED` | `JUNTA ESPIROMETALICA 2 POL CLASSE 300 ASME B16.20 316L/GRAFITE` | `JUNTA ESPIROMETALICA 2 POL CLASSE 300 AS` | `P` | **`POSITIVE_RETAINED`** | **`TP`** | **`TP`** |
| `CASE-SR001-B-T02-037` | `GENERAL` | `HN-DIM` | `CORREIA EM V PERFIL CLASSICO B60 COMPRIMENTO 60 POL GATES` | `CORREIA EM V PERFIL CLASSICO B62 COMPRIMENTO 62 POL GATES` | `HN` | **`NEGATIVE_RETAINED`** | **`FP`** | **`FP`** |
| `CASE-SR001-B-T02-038` | `GENERAL` | `HN-MAT` | `ANEL RASPADOR HIDRAULICO DKB 40X50X7 MM BORRACHA NBR 90 SHORE` | `ANEL RASPADOR HIDRAULICO DKB 40X50X7 MM POLIURETANO 95 SHORE` | `HN` | **`NEGATIVE_RETAINED`** | **`FP`** | **`FP`** |
| `CASE-SR001-B-T02-039` | `GENERAL` | `HN-VAR` | `JUNTA ESPIROMETALICA 3 POL CLASSE 150 TIPO CG ASME B16.20` | `JUNTA ESPIROMETALICA 3 POL CLASSE 150 TIPO CGI ASME B16.20` | `HN` | **`NEGATIVE_RETAINED`** | **`FP`** | **`FP`** |
| `CASE-SR001-B-T02-040` | `GENERAL` | `HN-DISTINCT` | `MANGUEIRA DE BORRACHA SUCCAO E DESCARGA DE AGUA 2 POL 10 BAR` | `MANGUEIRA DE BORRACHA SUCCAO E DESCARGA OLEO/COMBUSTIVEL 2 POL` | `HN` | **`NEGATIVE_RETAINED`** | **`TN`** | **`TN`** |

---

## 3. Métricas Metrológicas Segregadas

### 3.1 Bloco 1 — Candidate Selection (Filtro de Candidatos)
* Positivos no Ground Truth: **$20$**
* Positivos retidos (**`POSITIVE_RETAINED`**): **$19$**
* Positivos perdidos pelo filtro (**`POSITIVE_DROPPED`**): **$1$** (`CASE-SR001-B-T02-002`)
* Hard Negatives retidos (**`NEGATIVE_RETAINED`**): **$20$**
* Hard Negatives descartados (**`NEGATIVE_DROPPED`**): **$0$**
* Total de pares retidos para o detector: **$39/40$**
* **Candidate Pair Recall ($\text{Recall}_{\text{block}}$):** **$19/20 = 95.0\%$**
* **Candidate Pair Miss Rate:** **$5.0\%$**
* **Challenge-Set Retention Rate:** **$97.5\%$**
* **Challenge-Set Reduction Ratio:** **$2.5\%$**
  *(Ressalva canônica: redução no challenge set não é extrapolável para o catálogo completo de 100k).*  

### 3.2 Bloco 2 — Detector Incondicional (Baseline sobre Todos os 40 Pares)
* Verdadeiros Positivos ($TP$): **$19$**
* Falsos Positivos ($FP$): **$17$**
* Verdadeiros Negativos ($TN$): **$3$**
* Falsos Negativos ($FN$): **$1$** (`CASE-SR001-B-T02-002`)
* **Precision:** **$19 / (19 + 17) = 19/36 \approx 52.78\%$**
* **Recall:** **$19 / (19 + 1) = 19/20 = 95.00\%$**
* **F1-Score:** **$0.6786$**  

### 3.3 Bloco 3 — Detector Condicionado aos Candidatos (39 Pares Retidos)
* Pares avaliados pelo detector: **$39$**
* Verdadeiros Positivos ($TP$): **$19$**
* Falsos Positivos ($FP$): **$17$**
* Verdadeiros Negativos ($TN$): **$3$**
* Falsos Negativos ($FN$): **$0$** *(o par descartado na etapa de Candidate Selection não foi submetido ao detector)*
* **Precision Condicionada:** **$19/36 \approx 52.78\%$**
* **Recall Condicionado:** **$19/19 = 100.00\%$**
* **F1-Score Condicionado:** **$0.6909$**  

### 3.4 Bloco 4 — Pipeline End-to-End (Candidate Selection $\rightarrow$ Detector Condicionado)
* **Recall do Bloco:** **$95.0\%$** (0.9500)
* **Recall do Detector Condicionado:** **$100.0\%$** (1.0000)
* **Overall Pipeline Recall:** **$95.0\%$** (0.9500)
* **Challenge-Set Reduction Ratio:** **$2.5\%$** (0.0250)
* **Ponto Bidimensional $(\text{Reduction}, \text{Pipeline Recall})$:** **$(0.0250, 0.9500)$**

---

## 4. Breakdowns Descritivos

### 4.1 Por Família de Perturbação (F1–F10)

| Família | Taxonomia | Total | Pos | Neg | Retidos | Descartados | TP | FP | TN | FN |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **F1** | `P-PN-STRUCTURAL` | 3 | 3 | 0 | 3 | 0 | 3 | 0 | 0 | 0 |
| **F2** | `P-SEPARATOR` | 4 | 4 | 0 | 4 | 0 | 4 | 0 | 0 | 0 |
| **F3** | `P-MFG-MISSING` | 4 | 4 | 0 | 3 | 1 | 3 | 0 | 0 | 1 |
| **F4** | `P-ABBR` | 3 | 3 | 0 | 3 | 0 | 3 | 0 | 0 | 0 |
| **F5** | `P-CROSS-GRP` | 3 | 3 | 0 | 3 | 0 | 3 | 0 | 0 | 0 |
| **F6** | `P-TRUNCATED` | 3 | 3 | 0 | 3 | 0 | 3 | 0 | 0 | 0 |
| **F7** | `HN-DIM` | 5 | 0 | 5 | 5 | 0 | 0 | 4 | 1 | 0 |
| **F8** | `HN-MAT` | 5 | 0 | 5 | 5 | 0 | 0 | 4 | 1 | 0 |
| **F9** | `HN-VAR` | 5 | 0 | 5 | 5 | 0 | 0 | 5 | 0 | 0 |
| **F10** | `HN-DISTINCT` | 5 | 0 | 5 | 5 | 0 | 0 | 4 | 1 | 0 |

### 4.2 Por Estrato Industrial

| Estrato | Total | Pos | Neg | Retidos | Descartados | TP | FP | TN | FN |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **BEARINGS** | 8 | 4 | 4 | 8 | 0 | 4 | 2 | 2 | 0 |
| **ELECTRICAL** | 8 | 4 | 4 | 8 | 0 | 4 | 4 | 0 | 0 |
| **FASTENERS** | 8 | 4 | 4 | 7 | 1 | 3 | 4 | 0 | 1 |
| **GENERAL** | 8 | 4 | 4 | 8 | 0 | 4 | 3 | 1 | 0 |
| **VALVES** | 8 | 4 | 4 | 8 | 0 | 4 | 4 | 0 | 0 |

---

## 5. Inventário Completo de Erros e Casos Críticos

### 5.1 Falso Negativo / Positivo Descartado pelo Blocking (1 caso)

* **`CASE-SR001-B-T02-002` (`FASTENERS` / `P-MFG-MISSING`):**
  * *Material A (`MAT-SR001-B-T02-002A`):* `PRISIONEIRO ROSCA CONTINUA ASTM A193 B7 3/4 POL X 150 MM` (Fabricante: `CISER`, PN: `B7-075-150`)
  * *Material B (`MAT-SR001-B-T02-002B`):* `ESTOJO PRISIONEIRO ASTM A193 B7 3/4 X 150 MM` (Fabricante: ``, PN: ``)
  * *Desfecho Observado:* `POSITIVE_DROPPED` no Candidate Selection e `FN` no Detector Incondicional.
  * *Causa Estrutural:* Registro B possui fabricante e part number estruturados vazios (Rota 1 requer ambos não-vazios e Rota 2 diverge no token de categoria entre `PRISIONEIRO` e `ESTOJO`).

### 5.2 Falsos Positivos do Detector (17 casos)

* **`CASE-SR001-B-T02-005` (`FASTENERS` / `HN-DIM`):**
  * *Material A (`MAT-SR001-B-T02-005A`):* `PARAFUSO SEXTAVADO DIN 931 M12X60 ACO 8.8 ZB RP` (PN: `931-12-060`)
  * *Material B (`MAT-SR001-B-T02-005B`):* `PARAFUSO SEXTAVADO DIN 931 M12X70 ACO 8.8 ZB RP` (PN: `931-12-070`)
* **`CASE-SR001-B-T02-006` (`FASTENERS` / `HN-MAT`):**
  * *Material A (`MAT-SR001-B-T02-006A`):* `PARAFUSO SEXTAVADO DIN 933 M8X25 ACO CARBONO 8.8 ZB` (PN: `933-08-025-88`)
  * *Material B (`MAT-SR001-B-T02-006B`):* `PARAFUSO SEXTAVADO DIN 933 M8X25 ACO INOXIDAVEL A4-70` (PN: `933-08-025-A4`)
* **`CASE-SR001-B-T02-007` (`FASTENERS` / `HN-VAR`):**
  * *Material A (`MAT-SR001-B-T02-007A`):* `BARRA ROSCADA 1000 MM DIN 975 M20 PASSO NORMAL 2.5 MM` (PN: `975-M20-STD`)
  * *Material B (`MAT-SR001-B-T02-007B`):* `BARRA ROSCADA 1000 MM DIN 976-1 M20 PASSO FINO 1.5 MM` (PN: `976-M20-FINO`)
* **`CASE-SR001-B-T02-008` (`FASTENERS` / `HN-DISTINCT`):**
  * *Material A (`MAT-SR001-B-T02-008A`):* `REBITE DE REPUXO POP ALUMINIO/ACO 4.8X16 CABECA ABAULADA` (PN: `AD-616`)
  * *Material B (`MAT-SR001-B-T02-008B`):* `REBITE DE REPUXO POP ALUMINIO/ACO 4.8X16 CABECA ESCAREADA` (PN: `AK-616`)
* **`CASE-SR001-B-T02-013` (`VALVES` / `HN-DIM`):**
  * *Material A (`MAT-SR001-B-T02-013A`):* `VALVULA GAVETA FLANGEADA CLASSE 150 DN 3 POL WCB HASTE ASC` (PN: `GT-150-WCB-080`)
  * *Material B (`MAT-SR001-B-T02-013B`):* `VALVULA GAVETA FLANGEADA CLASSE 150 DN 4 POL WCB HASTE ASC` (PN: `GT-150-WCB-100`)
* **`CASE-SR001-B-T02-014` (`VALVES` / `HN-MAT`):**
  * *Material A (`MAT-SR001-B-T02-014A`):* `FILTRO TIPO Y FLANGEADO CLASSE 150 DN 50 CORPO FERRO FUNDIDO` (PN: `FIG12-CI-050`)
  * *Material B (`MAT-SR001-B-T02-014B`):* `FILTRO TIPO Y FLANGEADO CLASSE 150 DN 50 CORPO ACO CARBONO` (PN: `FIG16-CS-050`)
* **`CASE-SR001-B-T02-015` (`VALVES` / `HN-VAR`):**
  * *Material A (`MAT-SR001-B-T02-015A`):* `VALVULA ESFERA FLANGEADA CLASSE 150 DN 50 PASSAGEM PLENA WCB` (PN: `F150-FB-050`)
  * *Material B (`MAT-SR001-B-T02-015B`):* `VALVULA ESFERA FLANGEADA CLASSE 150 DN 50 PASSAGEM REDUZIDA WCB` (PN: `F150-RB-050`)
* **`CASE-SR001-B-T02-016` (`VALVES` / `HN-DISTINCT`):**
  * *Material A (`MAT-SR001-B-T02-016A`):* `PURGADOR DE VAPOR TERMODINAMICO 1/2 POL NPT TD52 SPIRAX SARCO` (PN: `TD52-015`)
  * *Material B (`MAT-SR001-B-T02-016B`):* `PURGADOR DE VAPOR BOIA TERMOSTATICA 1/2 POL NPT FT14 SPIRAX SARCO` (PN: `FT14-015`)
* **`CASE-SR001-B-T02-023` (`BEARINGS` / `HN-VAR`):**
  * *Material A (`MAT-SR001-B-T02-023A`):* `ROLAMENTO AUTOCOMPENSADOR ROLOS 22214 E FURO CILINDRICO` (PN: `22214-E`)
  * *Material B (`MAT-SR001-B-T02-023B`):* `ROLAMENTO AUTOCOMPENSADOR ROLOS 22214 EK FURO CONICO 1:12` (PN: `22214-EK`)
* **`CASE-SR001-B-T02-024` (`BEARINGS` / `HN-DISTINCT`):**
  * *Material A (`MAT-SR001-B-T02-024A`):* `BUCHA DE FIXACAO COMPLETA COM PORCA E ARRUELA H 311` (PN: `H-311`)
  * *Material B (`MAT-SR001-B-T02-024B`):* `BUCHA DE DESMONTAGEM COM ROSCA DE EXTRACAO AHX 311` (PN: `AHX-311`)
* **`CASE-SR001-B-T02-029` (`ELECTRICAL` / `HN-DIM`):**
  * *Material A (`MAT-SR001-B-T02-029A`):* `CABO DE POTENCIA COBRE HEPR 1KV UNIPOLAR SECAO 16 MM2 AZUL` (PN: `AFUMEX-16-AZ`)
  * *Material B (`MAT-SR001-B-T02-029B`):* `CABO DE POTENCIA COBRE HEPR 1KV UNIPOLAR SECAO 25 MM2 AZUL` (PN: `AFUMEX-25-AZ`)
* **`CASE-SR001-B-T02-030` (`ELECTRICAL` / `HN-MAT`):**
  * *Material A (`MAT-SR001-B-T02-030A`):* `ELETRODUTO RIGIDO ROSCAVEL NBR 5597 1 POL GALVANIZADO A FOGO` (PN: `NBR5597-1POL-GF`)
  * *Material B (`MAT-SR001-B-T02-030B`):* `ELETRODUTO RIGIDO ROSCAVEL NBR 5597 1 POL ALUMINIO COBRE-FREE` (PN: `NBR5597-1POL-AL`)
* **`CASE-SR001-B-T02-031` (`ELECTRICAL` / `HN-VAR`):**
  * *Material A (`MAT-SR001-B-T02-031A`):* `FONTE CHAVEADA TRILHO DIN 24VCC 5A 120W ENTRADA BIVOLT` (PN: `PSS24-W/5`)
  * *Material B (`MAT-SR001-B-T02-031B`):* `FONTE CHAVEADA TRILHO DIN 24VCC 5A 120W ATEX CONFORMAL COATING` (PN: `PSS24-W/5-EX`)
* **`CASE-SR001-B-T02-032` (`ELECTRICAL` / `HN-DISTINCT`):**
  * *Material A (`MAT-SR001-B-T02-032A`):* `TRANSMISSOR DE PRESSAO INDUSTRIAL 4-20MA 0 A 10 BAR MBS 3000` (PN: `060G1113`)
  * *Material B (`MAT-SR001-B-T02-032B`):* `TRANSMISSOR DE PRESSAO INDUSTRIAL 4-20MA 0 A 25 BAR MBS 3000` (PN: `060G1115`)
* **`CASE-SR001-B-T02-037` (`GENERAL` / `HN-DIM`):**
  * *Material A (`MAT-SR001-B-T02-037A`):* `CORREIA EM V PERFIL CLASSICO B60 COMPRIMENTO 60 POL GATES` (PN: `B60`)
  * *Material B (`MAT-SR001-B-T02-037B`):* `CORREIA EM V PERFIL CLASSICO B62 COMPRIMENTO 62 POL GATES` (PN: `B62`)
* **`CASE-SR001-B-T02-038` (`GENERAL` / `HN-MAT`):**
  * *Material A (`MAT-SR001-B-T02-038A`):* `ANEL RASPADOR HIDRAULICO DKB 40X50X7 MM BORRACHA NBR 90 SHORE` (PN: `DKB-0400-NBR`)
  * *Material B (`MAT-SR001-B-T02-038B`):* `ANEL RASPADOR HIDRAULICO DKB 40X50X7 MM POLIURETANO 95 SHORE` (PN: `DKB-0400-TPU`)
* **`CASE-SR001-B-T02-039` (`GENERAL` / `HN-VAR`):**
  * *Material A (`MAT-SR001-B-T02-039A`):* `JUNTA ESPIROMETALICA 3 POL CLASSE 150 TIPO CG ASME B16.20` (PN: `913-CG-3-150`)
  * *Material B (`MAT-SR001-B-T02-039B`):* `JUNTA ESPIROMETALICA 3 POL CLASSE 150 TIPO CGI ASME B16.20` (PN: `913-CGI-3-150`)

### 5.3 Verdadeiros Negativos (3 casos discriminados com sucesso pelo detector)

* **`CASE-SR001-B-T02-021` (`BEARINGS` / `HN-DIM`):**
  * *Material A (`MAT-SR001-B-T02-021A`):* `ROLAMENTO RIGIDO DE ESFERAS 6305 25X62X17 MM SKF` (PN: `6305`)
  * *Material B (`MAT-SR001-B-T02-021B`):* `ROLAMENTO RIGIDO DE ESFERAS 6306 30X72X19 MM SKF` (PN: `6306`)
* **`CASE-SR001-B-T02-022` (`BEARINGS` / `HN-MAT`):**
  * *Material A (`MAT-SR001-B-T02-022A`):* `ROLAMENTO LINEAR PILLOW BLOCK ABERTO EIXO 20 MM ACO CROMO` (PN: `SBR20UU`)
  * *Material B (`MAT-SR001-B-T02-022B`):* `ROLAMENTO LINEAR PILLOW BLOCK ABERTO EIXO 20 MM ACO INOX` (PN: `SBR20UU-SS`)
* **`CASE-SR001-B-T02-040` (`GENERAL` / `HN-DISTINCT`):**
  * *Material A (`MAT-SR001-B-T02-040A`):* `MANGUEIRA DE BORRACHA SUCCAO E DESCARGA DE AGUA 2 POL 10 BAR` (PN: `WATER-SD-2POL`)
  * *Material B (`MAT-SR001-B-T02-040B`):* `MANGUEIRA DE BORRACHA SUCCAO E DESCARGA OLEO/COMBUSTIVEL 2 POL` (PN: `OIL-SD-2POL`)

---

## 6. Comparação Descritiva com a Tranche 01

| Métrica | Tranche 01 (10 pares) | Tranche 02 (40 pares) |
|---|:---:|:---:|
| **Composição da Amostra** | 5P / 5HN (20 materiais) | 20P / 20HN (80 materiais) |
| **Estratos Industriais** | 5 (1P/1HN por estrato) | 5 (4P/4HN por estrato) |
| **Famílias de Perturbação** | 10 classes | 10 famílias F1–F10 |
| **Candidate Pair Recall** | 100.0% (5/5) | 95.0% (19/20) |
| **Candidate Set Reduction** | 10.0% (1/10) | 2.5% (1/40) |
| **Detector Precision (Unconditioned)** | ~55.6% (5/9) | ~52.8% (19/36) |
| **Detector Recall (Unconditioned)** | 100.0% (5/5) | 95.0% (19/20) |
| **Detector F1-Score (Unconditioned)** | 0.7143 | 0.6786 |
| **Overall Pipeline Recall** | 100.0% | 95.0% |

> **Ressalva Estatística Mandatória:** Esta comparação é puramente descritiva e não constitui alegação de regressão estatística controlada. A Tranche 01 e a Tranche 02 diferem substancialmente em poder observacional, escopo de perturbações e densidade amostral.

---

## 7. Interpretação Canônica e Limites Epistemológicos

### Formulação Canônica Permitida:
* Trata-se exclusivamente da **primeira observação da Tranche 02** (*observed-as-run*);
* A amostra é sintética e exploratória ($n=40$ pares);
* A discriminação semântica do detector heurístico frente a hard negatives permanece vulnerável (17 de 20 hard negatives foram declarados duplicatas, incluindo 5/5 em variações F9, 4/5 em divergências dimensionais F7, 4/5 em materiais F8 e 4/5 em produtos distintos F10);
* O Candidate Selection registrou o descarte de 1 par positivo (`CASE-SR001-B-T02-002`, família `P-MFG-MISSING`), gerando Candidate Pair Recall de 95.0%;
* A taxa de redução no challenge set ($2.5\%$) não se confunde com redução em catálogo real (*reduction != semantic correctness*).

### Interpretações Expressamente Vedadas:
* **NÃO** generalizar o recall para a população industrial ou catálogo de 100k SKUs;
* **NÃO** alegar validação em ambiente de produção;
* **NÃO** afirmar "H3 confirmada" ou "H3 rejeitada";
* **NÃO** considerar o detector heurístico ou o blocking como "validados no produto";
* **NÃO** converter nenhum resultado desta observação em meta ou KPI de produto.
