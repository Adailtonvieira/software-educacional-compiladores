"""Testes do endpoint POST /api/analisar (contrato da Etapa 4).

Garante compatibilidade com o contrato da Etapa 3 (sucesso, tokens, erros)
e verifica os campos novos (ast, etapas) e a validação de entrada.
"""

import pytest

from app import app, MAX_CARACTERES


@pytest.fixture
def cliente():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def post(cliente, corpo):
    return cliente.post("/api/analisar", json=corpo)


def test_contrato_etapa3_preservado(cliente):
    r = post(cliente, {"codigo": "x = 10"})
    assert r.status_code == 200
    dados = r.get_json()
    assert dados["sucesso"] is True
    assert [t["tipo"] for t in dados["tokens"]] == ["IDENTIFICADOR", "OPERADOR", "LITERAL_INTEIRO"]
    assert dados["erros"] == []


def test_campos_novos_ast_e_etapas(cliente):
    dados = post(cliente, {"codigo": "x = 10"}).get_json()
    assert dados["ast"]["tipo"] == "Programa"
    assert dados["etapas"] == {"lexica": "ok", "sintatica": "ok", "semantica": "nao_implementada"}


def test_erro_lexico_mantem_formato_da_etapa3(cliente):
    dados = post(cliente, {"codigo": "x = @"}).get_json()
    assert dados["sucesso"] is False
    assert dados["erros"][0] == {
        "tipo": "ERRO_LEXICO", "lexema": "@", "linha": 1, "coluna": 5,
        "mensagem": "Caractere não reconhecido: '@'",
    }


def test_erro_sintatico_via_api(cliente):
    dados = post(cliente, {"codigo": "if x > 0\n    y = 1"}).get_json()
    assert dados["sucesso"] is False
    assert dados["erros"][0]["tipo"] == "ERRO_SINTATICO"
    assert dados["etapas"]["sintatica"] == "erro"


def test_codigo_vazio(cliente):
    r = post(cliente, {"codigo": ""})
    assert r.status_code == 400 and "vazio" in r.get_json()["erro"]


def test_codigo_so_com_espacos(cliente):
    r = post(cliente, {"codigo": "   \n\t  "})
    assert r.status_code == 400


def test_codigo_acima_do_limite(cliente):
    r = post(cliente, {"codigo": "x = 1\n" * (MAX_CARACTERES // 6 + 10)})
    assert r.status_code == 400 and "limite" in r.get_json()["erro"]


def test_codigo_nao_texto(cliente):
    r = post(cliente, {"codigo": 123})
    assert r.status_code == 400


def test_requisicao_sem_json(cliente):
    r = cliente.post("/api/analisar", data="x = 1", content_type="text/plain")
    assert r.status_code == 400


def test_endpoint_acumula_varios_erros_lexicos(cliente):
    dados = post(cliente, {"codigo": "a = @\nb = $\nc = 3"}).get_json()
    assert dados["sucesso"] is False
    assert [(e["lexema"], e["linha"], e["coluna"]) for e in dados["erros"]] == [("@", 1, 5), ("$", 2, 5)]
    assert [t["lexema"] for t in dados["tokens"]] == ["a", "=", "b", "=", "c", "=", "3"]
    assert dados["etapas"]["sintatica"] == "nao_executada"


def test_endpoint_retorna_tokens_com_posicoes(cliente):
    dados = post(cliente, {"codigo": "if x >= 10:\n    y = 'ok'"}).get_json()
    assert [(t["tipo"], t["lexema"], t["linha"], t["coluna"]) for t in dados["tokens"]] == [
        ("PALAVRA_RESERVADA", "if", 1, 1), ("IDENTIFICADOR", "x", 1, 4), ("OPERADOR", ">=", 1, 6),
        ("LITERAL_INTEIRO", "10", 1, 9), ("DELIMITADOR", ":", 1, 11),
        ("IDENTIFICADOR", "y", 2, 5), ("OPERADOR", "=", 2, 7), ("LITERAL_STRING", "'ok'", 2, 9),
    ]
