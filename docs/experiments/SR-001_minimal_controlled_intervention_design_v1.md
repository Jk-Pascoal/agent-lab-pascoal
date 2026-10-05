# SR-001 — Desenho Experimental de Intervenções Mínimas e Controladas (v1)

> **Documento de Especificação Metodológica e Governança Científica**
> Proposta de desenho para intervenções experimentais mínimas, isoladas e controladas sobre os fenômenos causais observados na Tranche 02 do Baseline B (`SR-001 / Issue #158`).
> **Status:** `PROPOSED / NOT YET EXECUTED`
> **Data de Elaboração:** `2026-10-05`
> **Classificação:** Alteração exclusivamente documental; zero execução experimental; zero alteração em código de produto, testes canônicos e dados congelados.

---

## 1. Metadados e Contexto da Proposta

| Campo | Valor |
|---|---|
| **Investigação Experimental** | `SR-001 / Scale Reconnaissance v1` (Pressão Arquitetural P-07) |
| **Issue Vinculada** | `#158 — SR-001 Scale Reconnaissance v1` |
| **Status Formal** | `PROPOSED / NOT YET EXECUTED` |
| **Tipo de Documento** | Especificação Metodológica de Desenho Experimental |
| **Evidência Histórica de Partida** | [`experiments/evidence/sr001_baseline_b_tranche_02_first_observation.json`](../../experiments/evidence/sr001_baseline_b_tranche_02_first_observation.json) (`RUN-T02-20261003T130713Z-5D78EB04`) |
| **SHA-256 da Evidência Base** | `311b680e3d4c76c11ea11ea5c7dac8bcca6593f6f48b7c2d5a29135b61f7853c` |
| **Documentos de Custódia Base** | [`SR-001_baseline_b_tranche_02_first_observation.md`](SR-001_baseline_b_tranche_02_first_observation.md) e [`SR-001_baseline_b_tranche_02_forensic_error_review.md`](SR-001_baseline_b_tranche_02_forensic_error_review.md) |
| **Dataset Histórico de Referência** | Tranche 02 congelada (`40 pares`: 20 positivos / 20 hard negatives; `freeze_sha256 = 052bd6fec3f165cea9cdbf686cb961af4eccf962f4689d938a00fdc459b92008`) |
| **Alterações em Código de Produção** | Nenhuma (`src/agent_lab/` permanece 100% intocado) |
| **Alterações em Testes do Produto** | Nenhuma (`tests/` permanece 100% intocado) |
| **Alterações em Dados Congelados** | Nenhuma (zero alteração em catálogo, ground truth ou manifesto) |

---

## 2. Rigor Epistemológico e Princípios de Governança Causal

Para garantir integridade científica e evitar sobreajuste conceitual ou falácias de generalização, este desenho estabelece distinções formais rigorosas:

