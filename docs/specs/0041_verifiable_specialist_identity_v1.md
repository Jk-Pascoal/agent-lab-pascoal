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

## 7. Requisitos

### Requisitos funcionais

- `RF-01` — Deve existir um contrato imutável `VerifiedSpecialistIdentity`.
- `RF-02` — O contrato deve possuir `specialist_id`.
- `RF-03` — O contrato deve possuir `identity_provider`.
- `RF-04` — O contrato deve possuir `identity_subject`.
- `RF-05` — O contrato deve possuir `verification_id`.
- `RF-06` — O contrato deve possuir `verified_at`.
- `RF-07` — Campos string obrigatórios devem rejeitar valores vazios ou compostos apenas por espaços.
- `RF-08` — `verified_at` deve exigir datetime timezone-aware.
- `RF-09` — `HumanReview` deve carregar uma identidade verificável explícita.
- `RF-10` — O identificador estável do especialista deve permanecer disponível para correlação.
- `RF-11` — `record_human_review` deve receber e propagar a identidade verificável.
- `RF-12` — `AuditEvent.actor_id` deve corresponder a `specialist_id`.
- `RF-13` — A proveniência mínima deve ser registrada em `AuditEvent.metadata`.
- `RF-14` — Identidade inválida deve impedir a criação de `HumanReviewResult`.
- `RF-15` — A decisão humana e as regras de correção existentes devem permanecer inalteradas.

### Requisitos de qualidade

- `RQ-01` — O contrato deve ser imutável.
- `RQ-02` — O domínio não deve importar SDK de provedor de identidade.
- `RQ-03` — A implementação deve usar apenas biblioteca padrão do Python.
- `RQ-04` — Nenhuma credencial, token ou segredo deve ser armazenado.
- `RQ-05` — Nenhum campo deve sugerir autorização ou papel operacional.
- `RQ-06` — A mudança deve ser pequena e removível sem corromper o restante do domínio.
- `RQ-07` — O schema persistido v1 deve ser preservado se a proveniência puder ser carregada por `metadata`.
- `RQ-08` — Qualquer necessidade real de alterar `schema_version` deve ser explicitamente justificada antes da implementação.
- `RQ-09` — Os 128 testes anteriores devem continuar aprovados.
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
- `verification_id` — referência única da verificação ou asserção;
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

O domínio não deve manter duas fontes independentes de verdade para o mesmo ator.

Se compatibilidade transitória for necessária durante o incremento, ela deve ser
deliberada, testada e removida ou documentada antes do fechamento da Issue.

O identificador estável poderá ser acessado como:

```python
review.reviewer_identity.specialist_id
```

ou por propriedade derivada equivalente, caso a implementação demonstre ganho de
compatibilidade sem duplicação de estado.

### Integração com auditoria

`AuditEvent.actor_id` permanece string:

```python
actor_id = review.reviewer_identity.specialist_id
```

A proveniência mínima deve ser adicionada ao `metadata`.

Forma conceitual:

```python
metadata={
    "system_recommendation": "...",
    "human_decision": "...",
    "agrees_with_system": True,
    "correction_count": 0,
    "identity_provider": "...",
    "identity_subject": "...",
    "identity_verification_id": "...",
    "identity_verified_at": "...",
}
```

Os nomes finais devem ser estabilizados pelos testes antes do fechamento da SPEC.

### Compatibilidade com persistência

O schema atual já serializa:

```python
"metadata": dict(event.metadata)
```

e a desserialização aceita um `Mapping`.

Por isso, a hipótese inicial é:

```text
schema_version = 1 permanece suficiente
```

desde que os novos valores de metadata sejam JSON-serializáveis.

`verified_at` deve, portanto, ser registrado em metadata como representação ISO 8601,
e não como objeto `datetime` bruto.

Se testes demonstrarem incompatibilidade estrutural, a Issue deve ser reavaliada
antes de introduzir `schema_version = 2`.

