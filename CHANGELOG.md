# Changelog

Todas as mudanças relevantes do Agent Lab Pascoal serão registradas neste
arquivo.

O formato é inspirado em *Keep a Changelog* e o projeto adota Versionamento
Semântico conforme definido em `VERSIONING.md`.

## Como interpretar este arquivo

- `Unreleased` reúne mudanças incorporadas ou em preparação que ainda não
  receberam uma release formal.
- Uma versão somente é considerada publicada quando existir uma tag Git e uma
  GitHub Release correspondentes.
- O número existente no `pyproject.toml`, isoladamente, não comprova que uma
  release foi publicada.
- O histórico prioriza mudanças percebidas por pessoas, contratos e processos;
  não é uma cópia automática de todos os commits.

As mudanças são classificadas em:

- `Added`: funcionalidades, documentos ou capacidades novas;
- `Changed`: alterações em comportamento ou estrutura existente;
- `Deprecated`: recursos mantidos temporariamente antes da remoção;
- `Removed`: recursos eliminados;
- `Fixed`: correções de defeitos;
- `Security`: correções e controles de segurança.

## [Unreleased]

### Added

#### Fundação determinística

- Estrutura inicial do laboratório em Python 3.11 com pacote organizado em
  `src/agent_lab`.
- Modelo de domínio para registros de materiais, decisões de governança,
  alertas e avaliações.
- Validador determinístico de governança de materiais PDM/BOM.
- Regras iniciais para campos críticos, atributos técnicos, unidades suspeitas,
  descrições ambíguas e possíveis duplicidades.
- Normalização de textos com remoção de acentos e pontuação, separação de
  números unidos a letras e expansão de abreviações de categoria.
- Detecção determinística de duplicidade por fabricante, código de peça e
  categoria.
- Interface de terminal para execução do baseline sobre dados sintéticos.

#### Avaliação e risco de negócio

- Dataset sintético rotulado para avaliação reproduzível do baseline.
- Conjunto de desafio separado para revelar limitações que não aparecem no
  conjunto principal.
- Métricas de correspondência exata, cobertura do rótulo esperado, precisão e
  recall de duplicidade.
- Contagem de falsos negativos de duplicidade.
- Contagem de revisões humanas desnecessárias.
- Métrica de custo ponderado dos erros, considerando o falso negativo de
  duplicidade mais caro que uma revisão desnecessária.
- Testes de qualidade mínima e de processamento do conjunto completo.

#### Fronteira estruturada para agentes

- Contrato `GovernanceAgentOutput` com Pydantic para representar respostas
  estruturadas de futuros agentes.
- Reutilização dos Enums de decisão e alerta definidos no domínio.
- Validação de identificador, confiança, resumo, evidências e campos
  obrigatórios.
- Rejeição de campos não previstos no contrato por meio de configuração
  `extra="forbid"`.
- Imutabilidade das saídas validadas por meio de `frozen=True`.
- Conversão de JSON bruto em objeto estruturado antes da entrada no domínio.
- Rejeição testada de JSON malformado, confiança fora dos limites e campos
  inventados.
- Exportação do contrato como JSON Schema para integração futura com LLMs e
  ferramentas que suportem saídas estruturadas.
- Testes que verificam a preservação dos limites e dos valores válidos do
  domínio no JSON Schema.

#### Workflow de engenharia — Issue #8

- Formulário de Issue para propostas de funcionalidade em
  `.github/ISSUE_TEMPLATE/feature.yml`.
- Formulário de Issue para relatos de defeito em
  `.github/ISSUE_TEMPLATE/bug.yml`.
- Template de Pull Request com rastreabilidade, testes, riscos, segurança e
  responsabilidade humana.
- Template reutilizável de especificação em `docs/specs/SPEC_TEMPLATE.md`.
- SPEC da Issue #8 em `docs/specs/0008_engineering_workflow.md`.
- Documentação do fluxo completo em `docs/04_engineering_workflow.md`.
- Guia de contribuição em `CONTRIBUTING.md`.
- Política de versionamento e releases em `VERSIONING.md`.
- Changelog inicial para acompanhar a evolução do laboratório.
- Processo documentado:

  ```text
  Issue → análise → SPEC → TDD → implementação → Pull Request
        → CI → revisão → merge → release
  ```

### Changed

- Evolução do projeto de um conjunto inicial de regras para um laboratório com
  baseline mensurável e fronteira formal para respostas de agentes.
- Critérios técnicos passaram a considerar também o custo de negócio dos erros,
  evitando avaliar qualidade somente por acurácia agregada.
