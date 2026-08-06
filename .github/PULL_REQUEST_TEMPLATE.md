# Pull Request

## Vínculos obrigatórios

<!-- Substitua os exemplos pelos vínculos reais. -->

- Issue: Closes #0000
- SPEC: `docs/specs/0000_nome_da_spec.md`

## Problema e objetivo

<!--
Resuma o problema tratado e o resultado esperado. Não copie toda a Issue ou a
SPEC; destaque apenas o contexto necessário para revisar este Pull Request.
-->

## Mudanças realizadas

<!-- Liste as mudanças efetivamente presentes no diff. -->

- mudança realizada;
- mudança realizada.

## Fora do escopo

<!-- Registre explicitamente o que permaneceu fora deste incremento. -->

- item não tratado;
- item reservado para outra Issue.

## TDD e estratégia de validação

### Vermelho

<!-- Qual teste ou verificação demonstrou inicialmente a ausência do comportamento? -->

### Verde

<!-- Qual foi a menor implementação necessária para satisfazer o teste? -->

### Regressão

<!-- Informe o resultado da suíte completa. -->

## Evidências de validação

### Comandos executados

```powershell
python -m unittest discover -s tests -v
git diff --check
git status -sb
```

### Resultados

<!-- Substitua pelos resultados reais. -->

- testes específicos: `PREENCHER`;
- suíte completa: `PREENCHER`;
- `git diff --check`: `PREENCHER`;
- validação manual, quando aplicável: `PREENCHER`.

## Impacto funcional

<!-- Marque uma opção e explique quando necessário. -->

- [ ] altera comportamento funcional;
- [ ] corrige comportamento existente;
- [ ] altera somente testes, documentação ou governança;
- [ ] altera contrato público ou estrutura de dados;
- [ ] não altera regras de governança PDM/BOM.

## Responsabilidade humana

<!--
Explique como a mudança preserva a decisão final do especialista. Saídas de
agentes são recomendações auditáveis e não autorizações automáticas.
-->

- [ ] a decisão final de domínio permanece sob responsabilidade humana;
- [ ] recomendações do agente continuam acompanhadas de evidências;
- [ ] nenhuma aprovação, rejeição ou alteração PDM/BOM foi automatizada sem
      revisão humana;
- [ ] não se aplica, pois a mudança não toca decisões de domínio.

## Riscos

| Risco | Impacto | Mitigação |
| --- | --- | --- |
| Descrever ou registrar `Nenhum identificado` | Baixo/Médio/Alto | Ação de mitigação |

## Limitações conhecidas

<!-- Registre o que esta mudança ainda não resolve. Não deixe limitações ocultas. -->

- limitação conhecida ou `Nenhuma identificada`.

## Segurança e dados

- [ ] nenhum cadastro real de empresa foi incluído;
- [ ] nenhuma informação comercial ou documento proprietário foi incluído;
- [ ] nenhuma credencial, chave de API ou segredo foi versionado;
- [ ] dados de teste são sintéticos ou públicos e possuem origem identificada;
- [ ] logs e capturas de tela foram revisados para remover informações sensíveis.

## Versionamento e release

### Impacto SemVer

<!-- Marque uma opção e justifique abaixo. -->

- [ ] `MAJOR` — mudança incompatível;
- [ ] `MINOR` — nova funcionalidade compatível;
- [ ] `PATCH` — correção compatível;
- [ ] `SEM ALTERAÇÃO` — mudança ainda em `Unreleased` ou somente documental.

Justificativa:

### Publicação

- [ ] `CHANGELOG.md` atualizado quando aplicável;
- [ ] criação de tag necessária;
- [ ] criação de GitHub Release necessária;
- [ ] nenhuma tag ou release será criada neste incremento.

## Plano de reversão

<!-- Explique como desfazer a mudança com segurança. -->

## Checklist do autor

- [ ] li a Issue e a SPEC antes de implementar;
- [ ] o diff está limitado ao escopo aprovado;
- [ ] criei ou atualizei testes quando houve mudança funcional;
- [ ] executei os testes específicos;
- [ ] executei a suíte completa;
- [ ] executei `git diff --check`;
- [ ] atualizei a documentação afetada;
- [ ] registrei riscos e limitações;
- [ ] revisei segurança, privacidade e responsabilidade humana;
- [ ] não deixei código temporário, credenciais ou dados reais.

## Checklist do revisor

- [ ] Issue, SPEC e Pull Request estão coerentes;
- [ ] os critérios de aceite são verificáveis e foram atendidos;
- [ ] os testes cobrem o comportamento relevante;
- [ ] os gates de qualidade foram comprovados;
- [ ] riscos, limitações e plano de reversão são adequados;
- [ ] a responsabilidade humana pelas decisões de domínio foi preservada;
- [ ] a estratégia de versionamento está correta;
- [ ] o Pull Request está pronto para merge.