## 9. Arquivos previstos

Alterações prováveis:

```text
src/agent_lab/human_review.py
src/agent_lab/audit.py
tests/test_human_review.py
tests/test_audit.py
docs/specs/0041_verifiable_specialist_identity_v1.md
docs/PROJECT_COMPASS.md
```

Alterações condicionais, somente se necessárias:

```text
tests/test_audit_serialization.py
tests/test_audit_persistence_integration.py
README.md
CHANGELOG.md
```

Não criar novo módulo apenas por preferência estética. Se o contrato de identidade
ficar pequeno e coeso com o Human-in-the-Loop, ele pode permanecer em
`human_review.py` nesta versão.

## 10. Estratégia TDD

### Etapa A — contrato de identidade

#### RED

Criar testes para:

- caminho feliz;
- `specialist_id` vazio;
- `identity_provider` vazio;
- `identity_subject` vazio;
- `verification_id` vazio;
- `verified_at` sem timezone;
- imutabilidade.

#### GREEN

Implementar apenas o contrato e suas validações.

### Etapa B — integração com `HumanReview`

#### RED

Criar testes para:

- revisão aceita `VerifiedSpecialistIdentity`;
- identidade inválida não chega a produzir revisão;
- especialista permanece correlacionável;
- regras existentes de decisão permanecem válidas.

#### GREEN

Substituir a identidade puramente declarativa no contrato de revisão.

### Etapa C — integração com auditoria

#### RED

Criar testes para:

- `actor_id == specialist_id`;
- provider preservado em metadata;
- subject preservado em metadata;
- verification id preservado em metadata;
- `verified_at` preservado em ISO 8601;
- evento continua imutável.

#### GREEN

Propagar a identidade verificada por `record_human_review`.

### Etapa D — persistência

Executar os testes existentes de serialização e repositório.

Adicionar novo teste apenas se necessário para provar que a nova metadata faz
round-trip mantendo `schema_version = 1`.

## 11. Critérios de aceite

- [ ] existe `VerifiedSpecialistIdentity` imutável;
- [ ] `specialist_id` rejeita branco;
- [ ] `identity_provider` rejeita branco;
- [ ] `identity_subject` rejeita branco;
- [ ] `verification_id` rejeita branco;
- [ ] `verified_at` rejeita datetime sem timezone;
- [ ] `HumanReview` carrega identidade verificável;
- [ ] não existem duas fontes conflitantes de identidade do revisor;
- [ ] identificador estável do especialista permanece acessível;
- [ ] `record_human_review` recebe a identidade verificável;
- [ ] `AuditEvent.actor_id` corresponde a `specialist_id`;
- [ ] proveniência mínima fica registrada em metadata;
- [ ] `verified_at` auditado é serializável;
- [ ] identidade inválida impede resultado correlacionado;
- [ ] contratos de decisão humana permanecem válidos;
- [ ] schema de persistência v1 permanece compatível ou mudança é explicitamente justificada;
- [ ] testes anteriores permanecem verdes;
- [ ] novos testes cobrem identidade, integração e auditoria;
- [ ] CI permanece verde em Python 3.11;
- [ ] autenticação e autorização continuam fora do escopo;
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

### Acoplamento prematuro

Não adicionar campos específicos de Active Directory, Google, Microsoft, Okta ou
outro provedor.

O contrato deve permanecer agnóstico.

### Duplicação de identidade

Evitar manter simultaneamente:

```text
reviewer_id
reviewer_identity.specialist_id
```

como valores independentes.

Se ambos existirem temporariamente, deve existir uma única fonte de verdade e teste
explícito de coerência.

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
    identity_provider  = "provider"
    identity_subject   = "subject"
    verification_id    = "verification-001"
    verified_at        = timezone-aware datetime
```

Auditoria:

```text
AuditEvent
  actor_id = "specialist-001"

  metadata
    identity_provider
    identity_subject
    identity_verification_id
    identity_verified_at
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
