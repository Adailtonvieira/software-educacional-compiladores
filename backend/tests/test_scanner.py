"""Testes unitários do scanner (análise léxica).

Os três primeiros testes são os originais da Etapa 3 e foram mantidos como
regressão. Os demais cobrem cada categoria léxica, as posições (linha e
coluna), o acúmulo de erros e os casos de borda documentados no README.
"""

import pytest

from app import analisar_lexico


def tipos(codigo):
    tokens, _ = analisar_lexico(codigo)
    return [t["tipo"] for t in tokens]


def lexemas(codigo):
    tokens, _ = analisar_lexico(codigo)
    return [t["lexema"] for t in tokens]


# ---------------------------------------------------------------- Etapa 3 (originais)

def test_tokens_basicos():
    codigo = "x = 10"
    tokens, erros = analisar_lexico(codigo)

    assert len(erros) == 0
    assert len(tokens) == 3
    assert tokens[0]['tipo'] == 'IDENTIFICADOR'
    assert tokens[1]['tipo'] == 'OPERADOR'
    assert tokens[2]['tipo'] == 'LITERAL_INTEIRO'


def test_palavras_reservadas():
    codigo = "if else while"
    tokens, erros = analisar_lexico(codigo)

    assert len(erros) == 0
    assert tokens[0]['tipo'] == 'PALAVRA_RESERVADA'


def test_erro_lexico():
    codigo = "x = @"
    tokens, erros = analisar_lexico(codigo)

    assert len(erros) == 1
    assert "Caractere não reconhecido" in erros[0]['mensagem']


# ---------------------------------------------------------------- formato do token

def test_token_tem_os_quatro_campos_do_contrato():
    tokens, _ = analisar_lexico("x")
    assert set(tokens[0]) == {"tipo", "lexema", "linha", "coluna"}


def test_erro_tem_os_cinco_campos_do_contrato():
    _, erros = analisar_lexico("@")
    assert set(erros[0]) == {"tipo", "lexema", "linha", "coluna", "mensagem"}
    assert erros[0]["tipo"] == "ERRO_LEXICO"


# ---------------------------------------------------------------- palavras reservadas

@pytest.mark.parametrize("palavra", ["if", "else", "while", "for", "def", "return", "True", "False"])
def test_cada_palavra_reservada(palavra):
    assert tipos(palavra) == ["PALAVRA_RESERVADA"]


@pytest.mark.parametrize("nome", ["iffy", "elsewhere", "definir", "retorno", "true", "_if", "for2"])
def test_prefixo_de_palavra_reservada_e_identificador(nome):
    assert tipos(nome) == ["IDENTIFICADOR"]


# ---------------------------------------------------------------- identificadores

@pytest.mark.parametrize("nome", ["x", "numero", "_variavel", "contador1", "CamelCase", "__dunder__"])
def test_identificadores_validos(nome):
    assert tipos(nome) == ["IDENTIFICADOR"]
    assert lexemas(nome) == [nome]


# ---------------------------------------------------------------- literais

@pytest.mark.parametrize("codigo,tipo", [
    ("0", "LITERAL_INTEIRO"),
    ("42", "LITERAL_INTEIRO"),
    ("3.14", "LITERAL_REAL"),
    ("0.5", "LITERAL_REAL"),
    ('"texto"', "LITERAL_STRING"),
    ("'a'", "LITERAL_STRING"),
    ('""', "LITERAL_STRING"),
    ('"com # dentro"', "LITERAL_STRING"),
])
def test_literais(codigo, tipo):
    assert tipos(codigo) == [tipo]
    assert lexemas(codigo) == [codigo]


def test_real_nao_e_quebrado_em_inteiro_ponto_inteiro():
    assert tipos("x = 2.75") == ["IDENTIFICADOR", "OPERADOR", "LITERAL_REAL"]


# ---------------------------------------------------------------- operadores e delimitadores

@pytest.mark.parametrize("op", ["==", "!=", "<=", ">="])
def test_operadores_de_dois_caracteres_sao_um_token(op):
    assert lexemas(f"a {op} b") == ["a", op, "b"]


@pytest.mark.parametrize("op", ["+", "-", "*", "/", "=", "<", ">"])
def test_operadores_de_um_caractere(op):
    assert tipos(op) == ["OPERADOR"]


def test_operadores_colados_sem_espaco():
    assert lexemas("a<=b") == ["a", "<=", "b"]
    assert lexemas("x=y==z") == ["x", "=", "y", "==", "z"]


@pytest.mark.parametrize("d", ["(", ")", "[", "]", ":", ","])
def test_delimitadores(d):
    assert tipos(d) == ["DELIMITADOR"]


# ---------------------------------------------------------------- espaços e comentários

def test_comentario_e_ignorado():
    assert lexemas("x = 1  # comentário") == ["x", "=", "1"]


def test_linha_so_com_comentario_nao_gera_token():
    tokens, erros = analisar_lexico("# só comentário")
    assert tokens == [] and erros == []


