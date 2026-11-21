# Pesquisa de Preços

Coleta ofertas em marketplaces brasileiros a partir de uma planilha e devolve, para cada produto dentro da faixa pedida:

| campo | o que é |
|---|---|
| **valor** | preço anunciado (o que aparece no cartão) |
| **parcelamento** | em quantas vezes, valor da parcela e **se é sem juros** |
| **total parcelado** | parcelas × valor da parcela |
| **diferença à vista × parcelado** | quanto o parcelamento custa acima do preço anunciado |
| **link** | URL do anúncio, pronta para comprar |
| **imagem** | miniatura baixada e embutida na planilha |

Loja com suporte hoje: **Mercado Livre**, **Buscapé** e **Amazon**. Adicionar outra é uma classe de ~15 linhas (ver [Adicionar uma loja](#adicionar-uma-loja)).

---

## Instalação

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Python 3.11+ (testado no 3.14). O Selenium 4.25+ resolve o chromedriver sozinho — não precisa de `webdriver_manager`.

Navegador: usa **Brave**, **Chrome** ou **Edge** na ordem em que encontrar. Para forçar um caminho:

```powershell
python main.py --navegador "C:\Program Files\Google\Chrome\Application\chrome.exe"
```

---

## Uso

```powershell
# primeira vez: gera buscas.xlsx de exemplo
python main.py --criar-modelo

# roda tudo
python main.py

# só duas lojas, mais cartões por busca, e envia por e-mail
python main.py --lojas mercadolivre,amazon --limite 30 --email voce@dominio.com

# sem abrir janela (mais rápido, mais chance de bloqueio)
python main.py --headless

# reaproveita cookies/login entre execuções
python main.py --perfil perfil-brave
```

Saídas: `ofertas.xlsx` (com as fotos embutidas + aba **Resumo** com o menor preço por produto), `relatorio.html` (visual, clicável) e `imagens/` com as miniaturas.

### Opções

| flag | padrão | função |
|---|---|---|
| `-e, --entrada` | `buscas.xlsx` | planilha de produtos |
| `-s, --saida` | `ofertas.xlsx` | planilha de resultado |
| `--html` | `relatorio.html` | relatório visual |
| `--csv` | — | exporta CSV (`;`) também |
| `-l, --lojas` | todas | `mercadolivre,buscape,amazon` |
| `--limite` | 20 | cartões lidos por loja e produto |
| `--pausa` | 1.5 | segundos entre lojas |
| `--headless` | off | navegador invisível |
| `--navegador` | auto | caminho do executável |
| `--perfil` | — | pasta de perfil (cookies persistentes) |
| `--sem-imagens` | off | não baixa miniaturas |
| `--dir-imagens` | ao lado da saída | pasta das miniaturas |
| `--detalhar` | off | abre o anúncio quando o cartão não mostra parcelamento |
| `--debug` | off | salva o HTML das coletas vazias em `debug/` |
| `--email` | — | destinatários separados por vírgula (Outlook) |
| `--assunto` | `Ofertas encontradas` | assunto do e-mail |
| `--criar-modelo` | — | cria `buscas.xlsx` e sai |

---

## Planilha de entrada

| Nome | Termos banidos | Preço mínimo | Preço máximo | Termos obrigatórios |
|---|---|---|---|---|
| rtx 3060 | zotac, galax | 1500 | 3000 | |
| iphone 12 64 gb | mini, watch, capa | 1200 | 2500 | |
| memória ddr4 16gb | rgb, notebook | 150 | 320 | 16gb, ddr4 |

Regras:

- **Termos banidos** — com vírgula, cada item é uma frase (`usado, nao funciona`); sem vírgula, cada palavra vale sozinha (`usado recondicionado` = bane *usado* **ou** *recondicionado*).
- **Termos obrigatórios** — opcional. Vazio = o nome do produto vira a lista (todas as palavras precisam aparecer no título).
- **Preço mínimo/máximo** — vazio ou 0 = sem limite daquele lado.
- Comparação ignora acento, caixa e espaço: `16gb` casa com `16 GB`.

Aceita `.xlsx` e `.csv` (separador `;`).

---

## Como funciona

```
buscas.xlsx
   └─ entrada.py        lê e interpreta as regras
        └─ pesquisa.py   produto × loja
             ├─ lojas/mercadolivre.py
             ├─ lojas/buscape.py
             └─ lojas/amazon.py
                  ↓  cartões crus (título, preço, parcelamento, link, imagem)
             texto.py    normaliza preço e parcelamento
             filtros.py  aplica banidos/obrigatórios/faixa
                  ↓
             relatorio.py   .xlsx com fotos + .html
             imagens.py     download das miniaturas
             email_outlook.py
```

Cada loja só declara três coisas: a URL de busca, o seletor que indica "os cartões chegaram" e um coletor JavaScript que devolve os cartões. Espera, retry, parsing e normalização ficam na base — foi o que tirou a duplicação dos notebooks antigos.

**Parsers** (`texto.py`) são o núcleo. Eles lidam com o lixo real: `R$\n2.299\n,\n00`, `1.899` sem centavos, `12x de R$ 191,58 sem juros`, `10x R$ 129,90 com juros`. Quando o cartão não diz nada sobre juros, o parser compara `parcelas × valor` com o preço — se bate, é sem juros; se não há dado suficiente, grava **"não informado"** em vez de chutar.

---

## Adicionar uma loja

```python
# pesquisa_precos/lojas/minhaloja.py
from urllib.parse import quote_plus
from .base import Loja

JS = r"""
const cards = [...document.querySelectorAll('div.meu-card')];
return cards.map(c => {
  const a = c.querySelector('a');
  const img = c.querySelector('img');
  return {
    titulo: c.querySelector('.titulo')?.textContent || '',
    preco:  c.querySelector('.preco')?.textContent || '',
    parcelas: c.querySelector('.parcelas')?.textContent || '',
    texto:  c.innerText || '',
    link:   a ? a.href : '',
    imagem: img ? (img.getAttribute('data-src') || img.src) : ''
  };
});
"""

class MinhaLoja(Loja):
    chave = "minhaloja"
    nome = "Minha Loja"
    base = "https://www.minhaloja.com.br"
    seletor_espera = "div.meu-card"
    js_cartoes = JS

    def url(self, termo: str) -> str:
        return f"https://www.minhaloja.com.br/busca?q={quote_plus(termo)}"
```

Depois registre em `pesquisa_precos/lojas/__init__.py`. `texto` é o fallback: se o seletor de parcelamento falhar, o parser procura o padrão `Nx ... R$` no texto do cartão inteiro.

---

## Uso em notebook / script

```python
from pesquisa_precos.api import buscar, planilha

ofertas = buscar("rtx 3060", minimo=1500, maximo=3000, banidos="zotac, galax")
for o in ofertas:
    print(o.loja, o.preco, o.resumo_parcelamento, o.link)

planilha(ofertas, "ofertas.xlsx", html="relatorio.html")
```

---

## Bloqueios e limites

Marketplaces detectam automação. O código já remove as digitais óbvias do webdriver (`navigator.webdriver`, user-agent, `AutomationControlled`), mas:

- **Mercado Livre** serve uma página de *tráfego suspeito* para IPs de datacenter/VPN. Se aparecer `bloqueado: página de tráfego suspeito`, é a rede, não o código. Use `--perfil` com uma sessão já validada, ou rode de um IP residencial.
- **`--headless`** aumenta muito a chance de bloqueio. Prefira janela visível.
- **`--perfil perfil-brave`** guarda cookies entre execuções: o primeiro acesso pode pedir verificação manual, os seguintes não.
- **Ritmo** — `--pausa` existe para não virar martelo. Scraping agressivo gera 429 e captcha.
- **Layout** — quando um site muda de classe, a coleta volta vazia. Rode com `--debug` e compare o HTML salvo com os seletores da loja.

---

## Testes

```powershell
python -m unittest tests.test_offline -v
```

Cobrem os parsers de preço/parcelamento, os filtros, a leitura/criação da planilha e a geração de `.xlsx`, `.csv` e `.html`. Nada de rede, nada de navegador.

---

## Estrutura

```
main.py
requirements.txt
pesquisa_precos/
  config.py        opções e descoberta do navegador
  api.py           fachada para notebook (buscar/planilha)
  models.py        Oferta + derivados (total, diferença, resumo)
  texto.py         parsers de preço, parcelamento e termos
  navegador.py     Chrome/Brave/Edge, stealth, esperas, detecção de bloqueio
  lojas/           um adaptador por marketplace
  filtros.py       regras da planilha
  entrada.py       leitura/criação de buscas.xlsx
  imagens.py       download + miniatura
  relatorio.py     xlsx com fotos, html, csv, tabela de terminal
  email_outlook.py envio via Outlook (COM)
  pesquisa.py      orquestrador
tests/test_offline.py
```

`ProjetoV1.ipynb` e `ProjetoV2EmTeste.ipynb` ficam como histórico das versões em notebook.
