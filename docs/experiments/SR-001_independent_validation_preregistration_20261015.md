# SR-001 — Pré-registro de validação independente pós-B2 (DRAFT)

**Data:** 2026-10-15  
**Estado:** PROPOSED / NOT EXECUTED  
**Issue:** #158 (experimental, non-functional, weight=0)  
**Natureza:** contrato metodológico documental; não constitui HUMAN GO para amostragem, execução, T03 ou promoção.

## 1. Evidências e limites de partida

- A Tranche 02 (T02) está FROZEN: 40 pares, sendo 20 positivos e 20 hard negatives; seus dados, manifesto, Ground Truth e observações são históricos imutáveis.
- Referência B0: TP=19, FP=17, TN=3, FN=1; precision=52,78%; recall=95%.
- Intervenção isolada B2/FM-1 na T02: TP=19, FP=13, TN=7, FN=1; precision=59,375%; recall=95%; F1≈0,73077.
- A sonda B2 foi construída após exame dos erros da T02; portanto seus resultados são **post-hoc**, não evidência out-of-sample.
- A errata #189 reconhece que `M10X1.25X40` representa diâmetro, passo e comprimento. Atributos ambiguamente interpretáveis devem permanecer `UNKNOWN`, não ser convertidos em conflito dimensional.
- Nem o baseline A nem a observação T02 comprovam execução em 100 mil SKUs.

## 2. Pergunta científica

Uma regra conservadora de divergência dimensional, previamente congelada e avaliada sem acesso às respostas, reduz falsos positivos em materiais distintos **sem degradar o recall dos pares positivos**, em dados independentes da T02?

## 3. Fases e controles de cegamento (proposta)

1. **Contrato de atributos antes dos casos:** especificar slots dimensionais tipados por categoria, unidades, conversões permitidas, papel físico de cada medida e casos explicitamente incomparáveis.
2. **Protocolo e critérios antes da coleta:** fixar fontes permitidas, elegibilidade, esquema, distribuição-alvo, plano de amostragem, prevenção de duplicidade entre T02 e nova amostra, hashes e versionamento.
3. **Separação de papéis:** um responsável constrói/valida Ground Truth, outro congela a sonda e aplica o avaliador; quem modifica a regra não poderá observar o rótulo dos novos casos antes do freeze.
4. **Congelamento:** criar manifesto de inputs, hashes SHA-256, versão de código e registro de exclusões; qualquer mudança posterior gera uma execução nova, identificada e explicitamente não confirmatória.
5. **Execução única confirmatória autorizada:** comparar B0 e B2 sobre os mesmos pares, com matriz de confusão e relatório por família/estrato, observando também UNKNOWN e perdas no candidate selection. **Esta etapa depende de HUMAN GO específico**.
6. **Custódia e análise:** preservar observação original, trilha por caso, incerteza estatística, desvios de protocolo e limitações; não reutilizar resultado para tuning e simultaneamente alegar validação.

## 4. Contrato dimensional tipado — proposta inicial para revisão

| Campo lógico | Exemplo | Limitação |
| --- | --- | --- |
| `quantity_type` | `diameter`, `length`, `thread_pitch`, `thickness` | Tipos diferentes jamais comparados numericamente por mera posição de token |
| `unit` | `mm`, `inch` | Comparar apenas após conversão determinística explicitamente aceita |
| `nominal_value` | valor numérico analisável | Ausência, intervalo ou formato ambíguo ⇒ UNKNOWN |
| `feature_role` | `thread_major_diameter`, `thread_pitch`, `overall_length` | Papel físico depende de convenção documentada e categoria |
| `source_span` | segmento original da descrição | Proveniência rastreável; sem inferência silenciosa |
| `parse_status` | `TYPED`, `UNKNOWN` | UNKNOWN não equivale a igualdade nem discordância |

**Triestado proposto:** `DISAGREEMENT` somente se os mesmos slots físicos são comparáveis e materialmente conflitantes; `NO_DISAGREEMENT` quando comparáveis sem conflito; `UNKNOWN` em casos insuficientes, sem tipagem ou semanticamente ambíguos. O tratamento final ainda exige especificação e aprovação; não alterar a lógica implementada da B2 aqui.

## 5. Métricas e proteção contra conclusões indevidas

- Primárias: variação pareada de FP e TP, recall de positivos end-to-end e número de decisões UNKNOWN.
- Secundárias: precision, F1, TN/FN, recall condicionado ao blocking, cobertura por categoria, taxa de ambiguidades, tempo de inferência da sonda.
- Relatar contagens brutas, denominadores, intervalos de confiança adequados ao tamanho amostral e desacordos pareados; evitar significância artificial por pares correlacionados e não alegar representatividade industrial sem desenho amostral.
- **Gate de segurança proposto, sujeito a HUMAN GO:** zero TP adicionalmente perdido pela B2 contra B0 no conjunto cego; qualquer violação impede elegibilidade e requer análise, sem ajuste retroativo do limiar.
- Tamanho amostral, seleção de estratos e limiares de aceitação ainda **não aprovados**; não declarar poder estatístico ou generalização.

## 6. Frente paralela de 100 mil SKUs (P-07), sem benchmark autorizado

- Separar migração/ingestão de uma base industrial de 100 mil SKUs de diagnóstico quadrático catalog-wide e de análise incremental.
- Inventariar schema da origem/destino, chaves estáveis, campos obrigatórios, granularidade, unidades, cardinalidades, índices, qualidade e auditoria de reconciliação.
- Planejar testes de integridade da transferência: contagem origem/destino, unicidade, hashes por lote, nulos, tipagem, codificação, rollback e idempotência; mascarar dados sensíveis se houver fonte real.
- Medir posteriormente cargas progressivas, memória RSS, latência, throughput e comportamento incremental somente sob protocolo e autorização próprios.
- **Nenhuma capacidade para 100 mil SKUs está comprovada nesta etapa**.

## 7. Critérios de saída deste documento

Este DRAFT está concluído como **pré-registro de desenho** apenas quando revisto quanto à semântica dimensional, dependência do Ground Truth, segregação entre criação e avaliação, plano amostral, segurança de recall e alinhamento ao Compass. Não gera autorização de T03, novas execuções, mudanças em `src/agent_lab/`, `tests/`, GT, manifestos FROZEN ou KPI.

**Próxima decisão humana:** aprovar/revisar/rejeitar este pré-registro antes de materializar uma nova amostra.