# SPEC-0154 — Catalog CSV Ingestion Adapter v1

> Especificação técnica do adaptador de entrada operacional para ingestão de catálogos
> em formato CSV e mapeamento para registros brutos de domínio (MaterialRecord) no Agent Lab Pascoal.

---

## Metadados

| Campo | Valor |
|---|---|
| **Identificador** | `SPEC-0154` |
| **Status** | `IMPLEMENTED` |
| **Issue relacionada** | `#154` |
| **Título da Issue** | `[FEAT] Catalog CSV Ingestion Adapter v1: Operational Material Record Loader` |
| **Branch documental** | `docs/issue-154-catalog-csv-ingestion-adapter` |
| **Responsável** | `Jk-Pascoal` |
| **Data de criação** | `2026-09-24` |
| **Última atualização** | `2026-09-24` |
| **Data de integração** | `—` |
| **Domínio** | Governança de materiais industriais PDM/BOM e Master Data |
| **Camada arquitetural** | Infraestrutura / Adaptador de I/O de Entrada (`Input Adapter`) |
| **Baseline de entrada** | `1173 testes aprovados` (100% GREEN) |
| **Baseline final integrado** | `—` |
| **PR documental de aprovação** | `#155` |
| **PR funcional integrada** | `—` |
| **PR documental de closeout** | `—` |
| **Impacto SemVer** | `MINOR — nova capacidade pública aditiva de ingestão operacional de catálogo; release formal permanece v0.1.0` |
| **Runner oficial** | `python -m unittest discover -s tests -v` (Python 3.11) |

---

## 1. Contexto

O **Agent Lab Pascoal** estabeleceu na Issue #149 ([PR #150](https://github.com/Jk-Pascoal/agent-lab-pascoal/pull/150), [PR #151](https://github.com/Jk-Pascoal/agent-lab-pascoal/pull/151), [PR #152](https://github.com/Jk-Pascoal/agent-lab-pascoal/pull/152)) o seu núcleo analítico e orquestrador de aplicação para diagnóstico em lote de qualidade cadastral de catálogos fechados de materiais industriais:
1. **Read-Model de Diagnóstico:** `CatalogQualityReport` em `src/agent_lab/catalog_quality.py`, contendo ordenação canônica por `material_id`, métricas consolidadas e invariantes estritas de simetria relacional na detecção de duplicidades;
2. **Pipeline Determinístico:** A função `diagnose_catalog_quality(catalog: Sequence[MaterialRecord], *, catalog_id: str)` que realiza a avaliação exaustiva de regras e duplicidades sobre o catálogo;
3. **Boundary de Aplicação:** A classe `DiagnoseCatalogQualityUseCase` em `src/agent_lab/catalog_quality_use_case.py`, que orquestra a execução sob o protocolo estrutural `CatalogDiagnosticPipeline` e estabelece a fronteira de confiança e integridade dos resultados.

Baseline oficial verificado e auditado na branch `main`:
```text
Ran 1173 tests
OK
```

Paralelamente, a Seção 14 do `docs/PROJECT_COMPASS.md` define como prioridade da esteira evolutiva a viabilização de uma *PoC vendável de diagnóstico de qualidade cadastral*. Para que esse diagnóstico seja demonstrável e utilizável com dados operacionais externos sem depender de instâncias em memória instanciadas em scripts ad-hoc, é imprescindível introduzir uma porta de entrada física (*Input Adapter*) de ingestão de arquivos.

---

## 2. Problema e Evidências

### 2.1 Problema
O orquestrador `DiagnoseCatalogQualityUseCase` recebe em memória:
$$\text{catalog: Sequence[MaterialRecord]} \quad + \quad \text{catalog\_id: str}$$
mas não existe no sistema nenhum componente operacional responsável por receber o caminho de um arquivo CSV físico e transformá-lo na sequência imutável de `MaterialRecord` consumida pelo caso de uso.

### 2.2 Evidências no Código Real
1. O único carregador CSV existente no repositório é a função `load_labeled_materials(path: str | Path)` em `src/agent_lab/data_io.py`. Esse loader foi implementado na fase inicial do laboratório para avaliar benchmarks sintéticos e atende ao contrato:
   ```python
   @dataclass(frozen=True, slots=True)
   class LabeledMaterial:
       record: MaterialRecord
       expected_issue: str
   ```
