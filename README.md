# software-educacional-compiladores

## Introdução

Este projeto consiste no desenvolvimento de um **software educacional para o ensino de compiladores**, com foco nas fases de análise léxica e sintática. A ferramenta é voltada a estudantes de graduação em Ciência da Computação que enfrentam dificuldades na transição entre a teoria e a prática no estudo de compiladores.

O software adota uma abordagem **web interativa**, permitindo que os alunos visualizem o processo de compilação passo a passo, desde a tokenização do código-fonte até a construção da árvore sintática. Esta primeira etapa estabelece a fundação do projeto: estrutura de pastas, ambiente Docker funcional e uma aplicação web mínima exibindo a mensagem "Hello, World!", provando que toda a cadeia (frontend + backend) está operacional.

---

## Linguagem Foco

**Python** - escolhida pela simplicidade sintática e ampla adoção acadêmica.

---

## Justificativa da Escolha

A escolha do Python como linguagem foco do software educacional baseia-se em três razões principais:

1. **Simplicidade sintática** - Python possui uma gramática limpa e legível, o que permite que o estudante concentre seus esforços na compreensão dos conceitos de compilação (análise léxica, sintática e semântica) sem se dispersar com complexidades sintáticas da própria linguagem.

2. **Disponibilidade de bibliotecas de referência** - Ferramentas como PLY e Lark oferecem implementações de analisadores que podem servir como base de comparação e inspiração para o desenvolvimento do software.

3. **Ampla adoção acadêmica** - Python é a linguagem introdutória mais utilizada em cursos de Ciência da Computação no Brasil, o que facilita a adoção do software por alunos e professores.

Além disso, a escolha de Python alinha-se ao público-alvo (graduandos em Ciência da Computação), que tipicamente já possui familiaridade com a linguagem.

---

## Subconjunto Inicial

Para tornar o projeto viável dentro do prazo da disciplina, foi delimitado um **subconjunto inicial** da linguagem Python. Não se pretende cobrir a linguagem inteira, mas sim as construções mais fundamentais:

- **Declaração de variáveis** 
- **Operadores aritméticos** 
- **Estruturas condicionais simples** 
- **Expressões de comparação**

Novas construções serão incorporadas gradativamente nas etapas seguintes do projeto, conforme a evolução do software.

---

## Estrutura do Projeto
> software-educacional-compiladores/
    > backend/ 
      >    app.py 
      >    requirements.txt 
      >    Dockerfile 

    > frontend/
      > index.html
      > nginx.conf 
      > Dockerfile 

> compose.yaml # Orquestração dos serviços com Docker Compose
> README.md




## Como Clonar e Rodar em Qualquer Máquina

Esta seção descreve o passo a passo para executar o projeto em uma máquina que nunca teve contato com ele. Qualquer pessoa com os pré-requisitos instalados conseguirá reproduzir o ambiente.

### Pré-requisitos

Antes de começar, certifique-se de que a máquina possui:

| Ferramenta     | Versão mínima | Como verificar |
| Git            | 2.30+         | `git --version` |
| Docker Desktop | 24+           | `docker --version` |
| Docker Compose | v2+           | `docker compose version` |

#### Observação para Windows

O Docker Desktop no Windows requer:

- **WSL 2** instalado e configurado
- Uma **distribuição Linux** (ex: Ubuntu) instalada no WSL

Para instalar o WSL e o Ubuntu, execute no **PowerShell como Administrador**:

```powershell
wsl --install -d Ubuntu

## Funcionalidades da Etapa 3 (Análise Léxica)

- Scanner implementado em Python para o subconjunto da linguagem.
- Identificação de Palavras Reservadas, Identificadores, Literais, Operadores e Delimitadores.
- Detecção de erros léxicos com indicação de linha e coluna.
- Tabela interativa no frontend exibindo os tokens.

## Escopo Léxico (Subconjunto de Python)

| Categoria | Exemplos |
| :--- | :--- |
| **Palavras reservadas** | `if`, `else`, `while`, `for`, `def`, `return`, `True`, `False` |
| **Identificadores** | `x`, `numero`, `_variavel`, `contador1` |
| **Literais** | `10`, `3.14`, `"texto"`, `'a'` |
| **Operadores** | `+`, `-`, `*`, `/`, `=`, `==`, `!=`, `>`, `<` |
| **Delimitadores** | `(`, `)`, `[`, `]`, `:`, `,` |
| **Comentários** | `# linha` (ignorados) |

