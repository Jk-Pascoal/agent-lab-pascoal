# SPEC-POC-REPORT-001 — Contrato mínimo do relatório auditável da PoC (20/10/2026)

**Estado:** PROPOSED / DOCUMENT ONLY / AWAITING HUMAN ACCEPTANCE (D-01).  
**Natureza:** desenho de contrato, não implementação, validação nem aceite de macrofrente.  
**Entrada:** `docs/planning/agent_lab_poc_acceptance_matrix_20261019.md` (PR #196); auditoria da PR #195; `docs/PROJECT_COMPASS.md` (âncora experimental pós-B2).  
**Escopo:** reporting mínimo para demonstração sintética PDM/BOM; NÃO é relatório industrial validado.  
**Guarda:** sem alterações em `src/agent_lab/`, `tests/`, datasets, GT, T02 FROZEN, SR-001/#158, PR #191 DRAFT, KPI, percentuais ou datas históricas.

## 1. Objetivo e fronteira

Especificar um artefato versionado, determinístico e rastreável para que uma pessoa possa reconstruir **qual catálogo entrou**, **quais avaliações foram produzidas**, **quais evidências sustentam cada observação**, **o que o sistema recomendou** e **qual decisão humana foi efetivamente registrada** (se existir).

Este documento **não** declara que o exportador, a captura de linha de origem, a associação com revisão humana ou a demonstração ponta a ponta já existam. Especifica contratos **propostos** para uma implementação posterior, condicionada à decisão D-01 e revisão do exemplo de saída.

## 2. Inventário verificado em `main` antes do desenho

- `src/agent_lab/catalog_csv_adapter.py::load_catalog_materials(path)`: lê UTF-8 CSV com `csv.DictReader(strict=True)`, rejeita colunas desconhecidas/duplicadas, exige `material_id` e retorna `tuple[MaterialRecord, ...]` na ordem física dos **registros**; não produz mapa de números físicos de linha nem hash do arquivo.
- `src/agent_lab/domain.py`: `MaterialRecord` contém `material_id`, descrições, `unit`, `manufacturer`, `manufacturer_part_number`, `material_group` e `status`; `GovernanceAssessment` expõe `material_id`, `completeness`, `confidence`, `decision`, `normalized_description`, `suggested_group`, `issues`, `duplicate_candidates`, `evidence`, `evidence_collection`. `GovernanceIssue` expõe tipo, campo, mensagem e severidade.
- `src/agent_lab/catalog_quality_use_case.py::DiagnoseCatalogQualityUseCase.execute(catalog, *, catalog_id)` valida identidade e integridade do `CatalogQualityReport`; `src/agent_lab/catalog_quality.py` entrega avaliações ordenadas por `material_id`, contagens, razões opcionais e pares candidatos canônicos.
- `decision` de `GovernanceAssessment` é **recomendação do sistema** (`APPROVE | REVIEW | REJECT`), nunca autorização de mudança cadastral nem substituto de deliberação humana.
- A fronteira física que une catálogo, relatório exportado e eventos de revisão humana em um único artefato **não está demonstrada** pela presença desses modelos isolados. Não supor um join operacional inexistente.

## 3. Fluxo mínimo e estados de maturidade

```text
CSV físico --[adapter #154: I/G histórico]--> tuple[MaterialRecord]
         --[diagnóstico #149: I/G histórico]--> CatalogQualityReport
         --[NOVO serializador auditável: PROPOSED]--> arquivo JSON versionado + manifesto
         --[associação de revisão humana: PROPOSED]--> decisão registrada OU estado explícito não disponível
         --[demonstração sintética: PENDENTE]--> replay e aceite por humano
```

**Importante:** `CSV-only` é **candidato** ao escopo mínimo, não decisão D-01 aprovada. GT de benchmarking, assignment/lock/SLA e conectores Excel/SQL não são implicitamente implementados ou exigidos por esta SPEC; precisam de delimitação humana IN/OUT.

## 4. Envelope proposto `poc_audit_report.v0`

Campos marcados `REQUIRED` são requisitos **para futura implementação**, não afirmações sobre exportações atuais.

| Caminho lógico | Fonte pretendida | Regra proposta |
| --- | --- | --- |
| `schema_version` | exportador | REQUIRED; literal `poc_audit_report.v0`; leitura deve rejeitar versão desconhecida. |
| `catalog.catalog_id` | argumento do use case/resultado | REQUIRED; id canônico não vazio. Não inferir do nome do CSV. |
| `catalog.source_kind` | orquestrador | REQUIRED; `CSV` ou `UNKNOWN`; não declarar `CSV` sem prova. |
| `catalog.source_sha256` | etapa futura de custódia de bytes | `string` SHA-256 verificado ou `null` com `provenance_status=UNAVAILABLE`. Não gerar hash de conteúdo reformatado e apresentá-lo como hash do original. |
| `catalog.source_ref` | orquestrador | identificador lógico, sem caminho secreto obrigatório; `null` se ausente. |
| `catalog.provenance_status` | gate de custódia | `VERIFIED | PARTIAL | UNAVAILABLE`. Estado é obrigatório e não deve ser inferido por valor default otimista. |
| `engine.source_commit` | executor/orquestrador | SHA de código efetivamente executado, ou `null` e `execution_trace_status=UNAVAILABLE`. |
| `engine.execution_trace_status` | executor | `VERIFIED | UNAVAILABLE`; sem inventar run ID/hora. |
| `summary` | `CatalogQualityReport` | `total_records`, `clean_records_count`, `records_with_blocking_issues_count`, `records_with_non_blocking_issues_count`, `duplicate_candidate_records_count`, `total_issues_count`, `duplicate_pairs_count`, `clean_records_ratio`, `average_completeness`; razões `null` em catálogo vazio. |
| `records[]` | `assessments` em ordem de `material_id` | REQUIRED; cada material exatamente uma vez, sem reordenação implícita por CSV. |
| `duplicate_pairs[]` | `CatalogQualityReport.duplicate_pairs` | cada par não dirigido uma única vez e ordenado; **candidato** a duplicidade, não duplicata comprovada. |
| `limitations[]` | contrato de relatório | REQUIRED; limites do método, falta de validação semântica ou cobertura de origem nunca omitidos. |

### Registro por material — campos mínimos

- `material_id` (único); `recommendation` (enum `GovernanceDecision` do domínio); `completeness` e `confidence` (números entre 0 e 1, sem converter confidence em acurácia calibrada).
- `normalized_description`, `suggested_group`, `issues[]` com `issue_type`, `field_name`, `message`, `severity`; `duplicate_candidates[]` em ordem canônica; `evidence[]` como texto original do modelo.
- `source_row`: número físico inteiro positivo **somente** se um mapeamento verificável `material_id -> physical_row` for explicitamente capturado e auditado em uma etapa futura; caso contrário `null`, com `source_row_status=UNAVAILABLE`. **Nunca** usar o índice de `assessments` ou o índice ordenado por `material_id` como número de linha de arquivo.
- `human_review`: objeto com `status=NOT_RECORDED | RECORDED | UNAVAILABLE`; `decision`, `actor_ref`, `event_ref` nulos se não houver evento confirmado. `NOT_RECORDED` não significa `APPROVED`; somente evento auditável associado à identidade e ao contexto correto pode sustentar `RECORDED`.
- `evidence_collection` **não** é serializada com `repr()` ou por reflexão arbitrária: contrato de projeção tipada ainda será definido; usar `evidence_projection_status=NOT_DEFINED` enquanto não houver desenho aceito.

### Exemplo de estrutura **ilustrativa**, não saída de execução

```json
{
  "schema_version": "poc_audit_report.v0",
  "catalog": {
    "catalog_id": "DEMO-SINTETICA",
    "source_kind": "UNKNOWN",
    "source_ref": null,
    "source_sha256": null,
    "provenance_status": "UNAVAILABLE"
  },
  "engine": {"source_commit": null, "execution_trace_status": "UNAVAILABLE"},
  "summary": {
    "total_records": 0,
    "clean_records_count": 0,
    "records_with_blocking_issues_count": 0,
    "records_with_non_blocking_issues_count": 0,
    "duplicate_candidate_records_count": 0,
    "total_issues_count": 0,
    "duplicate_pairs_count": 0,
    "clean_records_ratio": null,
    "average_completeness": null
  },
  "records": [],
  "duplicate_pairs": [],
  "limitations": [
    "Exemplo de contrato sem execução, arquivo de origem ou decisão humana.",
    "Nenhuma precisão/recall industrial nem prontidão para 100 mil SKUs foram demonstrados."
  ]
}
```

Este exemplo usa um catálogo vazio porque o `CatalogQualityReport` permite `assessments=()`; todos os valores mostrados são **hipotéticos** para discutir o schema, não observações nem output de CI.

## 5. Regras de auditabilidade e segurança

1. **Identidade:** conjunto de `material_id` no relatório = conjunto do `CatalogQualityReport`; ids únicos, sem campos inventados. Falha deve abortar exportação.
2. **Proveniência:** hash de origem verificado somente a partir dos bytes exatos (e com cadeia de custódia documentada); se ausente, registrar `UNAVAILABLE`; nunca deduzir `source_row` do ordenamento do diagnóstico.
3. **Determinismo:** serialização JSON UTF-8 com ordenação estável do envelope, registros, issues e pares conforme contrato; campos voláteis (`generated_at`, execução física) devem ser explicitamente segregados do conteúdo canônico comparável.
4. **Semântica:** `POSSIBLE_DUPLICATE` e `duplicate_candidates` são hipóteses de triagem; decisão de `REVIEW` não prova duplicidade ou correção automática.
5. **Ação humana:** `recommendation` e `human_review.decision` são entidades separadas; status de revisão desconhecido não pode ser representado como aceite.
6. **Falha segura:** versão desconhecida, identidades desencontradas, pares órfãos, enum inválido e divergência entre contagens e detalhes devem rejeitar artefato como inválido; a evidência original não é substituída.
7. **Dados:** dataset demonstrativo apenas sintético; sem exposição de segredos corporativos/PNs reais; anonimização e acesso precisam de contrato separado se houver dados privados.
8. **Custódia:** relatório e manifesto futuramente produzidos deverão carregar hash do próprio artefato e referências de input; hash de relatório não substitui hash de CSV.

## 6. Critérios de aceite futuro — verificáveis

| Gate | Ensaio proposto | Evidência exigida |
| --- | --- | --- |
| R1 — shape/versionamento | Envelope válido, versão desconhecida rejeitada | teste de schema e serialização |
| R2 — identidade | catálogo vazio, IDs únicos, ordenação, conjunto completo | testes de limites/consistência |
| R3 — métricas | contagens e pares exatamente iguais ao `CatalogQualityReport`; razões `null` para vazio | testes de equivalência |
| R4 — proveniência | origem sem hash e sem linha registra `UNAVAILABLE`; mapa físico falso é rejeitado | testes negativos |
| R5 — reversibilidade | replay de mesmas entradas/commit produz payload canônico idêntico | dois runs com hashes comparados |
| R6 — recomendação ≠ decisão | recomendação `APPROVE` + nenhuma revisão mantém `NOT_RECORDED` | teste de segurança |
| R7 — situações adversas | CSV com esquema inválido falha antes do relatório; exportador não produz sucesso parcial | testes de falha |
| R8 — proteção metodológica | sem T02/GT SR-001 na fixture da PoC; sem claims sobre B2 ou 100k SKUs | inspeção de custódia |
| R9 — demo E2E | arquivo CSV sintético versionado → adapter → diagnóstico → relatório → revisão humana rastreada, com logs e artefatos | execução documentada + sign-off |
| R10 — CI | suíte `python -m unittest discover -s tests -v` e novos testes do exportador | execução GREEN da nova implementação |

**Estado de R1–R10 em 20/10:** `PROPOSED / NOT EXECUTED`. O baseline histórico de 1.194 testes **não** equivale à validação destes gates.

## 7. Decisões pendentes e sequência sem antecipar aprovação

- **D-01 (humana):** definir IN/OUT do MVP: CSV-only? Qual etapa GT é mandatória para a demo? Revisão humana exige assignment/locking/SLA ou não? A presente SPEC não responde em nome do proprietário do projeto.
- **D-02:** aceitar o shape acima ou solicitar alteração; decidir o vínculo confiável de `human_review` com material/catálogo e o mapa de linha física (necessário para declarar proveniência por linha).
- Após D-01/D-02: implementar projeção pura/serializador, testes unitários de todos os gates e fixture sintética **própria da PoC**; executar CI, depois demo e aceites.
- **D-03/D-04:** somente após aceite, reconciliar progresso e previsões em campos separados das datas históricas, sem mudar peso de SR-001.
- **D-05:** distinguir produto PoC demonstrável de v0.1.0 histórica, de SaaS e de escala industrial.

**STOP / delimitação:** não é aprovação de código, não é autorização de teste experimental, não é mudança no Compass, na PR #191, na Issue #158, nas métricas SR-001, nos testes, nos CSVs congelados, no cronograma ou no KPI. A integração documental apenas torna explícito um contrato futuro a revisar.