2. Embora `load_labeled_materials` consiga tecnicamente consumir certos CSVs sem a coluna `expected_issue` (recorrendo ao default vazio `row.get("expected_issue", "").strip()`), sua responsabilidade semântica e seu tipo de retorno (`list[LabeledMaterial]`) pertencem estritamente à trilha de benchmarking e avaliação de Ground Truth. Utilizá-lo para alimentar o pipeline de diagnóstico operacional violaria a separação entre dados de teste rotulados e dados operacionais de negócio.
3. Além disso, `load_labeled_materials` executa `.strip()` silencioso em todos os campos lidos e recorre a defaults permissivos mesmo na ausência da coluna `material_id`, ocultando problemas estruturais de cabeçalho que deveriam falhar de forma fechada (*fail-closed*).

---

## 3. Objetivo

Implementar um adaptador puro de ingestão operacional de catálogo:
$$\texttt{load\_catalog\_materials(path: str \mid Path) -> tuple[MaterialRecord, ...]}$$
situado no módulo de infraestrutura `src/agent_lab/catalog_csv_adapter.py`, viabilizando o fluxo ponta a ponta:

```text
Arquivo CSV Físico
        ↓
load_catalog_materials (Adapter de I/O)
        ↓
tuple[MaterialRecord, ...] (Registros Brutos de Domínio)
        ↓
DiagnoseCatalogQualityUseCase.execute(catalog, catalog_id=...)
        ↓
CatalogQualityReport (Read-Model Consolidado)
```

---

## 4. Não Objetivos

1. Não alterar o comportamento, contrato ou implementação de `DiagnoseCatalogQualityUseCase`, `diagnose_catalog_quality` ou `CatalogQualityReport`.
2. Não alterar ou reutilizar a infraestrutura de Ground Truth (`data_io.py`, `LabeledMaterial` ou runners de benchmark).
3. Não inferir, derivar ou embutir `catalog_id` dentro do arquivo CSV ou da assinatura do adaptador.
4. Não realizar validações semânticas de domínio (como unicidade de materiais ou regras de preenchimento) dentro do adaptador.
5. Não suportar formatos binários ou tabulares avançados (Excel `.xlsx`, `.parquet`, `.jsonl`).
6. Não suportar delimitadores alternativos (ponto-e-vírgula, tabulação) ou detecção mágica de dialeto (`csv.Sniffer`).
7. Não introduzir dependências externas (`pandas`, `polars`).
8. Não construir endpoints REST, interface gráfica (Streamlit) ou rotinas de exportação/serialização de relatórios.

---

## 5. Contrato Público

O módulo `src/agent_lab/catalog_csv_adapter.py` fornecerá a seguinte função pública:

```python
def load_catalog_materials(path: str | Path) -> tuple[MaterialRecord, ...]:
    """Carrega um arquivo CSV operacional de catálogo e mapeia suas linhas para MaterialRecord.

    Lê um arquivo delimitado por vírgula em codificação UTF-8, valida o cabeçalho
    segundo o schema canônico fail-closed, preserva os dados brutos exatamente
    como fornecidos (sem saneamento ou strip) e instancia instâncias de MaterialRecord.

    Args:
        path: Caminho no sistema de arquivos para o arquivo CSV físico.

    Returns:
        Tupla imutável de instâncias de MaterialRecord, preservando estritamente
        a ordem física das linhas no arquivo CSV. Retorna () se o arquivo contiver
        apenas o cabeçalho válido sem linhas de dados.

    Raises:
        FileNotFoundError: Se o arquivo não existir no caminho fornecido.
        IsADirectoryError: Se o caminho apontar para um diretório.
        UnicodeDecodeError: Se o arquivo contiver bytes inválidos para UTF-8.
        ValueError: Se o arquivo estiver vazio, se faltar o cabeçalho, se faltar
            a coluna obrigatória 'material_id', se o cabeçalho contiver colunas
            desconhecidas, se houver nomes de colunas duplicados no cabeçalho,
            ou se uma linha contiver campos excedentes ao cabeçalho.
        csv.Error: Se o parser CSV em modo estrito detectar corrupção sintática.
    """
```

