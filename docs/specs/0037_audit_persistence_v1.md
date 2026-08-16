# SPEC 0037 — Persistência auditável v1 com repositório JSONL

> Especificação técnica do primeiro mecanismo durável de persistência da
> trilha de auditoria do Agent Lab Pascoal.

## Metadados

| Campo | Valor |
| --- | --- |
| Identificador | `SPEC-0037` |
| Status | `Aprovada` |
| Issue relacionada | `#37` |
| Responsável | `Jk-Pascoal` |
| Data de criação | `2026-08-16` |
| Última atualização | `2026-08-16` |

## 1. Contexto

O Agent Lab Pascoal já produz recomendações estruturadas de governança,
preserva as evidências utilizadas e registra a decisão final do especialista
por meio do Human-in-the-Loop v1.

A entrega da Issue #33 introduziu:

- `HumanDecision`;
- `CorrectionRequest`;
- `HumanReview`;
- `AuditEventType`;
- `AuditEvent`;
- `HumanReviewResult`;
- `record_human_review`.

Esses contratos separam a recomendação automática da decisão humana, preservam
concordâncias e divergências e produzem eventos de auditoria imutáveis.

Entretanto, a trilha existe somente em memória. Ao encerrar o processo Python,
os eventos deixam de estar disponíveis. O sistema ainda não possui uma
fronteira explícita de persistência, um formato durável versionado ou operações
de recuperação do histórico.

O `PROJECT_COMPASS.md` registra persistência auditável como a próxima âncora
arquitetural e estabelece que o histórico não deve ser reconstruído somente a
partir do estado final.

## 2. Problema, evidências e impacto

### Problema

O percurso decisório produzido pelo Human-in-the-Loop não sobrevive a uma nova
execução da aplicação.

Não existe atualmente um mecanismo capaz de:

- persistir um `AuditEvent` de forma durável;
- recuperar eventos após reinicialização do repositório;
- consultar um evento por seu identificador;
- listar o histórico de um material;
- detectar gravações duplicadas;
- detectar corrupção do histórico;
- evoluir o formato persistido de maneira explicitamente versionada.

Sem essa capacidade, a auditoria é estruturalmente válida, mas operacionalmente
volátil.

### Evidências

- A Issue #33 e o PR #34 implementaram Human-in-the-Loop v1 e auditoria em memória.
- O baseline confirmado antes deste incremento é de 100 testes aprovados.
- O runner oficial é `unittest` em Python 3.11.
- `HumanReview` e `AuditEvent` são imutáveis.
- Os timestamps do domínio exigem timezone.
- `src/agent_lab/audit.py` não executa I/O nem oferece persistência durável.
- Não existe contrato de repositório de auditoria no código atual.
- Não existe serialização versionada de `AuditEvent` para armazenamento.
- O Project Compass registra persistência auditável como próxima âncora.
- A Issue #37 formaliza a necessidade e os limites deste incremento.

### Impacto

Caso o problema não seja tratado:

- decisões humanas e divergências com o sistema serão perdidas ao encerrar o processo;
- não será possível reconstruir o percurso decisório entre execuções;
- auditorias posteriores dependerão de memória transitória;
- futuras camadas de workflow não terão uma fronteira estável de histórico;
- erros de integridade poderão passar despercebidos;
- persistência futura poderá contaminar o domínio se não houver desacoplamento.

O incremento cria memória operacional local e durável sem antecipar banco de
dados industrial, autenticação, workflow ou integração com ERP.

## 3. Objetivo

Implementar uma fronteira de persistência auditável capaz de gravar e recuperar
eventos de auditoria em arquivo JSONL, preservando os contratos e invariantes do
domínio.

Ao final do incremento, deve ser possível:

1. persistir eventos de forma append-only pela API da aplicação;
2. recuperar o mesmo evento em uma nova instância do repositório;
3. consultar eventos por `event_id` e `material_id`;
4. preservar tipos, timezone, metadados e ordem de gravação;
5. rejeitar duplicidade, corrupção e versões incompatíveis de forma explícita;
6. substituir futuramente o backend sem alterar o domínio.

## 4. Escopo

### Incluído