```text
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                             INVARIANTES EPISTEMOLÓGICOS CENTRAIS                            │
├─────────────────────────────────────────────────────────────────────────────────────────────┤
│  1. ORIGINAL T02 OBSERVATION (HISTÓRICA)  ≠  INTERVENTION EXPERIMENT (CONTROLES A / B)      │
│  2. POST-HOC SENSITIVITY PROBE            ≠  INDEPENDENT VALIDATION  ≠  GENERALIZATION EV.  │
│  3. LEXICAL EQUIVALENCE HYPOTHESIS        ≠  SYNONYM DICTIONARY IMPL ≠  PRODUCTION RULE    │
│  4. CANDIDATE CONFLICTING SIGNAL          ≠  APPROVED PRODUCTION VETO POLICY                │
│  5. GROUND TRUTH DEFINITION               ≠  DETECTOR IMPLEMENTATION                        │
│  6. CANONICAL PRODUCT REPOSITORY (src/)   ≠  ISOLATED EXPERIMENTAL HARNESS (experiments/)   │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 2.1 Preservação Histórica da Observação T02
A primeira execução cega da Tranche 02 (`RUN-T02-20261003T130713Z-5D78EB04`) é um fato histórico imutável. Qualquer intervenção futura planejada neste documento constitui um experimento de intervenção separado que usa a Tranche 02 congelada estritamente como *challenge set histórico fixo*. Nenhuma run anterior será reescrita, sobrescrita ou retroativamente modificada.

### 2.2 Isolamento de Causalidade entre Dimensões
A análise forense da T02 revelou fragilidades em componentes distintos do pipeline:
- **Dimensão A (Candidate Selection):** descarte prematuro de 1 par positivo (`CASE-SR001-B-T02-002`) devido à rigidez na indexação por `category_token` na ausência de metadados estruturados de fabricante;
- **Dimensão B (Detector Downstream / Rota 2):** incapacidade discriminativa frente a 17 hard negatives devido à ausência de sensibilidade a sinais conflitantes disponíveis nos registros (part numbers discrepantes, cotas dimensionais incompatíveis, materiais excludentes, modificadores construtivos e subtipos funcionais).

Para atribuir causalidade de forma controlada:
* **Dimensão A e Dimensão B NÃO podem ser avaliadas conjuntamente na primeira intervenção.**
* **Dimensão B NÃO pode incorporar alterações de Candidate Selection.**
* Cada dimensão deve ser investigada em isolamento estrito antes de qualquer consideração de composição em pipeline.

---

## 3. Dimensão A — Candidate Selection Sensitivity

### 3.1 Reconstrução Causal do Descarte Observado (`CASE-SR001-B-T02-002`)

No experimento T02, o caso `CASE-SR001-B-T02-002` (estrato `FASTENERS`, classe `P-MFG-MISSING`, Ground Truth: positivo / `is_duplicate = True`) foi classificado pelo filtro de blocking como `POSITIVE_DROPPED`.

A cadeia causal reconstruída na auditoria forense é:
1. **Ausência de Part Number / Fabricante em B:** O registro `MAT-SR001-B-T02-002B` possui os campos `manufacturer` e `manufacturer_part_number` vazios (`""`) no catálogo CSV de entrada.
2. **Indisponibilidade da Família 1 (Rota 1):** A regra de extração de chave de Família 1 exige que ambos os campos (`part_number` e `manufacturer`) sejam não-vazios após normalização. Logo:
   - Registro A: `family_1_key = ("B7 075 150", "CISER")`;
   - Registro B: `family_1_key = None`;
   - Família 1 match: `False`.
3. **Não-retenção pela Família 2 (Rota 2):** A Família 2 baseia-se na tupla `(material_group, category_token)`. Ambos os registros pertencem ao grupo `"FIXADORES"`. Contudo:
   - Descrição Curta A: `"PRISIONEIRO ROSCA CONTINUA ASTM A193 B7 3/4 POL X 150 MM"` $\rightarrow$ primeiro token não-ignorado: `"PRISIONEIRO"`;
   - Descrição Curta B: `"ESTOJO PRISIONEIRO ASTM A193 B7 3/4 X 150 MM"` $\rightarrow$ primeiro token não-ignorado: `"ESTOJO"`;
   - Tupla A: `("FIXADORES", "PRISIONEIRO")`;
   - Tupla B: `("FIXADORES", "ESTOJO")`;
   - Família 2 match: `False` (`"PRISIONEIRO" != "ESTOJO"`).
4. **Desfecho:** O par não foi capturado por nenhuma das famílias (`is_candidate = False`), resultando em `POSITIVE_DROPPED`.

### 3.2 Distinção Tríplice Formal e Advertência de Generalização Post-Hoc

```text
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           TRÍPLICE DISTINÇÃO FORMAL                             │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  NÍVEL 1: LEXICAL EQUIVALENCE HYPOTHESIS (H-LEX)                                │
│  "A introdução de uma classe de equivalência lexical entre 'ESTOJO' e           │
│   'PRISIONEIRO' no estrato FASTENERS permite que o blocking retenha o par       │
│   positivo sem gerar explosão combinatorial no espaço de candidatos."           │
│                                                                                 │
│                                       ≠                                         │
│                                                                                 │
│  NÍVEL 2: SYNONYM DICTIONARY IMPLEMENTATION (IMPL-SYN)                          │
│  Um artefato de software ou estrutura de dados (ex.: lookup table, dicionário   │
│  em JSON, ontologia SKOS ou lematizador de domínio) que materializa o mapeamento│
│  de tokens para uma forma canônica.                                             │
│                                                                                 │
│                                       ≠                                         │
│                                                                                 │
│  NÍVEL 3: PRODUCTION RULE (PROD-RULE)                                           │
│  Alteração definitiva de código em src/agent_lab/normalization.py ou            │
│  src/agent_lab/duplicates.py integrando a regra ao comportamento em runtime     │
│  de todos os pipelines do produto.                                              │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