### 5.1 Justificativa da Tupla Imutável (`tuple[MaterialRecord, ...]`)
* É um contrato de leitura pura (ingestão);
* A coleção de materiais carregada a partir do arquivo físico não deve ser mutada após a leitura;
* Previne modificações acidentais por parte dos chamadores antes de alimentar a aplicação;
* Compatibiliza-se naturalmente com o tipo estrutural `Sequence[MaterialRecord]` esperado pelo método `DiagnoseCatalogQualityUseCase.execute()`.

### 5.2 Atribuição de `catalog_id`
O arquivo CSV modela uma tabela de registros de materiais. O identificador do catálogo (`catalog_id`) é um metadado de contexto do processo (ex.: identificador de lote, nome da unidade fabril, timestamp da extração ERP) e deve ser fornecido explicitamente pelo orquestrador/chamador no momento de invocar o caso de uso. O adaptador não infere e não exige `catalog_id`.

---

## 6. Schema CSV v1 e Política de Cabeçalho

### 6.1 Conjunto Canônico de Colunas
O schema canônico do cabeçalho aceito na versão v1 é composto exclusivamente pelos nomes de atributos do dataclass `MaterialRecord`:

$$\mathcal{C}_{\text{canonical}} = \left\{
\begin{array}{l}
\texttt{"material\_id"}, \\
\texttt{"description\_short"}, \\
\texttt{"long\_description"}, \\
\texttt{"unit"}, \\
\texttt{"manufacturer"}, \\
\texttt{"manufacturer\_part\_number"}, \\
\texttt{"material\_group"}, \\
\texttt{"status"}
\end{array}
\right\}$$

### 6.2 Política de Schema: Fail-Closed Canonical Schema
Em consonância com as convenções arquiteturais do Agent Lab:
1. **Coluna Obrigatória:** O cabeçalho deve conter obrigatoriamente a coluna `material_id`. Caso esteja ausente, o carregamento falha imediatamente com `ValueError("CSV header missing required column: 'material_id'")`.
2. **Colunas Opcionais Reconhecidas:** Qualquer subconjunto das outras 7 colunas canônicas pode estar presente ou omitido no cabeçalho.
3. **Colunas Opcionais Omitidas no Cabeçalho:** Mapeiam para o valor padrão `""` (string vazia) em todas as instâncias de `MaterialRecord` criadas.
4. **Rejeição Estrita de Colunas Desconhecidas (Fail-Closed):**
   * *Decisão de Design:* Rejeitar qualquer coluna que não pertença a $\mathcal{C}_{\text{canonical}}$ levantando `ValueError` com os nomes das colunas desconhecidas.
   * *Justificativa:* Em ambientes corporativos, pequenas variações de grafia (ex.: `desc_short`, `mfg_part_no`, `unit_of_measure`, `id_material`) fariam com que uma leitura tolerante descartasse silenciosamente atributos vitais de engenharia, gerando falsas acusações de ausência de dados pelo pipeline. A rejeição explícita protege a integridade operacional da PoC.
5. **Nomes de Colunas Duplicados:** Se o cabeçalho declarar duas colunas com o mesmo nome (ex.: `material_id,unit,unit`), o carregamento falha imediatamente com `ValueError("CSV header contains duplicate column names: ...")`.
6. **Arquivo Vazio ou Sem Cabeçalho:** Arquivo de 0 bytes ou arquivo cuja primeira linha não contenha dados interpretáveis como cabeçalho levanta `ValueError("CSV file is empty or missing header")`.
7. **Arquivo Apenas com Cabeçalho Válido:** Arquivo contendo um cabeçalho válido e zero linhas de registros subsequentes retorna `()` (tupla vazia).

---

## 7. Política Constitucional de Raw Ingestion (Preservação de Dados Brutos)

Conforme registrado na definição de domínio de `MaterialRecord` em `src/agent_lab/domain.py`:
```python
@dataclass(frozen=True, slots=True)
class MaterialRecord:
    """Registro bruto.

    Campos vazios são aceitos porque o objetivo do sistema é justamente
    encontrar defeitos nos dados recebidos.
    """
    material_id: str
    description_short: str = ""
    long_description: str = ""
    unit: str = ""
    manufacturer: str = ""
    manufacturer_part_number: str = ""
    material_group: str = ""
    status: str = ""
```

### Princípio Constitucional:
$$\mathbf{ADAPTER\ PARSEIA\ E\ MAPEIA.\ ADAPTER\ N\tilde{A}O\ SANEIA\ SILENCIOSAMENTE\ DADO\ DE\ DOM\acute{I}NIO.}$$

