"""Análise sintática (parser) — Etapa 4.

Parser descendente recursivo escrito à mão: cada regra da gramática abaixo
corresponde a um método da classe ``Parser``. A saída é uma árvore sintática
abstrata (AST) serializável em JSON.

Gramática do subconjunto suportado (EBNF):

    programa        = { comando } FIM_DE_ARQUIVO ;
    comando         = comando_simples NOVA_LINHA
                    | se | enquanto | funcao ;
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

Decisões de projeto:
- o parser para no PRIMEIRO erro sintático (sem recuperação), para evitar
  erros em cascata que confundem o estudante;
- parênteses orientam a construção da árvore, mas não viram nós da AST;
- comparações encadeadas (``a < b < c``) são rejeitadas com mensagem própria.
"""

from .lexico import ErroIndentacao, gerar_tokens_estruturais

MAX_PROFUNDIDADE = 100

OPERADORES_RELACIONAIS = ("==", "!=", "<", ">", "<=", ">=")

_DESCRICAO_ESTRUTURAL = {
    "NOVA_LINHA": "fim da linha",
    "INDENTACAO": "um aumento de indentação",
    "DEDENTACAO": "o fim do bloco indentado",
    "FIM_DE_ARQUIVO": "o fim do código",
}


class ErroSintatico(Exception):
    def __init__(self, mensagem, token, esperado, dica=None):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.token = token
        self.esperado = esperado
        self.dica = dica


def descrever(token):
    if token["tipo"] in _DESCRICAO_ESTRUTURAL:
        return _DESCRICAO_ESTRUTURAL[token["tipo"]]
    return f"'{token['lexema']}'"


