# SPEC-0109 — Human Review Claim Release Persistence v1

> Especificação técnica da persistência local, durável, append-only e fail-closed
> dos fatos de liberação voluntária de claim de revisão humana (`HumanReviewClaimRelease`) no Agent Lab Pascoal.

---

## Metadados

| Campo | Valor |
|---|---|
| **Identificador** | `SPEC-0109` |
| **Status** | `PROPOSED` |
| **Issue relacionada** | `#109` |
| **Título da Issue** | `Human Review Claim Release Persistence v1` |
| **Branch funcional** | `feature/issue-109-human-review-claim-release-persistence` |
| **Responsável** | `Jk-Pascoal` |
| **Data de criação** | `2026-09-08` |
| **Última atualização** | `2026-09-08` |
| **Baseline de entrada** | `595 testes aprovados` (100% GREEN) |
| **Runner oficial** | `python -m unittest discover -s tests -v` (Python 3.11.9) |

---

## 1. Contexto

O **Agent Lab Pascoal** consolida uma esteira de governança assistida de cadastros industriais PDM/BOM orientada pelo princípio:

```text
Repository preserva → Projection interpreta → Policy governa → Application coordena e aplica
```

O baseline atual integrado na branch `main` conta com **595 testes aprovados** (Python 3.11.9 / `unittest`).
Na trilha de assunção operacional de revisão humana (*Human Review Claim*), o sistema entregou recentemente a **Issue #106** (PR funcional #107, merge `f093ae9`; PR documental #108, merge `6948708`), que introduziu o contrato puro de domínio em memória:
- Dataclass imutável `HumanReviewClaimRelease` (`release_id`, `claim_id`, `workflow_id`, `released_by: VerifiedSpecialistIdentity`, `released_at: datetime`);
- Operação pura de domínio `release_human_review_claim(workflow, claim, *, release_id, releasing_specialist, released_at) -> HumanReviewClaimRelease`.

Atualmente, o fato `HumanReviewClaimRelease` existe estritamente em memória. Para que o fluxo de governança operacional possua rastreabilidade histórica durável e viabilize reconstituição consistente após interrupções de serviço, faz-se necessário implementar sua persistência durável em trilha append-only dedicada.

---

## 2. Problema, Justificativa e Impacto

### 2.1 Problema
1. **Volatilidade de memória:** Fatos de liberação voluntária de claim de revisão por especialistas verificados são descartados ao término da execução ou reinicialização do processo;
2. **Ausência de formato serializado:** Não existe representação versionada canônica para codificar e decodificar instâncias de `HumanReviewClaimRelease` em meio persistente;
3. **Ausência de armazenamento durável e auditável:** Inexiste repositório append-only local para preservar o histórico físico de releases com integridade *fail-closed*.

### 2.2 Justificativa e Prioridade de Entrega
A persistência durável de releases é uma **prioridade de entrega de durabilidade física** e tolerância a falhas. Projeções puras em memória operam teoricamente sobre sequências abstratas de objetos, mas em tempo de execução real os fatos de liberação necessitam de sobrevivência em disco para que o histórico do laboratório seja auditável e recuperável após encerramento do processo.

### 2.3 Isolamento da Trilha e Preservação de Schemas
A persistência de releases deve ser implementada em **arquivo JSONL dedicado** (ex.: `human_review_claim_releases.jsonl`), e não no arquivo existente de claims (`JsonlHumanReviewClaimRepository`):
- O repositório de claims opera com `schema_version = 1` fechado (*closed schema*); misturar registros exigiria converter a trilha em polimórfica (discriminador `event_type`), forçando migração retroativa ou aumentando o risco de quebra;
- Assunção (`HumanReviewClaim`) e liberação (`HumanReviewClaimRelease`) são fatos de naturezas ontológicas distintas;
- A trilha dedicada preserva a imutabilidade dos esquemas v1 existentes de claims, lifecycle e auditoria.

---

## 3. Limites de Confiabilidade e Escopo Operacional

Para evitar ambiguidades e expectativas irreais de confiabilidade:

