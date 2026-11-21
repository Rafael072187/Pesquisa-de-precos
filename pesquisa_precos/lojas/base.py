# language: Python 3.11+, file: pesquisa_precos/lojas/base.py
from __future__ import annotations

import re
from urllib.parse import urljoin

from selenium.webdriver.chrome.webdriver import WebDriver

from ..config import Config
from ..models import Oferta
from ..navegador import (
    abrir,
    coletar_cartoes,
    detectar_bloqueio,
    esperar_css,
    rolar,
    salvar_debug,
)
from ..texto import (
    achar_trecho_parcelamento,
    extrair_preco_do_texto,
    parse_parcelamento,
    parse_preco,
)


class LojaBloqueada(RuntimeError):
    """O site serviu página de verificação/bloqueio — não adianta insistir na rodada."""


class Loja:
    """Adaptador de um marketplace.

    Cada site só precisa dizer: como montar a URL de busca, qual seletor indica
    que os cartões chegaram, e um JS que devolve os cartões crus. O resto —
    espera, retry, parsing de preço/parcelas, normalização de URL — é aqui.
    """

    chave: str = ""
    nome: str = ""
    base: str = ""
    seletor_espera: str = "body"
    js_cartoes: str = ""

    # ------------------------------------------------------------- público

    def url(self, termo: str) -> str:
        raise NotImplementedError

    def buscar(self, driver: WebDriver, termo: str, cfg: Config) -> list[Oferta]:
        url = self.url(termo)
        abrir(driver, url, cfg.timeout_pagina)

        if not esperar_css(driver, self.seletor_espera, cfg.espera_cartao):
            # uma segunda tentativa: às vezes o primeiro load cai num interstitial
            abrir(driver, url, cfg.timeout_pagina)
            if not esperar_css(driver, self.seletor_espera, cfg.espera_cartao):
                motivo = detectar_bloqueio(driver)
                if motivo:
                    if cfg.debug:
                        caminho = salvar_debug(driver, cfg, f"{self.chave}_bloqueio")
                        print(f"    [{self.nome}] HTML salvo em {caminho}")
                    raise LojaBloqueada(motivo)
                print(
                    f"    [{self.nome}] nenhum cartão encontrado (layout mudou ou busca vazia)."
                )
                if cfg.debug:
                    caminho = salvar_debug(driver, cfg, f"{self.chave}_vazio")
                    print(f"    [{self.nome}] HTML salvo em {caminho}")
                return []

        rolar(driver, 4)
        brutos = coletar_cartoes(driver, self.js_cartoes)[: cfg.max_resultados]

        ofertas: list[Oferta] = []
        for item in brutos:
            oferta = self.montar(item, termo)
            if oferta:
                ofertas.append(oferta)

        if cfg.detalhar:
            self._completar_parcelamento(driver, ofertas, cfg)

        return ofertas

    # ------------------------------------------------------------- interno

    def montar(self, item: dict, termo: str) -> Oferta | None:
        titulo = re.sub(r"\s+", " ", item.get("titulo", "")).strip()
        if not titulo:
            return None

        preco = parse_preco(item.get("preco")) or extrair_preco_do_texto(
            item.get("texto")
        )
        if not preco:
            return None

        bruto_parcelas = item.get("parcelas") or ""
        trecho = achar_trecho_parcelamento(bruto_parcelas) or achar_trecho_parcelamento(
            item.get("texto")
        )
        parcelamento = parse_parcelamento(trecho or bruto_parcelas, preco)

        return Oferta(
            produto_busca=termo,
            loja=self.nome,
            titulo=titulo,
            preco=preco,
            link=self._link(item.get("link", "")),
            imagem=self._imagem(item.get("imagem", "")),
            parcelas=parcelamento.parcelas,
            valor_parcela=parcelamento.valor_parcela,
            sem_juros=parcelamento.sem_juros,
            texto_parcelamento=parcelamento.texto,
        )

    def _link(self, href: str) -> str:
        if not href:
            return ""
        if href.startswith("//"):
            return "https:" + href
        if href.startswith("/"):
            return urljoin(self.base, href)
        return href

    def _imagem(self, src: str) -> str:
        if not src or src.startswith("data:"):
            return ""
        if src.startswith("//"):
            return "https:" + src
        if src.startswith("/"):
            return urljoin(self.base, src)
        return src

    def _completar_parcelamento(
        self, driver: WebDriver, ofertas: list[Oferta], cfg: Config
    ) -> None:
        """Só para lojas que escondem o parcelamento na página do produto."""
        return