> [!WARNING]
> **DELIMITAÇÃO EPISTEMOLÓGICA OBRIGATÓRIA (POST-HOC PROBE):**
> $$\text{POST-HOC SENSITIVITY PROBE} \quad \neq \quad \text{INDEPENDENT VALIDATION} \quad \neq \quad \text{GENERALIZATION EVIDENCE}$$
> 1. A intervenção A1 é uma **intervenção post-hoc de sensibilidade**, formulada a partir do erro específico observado na T02;
> 2. A1 **NÃO** constitui validação independente de robustez lexical;
> 3. Recuperar `CASE-SR001-B-T02-002` sob A1 demonstra **apenas suficiência local** sobre este par no challenge set histórico;
> 4. **Nenhum resultado de A1 pode ser interpretado como evidência de generalização lexical** para o catálogo de 100k itens ou para outros sinônimos industriais;
> 5. Qualquer validação futura de generalização exigirá novos casos não utilizados na formulação da equivalência.

### 3.3 Desenho da Intervenção Experimental Abstrata A1

A intervenção experimental **A1** tem por finalidade testar exclusivamente a sensibilidade do mecanismo de Candidate Selection à flexibilização lexical mínima do `category_token`.

#### 3.3.1 Definição Conceitual de A1
Define-se $A_1$ como a parametrização experimental no harness de teste que aplica a projeção de equivalência focal observada:

$$\mathcal{E}_{\text{focal}} = \{ (\text{"ESTOJO"}, \text{"PRISIONEIRO"}), (\text{"PRISIONEIRO"}, \text{"ESTOJO"}) \}$$

Sob $A_1$, o predicado de equivalência de chave da Família 2 entre os registros $A$ e $B$ avalia:

$$\text{Match}_{F2}(A, B) \iff \text{grp}(A) = \text{grp}(B) \;\land\; \big( \text{tok}(A) = \text{tok}(B) \;\lor\; (\text{tok}(A), \text{tok}(B)) \in \mathcal{E}_{\text{focal}} \big)$$

#### 3.3.2 Localização e Injeção Experimental
* **Sem toque em `src/agent_lab/`:** A normalização do produto permanece inalterada.
* **Injeção via Harness Segregado:** No harness experimental em `experiments/`, a função de avaliação recebe um hook injetável `token_equivalence_fn: Callable[[str, str], bool] | None = None`. Na ausência do hook (`None`), o comportamento permanece estritamente idêntico ao baseline T02.

### 3.4 Métricas Mínimas para Avaliação da Dimensão A

| Métrica | Símbolo / Fórmula | Referência T02 Original | Meta / Expectativa Hipotética sob A1 |
|---|---|:---:|:---:|
| **Candidate Recall** | $\text{Recall}_{\text{block}} = \frac{P_{\text{ret}}}{P_{\text{total}}}$ | $95.00\%$ ($19/20$) | $100.00\%$ ($20/20$) |
| **Retained Positives** | $P_{\text{ret}} = \sum \mathbb{I}(\text{GT}=P \land \text{is\_candidate})$ | $19$ | $20$ ($+1$) |
| **Retained Hard Negatives** | $HN_{\text{ret}} = \sum \mathbb{I}(\text{GT}=HN \land \text{is\_candidate})$ | $20$ | $20$ (esperado invariante) |
| **Candidate Pair Count** | $N_{\text{cand}} = P_{\text{ret}} + HN_{\text{ret}}$ | $39$ | $40$ |
| **Challenge Reduction Ratio** | $\text{CRR} = 1 - \frac{N_{\text{cand}}}{N_{\text{total}}}$ | $2.50\%$ ($1/40$) | $0.00\%$ ($0/40$) |

