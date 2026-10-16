# SR-001 — Revisão metodológica independente do pré-registro PR #191

**Data:** 2026-10-16  
**Natureza:** REVIEW DOCUMENTAL / READ-ONLY; nenhuma validação executada.  
**Objeto:** PR #191, pré-registro de validação independente B2/FM-1, associado à Issue #158.  
**Decisão:** REVISIONS REQUESTED (recomendação metodológica, não revisão formal do GitHub). O documento deve permanecer DRAFT até deliberação humana.

## 1. Evidência sob revisão
- T02 FROZEN: 40 pares (20 positivos / 20 hard negatives).
- B0: TP=19, FP=17, TN=3, FN=1.
- B2 pós-hoc: TP=19, FP=13, TN=7, FN=1.
- Delta empírico pareado na T02: FP=-4; TP=0. Estes resultados **não** são validação out-of-sample.
- A correção de interpretação de `M10X1.25X40` na PR #189 preserva `UNKNOWN` quando o papel físico não é identificável com segurança.

## 2. Lacunas a resolver antes de congelar protocolo e amostra
1. **Unidade independente:** definir se a unidade é o par, o SKU, uma família de SKUs ou um cluster de material/fornecedor; pares com SKUs compartilhados não devem ser presumidos independentes para intervalos ou testes.
2. **Plano amostral:** explicitar população-alvo, famílias e estratos, distribuição de positivos/negativos, elegibilidade, método de seleção e tamanho amostral justificado *antes* de observar resultados; não transformar a razão 20/20 artificial da T02 em prevalência industrial.
3. **Vazamento de informação:** formalizar exclusão de pares duplicados/variantes próximas da T02 e casos usados em desenho/debug de B1/B2; separar construtor de rótulos e responsável por código; congelar hashes antes de revelar rótulos.
4. **Definição operacional de UNKNOWN:** especificar como `UNKNOWN` se propaga à decisão e ao relatório; contabilizar cobertura de tipagem por estrato; proibir contabilizá-lo silenciosamente como concordância, discordância ou descarte favorável.
5. **Critério primário e gate de recall:** distinguir `TP_B2 >= TP_B0` na amostra pareada do recall end-to-end absoluto; pré-especificar o tratamento de perdas do blocking e as condições de falha. Zero perda observada de TP em amostra finita não prova risco populacional zero.
6. **Comparações tipadas:** identificar convenções industriais por classe (diâmetro nominal, passo, comprimento, espessura), conversões exatas toleradas, tolerâncias e regras para geometria de múltiplos componentes. Não comparar números por posição de token.
7. **Análise estatística:** relatar tabela de discordância pareada B0/B2, denominadores, incerteza e clusters; deixar testes/inferência ajustados ao desenho e explicitar limitação de poder. Precision depende da prevalência dos casos.
8. **Gate separado P-07:** migração/integridade de 100 mil SKUs requer plano próprio de transferência, reconciliação, memória/latência e dataset autorizado; não declarar escala validada a partir de T02/B2.

## 3. Ordem sugerida de decisão
- Primeiro: revisar e aceitar o contrato físico tipado e semântica de `UNKNOWN`.
- Segundo: fechar amostragem, independência, segregação de papéis e métricas/gates antes de qualquer coleta.
- Terceiro: registrar um HUMAN GO específico, se concedido, para materialização e execução confirmatória.
- Qualquer mudança após freeze deve constar como estudo exploratório novo, sem reaproveitar alegação confirmatória.

## 4. Limites desta sessão
Este review **não** altera `src/agent_lab/`, `tests/`, GT, T02 FROZEN, manifesto, parâmetros B2, baseline 1194, suíte experimental ou KPI. **Não** autoriza execução B2 adicional, T03, produção, nem migração 100 mil SKUs. A PR #191 deve permanecer DRAFT até revisão humana explícita.