1. **Proibição de `.strip()` ou Normalização Silenciosa:**
   * O adaptador **NÃO** deve executar `.strip()` nos valores das células do CSV.
   * Valores com espaços externos (ex.: `" MAT-001 "`) devem ser atribuídos ao `MaterialRecord` exatamente como extraídos.
   * *Fundamentação:* O pipeline `diagnose_catalog_quality` possui verificação explícita que rejeita `material_id` com outer whitespace:
     ```python
     if material_id != material_id.strip():
         raise ValueError("MaterialRecord.material_id must not contain outer whitespace")
     ```
     Executar `.strip()` no adaptador mascararia um defeito cadastral grave que o sistema foi deliberadamente construído para apontar ou rejeitar.
2. **Preservação dos Demais Campos:**
   * Textos descritivos, códigos de fabricante e unidades devem preservar quebras de linha internas, espaços duplicados e formatações originais.
   * O objetivo das regras de governança (`rules.py`) e dos normalizadores é analisar esses desvios no momento adequado, e não escondê-los no momento da carga.
3. **Tratamento de Campos Ausentes na Linha (`restval=""`):**
   * Se uma linha física terminar com menos campos do que os declarados no cabeçalho, o parser deve utilizar semanticamente `restval=""`, garantindo que os campos faltantes recebam string vazia `""` e impedindo a propagação de `None` para os atributos tipados como `str`.

---

## 8. Separação de Responsabilidades: Adapter vs. Domain/Pipeline

A fronteira arquitetural entre o adaptador de infraestrutura e o núcleo analítico de domínio é rigorosa:

```text
+---------------------------------------------------------------------------------------+
| CAMADA DE ADAPTADOR (catalog_csv_adapter.py)                                          |
| - Acesso ao sistema de arquivos (Path, existência, permissão, arquivo vs diretório)   |
| - Decodificação de bytes em UTF-8                                                     |
| - Parsing sintático CSV em modo estrito (csv.DictReader(..., strict=True))            |
| - Validação da integridade estrutural do cabeçalho (obrigatório, canônico, único)     |
| - Mapeamento das linhas para instâncias de MaterialRecord (preservando valores brutos) |
| - Detecção e falha em linhas com campos excedentes ao cabeçalho (None in row)          |
| - Preservação da ordem física original das linhas                                     |
| - Retorno de tuple[MaterialRecord, ...]                                               |
+---------------------------------------------------------------------------------------+
                                           |
                                           v
+---------------------------------------------------------------------------------------+
| CAMADA DE DOMÍNIO / PIPELINE (diagnose_catalog_quality & CatalogQualityReport)        |
| - Validação de tipo de instância (isinstance(item, MaterialRecord))                   |
| - Validação semântica de material_id (não vazio, não nulo, sem outer whitespace)      |
| - Validação de unicidade de material_id no catálogo fechado                           |
| - Avaliação determinística de regras técnicas de materiais                            |
| - Avaliação de candidatos a duplicidade e simetria relacional de pares                |
| - Cálculo de métricas cadastrais consolidadas e emissão de CatalogQualityReport       |
+---------------------------------------------------------------------------------------+
```

*Regra de Ouro:* O adaptador não duplica validações semânticas que pertencem ao pipeline analítico (ex.: verificar se `material_id` é duplicado ou se contém espaços) unicamente para tentar gerar mensagens amigáveis com o número da linha. O domínio é a autoridade máxima e centralizada sobre a validade do catálogo.

---

## 9. Casos de Erro Estruturais (Fail-Closed)