---

## 4. Dimensão B — Negative / Conflicting Signals in Route 2

### 4.1 Foco Empírico: Os 17 Falsos Positivos da T02

Na primeira observação da T02:
* **17 de 20 hard negatives (85.0%)** foram classificados incorretamente como duplicatas (`is_possible_duplicate = True`).
* Em **100% dos 17 falsos positivos**, a decisão ocorreu pelo mesmo caminho permissivo da Rota 2:
  1. `category_token` idêntico;
  2. `normalize_text(material_group)` idêntico;
  3. Contagem de números compartilhados $\ge 2$;
  4. Contagem de palavras compartilhadas $\ge 1$.
* Em **100% dos 17 casos**, ambos os registros possuíam part numbers estruturados divergentes e/ou sinais textuais conflitantes evidentes que foram ignorados pelo algoritmo.

### 4.2 Taxonomia das Classes de Sinais Conflitantes (S1–S5)

Os sinais abaixo constituem **variáveis experimentais candidatas**. Eles **NÃO** são políticas finais de veto e **NÃO** estão aprovados para código de produção:

1. **S1: Structured Part-Number Disagreement**
   Discrepância explícita entre part numbers preenchidos e normalizados em ambos os materiais (`norm_pn(A) != norm_pn(B)`).
2. **S2: Dimensional Conflict (Cota Crítica)**
   Colisão em medidas numéricas dimensionais primárias do mesmo tipo (ex.: 60 vs 70 mm; 3" vs 4"; 16 vs 25 mm²).
3. **S3: Material / Metallurgical Conflict**
   Antagonismo metalúrgico ou polimérico explícito (ex.: Carbono vs Inox; Ferro Fundido vs Aço Carbono; NBR vs TPU).
4. **S4: Variant / Assembly Conflict**
   Modificadores construtivos de montagem, operação ou segurança (ex.: Passagem Plena vs Reduzida; Passo Normal vs Fino; Furo Cilíndrico vs Cônico; Padrão vs ATEX; Sem anel interno vs Com anel interno).
5. **S5: Subtype / Physical-Principle Conflict**
   Princípio físico de funcionamento ou função mecânica oposta sob o mesmo substantivo base (ex.: Fixação vs Desmontagem; Purgador Termodinâmico vs Boia; Faixa de Pressão 0-10 bar vs 0-25 bar).

### 4.3 Intervenções Conceituais Independentes (B1–B5)

Para cada classe de sinal $S_k$, define-se uma intervenção experimental conceitual independente $B_k$:

* **B1 — Observação de PN Conflitante (vinculado a S1):**
  Penalizar ou inibir a duplicidade na Rota 2 quando ambos os registros possuem part number estruturado preenchido, porém discordante.
* **B2 — Observação Dimensional Conflitante (vinculado a S2 e ao modo FM-1):**
  Penalizar ou inibir a duplicidade na Rota 2 quando há divergência entre grandezas dimensionais críticas do mesmo tipo. Alvo: `CASE-005`, `CASE-013`, `CASE-029`, `CASE-037` (4 casos).
* **B3 — Observação Material Conflitante (vinculado a S3 e ao modo FM-2):**
  Penalizar ou inibir a duplicidade na Rota 2 quando há termos textuais normalizados pertencentes a classes metalúrgicas ou poliméricas disjuntas. Alvo: `CASE-006`, `CASE-014`, `CASE-030`, `CASE-038` (4 casos).
