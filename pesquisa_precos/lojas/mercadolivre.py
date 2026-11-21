# language: Python 3.11+, file: pesquisa_precos/lojas/mercadolivre.py
from __future__ import annotations

import re

from ..texto import normalizar
from .base import Loja

# Cartão do ML (layout poly-card, 2024+). Os seletores antigos
# (ui-search-result__content, price__fraction) ficam como fallback porque o site
# alterna entre A/B de layout sem aviso.
JS_CARTOES = r"""
const cards = [...document.querySelectorAll(
  'li.ui-search-layout__item, div.poly-card, li.ui-search-layout__item--clp'
)];
const unicos = [];
for (const c of cards) {
  if (!unicos.some(u => u === c || u.contains(c))) unicos.push(c);
}
return unicos.map(c => {
  const tituloEl = c.querySelector('.poly-component__title, h2.poly-box, h2');
  const linkEl = c.querySelector('a.poly-component__title') || tituloEl || c.querySelector('a');
  const precoBox = c.querySelector('.poly-price__current') || c.querySelector('.ui-search-price__second-line');
  let precoEl = null;
  if (precoBox) {
    precoEl = precoBox.querySelector('.andes-money-amount--cents-superscript:not(.andes-money-amount--previous)')
           || precoBox.querySelector('.andes-money-amount:not(.andes-money-amount--previous)');
  }
  const instEl = c.querySelector('.poly-price__installments, .poly-component__installments, .ui-search-installments');
  const imgEl = c.querySelector('img.poly-component__picture, img');
  return {
    titulo: tituloEl ? tituloEl.textContent : '',
    preco: precoEl ? precoEl.textContent : (precoBox ? precoBox.textContent : ''),
    parcelas: instEl ? instEl.textContent : '',
    texto: c.innerText || '',
    link: linkEl ? linkEl.href : '',
    imagem: imgEl ? (imgEl.getAttribute('data-src') || imgEl.getAttribute('src') || '') : ''
  };
});
"""


class MercadoLivre(Loja):
    chave = "mercadolivre"
    nome = "Mercado Livre"
    base = "https://www.mercadolivre.com.br"
    seletor_espera = "li.ui-search-layout__item, div.poly-card"
    js_cartoes = JS_CARTOES

    def url(self, termo: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", normalizar(termo)).strip("-")
        return f"https://lista.mercadolivre.com.br/{slug}"
