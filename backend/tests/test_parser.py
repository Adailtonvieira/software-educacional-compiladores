"""Testes unitários do parser (Etapa 4).

Os identificadores CT-xx correspondem aos casos documentados em
docs/casos-de-teste.md.
"""

import pytest

from app import analisar
from analisador import analisar_lexico, gerar_tokens_estruturais


def ast_de(codigo):
    r = analisar(codigo)
    assert r["erros"] == [], r["erros"]
    return r["ast"]


def tipos(no):
    """Representação compacta da árvore: (tipo, valor, [filhos])."""
    return (no["tipo"], no["valor"], [tipos(f) for f in no["filhos"]])


def erro_unico(codigo):
    r = analisar(codigo)
    assert len(r["erros"]) == 1, r["erros"]
    return r["erros"][0], r


# ---------------- casos válidos ----------------

def test_ct01_atribuicao_simples():
    ast = ast_de("x = 10")
    assert tipos(ast) == ("Programa", None, [
        ("Atribuicao", "=", [("Identificador", "x", []), ("LiteralInteiro", "10", [])])
    ])


def test_ct02_precedencia_multiplicacao_antes_da_soma():
    expr = ast_de("x = 1 + 2 * 3")["filhos"][0]["filhos"][1]
    assert tipos(expr) == ("OperacaoBinaria", "+", [
        ("LiteralInteiro", "1", []),
        ("OperacaoBinaria", "*", [("LiteralInteiro", "2", []), ("LiteralInteiro", "3", [])]),
    ])


def test_ct03_parenteses_mudam_a_arvore_mas_nao_viram_no():
    expr = ast_de("x = (1 + 2) * 3")["filhos"][0]["filhos"][1]
    assert tipos(expr) == ("OperacaoBinaria", "*", [
        ("OperacaoBinaria", "+", [("LiteralInteiro", "1", []), ("LiteralInteiro", "2", [])]),
        ("LiteralInteiro", "3", []),
    ])


def test_ct04_associatividade_a_esquerda():
    expr = ast_de("x = 10 - 3 - 2")["filhos"][0]["filhos"][1]
    assert expr["valor"] == "-"
    assert expr["filhos"][0]["valor"] == "-"  # (10 - 3) - 2


def test_ct05_operador_unario_e_real():
    expr = ast_de("x = -3.5")["filhos"][0]["filhos"][1]
    assert tipos(expr) == ("OperacaoUnaria", "-", [("LiteralReal", "3.5", [])])


def test_ct06_expressao_relacional():
    expr = ast_de("ok = x >= 10")["filhos"][0]["filhos"][1]
    assert expr["tipo"] == "OperacaoRelacional" and expr["valor"] == ">="


def test_ct07_if_sem_else():
    se = ast_de("if x > 0:\n    y = 1\n")["filhos"][0]
    assert se["tipo"] == "Se"
    assert [f["tipo"] for f in se["filhos"]] == ["OperacaoRelacional", "Bloco"]


def test_ct08_if_else():
    se = ast_de("if x > 0:\n    y = 1\nelse:\n    y = -1\n")["filhos"][0]
    assert [f["valor"] for f in se["filhos"][1:]] == ["então", "senão"]


def test_ct09_while():
    w = ast_de("i = 0\nwhile i < 3:\n    i = i + 1\n")["filhos"][1]
    assert w["tipo"] == "Enquanto"
    assert w["filhos"][1]["tipo"] == "Bloco"


def test_ct10_blocos_aninhados():
    codigo = "while i < 10:\n    if i == 5:\n        print(i)\n    i = i + 1\n"
    w = ast_de(codigo)["filhos"][0]
    corpo = w["filhos"][1]
    assert [c["tipo"] for c in corpo["filhos"]] == ["Se", "Atribuicao"]
    assert corpo["filhos"][0]["filhos"][1]["filhos"][0]["tipo"] == "Chamada"


def test_ct11_funcao_com_parametros_e_return():
    f = ast_de("def soma(a, b):\n    return a + b\n")["filhos"][0]
    assert f["tipo"] == "Funcao" and f["valor"] == "soma"
    assert [p["valor"] for p in f["filhos"][0]["filhos"]] == ["a", "b"]
    assert f["filhos"][1]["filhos"][0]["tipo"] == "Retorno"


def test_ct12_programa_combinado():
    codigo = (
        "def dobro(n):\n    return n * 2\n"
        "total = 0\n"
        "i = 1\n"
        "while i <= 3:\n"
        "    total = total + dobro(i)\n"
        "    i = i + 1\n"
        "if total > 10:\n    print(\"grande\")\nelse:\n    print(\"pequeno\")\n"
    )
    ast = ast_de(codigo)
    assert [c["tipo"] for c in ast["filhos"]] == ["Funcao", "Atribuicao", "Atribuicao", "Enquanto", "Se"]


