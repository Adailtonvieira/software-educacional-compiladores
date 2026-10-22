import pytest
from app import analisar_lexico

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
