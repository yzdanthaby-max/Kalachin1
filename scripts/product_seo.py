import json, html, urllib.request, pathlib, re, datetime, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
BASE = "https://yzdanthaby-max.github.io/Kalachin1"
API = "https://chyhxnkdewkslwrrpboq.supabase.co/rest/v1/Products"
KEY = "sb_publishable_qi3iOgtJHzzRlPIw35Av6A_6uj4vZJ4"
OUT = ROOT / "products"

def fetch():
    fields = "id,sku,name,brand,category,description,image_url,price,old_price,is_active,stock"
    url = API + "?select=" + fields + "&is_active=eq.true&limit=1000"
    req = urllib.request.Request(url, headers={"apikey": KEY})
    with urllib.request.urlopen(req, timeout=40) as res:
        data = json.load(res)
    if not isinstance(data, list) or not data:
        raise RuntimeError("Supabase محصولی برنگرداند؛ فایل‌ها ساخته نشدند.")
    if any(not p.get("id") or not p.get("name") for p in data):
        raise RuntimeError("بعضی محصولات شناسه یا نام ندارند؛ متوقف شد.")
    if len({p["id"] for p in data}) != len(data):
        raise RuntimeError("شناسه تکراری است؛ متوقف شد.")
    return data

def esc(x):
    return html.escape(str(x or ""), quote=True)

def page(p):
    name = esc(p.get("name"))
    desc = esc(p.get("description") or p.get("name"))
    sku = esc(p.get("sku") or p.get("id"))
    brand = esc(p.get("brand") or "کالاچین")
    image = esc(p.get("image_url"))
    url = BASE + "/products/" + str(p["id"]) + "/"
    price = p.get("price")
    price_tag = f'<meta property="product:price:amount" content="{esc(price)}"><meta property="product:price:currency" content="IRR">' if isinstance(price, (int,float)) else ""
    stock = p.get("stock")
    avail = "https://schema.org/InStock" if stock is None or stock > 0 else "https://schema.org/OutOfStock"
    product_json = json.dumps({
        "@context":"https://schema.org","@type":"Product","name":p["name"],
        "sku":p.get("sku") or p["id"],"description":p.get("description") or p["name"],
        "image":[p["image_url"]] if p.get("image_url") else [],
        "brand":{"@type":"Brand","name":p.get("brand") or "کالاچین"},
        "offers":{"@type":"Offer","url":url,"priceCurrency":"IRR","price":price * 10 if isinstance(price, (int, float)) else None,
                  "availability":avail}
    }, ensure_ascii=False).replace("</", "<\\/")
    return f'''<!doctype html>
<html lang="fa" dir="rtl">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{name} | کالاچین</title>
<meta name="description" content="{desc} | خرید آنلاین از کالاچین">
<meta name="robots" content="index,follow">
<link rel="canonical" href="{url}">
<meta property="og:type" content="product"><meta property="og:site_name" content="کالاچین">
<meta property="og:title" content="{name} | کالاچین"><meta property="og:description" content="{desc}">
<meta property="og:url" content="{url}"><meta property="og:image" content="{image}">
{price_tag}
<script type="application/ld+json">{product_json}</script>
<style>
body{{font-family:Tahoma,Arial,sans-serif;max-width:850px;margin:35px auto;padding:20px;line-height:2;color:#222}}
header,footer{{padding:12px 0;border-bottom:1px solid #ddd}}a{{color:#146b55}}
main{{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:25px;align-items:start}}
img{{width:100%;height:auto;object-fit:contain}}.price{{font-size:1.5rem;font-weight:bold}}
.btn{{display:inline-block;background:#1c2440;color:white;padding:10px 18px;border-radius:9px;text-decoration:none}}
@media(max-width:600px){{main{{grid-template-columns:1fr}}}}
</style>
</head><body>
<header><a href="{BASE}/">کالاچین | فروشگاه اینترنتی</a></header>
<main><section>{f'<img src="{image}" alt="{name}" fetchpriority="high">' if image else ''}</section>
<article><h1>{name}</h1><p>{desc}</p><p>برند: {brand}</p><p>شناسه کالا: {sku}</p>
{f'<p class="price">{html.escape(format(price, ",") )} تومان</p>' if isinstance(price,(int,float)) else ''}
<a class="btn" href="{BASE}/#/p/{esc(p["id"])}">مشاهده و خرید محصول</a>
<p><a href="{BASE}/#/shop">مشاهده همه محصولات</a></p></article></main>
<footer><a href="{BASE}/">صفحه اصلی کالاچین</a></footer>
</body></html>'''

def main():
    products = fetch()
    OUT.mkdir(exist_ok=True)
    urls = []
    for p in products:
        slug = re.sub(r"[^A-Za-z0-9_-]", "-", str(p["id"]))
        folder = OUT / slug
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "index.html").write_text(page(p), encoding="utf-8")
        urls.append(BASE + "/products/" + slug + "/")
    today = datetime.date.today().isoformat()
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n' + '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    sitemap += f'  <url><loc>{BASE}/</loc><lastmod>{today}</lastmod></url>\n'
    sitemap += "".join(f'  <url><loc>{html.escape(u)}</loc><lastmod>{today}</lastmod></url>\n' for u in urls)
    sitemap += '</urlset>\n'
    (ROOT / "sitemap.xml").write_text(sitemap, encoding="utf-8")
    (ROOT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {BASE}/sitemap.xml\n", encoding="utf-8")
    print(f"✅ صفحات ساخته شد: {len(products)}")
    print(f"📄 sitemap.xml: {len(urls)} محصول + صفحه اصلی")
    print("🤖 robots.txt ساخته شد")
    print("ℹ️ این مرحله فقط فایل می‌سازد؛ هنوز منتشر نشده.")
    print("نمونه:", urls[0])

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("❌ خطا:", e)
        sys.exit(1)
