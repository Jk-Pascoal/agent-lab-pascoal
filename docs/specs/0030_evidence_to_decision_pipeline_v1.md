# SPEC 0030 — Evidence-to-Decision Pipeline v1

**Status:** Concluída
**Issue:** #30 — Evidence-to-Decision Pipeline v1
**Tipo:** Evolução arquitetural
**Método:** TDD

## 1. Contexto

A Issue #27 integrou `GovernanceAgentOutput` ao Evidence Engine. O sistema já consegue converter a saída estruturada do agente LLM em evidências internas de governança, preservando contratos tipados e validação de domínio.

O próximo incremento deve conectar essas evidências a uma recomendação determinística de governança. Essa recomendação continuará subordinada à validação humana: o pipeline recomenda; o especialista decide.

## 2. Problema

O projeto ainda não possui um componente central e explícito responsável por:

1. receber o identificador de um material e suas evidências estruturadas;
2. avaliar a severidade das evidências;
3. aplicar uma política determinística de precedência;
4. produzir uma recomendação tipada;
5. explicar quais evidências sustentaram a recomendação.

Sem essa fronteira, a relação entre evidência e decisão permanece implícita ou distribuída, dificultando testes, auditoria e futura integração com o fluxo human-in-the-loop.

## 3. Objetivos

- Criar uma camada explícita entre o Evidence Engine e o mecanismo de decisão.
- Transformar evidências estruturadas em recomendações determinísticas e tipadas.
- Aplicar a precedência `REJECT > REVIEW > APPROVE`.
- Preservar o `material_id` e as evidências que sustentam cada recomendação.
- Produzir justificativas rastreáveis e explicáveis.
- Manter separadas evidência, recomendação automatizada e decisão humana final.
- Preparar a arquitetura para o futuro fluxo human-in-the-loop.
- Garantir o comportamento por TDD, sem regressões nos 59 testes existentes.

## 4. Escopo proposto

### 4.1 Incluído

- Criar o componente `Evidence-to-Decision Pipeline v1`.
- Definir o contrato de entrada com `material_id` e coleção de evidências estruturadas.
- Definir o contrato de saída com recomendação, justificativa e evidências consideradas.
- Integrar o pipeline aos contratos existentes do Evidence Engine.
- Implementar uma política determinística de precedência.
- Preservar a rastreabilidade entre material, evidências e recomendação.
- Declarar no contrato que a saída é uma recomendação do sistema.
- Criar testes unitários para cenários isolados e combinações de evidências.
- Preservar compatibilidade com os 59 testes existentes.

### 4.2 Fora do escopo

- Interface gráfica.
- Persistência em banco de dados.
- Integração com ERP.
- Chamada direta a provedor LLM.
- Decisão humana final.
- Aprovação ou rejeição automática de cadastros.
- Trilha de auditoria persistente.
- Autenticação, autorização ou perfis de usuário.
- Políticas configuráveis por cliente.

## 5. Princípios de projeto

### 5.1 Separação de responsabilidades

O pipeline não cria nem corrige evidências. Ele apenas interpreta uma coleção já estruturada e produz uma recomendação.

### 5.2 Determinismo

A mesma entrada deve sempre produzir a mesma saída. A versão v1 não dependerá de LLM, aleatoriedade, serviços externos ou estado persistente.

### 5.3 Explicabilidade

Toda recomendação deverá informar a política aplicada e preservar as evidências consideradas.

### 5.4 Human-in-the-loop

`APPROVE`, `REVIEW` e `REJECT` representam recomendações do sistema. Nenhuma delas substitui a decisão final do especialista de governança.

### 5.5 Compatibilidade

Contratos e enums existentes deverão ser reutilizados sempre que forem semanticamente adequados. Não serão criados tipos duplicados para conceitos já representados no domínio.

## 6. Política decisória v1

A recomendação final obedecerá à seguinte ordem de precedência:

```text
REJECT > REVIEW > APPROVE
```

Regras:

1. Se existir ao menos uma evidência crítica, retornar `REJECT`.
2. Na ausência de evidência crítica, se existir ao menos uma evidência revisável, retornar `REVIEW`.
3. Na ausência de evidências críticas ou revisáveis, retornar `APPROVE`.
4. Quando existirem múltiplas evidências, prevalecerá a recomendação mais restritiva.
5. A ordem de entrada das evidências não poderá alterar o resultado.

## 7. Contratos funcionais

### 7.1 Entrada

O pipeline deverá receber:

- `material_id`: identificador não vazio do material;
- `evidences`: coleção imutável ou tratada como imutável de evidências estruturadas.

### 7.2 Saída

O resultado deverá conter, no mínimo:

- `material_id`;
- `recommendation`: `APPROVE`, `REVIEW` ou `REJECT`;
- `evidences`: evidências consideradas;
- `rationale`: justificativa determinística;
- indicação semântica ou documental de que a saída não é a decisão humana final.

Os nomes definitivos dos tipos e campos serão alinhados aos contratos já existentes durante a implementação, evitando duplicação conceitual.

## 8. Invariantes

- O `material_id` de saída deve ser igual ao `material_id` de entrada.
- A coleção recebida não deve ser alterada pelo pipeline.
- A ordem das evidências não deve modificar a recomendação.
- `REJECT` sempre prevalece sobre `REVIEW` e `APPROVE`.
- `REVIEW` sempre prevalece sobre `APPROVE`.
- A ausência de impedimentos produz `APPROVE`.
- A justificativa deve corresponder à recomendação efetivamente produzida.
- A recomendação nunca deve ser apresentada como decisão humana final.

