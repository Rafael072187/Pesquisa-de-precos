# language: Python 3.11+, file: tests/test_offline.py
"""Testes sem rede e sem navegador: parsers, filtros, planilha e HTML."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pesquisa_precos.entrada import criar_modelo, ler_regras
from pesquisa_precos.filtros import Regra
from pesquisa_precos.models import Oferta, melhor_oferta
from pesquisa_precos.relatorio import salvar_csv, salvar_html, salvar_xlsx
from pesquisa_precos.texto import (
    achar_trecho_parcelamento,
    contem,
    lista_termos,
    normalizar,
    parse_parcelamento,
    parse_preco,
    tokens_produto,
)


class TestPreco(unittest.TestCase):
    def test_formatos_brasileiros(self):
        casos = {
            "R$ 2.299,00": 2299.0,
            "R$ 2.299": 2299.0,
            "2299,90": 2299.9,
            "R$\n2.299\n,\n00": 2299.0,
            "R$ 12.499,99": 12499.99,
            "R$\u00a01.099,00": 1099.0,
            "349,9": 349.9,
            "R$ 89": 89.0,
            "1.299.000,50": 1299000.5,
        }
        for bruto, esperado in casos.items():
            with self.subTest(bruto=bruto):
                self.assertEqual(parse_preco(bruto), esperado)

    def test_lixo_nao_quebra(self):
        for bruto in (None, "", "esgotado", "R$ --"):
            self.assertIsNone(parse_preco(bruto))


class TestParcelamento(unittest.TestCase):
    def test_sem_juros_explicito(self):
        p = parse_parcelamento("em 12x R$ 191,58 sem juros", 2299.0)
        self.assertEqual((p.parcelas, p.valor_parcela, p.sem_juros), (12, 191.58, True))
        self.assertAlmostEqual(p.total, 2298.96, places=2)

    def test_com_juros_explicito(self):
        p = parse_parcelamento("10x de R$ 129,90 com juros", 1199.0)
        self.assertEqual((p.parcelas, p.sem_juros), (10, False))

    def test_inferencia_pelo_total(self):
        p = parse_parcelamento("6x R$ 200,00", 1200.0)
        self.assertTrue(p.sem_juros)
        p2 = parse_parcelamento("6x R$ 260,00", 1200.0)
        self.assertFalse(p2.sem_juros)

    def test_avista(self):
        p = parse_parcelamento("", 999.0)
        self.assertEqual((p.parcelas, p.valor_parcela, p.sem_juros), (1, 999.0, True))

    def test_cartao_inteiro(self):
        texto = "Placa de vídeo RTX 3060 R$ 2.699,00 ou 12x de R$ 224,91 sem juros Frete grátis"
        trecho = achar_trecho_parcelamento(texto)
        p = parse_parcelamento(trecho, 2699.0)
        self.assertEqual((p.parcelas, p.valor_parcela, p.sem_juros), (12, 224.91, True))

    def test_sem_informacao_nao_inventa(self):
        p = parse_parcelamento("12x", 1000.0)
        self.assertEqual(p.parcelas, 12)
        self.assertIsNone(p.valor_parcela)
        self.assertIsNone(p.sem_juros)


class TestTermos(unittest.TestCase):
    def test_normalizacao_e_acento(self):
        self.assertEqual(normalizar("Memória  DDR4"), "memoria ddr4")
        self.assertTrue(contem("Memória XPG 16GB", "16gb"))
        self.assertTrue(contem("Memória XPG 16 GB", "16gb"))

    def test_lista_virgula_vira_frase(self):
        self.assertEqual(lista_termos("mini, watch"), ["mini", "watch"])
        self.assertEqual(
            lista_termos("usado recondicionado"), ["usado", "recondicionado"]
        )

    def test_tokens_ignoram_stopword(self):
        self.assertEqual(
            tokens_produto("Memória de 16GB para Notebook"),
            ["memoria", "16gb", "notebook"],
        )


class TestRegra(unittest.TestCase):
    def _oferta(self, titulo, preco):
        return Oferta("rtx 3060", "KaBuM!", titulo, preco, "https://x/1")

    def test_aprova(self):
        regra = Regra.da_linha("rtx 3060", "zotac, galax", 1500, 3000)
        ok, _ = regra.aceita(self._oferta("Placa RTX 3060 12GB MSI", 2699))
        self.assertTrue(ok)

    def test_banido(self):
        regra = Regra.da_linha("rtx 3060", "zotac", 1500, 3000)
        ok, motivo = regra.aceita(self._oferta("RTX 3060 Zotac", 2699))
        self.assertFalse(ok)
        self.assertIn("banido", motivo)

    def test_faixa_e_termo_faltando(self):
        regra = Regra.da_linha("rtx 3060", "", 1500, 2000)
        self.assertFalse(regra.aceita(self._oferta("RTX 3060", 2699))[0])
        self.assertFalse(regra.aceita(self._oferta("RTX 3070", 1800))[0])


class TestSaidas(unittest.TestCase):
    def _ofertas(self):
        return [
            Oferta(
                "rtx 3060",
                "Mercado Livre",
                "RTX 3060 MSI Ventus",
                2699.0,
                "https://ml/1",
                "https://cdn/1.jpg",
                12,
                224.91,
                True,
            ),
            Oferta(
                "rtx 3060",
                "KaBuM!",
                "RTX 3060 Galax",
                2499.0,
                "https://kb/2",
                "",
                10,
                274.89,
                False,
            ),
            Oferta(
                "memoria 16gb",
                "Buscapé",
                "Memória DDR4 16GB",
                289.9,
                "https://bc/3",
                "",
            ),
        ]

    def test_xlsx_csv_html(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            ofertas = self._ofertas()
            xlsx = salvar_xlsx(ofertas, tmp / "o.xlsx")
            csv = salvar_csv(ofertas, tmp / "o.csv")
            html = salvar_html(ofertas, tmp / "o.html")
            for arquivo in (xlsx, csv, html):
                self.assertTrue(arquivo.exists() and arquivo.stat().st_size > 500)
            texto = html.read_text(encoding="utf-8")
            self.assertIn("RTX 3060 MSI", texto)
            self.assertIn("sem juros", texto)

    def test_melhor_oferta(self):
        melhor = melhor_oferta(
            [o for o in self._ofertas() if o.produto_busca == "rtx 3060"]
        )
        self.assertEqual(melhor.loja, "KaBuM!")

    def test_planilha_modelo_e_leitura(self):
        with tempfile.TemporaryDirectory() as tmp:
            caminho = criar_modelo(Path(tmp) / "buscas.xlsx")
            regras = ler_regras(caminho)
            self.assertEqual(len(regras), 3)
            self.assertEqual(regras[0].produto, "iphone 12 64 gb")
            self.assertIn("mini", regras[0].termos_banidos)
            self.assertEqual(regras[0].preco_maximo, 2500.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
