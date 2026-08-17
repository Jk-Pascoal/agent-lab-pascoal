# SPEC 0041 — Identidade verificável do especialista v1

> Especificação técnica da primeira camada explícita de proveniência de identidade
> humana no Agent Lab Pascoal.

## Metadados

| Campo | Valor |
| --- | --- |
| Identificador | `SPEC-0041` |
| Status | `Proposta` |
| Issue relacionada | `#41` |
| Responsável | `Jk-Pascoal` |
| Data de criação | `2026-08-17` |
| Última atualização | `2026-08-17` |

## 1. Contexto

O Agent Lab Pascoal já possui:

- recomendações estruturadas `APPROVE`, `REVIEW` e `REJECT`;
- Human-in-the-Loop com decisão humana final;
- `HumanReview` imutável;
- `AuditEvent` imutável;
- correlação entre revisão humana e evento de auditoria;
- serialização versionada de auditoria com `schema_version = 1`;
- persistência auditável local em JSONL append-only pela API;
- recuperação fail-closed diante de corrupção ou duplicidade.

O baseline de entrada deste incremento é:

```text
Ran 128 tests
OK
```

O runner oficial permanece:

```powershell
python -m unittest discover -s tests -v
```

A limitação atual está na identidade do especialista.

`HumanReview` recebe atualmente:

```python
reviewer_id: str
```

e `record_human_review` propaga esse valor para:

```python
AuditEvent.actor_id
```

Essa estrutura preserva um identificador declarado, mas não registra de onde essa
identidade veio, qual sujeito foi verificado por uma fronteira confiável, qual
asserção ou verificação sustentou a identidade nem quando essa verificação ocorreu.

A próxima âncora registrada no `PROJECT_COMPASS.md` é identidade verificável.

## 2. Problema, evidências e impacto

### Problema

Hoje o domínio consegue responder:

```text
qual reviewer_id foi informado?
```

mas não consegue responder:

```text
qual identidade verificada foi associada à revisão?
de qual provedor essa identidade veio?
qual sujeito do provedor foi correlacionado ao especialista?
qual verificação sustentou essa associação?
quando essa identidade foi verificada?
```

A identidade humana é, portanto, declarativa.

### Evidências

- `HumanReview.reviewer_id` é uma `str` não vazia;
- `AuditEvent.actor_id` também é uma `str` não vazia;
- `record_human_review` copia `review.reviewer_id` para `AuditEvent.actor_id`;
- o evento de auditoria já possui `metadata` imutável;
- `audit_event_to_record` serializa `metadata` sem exigir mudança do schema v1;
- `audit_event_from_record` restaura `metadata`;
- autenticação, autorização e RBAC continuam deliberadamente fora do escopo;
- o baseline confirmado antes deste incremento é de 128 testes.

### Impacto

Sem uma identidade verificável explícita:

- responsabilidade humana permanece apoiada apenas em um identificador declarado;
- auditorias futuras não conseguem demonstrar a proveniência da identidade;
- uma futura camada de workflow ou integração ERP não possui contrato estável para
  associar decisão humana a uma identidade previamente verificada;
- autenticação futura tenderia a vazar para o domínio de forma ad hoc;
- `reviewer_id` pode ser confundido com prova de identidade, embora atualmente não seja.

## 3. Objetivo

Introduzir a menor camada vertical capaz de representar uma identidade humana
previamente verificada por uma fronteira externa ou futura e propagá-la até o
evento de auditoria.

O incremento deve:

1. criar um contrato imutável de identidade verificável;
2. integrar esse contrato a `HumanReview`;
3. propagar o identificador estável do especialista para `AuditEvent.actor_id`;
4. registrar proveniência mínima da identidade em `AuditEvent.metadata`;
5. preservar, se tecnicamente adequado, `schema_version = 1`;
6. manter autenticação, autorização e gestão de credenciais fora do domínio.

## 4. Escopo

### Incluído

- contrato `VerifiedSpecialistIdentity`;
- identificador estável do especialista;
- provedor/origem da identidade;
- sujeito da identidade no provedor;
- identificador da verificação;
- timestamp timezone-aware da verificação;
- validação de strings obrigatórias não vazias;
- validação de `verified_at`;
- imutabilidade do contrato;
- integração com `HumanReview`;
- integração com `record_human_review`;
- coerência entre especialista verificado e `AuditEvent.actor_id`;
- proveniência mínima da identidade em `AuditEvent.metadata`;
- testes unitários;
- testes de integração;
- regressão completa do baseline;
- documentação explícita das limitações.

### Fora do escopo