- protocolo mínimo `AuditRepository`;
- implementação `JsonlAuditRepository`;
- serialização e desserialização determinísticas de `AuditEvent`;
- versão de schema persistido igual a `1`;
- uma linha JSON completa por evento;
- escrita síncrona com `write`, `flush` e `fsync`;
- consulta por `event_id`;
- listagem por `material_id`;
- listagem completa;
- preservação da ordem física de gravação;
- detecção de identificador duplicado;
- detecção de linha corrompida ou estruturalmente inválida;
- falha explícita, sem retorno silencioso de histórico parcial;
- exceções específicas de persistência;
- testes com `unittest` e diretórios temporários;
- teste de integração do fluxo revisão → auditoria → persistência → recuperação;
- atualização da documentação estrutural aplicável.

### Fora do escopo

- SQLite ou banco de dados cliente/servidor;
- armazenamento remoto ou em nuvem;
- autenticação, autorização e identidade verificável;
- papéis e segregação de funções;
- interface gráfica, API web ou CLI interativa;
- filas, SLA, notificações ou escalonamento;
- integração ou injeção em ERP;
- concorrência multiprocesso ou múltiplos escritores;
- locking distribuído;
- event sourcing completo, CQRS ou projeções;
- criptografia em repouso;
- assinatura digital ou hash encadeado;
- prova criptográfica de não adulteração;
- update ou delete de eventos;
- recuperação automática de arquivo corrompido;
- migração entre versões de schema;
- uso de dados reais ou proprietários;
- mudança do runner `unittest`.

## 5. Responsabilidade humana e limites do agente

A persistência não altera a fronteira de autoridade do projeto.

O sistema continua autorizado apenas a:

- produzir evidências;
- gerar recomendações `APPROVE`, `REVIEW` ou `REJECT`;
- registrar a decisão informada pelo especialista;
- preservar o percurso de maneira auditável.

A persistência de uma recomendação não a transforma em autorização
operacional. Mesmo com `decision = APPROVE` e `confidence = 1.0`, o contrato
deve preservar `requires_human_decision = True` no escopo vigente.

A decisão final sobre aprovação, reprovação, correção ou alteração de dados
PDM/BOM permanece humana.

## 6. Requisitos

### Requisitos funcionais

- `RF-01` — O sistema deve persistir um `AuditEvent` como uma única linha JSON.
- `RF-02` — Cada registro deve conter `schema_version` com valor inteiro `1`.
- `RF-03` — O repositório deve recuperar um evento por `event_id`.
- `RF-04` — A ausência do `event_id` consultado deve retornar `None`.
- `RF-05` — O repositório deve listar eventos por `material_id`.
- `RF-06` — O repositório deve listar todos os eventos persistidos.
- `RF-07` — As listagens devem preservar a ordem física de gravação.
- `RF-08` — Arquivo inexistente ou vazio deve produzir coleção vazia.
- `RF-09` — Uma nova instância apontando para o mesmo arquivo deve recuperar os eventos anteriores.
- `RF-10` — Tentativa de gravar `event_id` existente deve lançar exceção explícita.
- `RF-11` — Linha malformada ou estruturalmente inválida deve lançar erro de corrupção com número da linha.
- `RF-12` — Versão de schema desconhecida deve falhar explicitamente.
- `RF-13` — O round-trip deve preservar todos os campos observáveis de `AuditEvent`.
- `RF-14` — Timestamp sem timezone deve ser rejeitado na desserialização.

### Requisitos de qualidade

- `RQ-01` — `audit.py` e `human_review.py` não devem importar infraestrutura de persistência.
- `RQ-02` — A API pública do repositório não deve oferecer update ou delete.
- `RQ-03` — As coleções retornadas devem ser imutáveis.
- `RQ-04` — A escrita deve executar `flush` e `os.fsync` antes de retornar sucesso.
- `RQ-05` — A leitura deve operar em modo fail-closed diante de corrupção.
- `RQ-06` — O sistema não deve retornar histórico parcial como se estivesse íntegro.
- `RQ-07` — A implementação deve usar somente a biblioteca padrão do Python.
- `RQ-08` — Testes de arquivo devem utilizar `tempfile` e não deixar resíduos.
- `RQ-09` — Os 100 testes anteriores devem permanecer aprovados.
- `RQ-10` — A solução deve permanecer síncrona e monoprocesso nesta versão.
- `RQ-11` — A garantia append-only deve ser descrita como garantia da API da aplicação, não como proteção física ou criptográfica.

## 7. Proposta técnica

### Visão geral

A solução separa domínio, serialização e infraestrutura:

```text
HumanReview
    ↓
record_human_review
    ↓
AuditEvent imutável
    ↓
serialização versionada
    ↓
AuditRepository (Protocol)
    ↓
JsonlAuditRepository
    ↓
arquivo JSONL local
```

JSONL foi escolhido para a v1 porque:

