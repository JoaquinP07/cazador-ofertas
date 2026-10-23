"""Lectores de cada tienda. Cada uno devuelve una lista de Producto."""
from __future__ import annotations

import html
import json
import re
import time
from typing import Callable, Iterable

import requests

from .nucleo import Producto

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/129.0 Safari/537.36"
)
DETALLE: list[str] = []  # notas por categoría, para el reporte de prueba


def nota(txt: str) -> None:
    print(txt)
    DETALLE.append(txt)


SES = requests.Session()
SES.headers.update({"User-Agent": UA, "Accept-Language": "es-UY,es;q=0.9"})


def _get(url: str, **kw) -> requests.Response:
    for intento in range(3):
        try:
            r = SES.get(url, timeout=30, **kw)
            if r.status_code < 500:
                return r
        except requests.RequestException:
            if intento == 2:
                raise
        time.sleep(2 + intento * 3)
    return r


def numero(txt: str) -> float:
    """'7.080' -> 7080 ; '439,00' -> 439.0 ; '1.299,50' -> 1299.5"""
    txt = txt.strip().replace("\xa0", "")
    if "," in txt:
        txt = txt.replace(".", "").replace(",", ".")
    else:
        txt = txt.replace(".", "")
    return float(txt or 0)


def moneda(sim: str) -> str:
    return "USD" if re.search(r"USD|U\$S|US\$", sim, re.I) else "UYU"


# ---------------------------------------------------------------- Fenicio
# (ZonaTecno, AMV Store, Tienda Soy Santander)
_IT = re.compile(r"<div class='it [^']*' data-disp='(\d)' data-codProd='([^']+)' data-codVar='([^']+)'")


def _fenicio_pagina(texto: str, tienda: str) -> list[Producto]:
    prods = []
    cortes = [m.start() for m in _IT.finditer(texto)] + [len(texto)]
    for i, m in enumerate(_IT.finditer(texto)):
        bloque = texto[m.start(): cortes[i + 1]]
        disp, cod, var = m.groups()
        a = re.search(r'<a class="tit" href="([^"]+)" title="([^"]*)"', bloque)
        venta = re.search(
            r'class="precio venta"><span class="sim">([^<]*)</span>\s*<span class="monto">([^<]*)<',
            bloque,
        )
        if not a or not venta:
            continue
        lista = re.search(
            r'class="precio lista"><span class="sim">[^<]*</span>\s*<span class="monto">([^<]*)<',
            bloque,
        )
        precio = numero(venta.group(2))
        prods.append(
            Producto(
                tienda=tienda,
                id=f"{cod}-{var}",
                nombre=html.unescape(a.group(2)),
                precio=precio,
                moneda=moneda(venta.group(1)),
                url=a.group(1),
                precio_lista=numero(lista.group(1)) if lista else None,
                disponible=disp == "1",
            )
        )
    return prods


def fenicio(tienda: str, base: str, categorias: Iterable[str], max_paginas: int = 120) -> list[Producto]:
    vistos: dict[str, Producto] = {}
    for cat in categorias:
        total = None
        for pag in range(1, max_paginas + 1):
            url = f"{base}/{cat}?js=1&pag={pag}"
            r = _get(url)
            if r.status_code != 200:
                nota(f"  [{tienda}] {cat} pág {pag}: HTTP {r.status_code}")
                break
            if total is None:
                t = re.search(r'data-total="(\d+)"', r.text)
                total = int(t.group(1)) if t else 0
            nuevos = _fenicio_pagina(r.text, tienda)
            if not nuevos:
                break
            for p in nuevos:
                vistos[p.clave] = p
            if pag * 12 >= (total or 0):
                break
        nota(f"  [{tienda}] {cat}: {total} declarados")
    return list(vistos.values())


