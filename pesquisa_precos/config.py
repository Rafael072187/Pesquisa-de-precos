# language: Python 3.11+, file: pesquisa_precos/config.py
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

# Ordem de preferência. Env var vence a lista (BRAVE_PATH / CHROME_PATH / EDGE_PATH).
CANDIDATOS_NAVEGADOR = [
    r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
    r"C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
]

UA_PADRAO = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)


@dataclass
class Config:
    navegador_path: str | None = None
    headless: bool = False
    perfil_dir: str | None = None  # reaproveita cookies/login entre execuções
    timeout_pagina: int = 40  # segundos para o load completo
    espera_cartao: int = 18  # segundos esperando o primeiro cartão
    pausa_loja: float = 1.5  # respiro entre lojas (evita 429)
    max_resultados: int = 20  # cartões lidos por loja/produto
    baixar_imagens: bool = True
    dir_imagens: Path = field(default_factory=lambda: Path("imagens"))
    dir_debug: Path = field(default_factory=lambda: Path("debug"))
    user_agent: str = UA_PADRAO
    detalhar: bool = False  # abre a página do produto quando falta parcela
    debug: bool = False  # salva HTML quando a coleta volta vazia

    def localizar_navegador(self) -> str | None:
        if self.navegador_path:
            return self.navegador_path if Path(self.navegador_path).exists() else None
        for env in ("BRAVE_PATH", "CHROME_PATH", "EDGE_PATH"):
            caminho = os.environ.get(env)
            if caminho and Path(caminho).exists():
                return caminho
        for caminho in CANDIDATOS_NAVEGADOR:
            if Path(caminho).exists():
                return caminho
        return None