* **B4 — Observação de Variante / Montagem Conflitante (vinculado a S4 e ao modo FM-3):**
  Penalizar ou inibir a duplicidade na Rota 2 quando há modificadores construtivos ou funcionais excludentes. Alvo: `CASE-007`, `CASE-015`, `CASE-023`, `CASE-031`, `CASE-039` (5 casos).
* **B5 — Observação de Subtipo / Princípio Físico Conflitante (vinculado a S5 e ao modo FM-4):**
  Penalizar ou inibir a duplicidade na Rota 2 quando há termos indicativos de princípios físicos ou papéis operacionais incompatíveis. Alvo: `CASE-008`, `CASE-016`, `CASE-024`, `CASE-032` (4 casos).

### 4.4 Caracterização Controlada de Efeitos Isolados e Cumulativos

> [!NOTE]
> **ESCOPO DO PROTOCOLO EXPERIMENTAL:**
> O protocolo abaixo mede efeitos marginais isolados e uma trajetória cumulativa pré-definida. Ele **NÃO** constitui um desenho fatorial completo de interações ($2^5 = 32$ combinações) e **NÃO** alega identificação completa de efeitos de interação multidirecionais. Seu propósito é caracterizar a suficiência discriminativa individual e o comportamento de composição aditiva ordenada.

#### Etapa 1: Caracterização de Efeitos Isolados (Marginal Puro)
1. **$B_0$ (Baseline de Controle):** Detector original da T02 (sem sinais conflitantes);
2. **$B_1$ Isolado:** Detector original $+$ apenas Sinal de PN Conflitante ($S_1$);
3. **$B_2$ Isolado:** Detector original $+$ apenas Sinal Dimensional ($S_2$);
4. **$B_3$ Isolado:** Detector original $+$ apenas Sinal Material ($S_3$);
5. **$B_4$ Isolado:** Detector original $+$ apenas Sinal Variante/Montagem ($S_4$);
6. **$B_5$ Isolado:** Detector original $+$ apenas Sinal Subtipo/Princípio ($S_5$).

#### Etapa 2: Caracterização de Efeitos Cumulativos (Composição Aditiva)
7. **$B_{1+2}$:** $B_1 + B_2$ (PN $+$ Dimensão);
8. **$B_{1+2+3}$:** $B_1 + B_2 + B_3$ (PN $+$ Dimensão $+$ Material);
9. **$B_{1+2+3+4}$:** $B_1 + B_2 + B_3 + B_4$ (PN $+$ Dimensão $+$ Material $+$ Variante);
10. **$B_{1+2+3+4+5}$:** Composição cumulativa completa dos cinco sinais.

```text
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│                  MATRIZ DE CARACTERIZAÇÃO DE EFEITOS ISOLADOS E CUMULATIVOS                  │
├────────────────────┬───────────┬───────────┬───────────┬──────────────┬──────────────────────┤
│ Configuração       │ S1 (PN)   │ S2 (Dim)  │ S3 (Mat)  │ S4 (Var/Mnt) │ S5 (Subtipo/Princ)   │
├────────────────────┼───────────┼───────────┼───────────┼──────────────┼──────────────────────┤
│ B0 (Controle T02)  │ Inativo   │ Inativo   │ Inativo   │ Inativo      │ Inativo              │
│ B1 (Isolado)       │ ATIVO     │ Inativo   │ Inativo   │ Inativo      │ Inativo              │
│ B2 (Isolado)       │ Inativo   │ ATIVO     │ Inativo   │ Inativo      │ Inativo              │
│ B3 (Isolado)       │ Inativo   │ Inativo   │ ATIVO     │ Inativo      │ Inativo              │
│ B4 (Isolado)       │ Inativo   │ Inativo   │ Inativo   │ ATIVO        │ Inativo              │
│ B5 (Isolado)       │ Inativo   │ Inativo   │ Inativo   │ Inativo      │ ATIVO                │
├────────────────────┼───────────┼───────────┼───────────┼──────────────┼──────────────────────┤
│ B(1+2)             │ ATIVO     │ ATIVO     │ Inativo   │ Inativo      │ Inativo              │
│ B(1+2+3)           │ ATIVO     │ ATIVO     │ ATIVO     │ Inativo      │ Inativo              │
│ B(1+2+3+4)         │ ATIVO     │ ATIVO     │ ATIVO     │ ATIVO        │ Inativo              │
│ B(1+2+3+4+5)       │ ATIVO     │ ATIVO     │ ATIVO     │ ATIVO        │ ATIVO                │
└────────────────────┴───────────┴───────────┴───────────┴──────────────┴──────────────────────┘
```