- representa naturalmente um log append-only;
- é inspecionável em texto plano;
- exige pouca infraestrutura;
- permite validar o contrato antes de introduzir banco de dados;
- pode ser substituído futuramente por outra implementação do protocolo.

SQLite foi considerado, mas adiado porque adicionaria DDL, conexões, transações,
índices e decisões de migração antes de haver evidência de necessidade.

Arquivos JSON individuais também foram considerados, mas possuem pior
representação do fluxo cronológico e maior custo operacional para listagens.

### Fluxo esperado

```text
AuditEvent
  → validação de duplicidade
  → serialização com schema_version = 1
  → escrita de uma linha
  → flush
  → fsync
  → sucesso

arquivo JSONL
  → leitura sequencial
  → identificação da linha
  → parsing JSON
  → validação de schema_version
  → reconstrução de AuditEvent
  → coleção imutável ou erro explícito
```

### Semântica temporal

`occurred_at` representa o instante declarado do evento.

A posição da linha representa a ordem de gravação no repositório.

A v1 preserva a ordem de gravação e não reordena silenciosamente os eventos
por `occurred_at`.

### Semântica append-only

Append-only é garantido pela API da aplicação:

- existe `append`;
- não existe `update`;
- não existe `delete`;
- identificadores duplicados são rejeitados.

O arquivo pode ser alterado externamente pelo sistema operacional ou por
intervenção manual. Detecção criptográfica de adulteração não pertence à v1.

### Comportamento diante de corrupção

A leitura deve falhar por inteiro quando encontrar:

- JSON malformado;
- campos obrigatórios ausentes;
- tipos inválidos;
- timestamp sem timezone;
- versão de schema não suportada;
- evento incompatível com o contrato do domínio.

O erro deve informar pelo menos o número da linha e preservar a causa original.
Não é permitido ignorar a linha e retornar silenciosamente os demais eventos.

### Contratos de dados

#### `AuditRepository`

```python
class AuditRepository(Protocol):
    def append(self, event: AuditEvent) -> None: ...
    def get_by_id(self, event_id: str) -> AuditEvent | None: ...
    def list_by_material(self, material_id: str) -> tuple[AuditEvent, ...]: ...
    def list_all(self) -> tuple[AuditEvent, ...]: ...
```

#### Envelope persistido

```json
{
  "schema_version": 1,
  "event_id": "evento-identificador",
  "event_type": "valor-do-enum",
  "material_id": "MAT-001",
  "actor_id": "especialista-001",
  "occurred_at": "2026-08-16T08:00:00+00:00",
  "metadata": {}
}
```

Os nomes finais dos campos devem refletir exatamente o contrato vigente de
`AuditEvent`. A implementação não deve inventar, renomear ou omitir campos do
domínio para se ajustar ao exemplo.

#### Exceções

- `AuditPersistenceError` — erro-base da fronteira de persistência;
- `DuplicateAuditEventError` — tentativa de persistir `event_id` existente;
- `AuditCorruptionError` — registro persistido inválido, com referência à linha.

Exceções adicionais só devem ser criadas quando reduzirem ambiguidade observável
e permanecerem dentro do escopo da Issue.

### Arquivos previstos

- `src/agent_lab/audit_repository.py` — protocolo, implementação JSONL e exceções de persistência;
- `src/agent_lab/audit_serialization.py` — serialização versionada e reconstrução de `AuditEvent`;
- `tests/test_audit_serialization.py` — round-trip, timezone, versão e entradas inválidas;
- `tests/test_audit_repository.py` — append, consultas, durabilidade, duplicidade e corrupção;
- `tests/test_audit_persistence_integration.py` — fluxo ponta a ponta;
- `docs/specs/0037_audit_persistence_v1.md` — esta especificação;
- `docs/PROJECT_COMPASS.md` — atualização do estado estrutural após implementação;
- `README.md` — atualização do estado e baseline quando aplicável;
- `CHANGELOG.md` — registro do incremento quando aplicável.

Os nomes dos módulos podem ser ajustados antes do primeiro commit de código se
a inspeção do repositório demonstrar conflito com convenções existentes. Qualquer
ajuste deve ser documentado nesta SPEC.

## 8. Estratégia de testes e TDD

### Vermelho

Criar primeiro os testes que importam e exercitam contratos ainda inexistentes.
Os testes devem falhar pela ausência da capacidade, e não por erro de sintaxe ou
configuração.

Ordem recomendada:

