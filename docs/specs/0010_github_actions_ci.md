# SPEC 0010 — Integração contínua com GitHub Actions

## Metadados

- Issue: #10
- Status: Em implementação
- Data: 06/08/2026
- Responsável: Jakson Pascoal
- Área: Testes e qualidade

## 1. Contexto

O Agent Lab Pascoal possui uma suíte automatizada com 24 testes executados
localmente por meio do módulo `unittest`.

Até o momento, a validação depende da execução manual dos testes antes de cada
commit e Pull Request. O GitHub ainda não verifica automaticamente se uma
alteração mantém o comportamento esperado do sistema.

## 2. Problema

Uma alteração pode ser incorporada à branch `main` sem que a suíte de testes
tenha sido executada. Isso cria risco de regressão e torna a qualidade do
repositório dependente exclusivamente da disciplina manual do desenvolvedor.

## 3. Objetivo

Criar um workflow de integração contínua com GitHub Actions que execute
automaticamente a suíte completa de testes em Python 3.11.

O workflow deverá ser acionado em:

- pushes direcionados à branch `main`;
- Pull Requests direcionados à branch `main`.

## 4. Resultado esperado

Cada Pull Request deverá apresentar um check automático informando se:

- o ambiente Python foi configurado;
- o projeto foi instalado;
- as dependências foram instaladas;
- os 24 testes foram executados;
- a suíte foi aprovada ou reprovada.

## 5. Escopo

Este incremento inclui:

- criação de `.github/workflows/tests.yml`;
- utilização de um executor Linux fornecido pelo GitHub;
- configuração do Python 3.11;
- instalação do projeto em modo editável;
- execução da suíte completa com `unittest`;
- acionamento automático em push e Pull Request para `main`.

## 6. Fora do escopo

Este incremento não inclui:

- integração com provedores de LLM;
- deploy da aplicação;
- publicação automática de releases;
- cálculo de cobertura de testes;
- execução em múltiplas versões do Python;
- execução em múltiplos sistemas operacionais;
- armazenamento de credenciais;
- proteção obrigatória da branch `main`.

## 7. Solução técnica proposta

O workflow utilizará:

- `actions/checkout` para obter o código do repositório;
- `actions/setup-python` para configurar o Python 3.11;
- `python -m pip install --upgrade pip` para atualizar o instalador;
- `python -m pip install -e .` para instalar o projeto e suas dependências;
- `python -m unittest discover -s tests -v` para executar a suíte completa.

## 8. Fluxo esperado

```text
Push ou Pull Request
        ↓
GitHub Actions inicia o job
        ↓
Código do repositório é obtido
        ↓
Python 3.11 é configurado
        ↓
Projeto e dependências são instalados
        ↓
24 testes são executados
        ↓
Check aprovado ou reprovado
```

## 9. Critérios de aceite

- [ ] existe um arquivo `.github/workflows/tests.yml`;
- [ ] o arquivo contém YAML válido;
- [ ] o workflow é acionado em Pull Requests para `main`;
- [ ] o workflow é acionado em pushes para `main`;
- [ ] o ambiente utiliza Python 3.11;
- [ ] o projeto é instalado por meio do `pyproject.toml`;
- [ ] os testes são executados com `unittest`;
- [ ] os 24 testes são aprovados no GitHub Actions;
- [ ] o resultado aparece como check no Pull Request;
- [ ] a suíte local permanece aprovada;
- [ ] nenhuma credencial ou informação sensível é utilizada.

## 10. Riscos

### Erro de sintaxe ou indentação no YAML

Um erro de estrutura pode impedir que o GitHub reconheça ou execute o workflow.

Mitigação: revisar o arquivo completo e observar a execução inicial no GitHub.

### Diferenças entre Windows e Linux

Os testes são executados localmente no Windows, enquanto o GitHub Actions
utilizará inicialmente `ubuntu-latest`.

Mitigação: evitar dependências de caminhos específicos do Windows e utilizar
comandos portáveis do Python.

### Falha na instalação das dependências

Uma dependência ausente no `pyproject.toml` pode funcionar localmente, mas
falhar em um ambiente limpo.

Mitigação: instalar o projeto em um ambiente novo durante o workflow.

## 11. Segurança

O workflow não utilizará:

- chaves de API;
- credenciais;
- dados reais de empresas;
- documentos proprietários;
- secrets do GitHub.

Somente código público, dependências e dados sintéticos do laboratório serão
processados.

## 12. Estratégia de validação

A validação será realizada em três níveis:

1. execução local dos 24 testes;
2. verificação do YAML e das alterações com Git;
3. execução automática no GitHub Actions durante o Pull Request.

## 13. Estratégia de rollback

Se o workflow impedir incorretamente o desenvolvimento:

1. não realizar o merge do Pull Request;
2. revisar o log apresentado pelo GitHub Actions;
3. corrigir o workflow na mesma branch;
4. enviar um novo commit;
5. aguardar uma nova execução automática.

## 14. Valor educacional

Este incremento introduz os seguintes conceitos:

- integração contínua;
- ambientes limpos e reproduzíveis;
- automação da qualidade;
- eventos de push e Pull Request;
- jobs, steps e runners;
- diferença entre teste local e teste remoto;
- checks automatizados;
- diagnóstico por logs.

## 15. Rastreabilidade

Esta especificação implementa a Issue #10:

`[FEATURE] Automatizar testes com GitHub Actions`

O futuro Pull Request deverá conter:

```text
Closes #10
```
