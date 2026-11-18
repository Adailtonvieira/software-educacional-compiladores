# Gramática, parser e AST

Este documento descreve a gramática do subconjunto de Python reconhecido pelo software, a estratégia de análise
sintática e a estrutura da árvore sintática abstrata (AST). A gramática também é devolvida pela rota
`GET /api/gramatica`, a partir do dicionário `GRAMATICA` em `backend/analisador/sintatico.py`, que é a fonte única
usada pelo parser, pelas mensagens de erro e pela interface.

## 1. Gramática formal (EBNF)

**Símbolo inicial:** `programa`.

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

Notação: `{ x }` repete zero ou mais vezes; `[ x ]` é opcional; `|` separa alternativas; texto entre aspas é um
terminal literal; nomes em MAIÚSCULAS são categorias de token.

**Não terminais (17):** `programa`, `comando`, `comando_simples`, `atribuicao`, `retorno`, `se`, `enquanto`,
`funcao`, `parametros`, `bloco`, `expressao`, `op_relacional`, `aritmetica`, `termo`, `fator`, `atomo`,
`argumentos`.

## 2. Terminais e correspondência com os tokens da Etapa 3

| Terminal na gramática | Categoria produzida pelo scanner |
|---|---|
| `IDENTIFICADOR` | `IDENTIFICADOR` |
| `LITERAL_INTEIRO`, `LITERAL_REAL`, `LITERAL_STRING` | categorias de mesmo nome |
| `"if"`, `"else"`, `"while"`, `"def"`, `"return"`, `"True"`, `"False"` | `PALAVRA_RESERVADA` (o parser compara o lexema) |
| `"="`, `"+"`, `"-"`, `"*"`, `"/"`, `"=="`, `"!="`, `"<"`, `">"`, `"<="`, `">="` | `OPERADOR` |
| `"("`, `")"`, `":"`, `","` | `DELIMITADOR` |
| `NOVA_LINHA`, `INDENTACAO`, `DEDENTACAO`, `FIM_DE_ARQUIVO` | **tokens estruturais**, gerados por `gerar_tokens_estruturais` a partir do recuo de cada linha |

O scanner reconhece `for`, `[` e `]`, que **não aparecem** na gramática: o parser responde com mensagem própria
("A estrutura 'for' não é suportada nesta versão") ou como token inesperado.

**Alterações no scanner para a Etapa 4** (documentadas e com testes léxicos):
- número seguido de letra (`12abc`) passou a gerar **um** erro "Literal numérico malformado", em vez de um erro por
  caractere;
- aspa sem fechamento na linha passou a gerar o erro "String não fechada" (antes, uma string podia atravessar
  linhas);
- `\r` passou a ser tratado como espaço (quebra de linha do Windows).

Os tokens produzidos para entradas válidas não mudaram; os testes da Etapa 3 continuam passando sem alteração.

**Tokens estruturais.** O Python delimita blocos pelo recuo. Antes do parser, cada linha que tem tokens é comparada
com uma pilha de níveis de recuo: recuo maior gera `INDENTACAO`; recuo menor gera um `DEDENTACAO` por nível
fechado; recuo que não volta a um nível anterior gera erro de indentação. Ao final de cada linha com comando entra um
`NOVA_LINHA`. Linhas vazias ou só com comentário são ignoradas. Esses tokens não aparecem na tabela de tokens.

## 3. Precedência e associatividade

A precedência está codificada nos níveis da gramática: quanto mais fundo o não terminal, maior a precedência.

| Precedência | Operadores | Não terminal | Associatividade |
|---|---|---|---|
| 1 (menor) | `==` `!=` `<` `>` `<=` `>=` | `expressao` | não associativa (uma comparação por expressão) |
| 2 | `+` `-` binários | `aritmetica` | à esquerda |
| 3 | `*` `/` | `termo` | à esquerda |
| 4 (maior) | `+` `-` unários | `fator` | à direita (`--x` é `-(-x)`) |

A associatividade à esquerda vem das repetições `{ ... }`: o parser junta o resultado acumulado com o próximo
operando a cada volta do laço.

| Código | Organização reconhecida | AST |
|---|---|---|
| `resultado = 10 + 5 * 2` | `10 + (5 * 2)` | `+` com filhos `10` e `*(5, 2)` |
| `resultado = 20 - 5 - 3` | `(20 - 5) - 3` | `-` com filhos `-(20, 5)` e `3` |
| `resultado = (10 + 5) * 2` | `(10 + 5) * 2` | `*` com filhos `+(10, 5)` e `2` |
| `ok = a + 1 > b * 2` | `(a + 1) > (b * 2)` | `>` com filhos `+(a, 1)` e `*(b, 2)` |

AST de `resultado = 10 + 5 * 2`:

```
Programa
└── Atribuicao (=)
    ├── Identificador: resultado
    └── OperacaoBinaria: +
        ├── LiteralInteiro: 10
        └── OperacaoBinaria: *
            ├── LiteralInteiro: 5
            └── LiteralInteiro: 2
```

