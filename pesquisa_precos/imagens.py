# language: Python 3.11+, file: pesquisa_precos/imagens.py
from __future__ import annotations

import hashlib
from io import BytesIO
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .config import UA_PADRAO

TIMEOUT = 15
LIMITE_BYTES = 4_000_000


def baixar(
    url: str, destino: Path, tamanho: tuple[int, int] = (180, 180)
) -> Path | None:
    """Baixa e normaliza a foto do produto em JPEG pequeno. Devolve o caminho local.

    Silencioso por design: imagem é enfeite, oferta é dado. Se o CDN recusar,
    a linha continua válida com a URL remota.
    """
    if not url or not url.lower().startswith("http"):
        return None
    try:
        from PIL import Image
    except ImportError:
        return None

    destino.mkdir(parents=True, exist_ok=True)
    alvo = destino / (hashlib.sha1(url.encode("utf-8")).hexdigest()[:16] + ".jpg")
    if alvo.exists() and alvo.stat().st_size > 512:
        return alvo

    req = Request(
        url,
        headers={
            "User-Agent": UA_PADRAO,
            "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
            "Referer": "https://www.google.com/",
        },
    )
    try:
        with urlopen(req, timeout=TIMEOUT) as resposta:
            dados = resposta.read(LIMITE_BYTES)
    except (HTTPError, URLError, TimeoutError, ValueError, OSError):
        return None

    try:
        imagem = Image.open(BytesIO(dados))
        imagem.load()
        if imagem.mode in ("RGBA", "LA", "P"):
            fundo = Image.new("RGB", imagem.size, (255, 255, 255))
            convertida = imagem.convert("RGBA")
            fundo.paste(convertida, mask=convertida.split()[-1])
            imagem = fundo
        else:
            imagem = imagem.convert("RGB")
        imagem.thumbnail(tamanho)
        imagem.save(alvo, "JPEG", quality=82, optimize=True)
    except Exception:
        return None
    return alvo


def baixar_lote(urls: dict[str, str], destino: Path) -> dict[str, Path]:
    """{chave: url} -> {chave: caminho}. Sem repetir download da mesma URL."""
    cache: dict[str, Path | None] = {}
    saida: dict[str, Path] = {}
    for chave, url in urls.items():
        if url not in cache:
            cache[url] = baixar(url, destino)
        caminho = cache[url]
        if caminho:
            saida[chave] = caminho
    return saida