### 9.1 Erros Tratados e Emitidos pelo Adaptador
1. **Arquivo Inexistente:** Se o arquivo especificado não existir no caminho, propaga `FileNotFoundError`.
2. **Caminho é Diretório:** Se o caminho apontar para um diretório, propaga `IsADirectoryError`.
3. **Encoding Inválido:** Se o arquivo contiver bytes que não formam caracteres UTF-8 válidos, propaga `UnicodeDecodeError`.
4. **Arquivo Vazio / Sem Cabeçalho:** Se o arquivo tiver tamanho zero ou não produzir campos de cabeçalho (`reader.fieldnames is None`), levanta `ValueError("CSV file is empty or missing header")`.
5. **Cabeçalho sem Coluna Obrigatória:** Se a coluna `material_id` não constar no cabeçalho, levanta `ValueError("CSV header missing required column: 'material_id'")`.
6. **Coluna Desconhecida no Cabeçalho:** Se houver nomes fora de $\mathcal{C}_{\text{canonical}}$, levanta `ValueError("CSV header contains unrecognized column(s): ...")`.
7. **Nomes de Colunas Duplicados:** Se o cabeçalho contiver o mesmo nome de coluna mais de uma vez, levanta `ValueError("CSV header contains duplicate column names: ...")`.
8. **Campos Excedentes na Linha:** Se uma linha contiver mais delimitadores do que o número de colunas declaradas no cabeçalho (detectado via presença de chave `None in row` no `csv.DictReader`), levanta `ValueError("CSV row contains more fields than header")`.
9. **Sintaxe CSV Inválida em Modo Estrito:** Quando executado com `strict=True`, o parser da biblioteca padrão levanta `csv.Error` diante de erros sintáticos reconhecidos pelo parser CSV quando operado em modo estrito, como determinados casos de aspas não fechadas. O adaptador deixa essa exceção ser propagada.

### 9.2 Casos Não Tratados pelo Adaptador (Delegados ao Domínio)
* Registro com `material_id` vazio (`""`) ou composto apenas de espaços (`"   "`);
* Registro com `material_id` contendo espaços externos (`" MAT-01 "`);
* Registros com `material_id` duplicado no catálogo;
* Registros com campos técnicos em desconformidade com regras de engenharia.

---

## 10. Invariantes

1. **Invariante de Preservação de Dados:** Nenhum valor de string de nenhuma coluna sofre mutação, stripping ou saneamento durante o processo de ingestão.
2. **Invariante de Schema Canônico:** O cabeçalho é validado de forma estrita contra $\mathcal{C}_{\text{canonical}}$, falhando de forma fechada na presença de colunas desconhecidas ou duplicadas.
3. **Invariante de Imutabilidade:** O retorno é sempre uma `tuple[MaterialRecord, ...]`.
4. **Invariante de Determinismo e Ordem:** O mesmo arquivo físico sempre resulta na mesma tupla de instâncias, mantendo rigorosamente a ordem sequencial física das linhas do CSV.
5. **Invariante de Isolamento:** O adaptador não depende de nenhum componente de Ground Truth, nem de dependências de terceiros, operando exclusivamente via biblioteca padrão Python (`csv`, `pathlib`).

---

## 11. Estratégia de Micro-TDD

O desenvolvimento do adaptador será conduzido por ciclo estrito de Micro-TDD dividido em 3 fatias verticais progressivas:

### SLICE 1 — Estrutura de I/O e Validação Estrita de Cabeçalho
* **Foco:** Resolução de caminhos, leitura do cabeçalho e validação *fail-closed* da estrutura.
* **Casos de Teste Unitário:**
  * Caminho inexistente levanta `FileNotFoundError`;
  * Caminho que aponta para diretório levanta `IsADirectoryError`;
  * Arquivo contendo bytes não UTF-8 levanta `UnicodeDecodeError`;
  * Arquivo vazio (0 bytes) levanta `ValueError`;
  * Arquivo sem linhas legíveis de cabeçalho levanta `ValueError`;
  * Cabeçalho sem `material_id` levanta `ValueError`;
  * Cabeçalho com colunas desconhecidas fora de $\mathcal{C}_{\text{canonical}}$ levanta `ValueError`;
  * Cabeçalho com nomes de colunas repetidos levanta `ValueError`;
  * Arquivo contendo apenas cabeçalho canônico válido retorna `()`.

### SLICE 2 — Raw Mapping, Parsing Estrito e Casos de Borda de Linhas
* **Foco:** Mapeamento tabular direto para `MaterialRecord`, preservação de whitespace e tratamento de linhas.
* **Casos de Teste Unitário:**
  * Arquivo com todas as 8 colunas canônicas preenchidas mapeia corretamente todos os atributos;
  * Arquivo com subconjunto de colunas opcionais atribui `""` para as colunas ausentes no cabeçalho;
  * Preservação estrita de outer whitespace em `material_id` (ex.: `" MAT-01 "`);
  * Preservação estrita de outer whitespace e quebras de linha em `description_short`, `unit`, etc.;
  * Linha com células opcionais vazias no CSV recebe `""`;
  * Linha que termina antes do final das colunas declaradas utiliza semanticamente `restval=""`, sem propagar `None`;
  * Linha com mais campos/delimitadores que o cabeçalho levanta `ValueError`;
  * CSV com aspas não fechadas sob parser em modo estrito levanta `csv.Error`;
  * Preservação da ordem física original das linhas no arquivo;
  * Retorno é estritamente uma instância de `tuple`.

