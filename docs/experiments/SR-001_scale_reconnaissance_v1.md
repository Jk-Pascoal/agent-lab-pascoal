# SR-001 — Scale Reconnaissance v1

> Protocolo de Investigação Experimental e Metrológica do Pipeline de Diagnóstico Cadastral do Agent Lab Pascoal.

---

## Metadados

| Campo | Valor |
|---|---|
| **Identificador** | `SR-001` |
| **Documento** | `docs/experiments/SR-001_scale_reconnaissance_v1.md` |
| **Status** | `PROPOSED` (Fase 1: Protocolo Experimental) |
| **Issue relacionada** | `#158` — `SR-001 — Scale Reconnaissance v1` |
| **Natureza** | Investigação experimental / não funcional |
| **Pressão arquitetural de origem** | `P-07` — *Industrial Load / Scale Validation* |
| **Branch de trabalho** | `docs/issue-158-sr001-scale-reconnaissance` |
| **Responsável** | `Jk-Pascoal` |
| **Data de criação** | `2026-09-25` |
| **Baseline canônico de entrada** | `1194 testes aprovados` (100% GREEN via `unittest`) |
| **Runner oficial do produto** | `python -m unittest discover -s tests -v` (Python 3.11) |
| **Impacto funcional / SemVer** | `Nenhum — zero alteração em src/agent_lab/ ou contratos de produção` |

---

## 1. Justificativa Ontológica e Governança

1. **Separação Categorial (`docs/specs/` vs. `docs/experiments/`):**
   * Para esta investigação, opta-se por `docs/experiments/` porque a SR-001 registra protocolo, metodologia e evidência experimental, e não um contrato de comportamento de produção. Esta escolha NÃO redefine o escopo geral de `docs/specs/`, que permanece conforme as convenções históricas do projeto.
   * `Experimental Protocol ≠ Functional SPEC`: O documento em `docs/experiments/` define a metodologia, as hipóteses, os limites metrológicos e o registro de evidências de um experimento observacional.
2. **Impacto no Roadmap e KPIs:**
   * A SR-001 investiga a pressão de escala P-07 e **não adiciona peso ao Roadmap** nem altera o KPI da PoC no `docs/PROJECT_COMPASS.md`.
   * O percentual de completude da PoC reflete entregas funcionais de governança e não deve ser inflacionado artificialmente por ciclos de exploração ou benchmarking.

---

## 2. Contexto e Problema

