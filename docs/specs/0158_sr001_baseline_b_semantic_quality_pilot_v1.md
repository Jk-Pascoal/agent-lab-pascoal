# SPEC-0158 — SR-001 Baseline B: Semantic Quality Exploratory Pilot Specification v1

> Especificação metodológica, taxonômica e experimental do piloto exploratório
> de 200 pares para avaliação da qualidade semântica de materiais (Baseline B)
> no âmbito da investigação experimental SR-001 (Issue #158).

---

## Metadados

| Campo | Valor |
|---|---|
| **Identificador** | `SPEC-0158` |
| **Status** | `PROPOSED` |
| **Issue relacionada** | `#158` |
| **Título da Issue** | `[SPIKE] Investigar escalabilidade da detecção de duplicidades sob carga industrial (Pressão P-07)` |
| **Investigação experimental** | `SR-001 / Scale Reconnaissance v1` |
| **Pressão arquitetural** | `P-07 (Industrial Load / Scale Validation)` |
| **Branch documental** | `docs/issue-158-baseline-b-pilot-spec` |
| **Responsável** | `Jk-Pascoal` |
| **Data de criação** | `2026-09-28` |
| **Última atualização** | `2026-09-28` |
| **Domínio** | Metrologia Experimental / Governança de Catálogo PDM/BOM |
| **Camada arquitetural** | Metrologia Experimental e Avaliação de Ground Truth |
| **Baseline de entrada** | `1194 testes aprovados` (100% GREEN) |
| **Impacto funcional** | `ZERO — investigação experimental sem impacto no Roadmap ou KPI da PoC v0.1.0` |
| **Runner oficial** | `python -m unittest discover -s tests -v` (Python 3.11) |

---

## 1. Contexto e Motivação Científica

### 1.1 Contexto e Evidência do Baseline A
A investigação experimental **SR-001 (Issue #158)** foi deflagrada sob a pressão arquitetural **P-07 (Industrial Load / Scale Validation)** para investigar o comportamento assintótico e computacional da governança de catálogo do Agent Lab Pascoal.

No **Baseline A (Capacidade Computacional e Blocking Teórico)**, consolidado em `docs/experiments/SR-001_scale_reconnaissance_v1.md`, foram obtidos os seguintes fatos canônicos observados no intervalo $N \in \{250, 500, 1000, 2000\}$:
- O tempo mediano de diagnóstico exaustivo dirigido ($N(N-1)$) escalou de $1.1653\,\text{s}$ ($N=250$) para $99.8750\,\text{s}$ ($N=2000$), com ajuste log-log empírico de expoente $p = 2.1626$, compatível com complexidade predominantemente quadrática;
- A análise estrutural da união de blocos candidatos teóricos ($P_1 \cup P_2$) demonstrou uma redução do espaço de comparação de **$\approx 99.09\%$ a $99.16\%$** (para $N=2000$, foram $1.999.000$ pares não-direcionados reduzidos para $16.887$ pares candidatos na união, com razão de candidatos de $0.8448\%$ e redução de $99.1552\%$);
- O consumo de memória monitorado via `tracemalloc` manteve pico contido em $2.65\,\text{MB}$ em $N=2000$.

### 1.2 A Lacuna Metrológica e a Necessidade do Baseline B
O Baseline A demonstrou que a união teórica dos blocos candidatos observados possui potencial estrutural de redução de aproximadamente $99.09\%$ a $99.16\%$ no intervalo medido ($N \in \{250, 500, 1000, 2000\}$), gerando uma ressalva obrigatória de preservação semântica:
$$\text{Candidate-Space Reduction} \neq \text{Semantic Recall Preservation}$$

A redução do espaço de candidatos é inadequada para a integridade do catálogo mestre se o mecanismo de poda descartar precocemente duplicatas materiais verdadeiras. A eventual eliminação de um par duplicado verdadeiro antes da análise detalhada constitui um **Falso Negativo Crítico**: se o *candidate blocking* for utilizado como gate, uma duplicata verdadeira removida do *candidate set* não será apresentada ao detector *downstream* naquela execução.

Portanto, faz-se estritamente necessário o **Baseline B (Qualidade Semântica)**.

### 1.3 Objetivos Primário e Secundário do Baseline B
1. **Objetivo Primário:**
   Medir a preservação semântica do espaço de candidatos produzido por uma hipótese de blocking, confrontando a decisão de pré-filtragem (`is_candidate`) contra um Ground Truth referencial independente e não-circular baseado na *Strict Material Identity Policy*.
2. **Objetivo Secundário e Complementar:**
   Caracterizar, após a retenção dos candidatos pelo blocking, o comportamento do detector heurístico existente na PoC (`is_possible_duplicate` em `src/agent_lab/duplicates.py`) sobre os casos de teste congelados.

### 1.4 Limites de Extrapolação
Esta especificação restringe-se aos dados observados e ao intervalo experimental controlado. **Nenhuma extrapolação operacional para catálogos industriais de 100k SKUs é autorizada** a partir deste documento.

---

## 2. Política de Identidade Material Cadastrável (Strict Material Identity Policy)

### 2.1 Definição Canônica
Para assegurar que o Ground Truth referencial possua semântica única, estável e auditável, adota-se a seguinte política:

> **Strict Material Identity Policy:**
> Dois registros de catálogo representam uma duplicata cadastral (`is_duplicate = True`) se, e somente se, ambos referenciam a **mesma identidade material cadastrável segundo todos os atributos identity-defining aplicáveis**.

### 2.2 Distinção Ontológica: Instância Física vs. Identidade Cadastrável
$$\text{Physical Instance} \neq \text{Material Identity}$$
- **Instância Física:** O objeto físico concreto estocado em uma posição específica do almoxarifado. Duas peças físicas distintas (ex.: dois parafusos em caixas separadas) são instâncias físicas diferentes.
- **Identidade Material Cadastrável:** A entidade formal de catálogo mestre que define o item. Se ambas as unidades físicas satisfazem aos mesmíssimos requisitos de especificação de engenharia, elas pertencem à mesma identidade cadastrável e constituem duplicata se cadastradas sob códigos mestres distintos.

### 2.3 Atributos Identity-Defining por Classe de Item
1. **Item Proprietário (Peça de Fabricante):**
   - Fabricante formal (`manufacturer`);
   - Código de peça do fabricante (`manufacturer_part_number`);
   - Revisão, variante ou sufixo funcional quando integrante da designação técnica;
   - Atributos técnicos críticos *identity-defining* complementares.
2. **Item Normatizado (Commodity / Peça Padronizada):**
   - Norma técnica de especificação dimensional e de produto (ex.: DIN 933, ISO 4017, ASME B16.5);
   - Dimensões nominais completas (diâmetro, passo, comprimento, espessura, diâmetro nominal DN);
   - Material de base e especificação metalúrgica exata (ex.: aço 8.8, inox A2-70, ASTM A216 WCB, ASTM A351 CF8M);
   - Classe de pressão nominal ou resistência mecânica (ex.: 150#, 300#, Classe 8.8, Classe 10.9);
   - Tolerâncias geométricas e folgas internas (ex.: folga radial Normal vs. C3);
   - Acabamento, tratamento térmico ou revestimento especificado (ex.: zincado branco, bicromatizado, polido);
   - Opções normativas relevantes (ex.: vedação de borracha 2RS vs. blindagem metálica ZZ).

*A norma técnica é apenas o sistema de referência; a identidade completa exige a conformidade de todos os atributos acima.*

### 2.4 Não-Equivalência: Intercambialidade vs. Duplicidade Cadastral
Fica formalmente vedado classificar como duplicata (`is_duplicate = True`):
- **Equivalência Técnica:** Materiais com propriedades semelhantes que desempenham a mesma função em projeto;
- **Intercambialidade Mecânica:** Peças que podem substituir fisicamente outras em manutenção (ex.: parafuso A4 substituindo A2);
- **Substituição Comercial:** Marcas homologadas concorrentes com part numbers distintos;
- **Materiais Semelhantes porém Distintos:** Itens de mesma família com divergência em qualquer cota dimensional, metalúrgica ou de folga interna.

Sob a *Strict Material Identity Policy*, todos esses casos devem receber obrigatoriamente:
$$\text{is\_duplicate} = \text{False}$$

### 2.5 Tratamento de Part Number: Representação Superficial vs. Divergência Semântica
- **Variação Superficial de Representação:** Presença, ausência ou troca de caracteres separadores (`-`, `/`, `.`, espaços) e variações de caixa (maiúsculas/minúsculas) que comprovadamente apontam para o mesmo código de catálogo do fabricante $\implies$ **preserva** `is_duplicate = True` (Classe `P-PN-FORMAT`).
- **Divergência Semântica de Part Number:** Alteração em caracteres alfanuméricos que representam variantes de modelo, revisões de hardware, tecnologias distintas ou fabricantes diferentes $\implies$ **implica** `is_duplicate = False` (Classe `HN-PN`).

### 2.6 Separação Tripartite dos Três Conceitos do Sistema
Para erradicar confusões entre fatos de engenharia, hipóteses do detector e filtros de escala, fixam-se:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. Ground Truth Referencial (ground_truth.py)                               │
│    is_duplicate: bool                                                       │
│    -> Fato auditável de catálogo segundo a Strict Material Identity Policy. │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ (Confrontado com)
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 2. Filtro de Candidatos / Blocking (Investigativo P-07)                      │
│    is_candidate: bool                                                       │
│    -> Decisão topológica de pré-filtragem para redução de pares O(N^2).     │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ (Se retido como candidato)
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 3. Detector Heurístico / Algorítmico (duplicates.py)                        │
│    is_possible_duplicate: bool                                              │
│    -> Hipótese diagnóstica downstream avaliada sobre o par retido.          │
└─────────────────────────────────────────────────────────────────────────────┘
```

Fica expressamente estabelecido que:
$$\text{is\_duplicate} \neq \text{is\_candidate} \neq \text{is\_possible\_duplicate}$$

O contrato de produção `DuplicatePairPrediction` (`src/agent_lab/ground_truth_evaluation.py`) destina-se exclusivamente à predição de duplicidade (`is_duplicate`) e **NÃO** deve ser utilizado para armazenar `is_candidate`.

---

## 3. Natureza e Metrologia do Piloto Exploratório (200 Pares)

### 3.1 Classificação e Finalidade do Piloto
O conjunto de 200 pares nominais é classificado formalmente como:
> `PILOTO EXPLORATÓRIO DE QUALIDADE SEMÂNTICA`

**Finalidade Estrita:**
- Revelar falhas estruturais grosseiras no candidate blocking;
- Identificar classes taxonômicas mais suscetíveis à geração de Falsos Negativos ($FN$);
- Validar na prática a viabilidade operacional do fluxo de anotação, freeze e auditoria humana;
- Calibrar o instrumental metrológico.

### 3.2 Limitações Estatísticas e Ressalva de Independência (Exchangeability)
O piloto **NÃO** constitui um benchmark estatístico conclusivo e **NÃO sustenta sozinho alegações de recall elevado ($\ge 99\%$)**.

**Fundamentação Metrológica:**
1. **Regra de Amostragem Binomial Ideal:**
   Sob a premissa de observações independentes e identicamente distribuídas (i.i.d.), para garantir $95\%$ de confiança estatística de que o recall seja de pelo menos $R$ na ausência de falsos negativos ($k=0$):
   $$n \ge \frac{\ln(0.05)}{\ln(R)}$$
   - Para $R \ge 0.95 \implies n \approx 59$ positivos;
   - Para $R \ge 0.99 \implies n \approx 299$ positivos;
   - Para $R \ge 0.995 \implies n \approx 598$ positivos.
   *Esses valores atuam estritamente como referências nominais de custo amostral sob hipótese ideal de independência.*
2. **Efeito de Correlação Intraclasse (Cluster Correlation):**
   Pares gerados a partir de perturbações da mesma identidade material base ou pertencentes à mesma família técnica exibem correlação interna. Dez casos derivados de uma mesma família de parafusos não equivalem a 10 observações independentes; o tamanho amostral efetivo ($n_{\text{eff}}$) é inferior.
3. **Status dos 100 Positivos do Piloto:**
   Com 100 positivos nominais, mesmo com zero falhas, o limite inferior de confiança binomial ideal cobre apenas $R \approx 97\%$. Havendo correlação interna, a cobertura real é menor. Portanto, é vedado extrair alegações de "recall $\ge 99\%$ comprovado" a partir exclusivamente deste piloto.

---

## 4. Estratos, Famílias, Taxonomias e Templates

### 4.1 Estratos Industriais Selecionados
Para assegurar diversidade técnica sem reivindicar representatividade universal da indústria global, selecionam-se 5 estratos industriais:
1. **Fixadores & Parafusos**
2. **Tubulação & Válvulas**
3. **Rolamentos & Mancais**
4. **Elétrica & Instrumentação**
5. **Diversos & Consumíveis**

Cada estrato conterá nominalmente **40 pares** (20 positivos e 20 hard negatives), totalizando os 200 pares do piloto.

### 4.2 Famílias Base Candidatas por Estrato
Cada estrato deverá ser composto por no mínimo **5 famílias tecnicamente distintas** e ao menos **10 identidades materiais base distintas**:
- **Fixadores:** Parafuso sextavado DIN 933, Parafuso Allen DIN 912, Porca sextavada DIN 934, Arruela cunha Nord-Lock, Prisioneiro ASTM A193 B7.
- **Tubulação & Válvulas:** Válvula de esfera ASME B16.34, Válvula de retenção ASME B16.10, Flange Welding Neck ASME B16.5, Curva Butt-Weld ASME B16.9, União forjada ASME B16.11.
- **Rolamentos & Mancais:** Rolamento rígido de esferas série 6200, Rolamento autocompensador de rolos 22200, Rolamento cônico série 32200, Caixa de mancal SNL 500, Bucha de fixação H200.
- **Elétrica & Instrumentação:** Motor elétrico de indução trifásico, Sensor fotoelétrico óptico, Transmissor de pressão 4-20 mA HART, Contator tripolar de potência, Disjuntor-motor termomagnético.
- **Diversos & Consumíveis:** Correia de transmissão em V, Elemento filtrante hidráulico, Retentor radial para eixos DIN 3760, Junta espirometálica ASME B16.20, Mangueira hidráulica de alta pressão SAE 100 R2AT.

**Teto Amostral:** No máximo **4 pares derivados da mesma identidade material base**.

### 4.3 Taxonomia Positiva ($P$) — Target de Preservação de Identidade
Pares onde a *Strict Material Identity* é integralmente preservada (`is_duplicate = True`):

| Classe | Intenção da Perturbação | Atributos Mutáveis na Superfície | Atributos Identity-Defining Invariantes |
| :--- | :--- | :--- | :--- |
| **P-ABBR** | Abreviações técnicas consagradas em suprimentos | Descrição textual com contrações conhecidas (`PARAF`, `SEXT`, `RET`) | Dimensões, normas, materiais, part numbers e classes de pressão |
| **P-WORD-ORDER** | Inversão sintática de tokens descritivos | Posição relativa de cláusulas e substantivos/adjetivos | Todos os tokens substantivos e modificadores dimensionais |
| **P-PN-FORMAT** | Variação superficial de formato de part number | Delimitadores (`-`, `/`, `.`), espaços e caixa em PN oficial | Sequência de caracteres alfanuméricos, sufixos de variantes e fabricante |
| **P-UNIT-SYN** | Sinonímia estrita de contagem unitária | Campo `unit` variando exclusivamente entre $\{ \text{UN}, \text{PC}, \text{PÇA} \}$ | Toda a especificação física e ausência de múltiplos/embalagens |
| **P-NOISE** | Ruído tipográfico leve não crítico | Distância Levenshtein = 1 em substantivos comuns | Invariância total em números, normas, códigos e ligas metálicas |

### 4.4 Taxonomia Hard Negative ($HN$) — Target de Discriminação
Pares onde a similaridade léxica é deliberadamente alta, mas a *Strict Material Identity* é violada em pelo menos um atributo essencial (`is_duplicate = False`):

| Classe | Atributo Violado | Elementos Deliberadamente Semelhantes | Mecanismo de Indução a Erro |
| :--- | :--- | :--- | :--- |
| **HN-DIM** | Cota dimensional crítica | Mesma norma, material, acabamento e fabricante | Alta sobreposição de tokens, divergindo em 1 número dimensional |
| **HN-MAT** | Especificação metalúrgica / liga | Mesma norma dimensional, DN, classe de pressão | Manutenção de dimensões idênticas com ligas distintas (ex.: WCB vs CF8M) |
| **HN-VAR** | Variante de projeto / folga / vedação | Mesmo modelo base, série e diâmetros | Sufixos de engenharia ignorados por tokenizadores (ex.: 2RS vs ZZ vs C3) |
| **HN-UNT** | Entidade física: Peça vs. Conjunto | Descrição idêntica da peça principal | Conjunto montado repete o nome da peça individual (ex.: UN vs CJ/KIT) |
| **HN-PN** | Código de modelo / sufixo funcional | Mesma família e fabricante | Part numbers com distância de 1 caractere alfanumérico crítico |

### 4.5 Matriz de Cobertura: Target de Balanceamento e Regras de Flexibilidade
A matriz $5 \times 5$ (4 pares nominais por célula) constitui um **TARGET DE BALANCEAMENTO**, e **NÃO UMA OBRIGAÇÃO ABSOLUTA**:

```
                       Matriz Alvo de Balanceamento
┌───────────────────────────┬───────────────────────────────────┐
│ Positivos (100 Pares)     │ Hard Negatives (100 Pares)        │
│ 5 Classes x 5 Estratos    │ 5 Classes x 5 Estratos            │
│ Target: 4 pares / célula  │ Target: 4 pares / célula          │
└───────────────────────────┴───────────────────────────────────┘
```

**Princípio de Flexibilidade Técnica Auditável:**
- É expressamente proibido conceber exemplos artificiais, inverossímeis ou forçados apenas para preencher uma célula da matriz;
- Se uma determinada combinação (ex.: `P-PN-FORMAT` em fixadores estritamente normatizados sem fabricante, ou `HN-UNT` em famílias onde conjuntos montados não existem industrialmente) não for tecnicamente natural:
  1. Registrar formalmente a incompatibilidade de domínio na documentação de anotação;
  2. Redistribuir a quantidade de pares para outra combinação do mesmo estrato e mesmo rótulo ($P$ ou $HN$);
  3. Preservar rigorosamente o total de 20 positivos e 20 hard negatives por estrato e a presença de todas as classes taxonômicas no cômputo global;
  4. Toda redistribuição deve ser expressamente justificada no manifesto.

### 4.6 Exemplos Textuais Ilustrativos
*Os exemplos abaixo são estritamente ilustrativos para demonstrar o conceito taxonômico. Eles NÃO constituem casos automaticamente aprovados do Ground Truth futuro:*
- *Exemplo P-ABBR:* `PARAFUSO SEXTAVADO DIN 933 M10X30 AÇO 8.8 ZINCADO` vs. `PARAF SEXT DIN933 M10 X 30 AC 8.8 ZB` $\implies$ `is_duplicate = True`.
- *Exemplo HN-DIM:* `PARAFUSO SEXTAVADO DIN 933 M10X30 AÇO 8.8 ZINCADO` vs. `PARAFUSO SEXTAVADO DIN 933 M10X40 AÇO 8.8 ZINCADO` $\implies$ `is_duplicate = False`.
- *Exemplo HN-MAT:* `VALVULA ESFERA FLANGEADA DN 50 CLASSE 150 CORPO WCB` vs. `VALVULA ESFERA FLANGEADA DN 50 CLASSE 150 CORPO CF8M` $\implies$ `is_duplicate = False`.

---

## 5. Metadados e Experimental Challenge Manifest

### 5.1 Desacoplamento Arquitetural de Contratos
Os contratos estáveis de produção e avaliação:
- `DuplicatePairGroundTruth` (`src/agent_lab/ground_truth.py`)
- `DuplicatePairGroundTruthDataset` (`src/agent_lab/ground_truth.py`)
- `DuplicatePairPrediction` (`src/agent_lab/ground_truth_evaluation.py`)
- `evaluate_duplicate_pairs` (`src/agent_lab/ground_truth_evaluation.py`)

serão reutilizados integralmente sem qualquer adição de campos ou mutações de schema. Os campos de domínio `rationale` e `source_reference` em `DuplicatePairGroundTruth` permanecem dedicados estritamente a textos explicativos humanos e fontes documentais, sendo **proibida a sobrecarga com JSON empacotado**.

### 5.2 Schema Conceitual do Manifest Colateral
Os metadados analíticos do experimento serão persistidos em arquivo colateral desacoplado denominado **`ExperimentalChallengeManifest`**, indexado unicamente pela chave primária `evaluation_case_id`:

```python
# Estrutura Conceitual de Metadados (Desacoplada do Domínio)
@dataclass(frozen=True, slots=True)
class ExperimentalChallengeCaseMeta:
    evaluation_case_id: str                      # UUID do caso (chave 1:1 com DuplicatePairGroundTruth)
    stratum: str                                 # FASTENERS, VALVES, BEARINGS, ELECTRICAL, GENERAL
    challenge_taxonomy_class: str                # P-ABBR, P-WORD-ORDER, P-PN-FORMAT, P-UNIT-SYN, P-NOISE,
                                                 # HN-DIM, HN-MAT, HN-VAR, HN-UNT, HN-PN
    base_material_family: str                    # Identificador da família (ex.: DIN_933_STEEL)
    base_material_identity_id: str               # Identificador da identidade cadastrável de origem
    challenge_case_provenance: str               # SPECIALIST_CURATED | SYNTHETIC_SPECIFIED
    generation_method: str                       # Identificador do template ou regra de perturbação
    identity_defining_attributes_preserved: tuple[str, ...]  # Campos canônicos preservados
    identity_defining_attributes_violated: tuple[str, ...]   # Campos canônicos violados (vazio para P)
    reviewer_notes: str                          # Parecer da auditoria humana independente
```

### 5.3 Decisão sobre `difficulty`
O atributo `difficulty` foi **formalmente descartado no piloto inicial**. A estratificação analítica por classes taxonômicas (`P-ABBR`, `HN-DIM`, etc.) provê granularidade científica suficiente sem introduzir a subjetividade inerente a rótulos ordinais arbitrários (*Easy/Medium/Hard*).

---

## 6. Proveniência e Regras de Anti-Circularidade

### 6.1 Categorias de Proveniência
1. **`SPECIALIST_CURATED`:** Caso derivado de dados operacionais reais ou catálogos oficiais de fabricantes sob supervisão e transcrição direta de especialista humano.
2. **`SYNTHETIC_SPECIFIED`:** Caso derivado por transformação determinística controlada a partir de uma identidade base documentada.

### 6.2 Blindagem Anti-Circularidade para Casos Sintéticos
Quando da futura geração sintética, aplicam-se obrigatoriamente as regras:
- Semente pseudo-aleatória fixa e reprodutível (`seed`);
- Template formal documentado e versionado;
- Identidade base de origem explicitamente rastreada;
- Regra de mutação declarada e auditável;
- **Isolamento e Cegueira em Relação ao Detector:** É expressamente vedado consultar saídas do detector, testar predicados de `src/agent_lab/duplicates.py` ou manipular o texto do teste para contornar ou acionar heurísticas específicas do código de produto.

$$\text{Challenge-Case Generation} \neq \text{Detector Heuristic Inversion}$$

---

## 7. Checklist Humano de Auditoria e Processo de Freeze

### 7.1 Checklist Obrigatório de Auditoria por Caso
Cada par submetido ao Ground Truth referencial deve ser validado contra o checklist de 6 etapas:
- [ ] **1. Consistência Industrial da Base:** A identidade base reflete um material industrialmente viável e normativamente correto?
- [ ] **2. Validação Estrita do Rótulo:**
  - Se `is_duplicate = True`: Ambos os materiais representam rigorosamente a mesma identidade cadastrável segundo todos os atributos *identity-defining*?
  - Se `is_duplicate = False`: Há divergência inequívoca em ao menos um atributo *identity-defining*?
- [ ] **3. Conformidade das Listas Canônicas:** Os campos `attributes_preserved` e `attributes_violated` correspondem precisamente aos atributos técnicos divergentes?
- [ ] **4. Cegueira do Rótulo:** O rótulo foi emitido sem qualquer inspeção de código ou execução de detectores algorítmicos?
- [ ] **5. Fronteira da Perturbação:** Se positivo, valores numéricos e normas foram preservados? Se negativo, a divergência não é trivial/óbvia?
- [ ] **6. Invariância de Unidade:** A unidade declarada respeita a regra de equivalência de contagem ($\{ \text{UN}, \text{PC}, \text{PÇA} \}$ para positivos; incompatível para conjuntos/peças)?

### 7.2 Processo de Freeze Operacional Unidirecional
A execução futura obedecerá à cadeia unidirecional estrita em 5 passos:

```text
PASSO A: Geração e Anotação Independente dos 200 Casos
    │
    ▼
PASSO B: Auditoria Humana e FREEZE Criptográfico
    │    (Gravação e registro dos hashes SHA-256 do dataset e do manifest)
    │
    ▼  [IMUTABILIDADE ATIVADA — PROIBIDA QUALQUER ALTERAÇÃO DE DADOS]
PASSO C: Execução do Candidate Blocking
    │    (Avaliação de Candidate Pair Recall sobre os 200 casos)
    │
    ▼
PASSO D: Execução Downstream do Detector Léxico (is_possible_duplicate)
    │    (Geração de DuplicatePairPrediction por caso)
    │
    ▼
PASSO E: Computação e Fatiamento de Métricas Metrológicas
```

**Proibição Absoluta de Ajuste Silencioso:** É terminantemente proibido retificar rótulos ou descrições após a observação das predições do blocking ou do detector. Eventuais erros de anotação constatados durante o benchmark devem ser registrados como falhas de anotação documentadas e corrigidos apenas via novo ciclo de versionamento documental.

---

## 8. Metrologia e Avaliação de Resultados

### 8.1 Métricas Primárias de Candidate Blocking
Para avaliar se o mecanismo de blocking preserva os positivos verdadeiros:
1. **Candidate Pair Recall ($\text{Recall}_{\text{block}}$):**
   $$\text{Recall}_{\text{block}} = \frac{TP_{\text{block}}}{TP_{\text{block}} + FN_{\text{block}}} = \frac{|\{ (A, B) \in \text{Positives} : \text{is\_candidate}(A, B) = \text{True} \}|}{|\text{Positives}|}$$
2. **Inventário Crítico de Falsos Negativos ($FN_{\text{block}}$):**
   Lista exaustiva de todos os pares verdadeiros descartados pelo bloqueio, correlacionados com o estrato e a classe taxonômica.

### 8.2 Métricas Secundárias e Complementares do Detector Downstream
Sobre os pares retidos pelo blocking, avalia-se o detector (`is_possible_duplicate`):
- **Candidate-Conditioned Precision:** Precisão sobre os pares retidos;
- **Candidate-Conditioned Recall ($\text{Recall}_{\text{detector}|\text{candidate}}$):** Proporção dos verdadeiros duplicados retidos pelo *candidate blocking* que são também identificados pelo detector *downstream*;
- **Overall Pipeline Recall ($\text{Recall}_{\text{pipeline}}$):** Recall ponta a ponta do sistema, definido estritamente de forma condicional:
  $$\text{Recall}_{\text{pipeline}} = \text{Recall}_{\text{block}} \times \text{Recall}_{\text{detector}|\text{candidate}}$$

### 8.3 Preservação do Plano Bidimensional (Sem Fórmulas Arbitrárias)
Rejeita-se categoricamente o uso de métricas combinadas artificiais como $E = \frac{RR}{1 - \text{Recall}}$.

A metrologia do Agent Lab Pascoal preserva o **plano bidimensional explícito**:
$$(\text{Reduction Ratio}, \text{Candidate Pair Recall})$$
permitindo análise formal de dominância de Pareto e identificação clara de trade-offs de engenharia.

---

## 9. Distinção Metrológica do Reduction Ratio (RR)

É mandatório manter a separação conceitual entre dois universos amostrais completamente distintos:

1. **Reduction Ratio Catalog-Wide (Evidência do Baseline A):**
   - Medido sobre o espaço cartesiano integral dos $N$ itens do catálogo ($N \in \{250, 500, 1000, 2000\}$);
   - Para $N=2000$: $1.999.000$ pares não-direcionados, $16.887$ candidatos retidos $\implies$ **$99.16\%$ de redução estrutural**;
   - Mede a redução estrutural observada sobre o espaço *catalog-wide* dos volumes experimentais executados ($N \in \{250, 500, 1000, 2000\}$).
2. **Retenção / Redução no Challenge Set (Diagnóstico do Baseline B):**
   - Medido exclusivamente sobre os 200 pares rotulados do piloto;
   - Espaço altamente enriquecido com casos positivos e hard negatives sutis;
   - A razão de redução no Challenge Set possui valor puramente diagnóstico interno da amostra e **NÃO deve ser comparada numericamente com o RR catalog-wide**.

$$\text{Challenge-Set Precision} \neq \text{Operational Precision}$$
$$\text{RR Catalog-Wide} \neq \text{Challenge-Set Reduction}$$

---

## 10. Gates e Critérios de GO para a Futura Geração dos Casos

A materialização física dos 200 pares de teste em datasets e manifestos permanece **NÃO AUTORIZADA** por esta SPEC. A transição para a fase de geração exigirá o cumprimento cumulativo dos seguintes gates:
1. [ ] **Gate 1:** Revisão formal e aprovação da `SPEC-0158` via PR documental integrada na `main`;
2. [ ] **Gate 2:** Aprovação expressa da *Strict Material Identity Policy* e das taxonomias de $P$ e $HN$;
3. [ ] **Gate 3:** Convalidação do schema do `ExperimentalChallengeManifest` e da regra de blindagem anti-circularidade;
4. [ ] **Gate 4:** Homologação do checklist de auditoria em 6 etapas e do fluxo de freeze com SHA-256;
5. [ ] **Gate 5:** Confirmação de ausência de dependência ou acoplamento com o detector de produto;
6. [ ] **Gate 6:** Emissão de decisão humana formal autorizando o início da construção dos dados.

---

## 11. Limites de Escopo da SPEC-0158

Ficam explicitamente definidos como **FORA DE ESCOPO** desta especificação:
- Materialização de arquivos CSV, JSON ou JSONL contendo os 200 pares de dados;
- Geração de identificadores `evaluation_case_id` concretos ou anotações reais de especialistas;
- Implementação de código de harness experimental ou scripts de medição;
- Alterações em qualquer arquivo de código-fonte de produto (`src/agent_lab/`);
- Alterações na suite de testes unitários (`tests/`);
- Construção de interfaces de usuário, endpoints de API ou integrações com ERP;
- Implementação de algoritmos de blocking ou alteração de regras do detector no produto;
- Reivindicações de desempenho operacional para catálogos industriais de 100k SKUs.