1. **Durabilidade via `flush` + `fsync`:** Toda gravação física em disco força o esvaziamento de buffers da aplicação (`file.flush()`) e solicita a sincronização do descritor de arquivo no sistema operacional (`os.fsync(file.fileno())`).
2. **Ausência de Garantia contra Toda Escrita Parcial:** Falhas abruptas de hardware, sistema ou energia durante o ciclo de gravação física podem deixar bytes incompletos ou linhas truncadas em disco. O sistema não possui journaling transacional ou rollback automático para evitar escritas parciais nessas circunstâncias extremas; a leitura subsequente acusará a anomalia de forma estritamente *fail-closed*.
3. **Sem Atomicidade Transacional ACID:** A implementação é append-only local simples; não possui suporte a transações distribuídas (2PC), write-ahead logging (WAL) ou rollback automático.
4. **Sem Reparo Automático:** Corrupções físicas ou violações estruturais nunca são reconciliadas ou reparadas silenciosamente; o comportamento é estritamente *fail-closed*.
5. **Sem Garantias de Concorrência Multiprocesso:** A implementação é síncrona e desenhada para ambiente de processo único. Não há distributed locking, travas interprocesso (IPC) ou coordenação contra múltiplos processos escrevendo concorrentemente no mesmo arquivo físico.
6. **Recuperação por Nova Instância vs. Restart Real de Processo:** Os testes automatizados de integração validam a reconstituição fiel do estado a partir do arquivo persistido através da criação de uma **nova instância fresca do repositório** após o fechamento formal dos handles de arquivo da instância anterior, sem compartilhamento de cache ou estado em memória. Não se exige a execução de subprocessos do SO para sustentar essa evidência.

---

## 4. Invariantes Constitucionais e Arquiteturais

1. **`HumanReviewClaimRelease != HumanReviewClaim`:** O release registra a liberação voluntária de um claim prévio; não se confunde com o fato de assunção.
2. **`RELEASED CLAIM != REVIEWED WORKFLOW`:** Liberar o claim não altera o ciclo de vida temporal do workflow (`WorkflowStatus.PENDING_HUMAN_REVIEW` permanece inalterado; `review is None`).
3. **`release factual != active claim semantics`:** O repositório apenas preserva os fatos físicos na ordem de append; ele **não** elege claim ativo, não determina vigência, exclusividade ou ownership, e não aplica desempates (First-Claim-Wins / Last-Claim-Wins).
4. **`Repository preserva fatos físicos | Projection interpreta`:** O repositório armazena a história bruta e não aplica regras de negócio ou de autoridade normativa.
5. **Trilha Persistente Dedicada:** Registros gravados em arquivo JSONL próprio, sem alteração em `JsonlHumanReviewClaimRepository`, `JsonlWorkflowLifecycleRepository` ou `JsonlAuditRepository`.
6. **Unicidade Estrita Exclusivamente por `release_id`:** O repositório impede a inserção de registros cujo `release_id` já conste no arquivo (`DuplicateHumanReviewClaimReleaseError`).
7. **Permissão de Múltiplos Releases para o Mesmo `claim_id`:** O repositório **tolera** gravações de releases distintos que apontem para o mesmo `claim_id` (desde que com `release_id`s diferentes). O repositório append-only apenas preserva fatos físicos; não introduz nesta fatia regra de unicidade por `claim_id`.
8. **Retornos e Ordem Física:**
   - O método `get_by_id(release_id)` retorna `HumanReviewClaimRelease | None`;
   - Os métodos `list_by_claim_id(claim_id)`, `list_by_workflow_id(workflow_id)` e `list_all()` retornam tuplas imutáveis (`tuple[HumanReviewClaimRelease, ...]`) na ordem física exata de append no arquivo;
   - Métodos filtrados realizam varredura linear e não prometem índice nem economia de leitura global.
9. **Preservação Exata de Identificadores:** `claim_id` e `workflow_id` são preservados exatamente como fornecidos no contrato da Issue #106, sem aplicação de `.strip()` ou normalizações que alterem sua identidade textual. A validação de parâmetros de consulta exige string não-vazia (sem coerção silenciosa de booleanos) e compara por igualdade textual exata (`==`).
10. **Validação Integral do Arquivo em Todas as Operações:** Tanto as consultas (`get_by_id`, `list_by_claim_id`, `list_by_workflow_id`, `list_all`) quanto a verificação preliminar ao `append` validam **integralmente** todas as linhas do arquivo existente antes de qualquer retorno ou escrita:
    - Nenhum retorno antecipado pode mascarar corrupção em linhas posteriores: se o registro procurado for válido na linha 1, mas a linha 2 contiver JSON malformado ou corrupção, a consulta falha com `HumanReviewClaimReleaseCorruptionError(line_number=2)`;
    - Se houver `release_id` duplicado no arquivo em disco, a leitura levanta `HumanReviewClaimReleaseCorruptionError` apontando o `line_number` físico da segunda ocorrência;
    - Se o arquivo estiver corrompido, o `append` é abortado antes da abertura do arquivo para escrita, garantindo **zero escritas** adicionais em arquivo danificado;
    - Se o arquivo estiver íntegro mas o novo `release_id` já existir, levanta `DuplicateHumanReviewClaimReleaseError` sem escrever no disco.