## Como Executar os Testes Automatizados

Para rodar os testes no Docker, utilize o comando:
```bash
docker compose exec -e PYTHONPATH=/app backend pytest tests/ -v

## Contrato de Comunicação (API)

**Requisição (POST /api/analisar):**
```json
{ "codigo": "x = 10" }


{
  "sucesso": true,
  "tokens": [
    { "tipo": "IDENTIFICADOR", "lexema": "x", "linha": 1, "coluna": 1 },
    { "tipo": "OPERADOR", "lexema": "=", "linha": 1, "coluna": 3 },
    { "tipo": "LITERAL_INTEIRO", "lexema": "10", "linha": 1, "coluna": 5 }
  ],
  "erros": []
}

{
  "sucesso": false,
  "tokens": [],
  "erros": [
    { "tipo": "ERRO_LEXICO", "lexema": "@", "linha": 1, "coluna": 5, "mensagem": "Caractere não reconhecido: '@'" }
  ]
}


#### 3. Registro dos Testes (Item 6 e 9)
O professor exige um registro em `docs/` mostrando que você executou os testes.
**Como resolver:** 
1. No seu GitHub, vá na pasta `docs`.
2. Clique em "Add file" -> "Create new file".
3. Nomeie como `registro_testes.md`.
4. Cole o seguinte texto:

```markdown
# Registro de Testes - Etapa 3

## Testes Unitários do Scanner
- **Comando:** `docker compose exec -e PYTHONPATH=/app backend pytest tests/ -v`
- **Resultado:** 4 testes passaram com sucesso (Tokens básicos, Palavras Reservadas, Erro Léxico, Requisição Vazia).
- **Falhas encontradas:** Nenhuma falha na execução final.

## Testes de Regressão (Etapas 1 e 2)
- O ambiente Docker subiu corretamente.
- A comunicação frontend-backend continua funcionando.
- A interface não quebrou ao inserir entradas inválidas.

## Limitações Conhecidas
- O sistema realiza apenas a Análise Léxica (Scanner). A Análise Sintática (Parser) e a Análise Semântica serão implementadas nas próximas etapas.

## Etapa 4 — Análise sintática (parser) e árvore sintática abstrata (AST)

Nesta etapa o sistema passou a verificar a **estrutura** do programa e a montar a **AST**, exibida na interface em
forma hierárquica (navegável por teclado) e gráfica (SVG). A análise semântica **ainda não está implementada**
(Etapa 5).

### Escopo da linguagem (subconjunto de Python 3)

| Suportado | Não suportado nesta versão |
|---|---|
| Atribuição simples (`x = expr`) | `for`, `elif`, `and`/`or`/`not`, `in` |
| Expressões aritméticas `+ - * /`, menos unário, parênteses | listas, tuplas, dicionários, índices `a[i]` |
| Comparações `== != < > <= >=` (uma por expressão) | comparações encadeadas (`a < b < c`) |
| `if` / `else`, `while`, blocos aninhados por indentação | classes, `import`, `try`, `lambda`, decoradores |
| `def nome(params):` e `return [expr]` | atribuição múltipla / aumentada (`a, b = ...`, `+=`) |
| Chamadas de função (`print(x)`, `soma(1, 2)`) | comando na mesma linha do `:` (`if x: y = 1`) |
| Inteiros, reais, textos entre aspas, `True`, `False` | quebra de linha dentro de parênteses; strings com `\"`, `'''` |
| Comentários de linha (`#`) | mistura de tabulação e espaço na indentação |

### Gramática (EBNF)

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

`NOVA_LINHA`, `INDENTACAO`, `DEDENTACAO` e `FIM_DE_ARQUIVO` são **tokens estruturais** gerados a partir das linhas e do
recuo do código (como no Python). Eles são usados pelo parser, mas não aparecem na tabela de tokens.

### Estrutura do backend