### 4.5 Métricas Mínimas para Avaliação da Dimensão B

#### 4.5.1 Métricas Globais da Matriz de Confusão
* **True Positives ($TP$):** Pares positivos corretamente classificados como duplicata;
* **False Positives ($FP$):** Hard negatives incorretamente classificados como duplicata;
* **True Negatives ($TN$):** Hard negatives corretamente rejeitados;
* **False Negatives ($FN$):** Pares positivos incorretamente rejeitados;
* **Precision:** $\frac{TP}{TP + FP}$;
* **Recall:** $\frac{TP}{TP + FN}$;
* **F1-Score:** $\frac{2 \cdot \text{Precision} \cdot \text{Recall}}{\text{Precision} + \text{Recall}}$;
* **FP Reduction ($\Delta FP$):** $FP(B_0) - FP(B_k)$ (falsos positivos suprimidos);
* **Positive Recall Loss ($\Delta \text{Recall}_P$):** $\text{Recall}_P(B_0) - \text{Recall}_P(B_k)$ (perda de recall positivo — meta prioritária de controle: **$\Delta \text{Recall}_P = 0$**).

#### 4.5.2 Métricas por Modo de Falha Empírico (FM-1 a FM-4)

$$\text{FP\_Suppression\_Rate}(\text{FM}_i) = \frac{FP_{\text{suprimidos}}(\text{FM}_i)}{FP_{\text{total}}(\text{FM}_i)}$$

| Modo de Falha Empírico | Universo T02 | Casos Alvo | Intervenção Direta Primária | Meta Específica |
|---|:---:|---|:---:|:---:|
| **FM-1: Divergência Dimensional** | 4 FP | `CASE-005`, `CASE-013`, `CASE-029`, `CASE-037` | $B_2$ | $FP_{\text{FM-1}} = 0/4$ |
| **FM-2: Divergência de Material** | 4 FP | `CASE-006`, `CASE-014`, `CASE-030`, `CASE-038` | $B_3$ | $FP_{\text{FM-2}} = 0/4$ |
| **FM-3: Variante Construtiva/Montagem** | 5 FP | `CASE-007`, `CASE-015`, `CASE-023`, `CASE-031`, `CASE-039` | $B_4$ | $FP_{\text{FM-3}} = 0/5$ |
| **FM-4: Subtipo / Princípio Físico** | 4 FP | `CASE-008`, `CASE-016`, `CASE-024`, `CASE-032` | $B_5$ | $FP_{\text{FM-4}} = 0/4$ |

---

## 5. Controles Experimentais de Causalidade e Não-Interferência

### 5.1 Regra de Independência Estrita entre A e B
1. **Não-simultaneidade na primeira intervenção:** $A_1$ e as intervenções $B_k$ **NUNCA** devem ser testadas simultaneamente na primeira rodada de observação.
2. **Isolamento de Causa:** Se $A$ e $B$ fossem combinados simultaneamente, seria impossível determinar se uma variação métrica decorre da recuperação de candidatos (Candidate Selection) ou da supressão de falsos positivos (Detector).

### 5.2 Regra de Blindagem do Challenge Set de B
* Nas avaliações da Dimensão B, o conjunto de pares submetido ao detector deve ser **estritamente idêntico** ao conjunto avaliado na T02:
  - Avaliação incondicional: todos os 40 pares congelados da Tranche 02;
  - Avaliação condicionada: os 39 pares retidos pelo Candidate Selection original da T02.