## 9. Cenários de teste

### 9.1 Aprovação

- coleção vazia de evidências impeditivas retorna `APPROVE`;
- o resultado preserva o `material_id`;
- a justificativa informa a ausência de impedimentos.

### 9.2 Revisão

- uma evidência revisável retorna `REVIEW`;
- múltiplas evidências revisáveis continuam retornando `REVIEW`;
- a justificativa identifica a necessidade de avaliação humana.

### 9.3 Rejeição

- uma evidência crítica retorna `REJECT`;
- evidência crítica combinada com evidência revisável retorna `REJECT`;
- a justificativa identifica a existência de impedimento crítico.

### 9.4 Precedência e estabilidade

- `REJECT` prevalece sobre `REVIEW`;
- `REVIEW` prevalece sobre `APPROVE`;
- permutar a ordem das evidências não altera o resultado;
- as evidências consideradas permanecem disponíveis no resultado.

### 9.5 Validação de contrato

- `material_id` vazio é rejeitado conforme o padrão do domínio;
- entradas inválidas não produzem recomendações silenciosamente;
- a coleção de entrada não é modificada.

### 9.6 Regressão

- os 59 testes anteriores permanecem aprovados;
- a suíte completa passa localmente e na CI com Python 3.11.

## 10. Critérios de aceitação

- [x] O pipeline recebe `material_id` e evidências estruturadas.
- [x] O pipeline retorna uma recomendação tipada.
- [x] Evidências críticas produzem `REJECT`.
- [x] Evidências revisáveis produzem `REVIEW`.
- [x] A ausência de impedimentos produz `APPROVE`.
- [x] A recomendação mais restritiva prevalece em coleções mistas.
- [x] A ordem das evidências não altera a recomendação.
- [x] O resultado preserva o `material_id`.
- [x] O resultado informa as evidências utilizadas.
- [x] O resultado contém justificativa determinística.
- [x] O contrato distingue recomendação automatizada de decisão humana final.
- [x] Os novos comportamentos são cobertos por testes unitários.
- [x] Os testes anteriores permanecem aprovados.
- [x] A CI permanece verde.

## 11. Riscos e mitigação

### 11.1 Duplicação de regras

**Risco:** reproduzir no pipeline lógica já existente no baseline ou no domínio.
**Mitigação:** inspecionar e reutilizar enums, contratos e funções existentes antes da implementação.

### 11.2 Mistura entre evidência e decisão

**Risco:** o novo componente começar a gerar, corrigir ou reinterpretar evidências.
**Mitigação:** limitar sua responsabilidade à aplicação da política decisória sobre evidências já estruturadas.

### 11.3 Automação indevida da governança

**Risco:** interpretar a recomendação como autorização automática para alterar o ERP.
**Mitigação:** declarar no contrato e na documentação que a decisão humana final permanece fora do pipeline.

### 11.4 Acoplamento ao LLM

**Risco:** tornar a política decisória dependente do provedor ou do texto produzido pelo modelo.
**Mitigação:** manter a v1 determinística e dependente apenas dos contratos internos validados.

## 12. Plano TDD

1. Criar a branch da Issue #30.
2. Criar os testes do contrato de saída e dos três resultados possíveis.
3. Criar testes de precedência, estabilidade de ordem e preservação do `material_id`.
4. Executar os novos testes e registrar a falha esperada.
5. Implementar apenas o comportamento necessário para fazê-los passar.
6. Executar a suíte completa.
7. Refatorar sem alterar o comportamento.
8. Atualizar esta SPEC com decisões técnicas efetivamente adotadas.
9. Abrir o Pull Request vinculado à Issue #30.
10. Validar review e CI antes do merge.

## 13. Arquivos previstos

Os nomes poderão ser ajustados após a inspeção do domínio existente, mas a mudança deverá permanecer concentrada, preferencialmente, em:

```text
docs/specs/0030_evidence_to_decision_pipeline_v1.md
src/agent_lab/decision.py
tests/test_decision.py
```

Alterações em outros arquivos exigirão justificativa no Pull Request.

## 14. Definition of Done

- SPEC versionada e vinculada à Issue #30.
- Implementação concluída por TDD.
- Política decisória explícita e determinística.
- Recomendação explicável e rastreável.
- Separação entre sistema recomendador e decisão humana preservada.
- Suíte completa aprovada localmente.
- GitHub Actions aprovado.
- Revisão concluída.
- Pull Request incorporado à `main`.
- Issue #30 encerrada.

## 15. Encerramento

Implementação concluída e incorporada à `main` em 14 de agosto de 2026.

- **Issue:** #30 — Evidence-to-Decision Pipeline v1
- **Pull Request:** #31 — `feat: add evidence-to-decision pipeline (#30)`
- **Commit da implementação:** `3b8d774`
- **Commit de merge:** `dbf3abf`
- **CI obrigatória:** `Tests / Python 3.11` aprovada
- **Baseline anterior:** 59 testes aprovados
- **Baseline final:** 70 testes aprovados
- **Evolução:** 11 novos testes, zero regressões
- **Estado final:** pipeline determinístico, explicável e subordinado à decisão humana

---

**Referência:** Issue #30 — Evidence-to-Decision Pipeline v1
**Baseline final:** 70 testes aprovados
**Próximo incremento arquitetural:** human-in-the-loop e trilha de auditoria, em Issue própria.
