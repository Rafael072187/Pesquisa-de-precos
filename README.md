<center>
  <h1 style="font-size:2.4em; margin-bottom:0.1em;">🛒 Pesquisa de Preços Pro</h1>
  <p style="margin-top:0.2em; font-size:1.05em; color:#555;">
    Automação em <b>Python + Selenium</b> que pesquisa produtos em marketplaces
    brasileiros e devolve <b>preço, parcelamento, se é sem juros, link de compra e imagem</b>
    — com planilha pronta, relatório visual e envio por e-mail.
  </p>
  <p style="margin-top:0.1em; font-size:0.95em; color:#777;">
    Repositório <b>Pesquisa-de-precos</b> · versão <b>3.0</b>
  </p>
  <p>
    <a href="https://github.com/Rafael072187/Pesquisa-de-precos" style="background:#24292F;color:#fff;padding:8px 14px;border-radius:8px;text-decoration:none;font-weight:600;">
      🔗 Repositório no GitHub
    </a>
  </p>
</center>

<hr>

## 🧭 Tabela de Conteúdos

- [Descrição](#-descrição)
- [Funcionalidades](#-funcionalidades)
- [Requisitos](#-requisitos)
- [Instalação](#-instalação)
- [Como usar](#-como-usar)
- [Planilha de entrada](#-planilha-de-entrada)
- [Saídas geradas](#-saídas-geradas)
- [Lojas suportadas](#-lojas-suportadas)
- [Uso em notebook e script](#-uso-em-notebook-e-script)
- [Tecnologias](#-tecnologias)
- [Solução de problemas](#-solução-de-problemas)
- [Como contribuir](#-como-contribuir)
- [Autor](#-autor)
- [Observações](#-observações)

---

## 📘 Descrição

<details>
<summary><b>Resumo</b></summary>

O **Pesquisa de Preços Pro** é a evolução dos notebooks `ProjetoV1` e `ProjetoV2EmTeste`:
o que era uma sequência de células virou um **pacote Python** com camadas separadas,
uma **loja por arquivo** e uma CLI de verdade.

Você preenche uma planilha com o produto, os termos que quer evitar e a faixa de preço.
O programa abre o navegador, pesquisa em cada marketplace, filtra o que não serve e
devolve uma linha por oferta com:

- **valor** anunciado;
- **em quantas vezes** parcela e **quanto** fica cada parcela;
- **se é sem juros**, com juros ou não informado;
- **total parcelado** e quanto o parcelamento custa acima do preço à vista;
- **link** direto para comprar;
- **imagem** do produto baixada e embutida na planilha.

O resultado sai em três formatos ao mesmo tempo: `ofertas.xlsx` (com as fotos dentro e
uma aba **Resumo** com o menor preço de cada produto), `relatorio.html` (cards clicáveis
para conferir no navegador) e, se você pedir, um **e-mail pelo Outlook** com a planilha
anexada e as ofertas no corpo.

</details>

---

## ✨ Funcionalidades

<details open>
<summary><b>O que o programa faz</b></summary>

| Recurso | Descrição |
| --- | --- |
| 🏬 **Busca multi-loja** | Mercado Livre, Buscapé e Amazon na mesma rodada, com o mesmo filtro para todas. |
| 💰 **Preço normalizado** | Entende `R$ 2.299,00`, `R$ 1.899`, `R$\n2.299\n,\n00` e o `2.299` sem centavos. |
| 💳 **Parcelamento completo** | Extrai `12x R$ 191,58 sem juros` e devolve parcelas, valor da parcela e o total. |
| 🧾 **Sem juros ou com juros** | Lê o texto do anúncio; se ele cala, compara `parcelas × valor` com o preço. Sem dado, grava **não informado** em vez de chutar. |
| 📉 **Diferença à vista × parcelado** | Mostra em % quanto o parcelamento custa acima do preço anunciado. |
| 🔗 **Link pronto para comprar** | URL do anúncio, com hiperlink clicável na planilha. |
| 🖼️ **Imagem embutida** | Miniatura baixada do CDN e ancorada na coluna **Imagem** da planilha. |
| 📊 **Aba Resumo** | Segunda aba com o menor preço por produto, a loja e o parcelamento vencedor. |
| 🌐 **Relatório HTML** | Cards com foto, preço, selo verde/vermelho de juros e botão **Ver oferta**. |
| 📤 **E-mail pelo Outlook** | Planilha anexada + tabela HTML no corpo, via COM (sem SMTP, sem senha). |
| 🚫 **Filtros da planilha** | Termos banidos, termos obrigatórios e faixa de preço, com comparação sem acento e sem caixa. |
| 🔁 **Deduplicação** | O mesmo anúncio repetido em dois cartões entra uma vez só. |
| 🧯 **Isolamento por loja** | Um site fora do ar não derruba a rodada; a próxima loja continua. |
| 🛡️ **Detecção de bloqueio** | Reconhece a página de verificação do site, avisa e descarta a loja nas buscas seguintes. |
| 🍪 **Perfil persistente** | `--perfil` reaproveita cookies entre execuções e reduz o captcha. |
| 🧪 **Testes offline** | 17 testes de parser, filtro e relatório que rodam sem rede e sem navegador. |
| 💻 **API para notebook** | `buscar()` e `planilha()` para usar em célula, sem passar pela CLI. |

</details>

<details>
<summary><b>O que mudou em relação aos notebooks</b></summary>

| Antes (ProjetoV1 / ProjetoV2) | Agora (versão atual) |
| --- | --- |
| Células soltas, precisava rodar na ordem | Pacote com CLI: `python main.py` |
| Só preço e link | Preço, parcelas, juros, total, diferença, link e imagem |
| Classes com hash copiadas à mão no notebook | Seletores ancorados em `data-testid` + coletor JavaScript |
| Duas cópias da função de filtro | `texto.py` e `filtros.py`, testados |
| `.xlsx` sem formatação | Planilha com cabeçalho, filtro, hiperlink, moeda e fotos |
| Sem relatório visual | `relatorio.html` com cards |
| E-mail com caminho fixo e sem anexo real | Anexo da planilha + corpo HTML |
| `pandas` como dependência | Só `openpyxl` para planilha |
| Um site quebrado derrubava tudo | Erro isolado por loja, com aviso claro |
| Sem detecção de captcha | Página de bloqueio reconhecida e reportada |

</details>

---

## 📋 Requisitos

| Requisito | Versão / Observação |
| --- | --- |
| **Python** | 3.11 ou superior (testado no 3.14) |
| **selenium** | 4.25+ — o Selenium Manager baixa o chromedriver sozinho |
| **openpyxl** | Leitura de `buscas.xlsx` e geração de `ofertas.xlsx` |
| **pillow** | Miniatura das imagens antes de embutir na planilha |
| **pywin32** | Apenas para o envio por e-mail (Outlook via COM) |
| **Navegador** | Brave, Chrome ou Edge instalado — o programa procura sozinho |

> Sem `pywin32` ou sem Outlook configurado, tudo funciona menos o `--email`.
> A planilha e o relatório são gerados do mesmo jeito.

---

## 🛠️ Instalação

<details>
<summary><b>Passo a passo (Windows)</b></summary>

### 1. Clone o repositório

```bash
git clone https://github.com/Rafael072187/Pesquisa-de-precos.git
cd Pesquisa-de-precos
```

### 2. Crie e ative um ambiente virtual

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

```bash
# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instale as dependências

```powershell
pip install -r requirements.txt
```

### 4. Confira o navegador

O programa usa, nesta ordem: **Brave**, **Chrome**, **Edge**. Para forçar um caminho:

```powershell
python main.py --navegador "C:\Program Files\Google\Chrome\Application\chrome.exe"
```

Também aceita variável de ambiente: `BRAVE_PATH`, `CHROME_PATH` ou `EDGE_PATH`.

### 5. Gere a planilha de exemplo

```powershell
python main.py --criar-modelo
```

</details>

---

## 🚀 Como usar

<details open>
<summary><b>Rodando a pesquisa</b></summary>

### 1. Preencha `buscas.xlsx`

O `--criar-modelo` já cria a planilha com três exemplos. Troque pelos seus produtos.

### 2. Rode

```powershell
python main.py
```

### 3. Acompanhe no terminal

```
[1/3] iphone 12 64 gb  (R$ 1200–2500)
    Buscapé           5 lidos    2 aprovados  (4.8s)
    Amazon            5 lidos    4 aprovados  (4.4s)

LOJA                 PREÇO  PARCELAMENTO                      TÍTULO
------------------------------------------------------------------------
Amazon         R$ 1.469,61  12x R$ 128,91 sem juros           Apple iPhone 12 (64 GB) - Preto…
Buscapé        R$ 1.546,96  à vista                           Celular Apple iPhone 12 64GB 4 GB Usado
```

### 4. Abra o resultado

- `ofertas.xlsx` — planilha com as fotos e a aba **Resumo**;
- `relatorio.html` — cards clicáveis no navegador;
- `imagens/` — miniaturas baixadas.

### 5. Exemplos de uso

```powershell
# só duas lojas, mais cartões por busca
python main.py --lojas mercadolivre,amazon --limite 30

# manda por e-mail com a planilha anexada
python main.py --email voce@dominio.com --assunto "Ofertas de hoje"

# janela invisível (mais rápido, mais chance de bloqueio)
python main.py --headless

# reaproveita a sessão já validada no navegador
python main.py --perfil perfil-brave

# abre o anúncio quando o cartão não mostra parcelamento
python main.py --detalhar
```

### 6. Opções da linha de comando

| Flag | Padrão | Função |
| --- | --- | --- |
| `-e, --entrada` | `buscas.xlsx` | planilha de produtos |
| `-s, --saida` | `ofertas.xlsx` | planilha de resultado |
| `--html` | `relatorio.html` | relatório visual |
| `--csv` | — | exporta CSV (`;`) também |
| `-l, --lojas` | todas | `mercadolivre,buscape,amazon` |
| `--limite` | 20 | cartões lidos por loja e produto |
| `--pausa` | 1.5 | segundos entre lojas |
| `--headless` | desligado | navegador invisível |
| `--navegador` | automático | caminho do executável |
| `--perfil` | — | pasta de perfil (cookies persistentes) |
| `--sem-imagens` | desligado | não baixa miniaturas |
| `--dir-imagens` | ao lado da saída | pasta das miniaturas |
| `--detalhar` | desligado | abre o anúncio quando falta parcelamento |
| `--debug` | desligado | salva o HTML das coletas vazias em `debug/` |
| `--email` | — | destinatários separados por vírgula |
| `--assunto` | `Ofertas encontradas` | assunto do e-mail |
| `--criar-modelo` | — | cria `buscas.xlsx` e sai |

</details>

---

## 📄 Planilha de entrada

<details open>
<summary><b>Formato do buscas.xlsx</b></summary>

| Nome | Termos banidos | Preço mínimo | Preço máximo | Termos obrigatórios |
| --- | --- | --- | --- | --- |
| rtx 3060 | zotac, galax | 1500 | 3000 | |
| iphone 12 64 gb | mini, watch, capa | 1200 | 2500 | |
| memória ddr4 16gb | rgb, notebook | 150 | 320 | 16gb, ddr4 |

Regras dos filtros:

- **Termos banidos** — com vírgula, cada item é uma frase (`usado, nao funciona`);
  sem vírgula, cada palavra vale sozinha (`usado recondicionado` bane *usado* **ou**
  *recondicionado*).
- **Termos obrigatórios** — opcional. Vazio, o nome do produto vira a lista: todas as
  palavras precisam aparecer no título.
- **Preço mínimo / máximo** — vazio ou 0 significa "sem limite" daquele lado.
- A comparação ignora acento, caixa e espaço: `16gb` casa com `16 GB`.
- Aceita `.xlsx` e `.csv` (separador `;`). Linhas de observação no fim da planilha
  são ignoradas.

</details>

---

## 📁 Saídas geradas

<details open>
<summary><b>Exemplos reais de saída</b></summary>

### Arquivos na pasta

```
C:\Users\SeuNome\Documents\PesquisaDePrecos\
├── buscas.xlsx          ← você preenche
├── ofertas.xlsx         ← resultado com as fotos
├── relatorio.html       ← cards clicáveis
└── imagens\
    ├── 3f9a1c77b0d24e51.jpg
    └── 8c2e5a90d1f7b643.jpg
```

### Colunas de `ofertas.xlsx`

| Coluna | Exemplo |
| --- | --- |
| Produto buscado | `rtx 3060` |
| Loja | `Amazon` |
| Título | `Placa De Vídeo Husky Alpha RTX 3060, 12GB, GDDR6` |
| Preço (R$) | `2.599,99` |
| Parcelas | `10` |
| Valor da parcela (R$) | `275,86` |
| Sem juros | `sem juros` / `com juros` / `à vista` / `não informado` |
| Total parcelado (R$) | `2.758,60` |
| Diferença à vista × parcelado (%) | `0,00` |
| Resumo do parcelamento | `10x R$ 275,86 sem juros` |
| Link | `https://www.amazon.com.br/dp/...` |
| Imagem (URL) | `https://m.media-amazon.com/...jpg` |
| Imagem | *(miniatura embutida)* |

### Aba **Resumo**

Uma linha por produto, com a melhor oferta já escolhida:

| Produto | Ofertas | Menor preço | Loja | Parcelamento |
| --- | --- | --- | --- | --- |
| rtx 3060 | 5 | R$ 2.495,53 | Amazon | 10x R$ 255,36 sem juros |
| iphone 12 64 gb | 6 | R$ 1.469,61 | Amazon | 12x R$ 128,91 sem juros |

> Quando o site diz "sem juros" mas o total parcelado é maior que o preço anunciado,
> a coluna **Diferença** mostra a distância entre o preço à vista e o parcelado — é
> comum o marketplace anunciar o valor do Pix e parcelar sobre o preço cheio.

</details>

---

## 🏬 Lojas suportadas

<details>
<summary><b>O que cada loja entrega</b></summary>

| Loja | Chave | Preço | Parcelamento | Imagem | Observação |
| --- | --- | --- | --- | --- | --- |
| **Mercado Livre** | `mercadolivre` | ✅ | ✅ | ✅ | Serve página de *tráfego suspeito* para IP de datacenter/VPN |
| **Buscapé** | `buscape` | ✅ | ✅ | ✅ | Cartão traz `installment` e `interest` separados |
| **Amazon** | `amazon` | ✅ | ✅ | ✅ | Parcelamento vem no texto do cartão |

Adicionar uma loja é uma classe de ~15 linhas em `pesquisa_precos/lojas/` e uma linha
no registro. O contrato é sempre o mesmo: **URL de busca**, **seletor de espera** e um
**coletor JavaScript** que devolve `{titulo, preco, parcelas, texto, link, imagem}`.

</details>

---

## 💻 Uso em notebook e script

<details>
<summary><b>Sem passar pela CLI</b></summary>

```python
from pesquisa_precos.api import buscar, planilha

ofertas = buscar("rtx 3060", minimo=1500, maximo=3000, banidos="zotac, galax")

for o in ofertas:
    print(o.loja, o.preco, o.resumo_parcelamento, o.link)

planilha(ofertas, "ofertas.xlsx", html="relatorio.html")
```

Cada `Oferta` carrega `preco`, `parcelas`, `valor_parcela`, `sem_juros`,
`total_parcelado`, `custo_credito_pct`, `link` e `imagem`.

</details>

---

## 🧰 Tecnologias

<details>
<summary><b>Stack principal</b></summary>

| Tecnologia | Uso no projeto |
| --- | --- |
| **Python** | Linguagem principal |
| **Selenium** | Controle do navegador, esperas explícitas e execução de JavaScript |
| **Selenium Manager** | Resolve o chromedriver sem `webdriver_manager` |
| **openpyxl** | Leitura da planilha de entrada e geração da de saída |
| **Pillow** | Redimensionamento das miniaturas |
| **urllib** | Download das imagens, sem dependência extra |
| **argparse** | Interface de linha de comando |
| **dataclasses** | Modelo `Oferta` e `Config` |
| **unittest** | Testes offline dos parsers e do relatório |
| **win32com** | Envio do e-mail pelo Outlook instalado |

</details>

---

## 🩺 Solução de problemas

<details>
<summary><b>Erros comuns</b></summary>

**"Planilha de buscas não encontrada: buscas.xlsx"**
Rode `python main.py --criar-modelo` para gerar o modelo, ou aponte o caminho com
`-e "C:\caminho\buscas.xlsx"`.

**`bloqueado: página de tráfego suspeito` (Mercado Livre)**
É a rede, não o código: o site serve essa página para IP de datacenter/VPN, até em
requisição HTTP simples. Use um IP residencial, ou `--perfil perfil-brave` depois de
resolver a verificação uma vez na janela visível.

**`nenhum cartão encontrado (layout mudou ou busca vazia)`**
O site trocou as classes. Rode com `--debug`: o HTML da coleta vai para `debug/` e dá
para comparar com os seletores da loja em `pesquisa_precos/lojas/`.

**Tudo volta vazio quando uso `--headless`**
Headless aumenta muito a chance de bloqueio. Prefira a janela visível; deixe o headless
para testes rápidos.

**A planilha sai sem as fotos**
Algumas imagens vêm de CDN que exige referer ou está bloqueado para o seu IP. A linha
continua válida com a URL na coluna **Imagem (URL)**. Rode com `--sem-imagens` se
preferir não baixar nada.

**Uma oferta aparece como "à vista" mas o site parcela**
O cartão não trazia o texto de parcelamento. Rode com `--detalhar`: o programa abre o
anúncio e lê o parcelamento na página do produto (custa uma requisição por oferta).

**"falha no e-mail: Outlook não respondeu ao COM"**
O Outlook precisa estar instalado e com conta configurada. Alternativa: use `--csv` ou
o `relatorio.html` e envie você mesmo.

**Acentos estranhos no terminal (`Buscap�`)**
É a página de código do console do Windows, não o programa. Os arquivos `.xlsx` e
`.html` saem em UTF-8 correto. No Windows Terminal os acentos aparecem normalmente.

</details>

---

## 🤝 Como contribuir

<details>
<summary><b>Guia rápido</b></summary>

1. Faça um fork do repositório.
2. Crie uma branch:

   ```bash
   git checkout -b feature/nova-loja
   ```

3. Implemente a melhoria. Algumas ideias que ainda faltam:
   - novas lojas (Magalu, Pichau, Terabyte, Americanas);
   - paginação de resultados (hoje lê a primeira página);
   - histórico de preços entre execuções, para achar queda real;
   - agendamento diário com entrega por e-mail ou Telegram;
   - cache de imagens por URL, para rodadas repetidas;
   - testes de integração com HTML salvo de cada site.

4. Commit e push:

   ```bash
   git commit -m "feat: adiciona loja Pichau"
   git push origin feature/nova-loja
   ```

5. Abra um Pull Request detalhando a mudança.

</details>

---

## 👤 Autor

<details>
<summary><b>Contato</b></summary>

**Rafael Bittencourt de Araújo** — desenvolvedor do projeto.

- GitHub: [github.com/Rafael072187](https://github.com/Rafael072187)
- Repositório: [Pesquisa-de-precos](https://github.com/Rafael072187/Pesquisa-de-precos)

</details>

---

## 📝 Observações

- ✅ Projeto prático de automação de pesquisa de preços com Python, Selenium e openpyxl.
- ✅ O parcelamento é tratado como dado, não como enfeite: parcelas, valor, juros e total
  ficam em colunas separadas e o parser nunca inventa o que o site não informou.
- ✅ Os notebooks `ProjetoV1.ipynb` e `ProjetoV2EmTeste.ipynb` ficam no repositório como
  histórico das versões anteriores.
- ⚠️ **Aviso de uso:** os marketplaces têm termos próprios sobre coleta automatizada.
  Use com moderação (`--pausa`, `--limite`), apenas para comparar preços de interesse
  pessoal, e respeite os limites de cada site.

<p align="center" style="margin-top:18px;">
  <a href="https://github.com/Rafael072187/Pesquisa-de-precos" style="background:#0b5fff;color:#fff;padding:10px 18px;border-radius:8px;text-decoration:none;font-weight:600;">
    Ver repositório
  </a>
</p>

<p align="center" style="margin-top:14px;color:#666;">
  README atualizado com base no comportamento real da versão <b>3.0</b> do projeto.
</p>