---

## 5. Fronteira entre Invariantes Internas e Validações Relacionais

- **Invariantes Internas do Registro (Responsabilidade da Serialização e Persistência):**
  - Campos obrigatórios do envelope presentes e tipos estritos;
  - `schema_version`: inteiro estrito igual a `1` (rejeitar `bool`, `float`, `str`, ausência e versões desconhecidas);
  - Rejeição de chaves desconhecidas (*closed schema*) tanto no envelope root quanto no sub-mapeamento `released_by`;
  - `release_id`, `claim_id`, `workflow_id` como strings não-vazias;
  - `released_at` como datetime timezone-aware em formato ISO 8601;
  - `released_by` estruturado fielmente como `VerifiedSpecialistIdentity` com strings não-vazias e `verified_at` timezone-aware;
  - Consistência temporal interna do release: `released_by.verified_at <= released_at`.
- **Validações Relacionais de Domínio (Fora da Persistência):**
  - Equivalência de Stable Principal entre `released_by` e claimant original;
  - Validação de que o workflow correspondente está em `PENDING_HUMAN_REVIEW`;
  - Validação de não-retroatividade em relação ao claim (`released_at >= claim.claimed_at`);
  - Coerência de `workflow.workflow_id == claim.workflow_id`.

> **Princípio Epistemológico:** A desserialização de um registro de release atesta exclusivamente sua validade sintática, tipagem e coerência cronológica interna. **Desserializar não comprova nem atesta que a operação pura de domínio `release_human_review_claim` foi executada previamente no contexto global do sistema.**

---

## 6. Contratos e Desenho Técnico

### 6.1 Módulo de Serialização (`src/agent_lab/human_review_claim_release_serialization.py`)

#### Constante e Chaves Fechadas
```python
SCHEMA_VERSION_V1 = 1

_ROOT_REQUIRED_FIELDS = frozenset(
    {"schema_version", "release_id", "claim_id", "workflow_id", "released_by", "released_at"}
)

_SPECIALIST_REQUIRED_FIELDS = frozenset(
    {
        "specialist_id",
        "identity_provider",
        "identity_subject",
        "verification_id",
        "verified_at",
    }
)
```

#### Regras Estritas de `schema_version`
- Deve satisfazer: `type(schema_version) is int and not isinstance(schema_version, bool) and schema_version == SCHEMA_VERSION_V1`;
- Valores booleanos (`True`/`False`), floats (`1.0`), strings (`"1"`), ausência da chave ou versões diferentes de `1` disparam `ValueError`.

#### Envelope Serializado Canônico (JSON)
```json
{
  "schema_version": 1,
  "release_id": "REL-001",
  "claim_id": "CLM-001",
  "workflow_id": "WF-001",
  "released_by": {
    "specialist_id": "SPEC-001",
    "identity_provider": "CORPORATE_IDP",
    "identity_subject": "user-12345",
    "verification_id": "VER-001",
    "verified_at": "2026-09-08T10:00:00+00:00"
  },
  "released_at": "2026-09-08T10:05:00+00:00"
}
```

#### Funções de Serialização
```python
def human_review_claim_release_to_record(
    release: HumanReviewClaimRelease,
) -> dict[str, object]:
    """Converte instância imutável de HumanReviewClaimRelease em dicionário canônico versionado v1."""
    ...

def human_review_claim_release_from_record(
    record: Mapping[str, object],
) -> HumanReviewClaimRelease:
    """Reconstitui HumanReviewClaimRelease a partir de mapeamento versionado, aplicando closed-schema e fail-closed."""
    ...
```

### 6.2 Módulo de Repositório (`src/agent_lab/human_review_claim_release_repository.py`)

#### Taxonomia Canônica de Erros
1. **Entradas Inválidas e Erros de Desserialização:**
   - `TypeError`: tipos incorretos de argumentos passados às funções e métodos;
   - `ValueError`: argumentos vazios, mapeamentos com chaves extras/ausentes, datas malformadas ou inconsistência temporal interna.
2. **Erros de Persistência e Falhas Físicas:**
   - `HumanReviewClaimReleasePersistenceError(Exception)`: exceção base de persistência; captura e encapsula falhas físicas de E/S (`OSError` em leitura, escrita, abertura, flush ou fsync) via `from exc`, sem convertê-las indiscriminadamente em corrupção.
