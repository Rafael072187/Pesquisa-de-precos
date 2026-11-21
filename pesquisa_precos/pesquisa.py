# language: Python 3.11+, file: pesquisa_precos/pesquisa.py
from __future__ import annotations

import time
import traceback

from .config import Config
from .filtros import Regra
from .lojas import Loja
from .lojas.base import LojaBloqueada
from .models import Oferta
from .navegador import criar_navegador


def pesquisar(
    regras: list[Regra], lojas: list[type[Loja]], cfg: Config, verboso: bool = True
) -> list[Oferta]:
    """Percorre produto × loja, filtra e devolve as ofertas aprovadas.

    Uma loja quebrada não derruba a rodada: o erro é isolado por par
    (produto, loja) e a próxima combinação segue.
    """
    driver = criar_navegador(cfg)
    aprovadas: list[Oferta] = []
    vistos: set[str] = set()
    descartes: dict[str, int] = {}
    bloqueadas: dict[str, str] = {}

    try:
        for indice, regra in enumerate(regras, start=1):
            if verboso:
                faixa = _faixa(regra)
                print(f"\n[{indice}/{len(regras)}] {regra.produto}  ({faixa})")

            for loja_cls in lojas:
                loja = loja_cls()
                if loja.chave in bloqueadas:
                    continue

                inicio = time.time()
                try:
                    brutas = loja.buscar(driver, regra.produto, cfg)
                except LojaBloqueada as e:
                    bloqueadas[loja.chave] = str(e)
                    if verboso:
                        print(
                            f"    ! {loja.nome}: {e} — loja descartada nesta rodada "
                            f"(use --perfil ou outro IP)"
                        )
                    continue
                except Exception as e:
                    if verboso:
                        print(f"    ! {loja.nome}: {type(e).__name__}: {e}")
                    if cfg.debug:
                        traceback.print_exc()
                    continue

                aceitas = 0
                for oferta in brutas:
                    ok, motivo = regra.aceita(oferta)
                    if not ok:
                        descartes[motivo.split(" (")[0]] = (
                            descartes.get(motivo.split(" (")[0], 0) + 1
                        )
                        continue
                    chave = oferta.chave_dedupe()
                    if chave in vistos:
                        continue
                    vistos.add(chave)
                    aprovadas.append(oferta)
                    aceitas += 1

                if verboso:
                    segundos = time.time() - inicio
                    print(
                        f"    {loja.nome:<15} {len(brutas):>3} lidos  {aceitas:>3} aprovados"
                        f"  ({segundos:.1f}s)"
                    )

                time.sleep(cfg.pausa_loja)
    finally:
        try:
            driver.quit()
        except Exception:
            pass

    if verboso and descartes:
        resumo = ", ".join(
            f"{k}: {v}" for k, v in sorted(descartes.items(), key=lambda kv: -kv[1])
        )
        print(f"\nDescartes: {resumo}")

    if verboso and bloqueadas:
        nomes = ", ".join(bloqueadas)
        print(f"Lojas fora desta rodada por bloqueio: {nomes}")

    aprovadas.sort(key=lambda o: (o.produto_busca.lower(), o.preco or float("inf")))
    return aprovadas


def _faixa(regra: Regra) -> str:
    if regra.preco_minimo and regra.preco_maximo:
        return f"R$ {regra.preco_minimo:.0f}–{regra.preco_maximo:.0f}"
    if regra.preco_maximo:
        return f"até R$ {regra.preco_maximo:.0f}"
    if regra.preco_minimo:
        return f"a partir de R$ {regra.preco_minimo:.0f}"
    return "sem faixa"
