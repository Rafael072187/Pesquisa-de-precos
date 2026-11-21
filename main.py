# language: Python 3.11+, file: main.py
"""Ponto de entrada. `python main.py --help` mostra as opções."""

import sys

from pesquisa_precos.cli import main

if __name__ == "__main__":
    sys.exit(main())
