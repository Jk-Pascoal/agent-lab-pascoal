# SPEC — Título do incremento

> Este arquivo é o modelo oficial de especificação técnica do Agent Lab Pascoal.
> Para cada incremento relevante, copie este documento, renomeie-o e preencha
> todas as seções aplicáveis antes da implementação.

## Metadados

| Campo | Valor |
| --- | --- |
| Identificador | `SPEC-XXXX` |
| Status | `Proposta`, `Aprovada`, `Implementada` ou `Substituída` |
| Issue relacionada | `#XXXX` |
| Responsável | Nome ou usuário do GitHub |
| Data de criação | `AAAA-MM-DD` |
| Última atualização | `AAAA-MM-DD` |

## 1. Contexto

Descreva o cenário atual do projeto e por que este incremento está sendo
proposto. Inclua apenas o contexto necessário para compreender a decisão.

## 2. Problema, evidências e impacto

### Problema

Explique de forma objetiva o problema que precisa ser resolvido.

### Evidências

Registre fatos observáveis, exemplos, resultados de testes, métricas ou
limitações que comprovem o problema. Não substitua evidências por suposições.

### Impacto

Explique quem ou o que é afetado e quais riscos existem caso o problema não
seja tratado.

## 3. Objetivo

Declare o resultado esperado de forma mensurável. O objetivo deve explicar o
que será alcançado, e não apenas listar tarefas.

## 4. Escopo

### Incluído

- item incluído no incremento;
- item incluído no incremento.

### Fora do escopo

- item que não será tratado neste incremento;
- item que deverá ser tratado em outra Issue.

## 5. Responsabilidade humana e limites do agente

Descreva quais decisões podem ser recomendadas pelo sistema e quais continuam
sob responsabilidade de um especialista humano.

No Agent Lab Pascoal, saídas de agentes são recomendações auditáveis. Elas não
substituem automaticamente a decisão do especialista de domínio, especialmente
em aprovações, rejeições e alterações de dados PDM/BOM.

## 6. Requisitos

### Requisitos funcionais

- `RF-01` — descreva um comportamento observável;
- `RF-02` — descreva outro comportamento observável.

### Requisitos de qualidade

- `RQ-01` — descreva uma condição de segurança, testabilidade ou auditoria;
- `RQ-02` — descreva uma condição de desempenho, manutenção ou confiabilidade.

## 7. Proposta técnica

### Visão geral

Explique a solução proposta, as decisões principais e as alternativas
consideradas.

### Fluxo esperado

```text
Entrada → validação → processamento → saída auditável → revisão humana
```

### Contratos de dados

Liste os modelos, campos, tipos, validações, JSON Schemas ou interfaces que
serão criados ou alterados.

### Arquivos previstos

- `caminho/do/arquivo.py` — finalidade da alteração;
- `tests/test_arquivo.py` — comportamento que será verificado;
- `docs/documento.md` — decisão que será documentada.

## 8. Estratégia de testes e TDD

### Vermelho

Defina primeiro o teste ou verificação que demonstra a ausência do
comportamento desejado. Registre por que ele deve falhar antes da implementação.

### Verde

Implemente a menor mudança suficiente para satisfazer o teste e os critérios de
aceite, sem ampliar o escopo da Issue.

### Regressão

Execute a suíte completa para confirmar que comportamentos anteriores continuam
válidos.

### Testes previstos

- cenário válido;
- cenário inválido;
- limite relevante;
- regressão dos comportamentos existentes.

## 9. Gates de qualidade

Antes do Pull Request, execute e registre os comandos aplicáveis:

```powershell
python -m unittest discover -s tests -v
git diff --check
git status -sb
```

Critérios mínimos:

- todos os testes aprovados;
- nenhum erro de espaços em branco em `git diff --check`;
- alteração limitada aos arquivos previstos na SPEC;
- nenhum dado real, credencial ou chave de API versionado;
- documentação atualizada quando a mudança alterar contratos ou fluxo;
- limitações e riscos informados no Pull Request.

## 10. Riscos e limitações

| Risco ou limitação | Probabilidade | Impacto | Mitigação |
| --- | --- | --- | --- |
| Descrever o risco | Baixa/Média/Alta | Baixo/Médio/Alto | Ação preventiva |

Registre também limitações conhecidas que permanecerão após o incremento.

## 11. Plano de reversão

Explique como desfazer a mudança com segurança caso apareça uma regressão.
Indique quais arquivos, configurações ou dados exigem atenção.

## 12. Versionamento e release

### Impacto SemVer

Selecione e justifique uma opção:

- `MAJOR` — mudança incompatível com o contrato anterior;
- `MINOR` — nova funcionalidade compatível;
- `PATCH` — correção compatível;
- `SEM ALTERAÇÃO` — documentação, planejamento ou trabalho ainda não publicado.

### Publicação prevista

- versão planejada: `X.Y.Z` ou `Unreleased`;
- criação de tag: sim/não;
- criação de GitHub Release: sim/não;
- atualização do `CHANGELOG.md`: sim/não.

## 13. Critérios de aceite

- [ ] o comportamento ou documento previsto foi implementado;
- [ ] os testes específicos foram criados e aprovados;
- [ ] a suíte completa permanece aprovada;
- [ ] os gates de qualidade foram executados;
- [ ] riscos e limitações foram registrados;
- [ ] a responsabilidade humana foi preservada;
- [ ] o Pull Request referencia a Issue e esta SPEC.

## 14. Questões em aberto

- questão que ainda precisa de decisão;
- responsável e prazo para a decisão, quando aplicável.

Se não houver questões em aberto, registre: `Nenhuma`.

## 15. Histórico de decisões

| Data | Decisão | Motivo | Responsável |
| --- | --- | --- | --- |
| `AAAA-MM-DD` | Decisão registrada | Evidência ou justificativa | Nome |