- login;
- senha;
- sessão;
- autenticação real;
- OAuth;
- OIDC;
- SAML;
- JWT;
- autorização;
- RBAC;
- papéis;
- segregação de funções;
- diretório corporativo;
- banco de dados de identidades;
- criptografia;
- assinatura digital;
- certificação de identidade;
- workflow temporal;
- filas;
- integração ERP;
- interface gráfica;
- API web;
- migração de persistência sem necessidade comprovada.

## 5. Fronteira de confiança

`VerifiedSpecialistIdentity` não autentica ninguém.

O contrato representa o resultado já produzido por uma fronteira confiável externa
ou futura.

Fluxo conceitual:

```text
Fronteira futura de identidade
        ↓
verificação/autenticação externa
        ↓
VerifiedSpecialistIdentity
        ↓
HumanReview
        ↓
AuditEvent
        ↓
Persistência auditável
```

A responsabilidade desta Issue começa no recebimento de uma identidade já
verificada.

Ela não define como a verificação ocorre.

Princípio:

```text
identidade verificável ≠ autenticação implementada
identidade verificável ≠ autorização operacional
```

## 6. Invariantes

1. A recomendação automática nunca é uma decisão humana.
2. `requires_human_decision` permanece `True`.
3. Confiança da IA não concede autoridade operacional.
4. A recomendação original não pode ser sobrescrita.
5. Divergências humano–sistema permanecem auditáveis.
6. Revisões concluídas permanecem imutáveis.
7. Eventos de auditoria permanecem imutáveis.
8. Timestamps relevantes devem conter timezone.
9. Identidade verificável não concede autorização.
10. Esta Issue não introduz autenticação.
11. Persistência continua fail-closed.
12. Casos inválidos devem falhar antes da produção do evento correlacionado.
13. `reviewer_identity` é a única fonte de estado da identidade em `HumanReview`; `reviewer_id` existe exclusivamente como propriedade derivada de `reviewer_identity.specialist_id`.
14. Invariante temporal: `reviewer_identity.verified_at <= reviewed_at`. Uma identidade cuja verificação tenha timestamp posterior à decisão humana deve ser rejeitada.
15. Semântica opaca: `verification_id` é uma referência opaca da verificação/asserção emitida pela fronteira externa; a v1 não garante nem verifica unicidade global desse identificador.

## 7. Requisitos

### Requisitos funcionais

- `RF-01` — Deve existir um contrato imutável `VerifiedSpecialistIdentity`.
- `RF-02` — O contrato deve possuir `specialist_id`.
- `RF-03` — O contrato deve possuir `identity_provider`.
- `RF-04` — O contrato deve possuir `identity_subject`.
- `RF-05` — O contrato deve possuir `verification_id` como referência opaca da verificação ou asserção fornecida pela fronteira externa (sem garantia nem verificação de unicidade global na v1).
- `RF-06` — O contrato deve possuir `verified_at`.
- `RF-07` — Campos string obrigatórios devem rejeitar valores vazios ou compostos apenas por espaços.
- `RF-08` — `verified_at` deve exigir datetime timezone-aware.
- `RF-09` — `HumanReview` deve carregar `reviewer_identity: VerifiedSpecialistIdentity` como única fonte de estado de identidade do revisor.
- `RF-10` — `HumanReview` deve expor `reviewer_id` exclusivamente como propriedade derivada de `reviewer_identity.specialist_id`, sem ser argumento independente de construtor.
- `RF-11` — `HumanReview` deve validar a invariante temporal `reviewer_identity.verified_at <= reviewed_at`, rejeitando revisões onde a verificação for posterior à revisão humana.
- `RF-12` — `record_human_review` deve receber `reviewer_identity: VerifiedSpecialistIdentity` e propagar `reviewer_identity.specialist_id` para `AuditEvent.actor_id`.
- `RF-13` — `AuditEvent.actor_id` deve corresponder a `specialist_id`.
- `RF-14` — `AuditEvent.metadata` deve preservar os metadados existentes (`system_recommendation`, `human_decision`, `agrees_with_system`, `correction_count`) e adicionar as quatro chaves contratuais de proveniência de identidade:
  - `identity_provider`
  - `identity_subject`
  - `identity_verification_id`
  - `identity_verified_at`
- `RF-15` — `identity_verified_at` em `AuditEvent.metadata` deve ser gravado obrigatoriamente como string ISO 8601 através de `reviewer_identity.verified_at.isoformat()`.
- `RF-16` — Identidade inválida ou violação da invariante temporal deve impedir a criação de `HumanReviewResult`.
- `RF-17` — A decisão humana e as regras de correção existentes devem permanecer inalteradas.

### Requisitos de qualidade