3. **Duplicidade Lógica no Append:**
   - `DuplicateHumanReviewClaimReleaseError(HumanReviewClaimReleasePersistenceError)`: levantada quando o `release_id` a ser gravado já existe em arquivo íntegro (zero escritas).
4. **Corrupção de Conteúdo Persistido:**
   - `HumanReviewClaimReleaseCorruptionError(HumanReviewClaimReleasePersistenceError)`: levantada ao encontrar sequências de bytes UTF-8 inválidas, linhas vazias, JSON malformado, formato não-dicionário, violações de schema ou IDs duplicados no arquivo em disco, contendo obrigatoriamente `line_number: int` (1-based).

#### Protocolo Abstrato
```python
@runtime_checkable
class HumanReviewClaimReleaseRepository(Protocol):
    def append(self, release: HumanReviewClaimRelease) -> None:
        """Persiste um release de forma append-only e durável, validando o arquivo existente."""
        ...

    def get_by_id(self, release_id: str) -> HumanReviewClaimRelease | None:
        """Recupera release por release_id exato, validando a integridade integral do arquivo."""
        ...

    def list_by_claim_id(self, claim_id: str) -> tuple[HumanReviewClaimRelease, ...]:
        """Retorna todos os releases para o claim_id fornecido na ordem física de append."""
        ...

    def list_by_workflow_id(self, workflow_id: str) -> tuple[HumanReviewClaimRelease, ...]:
        """Retorna todos os releases para o workflow_id fornecido na ordem física de append."""
        ...

    def list_all(self) -> tuple[HumanReviewClaimRelease, ...]:
        """Retorna todos os releases persistidos na ordem física exata de append."""
        ...
```

#### Implementação Concreta: `JsonlHumanReviewClaimReleaseRepository`
- Construtor recebe `path: Path`;
- Leitura e validação integral `list_all() -> tuple[HumanReviewClaimRelease, ...]`:
  - Se arquivo não existe ou tamanho zero: retorna tupla vazia `()`;
  - Tratamento de `OSError`: encapsulado em `HumanReviewClaimReleasePersistenceError(f"Failed to inspect/read file {self._path}: {exc}") from exc`;
  - Itera sobre linhas físicas em modo binário (1-based);
  - Decodifica cada linha em UTF-8, convertendo `UnicodeDecodeError` em `HumanReviewClaimReleaseCorruptionError(..., line_number=line_number)`;
  - Rejeita linhas vazias ou puramente em branco com `HumanReviewClaimReleaseCorruptionError(..., line_number=line_number)`;
  - Decodifica JSON (`json.loads`), rejeitando malformações com `HumanReviewClaimReleaseCorruptionError(..., line_number=line_number)`;
  - Exige dicionário (`isinstance(record, dict)`), rejeitando outros tipos com `HumanReviewClaimReleaseCorruptionError(..., line_number=line_number)`;
  - Desserializa via `human_review_claim_release_from_record(record)`, capturando `ValueError` e convertendo em `HumanReviewClaimReleaseCorruptionError(..., line_number=line_number)`;
  - Rastreia conjunto de `seen_release_ids`: se `release.release_id in seen_release_ids`, levanta `HumanReviewClaimReleaseCorruptionError(f"Duplicate release_id '{release.release_id}' detected at line {line_number}", line_number=line_number)`;
  - Retorna tupla imutável `tuple[HumanReviewClaimRelease, ...]` na ordem física de append;
- Procedimento Estrito de `append(release)`:
  1. Valida tipo de entrada `isinstance(release, HumanReviewClaimRelease)` e `not isinstance(release, bool)` (`ValueError` / `TypeError`);
  2. Valida integralmente o arquivo existente em disco executando `list_all()`; qualquer anomalia física ou estrutural aborta o append imediatamente (zero escritas);
  3. Verifica unicidade lógica: se algum registro existente possuir `r.release_id == release.release_id`, levanta `DuplicateHumanReviewClaimReleaseError` (zero escritas);
  4. Prepara e valida o novo registro serializado em memória (`record = human_review_claim_release_to_record(release)`) e formata linha JSON (`line = json.dumps(record)`);
  5. Somente após a validação bem-sucedida do registro e do arquivo existente, cria diretórios pais (`self._path.parent.mkdir(parents=True, exist_ok=True)`);
  6. Se o arquivo preexistente possuir tamanho superior a zero e seu último byte não for quebra de linha LF (`\n`), insere delimitador `\n` antes do novo registro (`\n{line}\n`), preservando os bytes anteriores intactos (inclusive em arquivos com terminação CR isolada ou sem newline); abre o arquivo em modo `"a"` com codificação UTF-8 e `newline="\n"` para prevenir conversões de quebra de linha dependentes do sistema operacional, escreve o registro formatado, executa `file.flush()` e `os.fsync(file.fileno())`; falhas de E/S capturadas como `OSError` propagam como `HumanReviewClaimReleasePersistenceError` via `from exc`.
