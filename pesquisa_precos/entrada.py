# language: Python 3.11+, file: pesquisa_precos/entrada.py
from __future__ import annotations

import csv
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.comments import Comment
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from .filtros import Regra
from .texto import normalizar

CABECALHO = [
    "Nome",
    "Termos banidos",
    "Preço mínimo",
    "Preço máximo",
    "Termos obrigatórios",
]

EXEMPLOS = [
    ["iphone 12 64 gb", "mini, watch, capa", 1200, 2500, ""],
    ["rtx 3060", "zotac, galax", 1500, 3000, ""],
    ["memória ddr4 16gb 3200mhz", "rgb, notebook", 150, 320, ""],
]


def criar_modelo(caminho: str | Path = "buscas.xlsx") -> Path:
    """Gera a planilha de exemplo se ela não existir. Não sobrescreve."""
    destino = Path(caminho)
    if destino.exists():
        return destino

    wb = Workbook()
    ws = wb.active
    ws.title = "buscas"
    ws.append(CABECALHO)
    for linha in EXEMPLOS:
        ws.append(linha)

    larguras = [42, 32, 16, 16, 32]
    for i, largura in enumerate(larguras, start=1):
        ws.column_dimensions[get_column_letter(i)].width = largura

    cabecalho_fill = PatternFill("solid", fgColor="1F2937")
    for celula in ws[1]:
        celula.font = Font(bold=True, color="FFFFFF")
        celula.fill = cabecalho_fill
        celula.alignment = Alignment(vertical="center")

    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:E{ws.max_row}"

    ws["B1"].comment = Comment(
        "Separe por vírgula para frases inteiras (mini, watch). "
        "Sem vírgula, cada palavra vale sozinha.",
        "Pesquisa de Preços",
    )
    ws["E1"].comment = Comment(
        "Opcional. Vazio = o nome do produto vira a lista de termos obrigatórios.",
        "Pesquisa de Preços",
    )

    wb.save(destino)
    return destino


def ler_regras(caminho: str | Path) -> list[Regra]:
    arquivo = Path(caminho)
    if not arquivo.exists():
        raise FileNotFoundError(
            f"Planilha de buscas não encontrada: {arquivo}. "
            f"Rode `python main.py --criar-modelo` para gerar uma."
        )

    if arquivo.suffix.lower() == ".csv":
        return _ler_csv(arquivo)
    return _ler_xlsx(arquivo)


def _ler_xlsx(arquivo: Path) -> list[Regra]:
    wb = load_workbook(arquivo, data_only=True, read_only=True)
    ws = wb[wb.sheetnames[0]]

    linhas = list(ws.iter_rows(values_only=True))
    if not linhas:
        return []

    mapa = _mapear_colunas([str(c) if c is not None else "" for c in linhas[0]])
    regras: list[Regra] = []
    for linha in linhas[1:]:
        if not linha or all(c is None or str(c).strip() == "" for c in linha):
            continue
        produto = linha[mapa["nome"]] if mapa["nome"] < len(linha) else None
        if produto is None or str(produto).strip() == "":
            continue
        if _parece_nota(produto, linha, mapa):
            continue

        regras.append(
            Regra.da_linha(
                produto=produto,
                banidos=_col(linha, mapa.get("banidos")),
                minimo=_col(linha, mapa.get("minimo")),
                maximo=_col(linha, mapa.get("maximo")),
                obrigatorios=_col(linha, mapa.get("obrigatorios")),
            )
        )

    wb.close()
    return regras


def _ler_csv(arquivo: Path) -> list[Regra]:
    with arquivo.open("r", encoding="utf-8-sig", newline="") as f:
        leitor = csv.reader(f, delimiter=";")
        linhas = [l for l in leitor if any(c.strip() for c in l)]
    if not linhas:
        return []
    mapa = _mapear_colunas(linhas[0])
    regras = []
    for linha in linhas[1:]:
        produto = _col(linha, mapa.get("nome"))
        if not produto:
            continue
        regras.append(
            Regra.da_linha(
                produto=produto,
                banidos=_col(linha, mapa.get("banidos")),
                minimo=_col(linha, mapa.get("minimo")),
                maximo=_col(linha, mapa.get("maximo")),
                obrigatorios=_col(linha, mapa.get("obrigatorios")),
            )
        )
    return regras


def _mapear_colunas(cabecalho: list[str]) -> dict[str, int]:
    """Casa cabeçalho por pedaço de palavra — tolera acento, caixa e coluna extra."""
    mapa: dict[str, int] = {}
    for indice, bruto in enumerate(cabecalho):
        nome = normalizar(bruto)
        if not nome:
            continue
        if "obrigator" in nome:
            mapa.setdefault("obrigatorios", indice)
        elif "banid" in nome or "bloque" in nome:
            mapa.setdefault("banidos", indice)
        elif "minim" in nome:
            mapa.setdefault("minimo", indice)
        elif "maxim" in nome:
            mapa.setdefault("maximo", indice)
        elif "nome" in nome or "produto" in nome:
            mapa.setdefault("nome", indice)

    if "nome" not in mapa:
        mapa["nome"] = 0
    return mapa


def _parece_nota(produto: object, linha: tuple | list, mapa: dict[str, int]) -> bool:
    """Linha de observação escrita à mão no fim da planilha não é produto."""
    nome = normalizar(produto)
    if nome.startswith(("termos ", "observa", "nota", "obs", "legenda")):
        return True
    outros = [
        _col(linha, mapa.get(chave))
        for chave in ("banidos", "minimo", "maximo", "obrigatorios")
    ]
    vazios = all(v is None or str(v).strip() == "" for v in outros)
    return vazios and len(nome) > 80


def _col(linha: tuple | list, indice: int | None) -> object:
    if indice is None or indice >= len(linha):
        return None
    return linha[indice]