- `RQ-01` — O contrato deve ser imutável.
- `RQ-02` — O domínio não deve importar SDK de provedor de identidade.
- `RQ-03` — A implementação deve usar apenas biblioteca padrão do Python.
- `RQ-04` — Nenhuma credencial, token ou segredo deve ser armazenado.
- `RQ-05` — Nenhum campo deve sugerir autorização ou papel operacional.
- `RQ-06` — A mudança deve ser pequena e removível sem corromper o restante do domínio.
- `RQ-07` — O schema persistido v1 deve ser preservado utilizando `metadata` com `identity_verified_at` serializado em ISO 8601.
- `RQ-08` — Nenhuma alteração em `schema_version` ou em `audit_serialization.py` deve ser introduzida.
- `RQ-09` — Os 128 testes anteriores devem continuar aprovados após as adaptações contratuais.
- `RQ-10` — O runner oficial permanece `unittest`.

## 8. Proposta técnica

### Contrato de identidade

Contrato inicial proposto:

```python
@dataclass(frozen=True)
class VerifiedSpecialistIdentity:
    specialist_id: str
    identity_provider: str
    identity_subject: str
    verification_id: str
    verified_at: datetime
```

Semântica dos campos:

- `specialist_id` — identificador estável utilizado pelo domínio;
- `identity_provider` — origem que produziu ou sustentou a verificação;
- `identity_subject` — sujeito da identidade dentro do provedor;
- `verification_id` — referência opaca da verificação ou asserção fornecida pela fronteira externa (sem garantia nem verificação de unicidade global na v1);
- `verified_at` — instante da verificação, obrigatório com timezone.

### Integração com `HumanReview`

Estado atual:

```python
reviewer_id: str
```

Estado alvo:

```python
reviewer_identity: VerifiedSpecialistIdentity
```

`reviewer_identity` torna-se a única fonte de verdade da identidade do revisor em `HumanReview`.

Para conveniência e compatibilidade de leitura, `reviewer_id` existirá exclusivamente como propriedade derivada:

```python
@property
def reviewer_id(self) -> str:
    return self.reviewer_identity.specialist_id
```

Não será permitido passar `reviewer_id` como argumento independente no construtor de `HumanReview`.

Em `HumanReview.__post_init__`, a invariante temporal será validada:

```python
if not isinstance(self.reviewer_identity, VerifiedSpecialistIdentity):
    raise ValueError("reviewer_identity must be a VerifiedSpecialistIdentity")

if self.reviewer_identity.verified_at > self.reviewed_at:
    raise ValueError(
        "reviewer_identity.verified_at cannot be later than reviewed_at"
    )
```

### Integração com auditoria

`AuditEvent.actor_id` permanece string, alimentado pelo identificador estável do especialista:

```python
actor_id = review.reviewer_identity.specialist_id
```

`HumanReviewResult.__post_init__` valida a correlação:

```python
if self.audit_event.actor_id != self.review.reviewer_identity.specialist_id:
    raise ValueError("audit event must reference the same reviewer")
```

A proveniência da identidade é fixada contratualmente em `AuditEvent.metadata`, preservando os metadados existentes e adicionando as quatro chaves de identidade:

```python
metadata={
    "system_recommendation": review.system_recommendation.value,
    "human_decision": review.human_decision.value,
    "agrees_with_system": review.agrees_with_system,
    "correction_count": len(review.corrections),
    "identity_provider": review.reviewer_identity.identity_provider,
    "identity_subject": review.reviewer_identity.identity_subject,
    "identity_verification_id": review.reviewer_identity.verification_id,
    "identity_verified_at": review.reviewer_identity.verified_at.isoformat(),
}
```

O campo `identity_verified_at` é gravado obrigatoriamente como string ISO 8601 através de `reviewer_identity.verified_at.isoformat()`, garantindo serialização JSON nativa sem alterações na camada de persistência.

### Compatibilidade com persistência

O schema atual já serializa:

```python
"metadata": dict(event.metadata)
```

e a desserialização aceita um `Mapping`.

Como todas as quatro chaves contratuais de identidade são tipos primitivos serializáveis (`str`), conclui-se que:

```text
schema_version = 1 permanece suficiente e inalterado
```

Não há modificações estruturais em `audit_serialization.py` nem em `audit_repository.py`.

## 9. Arquivos previstos

Alterações prováveis:

```text
src/agent_lab/human_review.py
src/agent_lab/audit.py
tests/test_human_review.py
tests/test_human_review_integration.py
tests/test_audit_persistence_integration.py
docs/specs/0041_verifiable_specialist_identity_v1.md
docs/PROJECT_COMPASS.md
```

