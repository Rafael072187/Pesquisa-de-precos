"""Pesquisa de Preços — coleta de ofertas em marketplaces brasileiros.

Camadas:
    texto.py       parsers de preço e parcelamento
    navegador.py   fábrica do Chrome/Brave/Edge + utilitários de espera
    lojas/         um adaptador por marketplace
    filtros.py     termos banidos, termos obrigatórios, faixa de preço
    relatorio.py   .xlsx (com miniaturas), .html, .csv
    email_outlook.py  envio via Outlook instalado
    pesquisa.py    orquestrador
"""

__version__ = "3.0.0"