- Consultas `get_by_id`, `list_by_claim_id`, `list_by_workflow_id`:
  - Validam que o parâmetro de busca é string não-vazia (`isinstance(val, str) and not isinstance(val, bool) and bool(val.strip())`), mas utilizam o valor exato original sem strip para a comparação textual;
  - Invocam `list_all()`, garantindo varredura e validação integral do arquivo;
  - Retornam `()` (ou `None` no caso de `get_by_id`) quando o arquivo for inexistente ou vazio;
  - `get_by_id` retorna a instância correspondente ou `None`;
  - `list_by_claim_id` e `list_by_workflow_id` retornam tuplas imutáveis na ordem física exata de append.

---

## 7. Escopo e Limites

### 7.1 Incluído no Incremento
1. Módulo `src/agent_lab/human_review_claim_release_serialization.py` com envelope versionado v1;
2. Funções `human_review_claim_release_to_record` e `human_review_claim_release_from_record`;
3. Módulo `src/agent_lab/human_review_claim_release_repository.py` com hierarquia de exceções dedicadas, protocolo abstrato e classe concreta JSONL;
4. Métodos `append`, `get_by_id`, `list_by_claim_id`, `list_by_workflow_id` e `list_all`;
5. Bloqueio de duplicidade por `release_id` antes da escrita;
6. Validação completa do arquivo em disco em todas as leituras e appends (fail-closed diante de corrupção, linhas vazias, schemas inválidos ou duplicidade física);
7. Preparação e validação completa do registro em memória antes de criar diretórios ou abrir o arquivo para append;
8. Suíte de testes unitários para serialização e repositório;
9. Teste de integração vertical comprovando sobrevivência física em disco e reconstituição dos valores contratuais por nova instância do repositório;
10. Exportação pública dos novos símbolos em `src/agent_lab/__init__.py`;
11. Preservação integral do baseline de 595 testes existentes sem regressões.

### 7.2 Fora do Escopo
- Casos de uso da camada de aplicação para liberação de claims;
- Projeção de claims ativos e políticas normativas de claims ativos;
- Unicidade ou exclusividade por claim no repositório de releases;
- Alteração nos repositórios, projeções, políticas ou casos de uso existentes de claims, lifecycle ou auditoria;
- Mecanismos de locking, leases temporais, expiração de claims ou acordos de nível de serviço (SLA);
- Concorrência multiprocesso, distributed locking ou atomicidade transacional;
- Interfaces gráficas, APIs REST ou CLI.

---

## 8. Estratégia TDD e Fatias de Implementação

### Fatia 1: Serialização e Desserialização Versionada v1
- **Vermelho:** Criação de `tests/test_human_review_claim_release_serialization.py` testando round-trip contratual de valores e tipos, validação estrita de `schema_version = 1` (rejeitando bool, float, str, ausência e versões desconhecidas), closed-schema no envelope e no `released_by`, rejeição de strings vazias, formatação ISO 8601 com timezone e validação cronológica interna (`released_by.verified_at <= released_at`).
- **Verde:** Implementação de `src/agent_lab/human_review_claim_release_serialization.py`.

### Fatia 2: Protocolo, Exceções e Repositório JSONL Append-Only
- **Vermelho:** Criação de `tests/test_human_review_claim_release_repository.py` testando persistência append-only, durabilidade `fsync`, métodos de consulta (`get_by_id`, `list_by_claim_id`, `list_by_workflow_id`, `list_all`), bloqueio de `release_id` duplicado no append, detecção de corrupção com `line_number` 1-based, bloqueio de append em arquivo corrompido, e validação de que consultas acusam corrupção mesmo que a linha procurada seja válida e anterior à corrupção.
- **Verde:** Implementação de `src/agent_lab/human_review_claim_release_repository.py`.