# ---------------------------------------------------------------- Shopify (Cover Company)
def shopify(tienda: str, base: str, moneda_tienda: str = "UYU") -> list[Producto]:
    prods = []
    for pag in range(1, 60):
        r = _get(f"{base}/products.json?limit=250&page={pag}")
        if r.status_code != 200:
            nota(f"  [{tienda}] pág {pag}: HTTP {r.status_code}")
            break
        lote = r.json().get("products", [])
        if not lote:
            break
        for pr in lote:
            for v in pr.get("variants", []):
                nombre = pr["title"] + ("" if v.get("title") in (None, "Default Title") else f" - {v['title']}")
                lista = float(v["compare_at_price"]) if v.get("compare_at_price") else None
                prods.append(
                    Producto(
                        tienda=tienda,
                        id=str(v["id"]),
                        nombre=nombre,
                        precio=float(v["price"]),
                        moneda=moneda_tienda,
                        url=f"{base}/products/{pr['handle']}?variant={v['id']}",
                        precio_lista=lista,
                        disponible=bool(v.get("available", True)),
                    )
                )
    return prods


# ---------------------------------------------------------------- VTEX FastStore (Tata / Multiahorro Hogar)
_FS_QUERY = "https://www.tata.com.uy/api/graphql"


def faststore(tienda: str, base: str, categorias: Iterable[str]) -> list[Producto]:
    vistos: dict[str, Producto] = {}
    for cat in categorias:
        after, total = 0, None
        while True:
            variables = {
                "first": 50,
                "after": str(after),
                "sort": "price_asc",
                "term": "",
                "selectedFacets": [{"key": "category-1", "value": cat}],
            }
            r = _get(
                _FS_QUERY,
                params={"operationName": "ProductsQuery", "variables": json.dumps(variables)},
            )
            if r.status_code != 200:
                nota(f"  [{tienda}] {cat}: HTTP {r.status_code}")
                break
            try:
                datos = r.json()["data"]["search"]["products"]
            except (ValueError, KeyError, TypeError):
                nota(f"  [{tienda}] {cat}: respuesta inesperada {r.text[:200]}")
                break
            total = datos["pageInfo"]["totalCount"]
            for e in datos["edges"]:
                n = e["node"]
                for o in (n.get("offers") or {}).get("offers", [])[:1]:
                    p = Producto(
                        tienda=tienda,
                        id=str(n["sku"]),
                        nombre=n["name"],
                        precio=float(o["price"]),
                        moneda="UYU",
                        url=f"{base}/{n['slug']}/p",
                        precio_lista=float(o["listPrice"]) if o.get("listPrice") else None,
                        disponible="InStock" in (o.get("availability") or ""),
                    )
                    vistos[p.clave] = p
            after += 50
            if after >= total or not datos["edges"] or after >= 3000:
                break
        nota(f"  [{tienda}] {cat}: {total} declarados")
    return list(vistos.values())


# ---------------------------------------------------------------- Devoto (Blazor; solo primera página de cada categoría)
_DEV_ITEM = re.compile(
    r'href="(?:https://www\.devoto\.com\.uy)?/?(product/[a-z0-9-]+/(\d+))"[^>]*>.*?alt="([^"]+)".*?'
    r'(U\$S|\$)\s*</span>\s*<span[^>]*>\s*([\d.,]+)',
    re.S,
)


def devoto(tienda: str, categorias: Iterable[str]) -> list[Producto]:
    vistos: dict[str, Producto] = {}
    for cat in categorias:
        r = _get(f"https://www.devoto.com.uy/products/category/{cat}")
        if r.status_code != 200:
            nota(f"  [{tienda}] {cat}: HTTP {r.status_code}")
            continue
        n = 0
        for m in _DEV_ITEM.finditer(r.text):
            ruta, pid, nombre, sim, monto = m.groups()
            p = Producto(
                tienda=tienda,
                id=pid,
                nombre=html.unescape(nombre),
                precio=numero(monto),
                moneda=moneda(sim),
                url=f"https://www.devoto.com.uy/{ruta}",
            )
            vistos.setdefault(p.clave, p)
            n += 1
        nota(f"  [{tienda}] {cat}: {n} leídos")
    return list(vistos.values())