1. testes de serialização e round-trip;
2. testes do protocolo e repositório;
3. testes de duplicidade e corrupção;
4. teste de integração ponta a ponta.

O commit RED deve conter somente testes e ajustes documentais indispensáveis.

### Verde

Implementar a menor mudança suficiente para satisfazer os testes:

1. serialização versionada;
2. exceções explícitas;
3. protocolo do repositório;
4. implementação JSONL;
5. integração entre evento e repositório.

Não adicionar cache, índice, banco de dados, locking multiprocesso ou recuperação
automática.

### Regressão

Executar a suíte completa após cada etapa relevante e obrigatoriamente antes do
Pull Request:

```powershell
python -m unittest discover -s tests -v
```

O baseline inicial é:

```text
Ran 100 tests
OK
```

### Testes previstos

#### Serialização

- round-trip de evento válido;
- preservação de enum, campos e metadados;
- preservação de datetime aware;
- rejeição de timestamp naive;
- rejeição de campo obrigatório ausente;
- rejeição de tipo inválido;
- rejeição de versão desconhecida;
- comprovação de que `schema_version = 1` é persistido.

#### Repositório

- criação implícita do arquivo na primeira gravação;
- arquivo inexistente retorna tupla vazia;
- arquivo vazio retorna tupla vazia;
- append de um evento;
- append sequencial de múltiplos eventos;
- conteúdo anterior não é sobrescrito;
- recuperação após nova instância do repositório;
- `get_by_id` existente;
- `get_by_id` inexistente retorna `None`;
- `list_by_material` filtra corretamente;
- listagens preservam ordem física;
- duplicidade de `event_id` é rejeitada;
- JSON malformado produz `AuditCorruptionError`;
- registro estruturalmente inválido produz `AuditCorruptionError`;
- erro de corrupção identifica a linha;
- nenhum histórico parcial é retornado após corrupção.

#### Integração

- produzir `HumanReview` válida;
- gerar `AuditEvent` com `record_human_review`;
- persistir o evento;
- criar nova instância do repositório;
- recuperar o evento;
- comprovar preservação de recomendação, decisão humana, identidade, timestamp,
  justificativa, correções e divergência quando esses dados fizerem parte do
  contrato vigente do evento.

Todos os testes de filesystem devem usar `tempfile.TemporaryDirectory` ou
equivalente da biblioteca padrão e realizar limpeza automática.

## 9. Gates de qualidade

Antes do Pull Request, executar e registrar:

```powershell
python -m unittest discover -s tests -v
git diff --check
git status -sb
```

Critérios mínimos:

- todos os testes aprovados;
- os 100 testes anteriores preservados;
- nenhum erro de espaços em branco;
- alterações limitadas aos arquivos previstos;
- nenhuma dependência externa adicionada;
- nenhum dado real, credencial ou chave de API versionado;
- documentação alinhada ao comportamento implementado;
- limitações e riscos registrados no Pull Request;
- Issue #37 e SPEC 0037 referenciadas no PR.

## 10. Riscos e limitações

| Risco ou limitação | Probabilidade | Impacto | Mitigação |
| --- | --- | --- | --- |
| Interrupção durante a escrita produzir última linha incompleta | Baixa | Alto | `flush`, `fsync` e detecção fail-closed na leitura |
| Alteração externa do arquivo violar append-only | Média | Alto | Documentar limite e detectar corrupção estrutural; proteção criptográfica fica adiada |
| `event_id` duplicado | Baixa | Médio | Verificar histórico antes do append e lançar exceção explícita |
| Perda de timezone no round-trip | Baixa | Alto | Parser rigoroso e testes de datetime aware |
| Versão de schema desconhecida | Baixa | Alto | Campo obrigatório e falha explícita |
| Consulta linear ficar lenta em volumes altos | Média no futuro | Médio | Aceitar no laboratório e substituir backend quando houver evidência |
| Concorrência corromper o arquivo | Baixa no escopo atual | Alto | Declarar operação monoprocesso e adiar múltiplos escritores |
| Abstração crescer além da necessidade | Média | Médio | Manter quatro operações públicas e evitar recursos não exigidos |
| Confundir ordem do evento com ordem de gravação | Média | Médio | Preservar ordem física e documentar semânticas temporais distintas |

Limitações conhecidas após o incremento:

- armazenamento somente local;
- consultas lineares `O(n)`;
- verificação de duplicidade linear;
- ausência de transações multi-evento;
- ausência de concorrência multiprocesso;
- ausência de identidade verificável;
- ausência de recuperação automática;
- ausência de proteção criptográfica contra adulteração;
- ausência de integração com workflow ou ERP;
- validação restrita a dados sintéticos e cenários controlados.

