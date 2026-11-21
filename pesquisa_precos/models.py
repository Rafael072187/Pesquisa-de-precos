# language: Python 3.11+, file: pesquisa_precos/models.py
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from .texto import formatar_reais, resumo_parcelamento


@dataclass
class Oferta:
    """Um cartão de oferta coletado. `preco` é o valor à vista/anunciado."""

    produto_busca: str
    loja: str
    titulo: str
    preco: float | None
    link: str
    imagem: str = ""
    parcelas: int = 1
    valor_parcela: float | None = None
    sem_juros: bool | None = None
    texto_parcelamento: str = ""
    coletado_em: str = field(
        default_factory=lambda: datetime.now().strftime("%d/%m/%Y %H:%M")
    )

    # --------------------------------------------------------- derivados

    @property
    def total_parcelado(self) -> float | None:
        if self.parcelas <= 1:
            return self.preco
        if not self.valor_parcela:
            return None
        return round(self.valor_parcela * self.parcelas, 2)

    @property
    def custo_credito_pct(self) -> float | None:
        """Quanto o parcelamento custa acima do preço anunciado, em %."""
        total = self.total_parcelado
        if not self.preco or not total:
            return None
        if self.parcelas <= 1:
            return 0.0
        return round((total / self.preco - 1) * 100, 2)

    @property
    def resumo_parcelamento(self) -> str:
        return resumo_parcelamento(self.parcelas, self.valor_parcela, self.sem_juros)

    @property
    def sem_juros_texto(self) -> str:
        if self.parcelas <= 1:
            return "à vista"
        if self.sem_juros is True:
            return "sem juros"
        if self.sem_juros is False:
            return "com juros"
        return "não informado"

    def chave_dedupe(self) -> str:
        """Mesmo produto repetido em dois cartões do mesmo site."""
        base = self.link.split("#")[0].split("?")[0].rstrip("/")
        return f"{base}|{self.preco}"

    def para_linha(self) -> dict[str, object]:
        """Linha da planilha, na ordem das colunas do relatório."""
        return {
            "Produto buscado": self.produto_busca,
            "Loja": self.loja,
            "Título": self.titulo,
            "Preço (R$)": self.preco,
            "Parcelas": self.parcelas if self.parcelas > 1 else 1,
            "Valor da parcela (R$)": self.valor_parcela
            if self.parcelas > 1
            else self.preco,
            "Sem juros": self.sem_juros_texto,
            "Total parcelado (R$)": self.total_parcelado,
            "Diferença à vista × parcelado (%)": self.custo_credito_pct,
            "Resumo do parcelamento": self.resumo_parcelamento,
            "Link": self.link,
            "Imagem (URL)": self.imagem,
        }


COLUNAS = [
    "Produto buscado",
    "Loja",
    "Título",
    "Preço (R$)",
    "Parcelas",
    "Valor da parcela (R$)",
    "Sem juros",
    "Total parcelado (R$)",
    "Diferença à vista × parcelado (%)",
    "Resumo do parcelamento",
    "Link",
    "Imagem (URL)",
]


def melhor_oferta(ofertas: list[Oferta]) -> Oferta | None:
    """Menor preço; empate resolvido por mais parcelas sem juros."""
    validas = [o for o in ofertas if o.preco]
    if not validas:
        return None
    return sorted(
        validas,
        key=lambda o: (o.preco, -(o.parcelas if o.sem_juros else 0)),
    )[0]


def agrupar_por_produto(ofertas: list[Oferta]) -> dict[str, list[Oferta]]:
    grupos: dict[str, list[Oferta]] = {}
    for o in ofertas:
        grupos.setdefault(o.produto_busca, []).append(o)
    for lista in grupos.values():
        lista.sort(key=lambda o: (o.preco or float("inf"), o.loja))
    return grupos


__all__ = [
    "Oferta",
    "COLUNAS",
    "melhor_oferta",
    "agrupar_por_produto",
    "formatar_reais",
]
