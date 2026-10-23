"""Revisión completa: lee las tiendas, compara con el historial y avisa por Telegram.

Uso:
  python -m cazador            # revisión normal
  python -m cazador --prueba   # además guarda una muestra en reporte/ y manda un mensaje de prueba
"""
from __future__ import annotations

import json
import pathlib
import sys
import time
import traceback

from . import telegram
from .nucleo import Historial, fmt
from .tiendas import DETALLE, TIENDAS

HISTORIAL = pathlib.Path("estado/historial.json")


def main() -> int:
    prueba = "--prueba" in sys.argv
    hist = Historial(HISTORIAL)
    primera_vez = not hist.datos
    resumen, muestras, avisos = {}, {}, 0
    inicio = time.time()

    for nombre, leer in TIENDAS.items():
        t0 = time.time()
        try:
            prods = leer()
        except Exception:  # una tienda caída no frena a las demás
            traceback.print_exc()
            resumen[nombre] = "error"
            continue
        resumen[nombre] = f"{len(prods)} productos en {time.time() - t0:.0f}s"
        muestras[nombre] = [p.__dict__ for p in prods[:15]]
        for p in prods:
            motivo = hist.evaluar(p)
            # En la primera corrida no hay historial: solo se aprende, no se avisa.
            if motivo and not primera_vez:
                avisos += 1
                print("AVISO:", p.tienda, p.nombre, fmt(p.precio, p.moneda), motivo)
                telegram.enviar(telegram.aviso(p, motivo))
        print(f"{nombre}: {resumen[nombre]}")

    hist.limpiar()
    hist.guardar()
    duracion = time.time() - inicio
    print(f"Listo en {duracion:.0f}s · {len(hist.datos)} productos en historial · {avisos} avisos")

    if prueba:
        rep = pathlib.Path("reporte")
        rep.mkdir(exist_ok=True)
        (rep / "resumen.json").write_text(
            json.dumps({"tiendas": resumen, "duracion_s": round(duracion), "historial": len(hist.datos), "detalle": DETALLE},
                       ensure_ascii=False, indent=2), encoding="utf-8")
        (rep / "muestras.json").write_text(json.dumps(muestras, ensure_ascii=False, indent=1), encoding="utf-8")
        lineas = "\n".join(f"• {k}: {v}" for k, v in resumen.items())
        telegram.enviar(f"✅ <b>Cazador de ofertas conectado</b>\nRevisión de prueba:\n{lineas}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