Arquivos que **NÃO** devem ser alterados:

```text
src/agent_lab/audit_serialization.py
src/agent_lab/audit_repository.py
tests/test_audit_serialization.py
tests/test_audit_repository.py
```

O contrato `VerifiedSpecialistIdentity` residirá coeso com o Human-in-the-Loop em `src/agent_lab/human_review.py`.

## 10. Estratégia TDD

### Etapa A — contrato de identidade

#### RED

Criar testes em `tests/test_human_review.py` para:

- criação de `VerifiedSpecialistIdentity` válida com os 5 campos;
- rejeição de `specialist_id` vazio ou composto apenas por espaços;
- rejeição de `identity_provider` vazio ou composto apenas por espaços;
- rejeição de `identity_subject` vazio ou composto apenas por espaços;
- rejeição de `verification_id` vazio ou composto apenas por espaços;
- rejeição de `verified_at` sem timezone (naive datetime);
- imutabilidade (`FrozenInstanceError` ao tentar alterar atributos).

#### GREEN

Implementar `VerifiedSpecialistIdentity` e suas validações em `src/agent_lab/human_review.py`.

### Etapa B — integração com `HumanReview`

#### RED

Criar testes em `tests/test_human_review.py` para:

- `HumanReview` aceita `reviewer_identity: VerifiedSpecialistIdentity` como único campo de identidade;
- `review.reviewer_id` expõe `review.reviewer_identity.specialist_id` como propriedade derivada;
- tentativa de instanciar com tipo inválido em `reviewer_identity` lança `ValueError`;
- rejeição de revisão quando `reviewer_identity.verified_at > reviewed_at` (invariante temporal);
- preservação das regras de decisão existentes (`APPROVE`, `REJECT`, `REQUEST_CORRECTION`) com a nova identidade.

#### GREEN

Atualizar `HumanReview` para usar `reviewer_identity` como única fonte de estado e implementar `@property reviewer_id` e a validação temporal.

### Etapa C — integração com auditoria

#### RED

Criar testes em `tests/test_human_review_integration.py` para:

- `record_human_review` recebe `reviewer_identity: VerifiedSpecialistIdentity`;
- `result.audit_event.actor_id == identity.specialist_id`;
- `result.audit_event.metadata` preserva os metadados existentes (`system_recommendation`, `human_decision`, `agrees_with_system`, `correction_count`);
- `result.audit_event.metadata` adiciona as quatro chaves contratuais de identidade:
  - `identity_provider`
  - `identity_subject`
  - `identity_verification_id`
  - `identity_verified_at`
- `result.audit_event.metadata["identity_verified_at"] == identity.verified_at.isoformat()`;
- `HumanReviewResult` valida a coerência entre `audit_event.actor_id` e `review.reviewer_identity.specialist_id`.

#### GREEN

Atualizar `record_human_review` e `HumanReviewResult` em `src/agent_lab/audit.py`.

### Etapa D — persistência

Sem alterar `src/agent_lab/audit_serialization.py` nem `src/agent_lab/audit_repository.py`:

- adaptar `tests/test_audit_persistence_integration.py` para usar `VerifiedSpecialistIdentity`;
- persistir o `AuditEvent` produzido por `record_human_review`;
- reabrir uma nova instância de `JsonlAuditRepository`;
- recuperar o evento persistido por `get_by_id`;
- provar que `retrieved_event.actor_id` continua correspondendo a `specialist_id`;
- provar que os quatro metadados de identidade (`identity_provider`, `identity_subject`, `identity_verification_id`, `identity_verified_at`) sobrevivem ao round-trip;
- provar que `identity_verified_at` permanece a string ISO 8601 original;
- executar também a suíte existente de `tests/test_audit_serialization.py` e `tests/test_audit_repository.py` como regressão completa;
- manter `schema_version = 1`.

## 11. Critérios de aceite

