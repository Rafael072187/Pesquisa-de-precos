# language: Python 3.11+, file: pesquisa_precos/lojas/amazon.py
from __future__ import annotations

from urllib.parse import quote_plus

from .base import Loja

# Resultado de busca da Amazon: cada produto é um div com
# data-component-type="s-search-result". O preço vive em .a-offscreen (texto
# puro "R$ 4.399,00"); o riscado fica em .a-text-price e precisa ser ignorado.
JS_CARTOES = r"""
const cards = [...document.querySelectorAll('div[data-component-type="s-search-result"]')];
return cards.map(c => {
  const t = c.querySelector('h2 span') || c.querySelector('h2');
  const a = c.querySelector('h2 a') || c.querySelector('a.a-link-normal');
  const p = c.querySelector('span.a-price:not(.a-text-price) span.a-offscreen')
         || c.querySelector('span.a-offscreen');
  const img = c.querySelector('img.s-image');
  let inst = '';
  for (const s of c.querySelectorAll('span.a-color-secondary, span.a-size-base')) {
    const txt = (s.textContent || '').trim();
    if (/\bjuros\b/i.test(txt) || /\d+\s*x\s*R\$/i.test(txt)) { inst = txt; break; }
  }
  return {
    titulo: t ? t.textContent : '',
    preco: p ? p.textContent : '',
    parcelas: inst,
    texto: c.innerText || '',
    link: a ? a.href : '',
    imagem: img ? (img.getAttribute('src') || '') : ''
  };
});
"""


class Amazon(Loja):
    chave = "amazon"
    nome = "Amazon"
    base = "https://www.amazon.com.br"
    seletor_espera = 'div[data-component-type="s-search-result"]'
    js_cartoes = JS_CARTOES

    def url(self, termo: str) -> str:
        return f"https://www.amazon.com.br/s?k={quote_plus(termo)}"
