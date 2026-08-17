# PROJECT COMPASS — Agent Lab Pascoal

> Ponto oficial de reentrada cognitiva e operacional do projeto.
>
> Leia este documento antes de propor uma nova Issue, SPEC ou alteração de código.

## 1. Identidade do projeto

- **Projeto:** Agent Lab Pascoal
- **Repositório:** `Jk-Pascoal/agent-lab-pascoal`
- **Domínio:** governança de materiais PDM/BOM e Master Data
- **Linguagem:** Python 3.11
- **Runner oficial de testes:** `unittest`
- **Branch protegida:** `main`
- **Estado registrado em:** 2026-08-16
- **Baseline atual:** 128 testes aprovados
- **Última entrega:** Persistência auditável v1 e repositório JSONL
- **Última Issue concluída:** #37
- **Incremento atual:** Nenhum incremento aberto — próxima âncora: identidade verificável
- **Último PR integrado:** #39
- **Última SPEC:** `docs/specs/0037_audit_persistence_v1.md`

## 2. Propósito

O Agent Lab Pascoal é um sistema experimental de engenharia para governança de materiais industriais. Seu objetivo é apoiar a análise de cadastros PDM/BOM por meio de uma arquitetura híbrida que combina:

- regras determinísticas;
- normalização e validação de dados;
- detecção de duplicidades;
- saídas estruturadas de LLM;
- evidências auditáveis;
- recomendações de decisão;
- revisão humana obrigatória;
- trilha de auditoria.

O sistema não substitui o especialista de governança. Ele organiza evidências, detecta riscos e produz recomendações para apoiar uma decisão humana rastreável.

## 3. Tese arquitetural

O projeto segue esta separação de responsabilidades:

```text
Regras determinísticas
        ↓
LLM estruturada
        ↓
Evidence Engine
        ↓
Decision Recommendation
        ↓
Human-in-the-Loop
        ↓
Audit Event
        ↓
Serialização versionada
        ↓
Audit Repository (JSONL)
        ↓
Identidade e workflow futuros
        ↓
Integração ERP futura
```

Princípio central:

```text
A IA recomenda; o humano decide; a auditoria preserva o percurso.
```

## 4. Estado arquitetural atual

### 4.1 Núcleo normativo implementado

O sistema já representa e valida:

- materiais e atributos relevantes;
- normalização de descrições;
- validações cadastrais;
- possíveis duplicidades;
- issues estruturadas;
- severidade de problemas;
- evidências de regras e LLM;
- recomendações `APPROVE`, `REVIEW` e `REJECT`;
- confiança da recomendação;
- revisão humana;
- aprovação, reprovação e solicitação de correção;
- concordância e divergência humano–sistema;
- eventos de auditoria imutáveis;
- serialização versionada de auditoria (`schema_version = 1`);
- persistência local append-only pela API com JSONL;
- escrita durável com `flush` e `fsync`;
- recuperação e consultas de histórico com leitura *fail-closed*.

### 4.2 Limite atual

A versão atual possui:

- persistência local JSONL e execução síncrona/monoprocesso;
- identidade declarativa do especialista;
- validação em cenários controlados;
- ausência de autenticação e autorização;
- ausência de filas e estados completos de workflow;
- ausência de integração com ERP.

### 4.3 Próxima âncora

A próxima frente arquitetural é **identidade verificável**.

Sequência evolutiva recomendada:

```text
Contrato
  → Memória persistente
  → Identidade verificável
  → Workflow temporal
  → Integração ERP
```

Não implementar todas essas camadas em uma única Issue.

## 5. Invariantes constitucionais

Estas regras não devem ser alteradas incidentalmente:

1. A recomendação automática nunca é uma decisão humana.
2. `requires_human_decision` permanece `True` no escopo atual.
3. Confiança não concede autoridade operacional.
4. A recomendação original não pode ser sobrescrita pela decisão humana.
5. Divergências humano–sistema devem permanecer auditáveis.
6. Revisões concluídas e eventos de auditoria são imutáveis.
7. Reprovação exige justificativa.
8. Solicitação de correção exige justificativa e correção estruturada.
9. Aprovação não pode conter correções pendentes.
10. Timestamps de revisão e auditoria devem conter timezone.
11. A integração com ERP não deve executar apenas com base em recomendação automática.
12. O histórico não deve ser reconstruído somente a partir do estado final.
13. Concordância humano–IA não equivale automaticamente à verdade.
14. Casos objetivos devem ser resolvidos por regras antes de recorrer à LLM.
15. A LLM deve operar com contratos de saída estruturados e validados.

Qualquer mudança nessas regras exige:

- Issue explícita;
- evidências;
- análise de impacto;
- nova SPEC ou atualização deliberada de SPEC;
- testes que demonstrem o novo comportamento;
- revisão humana no PR.

## 6. Contratos e módulos centrais

### 6.1 Domínio e validação

```text
src/agent_lab/domain.py
src/agent_lab/normalization.py
src/agent_lab/validator.py
src/agent_lab/decision.py
```

Responsabilidades:

- tipos centrais;
- normalização;
- validação determinística;
- recomendação de decisão.

### 6.2 LLM e evidências

```text
src/agent_lab/llm_schema.py
src/agent_lab/llm_service.py
src/agent_lab/evidence.py
```

Responsabilidades:

- contrato estruturado da LLM;
- fronteira de execução da LLM;
- evidências originadas por regras e modelo;
- preservação da identidade do material;
- integração evidência–decisão.

### 6.3 Human-in-the-Loop

```text
src/agent_lab/human_review.py
```

Contratos principais:

- `HumanDecision`;
- `CorrectionRequest`;
- `HumanReview`.

Responsabilidades:

- representar a decisão final humana;
- preservar a recomendação automática;
- registrar especialista e timestamp;
- estruturar correções;
- indicar concordância ou divergência.

### 6.4 Auditoria

```text
src/agent_lab/audit.py
```

Contratos principais:

- `AuditEventType`;
- `AuditEvent`;
- `HumanReviewResult`;
- `record_human_review`.

Responsabilidades:

- criar evento correlacionado à revisão;
- congelar metadados defensivamente;
- preservar material, especialista, instante e decisão;
- produzir resultado auditável sem persistência ou efeitos externos.

### 6.5 Persistência e repositório de auditoria

```text
src/agent_lab/audit_serialization.py
src/agent_lab/audit_repository.py
```

Contratos principais:

- `audit_event_to_record`;
- `audit_event_from_record`;
- `AuditRepository`;
- `JsonlAuditRepository`;
- `AuditPersistenceError`;
- `DuplicateAuditEventError`;
- `AuditCorruptionError`.

Responsabilidades:

- serializar e desserializar `AuditEvent` com versão de schema explícita (`schema_version = 1`);
- persistir eventos de forma append-only em arquivo JSONL local;
- garantir sincronização em disco com `flush` e `os.fsync`;
- recuperar histórico por `event_id`, `material_id` e listagem completa;
- falhar de forma *fail-closed* diante de corrupção ou duplicidade;
- manter o domínio desacoplado de infraestrutura de armazenamento.

## 7. Comando canônico de testes

Use sempre:

```powershell
python -m unittest discover -s tests -v
```

Baseline esperado em 2026-08-16:

```text
Ran 128 tests
OK
```

Não assumir `pytest`.

Uma migração de runner somente poderá ocorrer por decisão explícita, documentada e testada.

## 8. Métrica de custo do baseline

O baseline utiliza uma função de custo ponderado inicial:

```text
duplicidade não detectada = custo 5
revisão humana desnecessária = custo 1
```

Representação:

```text
custo = 5 × falsos negativos de duplicidade
      + 1 × revisões desnecessárias
```

Interpretação:

- deixar uma duplicidade entrar tende a produzir efeitos sistêmicos;
- uma revisão desnecessária tende a produzir custo localizado de tempo e fila;
- o valor 5:1 é uma hipótese inicial de risco, não uma constante universal;
- a razão deverá ser calibrada com dados industriais reais.

## 9. Fronteira de autoridade

`DecisionRecommendation` é uma recomendação, não uma autorização.

Mesmo quando:

```text
decision = APPROVE
confidence = 1.0
```

o contrato deve preservar:

```text
requires_human_decision = True
```

Razão:

```text
confiança epistemológica ≠ autoridade operacional
```

Uma integração futura com ERP deverá exigir decisão humana válida e auditável, e não apenas recomendação automática.

## 10. Protocolo diário de reentrada

Ao iniciar uma nova rotina do Agent Lab, seguir esta ordem.

### Passo 1 — Ler este Compass

Confirmar:

- propósito;
- estado arquitetural;
- baseline;
- última entrega;
- próxima âncora;
- invariantes.

### Passo 2 — Verificar o Git

```powershell
git status
git branch --show-current
git log -5 --oneline
```

Confirmar:

- branch atual;
- sincronização com `origin/main`;
- working tree;
- últimos commits.

### Passo 3 — Confirmar o contrato operacional

Antes de recomendar comandos:

- verificar Python configurado;
- verificar workflow da CI;
- verificar runner oficial;
- verificar estrutura de arquivos;
- não substituir fatos do repositório por convenções genéricas.

