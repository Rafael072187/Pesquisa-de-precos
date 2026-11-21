# language: Python 3.11+, file: pesquisa_precos/api.py
"""Fachada para uso em notebook/script, sem passar pela CLI.

from pesquisa_precos.api import buscar, planilha

ofertas = buscar("rtx 3060", minimo=1500, maximo=3000, banidos="zotac, galax")
for o in ofertas:
    print(o.loja, o.preco, o.resumo_parcelamento, o.link)
planilha(ofertas, "ofertas.xlsx")
"""

from __future__ import annotations

from pathlib import Path

from .config import Config
from .filtros import Regra
from .imagens import baixar_lote
from .lojas import resolver
from .models import Oferta
from .pesquisa import pesquisar
from .relatorio import salvar_html, salvar_xlsx


def buscar(
    termo: str,
    minimo: float | None = None,
    maximo: float | None = None,
    banidos: str = "",
    obrigatorios: str = "",
    lojas: list[str] | None = None,
    limite: int = 20,
    headless: bool = False,
    perfil: str | None = None,
    detalhar: bool = False,
    verboso: bool = True,
) -> list[Oferta]:
    """Uma busca só. Devolve as ofertas já filtradas, ordenadas por preço."""
    regra = Regra.da_linha(termo, banidos, minimo, maximo, obrigatorios)
    cfg = Config(
        headless=headless,
        perfil_dir=perfil,
        max_resultados=max(1, limite),
        detalhar=detalhar,
        baixar_imagens=False,
    )
    return pesquisar([regra], resolver(lojas), cfg, verboso=verboso)


def planilha(
    ofertas: list[Oferta],
    caminho: str | Path = "ofertas.xlsx",
    html: str | Path | None = None,
    imagens: bool = True,
) -> Path:
    """Grava a planilha (com fotos) e, se pedido, o relatório HTML."""
    destino = Path(caminho)
    miniaturas = {}
    if imagens:
        urls = {i: o.imagem for i, o in enumerate(ofertas) if o.imagem}
        miniaturas = baixar_lote(urls, destino.parent / "imagens")
    arquivo = salvar_xlsx(ofertas, destino, miniaturas)
    if html:
        salvar_html(ofertas, html, miniaturas)
    return arquivo
