# language: Python 3.11+, file: pesquisa_precos/email_outlook.py
from __future__ import annotations

from pathlib import Path


def enviar(
    destinatarios: list[str],
    assunto: str,
    corpo_html: str,
    anexos: list[Path] | None = None,
) -> None:
    """Envia pelo Outlook instalado (COM). Levanta RuntimeError se o COM falhar."""
    if not destinatarios:
        raise ValueError("Nenhum destinatário informado.")

    try:
        import win32com.client as win32  # type: ignore
    except ImportError as e:
        raise RuntimeError(
            "pywin32 não está instalado. Rode: pip install pywin32"
        ) from e

    try:
        outlook = win32.Dispatch("outlook.application")
    except Exception as e:
        raise RuntimeError(
            "Outlook não respondeu ao COM. Ele precisa estar instalado e já "
            "configurado com uma conta."
        ) from e

    mail = outlook.CreateItem(0)
    mail.To = "; ".join(destinatarios)
    mail.Subject = assunto
    mail.HTMLBody = corpo_html

    for anexo in anexos or []:
        caminho = Path(anexo).resolve()
        if caminho.exists():
            mail.Attachments.Add(str(caminho))

    mail.Send()
