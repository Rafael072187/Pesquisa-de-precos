# language: Python 3.11+, file: pesquisa_precos/filtros.py
from __future__ import annotations

from dataclasses import dataclass, field

from .models import Oferta
from .texto import contem, lista_termos, tokens_produto


@dataclass
class Regra:
    """Uma linha da planilha de buscas, já interpretada."""

    produto: str
    termos_banidos: list[str] = field(default_factory=list)
    termos_obrigatorios: list[str] = field(default_factory=list)
    preco_minimo: float | None = None
    preco_maximo: float | None = None

    @classmethod
    def da_linha(
        cls,
        produto: str,
        banidos: object,
        minimo: object,
        maximo: object,
        obrigatorios: object = None,
    ) -> "Regra":
        obrig = lista_termos(obrigatorios) if obrigatorios else []
        return cls(
            produto=str(produto).strip(),
            termos_banidos=lista_termos(banidos),
            # sem coluna explícita, o nome do produto vira a lista de obrigatórios
            termos_obrigatorios=obrig or tokens_produto(produto),
            preco_minimo=_numero(minimo),
            preco_maximo=_numero(maximo),
        )

    def aceita(self, oferta: Oferta) -> tuple[bool, str]:
        titulo = oferta.titulo

        for termo in self.termos_banidos:
            if contem(titulo, termo):
                return False, f"termo banido ({termo})"

        faltando = [t for t in self.termos_obrigatorios if not contem(titulo, t)]
        if faltando:
            return False, f"falta termo ({', '.join(faltando[:3])})"

        preco = oferta.preco
        if preco is None:
            return False, "sem preço"
        if self.preco_minimo is not None and preco < self.preco_minimo:
            return False, f"abaixo do mínimo ({preco:.2f})"
        if self.preco_maximo is not None and preco > self.preco_maximo:
            return False, f"acima do máximo ({preco:.2f})"

        return True, "ok"


def _numero(valor: object) -> float | None:
    if valor is None:
        return None
    if isinstance(valor, (int, float)):
        return float(valor) if valor > 0 else None
    texto = str(valor).strip().replace("R$", "").replace(".", "").replace(",", ".")
    if not texto:
        return None
    try:
        numero = float(texto)
    except ValueError:
        return None
    return numero if numero > 0 else None
