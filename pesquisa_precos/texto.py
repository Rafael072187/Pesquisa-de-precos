# language: Python 3.11+, file: pesquisa_precos/texto.py
# Parsers de texto dos cartões de oferta. Tudo aqui é função pura — dá para
# testar sem navegador, e é o que mais quebra quando um site muda de layout.

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

ESPACOS = "\u00a0\u202f\u2009\t\r\n"

STOPWORDS = {
    "de",
    "da",
    "do",
    "das",
    "dos",
    "com",
    "sem",
    "para",
    "por",
    "e",
    "ou",
    "em",
    "no",
    "na",
    "nos",
    "nas",
    "ao",
    "aos",
    "um",
    "uma",
    "the",
    "and",
    "of",
    "for",
    "compativel",
    "compatível",
}


def normalizar(texto: object) -> str:
    """Minúsculas, sem acento, espaços colapsados. Comparação de termos passa por aqui."""
    if texto is None:
        return ""
    t = str(texto)
    t = unicodedata.normalize("NFKD", t)
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = t.replace("\u00a0", " ").replace("\u202f", " ")
    t = re.sub(r"\s+", " ", t)
    return t.strip().lower()


# ---------------------------------------------------------------- preço

_SO_NUMERO = re.compile(r"[^\d.,]")


def parse_preco(bruto: object) -> float | None:
    """'R$ 2.299,00' -> 2299.0 ; 'R$ 1.899' -> 1899.0 ; '2299.90' -> 2299.9

    Aceita o lixo que os sites mandam: quebras de linha no meio do número,
    espaço não separável, separador de milhar no texto e ponto decimal.
    """
    if bruto is None:
        return None
    if isinstance(bruto, (int, float)):
        return round(float(bruto), 2)

    t = str(bruto)
    for c in ESPACOS:
        t = t.replace(c, " ")
    t = _SO_NUMERO.sub("", t)
    if not t or not any(c.isdigit() for c in t):
        return None

    if "," in t:
        # vírgula manda: tudo antes é milhar, a última vírgula é o decimal
        inteiro, _, decimal = t.rpartition(",")
        inteiro = inteiro.replace(".", "").replace(",", "")
        decimal = decimal.replace(".", "").replace(",", "")
        t = f"{inteiro or '0'}.{decimal}" if decimal else (inteiro or "0")
    else:
        if re.fullmatch(r"\d{1,3}(\.\d{3})+", t):
            t = t.replace(".", "")  # 1.299 / 2.499.000 -> milhar
        elif t.count(".") > 1:
            partes = t.split(".")
            t = "".join(partes[:-1]) + "." + partes[-1]

    try:
        valor = float(t)
    except ValueError:
        return None
    return round(valor, 2) if valor > 0 else None


def extrair_preco_do_texto(texto: object) -> float | None:
    """Primeiro 'R$ …' que aparecer no texto. Usado quando não há seletor de preço."""
    if not texto:
        return None
    achado = re.search(
        r"R\$\s*([\d]{1,3}(?:[.\s]\d{3})*(?:,\d{2})?|\d+(?:[.,]\d{2})?)", str(texto)
    )
    return parse_preco(achado.group(1)) if achado else None


# ---------------------------------------------------------------- parcelamento


@dataclass
class Parcelamento:
    parcelas: int = 1
    valor_parcela: float | None = None
    sem_juros: bool | None = None
    texto: str = ""

    @property
    def total(self) -> float | None:
        if self.valor_parcela is None:
            return None
        return round(self.valor_parcela * self.parcelas, 2)


_RE_PARCELA = re.compile(r"(\d{1,2})\s*[xX]\b")
_RE_SEM_JUROS = re.compile(r"sem\s+juros", re.I)
_RE_COM_JUROS = re.compile(r"com\s+juros|juros\s+de|acr[eé]scimo", re.I)
_RE_TRECHO_PARCELA = re.compile(r"(\d{1,2})\s*[xX]\b.{0,45}?R\$\s*[\d.,]+.{0,35}", re.S)


