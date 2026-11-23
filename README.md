# Software educacional de compiladores

Ferramenta web para apoiar o ensino de **compiladores**. O estudante escreve (ou escolhe) um programa em um
**subconjunto de Python** e acompanha as etapas da compilação: os **tokens** reconhecidos pela análise léxica, a
**árvore sintática abstrata (AST)** montada pela análise sintática e os **erros** de cada etapa, com linha, coluna e
explicação.

| Etapa | Situação | Conteúdo |
|---|---|---|
| 1 | ✅ | Estrutura de pastas, Docker Compose, "Hello, World!" |
| 2 | ✅ | Comunicação frontend ↔ backend e validação de entrada |
| 3 | ✅ | **Análise léxica** (scanner), tabela de tokens, erros léxicos |
| 4 | ✅ | **Análise sintática** (parser), AST, erros sintáticos |
| 5 | ⏳ | Análise semântica e tabela de símbolos |

---

## Sumário

1. [Linguagem foco e justificativa](#1-linguagem-foco-e-justificativa)
2. [Estrutura do projeto](#2-estrutura-do-projeto)
3. [Como executar](#3-como-executar)
4. [Como executar os testes](#4-como-executar-os-testes)
5. [Escopo léxico](#5-escopo-léxico-análise-léxica)
6. [Escopo sintático e gramática](#6-escopo-sintático-e-gramática-análise-sintática)
7. [Contrato de comunicação (API)](#7-contrato-de-comunicação-api)
8. [Interface](#8-interface)
9. [Decisões de projeto](#9-decisões-de-projeto)
10. [Limitações conhecidas](#10-limitações-conhecidas)
11. [Documentação complementar](#11-documentação-complementar)
12. [Assistente de IA com Ollama (diferencial opcional)](#12-assistente-de-ia-com-ollama-diferencial-opcional)

---

## 1. Linguagem foco e justificativa

**Python 3 (subconjunto).** A escolha se apoia em três razões:

1. **Simplicidade sintática:** o estudante concentra a atenção nos conceitos de compilação, e não na complexidade da
   linguagem analisada.
2. **Familiaridade do público-alvo:** Python é a linguagem introdutória mais usada nos cursos de Computação, então as
   construções analisadas já são conhecidas.
3. **Indentação significativa:** blocos definidos por recuo geram exemplos léxicos e sintáticos interessantes, pouco
   comuns nas linguagens didáticas inventadas.

Não se pretende analisar Python inteiro: apenas as construções listadas nas seções 5 e 6.

---

## 2. Estrutura do projeto

```
software-educacional-compiladores/
├── compose.yaml                 # orquestra os contêineres frontend e backend
├── README.md
├── backend/                     # Python 3.11 + Flask (porta 5000)
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app.py                   # rota POST /api/analisar: validação e orquestração
│   ├── analisador/
│   │   ├── __init__.py
│   │   ├── lexico.py            # scanner + tokens estruturais de indentação
│   │   └── sintatico.py         # parser descendente recursivo + AST
│   └── tests/
│       ├── test_scanner.py      # testes do scanner (análise léxica)
│       ├── test_parser.py       # testes do parser (casos CT-xx)
│       └── test_api_etapa4.py   # testes do endpoint e da validação de entrada
├── tests_interface/
│   └── test_interface.py        # testes da interface no navegador (Playwright)
├── frontend/                    # HTML/CSS/JS puro servido por nginx (porta 8080)
│   ├── Dockerfile
│   ├── nginx.conf
│   └── index.html
└── docs/
    ├── gramatica.md             # gramática, estratégia do parser e estrutura da AST
    ├── casos-de-teste.md        # casos de teste planejados (válidos, inválidos, borda)
    ├── registro_testes.md       # registro das execuções dos testes
    ├── fluxograma.md            # fluxograma e arquitetura (+ .png, .pdf, .dot)
    └── ...
```

---

## 3. Como executar

### Pré-requisitos

| Ferramenta | Versão mínima | Como verificar |
|---|---|---|
| Git | 2.30+ | `git --version` |
| Docker Desktop | 24+ | `docker --version` |
| Docker Compose | v2+ | `docker compose version` |

**Windows:** o Docker Desktop precisa do **WSL 2** com uma distribuição Linux. Para instalar, no PowerShell como
administrador:

```powershell
wsl --install -d Ubuntu
```

### Passo a passo

```bash
git clone https://github.com/Adailtonvieira/software-educacional-compiladores.git
cd software-educacional-compiladores
docker compose up -d --build
```

- Interface: <http://localhost:8080>
- API: <http://localhost:5000/api/analisar>

Para encerrar:

```bash
docker compose down
```

Depois de atualizar o código (`git pull`), rode `docker compose up -d --build` de novo e recarregue a página com
**Ctrl+F5**.

---

## 4. Como executar os testes

Com os contêineres rodando:

```bash
docker compose exec -e PYTHONPATH=/app backend pytest tests/ -v
```

| Arquivo | O que testa |
|---|---|
| `tests/test_scanner.py` | Cada categoria léxica, prefixos de palavras reservadas, operadores de dois caracteres, comentários, linha e coluna, acúmulo de vários erros, número malformado, string não fechada, programa completo |
| `tests/test_parser.py` | Estrutura da AST (precedência, associatividade, blocos), erros sintáticos e casos de borda |
| `tests/test_api_etapa4.py` | Formato da resposta (`lexico`, `sintatico`), compatibilidade com a Etapa 3, rota `/api/gramatica`, validação de entrada (vazio, limite, não texto, sem JSON) |
| `tests_interface/test_interface.py` | Interface no navegador: árvore exibida, erros léxico × sintático, destaque de nó, expandir/recolher, filtro, exportação, passo a passo, consistência tabela × árvore, todos os exemplos, tela de celular |

**Testes da interface** (rodam fora do Docker, com a aplicação no ar):

```bash
pip install pytest playwright
playwright install chromium
pytest tests_interface -v
```

Os casos estão documentados em [`docs/casos-de-teste.md`](docs/casos-de-teste.md) e as execuções em
[`docs/registro_testes.md`](docs/registro_testes.md).

---

## 5. Escopo léxico (análise léxica)

O scanner (`backend/analisador/lexico.py`) percorre o código com **uma expressão regular mestre** formada por grupos
nomeados. As categorias são testadas **na ordem da tabela**, e vence a primeira que casa na posição atual. Espaços e
comentários são consumidos, mas não viram tokens.

| Ordem | Categoria (`tipo`) | Padrão | Exemplos válidos | Observações |
|---|---|---|---|---|
| 1 | `PALAVRA_RESERVADA` | `if else while for def return True False` (palavra inteira) | `if`, `True` | `iffy` e `true` são identificadores |
| 2 | *erro:* número malformado | dígitos seguidos de letra ou `_` | — | `12abc` gera **um** erro léxico |
| 3 | `IDENTIFICADOR` | letra ou `_`, seguida de letras, dígitos ou `_` | `x`, `_total`, `contador1` | — |
| 4 | `LITERAL_REAL` | dígitos `.` dígitos | `3.14`, `0.5` | testado antes do inteiro |
| 5 | `LITERAL_INTEIRO` | dígitos | `0`, `42` | — |
| 6 | `LITERAL_STRING` | texto entre `"` ou `'` na mesma linha | `"ok"`, `'a'`, `""` | `#` dentro de string não é comentário |
| 7 | *erro:* string não fechada | aspa sem fechamento até o fim da linha | — | gera um erro léxico |
| 8 | `OPERADOR` | `==` `!=` `<=` `>=` `+` `-` `*` `/` `=` `<` `>` | `>=` | os de dois caracteres formam **um** token |
| 9 | `DELIMITADOR` | `(` `)` `[` `]` `:` `,` | `:` | — |
| 10 | *(ignorado)* comentário | `#` até o fim da linha | `# nota` | não gera token |
| 11 | *(ignorado)* espaço | espaço, tabulação, `\r`, `\n` | — | só atualiza linha e coluna |
| 12 | *erro:* caractere não reconhecido | qualquer outro caractere | — | `@ $ ? ! & ; { } % π`... |

**Linha e coluna** começam em 1. A coluna conta caracteres (uma tabulação conta como 1).

**Erros léxicos.** O scanner **não para** no primeiro erro: registra o erro, avança e continua reconhecendo os tokens
seguintes, para que o estudante veja todos os problemas de uma vez. Mensagens possíveis:

| Situação | Mensagem |
|---|---|
| Caractere fora do alfabeto | `Caractere não reconhecido: '@'` |
| Número seguido de letra | `Literal numérico malformado: '12abc' (um nome não pode começar com dígito)` |
| Aspa sem fechamento na linha | `String não fechada: "abc (faltou a aspa final na mesma linha)` |

---

## 6. Escopo sintático e gramática (análise sintática)

A documentação completa (símbolo inicial, terminais × tokens, precedência, exemplos válidos e inválidos, estratégia
do parser, formato da AST e diferença entre AST e árvore de derivação) está em
[`docs/gramatica.md`](docs/gramatica.md). Resumo:

| Suportado | Não suportado nesta versão |
|---|---|
| Atribuição simples (`x = expr`) | `for`, `elif`, `and`/`or`/`not`, `in` |
| Expressões `+ - * /`, menos unário, parênteses | listas, tuplas, dicionários, índices `a[i]` |
| Comparações `== != < > <= >=` (uma por expressão) | comparações encadeadas (`a < b < c`) |
| `if` / `else`, `while`, blocos aninhados por indentação | classes, `import`, `try`, `lambda`, decoradores |
| `def nome(params):` e `return [expr]` | atribuição múltipla ou aumentada (`a, b = ...`, `+=`) |
| Chamadas de função (`print(x)`, `soma(1, 2)`) | comando na mesma linha do `:` (`if x: y = 1`) |
| Inteiros, reais, textos, `True`, `False`, comentários | quebra de linha dentro de parênteses; mistura de tab e espaço |

```ebnf
programa        = { comando } FIM_DE_ARQUIVO ;
comando         = comando_simples NOVA_LINHA | se | enquanto | funcao ;
comando_simples = retorno | atribuicao | expressao ;
atribuicao      = IDENTIFICADOR "=" expressao ;
retorno         = "return" [ expressao ] ;
se              = "if" expressao ":" bloco [ "else" ":" bloco ] ;
enquanto        = "while" expressao ":" bloco ;
funcao          = "def" IDENTIFICADOR "(" [ parametros ] ")" ":" bloco ;
parametros      = IDENTIFICADOR { "," IDENTIFICADOR } ;
bloco           = NOVA_LINHA INDENTACAO comando { comando } DEDENTACAO ;
expressao       = aritmetica [ op_relacional aritmetica ] ;
op_relacional   = "==" | "!=" | "<" | ">" | "<=" | ">=" ;
aritmetica      = termo { ( "+" | "-" ) termo } ;
termo           = fator { ( "*" | "/" ) fator } ;
fator           = ( "+" | "-" ) fator | atomo ;
atomo           = IDENTIFICADOR [ "(" [ argumentos ] ")" ]
                | LITERAL_INTEIRO | LITERAL_REAL | LITERAL_STRING
                | "True" | "False" | "(" expressao ")" ;
argumentos      = expressao { "," expressao } ;
```

**Precedência** (da menor para a maior): comparação (não associativa) < `+ -` (à esquerda) < `* /` (à esquerda) <
unário. Assim, `10 + 5 * 2` é `10 + (5 * 2)`, `20 - 5 - 3` é `(20 - 5) - 3` e `(10 + 5) * 2` multiplica a soma.

`NOVA_LINHA`, `INDENTACAO`, `DEDENTACAO` e `FIM_DE_ARQUIVO` são **tokens estruturais**, gerados a partir das linhas e
do recuo do código, como no Python. O parser os usa, mas eles **não aparecem** na lista `tokens` da resposta.

Tipos de nó da AST: `Programa`, `Atribuicao`, `Identificador`, `Se`, `Enquanto`, `Funcao`, `Parametros`, `Parametro`,
`Bloco` (valor `então`, `senão` ou `corpo`), `Retorno`, `Chamada`, `OperacaoBinaria`, `OperacaoRelacional`,
`OperacaoUnaria`, `LiteralInteiro`, `LiteralReal`, `LiteralTexto`, `LiteralLogico`.

---

## 7. Contrato de comunicação (API)

### Requisição

`POST /api/analisar` com `Content-Type: application/json`:

```json
{ "codigo": "x = 10" }
```

| Campo | Tipo | Regras |
|---|---|---|
| `codigo` | texto | obrigatório; não pode ser vazio nem só espaços; até 5000 caracteres |

### Respostas

| HTTP | Quando | Corpo |
|---|---|---|
| 200 | Entrada válida (mesmo que o código tenha erros léxicos ou sintáticos) | objeto de análise (abaixo) |
| 400 | Corpo não é JSON, `codigo` ausente ou não textual, vazio, só espaços ou acima de 5000 caracteres | `{"erro": "<mensagem>"}` |
| 500 | Falha inesperada no servidor (nenhum detalhe interno é exposto) | `{"erro": "Erro interno ao analisar o código..."}` |

**Objeto de análise:**

| Campo | Tipo | Descrição |
|---|---|---|
| `sucesso` | booleano | `true` se não houve nenhum erro |
| `tokens` | lista de Token | tokens na ordem do código (também quando há erros léxicos) |
| `erros` | lista de Erro | erros léxicos (todos) e, se o parser rodou, o primeiro erro sintático |
| `ast` | No ou `null` | árvore sintática; `null` se houve erro ou o parser não rodou |
| `etapas` | objeto | `lexica`: `ok`/`erro`; `sintatica`: `ok`/`erro`/`nao_executada`; `semantica`: `nao_implementada` |
| `lexico` | objeto | `sucesso`, `tokens`, `erros` (só os léxicos) |
| `sintatico` | objeto | `executado`, `sucesso`, `ast`, `erros` (só os sintáticos), `tokens_consumidos` (quantos tokens o parser consumiu) e `motivo` (por que não foi executado, ou `null`) |

**Token:** `tipo` (categoria da seção 5), `lexema` (texto original), `linha`, `coluna` (inteiros a partir de 1).

**Erro léxico:** `tipo` = `"ERRO_LEXICO"`, `lexema`, `linha`, `coluna`, `mensagem`.

**Erro sintático:** `tipo` = `"ERRO_SINTATICO"`, `lexema`, `linha`, `coluna`, `mensagem`, `esperado`, `encontrado`,
`dica` (texto ou `null`), `regra` (não terminal em análise), `producao` (texto da regra) e `abertura`
(`{linha, coluna}` da construção que ficou aberta, ou `null`).

**No (AST):** `tipo`, `valor` (texto ou `null`), `regra` (não terminal que reconheceu o nó), `linha` e `coluna` (token
que identifica o nó), `inicio` e `fim` (`{linha, coluna}` do trecho completo) e `filhos` (lista de No). Tipos de nó e
exemplos em [`docs/gramatica.md`](docs/gramatica.md#8-estrutura-da-ast).

**Gramática:** `GET /api/gramatica` devolve `simbolo_inicial`, `producoes`, `nao_terminais`, `terminais` (com a
categoria de token correspondente) e `categorias_lexicas`.

### Exemplos

Sucesso:

```json
{
  "sucesso": true,
  "tokens": [
    { "tipo": "IDENTIFICADOR", "lexema": "x", "linha": 1, "coluna": 1 },
    { "tipo": "OPERADOR", "lexema": "=", "linha": 1, "coluna": 3 },
    { "tipo": "LITERAL_INTEIRO", "lexema": "10", "linha": 1, "coluna": 5 }
  ],
  "erros": [],
  "ast": {
    "tipo": "Programa", "valor": null, "linha": 1, "coluna": 1,
    "filhos": [{
      "tipo": "Atribuicao", "valor": "=", "linha": 1, "coluna": 1,
      "filhos": [
        { "tipo": "Identificador", "valor": "x", "linha": 1, "coluna": 1, "filhos": [] },
        { "tipo": "LiteralInteiro", "valor": "10", "linha": 1, "coluna": 5, "filhos": [] }
      ]
    }]
  },
  "etapas": { "lexica": "ok", "sintatica": "ok", "semantica": "nao_implementada" }
}
```

Vários erros léxicos acumulados, para o código `a = @` / `b = $` em duas linhas (o parser não é executado):

```json
{
  "sucesso": false,
  "tokens": [
    { "tipo": "IDENTIFICADOR", "lexema": "a", "linha": 1, "coluna": 1 },
    { "tipo": "OPERADOR", "lexema": "=", "linha": 1, "coluna": 3 },
    { "tipo": "IDENTIFICADOR", "lexema": "b", "linha": 2, "coluna": 1 },
    { "tipo": "OPERADOR", "lexema": "=", "linha": 2, "coluna": 3 }
  ],
  "erros": [
    { "tipo": "ERRO_LEXICO", "lexema": "@", "linha": 1, "coluna": 5, "mensagem": "Caractere não reconhecido: '@'" },
    { "tipo": "ERRO_LEXICO", "lexema": "$", "linha": 2, "coluna": 5, "mensagem": "Caractere não reconhecido: '$'" }
  ],
  "ast": null,
  "etapas": { "lexica": "erro", "sintatica": "nao_executada", "semantica": "nao_implementada" }
}
```

Erro sintático (`if x > 0` sem `:`):

```json
{
  "tipo": "ERRO_SINTATICO", "lexema": "", "linha": 1, "coluna": 9,
  "esperado": "':' ao final do if", "encontrado": "fim da linha",
  "mensagem": "Esperado ':' ao final do if, mas foi encontrado fim da linha.",
  "dica": "Em Python, if, else, while e def terminam com ':'."
}
```

Entrada inválida (HTTP 400):

```json
{ "erro": "O código não pode estar vazio." }
```

A Etapa 4 **acrescentou** `ast`, `etapas`, `lexico` e `sintatico`; os campos da Etapa 3 (`sucesso`, `tokens`,
`erros`) continuam iguais. Os exemplos acima mostram só parte dos campos de cada nó.

---

## 8. Interface

1. **Código-fonte:** editor com 15 exemplos (válidos, com erro léxico e com erro sintático), contador de caracteres e
   atalho **Ctrl+Enter**. A tecla Tab insere 4 espaços; **Esc** seguido de **Tab** sai do editor.
2. **Etapas da compilação:** situação de cada etapa (concluída, com erros, não executada ou não implementada) e os erros
   léxicos e sintáticos em caixas separadas, com posição clicável, esperado, encontrado e dica.
3. **Tokens (análise léxica):**
   - **código classificado**, com cada trecho colorido pela categoria, erros sublinhados e comentários em itálico;
   - **legenda** com a quantidade de tokens por categoria e a explicação de cada uma (passe o mouse);
   - **tabela** com tipo, lexema, linha e coluna;
   - explicação de como o scanner decide a categoria e por que continua após um erro.
4. **AST:**
   - visão hierárquica (expandir e recolher tudo) e visão gráfica com **zoom** (−, +, 100%, *Ajustar à tela* e
     Ctrl + roda do mouse); ao abrir, a árvore gráfica é ajustada para caber inteira no quadro;
   - cada nó tem cor **e** selo com letra e, na visão gráfica, forma própria: comando (C, retângulo), expressão
     (X, elipse), folha (F, pílula), estrutura (E, tracejado);
   - clicar em um nó mostra a **regra gramatical** que o reconheceu, seleciona o **trecho completo** no editor e
     destaca o token na tabela e no código classificado;
   - **filtro por tipo de nó** e **exportação da AST em JSON**;
   - **passo a passo:** mostra a ordem em que o parser concluiu cada nó, com a regra usada, avançando, voltando ou
     reproduzindo automaticamente;
   - explicação da diferença entre tokens, árvore de derivação e AST.

Acessibilidade: operação completa pelo teclado, árvore em texto legível por leitores de tela, botões A−/A+ para o
tamanho da fonte, foco visível e layout de uma coluna em telas estreitas.

---

## 9. Decisões de projeto

- **Scanner por expressão regular mestre:** cada categoria é uma regra legível, e a ordem da tabela resolve
  ambiguidades (palavra reservada antes de identificador, real antes de inteiro, `>=` antes de `>`).
- **Erros léxicos acumulados:** o scanner continua após um erro para mostrar todos de uma vez.
- **Parser descendente recursivo escrito à mão:** cada regra da gramática é um método, o que facilita a leitura e
  permite mensagens específicas por construção.
- **Parser não roda com erro léxico:** com tokens faltando, ele apontaria erros sintáticos que não correspondem ao
  problema real.
- **Parada no primeiro erro sintático**, sem recuperação, para evitar erros em cascata.
- **Parênteses não viram nós da AST:** a forma da árvore já representa a precedência.
- **Gramática como fonte única:** o dicionário `GRAMATICA` alimenta o parser, as mensagens de erro, os nós da AST e a
  rota `/api/gramatica`, evitando que documentação e código divirjam.
- **Limites de segurança:** 5000 caracteres por análise e 100 níveis de aninhamento. A interface insere conteúdo
  apenas como texto, nunca como HTML.

---

## 10. Limitações conhecidas

- A análise semântica e a tabela de símbolos ainda não existem (Etapa 5).
- O parser relata apenas o primeiro erro sintático.
- Strings não aceitam aspas escapadas (`\"`) nem aspas triplas; números não aceitam notação científica, hexadecimal ou
  `_` como separador.
- Em árvores muito grandes, o ajuste à tela deixa o texto pequeno; nesse caso use o zoom com rolagem ou a visão
  hierárquica com subárvores recolhidas.
- O passo a passo mostra a ordem de conclusão dos nós, não a derivação completa com as regras intermediárias.
- Interface testada no Chrome (desktop e largura de 390 px).

---

## 11. Documentação complementar

- [`docs/gramatica.md`](docs/gramatica.md): gramática, parser e AST.
- [`docs/casos-de-teste.md`](docs/casos-de-teste.md): casos de teste por categoria.
- [`docs/registro_testes.md`](docs/registro_testes.md): registro das execuções.
- [`docs/fluxograma.md`](docs/fluxograma.md): fluxograma do sistema e arquitetura.

---

## 12. Assistente de IA com Ollama (diferencial opcional)

### O que é e qual a função

O [Ollama](https://ollama.com) executa modelos de linguagem localmente e expõe uma API HTTP. O projeto usa o modelo
**Llama 3.2** (`llama3.2`, versão de 3B parâmetros) para **explicar** os resultados do compilador. A IA **não**
substitui o scanner nem o parser: o backend refaz a análise do código, envia ao modelo os tokens, a AST e os erros
reais e devolve a explicação à interface. Se o Ollama estiver fora do ar, só os botões de IA são afetados; a análise
continua funcionando.

```
ESTUDANTE → INTERFACE WEB → BACKEND ─┬─ SCANNER → PARSER → AST   (resultado oficial)
                                     └─ OLLAMA (llama3.2)         (explicação didática)
```

### Como foi incorporado ao Docker Compose

O serviço `ollama` (imagem `ollama/ollama:latest`) e o volume `ollama_data` foram acrescentados ao `compose.yaml`. O
backend recebe as variáveis abaixo e depende do serviço `ollama`. A porta 11434 **não** é publicada no host: só o
backend acessa o Ollama, pela rede interna do Compose.

| Variável | Padrão | Função |
|---|---|---|
| `OLLAMA_BASE_URL` | `http://ollama:11434` | endereço do Ollama visto pelo backend |
| `OLLAMA_MODELO` | `llama3.2` | modelo usado |
| `OLLAMA_TIMEOUT` | `300` | segundos sem receber **nenhum** pedaço da resposta antes de desistir |
| `OLLAMA_MAX_TOKENS` | `400` | tamanho máximo da resposta (respostas menores saem mais rápido) |

### Como instalar o modelo

```bash
docker compose up -d --build
docker compose exec ollama ollama pull llama3.2      # baixa ~2 GB na primeira vez
docker compose exec ollama ollama list               # confere se o modelo aparece
docker compose exec ollama ollama run llama3.2       # teste rápido (Ctrl+D para sair)
```

O modelo fica salvo no volume `ollama_data` e não precisa ser baixado de novo ao recriar o contêiner. Ele precisa de
cerca de 4 GB de RAM livre; sem GPU, cada resposta pode levar de alguns segundos a mais de um minuto, e a primeira é a
mais lenta, porque o modelo é carregado na memória.

### Como o backend faz as requisições

O módulo `backend/ia.py` usa apenas a biblioteca padrão do Python (`urllib`), sem dependências novas:

1. a interface envia a `POST /api/ia/explicar` o código analisado e o que foi selecionado;
2. o backend **refaz a análise** do código (os dados vêm do compilador, não do navegador);
3. monta a instrução de sistema (professor de Compiladores que não pode inventar tokens, nós ou erros) e uma mensagem
   com o código, os tokens, a AST em texto, os erros, o elemento selecionado (com a regra gramatical, os ancestrais e
   os filhos, no caso de um nó) e a gramática; esses dados vão entre as marcas `<<<DADOS>>>` e `<<<FIM_DADOS>>>`, e a
   instrução de sistema manda tratá-los como material a explicar, nunca como ordens;
4. chama `POST {OLLAMA_BASE_URL}/api/chat` em modo **streaming** (`stream: true`), com `temperature: 0.2`,
   `num_predict` limitado e `keep_alive: 30m`; o tempo limite vale para a espera entre pedaços, não para a resposta
   inteira, então respostas lentas em CPU não são cortadas enquanto o modelo continua escrevendo;
5. junta os pedaços de `message.content` e devolve `{explicacao, modelo, pergunta, gerado_por_ia: true}`.

Para ficar mais rápido em máquinas sem GPU: o contexto enviado leva só as regras da gramática ligadas ao elemento
selecionado (a gramática inteira vai apenas nas perguntas livres), a resposta é limitada a 400 tokens, o modelo fica
carregado na memória por 30 minutos após o último uso e a interface pede `POST /api/ia/aquecer` ao abrir, para
carregar o modelo antes da primeira pergunta.

Rotas:

| Rota | Corpo | Resposta |
|---|---|---|
| `GET /api/ia/status` | — | `{disponivel, modelo, modelo_instalado, mensagem}` |
| `POST /api/ia/aquecer` | — | HTTP 202 `{iniciado}`; carrega o modelo em segundo plano |
| `POST /api/ia/explicar` | `{"tipo": "no", "codigo": "...", "caminho": [0, 1, 1]}` (índices dos filhos a partir da raiz) | `{explicacao, modelo, pergunta, gerado_por_ia}` |
| | `{"tipo": "erro", "codigo": "...", "indice": 0}` (posição em `erros`) | |
| | `{"tipo": "token", "codigo": "...", "indice": 3}` (posição em `tokens`) | |
| | `{"tipo": "pergunta", "pergunta": "...", "codigo": "..." (opcional)}` | |

Falhas tratadas: Ollama inacessível → HTTP 503 ("Assistente de IA indisponível"); modelo não instalado → 503 com o
comando `ollama pull`; tempo esgotado → 504; resposta vazia ou inválida → 502; pedido inválido → 400 sem chamar o
modelo.

### Funcionalidades na interface

- **Explicar um nó da AST:** botão *Explicar com IA* no painel do nó selecionado.
- **Entender um erro:** botão *Entender erro com IA* em cada erro léxico ou sintático.
- **Explicar um token:** botão *?* em cada linha da tabela de tokens.
- **Professor virtual:** campo de perguntas com sugestões (scanner × parser, terminais e não terminais, AST × árvore
  de derivação, precedência, parser descendente recursivo, recursão à esquerda).
- Indicador do estado do assistente, aviso de carregamento e o rótulo *Explicação gerada por IA — pode conter erros;
  o resultado oficial é o do compilador*.

### Testes da integração

- `backend/tests/test_ia.py` (roda no contêiner com os demais): o Ollama é **simulado**. Verifica que o pedido leva
  os dados reais do compilador (nó, regra, ancestrais, tokens, diagnóstico do parser), a gramática e as marcas de
  dados; o tratamento de indisponibilidade, tempo esgotado, modelo ausente e resposta vazia; a validação dos pedidos;
  a rota de status; e que `/api/analisar` funciona com o Ollama fora do ar e nunca chama a IA.
- `tests_interface/test_interface.py`: botões de IA mostram a explicação ou o aviso de indisponibilidade, sem quebrar.
- **Manual (com o modelo real):** ver o roteiro de demonstração abaixo e registrar em `docs/registro_testes.md`.

### Demonstração

1. `docker compose up -d --build` e `docker compose exec ollama ollama pull llama3.2`.
2. Em <http://localhost:8080>, escolher o exemplo **Precedência: 10 + 5 * 2** e analisar.
3. Clicar no nó `OperacaoBinaria *` e em **Explicar com IA**.
4. Escolher o exemplo **Falta ':' no if**, analisar e clicar em **Entender erro com IA**.

Exemplo de dados enviados ao modelo para o passo 3 (trecho):

```
Nó selecionado: OperacaoBinaria (*), linha 1, coluna 20.
Regra que reconheceu o nó: termo = fator { ( "*" | "/" ) fator } ;
Ancestrais (da raiz até o pai): Programa > Atribuicao (=) > OperacaoBinaria (+)
Filhos: LiteralInteiro (5), LiteralInteiro (2)
```

> Resposta obtida na demonstração: *(colar aqui a resposta do Llama 3.2 depois de rodar no seu computador)*.

### Limitações

- O modelo pode cometer erros conceituais; a explicação é apoio, não resultado oficial.
- O desempenho depende da máquina; sem GPU as respostas são lentas.
- O backend recebe a resposta aos poucos, mas a interface mostra o texto só quando ele fica pronto.
- O contexto enviado é limitado a 3500 caracteres; programas grandes são truncados.
