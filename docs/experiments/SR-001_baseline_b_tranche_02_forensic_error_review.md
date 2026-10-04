# SR-001 Baseline B — Tranche 02: Registro da Análise Forense de Erros e Deliberação Científica

> Documento de custódia e registro analítico da inspeção forense somente-leitura (*read-only*)
> dos 18 casos divergentes observados na primeira execução cega da Tranche 02 do Baseline B
> (SR-001 / Issue #158 / Run ID `RUN-T02-20261003T130713Z-5D78EB04`), realizada em sessão de 04/10/2026.

---

## 1. Metadados da Sessão Forense

| Campo | Valor |
|---|---|
| **Investigação Experimental** | `SR-001 / Scale Reconnaissance v1` (Pressão Arquitetural P-07) |
| **Componente Auditado** | `Baseline B — Tranche 02 (Primeira Observação observed-as-run)` |
| **Data da Auditoria Forense** | `2026-10-04` |
| **Tipo de Acesso** | Estritamente somente-leitura (*read-only*), zero mutação em código/dados |
| **Git HEAD de Execução Original** | `973eadb019289fb002aa4022a494663a24edd243` |
| **Run ID sob Análise** | `RUN-T02-20261003T130713Z-5D78EB04` |
| **Arquivo de Evidência Base** | [`experiments/evidence/sr001_baseline_b_tranche_02_first_observation.json`](file:///C:/Users/Administrador/agent-lab-pascoal/experiments/evidence/sr001_baseline_b_tranche_02_first_observation.json) |
| **SHA-256 da Evidência Base (LF)** | `311b680e3d4c76c11ea11ea5c7dac8bcca6593f6f48b7c2d5a29135b61f7853c` |
| **Documento de Custódia T02** | [`docs/experiments/SR-001_baseline_b_tranche_02_first_observation.md`](file:///C:/Users/Administrador/agent-lab-pascoal/docs/experiments/SR-001_baseline_b_tranche_02_first_observation.md) |
| **Universo Auditado** | 18 casos divergentes: 1 Positive Dropped (CS) e 17 Falsos Positivos (Detector) |

---

## 2. Rigor Epistemológico e Convenções Conceituais

Em conformidade com a governança científica do projeto Agent Lab Pascoal:

$$\text{OBSERVAÇÃO EMPÍRICA} \quad \neq \quad \text{HIPÓTESE CAUSAL PRELIMINAR} \quad \neq \quad \text{PROPOSTA DE MUDANÇA}$$

* **Não registrar "causa provada":** toda inferência explicativa é classificada estritamente como *hipótese causal preliminar* ou *evidência consistente com*;
* **Mecanismos observados:** representam comportamentos e ramificações de código diretamente demonstráveis pelos artefatos preservados;
* **Testagem causal:** qualquer validação de causalidade requer intervenção experimental controlada futura;
* **Estrutura dos erros:** evita-se alegação formal de não-aleatoriedade estatística estrita (pois nenhum teste de hipótese de aleatoriedade foi rodado). A formulação canônica adotada é:
  > *“Os erros da T02 apresentam forte estrutura recorrente e são inconsistentes com uma interpretação de falhas puramente dispersas ou heterogêneas dentro desta tranche.”*

---

## 3. Análise Detalhada do Descarte de Positivo (`CASE-SR001-B-T02-002`)

### 3.1 Reconstrução do Fluxo de Execução

```text
Ground Truth: Positivo (is_duplicate = True)
  │
  ├─ Registro A (MAT-SR001-B-T02-002A):
  │    - Fabricante: "CISER"
  │    - Part Number: "B7-075-150"
  │    - Descrição Curta: "PRISIONEIRO ROSCA CONTINUA ASTM A193 B7 3/4 POL X 150 MM"
  │    - Grupo Material: "FIXADORES"
  │    - Normalização:
  │         * Chave Família 1: ("B7 075 150", "CISER")
  │         * Category Token: "PRISIONEIRO" (primeiro token normalizado não-ignorado)
  │         * Chave Família 2: ("FIXADORES", "PRISIONEIRO")
  │
  ├─ Registro B (MAT-SR001-B-T02-002B):
  │    - Fabricante: "" (vazio no catálogo CSV)
  │    - Part Number: "" (vazio no catálogo CSV)
  │    - Descrição Curta: "ESTOJO PRISIONEIRO ASTM A193 B7 3/4 X 150 MM"
  │    - Grupo Material: "FIXADORES"
  │    - Normalização:
  │         * Chave Família 1: None (ambos os campos vazios; regra exige ambos não-vazios)
  │         * Category Token: "ESTOJO" (primeiro token normalizado não-ignorado)
  │         * Chave Família 2: ("FIXADORES", "ESTOJO")
  │
  ├─ Candidate Selection (extract_candidate_family_keys & evaluate_candidate_selection):
  │    * Família 1 match: False (chave nula em B)
  │    * Família 2 match: False ("PRISIONEIRO" != "ESTOJO")
  │    * is_candidate: False
  │    * Desfecho: POSITIVE_DROPPED (Falso Negativo do Filtro de Bloqueio)
  │
  └─ Confronto com Detector Incondicional (is_possible_duplicate):
       * Rota 1 (PN + Fabricante): False (campos vazios em B)
       * Rota 2 (Grupo + Category Token): Grupo coincide ("FIXADORES"), porém:
         if category_token(incoming_description) != category_token(existing_description):
             return False
         Retornou False na linha 47 ("PRISIONEIRO" != "ESTOJO").
       * Desfecho incondicional registrado: unconditioned_detector_prediction = False (FN)
```

### 3.2 Fatos Observados e Hipóteses Causais

* **Fato Observado 1:** O descarte do par no Candidate Selection decorreu cumulativamente de:
  1. Ausência de part number e fabricante estruturados no Registro B, inviabilizando a rota da Família 1;
  2. Divergência no primeiro token não-ignorado da descrição (`PRISIONEIRO` vs `ESTOJO`), inviabilizando a rota da Família 2.
* **Fato Observado 2:** O detector determinístico atual downstream também falhou com Falso Negativo sobre este par na avaliação incondicional, exatamente pela mesma restrição de igualdade do primeiro substantivo léxico.
* **Hipótese Causal Preliminar:** A dependência estrutural do blocking e do detector em relação à primeira palavra da descrição curta os torna vulneráveis a variações vocabulares sinônimas comuns na indústria de suprimentos (ex.: *"estojo prisioneiro"* vs *"prisioneiro"*), especialmente quando há omissão de metadados de fabricante.

---

## 4. Análise Sistemática dos 17 Falsos Positivos do Detector

### 4.1 Mecanismo Algorítmico Recorrente Observado
Em **17 de 17 casos** (100% dos falsos positivos observados na T02):
1. **Candidate Selection:** O par foi retido **exclusivamente via Família 2** (`matched_families = ['FAMILY_2']`). Em nenhum caso a Família 1 casou;
2. **Part Numbers Divergentes:** Em todos os 17 casos, ambos os materiais possuíam part numbers estruturados preenchidos e diferentes entre si no catálogo;
3. **Detector — Rota 1 (PN + Fabricante):** Avaliou `False` devido à divergência dos part numbers;
4. **Detector — Rota 2 (Grupo + Category Token + Heurística Numérica/Lexical):**
   * Grupos normatizados coincidiram (`normalize_text(group_a) == normalize_text(group_b)`);
   * Category tokens coincidiram (`category_token(desc_a) == category_token(desc_b)`);
   * Compartilhamento numérico: todos satisfizeram $\ge 2$ números compartilhados (`len(shared_numbers) >= 2`);
   * Compartilhamento léxico: todos satisfizeram $\ge 1$ palavra compartilhada (`len(shared_words) >= 1`);
   * **Resultado:** O detector predisse `is_possible_duplicate = True` (Falso Positivo).
5. **Ausência Observada de Veto:** O detector determinístico atual **não possui nenhum mecanismo** que interprete a divergência de part number, números dimensionais excludentes ou palavras técnicas antagônicas como veto ou penalidade à duplicidade na Rota 2.

---

### 4.2 Tabela Analítica dos 17 Falsos Positivos

| Case ID | Estrato | Família | PNs (A vs B) | Cat Token | Números Compartilhados | Qtd Palavras Comuns | Palavras / Sinais Conflitantes Presentes nos Dados |
|---|---|:---:|---|---|---|:---:|---|
| `CASE-005` | `FASTENERS` | `HN-DIM` | `931-12-060` vs `931-12-070` | `PARAFUSO` | `12`, `30`, `8`, `931` (4) | 13 | Comprimento nominal: `60` no A vs `70` no B (`M12X60` vs `M12X70`) |
| `CASE-006` | `FASTENERS` | `HN-MAT` | `933-08-025-88` vs `933-08-025-A4` | `PARAFUSO` | `25`, `8`, `933` (3) | 9 | Metalurgia: `CARBONO`, `ZB` vs `A4`, `INOXIDAVEL`, `AISI`, `316` |
| `CASE-007` | `FASTENERS` | `HN-VAR` | `975-M20-STD` vs `976-M20-FINO` | `BARRA` | `1`, `1000`, `20`, `5`, `8` (5) | 13 | Passo de rosca: `NORMAL`, `2.5` mm vs `FINO`, `1.5` mm (`DIN 975` vs `DIN 976`) |
| `CASE-008` | `FASTENERS` | `HN-DISTINCT` | `AD-616` vs `AK-616` | `REBITE` | `16`, `4`, `8` (3) | 13 | Geometria de cabeça: `ABAULADA` (`ISO 15977`) vs `ESCAREADA` (`ISO 15978`) |
| `CASE-013` | `VALVES` | `HN-DIM` | `GT-150-WCB-080` vs `GT-150-WCB-100` | `VALVULA` | `150`, `16`, `216`, `34`, `8` (5) | 23 | Diâmetro nominal: `3 POL`, `80` mm vs `4 POL`, `100` mm |
| `CASE-014` | `VALVES` | `HN-MAT` | `FIG12-CI-050` vs `FIG16-CS-050` | `FILTRO` | `150`, `16`, `2`, `20`, `304`, `50` (6) | 23 | Material carcaça: `FERRO`, `CINZENTO`, `A126` vs `ACO`, `CARBONO`, `WCB`, `A216` |
| `CASE-015` | `VALVES` | `HN-VAR` | `F150-FB-050` vs `F150-RB-050` | `VALVULA` | `150`, `16`, `2`, `216`, `34`, `50`, `8` (7) | 22 | Variante hidráulica: `FULL`, `PLENA` vs `REDUCED`, `REDUZIDA` (100% números comuns) |
| `CASE-016` | `VALVES` | `HN-DISTINCT` | `TD52-015` vs `FT14-015` | `PURGADOR` | `1`, `2` (2) | 11 | Princípio físico: `TERMODINAMICO`, `DISCO`, `TD52` vs `BOIA`, `TERMOSTATICA`, `FT14` |
| `CASE-023` | `BEARINGS` | `HN-VAR` | `22214-E` vs `22214-EK` | `ROLAMENTO` | `125`, `22214`, `31`, `70` (4) | 11 | Geometria furo: `CILINDRICO` vs `CONICO`, `BUCHA`, `CONICIDADE`, `EK` |
| `CASE-024` | `BEARINGS` | `HN-DISTINCT` | `H-311` vs `AHX-311` | `BUCHA` | `1`, `12`, `311`, `50` (4) | 6 | Função mecânica oposta: `FIXACAO`, `APERTO`, `H` vs `DESMONTAGEM`, `EXTRACAO`, `AHX` |
| `CASE-029` | `ELECTRICAL` | `HN-DIM` | `AFUMEX-16-AZ` vs `AFUMEX-25-AZ` | `CABO` | `0`, `1`, `2`, `5`, `6`, `90` (6) | 24 | Seção condutora: `16` mm² vs `25` mm² |
| `CASE-030` | `ELECTRICAL` | `HN-MAT` | `NBR5597-1POL-GF` vs `NBR5597-1POL-AL` | `ELETRODUTO` | `1`, `25`, `3`, `5597` (4) | 13 | Metalurgia/área: `CARBONO`, `FOGO`, `GALVANIZADO` vs `ALUMINIO`, `COPPER FREE`, `EX` |
| `CASE-031` | `ELECTRICAL` | `HN-VAR` | `PSS24-W/5` vs `PSS24-W/5-EX` | `FONTE` | `120`, `24`, `5` (3) | 13 | Certificação: padrão industrial vs `ATEX`, `EX`, `CONFORMAL COATING`, `VERNIZ` |
| `CASE-032` | `ELECTRICAL` | `HN-DISTINCT` | `060G1113` vs `060G1115` | `TRANSMISSOR` | `0`, `1`, `20`, `3000`, `4`, `43650` (6) | 24 | Faixa calibração: `0 A 10 BAR` vs `0 A 25 BAR` |
| `CASE-037` | `GENERAL` | `HN-DIM` | `B60` vs `B62` | `CORREIA` | `11`, `17` (2) | 18 | Comprimento primitivo: `60 POL` (`1524` mm) vs `62 POL` (`1575` mm) |
| `CASE-038` | `GENERAL` | `HN-MAT` | `DKB-0400-NBR` vs `DKB-0400-TPU` | `ANEL` | `10`, `40`, `50`, `7` (4) | 16 | Polímero: `BORRACHA`, `NBR`, `90 SHORE` vs `POLIURETANO`, `TPU`, `95 SHORE` |
| `CASE-039` | `GENERAL` | `HN-VAR` | `913-CG-3-150` vs `913-CGI-3-150` | `JUNTA` | `150`, `16`, `20`, `3`, `304` (5) | 15 | Estilo construtivo: `CG` (apenas anel externo) vs `CGI` (com anel interno anti-colapso) |

---

## 5. Taxonomia Emergente dos Modos de Falha

A partir do confronto sistemático entre as especificações dos materiais e as decisões do detector, os 17 falsos positivos agrupam-se estritamente em **quatro modos empíricos de falha**, unificados pelo super-mecanismo da Rota 2:

### Modo FM-1: Divergência Dimensional Mascarada por Sobreposição Normativa
* **Frequência Observada:** 4 casos (23.53% dos 17 FP: `CASE-005`, `CASE-013`, `CASE-029`, `CASE-037`);
* **Evidência Observada:** Os pares apresentam divergência clara na dimensão principal (comprimento 60 vs 70 mm; diâmetro nominal 3" vs 4"; seção 16 vs 25 mm²; comprimento 60" vs 62"), mas compartilham números acessórios decorrentes de normas técnicas padronizadas (DIN 931, ASME B16.34, NBR 5597, classe 150#, tensão 1kV);
* **Hipótese Causal:** O extrator numérico extrai todos os numerais de forma agnóstica, e a regra `len(shared_numbers) >= 2` é facilmente satisfeita por números normativos compartilhados, mesmo quando os números dimensionais principais colidem;
* **Nível de Confiança:** **ALTO**.

### Modo FM-2: Divergência de Materialidade (Metalúrgica / Polimérica) sob Mesma Geometria
* **Frequência Observada:** 4 casos (23.53% dos 17 FP: `CASE-006`, `CASE-014`, `CASE-030`, `CASE-038`);
* **Evidência Observada:** A geometria e as dimensões nominais são idênticas (parafuso M8x25; filtro DN 50; eletroduto 1"x3m; raspador 40x50x7), fornecendo de imediato os números e palavras exigidos pelo detector. A divergência reside exclusivamente na especificação do material (Aço carbono vs Inox; Ferro cinzento vs Aço fundido; Aço galvanizado vs Alumínio; Borracha nitrílica vs Poliuretano);
* **Hipótese Causal:** O detector não possui representação de termos de materiais incompatíveis, e a regra `len(shared_words) >= 1` aceita a duplicidade ignorando palavras materiais conflitantes;
* **Nível de Confiança:** **ALTO**.

### Modo FM-3: Variante Construtiva / Montagem Crítica sob Mesma Especificação Base
* **Frequência Observada:** 5 casos (29.41% dos 17 FP: `CASE-007`, `CASE-015`, `CASE-023`, `CASE-031`, `CASE-039`);
* **Evidência Observada:** Materiais compartilham a aplicação industrial básica e grandezas nominais, mas apresentam modificadores construtivos críticos (passo normal vs fino; passagem plena vs reduzida; furo cilíndrico vs cônico; padrão vs ATEX; junta sem anel interno vs com anel interno);
* **Hipótese Causal:** Em casos como `CASE-015` e `CASE-039`, 100% dos números coincidem entre os textos. Como o detector não penaliza a presença de tokens modificadores exclusivos, a densidade de palavras comuns domina a decisão;
* **Nível de Confiança:** **ALTO**.

### Modo FM-4: Subtipo / Princípio Físico Oposto sob Mesma Categoria Lexical
* **Frequência Observada:** 4 casos (23.53% dos 17 FP: `CASE-008`, `CASE-016`, `CASE-024`, `CASE-032`);
* **Evidência Observada:** Materiais pertencem ao mesmo substantivo técnico inicial (`REBITE`, `PURGADOR`, `BUCHA`, `TRANSMISSOR`), mas desempenham papéis mecânicos opostos (fixação vs desmontagem), termodinâmicos distintos (purga por disco vs boia contínua) ou faixas de medição incompatíveis (0-10 vs 0-25 bar);
* **Hipótese Causal:** O substantivo inicial (`category_token`) é genérico demais para distinguir subtipos funcionais quando há conexões ou modelos compartilhados (1/2" NPT, 4-20mA, MBS 3000);
* **Nível de Confiança:** **ALTO**.

---

## 6. Matriz Resumo Quantitativa dos Falsos Positivos

*(Nota: O caso `CASE-SR001-B-T02-002` não integra esta matriz por constituir falha de Candidate Selection e não Falso Positivo do detector).*

| Modo de Falha Empírico | Quantidade | % dos 17 FP | Case IDs Envolvidos | Estratos Industriais | Famílias de Perturbação | Confiança |
|---|:---:|:---:|---|---|---|:---:|
| **FM-1: Divergência Dimensional** | 4 | 23.53% | `CASE-005`, `CASE-013`, `CASE-029`, `CASE-037` | `FASTENERS`, `VALVES`, `ELECTRICAL`, `GENERAL` | `HN-DIM` (F7) | **ALTO** |
| **FM-2: Divergência de Material** | 4 | 23.53% | `CASE-006`, `CASE-014`, `CASE-030`, `CASE-038` | `FASTENERS`, `VALVES`, `ELECTRICAL`, `GENERAL` | `HN-MAT` (F8) | **ALTO** |
| **FM-3: Variante Construtiva/Montagem** | 5 | 29.41% | `CASE-007`, `CASE-015`, `CASE-023`, `CASE-031`, `CASE-039` | `FASTENERS`, `VALVES`, `BEARINGS`, `ELECTRICAL`, `GENERAL` | `HN-VAR` (F9) | **ALTO** |
| **FM-4: Subtipo / Princípio Físico** | 4 | 23.53% | `CASE-008`, `CASE-016`, `CASE-024`, `CASE-032` | `FASTENERS`, `VALVES`, `BEARINGS`, `ELECTRICAL` | `HN-DISTINCT` (F10) | **ALTO** |
| **TOTAL** | **17** | **100.0%** | *(17 pares avaliados)* | *(5/5 estratos atingidos)* | *(4/4 famílias de HN)* | — |

---

## 7. Padrões por Estrato Industrial e Inspeção dos Verdadeiros Negativos (TNs)

### 7.1 Distribuição por Estrato

| Estrato Industrial | Total HNs | Falsos Positivos | Verdadeiros Negativos | Taxa de FP Observada |
|---|:---:|:---:|:---:|:---:|
| **`FASTENERS`** | 4 | 4 | 0 | **100.0%** |
| **`VALVES`** | 4 | 4 | 0 | **100.0%** |
| **`ELECTRICAL`** | 4 | 4 | 0 | **100.0%** |
| **`GENERAL`** | 4 | 3 | 1 (`CASE-040`) | **75.0%** |
| **`BEARINGS`** | 4 | 2 | 2 (`CASE-021`, `CASE-022`) | **50.0%** |

### 7.2 Inspeção Forense dos 3 Casos de Sucesso (Verdadeiros Negativos)
Para verificar se o detector apresentou capacidade discriminativa semântica em algum ponto da amostra, foram inspecionados os 3 únicos casos classificados como `TN`:
1. **`CASE-SR001-B-T02-021` (`BEARINGS` / `6305` vs `6306`):**
   * Números compartilhados: apenas `{'6300'}` (contagem = 1);
2. **`CASE-SR001-B-T02-022` (`BEARINGS` / `SBR20UU` vs `SBR20UU-SS`):**
   * Números compartilhados: apenas `{'20'}` (contagem = 1);
3. **`CASE-SR001-B-T02-040` (`GENERAL` / Mangueira Água vs Óleo Combustível):**
   * Números compartilhados: apenas `{'2'}` (contagem = 1).

* **Constatação Fundamental Preservada:**
  Em todos os três casos de Verdadeiro Negativo, a decisão `is_possible_duplicate = False` ocorreu **exclusivamente porque a contagem de números compartilhados ficou abaixo do threshold** (`len(shared_numbers) < 2`). Não há evidência nesta Tranche de que o detector tenha discriminado semanticamente as diferenças físicas (cotas de contorno, tipo de aço inoxidável ou compatibilidade química de borracha).

---

## 8. Padrões por Família de Perturbação (F7–F10)

| Família de Perturbação | Taxonomia Industrial | Avaliados | Falsos Positivos | Verdadeiros Negativos | Taxa de FP |
|---|---|:---:|:---:|:---:|:---:|
| **`F7: HN-DIM`** | Divergência de cota dimensional crítica | 5 | 4 | 1 (`CASE-021`) | **80.0%** |
| **`F8: HN-MAT`** | Divergência metalúrgica / composição de material | 5 | 4 | 1 (`CASE-022`) | **80.0%** |
| **`F9: HN-VAR`** | Variante técnica / funcional / montagem | 5 | 5 | 0 | **100.0%** |
| **`F10: HN-DISTINCT`** | Produto / princípio físico distinto sob mesma categoria | 5 | 4 | 1 (`CASE-040`) | **80.0%** |

* **Constatação:** A família **`F9: HN-VAR`** registrou 100% de falsos positivos (5 de 5 pares classificados como duplicata), evidenciando que variantes de segurança ou montagem são totalmente transparentes às heurísticas atuais.

---

## 9. Formulação Canônica e Avaliação da Estrutura dos Erros

Em substituição a alegações estatísticas sobre aleatoriedade não-testadas formalmente:

> **Formulação Canônica Adotada:**  
> *“Os erros observados na primeira execução da Tranche 02 apresentam forte estrutura recorrente e são inconsistentes com uma interpretação de falhas puramente dispersas ou heterogêneas dentro desta tranche.”*

### Elementos Comprobatórios dessa Estrutura:
1. Em 100% dos 17 falsos positivos, a decisão originou-se exatamente do mesmo caminho determinístico na Rota 2;
2. Em 100% dos 17 falsos positivos, havia part numbers divergentes explícitos não aproveitados pelo detector;
3. O comportamento permissivo da Rota 2 manifestou-se de forma consistente nos cinco estratos industriais avaliados;
4. O único falso negativo de Candidate Selection (`CASE-002`) obedeceu à mesma rigidez sintática observada na Rota 2 downstream.

---

## 10. Próxima Âncora Proposta (Não Autorizada)

> [!IMPORTANT]
> **ESTE CLOSEOUT É ESTRITAMENTE DOCUMENTAL.**  
> Nenhuma das ações abaixo está autorizada neste momento.

A próxima âncora proposta para o projeto consiste em:
* **Deliberação humana sobre o desenho de uma intervenção experimental mínima e controlada**, destinada a testar separadamente em experimentos futuros:
  * **Dimensão A:** Sensibilidade do Candidate Selection a equivalências lexicais e normalização flexível do `category_token`;
  * **Dimensão B:** Impacto da introdução de sinais negativos/conflitantes (part numbers divergentes e atributos excludentes) na Rota 2 do detector.

### Vedações Mantidas:
* **NÃO** escolher solução técnica antecipadamente;
* **NÃO** implementar dicionário de sinônimos;
* **NÃO** introduzir veto de part number em código de produção;
* **NÃO** alterar thresholds numéricos;
* **NÃO** criar nova rota no detector;
* **NÃO** reexecutar a Tranche 02;
* **NÃO** criar Tranche 03 sem novo HUMAN GO explícito.