* A Dimensão B **NÃO PODE** incorporar nenhuma alteração de Candidate Selection ou recuperação de `CASE-002`.

### 5.3 Regra de Preservação dos Dados Congelados
* O catálogo CSV (`draft_tranche_02_catalog.csv`), o Ground Truth (`draft_tranche_02_ground_truth.json`) e o manifesto (`draft_tranche_02_manifest.json`) permanecem com seus hashes SHA-256 congelados inalterados.
* Nenhum par de teste será adicionado, removido ou modificado.
* O status de congelamento `freeze_state = FROZEN` (`freeze_sha256 = 052bd6fec3f165cea9cdbf686cb961af4eccf962f4689d938a00fdc459b92008`) deve ser verificado antes de qualquer leitura.

### 5.4 Regra de Blindagem do Repositório do Produto
* Todo código experimental para intervenções controladas deve residir estritamente no diretório de experimentos (`experiments/`).
* Os pacotes de produção em `src/agent_lab/` e os testes de regressão do produto em `tests/` permanecem **estritamente inalterados**.

---

## 6. Síntese Comparativa dos Protocolos Experimentais Propostos

| Propriedade Metodológica | Dimensão A (Candidate Selection Sensitivity) | Dimensão B (Conflicting Signals in Route 2) |
|---|---|---|
| **Alvo Empírico Central** | 1 Positive Dropped (`CASE-SR001-B-T02-002`) | 17 False Positives da Rota 2 |
| **Pergunta Científica** | Que classe mínima de equivalência lexical evita o descarte sem causar explosão de candidatos? | Sinais conflitantes pré-existentes suprimem falsos positivos sem sacrificar recall positivo? |
| **Estatuto Epistemológico** | Probe post-hoc de sensibilidade local (sem pretensão de generalização) | Caracterização controlada de sinais candidatos (sem política de veto em produção) |
| **Variáveis Manipuladas** | Projeção focal de equivalência de `category_token` ($A_1$) | Sinais de PN ($B_1$), dimensão ($B_2$), material ($B_3$), variante ($B_4$), subtipo ($B_5$) |
| **Ponto de Aplicação** | Indexação de Família 2 em Candidate Selection | Regra heurística da Rota 2 no Detector Downstream |
| **Forma de Aplicação** | Hook injetável no harness experimental segregado | Decorador/função de avaliação experimental segregada |
| **Avaliação Primária** | Isolada sobre os 40 pares congelados | Isolada ($B_1..B_5$) e Cumulativa ($B_{1..5}$) |
| **Métricas Primárias** | Candidate Recall, Retained Positives, CRR | Precision, Recall, F1, $\Delta FP$, Positive Recall Loss, FM-1..4 |
| **Controle de Confundimento** | Detector mantido idêntico ao original T02 | Candidate Selection mantido idêntico ao original T02 |
| **Risco Principal Monitorado**| Aumento indesejado do candidate-space | Sacrifício acidental de True Positives ($\Delta \text{Recall}_P > 0$) |

---

## 7. Status de Governança e Próximos Passos

### 7.1 Declaração Explícita de Não-Execução
> [!IMPORTANT]
> **ESTA ESPECIFICAÇÃO É ESTRITAMENTE DOCUMENTAL.**
> - NENHUM experimento de intervenção foi executado.
> - NENHUMA run foi iniciada.
> - NENHUMA alteração foi realizada em `src/agent_lab/`, `tests/` ou nos artefatos FROZEN da Tranche 02.
> - O status formal deste documento é: `PROPOSED / NOT YET EXECUTED`.

### 7.2 Pré-requisitos para Qualquer Execução Futura
Qualquer transição deste desenho para implementação de harness ou execução experimental requer:
1. Revisão humana detalhada desta especificação;
2. Emissão de novo **`HUMAN GO`** explícito, determinando qual das dimensões ($A$ ou $B$) terá seu instrumental experimental implementado e avaliado em primeiro lugar;
3. Planejamento do registro de custódia e checkpoints correspondentes.