- [ ] existe `VerifiedSpecialistIdentity` imutável;
- [ ] `specialist_id` rejeita branco;
- [ ] `identity_provider` rejeita branco;
- [ ] `identity_subject` rejeita branco;
- [ ] `verification_id` rejeita branco e é aceito como referência opaca da verificação sem validação de unicidade global;
- [ ] `verified_at` rejeita datetime sem timezone;
- [ ] `HumanReview` carrega `reviewer_identity: VerifiedSpecialistIdentity` como única fonte de estado de identidade;
- [ ] `HumanReview.reviewer_id` existe exclusivamente como propriedade derivada de `reviewer_identity.specialist_id`, sem ser argumento independente de construtor;
- [ ] `HumanReview` rejeita identidades verificadas após a decisão humana (`verified_at > reviewed_at`);
- [ ] `record_human_review` recebe `reviewer_identity: VerifiedSpecialistIdentity`;
- [ ] `AuditEvent.actor_id` corresponde a `specialist_id`;
- [ ] metadados existentes de auditoria permanecem preservados;
- [ ] proveniência mínima fica registrada em metadata com as chaves contratuais `identity_provider`, `identity_subject`, `identity_verification_id` e `identity_verified_at`;
- [ ] `identity_verified_at` é gravado obrigatoriamente como `reviewer_identity.verified_at.isoformat()`;
- [ ] identidade inválida ou temporariamente inconsistente impede a criação de `HumanReviewResult`;
- [ ] contratos de decisão humana permanecem válidos;
- [ ] schema de persistência v1 permanece compatível sem alteração de serialização ou repositório;
- [ ] `test_audit_persistence_integration.py` valida round-trip completo dos metadados de identidade;
- [ ] testes anteriores adaptados e novos testes permanecem verdes no baseline (128+ testes);
- [ ] CI permanece verde em Python 3.11 com `unittest`;
- [ ] autenticação, autorização, RBAC e workflow continuam fora do escopo;
- [ ] `PROJECT_COMPASS.md` é atualizado no fechamento.

## 12. Estratégia de regressão

Após cada GREEN relevante:

```powershell
python -m unittest discover -s tests -v
```

Baseline de entrada:

```text
Ran 128 tests
OK
```

Nenhuma regressão deve ser aceita como efeito colateral da mudança de identidade.

## 13. Riscos e limitações

### Falsa sensação de segurança

O nome `VerifiedSpecialistIdentity` pode sugerir que o Agent Lab verificou a
identidade.

Não verificou.

A v1 apenas preserva um contrato representando uma identidade cuja verificação
ocorreu em fronteira externa ou futura.

### Semântica e opacidade de `verification_id`

`verification_id` é uma referência opaca emitida pela fronteira externa (ex.: ID de asserção, protocolo, ticket de sessão ou hash).

A v1 não valida nem garante unicidade global deste identificador, nem rastreia revogações externas.

### Consistência temporal

A regra `verified_at <= reviewed_at` garante que a decisão humana não seja atribuída a uma identidade "do futuro". Não há validação de expiração ou janela máxima de validade da verificação nesta versão.

### Acoplamento prematuro

Não adicionar campos específicos de Active Directory, Google, Microsoft, Okta ou
outro provedor.

O contrato deve permanecer agnóstico.

### Duplicação de identidade eliminada

A fonte única de verdade é `reviewer_identity`.

`reviewer_id` não é um campo independente nem argumento de inicialização, eliminando qualquer risco de inconsistência de estado.

### Schema de persistência

A metadata atual permite preservar a proveniência sem alterar o envelope v1.

Não introduzir schema v2 por conveniência.

### Autorização

Uma pessoa pode possuir identidade verificável e ainda não possuir autoridade para
aprovar determinado material.

Esse problema pertence à futura camada de autorização/RBAC.

## 14. Resultado esperado

Antes:

```text
HumanReview
  reviewer_id = "specialist-001"
```

Depois:

```text
HumanReview
  reviewer_identity
    specialist_id      = "specialist-001"
    identity_provider  = "corporate-idp"
    identity_subject   = "user@corp.local"
    verification_id    = "assert-98765"
    verified_at        = 2026-08-17T12:00:00+00:00

  reviewer_id (propriedade derivada) -> "specialist-001"
```

Auditoria:

```text
AuditEvent
  actor_id = "specialist-001"

  metadata
    system_recommendation     = "REVIEW"
    human_decision            = "REQUEST_CORRECTION"
    agrees_with_system        = True
    correction_count          = 1
    identity_provider         = "corporate-idp"
    identity_subject          = "user@corp.local"
    identity_verification_id  = "assert-98765"
    identity_verified_at      = "2026-08-17T12:00:00+00:00"
```

O ganho desta versão não é autenticar o especialista.

O ganho é tornar explícita e auditável a proveniência da identidade humana
associada à decisão.

## 15. Sequência de implementação

```text
SPEC 0041
  ↓
teste RED — VerifiedSpecialistIdentity
  ↓
GREEN — contrato
  ↓
teste RED — HumanReview
  ↓
GREEN — integração
  ↓
teste RED — AuditEvent provenance
  ↓
GREEN — propagação
  ↓
regressão completa
  ↓
SPEC final
  ↓
PR + CI
  ↓
merge
  ↓
PROJECT_COMPASS
  ↓
Relatório Diário
```