### SLICE 3 — Integração com o Pipeline de Diagnóstico (#149)
* **Foco:** Comprovar a integração suave entre o adaptador de entrada e o pipeline analítico da Issue #149.
* **Casos de Teste de Integração:**
  * Catálogo CSV válido é carregado via `load_catalog_materials` e injetado em `DiagnoseCatalogQualityUseCase.execute(catalog, catalog_id="cat-operational")`, produzindo um `CatalogQualityReport` correto com métricas e avaliações;
  * Catálogo CSV contendo `material_id` com espaços externos é carregado intacto pelo adaptador e rejeitado categoricamente por `DiagnoseCatalogQualityUseCase` (comprovando que o adaptador não saneia e que o domínio impõe a rejeição);
  * Catálogo CSV contendo `material_id` duplicado em linhas distintas é carregado intacto pelo adaptador e rejeitado categoricamente por `DiagnoseCatalogQualityUseCase` (comprovando que o domínio valida a unicidade catalog-wide).

> *Nota de Governança:* A contagem de testes não é uma meta quantitativa rígida pré-fixada. A suíte final emergirá da implementação disciplinada das três fatias de micro-TDD.

---

## 12. Definition of Done

- [x] Módulo `src/agent_lab/catalog_csv_adapter.py` criado contendo a função pública `load_catalog_materials`.
- [x] Implementação restrita à biblioteca padrão Python (`csv`, `pathlib`), com zero dependências externas.
- [x] Parsing CSV executado em modo estrito (`strict=True`).
- [x] Validação *fail-closed* do cabeçalho conforme $\mathcal{C}_{\text{canonical}}$, rejeitando colunas desconhecidas e duplicadas.
- [x] Preservação integral de dados brutos sem aplicação de `.strip()`.
- [x] Suíte de testes `tests/test_catalog_csv_adapter.py` implementando integralmente os testes das Slices 1, 2 e 3.
- [x] Preservação integral do baseline existente de 1173 testes (100% GREEN).
- [x] Conformidade estrutural do diff (`git diff --check` limpo).

---

## 13. Out of Scope

- Suporte a arquivos Excel (`.xlsx`, `.xls`), Parquet ou JSONL.
- Delimitadores alternativos (ponto-e-vírgula `;`, tabulação `\t`, pipe `|`).
- Heurísticas de detecção de dialeto via `csv.Sniffer`.
- Bibliotecas de terceiros como `pandas` ou `polars`.
- Inferência ou derivação de `catalog_id` a partir de nomes de arquivos.
- Serialização em JSON, persistência em disco ou exportação de `CatalogQualityReport`.
- Criação de comandos de CLI, endpoints REST ou interfaces Streamlit.
- Alterações em `DiagnoseCatalogQualityUseCase` ou no algoritmo analítico de diagnóstico.
- Modelos ou chamadas de LLM / Machine Learning.

---

## 14. Relação com a Issue #149