# ---------------------------------------------------------------- Loi (feed público oficial, límite 100 pedidos/min)
# El filtro por categoría del feed no funciona, así que se trae todo y se descartan rubros ajenos.
_LOI_EXCLUIR = re.compile(
    r"perfum|fragan|maquill|belleza|cosm[eé]t|crema|cabello|piel|u[ñn]as|ropa|moda|calzado|"
    r"zapat|cartera|bolso|mochila|bijou|joya|beb[eé]|juguet|lencer|pijama|remera|buzo|campera",
    re.I,
)


def loi(tienda: str) -> list[Producto]:
    prods: list[Producto] = []
    pag, paginas, descartados = 1, 1, 0
    while pag <= paginas and pag <= 80:
        r = _get(f"https://loi.com.uy/api/v1/products.json?per_page=100&page={pag}")
        if r.status_code != 200:
            nota(f"  [{tienda}] pág {pag}: HTTP {r.status_code}")
            break
        d = r.json()
        paginas = d.get("total_pages") or 0
        for p in d.get("products", []):
            cats = " ".join(c.get("name", "") + " " + c.get("slug", "") for c in p.get("category_hierarchy") or [])
            if _LOI_EXCLUIR.search(cats):
                descartados += 1
                continue
            precio = p.get("price") or {}
            prods.append(
                Producto(
                    tienda=tienda,
                    id=str(p["id"]),
                    nombre=p["title"],
                    precio=float(precio.get("amount") or 0),
                    moneda="USD" if precio.get("currency") == "USD" else "UYU",
                    url=p["url"],
                    precio_lista=float(precio["original_amount"]) if precio.get("original_amount") else None,
                    disponible=p.get("availability") == "in_stock",
                )
            )
        pag += 1
        time.sleep(0.7)  # respeta el límite de 100 pedidos por minuto
    nota(f"  [{tienda}] {len(prods)} leídos, {descartados} de otros rubros descartados")
    return prods


# ---------------------------------------------------------------- Configuración
TIENDAS: dict[str, Callable[[], list[Producto]]] = {
    "Loi": lambda: loi("Loi"),
    "ZonaTecno": lambda: fenicio(
        "ZonaTecno",
        "https://www.zonatecno.com.uy",
        [
            "audio-foto-y-video",
            "celulares-relojes-y-tablets",
            "consolas-y-accesorios",
            "informatica",
            "notebooks-y-pc",
            "movilidad-electrica",
            "zona-home",
        ],
    ),
    "AMV Store": lambda: fenicio(
        "AMV Store",
        "https://amvstore.com.uy",
        [
            "celulares-y-tecnologia",
            "electrodomesticos",
            "informatica",
            "notebooks-y-accesorios",
            "tv-audio-y-video",
        ],
    ),
    "Soy Santander": lambda: fenicio(
        "Soy Santander",
        "https://tienda.soysantander.com.uy",
        [
            "electrodomesticos",
            "gaming",
            "informatica",
            "tecnologia",
            "televisores-audio-y-video",
        ],
    ),
    "Cover Company": lambda: shopify("Cover Company", "https://www.covercompany.com.uy"),
    "Multiahorro / Tata": lambda: faststore(
        "Multiahorro / Tata",
        "https://www.tata.com.uy",
        [
            "electrodomesticos-y-aires-ac-",
            "pequenos-electrodomesticos",
            "climatizacion",
            "smart-tv-y-audio",
            "electronica-audio-y-video",
            "tecnologia",
            "computacion",
            "celulares-y-telefonia",
            "consolas-y-videojuegos",
        ],
    ),
    "Devoto": lambda: devoto(
        "Devoto",
        ["tv-y-audio/20", "celulares-y-telefonia/21", "electrodomesticos/22", "tecnologia/23"],
    ),
}