Com a integração recente do pipeline determinístico de diagnóstico de qualidade de catálogo (Issue #149 / `diagnose_catalog_quality`) e do adaptador operacional de ingestão CSV (Issue #154 / `load_catalog_materials`), o Agent Lab Pascoal dispõe de um fluxo ponta a ponta funcional em memória.

Entretanto, sob a perspectiva da pressão arquitetural **P-07 (Industrial Load / Scale Validation)**, o pipeline opera atualmente em regime *cold-N catalog-wide*, avaliando exaustivamente cada material contra todos os demais registros do catálogo fechado. Isso gera exatamente $N(N-1)$ avaliações direcionadas do predicado de duplicidade.

Atualmente, o laboratório não possui:
1. Uma caracterização computacional reprodutível e oficial de tempos de execução, consumo de memória, overhead de parsing CSV e contagem de chamadas a predicados antes de qualquer otimização;
2. Uma avaliação de qualidade semântica (eficácia, precision, recall, F1) do detector determinístico frente a um Ground Truth independente e não-circular, que reflita as perturbações cadastrais reais da indústria.

Sem essa linha de base dupla (Computacional + Semântica), qualquer esforço prematuro de otimização (como caching, poda simétrica ou blocking) corre o risco de introduzir complexidade sem fundamentação empírica ou de incorrer em "performance sem preservação da verdade", o que configuraria regressão analítica inaceitável.

---

## 3. Pergunta Central da Investigação

> **Qual é o comportamento COMPUTACIONAL e SEMÂNTICO do pipeline catalog-wide existente ANTES de qualquer otimização?**

---

## 4. Hipóteses Formais da SR-001

* **H1 — Complexidade Assintótica:** O cold-N catalog-wide atual apresenta crescimento aproximadamente quadrático ($T(N) \approx k \cdot N^p$, com $p \approx 2$), estritamente coerente com as $N(N-1)$ avaliações direcionadas do predicado `is_possible_duplicate`.
* **H2 — Custo Dominante:** A detecção de duplicidades e a renormalização per-par de atributos textuais são candidatas a dominar o tempo total de processamento conforme $N$ cresce, mas essa dominância deve ser comprovada metrologicamente em relação aos custos de I/O de CSV e validação de regras cadastrais.
* **H3 — Qualidade Semântica e Não-Circularidade:** O recall do detector determinístico atual varia sensivelmente entre as diferentes categorias de perturbação cadastral industrial (ex.: part numbers com separadores removidos, fabricantes ausentes, erros de grupo de material), apresentando pontos cegos esperados e não devendo alcançar 100% de forma artificial.
* **H4 — Potencial Teórico de Blocking:** A estrutura lógica do detector atual permite estimar uma redução exata do espaço de candidatos relativamente ao próprio detector através da união deduplicada das famílias indexáveis, mas a efetividade real dessa redução depende da dispersão e do tamanho dos blocos de chaves no catálogo.
* **H5 — Não-Equivalência com Workload Incremental:** Os resultados observados no cold-N catalog-wide não autorizam alegações de desempenho para o workload incremental $B \times I + I(I-1)/2$, visto que o caminho incremental de nível de catálogo ainda não existe na arquitetura do produto.

---

## 5. Escopo da Investigação

### 5.1 Baseline A — Capacidade Computacional

Planejamento e execução de medições para caracterizar:
1. **Tempo de Ingestão CSV Isolado ($T_{CSV}$):** Leitura de arquivo físico em disco via `load_catalog_materials`, decodificação UTF-8, validação canônica de cabeçalho e instanciação de `MaterialRecord`;
2. **Tempo de Diagnóstico em Memória Isolado ($T_{diag}$):** Execução pura de `diagnose_catalog_quality` sobre a tupla de materiais em memória;
3. **Tempo Ponta a Ponta ($T_{total}$):** Execução completa $CSV \rightarrow \text{MaterialRecord} \rightarrow \text{Diagnóstico} \rightarrow \text{CatalogQualityReport}$;
4. **Volume de Comparações:** Contagem teórica ($N(N-1)$) versus chamadas efetivamente observadas ao predicado `is_possible_duplicate`;
5. **Curva de Escala e Expoente Empírico:** Ajuste de potência para determinação empírica de $p$ em $T(N) \approx k \cdot N^p$;
6. **Consumo de Memória:** Aferição do pico de alocação de memória (via `tracemalloc`) em rodada dedicada e isolada;
7. **Análise Teórica de Candidate Blocks (Sem Implementar Blocking):**
   * Mapeamento e distribuição de chaves candidatas;
   * Cardinalidade da união deduplicada de pares candidatos;
   * Razão teórica de redução: $\frac{|\text{pares candidatos deduplicados}|}{|\text{todos os pares possíveis}|}$;
   * Identificação dos maiores blocos válidos de candidatos.

### 5.2 Baseline B — Qualidade Semântica

Planejamento de um conjunto de teste com Ground Truth independente e rigoroso:
1. **Princípio Constitucional Anti-Circularidade:**
   $$\mathbf{Ground\ Truth\ generation \ne Detector\ implementation}$$
   $$\mathbf{Computational\ equivalence \ne Semantic\ recall}$$
   O gerador de Ground Truth sintético **não pode ser derivado das regras literais** de `duplicates.py` (ex.: não deve limitar-se a replicar exatamente a mesma regra de "mesmo part number normalizado + mesmo fabricante normalizado"). Ele deve introduzir perturbações industriais reais para avaliar a sensibilidade e os limites do detector.
2. **Composição do Dataset de Teste:**
   * Positivos verdadeiros óbvios e sutis;
   * *Hard negatives* (materiais tecnicamente semelhantes em descrição e números, mas pertencentes a aplicações ou itens distintos que não são duplicatas);
   * **Taxonomia de Perturbações Industriais:**
     - Variação estrutural de part number (espaçamento, hífen, pontuação);
     - Remoção de separadores em códigos de peça;
     - Fabricante ausente ou grafado sob razão social divergente;
     - Abreviações técnicas e sinônimos não mapeados no dicionário estático do detector;
     - Classificação errônea ou divergente de grupo de material (*cross-group duplicates*);
     - Descrições empobrecidas ou truncadas;
     - Unidades de medida divergentes para o mesmo item físico.
3. **Métricas Semânticas:**
   * Matriz de confusão completa: Verdadeiros Positivos (TP), Falsos Positivos (FP), Verdadeiros Negativos (TN), Falsos Negativos (FN);
   * Métricas consolidadas: Precision, Recall e F1-Score;
   * Taxa de Recall estratificada por cada categoria de perturbação cadastral.

---

## 6. Análise Estrutural de Blocking (Esclarecimentos Conceituais)

Para orientar a análise teórica de redução de pares do Baseline A (sem implementar blocking no código de produção), incorporam-se formalmente as seguintes correções conceituais:

### Correção A — Famílias de Blocking Não São Disjuntas
O detector atual possui duas rotas lógicas para identificação de duplicidade:
1. **Rota 1 (Part Number + Fabricante):** Part number não-vazio idêntico e fabricante não-vazio idêntico;
2. **Rota 2 (Grupo + Categoria Lexical + Números/Palavras):** Mesmo grupo de material, mesmo category token e interseção de números ($\ge 2$) e palavras ($\ge 1$).

Essas duas famílias de candidatos **não formam conjuntos disjuntos**. Um mesmo par de materiais duplicados pode satisfazer simultaneamente a Rota 1 e a Rota 2. Portanto:
* Qualquer estimativa teórica do espaço de candidatos **deve calcular a UNIÃO DEDUPLICADA dos pares** gerados por ambas as rotas:
  $$\text{Pares Candidatos} = \mathcal{P}_{\text{rota1}} \cup \mathcal{P}_{\text{rota2}}$$
* É matematicamente incorreto simplesmente somar a cardinalidade das duas famílias ($|\mathcal{P}_{\text{rota1}}| + |\mathcal{P}_{\text{rota2}}|$), sob risco de contagem dupla.

### Correção B — Tratamento de Chaves Vazias na Rota Lexical
* No detector atual, a função `category_token(full_description)` e a função `word_tokens(full_description)` compartilham a mesma rotina de extração e filtragem lexical.
* Se `category_token == ""`, o material não possui nenhum substantivo técnico reconhecido e, consequentemente, não possui tokens para satisfazer a exigência de `shared_words >= 1`.
* Portanto, em uma análise de blocking exato relativo ao detector atual, a rota lexical **não precisa gerar candidatos para `category_token == ""`**, pois nenhum par nessa condição pode resultar em duplicidade positiva por essa rota. O valor `category_token == ""` não forma um megabloco a ser comparado.
* Diferentemente, `material_group == ""` associado a um `category_token != ""` válido permanece uma chave legítima de bloco.
* A Rota 1 (part number + fabricante) opera de forma totalmente independente e exige que ambos os campos sejam não-vazios.

---

## 7. Metodologia e Protocolo de Execução

### 7.1 Volumes de Carga Planejados
Para o Baseline A, a progressão de volumes para avaliação na máquina local compreenderá:
$$N \in \{250, 500, 1000, 2000\}$$

* **Progressão Adaptativa:** A execução inicia nos volumes menores e progride de forma controlada. Volumes $N > 2000$ não constituem meta obrigatória para a rodada inicial e só serão avaliados se houver margem confortável no orçamento temporal e alto valor informacional.

### 7.2 Protocolo de Timing Limpo
1. Cada volume $N$ será submetido a **3 repetições independentes**;
2. As medições de tempo utilizarão `time.perf_counter()`;
3. Será reportada a **mediana** como estimativa central, acompanhada obrigatoriamente do **mínimo** e do **máximo** observados;
4. **Isolamento de Profiling:** É expressamente vedado o uso de `tracemalloc`, profilers ou instrumentação pesada durante as rodadas de timing limpo.

### 7.3 Protocolo de Medição de Memória
1. O consumo de memória será aferido em uma **rodada separada e dedicada** utilizando `tracemalloc`;
2. As métricas de memória focarão no pico de memória alocada (`peak_traced_memory`);
3. Os tempos de execução obtidos durante a rodada de memória **não serão misturados** com os tempos do timing limpo, devido ao overhead intrínseco de rastreamento de alocações.

### 7.4 Stop Conditions e Orçamento Operacional
* **Janela Operacional da Sessão:** A atividade de 25/09/2026 encerra impreterivelmente às 11:00 BRT.
* **Stop Condition de Execução Experimental:** Qualquer harness de medição ou execução experimental deve ser interrompido impreterivelmente às **10:35 BRT**, independentemente do tamanho de $N$ em andamento ou de repetições pendentes.
* **Reserva de Governança:** O intervalo entre 10:35 BRT e 11:00 BRT fica estritamente reservado para análise dos resultados coletados, verificação de gates de governança e fechamento da sessão.
* **Ciclo Multi-Sessão da SR-001:** A SR-001 pode atravessar mais de uma sessão de trabalho. A janela de 25/09/2026 e o stop de 10:35 BRT limitam exclusivamente a execução experimental desta sessão, e não constituem critério global de conclusão da investigação.
* **Critério de Interrupção por Erro Experimental:** Interromper a execução em caso de erro do harness, exceção não prevista, corrupção ou inconsistência dos dados gerados, não-determinismo inesperado sob a mesma entrada/seed, ou divergência entre uma prova de equivalência computacional e o comportamento original que ela deveria reproduzir. Divergências do detector em relação ao Ground Truth semântico NÃO interrompem a SR-001; elas constituem evidência experimental a ser registrada como FP/FN.

---

## 8. Evidência Externa Corroborativa (Não-Canônica)

Registra-se para fins exclusivos de sinalização e planejamento a observação externa read-only realizada em 25/09/2026. Esta observação possui o status estrito de:
> `External corroborative observation — non-canonical`

Tais dados **não constituem baseline oficial do Agent Lab Pascoal** e não devem ser promovidos a fatos do projeto sem reprodução sob o protocolo canônico.

### 8.1 Medições Externas Observadas
* **Hardware de teste externo:** Intel Xeon 2.10 GHz, 2 vCPU, 7 GB RAM, Linux x86_64, Python 3.11.15.
* **Tempos observados:**
  - $N = 500$: $\approx 3,0\text{ s}$
  - $N = 1000$: $\approx 11,8\text{ s}$
  - $N = 2000$: $\approx 47,0\text{ s}$
* **Chamadas ao predicado:** Confirmadas exatamente 999.000 avaliações para $N = 1000$.
* **Expoente observado:** $p \approx 1,99$.

### 8.2 Extrapolações Teóricas Externas
* $\approx 20\text{ min}$ para $N = 10.000$ (cold-N);
* $\approx 33\text{ h}$ para $N = 100.000$ (cold-N);
* $\approx 6\text{ min}$ para workload teórico de lote de 300 entrantes contra base de 100.000 históricos ($300 \times 100.000$).

### 8.3 Ressalvas Formais Obrigatórias
1. Extrapolações assintóticas **não são medições empíricas**;
2. O dataset sintético externo utilizado não é representativo da diversidade do domínio;
3. A constante de tempo observada em hardware virtualizado externo não deve ser generalizada para outros ambientes;
4. O workload incremental ($B \times I + I(I-1)/2$) **ainda não existe no produto**, sendo uma extrapolação puramente hipotética.

---

## 9. Limites Arquiteturais e Fora de Escopo

Durante toda a execução da SR-001, aplicam-se com rigor as seguintes proibições:

1. **Zero Mutação em Código de Produção:** Nenhuma linha de código em `src/agent_lab/` será alterada;
2. **Zero Alteração na Suíte Canônica:** O diretório `tests/` e a contagem oficial de **1194 testes aprovados** permanecem intocados;
3. **Proibição de Otimização Prematura:** É vedada qualquer implementação de cache de normalização, poda por simetria ou índices de blocking no produto nesta fase;
4. **Isolamento de Harness Futuro:** Qualquer script de geração ou harness experimental aprovado em etapa posterior deverá residir estritamente no diretório isolado `experiments/` na raiz, sem poluir os pacotes do projeto;
5. **Zero Dependências Pesadas:** É proibida a adição de bibliotecas externas (`pandas`, `polars`, `DuckDB`, `scipy`) ao projeto; o experimento deve utilizar a biblioteca padrão do Python e os contratos nativos do Agent Lab;
6. **Não Utilização do `pytest`:** O runner oficial para aferição da integridade do projeto é e permanece `python -m unittest discover -s tests`.

---

## 10. Critérios de Aceite da SR-001

A investigação SR-001 será considerada concluída com sucesso quando:
1. O protocolo experimental presente neste documento for aprovado pelo especialista humano;
2. As medições de Baseline A (computacional) forem executadas com sucesso para os volumes planejados, registrando mediana, mínimo, máximo e expoente empírico;
3. A análise de blocking quantificar o potencial teórico de redução de pares sobre a união deduplicada das famílias;
4. As medições de Baseline B (semântico) forem realizadas contra o dataset independente, quantificando precision, recall e F1 por categoria de perturbação;
5. Todas as evidências e números finais forem consolidados e versionados no presente documento;
6. O repositório permanecer com o baseline oficial de 1194 testes 100% GREEN via `unittest`, com zero alterações no código de produção.

---

## 11. Responsabilidade Humana

A interpretação das evidências colhidas, o julgamento sobre a suficiência do baseline para as necessidades da PoC e qualquer decisão subsequente sobre a formalização de uma SPEC de otimização estrutural (como caching ou blocking) pertencem exclusivamente ao especialista humano de governança.