def test_simbolo_invalido_dentro_de_comentario_nao_e_erro():
    _, erros = analisar_lexico("# custa R$ 10 @ unidade")
    assert erros == []


def test_tabulacao_e_quebra_windows_sao_espacos():
    assert lexemas("x\t=\t1\r\ny = 2") == ["x", "=", "1", "y", "=", "2"]


# ---------------------------------------------------------------- posições

def test_colunas_na_mesma_linha():
    tokens, _ = analisar_lexico("total = a + 10")
    assert [(t["lexema"], t["coluna"]) for t in tokens] == [
        ("total", 1), ("=", 7), ("a", 9), ("+", 11), ("10", 13)]


def test_linhas_e_colunas_em_varias_linhas():
    tokens, _ = analisar_lexico("x = 1\nif x > 0:\n    y = 2")
    pos = {(t["lexema"], t["linha"]): t["coluna"] for t in tokens}
    assert pos[("if", 2)] == 1
    assert pos[(":", 2)] == 9
    assert pos[("y", 3)] == 5


def test_linhas_em_branco_contam_na_numeracao():
    tokens, _ = analisar_lexico("x = 1\n\n\ny = 2")
    assert [t["linha"] for t in tokens if t["lexema"] == "y"] == [4]


def test_posicao_apos_comentario_na_linha_anterior():
    tokens, _ = analisar_lexico("# cabeçalho\nx = 1")
    assert (tokens[0]["linha"], tokens[0]["coluna"]) == (2, 1)


# ---------------------------------------------------------------- erros léxicos

def test_posicao_do_erro():
    _, erros = analisar_lexico("x = 1\ny = $")
    assert (erros[0]["lexema"], erros[0]["linha"], erros[0]["coluna"]) == ("$", 2, 5)


def test_acumula_varios_erros_sem_interromper():
    tokens, erros = analisar_lexico("a = @\nb = $\nc = 3")
    assert [(e["lexema"], e["linha"]) for e in erros] == [("@", 1), ("$", 2)]
    assert [t["lexema"] for t in tokens] == ["a", "=", "b", "=", "c", "=", "3"]


def test_tokens_validos_depois_do_erro_continuam_reconhecidos():
    tokens, erros = analisar_lexico("x = 1 ? 2")
    assert len(erros) == 1
    assert [t["lexema"] for t in tokens] == ["x", "=", "1", "2"]


@pytest.mark.parametrize("simbolo", ["@", "$", "?", "!", "&", "|", "{", "}", ";", "%", "^", "~", "`"])
def test_simbolos_fora_do_escopo_geram_erro(simbolo):
    _, erros = analisar_lexico(f"x {simbolo} y")
    assert len(erros) == 1 and erros[0]["lexema"] == simbolo


def test_numero_malformado_gera_um_unico_erro():
    tokens, erros = analisar_lexico("valor = 12abc")
    assert len(erros) == 1
    assert erros[0]["lexema"] == "12abc"
    assert "malformado" in erros[0]["mensagem"]
    assert [t["lexema"] for t in tokens] == ["valor", "="]


def test_string_nao_fechada():
    tokens, erros = analisar_lexico('msg = "olá\nx = 1')
    assert len(erros) == 1 and "String não fechada" in erros[0]["mensagem"]
    assert ("x", 2) in [(t["lexema"], t["linha"]) for t in tokens]


def test_caractere_unicode_fora_do_escopo():
    _, erros = analisar_lexico("π = 3.14")
    assert len(erros) == 1 and erros[0]["lexema"] == "π"


# ---------------------------------------------------------------- programa completo

def test_programa_completo_sem_erros():
    codigo = (
        "def soma(a, b):\n"
        "    return a + b\n"
        "\n"
        "if soma(1, 2) >= 3:\n"
        "    print(\"ok\")  # saída\n"
        "else:\n"
        "    print('erro')\n"
    )
    tokens, erros = analisar_lexico(codigo)
    assert erros == []
    contagem = {}
    for t in tokens:
        contagem[t["tipo"]] = contagem.get(t["tipo"], 0) + 1
    assert contagem == {
        "PALAVRA_RESERVADA": 4,   # def, return, if, else
        "IDENTIFICADOR": 8,       # soma, a, b, a, b, soma, print, print
        "DELIMITADOR": 13,        # ( , ) :   ( , ) :   ( )   :   ( )
        "OPERADOR": 2,            # +, >=
        "LITERAL_INTEIRO": 3,     # 1, 2, 3
        "LITERAL_STRING": 2,      # "ok", 'erro'
    }
    assert [t["lexema"] for t in tokens if t["tipo"] == "PALAVRA_RESERVADA"] == ["def", "return", "if", "else"]
    assert [t["lexema"] for t in tokens if t["tipo"] == "LITERAL_STRING"] == ['"ok"', "'erro'"]


def test_codigo_vazio_retorna_listas_vazias():
    assert analisar_lexico("") == ([], [])
