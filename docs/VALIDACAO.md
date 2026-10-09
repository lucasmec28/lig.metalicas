# Validação da versão 0.1.0

A validação combina testes numéricos, regras de domínio, estados de resultado, operação da interface e revisão visual das memórias. Ainda não é reprodução integral ou auditoria independente de todos os modelos de ligação.

## Comparações com fontes

| Parcela | Calculado | Referência | Unidade |
|---|---:|---:|---|
| Carini, força crítica no parafuso com e = a/2 | 31,8198 | 31,82 | kN |
| Carini, ruptura da chapa ao corte | 123,088 | 123,0 | kN |
| AISC II.A-17B, interação de escoamento | 0,181395 | 0,181 | — |
| AISC II.A-17B, interação de ruptura | 0,500497 | 0,500 | — |
| AISC II.A-19B, interação de ruptura | 0,591639 | 0,592 | — |
| AISC II.A-19B, momento nominal da chapa | 2.109,375 | 2.110 | kip·in |
| AISC II.A-19B, bloco U da chapa | 541,970 | 542 | kip |

As sete comparações atendem às tolerâncias de arredondamento registradas em `benchmarks.json` e no código. Os testes das interações usam resistências fornecidas pelos exemplos e verificam a expressão combinada; não recalculam todos os componentes desses exemplos. As comparações em unidades americanas permanecem nessas unidades para não misturar coeficientes normativos.

A conferência original de Carini preserva a geometria e as hipóteses históricas apenas no teste. O exemplo interativo foi alterado de chapa 6,3 mm para 5/16 polegada, de folga 10 mm para 15 mm e de e = a/2 para e = a. Também usa coeficientes e materiais da NBR atual. Não é esperado que seus resultados finais sejam idênticos aos da anotação original.

## Testes automatizados

Resultado final: **42 testes aprovados**. A suíte verifica:

- Equilíbrio de N, V e M no grupo elástico de parafusos.
- Conversão kgf/N, preservação das ações originais e aplicação separada do mínimo normativo.
- Limites de passo e geometria, interferência entre mesas, efeito geométrico dos recortes.
- Bloqueio de entradas inválidas, não finitas, compressão e dados fora do domínio.
- Persistência por JSON e equivalência de resultados após reabertura.
- Interações, mudanças de sinal e escala das ações, ramos de resistência da chapa.
- Proibição de aprovação quando há estados não implementados ou ações nulas.
- Restrições de produto/material e identificação explícita da desativação do mínimo normativo.
- Troca de exemplo e material pela tela, geração de Word, importação e retirada do download desatualizado após alterar entradas.
- Texto de conclusão do relatório reprovado: não pode afirmar que todas as verificações atendem.

Comando reproduzível: `python -m pytest -q`. Ambiente: Python 3.12; versões das dependências fixadas em `requirements.txt`.

## Relatórios e interface

Os dois relatórios compactos foram renderizados e suas oito páginas foram inspecionadas visualmente. Foram conferidos desenho proporcional, cotas, equações editáveis, tabelas, quebras de página, identificação da LRO e link do LinkedIn.

A interface foi exercitada por Streamlit AppTest. A tentativa de captura visual em navegador local foi bloqueada pelas restrições de execução do ambiente; portanto a revisão visual final da página no navegador/hospedagem permanece pendente. Não se afirma teste de publicação em Streamlit Community Cloud.

## Resultados dos exemplos entregues

| Entrada | Estado esperado |
|---|---|
| W360×39 → W410×38,8, 11 kN + 2 kN | Verificação incompleta: contenção e alma do apoio sob tração fora do plano. |
| Carini adaptado, 45 kN de corte | Atende ao escopo local verificado; índice determinante aproximado 0,902. |
| Viga → mesa de pilar W, 11 kN + 2 kN | Verificação incompleta enquanto a contenção longitudinal não for confirmada. |

Não foi concluída a validação integral do nó para os dois detalhes reais de projeto. As pendências técnicas são identificadas em `METODOLOGIA.md` e reaparecem na tela e na memória correspondente.

## Próximos critérios de liberação técnica

1. Reproduzir integralmente pelo menos um exemplo convencional e um exemplo com N + V, separando AISC original e adaptação brasileira.
2. Concluir a resistência da alma da viga de apoio à tração fora do plano.
3. Incluir a solda mesa–alma do pilar soldado como dado verificável.
4. Validar recortes e configurações fora da dispensa simplificada de ductilidade.
5. Rever o catálogo e as hipóteses de fabricação aplicáveis ao projeto.
6. Revisão técnica independente dos critérios complementares e da memória.

Depois dessas etapas, ampliar para cantoneiras simples e duplas mantendo a mesma separação entre método, domínio, catálogo, desenho e relatório.
