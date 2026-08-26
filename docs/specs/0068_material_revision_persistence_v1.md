# SPEC-0068 — Material Revision Persistence v1

> Especificação técnica para persistência local, durável, append-only e fail-closed
> de revisões factuais de materiais (`MaterialRevision`) no Agent Lab Pascoal.

## Metadados

| Campo | Valor |
| --- | --- |
| Identificador | `SPEC-0068` |
| Status | `Implementada, Validada e Integrada na main` |
| Issue relacionada | `#68` |
| Responsável | `Jk-Pascoal` |
| Data de criação | `2026-08-26` |
| Última atualização | `2026-08-26` |
| Baseline de entrada | `347 testes aprovados` |
| Runner oficial | `unittest` / Python 3.11 |

---

## 1. Contexto

O Agent Lab Pascoal é um sistema experimental de engenharia para governança de materiais industriais PDM/BOM. O baseline atual integrado na branch `main` possui **347 testes aprovados** (`unittest`, Python 3.11) e consolida:

- validação cadastral determinística e fronteira LLM estruturada com guardrails de identidade;
- Evidence Engine multiorigem (`RULE`, `VALIDATION`, `DUPLICATE`, `LLM`) e pipeline de recomendação determinístico com `requires_human_decision = True`;
- deliberação humana estruturada via `HumanReview` com `VerifiedSpecialistIdentity`;
- persistência durável append-only de auditoria (`AuditEvent` com `schema_version = 1` e `JsonlAuditRepository`);
- ciclo de vida temporal de governança em memória (`GovernanceWorkflow`);
- persistência durável append-only de abertura e conclusão de ciclo de vida (`WorkflowOpened` v1/v2, `WorkflowConcluded` v1 e `JsonlWorkflowLifecycleRepository`);
- projeção determinística de reidratação (`rehydrate_workflow`) reconstruindo `GovernanceWorkflow` em `PENDING_HUMAN_REVIEW` e `REVIEWED`;
- verificação somente-leitura de consistência cruzada dual-write (`verify_dual_write_consistency`, `verify_repositories_consistency`);
- linhagem causal de follow-up pós-correção com persistência versionada (`schema_version = 2` na Issue #61);
- **contrato factual de proveniência de revisões de material em memória integrado na Issue #64:** módulo `src/agent_lab/material_revision.py`, definindo o dataclass congelado `MaterialRevision` (`revision_id`, `record: MaterialRecord`, `revised_at` timezone-aware, `predecessor_revision_id`, `source_review_id`, propriedade `material_id`) e a função pura de transição `create_successor_revision`.

Baseline oficial verificado:

```text
Ran 347 tests in 1.550s
OK
```

Runner oficial:

```powershell
python -m unittest discover -s tests -v
```

---

## 2. Problema, evidências e impacto

### Problema

Atualmente, `MaterialRevision` e `create_successor_revision` operam exclusivamente em memória. Quando o processo é reinicializado ou finalizado, todos os snapshots cadastrais revisionados e seus vínculos declarados de linhagem/proveniência são perdidos:

1. Inexistência de formato canônico e versionado de serialização para `MaterialRevision`;
2. Inexistência de repositório local em disco para armazenar e recuperar o histórico de revisões factuais;
3. Ausência de garantias de durabilidade (`flush` + `os.fsync`) e de integridade *fail-closed* com identificação de `line_number` em caso de corrupção física ou estrutural.

### Evidências

- `src/agent_lab/material_revision.py` define o contrato puro em memória, mas não contém rotinas de serialização ou repositório de persistência;
- Inexistência dos módulos `src/agent_lab/material_revision_serialization.py` e `src/agent_lab/material_revision_repository.py`;
- `docs/PROJECT_COMPASS.md` registrava a persistência de revisões entre as fronteiras deliberadamente adiadas após a Issue #64; em 26/08/2026, após reentrada operacional com 347 testes verdes, essa frente foi formalmente escolhida pelo planejamento humano como a próxima âncora funcional.

### Impacto

- Impossibilidade de manter o histórico cadastral de materiais através de restarts da aplicação;
- Impossibilidade de preparar a esteira evolutiva para alimentar futuras avaliações de qualidade cadastral sobre revisões persistidas.

---

## 3. Hipótese

A introdução de uma camada de serialização versionada (`schema_version = 1`) e de um repositório local append-only (`JsonlMaterialRevisionRepository`), seguindo os mesmos padrões de confiabilidade adotados em `AuditRepository` e `WorkflowLifecycleRepository`, permitirá persistir e recuperar instâncias de `MaterialRevision` de forma durável e determinística após reinicializações do processo, mantendo o snapshot bruto de `MaterialRecord` e os identificadores de proveniência semântica inalterados e sem introduzir acoplamentos indevidos com o pipeline avaliador ou com o fluxo de governança.

---

## 4. Objetivo

Implementar a persistência local, versionada, append-only e *fail-closed* para `MaterialRevision`:

1. Definir o formato serializado versionado com `schema_version = 1` explícito em `src/agent_lab/material_revision_serialization.py`;
2. Implementar as funções puras `material_revision_to_record` e `material_revision_from_record` com round-trip preservando a equivalência temporal e semântica;
3. Preservar integralmente todos os 8 campos brutos de `MaterialRecord` sem normalização, exigindo tipos string estritos na fronteira de serialização;
4. Definir o protocolo `MaterialRevisionRepository` e a implementação concreta `JsonlMaterialRevisionRepository` em `src/agent_lab/material_revision_repository.py`;
5. Assegurar durabilidade com escrita append-only, `flush` e `os.fsync`;
6. Garantir unicidade de `revision_id` no repositório com bloqueio de duplicidades (`DuplicateMaterialRevisionError`);
7. Implementar leitura *fail-closed* que acuse corrupção com `line_number` (`MaterialRevisionCorruptionError`);
8. Validar recuperação através de restart simulado por nova instância do repositório sobre o mesmo arquivo JSONL persistido;
9. Manter 100% dos 347 testes existentes verdes.

---

## 5. Escopo

### Incluído

- **Módulo de Serialização (`src/agent_lab/material_revision_serialization.py`):**
  - Constante `SCHEMA_VERSION_V1 = 1`;
  - Função pura `material_revision_to_record(revision: MaterialRevision) -> dict[str, object]`;
  - Função pura `material_revision_from_record(record: Mapping[str, object]) -> MaterialRevision`;
  - Suporte com round-trip aos três cenários canônicos:
    - Root Revision (`predecessor_revision_id=None`, `source_review_id=None`);
    - Derived Revision (`predecessor_revision_id` preenchido, `source_review_id=None`);
    - Review-Associated Derived Revision (`predecessor_revision_id` e `source_review_id` preenchidos);
  - Preservação exata de todos os 8 campos de `MaterialRecord` (`material_id`, `description_short`, `long_description`, `unit`, `manufacturer`, `manufacturer_part_number`, `material_group`, `status`) exigindo tipos string estritos na serialização sem coerção implícita (`str(value)`) e sem normalização ou `strip()`;
  - Serialização de `revised_at` em ISO 8601 preservando a equivalência temporal e offset timezone-aware no round-trip (sem exigir identidade de classe de `tzinfo`);
  - Validação fail-closed de `schema_version`, tipos e campos obrigatórios.
- **Módulo de Repositório (`src/agent_lab/material_revision_repository.py`):**
  - Hierarquia de exceções: `MaterialRevisionPersistenceError`, `DuplicateMaterialRevisionError`, `MaterialRevisionCorruptionError(line_number)`;
  - Protocolo `MaterialRevisionRepository` com métodos:
    - `append(revision: MaterialRevision) -> None`;
    - `get_by_id(revision_id: str) -> MaterialRevision | None`;
    - `list_by_material(material_id: str) -> tuple[MaterialRevision, ...]`;
    - `list_all() -> tuple[MaterialRevision, ...]`;
  - Implementação concreta `JsonlMaterialRevisionRepository(path: Path)`;
  - Preservação estrita da ordem física de inserção (append) nos métodos de listagem, sem ordenação por `revised_at`;
  - Criação automática de diretórios pai na persistência;
  - Durabilidade por linha com `flush` e `os.fsync`;
  - Validação estrita de unicidade global de `revision_id` no repositório;
  - Leitura *fail-closed* acusando linha vazia, JSON malformado, formato não-mapeamento, violação de schema ou campos incompatíveis com identificação precisa do `line_number`.
- **Suíte de Testes:**
  - `tests/test_material_revision_serialization.py`: testes unitários de serialização, round-trip e validações fail-closed;
  - `tests/test_material_revision_repository.py`: testes unitários do protocolo, repositório append-only, ordem física, unicidade, consultas e corrupções;
  - `tests/test_material_revision_persistence_integration.py`: teste de integração validando múltiplos restarts simulados por novas instâncias do repositório sobre o mesmo arquivo JSONL persistido.

---

## 6. Fora do escopo

Em estrita consonância com os princípios constitucionais do Agent Lab:

1. **`Repository ≠ Projection`:** O repositório apenas persiste e recupera registros individuais em ordem física de inserção. Nenhuma projeção agregada, reconstrução de grafo de revisões, árvore de precedência ou ordenação por timestamp é executada na recuperação;
2. **`CorrectionRequest ≠ MaterialRevision`:** Nenhuma aplicação automática, execução de correções (`apply_corrections`) ou semântica `CORRECTION_APPLIED` é introduzida;
3. **Proveniência Declarada:** `source_review_id` e `predecessor_revision_id` são identificadores contextuais declarados. Não há validação cruzada contra `AuditRepository`, `WorkflowLifecycleRepository` ou `HumanReview`;
4. **Sem Prova Causal ou de Cumprimento:** A persistência de `source_review_id` não atesta que a revisão existiu, que a decisão foi `REQUEST_CORRECTION` ou que correções foram cumpridas;
5. **Sem Conceito de "Latest Revision" / Ordenação Cronológica:** O repositório não ordena por `revised_at` e não introduz métodos ou índices para identificar a "última revisão";
6. **Sem Armazenamento de Diff:** Não persistir `diff`, `changed_fields` ou `revision_number`;
7. **Sem Conexão ao Pipeline Avaliador:** `MaterialRevision` não é conectada a `EvidenceCollection` ou `DecisionRecommendation`;
8. **Sem Reexecução de Regras/LLM:** Nenhuma execução de regras ou LLM é acionada por eventos de persistência;
9. **Sem Transações / Concorrência Distribuída:** Sem 2PC entre repositórios, locking multiprocesso ou banco relacional;
10. **Sem Subprocesso / Sem ERP / Filas / SLA / RBAC:** O teste de restart opera via instanciação de repositório em memória sobre o mesmo arquivo sem execução de subprocessos; todas as fronteiras externas permanecem adiadas.

---

## 7. Requisitos funcionais

- `RF-01` — **Serialização canônica:** `material_revision_to_record` deve serializar `MaterialRevision` em dicionário com `schema_version = 1`, `revision_id`, `record` (sub-objeto), `revised_at` (ISO 8601), `predecessor_revision_id` e `source_review_id`.
- `RF-02` — **Preservação e validação de tipos de `MaterialRecord`:** `material_revision_to_record` e `material_revision_from_record` devem preservar os 8 campos de `MaterialRecord` exatamente como fornecidos, sem aplicação de `strip()`, coerção implícita para string ou normalização textual. `material_revision_to_record` deve falhar explicitamente (`ValueError`) caso algum dos 8 campos de `MaterialRecord` não seja uma string.
- `RF-03` — **Desserialização fail-closed:** `material_revision_from_record` deve reconstruir a instância de `MaterialRevision`. Caso o registro possua campos ausentes, tipos inválidos, `schema_version` diferente de `1`, timestamps naive ou dados que violem as invariantes de `MaterialRevision`, deve levantar `ValueError`.
- `RF-04` — **Round-trip e equivalência temporal:** O ciclo `material_revision_from_record(material_revision_to_record(revision))` deve produzir um objeto com equivalência semântica e temporal idêntica à instância original (mesmo instante e offset timezone-aware), sem exigir a identidade exata da instância de `tzinfo`.
- `RF-05` — **Protocolo de Repositório:** `MaterialRevisionRepository` deve definir os métodos `append`, `get_by_id`, `list_by_material` e `list_all`.
- `RF-06` — **Persistência Append-Only:** `JsonlMaterialRevisionRepository.append` deve serializar e acrescentar o registro ao final do arquivo JSONL configurado.
- `RF-07` — **Durabilidade explícita:** `append` deve executar `flush()` e `os.fsync()` no descritor de arquivo e criar os diretórios pai caso não existam.
- `RF-08` — **Unicidade de `revision_id`:** `append` deve verificar os registros existentes e levantar `DuplicateMaterialRevisionError` se já existir uma revisão com o mesmo `revision_id`.
- `RF-09` — **Leitura por identificador:** `get_by_id(revision_id)` deve retornar a `MaterialRevision` correspondente ou `None` caso não encontrada.
- `RF-10` — **Listagem por material em ordem física:** `list_by_material(material_id)` deve retornar uma tupla contendo todas as `MaterialRevision` do material informado, preservando a ordem física de inserção (append) no arquivo, sem ordenação por `revised_at`.
- `RF-11` — **Listagem geral em ordem física:** `list_all()` deve retornar uma tupla com todas as revisões persistidas no arquivo, preservando a ordem física de inserção (append), sem ordenação por `revised_at`.
- `RF-12` — **Detecção de corrupção fail-closed:** `JsonlMaterialRevisionRepository` deve levantar `MaterialRevisionCorruptionError` contendo o atributo `line_number` em caso de linha vazia, JSON inválido, registro não-objeto, erro de schema ou incompatibilidade de dados.
- `RF-13` — **Sobrevivência a restart simulado:** Uma nova instância de `JsonlMaterialRevisionRepository` apontando para um arquivo JSONL existente deve recuperar com sucesso todas as revisões persistidas por instâncias anteriores mantendo a ordem física de gravação.

---

## 8. Requisitos de qualidade

- `RQ-01` — **Imutabilidade e tipos:** Resultados de listagem devem ser retornados como `tuple` imutáveis contendo instâncias congeladas de `MaterialRevision`.
- `RQ-02` — **Isolamento de Domínio:** A camada de serialização e repositório não altera o contrato nem os métodos de `MaterialRevision`, `create_successor_revision` e `MaterialRecord`. As validações de tipos string para os 8 campos de `MaterialRecord` pertencem estritamente à fronteira de serialização/persistência v1.
- `RQ-03` — **Desempenho e Confiabilidade:** I/O síncrono com garantia de flush físico em disco por operação de escrita.
- `RQ-04` — **Não-regressão:** Preservação estrita do baseline de 347 testes verdes executados via `python -m unittest discover -s tests -v`.

---

## 9. Modelo canônico do registro JSON

O envelope de persistência segue a versão `schema_version = 1` como obrigatória:

```json
{
  "schema_version": 1,
  "revision_id": "REV-001",
  "record": {
    "material_id": "MAT-001",
    "description_short": "PARAFUSO SEXTAVADO M8",
    "long_description": "PARAFUSO SEXTAVADO M8 X 25MM ACO INOX",
    "unit": "UN",
    "manufacturer": "ACME",
    "manufacturer_part_number": "ACM-825",
    "material_group": "FIXADORES",
    "status": "ACTIVE"
  },
  "revised_at": "2026-08-26T10:00:00+00:00",
  "predecessor_revision_id": null,
  "source_review_id": null
}
```

### Especificação dos Campos

| Campo | Tipo JSON | Obrigatório | Descrição / Regra |
| --- | --- | --- | --- |
| `schema_version` | `integer` | Sim | Deve ser exatamente `1`. Ausência, tipo diferente ou outros valores levantam `ValueError`. Não há suporte a schemas legados sem versão. |
| `revision_id` | `string` | Sim | Identificador único da revisão. Deve ser string não-vazia após `strip()`. |
| `record` | `object` | Sim | Objeto encapsulando os dados de `MaterialRecord`. Deve conter os 8 campos. |
| `record.material_id` | `string` | Sim | Identificador do material. Deve ser string não-vazia. |
| `record.description_short` | `string` | Sim | Descrição curta bruta. Deve ser string (aceita vazia). |
| `record.long_description` | `string` | Sim | Descrição longa bruta. Deve ser string (aceita vazia). |
| `record.unit` | `string` | Sim | Unidade cadastral bruta. Deve ser string (aceita vazia). |
| `record.manufacturer` | `string` | Sim | Fabricante bruto. Deve ser string (aceita vazia). |
| `record.manufacturer_part_number` | `string` | Sim | Código do fabricante bruto. Deve ser string (aceita vazia). |
| `record.material_group` | `string` | Sim | Grupo de mercadoria bruto. Deve ser string (aceita vazia). |
| `record.status` | `string` | Sim | Status cadastral bruto. Deve ser string (aceita vazia). |
| `revised_at` | `string` | Sim | Timestamp no formato ISO 8601. Reconstituído obrigatoriamente como `datetime` timezone-aware. |
| `predecessor_revision_id` | `string` ou `null` | Sim | Identificador da revisão predecessora. `null` para root; string não-vazia para derived. |
| `source_review_id` | `string` ou `null` | Sim | Identificador de proveniência de deliberação. `null` para root e derived puras; string não-vazia apenas se `predecessor_revision_id` estiver preenchido. |

---

## 10. Taxonomia de erros

A persistência de revisões adota uma hierarquia explícita de exceções:

```text
Exception
   └── MaterialRevisionPersistenceError
            ├── DuplicateMaterialRevisionError
            └── MaterialRevisionCorruptionError (com line_number: int)
```

### Categorização dos Erros

1. **Erros de Chamada / API (Validação de Parâmetros):**
   - Tipos inválidos de argumentos passados para métodos públicos (`append`, `get_by_id`, etc.) levantam `TypeError` ou `ValueError`.
2. **Erros de Domínio e Desserialização:**
   - Payloads com violações de tipos, campos faltantes, campos de `MaterialRecord` com tipos não-string, `schema_version` ausente ou inválido, ou violações das regras do dataclass `MaterialRevision` levantam `ValueError` em `material_revision_from_record`.
   - `material_revision_to_record` levanta `ValueError` se `MaterialRevision.record` contiver campos não-string, recusando coerções silenciosas.
3. **Erros de Corrupção Persistida:**
   - Durante a leitura do arquivo no repositório, falhas de decodificação JSON, linhas vazias ou `ValueError` oriundos da desserialização são capturados e re-empacotados como `MaterialRevisionCorruptionError`, informando explicitamente o `line_number`.
4. **Erros Físicos de I/O:**
   - Falhas de sistema operacional (`OSError`, permissão, disco cheio) são capturadas e re-empacotadas como `MaterialRevisionPersistenceError`.
5. **Erros de Conflito de Identidade:**
   - Tentativa de gravar um `revision_id` já existente no repositório levanta `DuplicateMaterialRevisionError`.

---

## 11. Estratégia TDD

A implementação seguirá ciclo estrito de micro-TDD em fatias incrementais:

```text
Fatia 1 (RED → GREEN) — Serialização e Desserialização de Root Revision
Fatia 2 (RED → GREEN) — Serialização e Desserialização de Derived e Review-Associated Revisions
Fatia 3 (RED → GREEN) — Validações Fail-Closed de Schema, Tipos de MaterialRecord e Invariantes
Fatia 4 (RED → GREEN) — Repositório Append-Only e Operações de Consulta (Ordem Física)
Fatia 5 (RED → GREEN) — Detecção de Duplicidade, Erros de I/O e Corrupção com Line Number
Fatia 6 (RED → GREEN) — Integração Ponta a Ponta com Múltiplos Restarts Simulados
Regressão Geral       — python -m unittest discover -s tests -v (347 + novos testes)
```

### Detalhamento das Fatias

- **Fatia 1 — Serialização Root Revision (`tests/test_material_revision_serialization.py`):**
  - Teste de `material_revision_to_record` para Root Revision gerando dicionário canônico com `schema_version = 1`, `predecessor_revision_id = None`, `source_review_id = None`;
  - Teste de `material_revision_from_record` reconstituindo fielmente a Root Revision;
  - Teste de round-trip para Root Revision com equivalência temporal e semântica.
- **Fatia 2 — Derived e Review-Associated Revisions (`tests/test_material_revision_serialization.py`):**
  - Teste de serialização e desserialização de Derived Revision com `predecessor_revision_id`;
  - Teste de serialização e desserialização de Review-Associated Revision com `predecessor_revision_id` e `source_review_id`;
  - Teste de round-trip completo preservando todos os 8 campos de `MaterialRecord` e equivalência de timestamp timezone-aware.
- **Fatia 3 — Fail-Closed de Schema e Tipos (`tests/test_material_revision_serialization.py`):**
  - Rejeição de `record` que não seja mapping;
  - Rejeição de ausência ou invalidade de `schema_version` (versão desconhecida, string, bool, ausência de schema);
  - Rejeição de campos faltantes no envelope ou em `record`;
  - Rejeição de tipos não-string nos campos de `MaterialRecord` tanto na serialização quanto na desserialização (sem coerção `str()`);
  - Rejeição de timestamp naive ou ISO inválido;
  - Rejeição de inconsistências de proveniência (`source_review_id` sem `predecessor_revision_id`).
- **Fatia 4 — Repositório Append-Only e Consultas (`tests/test_material_revision_repository.py`):**
  - Teste do protocolo `MaterialRevisionRepository` e instanciação de `JsonlMaterialRevisionRepository`;
  - Gravação de revisões com criação de diretório pai e verificação de JSONL durável;
  - Teste de `get_by_id` para identificadores existentes e inexistentes;
  - Teste de `list_by_material` filtrando por material e preservando a ordem física de append no arquivo (sem ordenação por `revised_at`);
  - Teste de `list_all` retornando tupla preservando a ordem física de append no arquivo (sem ordenação por `revised_at`).
- **Fatia 5 — Duplicidades e Corrupção (`tests/test_material_revision_repository.py`):**
  - Teste de rejeição de `revision_id` duplicado (`DuplicateMaterialRevisionError`);
  - Teste de arquivo com linha vazia levantando `MaterialRevisionCorruptionError` com `line_number`;
  - Teste de arquivo com JSON corrompido levantando `MaterialRevisionCorruptionError` com `line_number`;
  - Teste de registro não-dicionário levantando `MaterialRevisionCorruptionError` com `line_number`;
  - Teste de registro com schema inválido levantando `MaterialRevisionCorruptionError` com `line_number`.
- **Fatia 6 — Integração e Restarts Simulados (`tests/test_material_revision_persistence_integration.py`):**
  - Teste criando repositório A, persistindo Root Revision e Derived Revision sucessora via `create_successor_revision`;
  - Simulação de restart instanciando repositório B sobre o mesmo arquivo JSONL e recuperando os registros com igualdade semântica estrita na mesma ordem física de inserção;
  - Persistência de uma terceira revisão via repositório B e revalidação com repositório C.

---

## 12. Critérios de aceite

- [x] Suíte existente de 347 testes preservada 100% GREEN;
- [x] Novos testes implementados exclusivamente via `unittest` em Python 3.11;
- [x] Round-trip completo de Root Revision, Derived Revision e Review-Associated Revision;
- [x] Todos os 8 campos de `MaterialRecord` preservados de forma exata e não-modificada, com rejeição estrita de tipos não-string sem coerção silenciosa;
- [x] `revised_at` timezone-aware preservado com equivalência semântica e offset temporal;
- [x] `schema_version = 1` obrigatório e validado; ausência de versão ou versões desconhecidas rejeitadas;
- [x] `JsonlMaterialRevisionRepository` executando escrita append-only com `flush` e `os.fsync`;
- [x] Rejeição estrita de `revision_id` duplicado com `DuplicateMaterialRevisionError`;
- [x] Leitura *fail-closed* reportando `line_number` em caso de corrupção ou incompatibilidade de dados;
- [x] Consultas `get_by_id`, `list_by_material` e `list_all` operando fielmente, retornando tuplas imutáveis e preservando a ordem física de append;
- [x] Teste de integração comprovando sobrevivência de revisões após múltiplos restarts simulados por novas instâncias do repositório sobre o mesmo arquivo JSONL;
- [x] Nenhuma semântica de aplicação automática de correções e nenhuma validação cruzada de `source_review_id`.

---

## 13. Riscos e limitações

| Risco ou Limitação | Severidade | Mitigação Arquitetural |
| --- | --- | --- |
| Supor que persistir `predecessor_revision_id` prova existência do predecessor | Alta | Documentação e testes explícitos estabelecendo que `predecessor_revision_id` é linhagem declarada sem consulta ou travessia no repositório (`Repository ≠ Projection`). |
| Supor que persistir `source_review_id` comprova existência, decisão ou cumprimento de `HumanReview` | Alta | Documentação explícita de que `source_review_id` é proveniência declarada sem validação cruzada contra `AuditRepository`. |
| Normalização silenciosa ou coerção de `MaterialRecord` na persistência | Média | Rejeição explícita de tipos não-string sem coerção `str()` e testes comprovando round-trip literal dos 8 campos. |
| Inconsistência de fuso horário em `revised_at` | Média | Rejeição estrita de datetimes naive e validação de equivalência temporal via ISO 8601. |

---

## 14. Impacto arquitetural

A arquitetura do Agent Lab ganha a capacidade de persistência durável para snapshots factuais de materiais sem adicionar camadas desnecessárias de complexidade:

```text
MaterialRevision (domínio puro)
        ↓
material_revision_to_record (serialização versionada v1)
        ↓
JsonlMaterialRevisionRepository (append-only com fsync)
        ↓
[ Restart simulado por nova instância ]
        ↓
JsonlMaterialRevisionRepository (leitura fail-closed)
        ↓
material_revision_from_record
        ↓
MaterialRevision (semanticamente equivalente)
```

Nenhum contrato existente (`MaterialRecord`, `GovernanceWorkflow`, `AuditEvent`, `WorkflowOpened`, `WorkflowConcluded`, `DecisionRecommendation`) é alterado.

---

## 15. Plano de implementação

### Arquivos previstos

1. `docs/specs/0068_material_revision_persistence_v1.md` — Esta especificação técnica;
2. `src/agent_lab/material_revision_serialization.py` — Serialização e desserialização versionada v1 de `MaterialRevision`;
3. `src/agent_lab/material_revision_repository.py` — Protocolo e repositório JSONL append-only;
4. `tests/test_material_revision_serialization.py` — Testes unitários de serialização;
5. `tests/test_material_revision_repository.py` — Testes unitários do repositório;
6. `tests/test_material_revision_persistence_integration.py` — Teste de integração de persistência e restart simulado.

---

## 16. Histórico de decisões

| Data | Decisão | Motivo | Responsável |
| --- | --- | --- | --- |
| 2026-08-26 | Adoção de `schema_version = 1` explícito e obrigatório | Evitar ambiguidades e garantir comportamento fail-closed desde a primeira versão serializada. | `Jk-Pascoal` |
| 2026-08-26 | Preservação integral e literal dos 8 campos de `MaterialRecord` com checagem de tipo string | Respeitar a fonte da verdade factual sem coerção silenciosa ou mutação na persistência. | `Jk-Pascoal` |
| 2026-08-26 | Preservação estrita da ordem física de append nas listagens | Não inventar ordenação temporal por `revised_at` nem conceito de latest revision (`Repository ≠ Projection`). | `Jk-Pascoal` |
| 2026-08-26 | Validação de equivalência temporal timezone-aware sem exigir identidade de `tzinfo` | Garantir precisão temporal sem acoplamento a implementações específicas de timezone. | `Jk-Pascoal` |
| 2026-08-26 | Validação de restart simulada por nova instância do repositório | Testar a sobrevivência em disco pós-instanciação sem expandir o escopo com subprocessos. | `Jk-Pascoal` |
| 2026-08-26 | Tratamento de `predecessor_revision_id` e `source_review_id` como proveniência declarada | Evitar acoplamento com repositórios externos de auditoria ou ciclo de vida. | `Jk-Pascoal` |
