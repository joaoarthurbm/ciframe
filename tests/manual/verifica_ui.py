"""Verificação manual da tela de sequências, sem baixar navegador.

Usa o Chrome já instalado (headless) via DevTools Protocol para: abrir a tela,
esperar o Angular renderizar o catálogo, clicar numa sequência, cadastrar uma
nova pelo formulário e repetir o cadastro para ver o aviso de duplicata.

Como rodar (o servidor precisa estar no ar servindo a aplicação):

    CIFRAME_DB=/tmp/ciframe-ui/c.db .venv/bin/python main.py     # :5000
    .venv/bin/pip install websocket-client                       # só para este check
    .venv/bin/python tests/manual/verifica_ui.py http://127.0.0.1:5000/#/porsequencia

Sai com código 2 se o banco já tiver a sequência de teste — nesse caso use um
banco novo (`CIFRAME_DB` em um diretório temporário), porque a tela não tem
como apagar cadastro.
"""

import json
import subprocess
import sys
import time
import urllib.request

import websocket

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
PORTA_CDP = 9222
URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5000/#/porsequencia"
ACORDES_TESTE = "Dm E7 Am"
NOME_TESTE = "Dm - E7 - Am"
# quantas músicas 'Sequência Em' (Em;G) deve devolver — igual à baseline de regressão
MUSICAS_EMG = 4

DOM = r"""
(async () => {
  const texto = (sel) => {
    const el = document.querySelector(sel);
    return el ? el.textContent.trim() : '';
  };
  const itens = () => Array.from(document.querySelectorAll('.sequencia-item'));
  const nomes = () => itens().map(i => i.querySelector('.sequencia-nome').textContent.trim());
  const cards = () => Array.from(document.querySelectorAll('.music-card'));
  const esperar = async (fn, ms = 15000) => {
    const fim = Date.now() + ms;
    while (Date.now() < fim) {
      if (fn()) return true;
      await new Promise(r => setTimeout(r, 150));
    }
    return false;
  };
  const cadastrar = async (valor) => {
    const input = document.querySelector('.sequencia-form input');
    input.value = valor;
    input.dispatchEvent(new Event('input', { bubbles: true }));
    await new Promise(r => setTimeout(r, 100));
    document.querySelector('.sequencia-form button[type=submit]').click();
  };

  const renderizou = await esperar(() => itens().length > 0);
  const catalogoInicial = nomes();

  const jaExiste = catalogoInicial.includes('__NOME__');
  if (jaExiste) return JSON.stringify({ jaExiste }, null, 2);

  itens().find(i => i.querySelector('.sequencia-nome').textContent.includes('Em')).click();
  const achouResultados = await esperar(() => cards().length > 0);
  const aoClicar = {
    titulo: texto('#results h4'),
    selecionada: texto('.sequencia-selecionada'),
    musicas: cards().length,
    primeira: cards().length ? texto('.music-card .music-title') : null
  };

  await cadastrar('__ACORDES__');
  const criou = await esperar(() => nomes().length > catalogoInicial.length && cards().length > 0);
  const aposCadastro = {
    criou,
    total: nomes().length,
    entrada: nomes().find(n => n === '__NOME__') || null,
    selecionada: texto('.sequencia-selecionada'),
    musicas: cards().length,
    erro: texto('.sequencia-erro')
  };

  await cadastrar('__ACORDES__');
  const avisouDuplicata = await esperar(() => texto('.sequencia-erro') !== '');
  const voltouResultados = await esperar(() => cards().length > 0);
  const aposDuplicata = {
    avisouDuplicata,
    aviso: texto('.sequencia-erro'),
    voltouResultados,
    musicas: cards().length,
    total: nomes().length,
    inputLimpo: document.querySelector('.sequencia-form input').value === ''
  };

  return JSON.stringify({ renderizou, catalogoInicial, achouResultados, aoClicar,
                          aposCadastro, aposDuplicata }, null, 2);
})()
""".replace("__NOME__", NOME_TESTE).replace("__ACORDES__", ACORDES_TESTE)


def abrir_chrome():
    proc = subprocess.Popen(
        [CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
         "--remote-debugging-port=%d" % PORTA_CDP, "--window-size=1440,900",
         "about:blank"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(60):
        try:
            with urllib.request.urlopen("http://127.0.0.1:%d/json" % PORTA_CDP) as r:
                for pagina in json.loads(r.read().decode()):
                    if pagina.get("type") == "page":
                        return proc, pagina["webSocketDebuggerUrl"]
        except Exception:
            pass
        time.sleep(0.25)
    proc.kill()
    raise SystemExit("chrome headless não subiu (porta %d livre?)" % PORTA_CDP)


def main():
    if not URL.startswith("http"):
        raise SystemExit("passe a URL da tela, ex.: http://127.0.0.1:5000/#/porsequencia")

    proc, ws_url = abrir_chrome()
    ws = websocket.create_connection(ws_url, timeout=30)
    seq = [0]

    def enviar(method, **params):
        seq[0] += 1
        ws.send(json.dumps({"id": seq[0], "method": method, "params": params}))
        while True:
            msg = json.loads(ws.recv())
            if msg.get("id") == seq[0]:
                return msg.get("result", {})

    try:
        enviar("Page.enable")
        enviar("Runtime.enable")
        enviar("Page.navigate", url=URL)
        time.sleep(2.5)

        resultado = enviar("Runtime.evaluate", expression=DOM, awaitPromise=True,
                           returnByValue=True)
        if "exceptionDetails" in resultado:
            print(json.dumps(resultado["exceptionDetails"], indent=2, ensure_ascii=False))
            return 1

        texto = resultado["result"]["value"]
        print(texto)
        dados = json.loads(texto)

        if dados.get("jaExiste"):
            print("\nbanco já tem '%s': rode com um CIFRAME_DB novo" % NOME_TESTE,
                  file=sys.stderr)
            return 2

        ok = (
            dados["renderizou"]
            and len(dados["catalogoInicial"]) == 6
            and dados["aoClicar"]["selecionada"] == "Sequência Em"
            and dados["aoClicar"]["musicas"] == MUSICAS_EMG
            and dados["aposCadastro"]["criou"]
            and dados["aposCadastro"]["total"] == 7
            and dados["aposCadastro"]["entrada"] == NOME_TESTE
            and dados["aposCadastro"]["musicas"] > 0
            and dados["aposDuplicata"]["avisouDuplicata"]
            and dados["aposDuplicata"]["total"] == 7
            and dados["aposDuplicata"]["inputLimpo"]
        )
        print("\nUI OK" if ok else "\nUI FALHOU")
        return 0 if ok else 1
    finally:
        ws.close()
        proc.kill()


if __name__ == "__main__":
    sys.exit(main())
