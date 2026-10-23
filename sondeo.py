import json, pathlib, re, requests
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36"
URLS = {
    "loi_home": "https://www.loi.com.uy/",
    "loi_shopify": "https://www.loi.com.uy/products.json?limit=3",
    "loi_vtex": "https://www.loi.com.uy/api/catalog_system/pub/products/search?_from=0&_to=2",
    "loi_woo": "https://www.loi.com.uy/wp-json/wc/store/v1/products?per_page=3",
}
out = pathlib.Path("sondeo"); out.mkdir(exist_ok=True)
res = {}
for n, u in URLS.items():
    try:
        r = requests.get(u, headers={"User-Agent": UA, "Accept-Language": "es-UY"}, timeout=30)
        (out / f"{n}.txt").write_text(r.text[:3_000_000], encoding="utf-8")
        res[n] = {"status": r.status_code, "url_final": r.url, "tipo": r.headers.get("content-type"), "server": r.headers.get("server"),
                  "tamano": len(r.text), "senales": [k for k, p in {"fenicio": "fenicio", "vtex": "vtex", "shopify": r"cdn\.shopify", "woo": "woocommerce", "next": "__NEXT_DATA__"}.items() if re.search(p, r.text, re.I)]}
    except Exception as e:
        res[n] = {"error": repr(e)}
(out / "resumen.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
