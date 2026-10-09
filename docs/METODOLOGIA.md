# Metodologia e domínio — LRO Ligações 0.1.0

## Referencial e estratégia

A base brasileira é a ABNT NBR 8800:2024, versão corrigida de 2025 fornecida pelo usuário. Carini e AISC complementam procedimentos de single plate e fornecem exemplos para conferência. Resistências tabuladas em LRFD não são convertidas em bloco para o sistema brasileiro: cada expressão, coeficiente e hipótese é identificado no motor e na memória.

O desenvolvimento separa cálculo, catálogo, desenho e relatório. Tela, desenho e Word usam o mesmo objeto de ligação. A versão não depende de interpretações de IA durante o uso: o cálculo é determinístico, inspecionável e testável.

Esta é uma versão de pré-verificação com procedimentos complementares ainda sujeitos à revisão técnica independente. “Atende ao escopo verificado” descreve somente as verificações locais implementadas. Não significa verificação integral do nó, da estrutura ou de todos os critérios possíveis.

## Domínio geométrico e ações

- Uma viga apoiada em perfil I, chegada a 90°; apoio na alma de outra viga ou na mesa de pilar, alinhado à alma do pilar.
- Uma chapa soldada ao apoio por dois filetes e parafusada à alma apoiada; uma coluna vertical com 2–12 parafusos.
- Parafusos por contato, furos padrão, corte simples e soldas executadas em oficina.
- Cortante no plano e força axial de tração. Compressão, momento externo de engaste e torção aplicada não são aceitos como ações do modelo.
- Um caso de esforços já majorados. Conversão exata: 1 kgf = 9,80665 N. O motor usa N, mm e MPa; a tela e os resultados principais usam kgf, kgf·m e mm.
- O passo, as bordas e as dimensões são livres dentro das verificações. Valores usuais de fabricação não substituem condições normativas.
- Chapas e parafusos têm seleção nominal em polegadas; também é possível informar a espessura real da chapa.

### Mínimo normativo

O item 6.1.5.2 da NBR prevê resistência mínima de 45 kN para ligações, com as exceções expressas nesse item. Para os casos viga–viga e viga–pilar do escopo, a V1 cria uma conferência adicional se a resultante informada for menor que 45 kN, preservando a direção e o sentido de N e V. Essa aplicação à resultante é uma interpretação operacional explicitada, a ser confirmada na revisão técnica do projeto.

As ações originais continuam disponíveis em `Result.actual`; não há novo coeficiente de majoração aplicado às entradas. `Result.checks` contém a conferência governante, identificada como entrada ou mínimo normativo. Desativar essa conferência é permitido para comparação, mas impede conclusão de atendimento normativo. Requisitos de integridade estrutural e definição das combinações permanecem na análise global.

## Excentricidades e resistências

Adota-se sempre a excentricidade completa `e = a`, da face do apoio à linha de parafusos, inclusive para corte puro. Não se adota automaticamente a redução convencional `a/2`. Com tração referida ao eixo da viga, acrescenta-se a envoltória `|N·eN|`, sendo `eN` o desnível entre esse eixo e o centro do grupo. Isso também explica diferenças em relação a exemplos históricos.

O grupo de parafusos é calculado elasticamente, combinando as componentes de N/n, V/n e momento. É conferido o equilíbrio das forças e do momento nos testes. Não se usam coeficientes do centro instantâneo como se fossem resultados do método elástico.

| Componente | Verificações e bases |
|---|---|
| Parafusos | Corte simples pela NBR 6.3.3.2; coeficientes 0,45/0,56 conforme posição da rosca; resistências do Anexo A. A307 permanece com pendência específica de ductilidade. |
| Furos | Contato e rasgamento segundo 6.3.3.3(a), com limite de deformação. Menor distância livre pertinente adotada conservadoramente para a resultante de cada parafuso. |
| Chapa | Escoamento e ruptura por N e V; ruptura por flexão com módulo plástico líquido; flexão e instabilidade F11 do AISC, com resistência nominal e γa1 explícitos; interação N–V–M do Manual AISC, equações 12-2/12-3. |
| Blocos de ruptura | Caminhos L e U da chapa e U da alma apoiada; interação quadrática de N e V no caminho L, conforme complemento AISC. |
| Alma apoiada | Corte local, tração usando apenas a alma, bloco U e mecanismo de flexão/corte apresentado por Carini/SCI. A interação linear adicional com N é uma adaptação de implementação, não uma equação atribuída à NBR ou a Carini. |
| Soldas | Dois filetes por análise elástica de linhas; força direta e momento completo; resistência da garganta sem aumento direcional; metal-base da chapa; limites geométricos e requisito complementar de desenvolvimento da chapa. |
| Apoio | Corte/ruptura local junto à solda e hierarquia de espessuras contra punção do roteiro Carini/SCI. No pilar, escoamento local da alma por N e flexão local da mesa quando aplicável, com hipóteses de extremidade conservadoras. |

As equações de interação têm o expoente aplicado ao colchete inteiro: `[n/2+m]²+v²` ou `[n+8m/9]²+v²`. Seu índice não é um multiplicador linear de carga.

Para a instabilidade da chapa, a V1 usa `Lb=a` e `Cb=1,84`, hipótese dos exemplos de referência. A contenção longitudinal da viga deve corresponder ao detalhe real. Sem sua confirmação nos casos que a exigem, o app mantém pendência; computar a parcela `N(tp+tw)/2` não substitui a avaliação tridimensional do conjunto.

## Geometria e interferências