### Fatia 3: Integração Vertical por Nova Instância e Exportações Públicas
- **Vermelho:** Criação de `tests/test_human_review_claim_release_persistence_integration.py` simulando o fluxo de vida completo: criação de release via domínio `release_human_review_claim` $\rightarrow$ gravação durável via repositório $\rightarrow$ encerramento de handles $\rightarrow$ instanciação fresca do repositório sobre o mesmo arquivo em disco $\rightarrow$ verificação de equivalência de valores de todos os campos e consultas; teste de integridade com múltiplos releases para o mesmo claim.
- **Verde:** Ajuste final de exportações em `src/agent_lab/__init__.py` e verificação da suíte completa.

---

## 9. Riscos e Limitações Conhecidas

| Risco ou Limitação | Impacto | Controle e Mitigação |
|---|---|---|
| Escrita física interrompida abruptamente no SO (queda de energia / processo terminado) | Alto | `file.flush()` seguido de `os.fsync()` força a sincronização pelo SO, mas falhas durante o ciclo de gravação física podem deixar registros truncados em disco. Não há rollback automático; a leitura subsequente diagnostica o registro truncado como corrupção fail-closed (`HumanReviewClaimReleaseCorruptionError`), impedindo leituras e escritas adicionais. |
| Consulta ignorar corrupção no final do arquivo | Alto | `list_all()` realiza varredura integral obrigatória de todas as linhas do arquivo antes de retornar qualquer consulta pontual ou filtrada. |
| Gravação sobre arquivo corrompido | Alto | `append` executa `list_all()` antes de preparar diretórios ou abrir o arquivo para escrita; se houver corrupção, a operação aborta sem gravar novos dados. |
| Múltiplos processos gravando no mesmo arquivo | Alto | Limitação formal declarada: projeto single-process, sem garantias de concorrência multiprocesso nesta fase. |

---

## 10. Pendência Documental Vinculada à #106

O trecho residual na Seção 17 do [PROJECT_COMPASS.md](file:///C:/Users/Administrador/agent-lab-pascoal/docs/PROJECT_COMPASS.md#L1185-L1187) decorre da conclusão documental da Issue #106. Ao formalizar o estado atual nesta branch:
- O incremento funcional atual passa a referenciar formalmente a **Issue #109** aberta;
- A Seção 17 e a Seção 1 do Compass registram a conclusão da Issue #106 (PRs #107 e #108 integrados) e refletem o trabalho em andamento da Issue #109, eliminando a frase residual "permanece aberta até o merge do PR documental" e evitando inserir "nenhum incremento aberto" enquanto a Issue #109 estiver em curso.

---

## 11. Critérios de Aceite Globais

- [x] SPEC-0109 revisada e formalizada na branch `feature/issue-109-human-review-claim-release-persistence`;
- [x] Serialização versionada v1 de `HumanReviewClaimRelease` com round-trip comprovado sem mutação de tipos ou valores;
- [x] `schema_version` validado estritamente como inteiro `1` (rejeitando bool, float, str e ausência);
- [x] Envelope root e mapeamento `released_by` validados como closed-schema estrito;
- [x] Repositório JSONL append-only grava duravelmente com `flush` e `os.fsync`;
- [x] Validação e preparação do registro em memória antes de criar diretórios ou abrir arquivo para append;
- [x] Tentativa de gravar `release_id` duplicado em arquivo íntegro levanta `DuplicateHumanReviewClaimReleaseError` sem escrita;
- [x] Arquivo com linhas vazias, JSON malformado, schemas inválidos ou duplicidade física de `release_id` acusa fail-closed imediato com `HumanReviewClaimReleaseCorruptionError` contendo `line_number` 1-based;
- [x] Qualquer leitura ou verificação de append valida integralmente o arquivo; registros válidos anteriores a linhas corrompidas não mascaram o erro;
- [x] Tentativa de append sobre arquivo previamente corrompido falha sem gravar novos dados;
- [x] `get_by_id` retorna `HumanReviewClaimRelease | None`;
- [x] `list_by_claim_id`, `list_by_workflow_id` e `list_all` retornam tuplas imutáveis preservando a ordem física de append;
- [x] Múltiplos releases para o mesmo `claim_id` são permitidos no repositório desde que possuam `release_id`s distintos;
- [x] Teste de integração comprova recuperação fiel de valores contratuais por nova instância fresca do repositório lendo arquivo persistido em disco;
- [x] Símbolos públicos exportados canonicamente no pacote `src/agent_lab/__init__.py`;
- [x] 100% GREEN no baseline de testes com runner canônico (`python -m unittest discover -s tests -v`), preservando os 595 testes existentes sem regressões.