- Respostas externas passam a ser tratadas como dados não confiáveis até serem
  validadas pelo contrato Pydantic.
- Desenvolvimento passa a seguir um workflow explícito, rastreável e orientado
  por testes.
- Documentação passa a separar apresentação do laboratório, aprofundamento
  técnico, especificações e políticas de engenharia.

### Security

- Registro explícito de que o repositório é público e deve conter somente dados
  sintéticos, anonimizados e autorizados.
- Proibição documentada de credenciais, chaves de API, documentos proprietários
  e cadastros reais de empresas.
- Validação estrita da fronteira JSON para impedir que campos inesperados sejam
  aceitos silenciosamente.
- Preservação obrigatória da revisão humana nas recomendações de governança
  PDM/BOM.

### Deprecated

- Nenhum recurso foi formalmente depreciado.

### Removed

- Nenhum recurso público foi formalmente removido.

### Fixed

- Nenhuma correção será declarada como release até a criação do primeiro marco
  versionado formal.

## Releases publicadas

Ainda não existem releases formais publicadas.

A primeira versão será criada em incremento próprio, depois que:

- a Issue #8 estiver incorporada;
- os testes estiverem aprovados na branch `main`;
- o número de versão for revisado;
- as entradas de `Unreleased` forem conferidas;
- a tag anotada e a GitHub Release forem deliberadamente criadas.

Quando isso acontecer, as entradas aplicáveis serão movidas para uma seção no
seguinte formato:

```markdown
## [0.1.0] - AAAA-MM-DD

### Added

- Descrição da capacidade publicada.
```

## Critérios para novas entradas

Inclua uma entrada em `Unreleased` quando uma mudança:

- adicionar funcionalidade ou comportamento público;
- alterar contrato, regra, decisão ou alerta;
- corrigir defeito percebido por usuários;
- modificar instalação, configuração ou execução;
- introduzir depreciação ou remoção;
- alterar segurança, privacidade ou revisão humana;
- mudar resultados ou métricas de avaliação;
- exigir instrução de migração.

Mudanças exclusivamente editoriais podem ser omitidas quando não alterarem o
entendimento ou o uso do projeto.

## Padrão para escrever entradas

Uma boa entrada deve:

- começar pelo resultado observado;
- ser compreensível sem consultar o diff;
- evitar jargão desnecessário;
- identificar incompatibilidade ou migração;
- citar Issue, SPEC ou Pull Request quando isso melhorar a rastreabilidade;
- não incluir dados sensíveis;
- não prometer desempenho que não tenha sido medido.

Prefira:

```text
- Adiciona validação de confiança entre 0 e 1 na saída estruturada.
```

Evite:

```text
- Ajustes no código.
```

## Procedimento de release

Ao preparar uma release:

1. revise todas as entradas de `Unreleased`;
2. remova duplicidades e detalhes puramente internos;
3. identifique mudanças incompatíveis e instruções de migração;
4. defina a versão conforme `VERSIONING.md`;
5. crie a seção `## [X.Y.Z] - AAAA-MM-DD`;
6. mova para ela somente as mudanças incluídas na release;
7. mantenha uma seção `Unreleased` vazia para o próximo ciclo;
8. alinhe o número no `pyproject.toml`;
9. execute os testes e as verificações do Pull Request;
10. crie a tag e a GitHub Release somente após o merge aprovado.

## Responsabilidade humana

As decisões `APPROVE`, `REVIEW` e `REJECT` representam recomendações do sistema.
Nenhuma entrada neste changelog deve sugerir que o agente substitui a decisão de
um profissional autorizado sobre materiais, cadastros ou estruturas PDM/BOM.

Mudanças que alterem evidências, confiança, alertas ou revisão humana devem ser
destacadas de forma explícita.

## Referências de rastreabilidade

- Repositório: <https://github.com/Jk-Pascoal/agent-lab-pascoal>
- Workflow de engenharia: `docs/04_engineering_workflow.md`
- Template de SPEC: `docs/specs/SPEC_TEMPLATE.md`
- SPEC da governança: `docs/specs/0008_engineering_workflow.md`
- Guia de contribuição: `CONTRIBUTING.md`
- Política de versionamento: `VERSIONING.md`

<!--
Links de comparação entre versões devem ser adicionados depois da criação das
tags formais. Não inventar referências para tags ainda inexistentes.

Exemplo futuro:
[Unreleased]: https://github.com/Jk-Pascoal/agent-lab-pascoal/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/Jk-Pascoal/agent-lab-pascoal/releases/tag/v0.1.0
-->
