# LRO Ligações — versão 0.1.0

Desenvolvido por LRO Soluções de engenharia LTDA.

[Contato: Lucas Oliveira no LinkedIn](https://www.linkedin.com/in/lucas-oliveira-722723149/?isSelfProfile=true)

Primeira versão funcional para **pré-verificação de ligações single plate** em perfis I. A versão possui limites técnicos explícitos; consulte `docs/METODOLOGIA.md` antes de utilizar seus resultados em projeto.

## Começar

O pacote contém o aplicativo completo, duas entradas de exemplo, dois relatórios Word, catálogo de perfis, metodologia e testes. Não contém os PDFs e as planilhas de terceiros utilizados como referências.

### Usar no computador

Instale Python 3.12. Extraia o ZIP, abra um terminal na pasta que contém `app.py` e execute:

```bash
python -m venv .venv
```

Ative o ambiente:

```powershell
# Windows PowerShell
.venv\Scripts\Activate.ps1
```

```bash
# macOS ou Linux
source .venv/bin/activate
```

Instale e inicie:

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

O terminal informa o endereço local para abrir no navegador. Não é necessário Word instalado para gerar o DOCX. O aplicativo funciona sem APIs pagas ou serviços de IA.

### Disponibilizar por um link Streamlit

1. Coloque o conteúdo extraído em um repositório GitHub destinado ao aplicativo. `app.py`, `requirements.txt`, `lro/`, `data/` e `.streamlit/` devem permanecer juntos na raiz.
2. No Streamlit Community Cloud, crie um aplicativo e selecione esse repositório, a branch e o arquivo principal `app.py`.
3. Nas configurações avançadas, selecione Python 3.12, versão usada na validação deste pacote, se disponível.
4. Publique e confira o carregamento dos exemplos e a exportação Word no endereço gerado.

Instruções oficiais: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy

**Este pacote ainda não corresponde a um aplicativo publicado.** A publicação exige um repositório e a conta de hospedagem de destino. O app não inclui autenticação própria; configure o acesso na hospedagem conforme o uso pretendido.

## Fluxo de uso

1. Escolha ligação na alma de viga ou na mesa do pilar.
2. Selecione os perfis e informe cortante e tração já majorados, em kgf.
3. Ajuste parafusos, chapa, solda e cotas. As vistas proporcionais são atualizadas junto com o cálculo.
4. Confira os alertas e as abas de verificações e referências.
5. Gere a memória compacta ou detalhada em Word. Salve também o projeto em JSON para reabrir as mesmas entradas.

A memória compacta apresenta todos os índices no resumo e desenvolve as verificações determinantes por componente. As equações no Word são editáveis. Um relatório gerado deixa de ser oferecido para download quando as entradas são alteradas.

## Exemplos

- **Seu caso W360 → W410:** V = 11 kN e N = 2 kN, preservados como entradas. Inclui conferência independente do mínimo normativo de 45 kN. Resultado condicionado, entre outros pontos, à flexão fora do plano da alma do apoio sob N.
- **Carini adaptado:** exemplo didático W310×21 → W150×22,5(H), V = 45 kN. Chapa, folga e excentricidade foram alteradas e estão identificadas; não é uma reprodução integral do exemplo original.
- **Viga na mesa de pilar W:** alternativa laminada para explorar a outra geometria. A indicação do usuário “CVS 600×281” não foi substituída automaticamente: no catálogo fornecido, a designação existente é **CS 600×281**. O perfil definitivo pode ser escolhido ou informado como seção personalizada.

## Estados de resultado

| Estado | Significado |
|---|---|
| Geometria inválida | Dados ou interferências impedem o cálculo de resistência. |
| Não atende | Pelo menos uma verificação implementada excede o limite. Pode também haver pendências. |
| Verificação incompleta | As verificações calculadas atendem, mas há estados limite ou condições sem confirmação. |
| Atende ao escopo verificado | As verificações locais implementadas atendem às hipóteses informadas; não equivale à aprovação global da estrutura. |

## Conteúdo técnico e desenvolvimento

- [Metodologia e pendências](docs/METODOLOGIA.md)
- [Validação e referências](docs/VALIDACAO.md)
- `docs/fontes.json`: inventário das fontes selecionadas, edições e identificação por hash.
- `lro/models.py`: unidades, dados e objetos de entrada/saída.
- `lro/engine.py`: cálculo e regras geométricas independentes da tela.
- `lro/drawing.py`: desenho derivado da mesma geometria.
- `lro/report.py`: memória Word derivada dos resultados do motor.
- `data/profiles.json`: 560 seções catalogadas com indicação da origem.

Para executar os testes:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

A próxima família prevista é cantoneira simples e dupla. Antes de ampliar o catálogo de ligações, a prioridade técnica é concluir as pendências dos dois casos de single plate do projeto e ampliar a comparação integral com exemplos resolvidos.
