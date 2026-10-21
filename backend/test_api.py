import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_analise_sucesso(client):
    """Testa envio válido de código"""
    resposta = client.post('/api/analisar', json={"codigo": "x = 10"})
    assert resposta.status_code == 200
    assert resposta.json['mensagem'] == "Código recebido e validado com sucesso pelo backend!"
    assert resposta.json['recebido'] == "x = 10"

def test_analise_codigo_vazio(client):
    """Testa envio de string vazia"""
    resposta = client.post('/api/analisar', json={"codigo": ""})
    assert resposta.status_code == 400
    assert 'erro' in resposta.json

def test_analise_apenas_espacos(client):
    """Testa envio de apenas espaços em branco"""
    resposta = client.post('/api/analisar', json={"codigo": "   \n\t  "})
    assert resposta.status_code == 400
    assert 'erro' in resposta.json

def test_analise_sem_json(client):
    """Testa requisição sem formato JSON"""
    resposta = client.post('/api/analisar', data="texto qualquer")
    assert resposta.status_code == 400