def no(tipo, token, valor=None, filhos=None):
    return {
        "tipo": tipo,
        "valor": valor,
        "linha": token["linha"],
        "coluna": token["coluna"],
        "filhos": filhos or [],
    }


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.profundidade = 0

    # ---------- utilitários ----------
    def atual(self):
        return self.tokens[self.pos]

    def proximo(self):
        return self.tokens[min(self.pos + 1, len(self.tokens) - 1)]

    def eh(self, tipo, lexema=None, token=None):
        tok = token or self.atual()
        return tok["tipo"] == tipo and (lexema is None or tok["lexema"] == lexema)

    def avancar(self):
        tok = self.atual()
        if tok["tipo"] != "FIM_DE_ARQUIVO":
            self.pos += 1
        return tok

    def erro(self, esperado, dica=None, token=None):
        tok = token or self.atual()
        if tok["tipo"] == "PALAVRA_RESERVADA" and dica is None and "nome" in esperado:
            dica = f"'{tok['lexema']}' é uma palavra reservada e não pode ser usada como nome."
        mensagem = f"Esperado {esperado}, mas foi encontrado {descrever(tok)}."
        raise ErroSintatico(mensagem, tok, esperado, dica)

    def consumir(self, tipo, lexema=None, esperado=None, dica=None):
        if self.eh(tipo, lexema):
            return self.avancar()
        self.erro(esperado or (f"'{lexema}'" if lexema else tipo), dica)

    def entrar(self):
        self.profundidade += 1
        if self.profundidade > MAX_PROFUNDIDADE:
            raise ErroSintatico(
                f"Aninhamento excede o limite de {MAX_PROFUNDIDADE} níveis.",
                self.atual(), "menos níveis de aninhamento",
                "Divida a expressão ou o bloco em partes menores.",
            )

    def sair(self):
        self.profundidade -= 1

    # ---------- regras ----------
    def programa(self):
        inicio = self.atual()
        comandos = []
        while not self.eh("FIM_DE_ARQUIVO"):
            comandos.append(self.comando())
        return no("Programa", {"linha": inicio["linha"] if comandos else 1, "coluna": 1}, None, comandos)

    def comando(self):
        tok = self.atual()
        if self.eh("INDENTACAO"):
            self.erro("um comando", "Indentação inesperada: só recue linhas dentro de if, while ou def.")
        if self.eh("PALAVRA_RESERVADA"):
            lex = tok["lexema"]
            if self.eh("OPERADOR", "=", self.proximo()):
                self.erro("um nome de variável", f"'{lex}' é uma palavra reservada e não pode ser usada como nome de variável.")
            if lex == "if":
                return self.se()
            if lex == "while":
                return self.enquanto()
            if lex == "def":
                return self.funcao()
            if lex == "else":
                raise ErroSintatico(
                    "'else' sem 'if' correspondente.", tok, "um comando",
                    "O else deve ficar alinhado com um if logo acima, depois do bloco do if.",
                )
            if lex == "for":
                raise ErroSintatico(
                    "A estrutura 'for' não é suportada nesta versão.", tok, "um comando suportado",
                    "Use while para repetições.",
                )
        cmd = self.comando_simples()
        self.consumir("NOVA_LINHA", esperado="o fim da linha (um comando por linha)")
        return cmd

    def comando_simples(self):
        tok = self.atual()
        if self.eh("PALAVRA_RESERVADA", "return"):
            self.avancar()
            filhos = [] if self.eh("NOVA_LINHA") else [self.expressao()]
            return no("Retorno", tok, None, filhos)
        if self.eh("IDENTIFICADOR") and self.eh("OPERADOR", "=", self.proximo()):
            nome = self.avancar()
            self.avancar()  # '='
            valor = self.expressao()
            return no("Atribuicao", nome, "=", [no("Identificador", nome, nome["lexema"]), valor])
        return self.expressao()

    def bloco(self, rotulo, construcao):
        inicio = self.atual()
        self.consumir("NOVA_LINHA", esperado=f"o fim da linha após ':' do {construcao}",
                      dica="O corpo deve começar na linha seguinte, indentado.")
        self.consumir("INDENTACAO", esperado=f"um bloco indentado no corpo do {construcao}",
                      dica="Recue as linhas do corpo (ex.: 4 espaços).")
        self.entrar()
        comandos = [self.comando()]
        while not self.eh("DEDENTACAO") and not self.eh("FIM_DE_ARQUIVO"):
            comandos.append(self.comando())
        self.consumir("DEDENTACAO", esperado="o fim do bloco")
        self.sair()
        return no("Bloco", comandos[0] if comandos else inicio, rotulo, comandos)

    def dois_pontos(self, construcao):
        self.consumir("DELIMITADOR", ":", esperado=f"':' ao final do {construcao}",
                      dica="Em Python, if, else, while e def terminam com ':'.")

    def se(self):
        tok = self.avancar()  # if
        condicao = self.expressao()
        self.dois_pontos("if")
        filhos = [condicao, self.bloco("então", "if")]
        if self.eh("PALAVRA_RESERVADA", "else"):
            self.avancar()
            self.dois_pontos("else")
            filhos.append(self.bloco("senão", "else"))
        return no("Se", tok, None, filhos)

    def enquanto(self):
        tok = self.avancar()  # while
        condicao = self.expressao()
        self.dois_pontos("while")
        return no("Enquanto", tok, None, [condicao, self.bloco("corpo", "while")])

    def funcao(self):
        tok = self.avancar()  # def
        nome = self.consumir("IDENTIFICADOR", esperado="o nome da função")
        self.consumir("DELIMITADOR", "(", esperado="'(' após o nome da função")
        params = []
        if not self.eh("DELIMITADOR", ")"):
            p = self.consumir("IDENTIFICADOR", esperado="o nome de um parâmetro")
            params.append(no("Parametro", p, p["lexema"]))
            while self.eh("DELIMITADOR", ","):
                self.avancar()
                p = self.consumir("IDENTIFICADOR", esperado="o nome de um parâmetro após ','")
                params.append(no("Parametro", p, p["lexema"]))
        self.consumir("DELIMITADOR", ")", esperado="')' para fechar a lista de parâmetros")
        self.dois_pontos("def")
        corpo = self.bloco("corpo", "def")
        return no("Funcao", tok, nome["lexema"], [no("Parametros", nome, None, params), corpo])

    def expressao(self):
        self.entrar()
        esquerda = self.aritmetica()
        if self.eh("OPERADOR") and self.atual()["lexema"] in OPERADORES_RELACIONAIS:
            op = self.avancar()
            direita = self.aritmetica()
            esquerda = no("OperacaoRelacional", op, op["lexema"], [esquerda, direita])
            if self.eh("OPERADOR") and self.atual()["lexema"] in OPERADORES_RELACIONAIS:
                raise ErroSintatico(
                    "Comparações encadeadas (ex.: a < b < c) não são suportadas nesta versão.",
                    self.atual(), "o fim da expressão",
                    "Separe em duas comparações.",
                )
        self.sair()
        return esquerda

    def aritmetica(self):
        esquerda = self.termo()
        while self.eh("OPERADOR", "+") or self.eh("OPERADOR", "-"):
            op = self.avancar()
            esquerda = no("OperacaoBinaria", op, op["lexema"], [esquerda, self.termo()])
        return esquerda

    def termo(self):
        esquerda = self.fator()
        while self.eh("OPERADOR", "*") or self.eh("OPERADOR", "/"):
            op = self.avancar()
            esquerda = no("OperacaoBinaria", op, op["lexema"], [esquerda, self.fator()])
        return esquerda

    def fator(self):
        if self.eh("OPERADOR", "+") or self.eh("OPERADOR", "-"):
            op = self.avancar()
            self.entrar()
            operando = self.fator()
            self.sair()
            return no("OperacaoUnaria", op, op["lexema"], [operando])
        return self.atomo()

    def atomo(self):
        tok = self.atual()
        tipo = tok["tipo"]
        if tipo == "IDENTIFICADOR":
            self.avancar()
            if self.eh("DELIMITADOR", "("):
                self.avancar()
                args = []
                if not self.eh("DELIMITADOR", ")"):
                    args.append(self.expressao())
                    while self.eh("DELIMITADOR", ","):
                        self.avancar()
                        args.append(self.expressao())
                self.consumir("DELIMITADOR", ")", esperado="')' para fechar a chamada de função")
                return no("Chamada", tok, tok["lexema"], args)
            return no("Identificador", tok, tok["lexema"])
        if tipo == "LITERAL_INTEIRO":
            self.avancar()
            return no("LiteralInteiro", tok, tok["lexema"])
        if tipo == "LITERAL_REAL":
            self.avancar()
            return no("LiteralReal", tok, tok["lexema"])
        if tipo == "LITERAL_STRING":
            self.avancar()
            return no("LiteralTexto", tok, tok["lexema"])
        if self.eh("PALAVRA_RESERVADA", "True") or self.eh("PALAVRA_RESERVADA", "False"):
            self.avancar()
            return no("LiteralLogico", tok, tok["lexema"])
        if self.eh("DELIMITADOR", "("):
            self.avancar()
            interna = self.expressao()
            self.consumir("DELIMITADOR", ")", esperado="')' para fechar o parêntese")
            return interna
        self.erro("um operando (número, texto, variável, chamada ou '(')",
                  "Verifique se falta um valor antes ou depois de um operador.")


def analisar_sintatico(codigo, tokens):
    """Retorna (ast, erros). Em caso de erro, ast é None e erros tem 1 item."""
    try:
        estruturais = gerar_tokens_estruturais(codigo, tokens)
    except ErroIndentacao as e:
        return None, [{
            "tipo": "ERRO_SINTATICO",
            "lexema": "",
            "linha": e.linha,
            "coluna": e.coluna,
            "esperado": "indentação consistente",
            "encontrado": "recuo inválido",
            "mensagem": e.mensagem,
            "dica": e.dica,
        }]
    parser = Parser(estruturais)
    try:
        return parser.programa(), []
    except ErroSintatico as e:
        return None, [{
            "tipo": "ERRO_SINTATICO",
            "lexema": e.token["lexema"],
            "linha": e.token["linha"],
            "coluna": e.token["coluna"],
            "esperado": e.esperado,
            "encontrado": descrever(e.token),
            "mensagem": e.mensagem,
            "dica": e.dica,
        }]