def achar_trecho_parcelamento(texto: object) -> str:
    """Recorta a janela '…12x de R$ 191,58 sem juros…' de um texto grande.

    O cartão inteiro carrega preço, frete, cupom e às vezes outro 'Nx'. Aqui a
    gente isola só o trecho no formato de parcelamento antes de interpretar.
    """
    if not texto:
        return ""
    t = str(texto)
    for m in _RE_TRECHO_PARCELA.finditer(t):
        if 2 <= int(m.group(1)) <= 36:
            return re.sub(r"\s+", " ", m.group(0)).strip()
    return ""


def parse_parcelamento(bruto: object, preco: float | None = None) -> Parcelamento:
    """Interpreta '12x de R$ 191,58 sem juros' e devolve parcelas + valor + flag.

    Regra de decisão do 'sem juros':
      1. se o texto diz "sem juros"  -> True
      2. se o texto diz "com juros"  -> False
      3. se cala, compara parcelas*valor com o preço: igual = sem juros
      4. sem dados suficientes      -> None (desconhecido, não invente)
    """
    if not bruto:
        return Parcelamento(1, preco, True, "")

    texto = re.sub(r"\s+", " ", str(bruto)).strip()
    if not texto:
        return Parcelamento(1, preco, True, "")

    m = _RE_PARCELA.search(texto)
    if not m:
        return Parcelamento(1, preco, True, texto)

    n = int(m.group(1))
    if n <= 1:
        return Parcelamento(1, preco, True, texto)

    # valor da parcela: primeiro R$ depois do "Nx", senão primeiro R$ do trecho
    trecho = texto[m.end() : m.end() + 60]
    mp = re.search(
        r"R\$\s*([\d]{1,3}(?:[.\s]\d{3})*(?:,\d{2})?|\d+(?:[.,]\d{2})?)", trecho
    )
    valor = parse_preco(mp.group(1)) if mp else None

    sem_juros: bool | None = None
    if _RE_SEM_JUROS.search(texto):
        sem_juros = True
    elif _RE_COM_JUROS.search(texto):
        sem_juros = False

    if sem_juros is None and valor and preco:
        total = valor * n
        sem_juros = abs(total - preco) <= max(preco * 0.015, 0.05)

    return Parcelamento(n, valor, sem_juros, texto)


def resumo_parcelamento(
    parcelas: int, valor_parcela: float | None, sem_juros: bool | None
) -> str:
    """Texto curto para planilha/HTML: '12x R$ 191,58 sem juros'."""
    if not parcelas or parcelas <= 1:
        return "à vista"
    valor = (
        f"R$ {valor_parcela:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        if valor_parcela
        else "valor não informado"
    )
    selo = (
        "sem juros"
        if sem_juros is True
        else ("com juros" if sem_juros is False else "juros não informado")
    )
    return f"{parcelas}x {valor} {selo}"


# ---------------------------------------------------------------- termos


def tokens_produto(nome: object) -> list[str]:
    """Termos que obrigatoriamente precisam aparecer no título da oferta."""
    saida: list[str] = []
    for bruto in normalizar(nome).split(" "):
        token = bruto.strip(".,;:()[]-/\\|\"'")
        if len(token) < 2 or token in STOPWORDS:
            continue
        if token not in saida:
            saida.append(token)
    return saida


def lista_termos(termos: object) -> list[str]:
    """'usado recondicionado' -> ['usado', 'recondicionado']

    Vírgula ou ponto-e-vírgula separam frases inteiras ('usado, nao funciona');
    sem separador, cada palavra vale sozinha — comportamento das versões antigas.
    """
    t = normalizar(termos)
    if not t:
        return []
    if "," in t or ";" in t:
        partes = re.split(r"[,;]", t)
    else:
        partes = t.split(" ")
    return [p.strip() for p in partes if p.strip() and len(p.strip()) >= 2]


def contem(titulo: str, termo: str) -> bool:
    """Compara ignorando espaços — '16gb' casa com '16 gb'."""
    alvo = normalizar(titulo)
    if termo in alvo:
        return True
    return termo in alvo.replace(" ", "")


def formatar_reais(valor: float | None) -> str:
    if valor is None:
        return "—"
    s = f"{valor:,.2f}"
    return "R$ " + s.replace(",", "X").replace(".", ",").replace("X", ".")