### Passo 4 — Executar o baseline

```powershell
python -m unittest discover -s tests -v
```

Não iniciar nova implementação se o baseline estiver vermelho sem diagnóstico explícito.

### Passo 5 — Recapitular o estado

Registrar em poucas linhas:

```text
Núcleo atual:
Última entrega:
Baseline:
Limitação principal:
Próxima âncora:
```

### Passo 6 — Somente então abrir nova Issue

Toda Issue deve conter, conforme aplicável:

- problema;
- contexto;
- objetivo;
- evidências;
- solução ou hipóteses;
- escopo;
- fora do escopo;
- riscos e limitações;
- impactos;
- critérios de aceite;
- estratégia de validação.

## 11. Fluxo de engenharia

Fluxo padrão:

```text
Issue
  → branch
  → SPEC
  → commit documental
  → teste RED
  → commit do teste
  → implementação GREEN
  → regressão completa
  → atualização da SPEC
  → push
  → Pull Request
  → CI
  → merge
  → exclusão da branch
  → sincronização da main
  → validação pós-merge
  → Relatório Diário
```

O Relatório Diário é uma etapa obrigatória do encerramento técnico.

## 12. Hierarquia das fontes de verdade

Em caso de dúvida ou conflito, usar esta ordem:

1. comportamento validado pelos testes atuais;
2. código integrado à `main`;
3. SPEC implementada mais recente;
4. workflows e configurações do repositório;
5. este `PROJECT_COMPASS.md`;
6. Relatórios Diários;
7. memória conversacional;
8. convenções genéricas de engenharia.

Se este Compass divergir da `main`, a `main` e seus testes prevalecem e o Compass deve ser atualizado.

## 13. Decisões deliberadamente adiadas

- persistência em banco de dados;
- proteção física ou criptográfica contra adulteração do histórico;
- event sourcing completo;
- autenticação e autorização;
- papéis e segregação de funções;
- taxonomia completa de motivos;
- estados de workflow;
- filas e SLAs;
- notificações e escalonamento;
- interface do especialista;
- integração e fila de injeção ERP;
- idempotência e retentativas da integração;
- métricas de override humano–IA;
- benchmark industrial com ground truth;
- automação parcial por classe de risco.

Não implementar uma decisão adiada incidentalmente dentro de outra Issue.

## 14. Esteira evolutiva

Frentes oficiais de evolução:

- PoC vendável de diagnóstico de qualidade cadastral;
- Duplicate Intelligence;
- prevenção de novos cadastros duplicados;
- copiloto do analista PDM;
- arquitetura híbrida de regras, similaridade, RAG e LLM;
- Evidence Engine;
- Human-in-the-Loop;
- benchmark com ground truth;
- métricas de precision, recall e F1;
- versionamento de dados;
- dashboards;
- integração com CSV, Excel, SQL e ERP.

Essas frentes formam uma esteira; não são autorização para desenvolvimento simultâneo.

## 15. Critérios para a próxima Issue

Antes de abrir a próxima Issue, responder:

1. Qual limitação atual ela resolve?
2. Qual evidência demonstra que a limitação importa agora?
3. Qual é a menor entrega vertical testável?
4. Quais invariantes ela deve preservar?
5. O que ficará explicitamente fora do escopo?
6. Como saberemos que a implementação funcionou?
7. Quantos novos riscos operacionais ela introduz?
8. A nova camada pode ser removida ou substituída sem corromper o domínio?

## 16. Política de atualização deste Compass

Atualizar este documento quando houver mudança em:

- baseline de testes;
- comando canônico;
- arquitetura;
- invariantes;
- última entrega;
- próxima âncora;
- módulos centrais;
- limites do sistema;
- decisões deliberadamente adiadas.

Não atualizar o Compass por alterações cosméticas ou tarefas que não modifiquem o estado estrutural do projeto.

Toda atualização deve ocorrer na mesma branch da mudança que a tornou necessária, ou em uma Issue documental explicitamente vinculada.

## 17. Estado resumido para reentrada rápida

```text
AGENT LAB PASCOAL

Propósito:
Governança assistida de materiais PDM/BOM.

Arquitetura atual:
Regras + LLM estruturada + evidências + recomendação
+ decisão humana + evento de auditoria + serialização versionada
+ repositório JSONL append-only.

Autoridade:
A IA recomenda; o humano decide.

Baseline:
128 testes | unittest | Python 3.11.

Última entrega:
Issue #37 | SPEC 0037 | PR #38.

Limite atual:
Persistência local JSONL e identidade declarativa.

Próxima âncora:
Identidade verificável.

Comando oficial:
python -m unittest discover -s tests -v
```