```
backend/
├── app.py                  # rota POST /api/analisar, validação e orquestração
├── analisador/
│   ├── __init__.py
│   ├── lexico.py           # scanner (Etapa 3) + tokens estruturais
│   └── sintatico.py        # parser descendente recursivo + AST
└── tests/
    ├── test_scanner.py     # regressão da Etapa 3
    ├── test_parser.py      # casos CT-xx (docs/casos-de-teste.md)
    └── test_api_etapa4.py  # contrato da API e validação de entrada
```

### Contrato de comunicação (compatível com a Etapa 3)

Requisição: `POST /api/analisar` com `{"codigo": "<texto>"}` (máximo de 5000 caracteres).

Resposta (HTTP 200). Os campos `sucesso`, `tokens` e `erros` são os mesmos da Etapa 3; `ast` e `etapas` são novos:

```json
{
  "sucesso": true,
  "tokens": [{"tipo": "IDENTIFICADOR", "lexema": "x", "linha": 1, "coluna": 1}, "..."],
  "erros": [],
  "ast": {
    "tipo": "Programa", "valor": null, "linha": 1, "coluna": 1,
    "filhos": [{
      "tipo": "Atribuicao", "valor": "=", "linha": 1, "coluna": 1,
      "filhos": [
        {"tipo": "Identificador", "valor": "x", "linha": 1, "coluna": 1, "filhos": []},
        {"tipo": "LiteralInteiro", "valor": "10", "linha": 1, "coluna": 5, "filhos": []}
      ]
    }]
  },
  "etapas": {"lexica": "ok", "sintatica": "ok", "semantica": "nao_implementada"}
}
```

Erro sintático (o parser para no primeiro erro e `ast` vem `null`):

```json
{
  "tipo": "ERRO_SINTATICO", "lexema": "", "linha": 1, "coluna": 9,
  "esperado": "':' ao final do if", "encontrado": "fim da linha",
  "mensagem": "Esperado ':' ao final do if, mas foi encontrado fim da linha.",
  "dica": "Em Python, if, else, while e def terminam com ':'."
}
```

Valores de `etapas.sintatica`: `ok`, `erro` ou `nao_executada` (quando há erro léxico).
Entradas inválidas (vazio, só espaços, não texto, acima do limite, corpo sem JSON) retornam HTTP 400 com `{"erro": "..."}`.

Tipos de nó da AST: `Programa`, `Atribuicao`, `Identificador`, `Se`, `Enquanto`, `Funcao`, `Parametros`, `Parametro`,
`Bloco` (valor `então`, `senão` ou `corpo`), `Retorno`, `Chamada`, `OperacaoBinaria`, `OperacaoRelacional`,
`OperacaoUnaria`, `LiteralInteiro`, `LiteralReal`, `LiteralTexto`, `LiteralLogico`.

### Decisões de projeto

- **Parser descendente recursivo escrito à mão**: cada regra da gramática é um método, o que deixa o código legível
  para estudantes e permite mensagens de erro específicas por construção.
- **Erro léxico interrompe o pipeline**: o parser não é executado, para não gerar erros sintáticos em cascata.
- **Parada no primeiro erro sintático**, sem recuperação.
- **Parênteses não viram nós**: a forma da árvore já representa a precedência.
- **Limites de segurança**: 5000 caracteres por análise e 100 níveis de aninhamento; a interface insere texto com
  `textContent` (nunca `innerHTML`) para evitar injeção de HTML.

### Como executar e testar

```bash
docker compose up -d --build                     # sobe frontend (8080) e backend (5000)
docker compose exec -e PYTHONPATH=/app backend pytest tests/ -v
docker compose down                              # encerra
```

Acesse `http://localhost:8080`. Os casos de teste estão em [`docs/casos-de-teste.md`](docs/casos-de-teste.md); o
fluxograma e a arquitetura, em [`docs/fluxograma.md`](docs/fluxograma.md).

### Limitações conhecidas

- A análise semântica e a tabela de símbolos ainda não existem (Etapa 5).
- O parser relata apenas o primeiro erro sintático.
- A AST gráfica não tem zoom; árvores grandes exigem rolagem (a visão hierárquica permite recolher subárvores).
- Não há visualização passo a passo da construção da árvore.
- A interface foi testada apenas em Chrome (desktop e emulação de 390 px).
