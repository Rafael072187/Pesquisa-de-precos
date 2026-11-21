# language: Python 3.11+, file: pesquisa_precos/lojas/__init__.py
"""Registro de lojas. Adicionar um marketplace = uma classe + uma linha aqui."""

from __future__ import annotations

from .amazon import Amazon
from .base import Loja
from .buscape import Buscape
from .mercadolivre import MercadoLivre

LOJAS: dict[str, type[Loja]] = {
    MercadoLivre.chave: MercadoLivre,
    Buscape.chave: Buscape,
    Amazon.chave: Amazon,
}

TODAS = list(LOJAS)


def resolver(chaves: list[str] | None) -> list[type[Loja]]:
    if not chaves:
        return [LOJAS[c] for c in TODAS]
    escolhidas: list[type[Loja]] = []
    for chave in chaves:
        normalizada = chave.strip().lower()
        if normalizada in LOJAS:
            escolhidas.append(LOJAS[normalizada])
        else:
            disponiveis = ", ".join(TODAS)
            raise ValueError(
                f"Loja desconhecida: {chave!r}. Disponíveis: {disponiveis}"
            )
    return escolhidas


__all__ = ["LOJAS", "TODAS", "Loja", "resolver"]