## 11. Plano de reversão

A mudança é aditiva e deve permanecer isolada da lógica central.

Em caso de regressão:

1. interromper o uso de `JsonlAuditRepository`;
2. reverter os módulos de serialização e repositório;
3. reverter os testes específicos e atualizações documentais relacionadas;
4. preservar `audit.py`, `human_review.py` e os contratos da Issue #33;
5. executar novamente os 100 testes do baseline anterior.

Arquivos JSONL gerados durante testes não devem ser versionados. Dados de teste
devem existir apenas em diretórios temporários.

Como não haverá migração de dados reais, banco remoto ou alteração destrutiva,
a reversão não exige restauração de infraestrutura externa.

## 12. Versionamento e release

### Impacto SemVer

`MINOR` — nova capacidade compatível de persistência, adicionada sem remover ou
alterar intencionalmente contratos públicos existentes.

### Publicação prevista

- versão planejada: `Unreleased`;
- criação de tag: não neste incremento;
- criação de GitHub Release: não neste incremento;
- atualização do `CHANGELOG.md`: sim, antes do merge se confirmado pelo padrão vigente.

## 13. Critérios de aceite

- [ ] existe contrato explícito `AuditRepository`;
- [ ] existe implementação `JsonlAuditRepository`;
- [ ] cada evento ocupa uma nova linha JSON;
- [ ] cada registro contém `schema_version = 1`;
- [ ] eventos sobrevivem à criação de uma nova instância do repositório;
- [ ] o round-trip preserva integralmente o contrato vigente de `AuditEvent`;
- [ ] enums, metadados e timezone são preservados;
- [ ] timestamp sem timezone é rejeitado;
- [ ] consulta por `event_id` funciona;
- [ ] identificador inexistente retorna `None`;
- [ ] listagem por `material_id` funciona;
- [ ] listagem completa funciona;
- [ ] listagens retornam tuplas e preservam ordem de gravação;
- [ ] duplicidade de `event_id` falha explicitamente;
- [ ] arquivo inexistente ou vazio retorna tupla vazia;
- [ ] corrupção produz erro explícito com número da linha;
- [ ] histórico parcial não é retornado silenciosamente;
- [ ] escrita utiliza `flush` e `fsync`;
- [ ] domínio não importa infraestrutura de persistência;
- [ ] API não oferece update ou delete;
- [ ] testes de arquivo não deixam resíduos;
- [ ] existe teste de integração ponta a ponta;
- [ ] os 100 testes anteriores permanecem aprovados;
- [ ] todos os novos testes usam `unittest`;
- [ ] a CI permanece verde em Python 3.11;
- [ ] nenhuma dependência externa foi adicionada;
- [ ] Project Compass, README e CHANGELOG são atualizados quando aplicável;
- [ ] riscos e limitações são registrados;
- [ ] a responsabilidade humana permanece preservada;
- [ ] o Pull Request referencia a Issue #37 e esta SPEC.

## 14. Questões em aberto

Nenhuma.

Decisões deliberadamente adiadas — como backend SQLite, concorrência,
autenticação, workflow e proteção criptográfica — não são questões em aberto
desta SPEC. Elas exigirão Issues próprias quando houver evidência de necessidade.

## 15. Histórico de decisões

| Data | Decisão | Motivo | Responsável |
| --- | --- | --- | --- |
| `2026-08-16` | Adotar JSONL como backend de referência da v1 | Menor solução durável, inspecionável e compatível com log append-only | `Jk-Pascoal`, Pasquara e Agy |
| `2026-08-16` | Desacoplar persistência por `AuditRepository` | Permitir substituição futura do backend sem contaminar o domínio | `Jk-Pascoal`, Pasquara e Agy |
| `2026-08-16` | Usar `schema_version = 1` | Tornar explícita a evolução futura do formato persistido | `Jk-Pascoal` e Pasquara |
| `2026-08-16` | Falhar por inteiro diante de corrupção | Evitar apresentar histórico parcial como íntegro | `Jk-Pascoal` e Pasquara |
| `2026-08-16` | Preservar ordem física de gravação | Distinguir ordem de registro de instante declarado do evento | `Jk-Pascoal` e Pasquara |
| `2026-08-16` | Limitar a v1 a operação síncrona e monoprocesso | Evitar concorrência e locking prematuros | `Jk-Pascoal`, Pasquara e Agy |
