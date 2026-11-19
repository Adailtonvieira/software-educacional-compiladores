"""Testes automatizados da interface (navegador real, via Playwright).

Rodam FORA do Docker, contra a aplicação já em execução:

    docker compose up -d --build
    pip install pytest playwright
    playwright install chromium
    pytest tests_interface -v

Variáveis opcionais: BASE_URL (padrão http://localhost:8080) e
NAVEGADOR_CANAL (ex.: "chrome" para usar o Chrome instalado).
Se a aplicação não estiver acessível, os testes são pulados (skip).
"""

import json
import os
import urllib.request

import pytest

playwright_sync = pytest.importorskip("playwright.sync_api")

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8080")


def _app_no_ar():
    try:
        urllib.request.urlopen(BASE_URL, timeout=3)
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not _app_no_ar(), reason=f"Interface não acessível em {BASE_URL}")


@pytest.fixture(scope="module")
def navegador():
    with playwright_sync.sync_playwright() as p:
        canal = os.environ.get("NAVEGADOR_CANAL")
        b = p.chromium.launch(channel=canal) if canal else p.chromium.launch()
        yield b
        b.close()


@pytest.fixture
def pagina(navegador):
    pg = navegador.new_page(viewport={"width": 1280, "height": 900})
    erros_js = []
    pg.on("pageerror", lambda e: erros_js.append(str(e)))
    pg.goto(BASE_URL)
    pg.wait_for_timeout(300)
    yield pg
    assert erros_js == [], f"Erros de JavaScript na página: {erros_js}"
    pg.close()


def analisar(pg, codigo):
    pg.fill("#codigo", codigo)
    pg.click("#btnAnalisar")
    pg.wait_for_selector("#etapas .etapa:not(:has-text('aguardando'))")
    pg.wait_for_timeout(200)


# ---------------------------------------------------------------- fluxo principal

def test_codigo_valido_mostra_tokens_e_arvore(pagina):
    analisar(pagina, "resultado = 10 + 5 * 2")
    assert pagina.locator("#tabela-tokens tbody tr").count() == 7
    assert "Léxica: concluída" in pagina.inner_text("#etapas")
    assert "Sintática: concluída" in pagina.inner_text("#etapas")
    tipos = pagina.locator("#ast-hierarquica .no-tipo").all_inner_texts()
    assert tipos[:3] == ["Programa", "Atribuicao", "Identificador"]
    assert tipos.count("OperacaoBinaria") == 2


def test_erro_sintatico_mostra_posicao_e_nao_gera_arvore(pagina):
    analisar(pagina, "if x > 0\n    y = 1")
    msgs = pagina.inner_text("#mensagens")
    assert "Erro sintático" in msgs and "Linha 1, coluna 9" in msgs
    assert "Esperado ':' ao final do if" in msgs
    assert "Árvore não gerada" in pagina.inner_text("#ast-hierarquica")
    assert pagina.locator("#tabela-tokens tbody tr").count() == 7   # tokens continuam visíveis


def test_erro_lexico_e_distinto_do_sintatico(pagina):
    analisar(pagina, "x = @\ny = 2")
    etapas = pagina.inner_text("#etapas")
    assert "Léxica: com erros" in etapas and "Sintática: não executada" in etapas
    msgs = pagina.inner_text("#mensagens")
    assert "Erros léxicos (1)" in msgs and "Erro sintático" not in msgs
    assert "não foi executada" in msgs
    assert pagina.locator("#codigo-classificado .cat-ERRO").count() == 1


def test_entrada_vazia_e_limite_de_tamanho(pagina):
    pagina.fill("#codigo", "")
    pagina.click("#btnAnalisar")
    assert "Digite um código" in pagina.inner_text("#mensagens")
    pagina.fill("#codigo", "x = 1\n" * 900)       # 5400 caracteres
    assert "excedido" in pagina.get_attribute("#contador", "class")
    pagina.click("#btnAnalisar")
    assert "o limite é 5000" in pagina.inner_text("#mensagens")


# ---------------------------------------------------------------- interação com a árvore

def test_clicar_no_no_destaca_token_e_mostra_regra(pagina):
    analisar(pagina, "resultado = 10 + 5 * 2")
    pagina.click("#ast-hierarquica .no[data-tipo='OperacaoBinaria'] >> nth=1")   # o nó '*'
    linha = pagina.locator("#tabela-tokens tr.destacado")
    assert linha.count() == 1 and "*" in linha.inner_text()
    detalhe = pagina.inner_text("#no-detalhe")
    assert "termo =" in detalhe and "de 1:18 até 1:22" in detalhe
    sel = pagina.evaluate("() => { const c = document.getElementById('codigo'); return c.value.slice(c.selectionStart, c.selectionEnd); }")
    assert sel == "5 * 2"


def test_expandir_e_recolher(pagina):
    analisar(pagina, "if a > 1:\n    b = 2")
    pagina.click("#recolher")
    assert pagina.evaluate("() => [...document.querySelectorAll('#ast-hierarquica details')].every(d => !d.open)")
    pagina.click("#expandir")
    assert pagina.evaluate("() => [...document.querySelectorAll('#ast-hierarquica details')].every(d => d.open)")