## 4. Construções suportadas e fora do escopo

| Suportado | Fora do escopo nesta versão |
|---|---|
| Atribuição simples (`x = expr`) | `for`, `elif`, `and`/`or`/`not`, `in`, `is` |
| Expressões `+ - * /`, menos/mais unário, parênteses | listas, tuplas, dicionários, índices `a[i]`, fatias |
| Uma comparação por expressão | comparações encadeadas (`a < b < c`) |
| `if` / `else`, `while`, blocos aninhados | `break`, `continue`, `pass`, classes, `import`, `try`, `with`, `lambda` |
| `def` com parâmetros e `return` | parâmetros com valor padrão, `*args`, anotações de tipo |
| Chamadas de função com argumentos | chamadas encadeadas (`f(1)(2)`), métodos (`a.b()`) |
| Literais inteiros, reais, texto, `True`, `False` | `None`, notação científica, aspas triplas, escapes |
| Comentários de linha | atribuição múltipla ou aumentada (`a, b = ...`, `+=`) |
| | comando na mesma linha do `:`; quebra de linha dentro de parênteses; mistura de tab e espaço |

## 5. Exemplos

**Válidos**

```python
nota = 7
if nota >= 6:
    print("aprovado")
else:
    print("reprovado")
```

```python
def dobro(n):
    return n * 2

total = 0
i = 1
while i <= 3:
    total = total + dobro(i)
    i = i + 1
```

**Inválidos (erros sintáticos intencionais)**

| Código | Mensagem do parser |
|---|---|
| `if x > 0` + corpo | Esperado ':' ao final do if, mas foi encontrado fim da linha. |
| `x = (1 + 2` | Esperado ')' para fechar o parêntese aberto na linha 1, coluna 5, mas foi encontrado fim da linha. |
| `x = ` | Esperado um operando (número, texto, variável, chamada ou '('), mas foi encontrado fim da linha. |
| `x = 1 + * 2` | Esperado um operando (...), mas foi encontrado '*'. |
| `else:` sem `if` | 'else' sem 'if' correspondente. |
| `if = 5` | Esperado um nome de variável, mas foi encontrado 'if'. Dica: 'if' é uma palavra reservada... |
| `while x < 3:` no fim do código | O código terminou antes de concluir o while iniciado na linha N. Esperado um bloco indentado no corpo do while. |
| linha recuada sem bloco | Esperado um comando, mas foi encontrado um aumento de indentação. Dica: Indentação inesperada... |
| `x = a < b < c` | Comparações encadeadas (ex.: a < b < c) não são suportadas nesta versão. |

## 6. Estratégia de análise sintática

**Estratégia:** analisador **descendente recursivo**, escrito à mão em Python (`backend/analisador/sintatico.py`).
Cada não terminal da gramática é um método da classe `Parser`; um decorador registra qual regra está em análise,
para que as mensagens de erro e os nós da AST indiquem a regra.

**Por que essa estratégia:**
- é a mais próxima da gramática: quem lê o método `se()` reconhece a produção `se = "if" expressao ":" bloco ...`;
- permite mensagens específicas por construção ("':' ao final do if", "')' para fechar a chamada de 'print'");
- não exige ferramenta externa nem etapa de geração no build do Docker;
- a gramática não tem recursão à esquerda (as repetições usam `{ }`), então não foi preciso transformá-la.

**O que é manual e o que é gerado:** tudo é manual. Não há gerador de parser (ANTLR, Lark, PLY) nem uso do
módulo `ast` do Python. O scanner da Etapa 3 é reaproveitado sem reimplementação; a única etapa nova antes do
parser é a geração dos tokens estruturais de indentação.

**Limitações da estratégia:** a gramática precisa ser decidível olhando no máximo dois tokens à frente (o parser usa
um token de lookahead extra para diferenciar `x = ...` de uma expressão); acrescentar construções exige escrever
novos métodos à mão; não há recuperação de erros.

**Fluxo:** código → `analisar_lexico` (tokens e erros léxicos) → se houver erro léxico, o parser **não** roda →
`gerar_tokens_estruturais` → `Parser.programa()` → AST ou primeiro erro sintático → resposta JSON.

## 7. Tratamento de erros sintáticos

- **Parada no primeiro erro:** não há recuperação (modo pânico). Apenas o primeiro erro sintático é reportado, para
  evitar erros em cascata.
- **Campos de cada erro:** posição (`linha`, `coluna`), `esperado`, `encontrado`, `mensagem`, `dica`, `regra` (não
  terminal em análise), `producao` (texto da regra) e `abertura` (posição do `if`, `while`, `def` ou parêntese que
  ficou aberto, quando houver).
