"""Sondeo inicial: revisa cómo responde cada tienda para elegir la mejor forma de leerla.

Guarda lo que encuentra en la carpeta `sondeo/` (se sube como resultado de la ejecución).
"""
import json
import pathlib
import re

import requests

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/129.0 Safari/537.36"
)

URLS = {
    "zt_cat": "https://www.zonatecno.com.uy/celulares-relojes-y-tablets",
    "zt_cat_p2": "https://www.zonatecno.com.uy/celulares-relojes-y-tablets?pag=2",
    "zt_cat_ord": "https://www.zonatecno.com.uy/celulares-relojes-y-tablets?ord=pre-asc",
    "tata_vtex": "https://www.tata.com.uy/api/catalog_system/pub/products/search?ft=televisor&_from=0&_to=2",
    "tata_is": "https://www.tata.com.uy/api/io/_v/api/intelligent-search/product_search/?query=televisor&count=2",
    "tata_tree": "https://www.tata.com.uy/api/catalog_system/pub/category/tree/2",
    "devoto_cat": "https://www.devoto.com.uy/products/category/9115",
    "devoto_beta_cat": "https://beta.devoto.com.uy/products/category/9115",
    "devoto_busq": "https://www.devoto.com.uy/products/search?text=televisor",
    "ti_cffi": "CFFI:https://www.tiendainglesa.com.uy/supermercado/busqueda?0,0,televisor,0",
    "ml_api_cffi": "CFFI:https://api.mercadolibre.com/sites/MLU/search?q=televisor&limit=2",
    "ml_listado_cffi": "CFFI:https://listado.mercadolibre.com.uy/televisores_Tienda_all",
    "ml_ofertas_cffi": "CFFI:https://www.mercadolibre.com.uy/ofertas",
}
_VIEJAS = {
    "tiendainglesa_home": "https://www.tiendainglesa.com.uy/",
    "tiendainglesa_busqueda": "https://www.tiendainglesa.com.uy/supermercado/busqueda?0,0,televisor,0",
    "devoto_home": "https://www.devoto.com.uy/",
    "devoto_vtex": "https://www.devoto.com.uy/api/catalog_system/pub/products/search?ft=televisor&_from=0&_to=5",
    "multiahorro_home": "https://www.multiahorro.com.uy/",
    "multiahorro_vtex": "https://www.multiahorro.com.uy/api/catalog_system/pub/products/search?ft=televisor&_from=0&_to=5",
    "zonatecno_home": "https://www.zonatecno.com.uy/",
    "zonatecno_shopify": "https://www.zonatecno.com.uy/products.json?limit=5",
    "zonatecno_woo": "https://www.zonatecno.com.uy/wp-json/wc/store/v1/products?per_page=5",
    "amv_home": "https://www.amvstore.com.uy/",
    "amv_shopify": "https://www.amvstore.com.uy/products.json?limit=5",
    "amv_woo": "https://www.amvstore.com.uy/wp-json/wc/store/v1/products?per_page=5",
    "amv_vtex": "https://www.amvstore.com.uy/api/catalog_system/pub/products/search?_from=0&_to=5",
    "cover_home": "https://www.covercompany.com.uy/",
    "cover_shopify": "https://www.covercompany.com.uy/products.json?limit=5",
    "cover_woo": "https://www.covercompany.com.uy/wp-json/wc/store/v1/products?per_page=5",
    "cover_vtex": "https://www.covercompany.com.uy/api/catalog_system/pub/products/search?_from=0&_to=5",
    "santander_home": "https://tienda.soysantander.com.uy/",
    "santander_catalogo": "https://tienda.soysantander.com.uy/catalogo",
    "ml_api": "https://api.mercadolibre.com/sites/MLU/search?category=MLU1051&official_store=all&limit=5",
    "ml_listado": "https://listado.mercadolibre.com.uy/celulares-telefonos/celulares-smartphones/_Tienda_all",
}

SENALES = {
    "vtex": r"vtex",
    "shopify": r"cdn\.shopify|Shopify\.shop",
    "woocommerce": r"woocommerce|wp-content",
    "magento": r"Magento|mage/",
    "genexus": r"GeneXus|gxcfg",
    "nextjs": r"__NEXT_DATA__",
    "jsonld_product": r'"@type"\s*:\s*"Product"',
}

out = pathlib.Path("sondeo")
out.mkdir(exist_ok=True)
resumen = {}
s = requests.Session()
s.headers.update({"User-Agent": UA, "Accept-Language": "es-UY,es;q=0.9"})

for nombre, url in URLS.items():
    try:
        if url.startswith("CFFI:"):
            from curl_cffi import requests as creq
            r = creq.get(url[5:], impersonate="chrome", timeout=30)
        else:
            r = s.get(url, timeout=30, allow_redirects=True)
        texto = r.text
        (out / f"{nombre}.txt").write_text(texto[:400_000], encoding="utf-8")
        resumen[nombre] = {
            "status": r.status_code,
            "url_final": r.url,
            "tipo": r.headers.get("content-type"),
            "server": r.headers.get("server"),
            "tamano": len(texto),
            "senales": [k for k, p in SENALES.items() if re.search(p, texto, re.I)],
            "inicio": texto[:300],
        }
    except Exception as e:  # noqa: BLE001
        resumen[nombre] = {"error": repr(e)}
    print(nombre, json.dumps(resumen[nombre], ensure_ascii=False)[:400])

(out / "resumen.json").write_text(json.dumps(resumen, indent=2, ensure_ascii=False), encoding="utf-8")