def test_visao_grafica_tem_os_mesmos_nos(pagina):
    analisar(pagina, "def f(a):\n    return a * 2")
    n_hier = pagina.locator("#ast-hierarquica .no").count()
    pagina.click("#verGrafica")
    assert pagina.locator("#ast-grafica g.n").count() == n_hier


def test_filtro_por_tipo(pagina):
    analisar(pagina, "resultado = 10 + 5 * 2")
    pagina.select_option("#filtroTipo", "LiteralInteiro")
    assert pagina.locator("#ast-hierarquica .no.filtrado").count() == 3
    assert pagina.locator("#ast-hierarquica .no.esmaecido").count() == 5


def test_exportar_json(pagina):
    analisar(pagina, "x = 1")
    with pagina.expect_download() as d:
        pagina.click("#exportar")
    caminho = d.value.path()
    with open(caminho, encoding="utf-8") as f:
        ast = json.load(f)
    assert ast["tipo"] == "Programa" and ast["filhos"][0]["tipo"] == "Atribuicao"


def test_passo_a_passo_percorre_todos_os_nos(pagina):
    analisar(pagina, "resultado = 10 + 5 * 2")
    total = pagina.locator("#ast-hierarquica .no").count()
    pagina.click("#passoIniciar")
    assert f"Passo 1 de {total}" in pagina.inner_text("#passo-texto")
    for _ in range(total - 1):
        pagina.click("#passoProximo")
    assert f"Passo {total} de {total}" in pagina.inner_text("#passo-texto")
    assert "Programa" in pagina.inner_text("#passo-texto")
    assert pagina.locator("#ast-hierarquica .no.futuro").count() == 0
    pagina.click("#passoSair")
    assert pagina.locator("#passo-texto.oculto").count() == 1


# ---------------------------------------------------------------- consistência entre visualizações

def test_posicoes_da_arvore_coincidem_com_a_tabela(pagina):
    analisar(pagina, "i = 0\nwhile i < 3:\n    print(i)\n    i = i + 1")
    pos_tabela = set(pagina.eval_on_selector_all("#tabela-tokens tbody tr", "rs => rs.map(r => r.dataset.pos)"))
    pos_nos = pagina.eval_on_selector_all(
        "#ast-hierarquica .no:not([data-tipo='Programa'])", "ns => ns.map(n => n.dataset.noPos)")
    assert pos_nos and set(pos_nos) <= pos_tabela


def test_todos_os_exemplos_analisam_sem_quebrar(pagina):
    opcoes = pagina.eval_on_selector_all("#exemplos optgroup", "gs => gs.map(g => [g.label, [...g.children].map(o => o.textContent)])")
    for grupo, nomes in opcoes:
        for nome in nomes:
            pagina.select_option("#exemplos", label=nome)
            pagina.click("#btnAnalisar")
            pagina.wait_for_timeout(250)
            etapas = pagina.inner_text("#etapas")
            if grupo == "Válidos":
                assert "Sintática: concluída" in etapas, nome
            elif grupo == "Erros léxicos":
                assert "Léxica: com erros" in etapas, nome
            else:
                assert "Sintática: com erros" in etapas, nome


def test_tela_estreita_sem_rolagem_horizontal(navegador):
    pg = navegador.new_page(viewport={"width": 390, "height": 844})
    pg.goto(BASE_URL)
    analisar(pg, "resultado = 10 + 5 * 2")
    assert pg.evaluate("() => document.documentElement.scrollWidth <= window.innerWidth + 1")
    pg.close()


# ---------------------------------------------------------------- assistente de IA (opcional)
# Estes testes passam com ou sem o Ollama: verificam que a interface mostra a
# explicação OU um aviso de indisponibilidade, sem quebrar a análise.

def _resposta_ia(pg):
    pg.wait_for_selector("#ia-resposta:not(.oculto) .ia-rotulo:not(.ia-carregando)", timeout=200_000)
    return pg.inner_text("#ia-resposta")


def test_ia_explicar_no(pagina):
    analisar(pagina, "resultado = 10 + 5 * 2")
    pagina.click("#ast-hierarquica .no[data-tipo='OperacaoBinaria'] >> nth=1")
    pagina.click("#no-detalhe .ia-botao")
    texto = _resposta_ia(pagina)
    assert "Explicação gerada por IA" in texto or "indisponível" in texto or "não está instalado" in texto


def test_ia_entender_erro(pagina):
    analisar(pagina, "if x > 0\n    y = 1")
    pagina.click("#mensagens .ia-botao")
    texto = _resposta_ia(pagina)
    assert "Erro na linha 1, coluna 9" in texto or "Explicação gerada por IA" in texto


def test_ia_status_e_professor_virtual_visiveis(pagina):
    assert "Assistente de IA:" in pagina.inner_text("#ia-status")
    assert pagina.locator("#sugestoes button").count() >= 3