- **Fim inesperado do código:** a mensagem cita a linha em que a construção começou.
- **Construções conhecidas mas não suportadas** (`for`, comparação encadeada) têm mensagem própria.
- **Limites:** 5000 caracteres e 100 níveis de aninhamento. Falhas inesperadas retornam HTTP 500 com mensagem
  genérica; detalhes internos vão apenas para o log do servidor.

## 8. Estrutura da AST

Cada nó é um objeto JSON com os mesmos campos:

| Campo | Tipo | Descrição |
|---|---|---|
| `tipo` | texto | tipo do nó (tabela abaixo) |
| `valor` | texto ou `null` | operador, nome ou valor literal, conforme o tipo |
| `regra` | texto | não terminal da gramática que reconheceu o nó |
| `linha`, `coluna` | inteiros | posição do token que **identifica** o nó (o operador, o nome, a palavra reservada); coincide com uma linha da tabela de tokens |
| `inicio`, `fim` | `{linha, coluna}` | trecho completo do código coberto pelo nó (fim inclusivo) |
| `filhos` | lista de nós | subárvores, na ordem do código |

| Tipo | Categoria | `valor` | Filhos | Regra |
|---|---|---|---|---|
| `Programa` | estrutura | `null` | comandos de topo | `programa` |
| `Bloco` | estrutura | `então`, `senão` ou `corpo` | comandos do bloco | `bloco` |
| `Parametros` | estrutura | `null` | `Parametro`* | `parametros` |
| `Atribuicao` | comando | `=` | `Identificador`, expressão | `atribuicao` |
| `Se` | comando | `null` | condição, `Bloco(então)`, [`Bloco(senão)`] | `se` |
| `Enquanto` | comando | `null` | condição, `Bloco(corpo)` | `enquanto` |
| `Funcao` | comando | nome da função | `Parametros`, `Bloco(corpo)` | `funcao` |
| `Retorno` | comando | `null` | [expressão] | `retorno` |
| `OperacaoBinaria` | expressão | `+` `-` `*` `/` | esquerda, direita | `aritmetica` ou `termo` |
| `OperacaoRelacional` | expressão | `==` `!=` `<` `>` `<=` `>=` | esquerda, direita | `expressao` |
| `OperacaoUnaria` | expressão | `+` `-` | operando | `fator` |
| `Chamada` | expressão | nome da função | argumentos | `atomo` |
| `Identificador` | folha | nome | — | `atomo` ou `atribuicao` |
| `Parametro` | folha | nome | — | `parametros` |
| `LiteralInteiro` / `LiteralReal` | folha | texto do número | — | `atomo` |
| `LiteralTexto` | folha | texto com as aspas | — | `atomo` |
| `LiteralLogico` | folha | `True` ou `False` | — | `atomo` |

Exemplo (trecho) para `x = 10 + 5`:

```json
{
  "tipo": "OperacaoBinaria", "valor": "+", "regra": "aritmetica",
  "linha": 1, "coluna": 8,
  "inicio": {"linha": 1, "coluna": 5}, "fim": {"linha": 1, "coluna": 10},
  "filhos": [
    {"tipo": "LiteralInteiro", "valor": "10", "regra": "atomo", "linha": 1, "coluna": 5,
     "inicio": {"linha": 1, "coluna": 5}, "fim": {"linha": 1, "coluna": 6}, "filhos": []},
    {"tipo": "LiteralInteiro", "valor": "5", "regra": "atomo", "linha": 1, "coluna": 10,
     "inicio": {"linha": 1, "coluna": 10}, "fim": {"linha": 1, "coluna": 10}, "filhos": []}
  ]
}
```

## 9. Tokens, árvore de derivação e AST

- **Tokens:** sequência plana do scanner. Para `x = 5 + 3`: `IDENTIFICADOR(x)`, `OPERADOR(=)`,
  `LITERAL_INTEIRO(5)`, `OPERADOR(+)`, `LITERAL_INTEIRO(3)`.
- **Árvore de derivação (concreta):** teria um nó para cada regra aplicada, inclusive as intermediárias
  (`comando → comando_simples → atribuicao`, `expressao → aritmetica → termo → fator → atomo`) e para todos os
  terminais, incluindo parênteses e `:`.
- **AST (o que o software mostra):** só os nós com significado: `Atribuicao(Identificador x, OperacaoBinaria +(5, 3))`.
  Parênteses e regras intermediárias desaparecem, e a precedência fica na forma da árvore.

A interface exibe a **AST** e identifica, em cada nó, a regra que o reconheceu. A ordem do **passo a passo** é a
ordem em que o parser conclui cada nó (pós-ordem: filhos antes do pai), que é a ordem real de construção num parser
descendente recursivo.

## 10. Relação com a Etapa 5

A análise semântica ainda **não** está implementada. A AST já guarda o que ela vai precisar: nomes de variáveis e
funções nos nós `Identificador`, `Atribuicao`, `Funcao` e `Chamada`, número de parâmetros e argumentos, e posições
para localizar os erros semânticos (variável usada antes de receber valor, função não definida, número de argumentos
incompatível, `return` fora de função).
