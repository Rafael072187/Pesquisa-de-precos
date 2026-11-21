# language: Python 3.11+, file: pesquisa_precos/relatorio.py
from __future__ import annotations

import csv
import html
from datetime import datetime
from pathlib import Path

from openpyxl import Workbook
from openpyxl.drawing.image import Image as XLImage
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from .models import COLUNAS, Oferta, agrupar_por_produto, melhor_oferta
from .texto import formatar_reais

VERDE = "047857"
VERMELHO = "B91C1C"
CINZA = "6B7280"


# ------------------------------------------------------------------ xlsx


def salvar_xlsx(
    ofertas: list[Oferta],
    caminho: str | Path,
    miniaturas: dict[int, Path] | None = None,
) -> Path:
    """Planilha com uma linha por oferta e a foto do produto embutida na coluna M."""
    destino = Path(caminho)
    miniaturas = miniaturas or {}

    wb = Workbook()
    ws = wb.active
    ws.title = "Ofertas"

    cabecalho = COLUNAS + ["Imagem"]
    ws.append(cabecalho)

    larguras = [26, 14, 58, 13, 10, 17, 15, 17, 17, 32, 46, 40, 13]
    for i, largura in enumerate(larguras, start=1):
        ws.column_dimensions[get_column_letter(i)].width = largura

    fill_cabecalho = PatternFill("solid", fgColor="111827")
    for celula in ws[1]:
        celula.font = Font(bold=True, color="FFFFFF", size=10)
        celula.fill = fill_cabecalho
        celula.alignment = Alignment(
            vertical="center", horizontal="center", wrap_text=True
        )
    ws.row_dimensions[1].height = 30

    fina = Side(style="thin", color="E5E7EB")
    borda = Border(left=fina, right=fina, top=fina, bottom=fina)

    for indice, oferta in enumerate(ofertas):
        linha = oferta.para_linha()
        valores = [linha[coluna] for coluna in COLUNAS]
        ws.append(valores)
        r = ws.max_row

        ws.row_dimensions[r].height = 50 if indice in miniaturas else 18
        for coluna in range(1, len(COLUNAS) + 1):
            celula = ws.cell(row=r, column=coluna)
            celula.border = borda
            celula.alignment = Alignment(vertical="center", wrap_text=coluna in (3, 10))

        ws.cell(row=r, column=4).number_format = "R$ #,##0.00"
        ws.cell(row=r, column=6).number_format = "R$ #,##0.00"
        ws.cell(row=r, column=8).number_format = "R$ #,##0.00"
        ws.cell(row=r, column=9).number_format = '0.00"%"'

        if oferta.sem_juros is True:
            ws.cell(row=r, column=7).font = Font(color=VERDE, bold=True)
        elif oferta.sem_juros is False:
            ws.cell(row=r, column=7).font = Font(color=VERMELHO, bold=True)
        else:
            ws.cell(row=r, column=7).font = Font(color=CINZA)

        if oferta.link:
            celula_link = ws.cell(row=r, column=11)
            celula_link.hyperlink = oferta.link
            celula_link.font = Font(color="1D4ED8", underline="single", size=9)

        caminho_imagem = miniaturas.get(indice)
        if caminho_imagem and caminho_imagem.exists():
            try:
                imagem = XLImage(str(caminho_imagem))
                escala = 64 / max(imagem.width, imagem.height)
                imagem.width = int(imagem.width * escala)
                imagem.height = int(imagem.height * escala)
                ws.add_image(imagem, f"M{r}")
            except Exception:
                pass

    ws.freeze_panes = "D2"
    ws.auto_filter.ref = f"A1:M{max(ws.max_row, 1)}"

    _aba_resumo(wb, ofertas)
    destino.parent.mkdir(parents=True, exist_ok=True)
    wb.save(destino)
    return destino


def _aba_resumo(wb: Workbook, ofertas: list[Oferta]) -> None:
    ws = wb.create_sheet("Resumo")
    ws.append(["Produto", "Ofertas", "Menor preço", "Loja", "Parcelamento", "Link"])

    for i, largura in enumerate([30, 10, 15, 16, 34, 60], start=1):
        ws.column_dimensions[get_column_letter(i)].width = largura

    for celula in ws[1]:
        celula.font = Font(bold=True, color="FFFFFF")
        celula.fill = PatternFill("solid", fgColor="111827")

    for produto, lista in agrupar_por_produto(ofertas).items():
        melhor = melhor_oferta(lista)
        if not melhor:
            continue
        ws.append(
            [
                produto,
                len(lista),
                melhor.preco,
                melhor.loja,
                melhor.resumo_parcelamento,
                melhor.link,
            ]
        )
        r = ws.max_row
        ws.cell(row=r, column=3).number_format = "R$ #,##0.00"
        if melhor.link:
            ws.cell(row=r, column=6).hyperlink = melhor.link
            ws.cell(row=r, column=6).font = Font(
                color="1D4ED8", underline="single", size=9
            )

    ws.freeze_panes = "A2"