def test_ct13_posicoes_da_ast_batem_com_tokens():
    codigo = "x = 1 + 2"
    r = analisar(codigo)
    soma = r["ast"]["filhos"][0]["filhos"][1]
    token_mais = [t for t in r["tokens"] if t["lexema"] == "+"][0]
    assert (soma["linha"], soma["coluna"]) == (token_mais["linha"], token_mais["coluna"])


# ---------------- erros sintáticos ----------------

def test_ct20_falta_dois_pontos():
    e, _ = erro_unico("if x > 0\n    y = 1\n")
    assert e["tipo"] == "ERRO_SINTATICO" and "':'" in e["esperado"]
    assert (e["linha"], e["coluna"]) == (1, 9)


def test_ct21_falta_parentese():
    e, _ = erro_unico("print(1\n")
    assert "')'" in e["esperado"]


def test_ct22_expressao_sem_operando():
    e, _ = erro_unico("x = \n")
    assert "operando" in e["esperado"] and e["encontrado"] == "fim da linha"


def test_ct23_else_sem_if():
    e, _ = erro_unico("else:\n    y = 1\n")
    assert "else" in e["mensagem"] and e["linha"] == 1


def test_ct24_operadores_consecutivos():
    e, _ = erro_unico("x = 1 + * 2\n")
    assert e["encontrado"] == "'*'" and e["coluna"] == 9


def test_ct25_palavra_reservada_como_nome():
    e, _ = erro_unico("if = 5\n")
    assert "palavra reservada" in e["dica"]


def test_ct26_fim_inesperado():
    e, _ = erro_unico("if x > 0:\n")
    assert e["encontrado"] == "o fim do código"


def test_ct27_indentacao_inesperada():
    e, _ = erro_unico("x = 1\n    y = 2\n")
    assert e["linha"] == 2 and "Indentação inesperada" in e["dica"]


def test_ct28_indentacao_inconsistente():
    e, _ = erro_unico("if x:\n        y = 1\n    z = 2\n")
    assert e["linha"] == 3 and "inconsistente" in e["mensagem"]


def test_ct29_comparacao_encadeada_nao_suportada():
    e, _ = erro_unico("x = a < b < c\n")
    assert "encadeadas" in e["mensagem"]


def test_ct30_for_nao_suportado():
    e, _ = erro_unico("for i in x:\n    y = 1\n")
    assert "for" in e["mensagem"]


def test_erro_sintatico_tem_campos_do_contrato():
    e, r = erro_unico("x = 1 +\n")
    assert r["ast"] is None
    for campo in ("tipo", "lexema", "linha", "coluna", "esperado", "encontrado", "mensagem", "dica"):
        assert campo in e


# ---------------- erros léxicos e decisão de projeto ----------------

def test_ct40_literal_numerico_malformado():
    tokens, erros = analisar_lexico("x = 12abc")
    assert len(erros) == 1 and "malformado" in erros[0]["mensagem"]


def test_ct41_string_nao_fechada():
    tokens, erros = analisar_lexico('x = "abc')
    assert len(erros) == 1 and "String não fechada" in erros[0]["mensagem"]


def test_ct42_parser_nao_executa_com_erro_lexico():
    r = analisar("x = @\ny = 2\n")
    assert r["etapas"] == {"lexica": "erro", "sintatica": "nao_executada", "semantica": "nao_implementada"}
    assert r["ast"] is None
    assert [e["tipo"] for e in r["erros"]] == ["ERRO_LEXICO"]


# ---------------- casos de borda ----------------

def test_ct50_apenas_comentarios_gera_programa_vazio():
    r = analisar("# só um comentário\n")
    assert r["sucesso"] and r["ast"]["filhos"] == []


def test_ct51_um_unico_comando():
    assert len(ast_de("print(1)")["filhos"]) == 1


def test_ct52_aninhamento_profundo_dentro_do_limite():
    codigo = "x = " + "(" * 50 + "1" + ")" * 50
    assert ast_de(codigo)["filhos"][0]["tipo"] == "Atribuicao"


def test_ct53_aninhamento_acima_do_limite():
    e, _ = erro_unico("x = " + "(" * 150 + "1" + ")" * 150)
    assert "limite" in e["mensagem"]


def test_ct54_quebra_de_linha_windows():
    assert ast_de("if x > 0:\r\n    y = 1\r\n")["filhos"][0]["tipo"] == "Se"


def test_tokens_estruturais_nao_alteram_tabela_de_tokens():
    codigo = "if x:\n    y = 1\n"
    tokens, _ = analisar_lexico(codigo)
    estruturais = gerar_tokens_estruturais(codigo, tokens)
    assert {t["tipo"] for t in tokens}.isdisjoint({"INDENTACAO", "DEDENTACAO", "NOVA_LINHA"})
    assert [t["tipo"] for t in estruturais].count("INDENTACAO") == 1
    assert estruturais[-1]["tipo"] == "FIM_DE_ARQUIVO"
