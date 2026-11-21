# language: Python 3.11+, file: pesquisa_precos/cli.py
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .config import Config
from .email_outlook import enviar
from .entrada import criar_modelo, ler_regras
from .imagens import baixar_lote
from .lojas import TODAS, resolver
from .pesquisa import pesquisar
from .relatorio import (
    corpo_email,
    salvar_csv,
    salvar_html,
    salvar_xlsx,
    tabela_terminal,
)


def montar_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="pesquisa-precos",
        description="Pesquisa preços em marketplaces e devolve valor, parcelamento, link e imagem.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""exemplos:
  python main.py
  python main.py --lojas mercadolivre,kabum --limite 30 --headless
  python main.py --entrada buscas.xlsx --saida ofertas.xlsx --html relatorio.html
  python main.py --detalhar --email voce@dominio.com
""",
    )
    p.add_argument(
        "-e",
        "--entrada",
        default="buscas.xlsx",
        help="planilha de buscas (padrão: buscas.xlsx)",
    )
    p.add_argument(
        "-s",
        "--saida",
        default="ofertas.xlsx",
        help="planilha de saída (padrão: ofertas.xlsx)",
    )
    p.add_argument(
        "--html",
        default="relatorio.html",
        help="relatório visual (padrão: relatorio.html)",
    )
    p.add_argument("--csv", default=None, help="também exporta CSV neste caminho")
    p.add_argument(
        "-l",
        "--lojas",
        default=",".join(TODAS),
        help=f"lojas separadas por vírgula: {', '.join(TODAS)}",
    )
    p.add_argument(
        "--limite",
        type=int,
        default=20,
        help="cartões lidos por loja e produto (padrão: 20)",
    )
    p.add_argument(
        "--pausa", type=float, default=1.5, help="segundos entre lojas (padrão: 1.5)"
    )
    p.add_argument(
        "--headless",
        action="store_true",
        help="navegador invisível (mais chance de bloqueio)",
    )
    p.add_argument(
        "--navegador", default=None, help="caminho do brave.exe/chrome.exe/msedge.exe"
    )
    p.add_argument(
        "--perfil",
        default=None,
        help="pasta de perfil para reaproveitar cookies entre execuções",
    )
    p.add_argument(
        "--sem-imagens",
        action="store_true",
        help="não baixa miniaturas (planilha sem foto)",
    )
    p.add_argument(
        "--dir-imagens",
        default=None,
        help="pasta das miniaturas (padrão: imagens/ ao lado da planilha de saída)",
    )
    p.add_argument(
        "--detalhar",
        action="store_true",
        help="abre a página do produto quando o cartão não mostra parcelamento",
    )
    p.add_argument(
        "--debug", action="store_true", help="salva o HTML das coletas vazias em debug/"
    )
    p.add_argument(
        "--email",
        default=None,
        help="destinatários separados por vírgula (envia pelo Outlook)",
    )
    p.add_argument("--assunto", default="Ofertas encontradas", help="assunto do e-mail")
    p.add_argument(
        "--criar-modelo", action="store_true", help="cria buscas.xlsx de exemplo e sai"
    )
    p.add_argument("--versao", action="version", version=f"%(prog)s {__version__}")
    return p


def main(argv: list[str] | None = None) -> int:
    for fluxo in (sys.stdout, sys.stderr):
        try:
            fluxo.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
        except (AttributeError, ValueError):
            pass

    args = montar_parser().parse_args(argv)

    if args.criar_modelo:
        destino = criar_modelo(args.entrada)
        print(f"Modelo pronto: {destino}")
        return 0

    try:
        lojas = resolver([l for l in args.lojas.split(",") if l.strip()])
    except ValueError as e:
        print(f"erro: {e}")
        return 2

    cfg = Config(
        navegador_path=args.navegador,
        headless=args.headless,
        perfil_dir=args.perfil,
        max_resultados=max(1, args.limite),
        pausa_loja=max(0.0, args.pausa),
        baixar_imagens=not args.sem_imagens,
        detalhar=args.detalhar,
        debug=args.debug,
    )
    # as miniaturas moram ao lado do relatório: o HTML referencia caminho relativo
    cfg.dir_imagens = (
        Path(args.dir_imagens)
        if args.dir_imagens
        else Path(args.html).parent / "imagens"
    )

    try:
        regras = ler_regras(args.entrada)
    except FileNotFoundError as e:
        print(f"erro: {e}")
        return 2

    if not regras:
        print(f"erro: nenhuma linha válida em {args.entrada}")
        return 2

    print(f"pesquisando {len(regras)} produto(s) em {len(lojas)} loja(s)…")
    print(
        f"navegador: {cfg.localizar_navegador() or 'padrão do Selenium'}  |  headless: {cfg.headless}"
    )

    try:
        ofertas = pesquisar(regras, lojas, cfg)
    except KeyboardInterrupt:
        print("\ninterrompido.")
        return 130
    except RuntimeError as e:
        print(f"erro: {e}")
        return 3

    print()
    print(tabela_terminal(ofertas))

    if not ofertas:
        print(
            "\nNada passou nos filtros. Ajuste a faixa de preço ou os termos banidos."
        )
        return 0

    miniaturas = {}
    if cfg.baixar_imagens:
        urls = {i: o.imagem for i, o in enumerate(ofertas) if o.imagem}
        if urls:
            print(f"\nbaixando {len(urls)} imagem(ns)…")
            miniaturas = baixar_lote(urls, cfg.dir_imagens)
            print(f"  {len(miniaturas)} baixada(s) em {cfg.dir_imagens}/")

    planilha = salvar_xlsx(ofertas, args.saida, miniaturas)
    print(f"planilha: {planilha}")

    if args.csv:
        print(f"csv: {salvar_csv(ofertas, args.csv)}")

    relatorio = salvar_html(ofertas, args.html, miniaturas)
    print(f"relatório: {relatorio}")

    if args.email:
        destinatarios = [d.strip() for d in args.email.split(",") if d.strip()]
        try:
            enviar(
                destinatarios,
                args.assunto,
                f"<p>{len(ofertas)} oferta(s) dentro da faixa pedida.</p>"
                + corpo_email(ofertas),
                [Path(args.saida)],
            )
            print(f"e-mail enviado para: {', '.join(destinatarios)}")
        except Exception as e:
            print(f"falha no e-mail: {e}")
            return 4

    return 0


if __name__ == "__main__":
    sys.exit(main())
