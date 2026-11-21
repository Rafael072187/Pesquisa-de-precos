# language: Python 3.11+, file: pesquisa_precos/lojas/buscape.py
from __future__ import annotations

import time
from urllib.parse import quote

from selenium.webdriver.chrome.webdriver import WebDriver

from ..config import Config
from ..models import Oferta
from ..navegador import detalhar_parcelamento
from ..texto import achar_trecho_parcelamento, parse_parcelamento
from .base import Loja

# O Buscapé compila CSS-modules: as classes têm hash e mudam a cada build.
# Por isso o seletor ancora em data-testid (estável) e num pedaço da classe.
# Cada cartão traz price, installment e interest separados — dá para montar
# "12x R$ 191,58 sem juros" sem abrir a página do produto.
JS_CARTOES = r"""
let cards = [...document.querySelectorAll('[data-testid="product-card"]')];
if (!cards.length) {
  cards = [...document.querySelectorAll('div[class*="OrqProductCard"], div[class*="ProductCard"]')];
}
return cards.map(c => {
  const a = c.querySelector('a[data-testid="product-card::card"]')
         || c.querySelector('a')
         || (c.tagName === 'A' ? c : null);
  const t = c.querySelector('[data-testid="product-card::name"], [class*="ProductCard_Name"]');
  const p = c.querySelector('[data-testid="product-card::price"], [class*="ProductCard_Price"]');
  const i = c.querySelector('img[data-testid="product-card::image"]')
         || c.querySelector('[data-testid="product-card::image"] img')
         || c.querySelector('img');
  const inst = c.querySelector('[data-testid="product-card::installment"], [class*="Installment"]');
  const juros = c.querySelector('[data-testid="product-card::interest"]');
  let parcelas = inst ? inst.textContent : '';
  if (juros && juros.textContent) parcelas = parcelas + ' ' + juros.textContent;
  return {
    titulo: t ? t.textContent : '',
    preco: p ? p.textContent : '',
    parcelas: parcelas,
    texto: c.innerText || '',
    link: a ? a.href : '',
    imagem: i ? (i.getAttribute('data-src') || i.getAttribute('src') || '') : ''
  };
});
"""


class Buscape(Loja):
    chave = "buscape"
    nome = "Buscapé"
    base = "https://www.buscape.com.br"
    seletor_espera = '[data-testid="product-card"], div[class*="OrqProductCard"]'
    js_cartoes = JS_CARTOES

    def url(self, termo: str) -> str:
        return f"https://www.buscape.com.br/search?q={quote(termo)}"

    def _completar_parcelamento(
        self, driver: WebDriver, ofertas: list[Oferta], cfg: Config
    ) -> None:
        """Fallback: quando o cartão não traz parcela, a página do anúncio traz."""
        pendentes = [o for o in ofertas if o.parcelas <= 1 and o.link]
        for oferta in pendentes:
            texto = detalhar_parcelamento(driver, oferta.link, timeout=10)
            trecho = achar_trecho_parcelamento(texto)
            if not trecho:
                continue
            parcelamento = parse_parcelamento(trecho, oferta.preco)
            oferta.parcelas = parcelamento.parcelas
            oferta.valor_parcela = parcelamento.valor_parcela
            oferta.sem_juros = parcelamento.sem_juros
            oferta.texto_parcelamento = parcelamento.texto
            time.sleep(0.4)
