# POC-REPORT — Revisão adversarial de D-02 e matriz de rastreabilidade (21/10/2026)

**Estado:** TECHNICAL REVIEW / DECISION SUPPORT / D-01+D-02 PENDING / NO ACCEPTANCE.  
**Escopo:** inspeção estática do contrato `SPEC-POC-REPORT-001` (20/10, PR #197) contra quatro módulos reais da `main` em `9b926e652f87bee994f236d4e53e3288d53f3a1e`.  
**Natureza:** documentação verificável, sem execução de testes, sem geração de relatório e sem aprovação por inferência.  
**Prazo histórico do marco `report`:** 25/10/2026 — não replanejado; ainda não há exportador demonstrado.

## 1. Pergunta operativa e evidência disponível

**Pergunta:** quais evidências faltam para que o contrato de relatório possa virar uma implementação mínima sem inventar origem de linhas, decisões humanas ou maturidade da PoC?

| Fonte inspecionada em `main` | Fato constatado por leitura do código | Implicação para a SPEC |
| --- | --- | --- |
| `src/agent_lab/catalog_csv_adapter.py` | `load_catalog_materials` usa `csv.DictReader(strict=True)`, retorna apenas `tuple[MaterialRecord, ...]` na ordem dos registros e não retorna manifesto, hash, offset nem linha física | `source_row`, `source_sha256`, `source_ref` e `source_kind` não podem ser declarados como verificados por esse retorno isolado |
| `src/agent_lab/catalog_quality_use_case.py` | `execute(..., catalog_id=...)` canonicaliza o id, verifica tipo/identidade do relatório e compara ids ordenados da entrada e saída | Há gate relacional de identidades; não há associação de linha CSV, evento humano ou proveniência física |
| `src/agent_lab/catalog_quality.py` | `CatalogQualityReport` valida ids únicos e ordenados, candidatos existentes/simétricos, deriva contagens/razões e `duplicate_pairs` | Métricas e pares podem ser projetados fielmente; a integridade interna não prova origem do arquivo nem duplicidade verdadeira |
| `src/agent_lab/domain.py` | `GovernanceAssessment.decision` é `GovernanceDecision` (APPROVE/REVIEW/REJECT), com `issues`, `evidence`, `duplicate_candidates` e `evidence_collection` opcional | Trata-se de **recomendação algorítmica**, não de aprovação humana; projeção tipada de `evidence_collection` continua indefinida |

**Regra de interpretação:** presença de atributos no modelo ≠ existência de um exportador, vínculo auditável entre eventos ou demonstração E2E. A revisão não alterou código nem afirmou ter executado os módulos.

## 2. Cinco riscos de implementação a tratar antes do código

### F1 — Linha física não equivale à posição na coleção

O `DictReader` pode consumir um **registro lógico CSV que ocupa várias linhas físicas** (campo com quebra de linha entre aspas). A ordenação por `material_id` no diagnóstico também difere da ordem do arquivo. Assim, nem índice da tupla nem índice de `assessments` servem como `source_row`.

- **Contrato de segurança:** quando não há mapa físico comprovado, exportar `source_row=null` e `source_row_status=UNAVAILABLE`. Nunca produzir um inteiro plausível sem sua cadeia de custódia.
- **Escolha D-02:** definir se `source_row` futuro será a **linha inicial física** do registro (recomendado para localização humana) ou outro marcador, e como registrar linhas multilinha/cabeçalhos.
- **Prova futura:** CSV sintético com cabeçalho, linhas simples, campo multilinha citado e linhas vazias; comparar início físico rastreado com fonte original e demonstrar que reordenação por `material_id` não altera o mapa.
- **Limite:** `csv.reader.line_num` por si só indica linhas já lidas, não autoriza rotulá-lo automaticamente como início físico do registro.

### F2 — Hash do arquivo ≠ hash do objeto decodificado

O adaptador recebe caminho e lê texto UTF-8; não devolve bytes originais. Reconstituir CSV a partir de `MaterialRecord` não preserva bytes, delimitadores, BOM, escapes ou terminadores.

- **Contrato de segurança:** `source_sha256` apenas sobre os **bytes exatos** do arquivo cuja identidade foi capturada; caso contrário `null` e `provenance_status=UNAVAILABLE`.
- **Escolha D-02:** quem captura o snapshot imutável do input e como evitar troca de arquivo entre hash e parse (TOCTOU).
- **Prova futura:** mesmo conteúdo lógico com finais de linha diferentes não pode receber falsamente a mesma identidade física; modificar o arquivo entre captura e leitura deve rejeitar `VERIFIED`.

### F3 — Assinatura do relatório e manifesto exigem objetos separados

Um relatório que contém seu próprio hash pode criar dependência circular na canonicalização. Além disso, timestamp de geração e dados de execução voláteis quebram comparabilidade byte-a-byte.

- **Contrato de segurança:** payload JSON canônico e **manifesto destacado**, cujo campo `report_sha256` referencia os bytes fechados do payload. Hash do CSV de origem é outro campo, nunca sinônimo de hash do relatório.
- **Escolha D-02:** ordem das chaves, separadores, UTF-8, política de `null`, newline final, ordenação de `issues`/`records` e segregação explícita do contexto volátil.
- **Prova futura:** duas projeções idênticas geram payload byte-a-byte igual; alteração de um campo muda o digest; entrada inconsistente rejeita exportação sem arquivo `success`.

### F4 — Recomendação do algoritmo ≠ decisão humana

A `GovernanceAssessment` não contém referência a `HumanReview` no fluxo CSV → diagnóstico inspecionado. Uma recomendação `APPROVE` nunca pode implicar uma revisão humana `APPROVED`.

- **Contrato de segurança:** manter `recommendation` independente de `human_review` e `human_review.status=NOT_RECORDED | RECORDED | UNAVAILABLE`. `RECORDED` depende de evento verificável, vinculado ao **catálogo, material, workflow/revisão e contexto temporal correto**.
- **Escolha D-01/D-02:** quais mecanismos HITL entram no MVP e que prova de associação autoriza `RECORDED`, sem presumir assignment/locking/SLA.
- **Prova futura:** recomendação `APPROVE` sem evento registrado deve resultar em `NOT_RECORDED`, sem ator/decisão inventados; evento de outro material/catálogo deve falhar fechado.

### F5 — Métrica estrutural não é qualidade semântica industrial

`duplicate_pairs_count` e `duplicate_candidate_records_count` refletem **candidatos heurísticos** no catálogo analisado; `confidence` não é precisão calibrada. Nenhuma dessas contagens mede diretamente acurácia, precision, recall ou F1 contra Ground Truth independente.

- **Contrato de segurança:** rótulos explícitos de candidato/triagem e seção `limitations[]` obrigatória; razões de catálogo vazio permanecem `null`, não `0`.
- **Escolha D-01:** determinar se Ground Truth é obrigatório na demo mínima; se não, declarar claramente o que a demo **não** valida.
- **Prova futura:** par candidato não é apresentado como duplicidade confirmada; nenhuma inferência de validação para 100 mil SKUs ou SR-001 é permitida.

## 3. Matriz de aceitação R1–R10 — estado nesta revisão

| Gate SPEC-POC-REPORT-001 | Evidência existente | Evidência que falta | Situação |
| --- | --- | --- | --- |
| R1 versão/schema | Envelope v0 **proposto** em Markdown | Implementação + rejeição de versão desconhecida | PENDING |
| R2 identidade | Trust boundary no use case e read-model de domínio | Prova no **exportador** para vazio, duplicatas e ordenação | PENDING |
| R3 métricas | Propriedades de `CatalogQualityReport` | Projeção fiel + testes de equivalência e `null` | PENDING |
| R4 proveniência | Adapter CSV sem mapa/hash | Custódia física + ensaios adversariais F1/F2 | PENDING |
| R5 replay | Contrato determinístico proposto | Dois payloads gerados e digests idênticos | PENDING |
| R6 recomendação/revisão | Modelo de recomendação existente | Associação de evento humano sem falso aceite | PENDING |
| R7 falhas | Validação de entrada no adapter | Falha atômica do **futuro** exportador | PENDING |
| R8 segregação SR-001 | Issue #158 e PR #191 em trilha separada | Inspeção de fixture PoC sem T02/GT congelados | PENDING |
| R9 demo E2E | Componentes em memória e adapter | Fixture, orquestração, exportador, revisão rastreada, replay, sign-off | PENDING |
| R10 CI | Baseline histórico de 1194 testes de produto | Execução dos testes **novos** e CI do incremento | PENDING |

**Não classificar nenhuma linha como PASS** com base apenas nesta revisão ou no baseline histórico.

## 4. Registro de decisões para o proprietário — sem autorização presumida

| ID | Decisão requerida | Alternativa conservadora para discussão | Estado |
| --- | --- | --- | --- |
| D-01A | CSV-only entra como input mínimo da PoC? | CSV-only como escopo MVP; Excel/SQL continuam fora e visivelmente pendentes | HUMAN DECISION REQUIRED |
| D-01B | Quais gates de GT/HITL são obrigatórios na demo? | Exigir revisão humana rastreada, sem atribuir características inexistentes à infraestrutura | HUMAN DECISION REQUIRED |
| D-02A | Linha física: definição e custódia | Linha inicial física + `UNAVAILABLE` até instrumentação verificável | HUMAN DECISION REQUIRED |
| D-02B | Associação do evento humano ao relatório | `NOT_RECORDED` sem vínculo auditado; nenhum join heurístico | HUMAN DECISION REQUIRED |
| D-02C | Shape/manifesto e projeção de evidências | Payload fechado + manifesto destacado; evidência tipada só após contrato aceito | HUMAN DECISION REQUIRED |
| D-03/D-04 | Progressos e previsão revisada | Preservar baseline/prazo original e registrar previsão em campo separado após aceite | HUMAN DECISION REQUIRED |

## 5. Sequência recomendada após aceites, não iniciada

1. Registrar decisão assinada D-01/D-02 e fronteira exata IN/OUT (incluindo F1–F5).
2. Especificar e congelar fixture sintética própria da PoC, sem reutilizar T02/GT experimental.
3. Implementar a menor projeção pura com invariantes R1–R3 e R5–R6; usar estados `UNAVAILABLE` enquanto custódia não existir.
4. Implementar custódia física CSV e manifesto apenas com semântica de linha/hash resolvida e ensaios de falha adversarial.
5. Executar R1–R10, registrar logs/CI e demo reproduzível; somente depois avaliar marco `report` e rebaseline do Crono.

## 6. Invariantes e fechamento da atividade de 21/10

- Revisão documental por leitura estática, sem artefato de execução, teste local, benchmark, claim de sucesso E2E ou aceite humano.
- Nenhuma mudança em `src/agent_lab/`, `tests/`, `experiments/`, T02 FROZEN, Ground Truth, algoritmos, dados reais, SR-001/Issue #158, PR #191 DRAFT ou `PROJECT_COMPASS.md`.
- Issue #158 permanece experimental, `weight=0`, `KPI=0`; resultados B2/T02 continuam **post-hoc**, não industrialmente validados.
- 1194/1194 (produto) e 40/40 (instrumental legado) são **baselines históricos**, não reexecutados neste registro.
- Prazo `report` de 25/10 e meta PoC de 20/11 permanecem datas históricas **não revalidadas**.
- Esta entrega constitui **preparação concreta de D-02**, não aprovação, serializador implementado, alteração de status de cronograma nem conclusão de macrofrente.

**Âncora de reentrada:** próxima sessão deve tratar D-01/D-02 primeiro; não iniciar coding nem promover DRAFT #191 sem HUMAN GO explícito.