# ------------------------------------------------------------------ html

_CSS = """
:root{color-scheme:light}
*{box-sizing:border-box}
body{margin:0;padding:28px 20px 60px;background:#f4f5f7;
     font-family:"Segoe UI",Roboto,Helvetica,Arial,sans-serif;color:#111827}
header{max-width:1180px;margin:0 auto 26px}
h1{font-size:22px;margin:0 0 6px;letter-spacing:-.3px}
.meta{font-size:13px;color:#6b7280}
.grupo{max-width:1180px;margin:0 auto 34px}
.grupo h2{font-size:15px;text-transform:uppercase;letter-spacing:.08em;
          color:#374151;border-bottom:2px solid #d1d5db;padding-bottom:8px;margin:0 0 16px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(258px,1fr));gap:16px}
.card{background:#fff;border:1px solid #e5e7eb;border-radius:10px;overflow:hidden;
      display:flex;flex-direction:column;box-shadow:0 1px 2px rgba(16,24,40,.05)}
.card .foto{height:158px;background:#fff;display:flex;align-items:center;justify-content:center;
            border-bottom:1px solid #f1f2f4;padding:10px}
.card .foto img{max-width:100%;max-height:100%;object-fit:contain}
.card .corpo{padding:12px 14px 14px;display:flex;flex-direction:column;gap:8px;flex:1}
.loja{font-size:11px;text-transform:uppercase;letter-spacing:.09em;color:#6b7280;font-weight:600}
.titulo{font-size:13px;line-height:1.35;color:#111827;min-height:52px;
        display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}
.preco{font-size:21px;font-weight:700;letter-spacing:-.5px}
.parc{font-size:12.5px;font-weight:600;padding:5px 8px;border-radius:6px;display:inline-block}
.parc.ok{background:#ecfdf5;color:#047857}
.parc.juros{background:#fef2f2;color:#b91c1c}
.parc.neutro{background:#f3f4f6;color:#4b5563}
.rodape{margin-top:auto;display:flex;align-items:center;justify-content:space-between;gap:10px}
.custo{font-size:11px;color:#9ca3af;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.sem-foto{font-size:10.5px;color:#c7cbd2;letter-spacing:.12em;text-transform:uppercase}
.btn{background:#111827;color:#fff;text-decoration:none;font-size:12px;font-weight:600;
     padding:7px 12px;border-radius:6px;white-space:nowrap}
.btn:hover{background:#374151}
.vazio{max-width:1180px;margin:40px auto;color:#6b7280;font-size:14px}
"""


def _src_imagem(
    oferta: Oferta, indice: int, miniaturas: dict[int, Path], base_dir: Path
) -> str:
    local = miniaturas.get(indice)
    if local and local.exists():
        try:
            return html.escape(local.relative_to(base_dir).as_posix())
        except ValueError:
            return html.escape(local.as_posix())
    return html.escape(oferta.imagem or "")


def _card(
    oferta: Oferta, indice: int, miniaturas: dict[int, Path], base_dir: Path
) -> str:
    if oferta.sem_juros is True:
        classe = "ok"
    elif oferta.sem_juros is False:
        classe = "juros"
    else:
        classe = "neutro"

    custo = oferta.custo_credito_pct
    custo_txt = ""
    if custo and custo > 0.01:
        pct = f"{custo:.2f}".replace(".", ",")
        custo_txt = f"{formatar_reais(oferta.total_parcelado)} (+{pct}%)"
    elif oferta.parcelas > 1 and oferta.sem_juros is True:
        custo_txt = f"total {formatar_reais(oferta.total_parcelado)}"

    src = _src_imagem(oferta, indice, miniaturas, base_dir)
    foto = (
        f'<img src="{src}" alt="" loading="lazy">'
        if src
        else '<span class="sem-foto">sem imagem</span>'
    )

    return f"""<article class="card">
  <div class="foto">{foto}</div>
  <div class="corpo">
    <span class="loja">{html.escape(oferta.loja)}</span>
    <div class="titulo">{html.escape(oferta.titulo)}</div>
    <div class="preco">{formatar_reais(oferta.preco)}</div>
    <div><span class="parc {classe}">{html.escape(oferta.resumo_parcelamento)}</span></div>
    <div class="rodape">
      <span class="custo">{custo_txt}</span>
      <a class="btn" href="{html.escape(oferta.link)}" target="_blank" rel="noopener">Ver oferta</a>
    </div>
  </div>
</article>"""


