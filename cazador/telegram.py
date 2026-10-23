"""Envío de avisos por Telegram."""
from __future__ import annotations

import html
import os

import requests

from .nucleo import Producto, fmt


def enviar(texto: str) -> bool:
    token = os.environ.get("TELEGRAM_TOKEN")
    chat = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat:
        print("[telegram] faltan TELEGRAM_TOKEN / TELEGRAM_CHAT_ID; mensaje no enviado:\n" + texto)
        return False
    r = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={
            "chat_id": chat,
            "text": texto,
            "parse_mode": "HTML",
            "disable_web_page_preview": False,
        },
        timeout=20,
    )
    if not r.ok:
        print("[telegram] error", r.status_code, r.text[:300])
    return r.ok


def aviso(p: Producto, motivo: str) -> str:
    return (
        f"🚨 <b>Posible error de precio</b> — {html.escape(p.tienda)}\n"
        f"{html.escape(p.nombre)}\n"
        f"<b>{fmt(p.precio, p.moneda)}</b> · {html.escape(motivo)}\n"
        f'<a href="{html.escape(p.url, quote=True)}">Ver producto</a>'
    )