A **Issue #149** entregou o núcleo de processamento do diagnóstico (`DiagnoseCatalogQualityUseCase` e `CatalogQualityReport`).
A presente especificação (**Issue #154**) fornece o componente complementar de infraestrutura de entrada (*Input Adapter*):
$$\text{CSV Físico} \xrightarrow[\text{SPEC-0154}]{\text{load\_catalog\_materials}} \text{tuple[MaterialRecord, ...]} \xrightarrow[\text{SPEC-0149}]{\text{DiagnoseCatalogQualityUseCase}} \text{CatalogQualityReport}$$

---

## 15. Impacto Arquitetural

* **Localizado e Aditivo:** Introduz um único arquivo novo na camada de infraestrutura (`src/agent_lab/catalog_csv_adapter.py`) e uma nova suíte de testes (`tests/test_catalog_csv_adapter.py`).
* **Zero Mutação no Domínio:** Não altera `domain.py`, `catalog_quality.py` ou `catalog_quality_use_case.py`.
* **Desacoplamento de Benchmarking:** Mantém a infraestrutura de dados de teste rotulados (`data_io.py`) totalmente segregada da ingestão de dados de produção.

---

## 16. Riscos Arquiteturais e Mitigações

| Risco Identificado | Severidade | Estratégia de Mitigação |
| :--- | :--- | :--- |
| **Reparo silencioso de dados brutos** | Alta | Proibição explícita de `.strip()` no adaptador. Dados brutos entram inalterados e desvios de whitespace são julgados pelo domínio. |
| **Perda silenciosa de colunas corporativas** | Média | Adoção da política *Fail-Closed Canonical Schema*. Qualquer coluna desconhecida causa erro explícito no carregamento. |
| **Parsing permissivo de arquivos corrompidos** | Média | Utilização do parser CSV em modo estrito (`strict=True`) e verificação explícita de campos excedentes (`None in row`). |
| **Duplicação de invariantes do domínio** | Baixa | O adaptador limita-se a mapear texto para `MaterialRecord`. Unicidade, integridade e regras de negócio permanecem exclusivamente no domínio. |
| **Acoplamento com a trilha de Ground Truth** | Baixa | Criação de um módulo novo dedicado, sem reutilização de `LabeledMaterial` ou `data_io.py`. |

---

## 17. Evidências da Implementação

### 17.1 Decomposição e Execução por Fatias
A implementação foi conduzida em três fatias incrementais. Os Slices 1 e 2 seguiram ciclos explícitos RED → GREEN; o Slice 3 foi uma prova de integração adicionada após a implementação funcional e nasceu GREEN, demonstrando composição direta entre o adapter da Issue #154 e o pipeline da Issue #149 sem necessidade de nova lógica de produção.

* **Slice 1 (I/O & Validação Estrutural de Header):**
  * 8 testes;
  * Cobertura: existência de arquivo, rejeição de diretório, arquivo vazio, cabeçalho ausente, ausência da coluna obrigatória `material_id`, rejeição de colunas desconhecidas (fail-closed) e rejeição de colunas duplicadas.
* **Slice 2 (Raw Mapping, Strict Parsing & Edge Cases):**
  * 10 testes;
  * Cobertura: mapeamento para `MaterialRecord`, parsing com `strict=True`, preenchimento default com `restval=""`, rejeição de campos excedentes (`None in row`), preservação integral de whitespace externo e quebras de linha internas sem `.strip()`, e preservação da ordem física original das linhas.
* **Slice 3 (Integração com Pipeline de Diagnóstico #149):**
  * 3 testes de integração com `DiagnoseCatalogQualityUseCase`;
  * Todos nasceram GREEN;
  * Nenhuma alteração em `src/` foi necessária;
  * Isso é evidência de composição arquitetural, não um RED artificial.

* **Total específico da SPEC:** 21 testes (21/21 GREEN).

### 17.2 Baseline e Regressão
* **Baseline de entrada:** 1173 testes aprovados (100% GREEN)
* **Baseline funcional pré-integração:** 1194 testes aprovados (100% GREEN)
* **Runner oficial:** `python -m unittest discover -s tests -v`
* **Resultado:** 1194/1194 GREEN
* **Conformidade estrutural:** `git diff --check` limpo.

### 17.3 Conclusão Arquitetural e Separação de Responsabilidades
A integração ponta a ponta consolida a esteira operacional de ingestão e diagnóstico:
$$\text{CSV Físico} \xrightarrow[\text{SPEC-0154}]{\text{load\_catalog\_materials}} \text{tuple[MaterialRecord, ...]} \xrightarrow[\text{SPEC-0149}]{\text{DiagnoseCatalogQualityUseCase}} \text{CatalogQualityReport}$$

A fronteira de responsabilidades foi rigorosamente validada pelos testes:
* **ADAPTER (`load_catalog_materials`):**
  * parseia o CSV físico em modo estrito (`strict=True`);
  * valida a estrutura do cabeçalho contra o esquema canônico;
  * mapeia cada linha física para uma instância de `MaterialRecord`;
  * preserva integralmente o dado bruto textual, sem normalização ou `.strip()`.
* **DOMÍNIO / APLICAÇÃO (`DiagnoseCatalogQualityUseCase` & regras de qualidade):**
  * rejeita `material_id` com *outer whitespace*;
  * rejeita `material_id` duplicado em linhas distintas;
  * executa regras de governança e integridade relacional;
  * produz diagnóstico consolidado e métricas no `CatalogQualityReport`.