def html_completo(
    ofertas: list[Oferta],
    miniaturas: dict[int, Path] | None = None,
    base_dir: Path | None = None,
    titulo: str = "Pesquisa de preços",
) -> str:
    miniaturas = miniaturas or {}
    base_dir = base_dir or Path(".")
    gerado = datetime.now().strftime("%d/%m/%Y %H:%M")
    indice_por_id = {id(o): i for i, o in enumerate(ofertas)}

    blocos = []
    for produto, lista in agrupar_por_produto(ofertas).items():
        cards = "\n".join(
            _card(o, indice_por_id[id(o)], miniaturas, base_dir) for o in lista
        )
        melhor = melhor_oferta(lista)
        referencia = (
            f" — menor: {formatar_reais(melhor.preco)} ({html.escape(melhor.loja)})"
            if melhor
            else ""
        )
        blocos.append(
            f'<section class="grupo"><h2>{html.escape(produto)}{referencia}</h2>'
            f'<div class="grid">{cards}</div></section>'
        )

    corpo = (
        "\n".join(blocos)
        if blocos
        else ('<p class="vazio">Nenhuma oferta passou pelos filtros nesta rodada.</p>')
    )

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(titulo)}</title>
<style>{_CSS}</style>
</head>
<body>
<header>
  <h1>{html.escape(titulo)}</h1>
  <div class="meta">{len(ofertas)} ofertas · gerado em {gerado}</div>
</header>
{corpo}
</body>
</html>"""


def corpo_email(
    ofertas: list[Oferta],
) -> str:
    """Fragmento HTML para o corpo do e-mail (sem <html>/<style> externo).

    As imagens apontam para a URL remota: anexo com cid não renderiza de forma
    confiável no Outlook, e o cliente de e-mail resolve melhor um <img src=http>.
    """
    partes = []
    for produto, lista in agrupar_por_produto(ofertas).items():
        melhor = melhor_oferta(lista)
        referencia = (
            f" (menor: {formatar_reais(melhor.preco)} em {melhor.loja})"
            if melhor
            else ""
        )
        linhas = []
        for oferta in lista:
            classe = (
                "ok"
                if oferta.sem_juros is True
                else ("juros" if oferta.sem_juros is False else "neutro")
            )
            imagem = (
                f'<img src="{html.escape(oferta.imagem)}" width="64" style="border-radius:4px">'
                if oferta.imagem
                else ""
            )
            linhas.append(
                f'<tr><td style="padding:6px;border-bottom:1px solid #eee">{imagem}</td>'
                f'<td style="padding:6px;border-bottom:1px solid #eee;font-size:12px">'
                f'<a href="{html.escape(oferta.link)}" style="color:#1d4ed8;text-decoration:none">'
                f"{html.escape(oferta.titulo)}</a><br>"
                f'<span style="color:#6b7280">{html.escape(oferta.loja)}</span></td>'
                f'<td style="padding:6px;border-bottom:1px solid #eee;white-space:nowrap;font-weight:700">'
                f"{formatar_reais(oferta.preco)}</td>"
                f'<td style="padding:6px;border-bottom:1px solid #eee;font-size:12px" class="{classe}">'
                f"{html.escape(oferta.resumo_parcelamento)}</td></tr>"
            )
        partes.append(
            f'<h3 style="font-size:14px;margin:18px 0 6px">{html.escape(produto)}{referencia}</h3>'
            f'<table cellspacing="0" cellpadding="0" style="border-collapse:collapse;width:100%">'
            f"{''.join(linhas)}</table>"
        )
    return "".join(partes) or "<p>Nenhuma oferta passou pelos filtros.</p>"


def salvar_html(
    ofertas: list[Oferta],
    caminho: str | Path,
    miniaturas: dict[int, Path] | None = None,
) -> Path:
    destino = Path(caminho)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(
        html_completo(ofertas, miniaturas, base_dir=destino.parent),
        encoding="utf-8",
    )
    return destino


# ------------------------------------------------------------------ csv


def salvar_csv(ofertas: list[Oferta], caminho: str | Path) -> Path:
    destino = Path(caminho)
    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("w", encoding="utf-8-sig", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=COLUNAS, delimiter=";")
        escritor.writeheader()
        for oferta in ofertas:
            escritor.writerow(oferta.para_linha())
    return destino


# ------------------------------------------------------------------ terminal


def tabela_terminal(ofertas: list[Oferta], limite: int = 40) -> str:
    """Resumo alinhado para o console — o que Kai confere antes de abrir a planilha."""
    if not ofertas:
        return "Nenhuma oferta coletada."

    linhas = [f"{'LOJA':<14}{'PREÇO':>12}  {'PARCELAMENTO':<34}TÍTULO"]
    linhas.append("-" * 118)
    for oferta in ofertas[:limite]:
        titulo = oferta.titulo if len(oferta.titulo) <= 42 else oferta.titulo[:41] + "…"
        linhas.append(
            f"{oferta.loja[:13]:<14}{formatar_reais(oferta.preco):>12}  "
            f"{oferta.resumo_parcelamento[:33]:<34}{titulo}"
        )
    if len(ofertas) > limite:
        linhas.append(f"... +{len(ofertas) - limite} ofertas")
    return "\n".join(linhas)
