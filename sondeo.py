import json, pathlib, re, requests
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36"
URLS = {
    "loi_all": "https://loi.com.uy/api/v1/products.json?per_page=3",
    "loi_all_nostock": "https://loi.com.uy/api/v1/products.json?per_page=3&in_stock=false",
    "loi_q": "https://loi.com.uy/api/v1/products.json?q=televisor&per_page=3",
    "loi_openapi": "https://loi.com.uy/.well-known/openapi.json",
    "loi_tools": "https://loi.com.uy/api/v1/tools.json",
    "loi_tec_html": "https://loi.com.uy/tecnologia",
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