São conferidos: furos padrão, passo mínimo e máximo, bordas mínimas e máximas, sobreposição de furos e extremidades, região livre da alma, concordâncias, altura da chapa, filetes, envelope ajustável de porca/ferramenta, encontro com mesas do apoio, posição e dimensões de recortes.

A categoria de espaçamento máximo é para elementos protegidos/pintados ou não sujeitos à corrosão. A versão não cobre automaticamente o detalhamento de aço sem proteção exposto à corrosão. O envelope de montagem inicial é ilustrativo; deve ser ajustado à ferramenta, arruela e porca reais.

As exceções normativas de borda reduzida não são aprovadas automaticamente apenas por atender à pressão de contato. Fora da condição simplificada de ductilidade da single plate, é requerida conferência específica do grupo sob momento puro e da espessura da chapa.

## Materiais e catálogo

Há dez opções de aço com valores mínimos e limites de produto/espessura cadastrados a partir do Anexo A da NBR. Produtos exclusivos de perfis laminados não são aceitos silenciosamente como chapas de perfis soldados. Valores de certificado que precisem de avaliação particular não são inferidos.

O catálogo inicial contém 99 W, 8 HP, 144 CS, 135 CVS e 174 VS: 560 seções. Foi extraído das abas de perfis da planilha do curso fornecida pelo usuário; cada registro preserva a origem. As seções dos casos prioritários foram comparadas com os catálogos disponíveis. Não foi realizada auditoria independente de todas as 560 seções. A seleção da seção deve ser conferida com o produto especificado, inclusive raios/concordâncias e dimensões de fabricação.

Cinco designações VS apareciam duas vezes na origem, com geometrias diferentes. As dez entradas correspondentes foram mantidas como variantes, identificadas por bf e tf no nome de seleção, sem sobreposição silenciosa de registros.

O perfil 600×281 identificado nas tabelas é **CS**, com d = 600 mm, bf = 600 mm, tw = 16 mm e tf = 22,4 mm. A designação “CVS 600×281” não foi criada nem substituída automaticamente. O perfil real e sua solda mesa–alma ainda devem ser confirmados para o caso do projeto.

## Pendências que impedem uma conclusão completa

1. **Viga W360×39 na alma da W410×38,8, com N = 2 kN:** implementar e validar a flexão fora do plano da alma de apoio sob tração. Corte local e hierarquia contra punção não encerram essa verificação. O exemplo AISC II.A-19B trata de outra orientação de apoio; sua expressão não deve ser transplantada sem adaptação justificada.
2. **Viga na mesa de pilar soldado:** falta a dimensão/especificação da solda mesa–alma da própria coluna para conferir a transferência de força localizada. A geometria exata da seção deve ser confirmada.
3. **Recortes:** já aparecem no desenho e nas interferências, mas faltam resistência à flexão e estabilidade do trecho recortado, inclusive diferenças entre recorte simples e duplo.
4. **Ausência de contenção longitudinal:** falta concluir a estabilidade e os efeitos tridimensionais da ligação nas configurações sinalizadas.
5. **Fora da dispensa de ductilidade:** falta implementar a verificação completa de espessura máxima e resistência nominal do grupo sob momento puro.
6. **Almas esbeltas, pega longa e materiais fora da faixa validada de desenvolvimento da solda:** permanecem pendentes, sem extrapolação silenciosa.

Também ficam fora desta versão: fadiga, atrito, vibração/ciclos, sismo, incêndio, compressão axial, momento de engaste aplicado, enrijecedores, segunda viga no nó, chumbadores e placas de base. São ampliações de produto, não campos fictícios na interface.

## Leitura e utilização das novas fontes

- **P901-23W:** fonte central para procedimentos e exemplos. Exame focado nas ligações simples, em particular II.A-17B, II.A-18 e II.A-19B. O último mostra por que conferir o apoio é indispensável: a resistência da alma da coluna à tração localizada é insuficiente no exemplo, apesar de outros componentes atenderem.
- **P902-23W:** tabelas suplementares. As tabelas 10-A/10-B de punção de paredes de perfis tubulares não se aplicam diretamente às almas de perfis I desta versão.
- **726569040-1-2-3-Simple-Shear-Connections-AISC:** recorte de exemplos v15, usado para comparação histórica; os exemplos correspondentes v16 do P901 têm prioridade de edição.
- **790747119-AISC-Steel-Design-Examples-v16-0:** subconjunto didático de 180 páginas, não o Companion completo.
- **62_01_053_Err:** errata de 2025 de artigo sobre torção de elementos retangulares, não errata geral do Manual/Companion.
- **Design of All-Bolted Extended Double Angle, Single Angle, and Tee Shear Connections:** relatório de pesquisa de 2005 de Green, Sputo e Higgins, base de estudos para a próxima família. Exigirá compatibilização com a NBR atual.
- **AISC Part 7, 13ª edição:** referência histórica sobre parafusos; não define os coeficientes atuais adotados no app.

A errata oficial do Companion v16, datada de 02/06/2025, foi localizada no índice público da AISC. As correções indexadas referem-se a IIA-149, IIA-150 e IIA-288/289; não aos exemplos usados nos sete testes pontuais desta versão. A conferência das erratas deve ser refeita quando uma nova ligação ou expressão for incorporada.

Fontes oficiais para controle de edição:

- https://www.aisc.org/aisc/publications/revisions-and-errata/
- https://www.aisc.org/globalassets/aisc/publications/revisions-and-errata/manual-companion-v16.0_vol-1-errata.pdf
- https://www.aisc.org/aisc/publications/steel-construction-manual/manual-companion-for-16th-edition/

A leitura desta etapa foi orientada pelos procedimentos pertinentes à V1. Não representa auditoria integral de todas as páginas, planilhas, normas ou desenhos enviados.
