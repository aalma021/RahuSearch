import os, re, json, time
from urllib.parse import urlencode, urlparse, parse_qs, urlunparse
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from seleniumbase import Driver

from common.image_to_text import image_to_text

# =================================================
# ENV
# =================================================
load_dotenv()

SITE_NAME  = os.getenv("SITE_NAME", "extra")
SITE_URL   = os.getenv("SITE_URL")
GROUP      = os.getenv("GROUP", "Default")
LIMIT      = int(os.getenv("LIMIT", 50))
MAX_IMAGES = int(os.getenv("MAX_IMAGES", 5))
HEADLESS   = os.getenv("HEADLESS", "false").lower() == "true"
LOCALE     = os.getenv("LOCALE", "en_US")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

OUT_ROOT = os.path.join(BASE_DIR, "data")
OUT_FILE = os.path.join(OUT_ROOT, GROUP, f"products_{GROUP}.jsonl")
os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)

AR_DIG = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")

# =================================================
# UTILS
# =================================================
def clean(s):
    return re.sub(r"\s+", " ", s or "").strip()

def to_price(txt):
    if not txt:
        return None
    t = str(txt).translate(AR_DIG)
    m = re.search(r"(\d[\d,\.]*)", t)
    return int(float(m.group(1).replace(",", ""))) if m else None

def to_ar_url(url_en):
    pu = urlparse(url_en)
    return urlunparse((
        pu.scheme,
        pu.netloc,
        pu.path.replace("/en-sa/", "/ar-sa/"),
        "",
        "",
        ""
    ))

# =================================================
# DUPLICATE PREVENTION
# =================================================
def load_seen_ids(path):
    ids = set()
    if not os.path.isfile(path):
        return ids
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                obj = json.loads(line)
                if "id" in obj:
                    ids.add(str(obj["id"]))
            except:
                pass
    return ids

# =================================================
# PAGE HELPERS
# =================================================
def wait_ready(drv, timeout=20):
    end = time.time() + timeout
    while time.time() < end:
        try:
            if drv.execute_script("return document.readyState") == "complete":
                return
        except:
            pass
        time.sleep(0.25)

def warmup(drv):
    wait_ready(drv, 25)
    for y in (400, 1200, 2400):
        try:
            drv.execute_script(f"window.scrollTo(0,{y})")
            time.sleep(0.3)
        except:
            pass
    drv.execute_script("window.scrollTo(0,0)")
    time.sleep(0.5)

def scroll_bottom(drv, max_idle=4):
    last, idle = 0, 0
    while idle < max_idle:
        drv.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(0.8)
        h = drv.execute_script("return document.body.scrollHeight")
        idle = idle + 1 if h == last else 0
        last = h

# =================================================
# SEARCH URL (SITE_URL BASED)
# =================================================
def build_search_url(page: int) -> str:
    pu = urlparse(SITE_URL)
    qs = parse_qs(pu.query)

    qs["pg"] = [str(page)]
    qs.setdefault("pageSize", ["48"])
    qs.setdefault("sort", ["relevance"])

    return urlunparse((
        pu.scheme,
        pu.netloc,
        pu.path,
        "",
        urlencode(qs, doseq=True),
        ""
    ))

# =================================================
# LISTING
# =================================================
def extract_listing(soup):
    cards = []
    for t in soup.select(".product-tile-container"):
        btn = t.select_one("[data-sku]") or t.select_one("[data-qac-button]")
        if not btn:
            continue

        sku = re.sub(r"[^\d]", "", btn.get("data-sku") or btn.get("data-qac-button") or "")
        if not sku:
            continue

        title_node = t.select_one(".product-name-data")
        price_node = t.select_one("section.price strong")
        brand_node = t.select_one(".brand-name")

        title = clean(title_node.text) if title_node else None
        price = to_price(price_node.text) if price_node else None
        brand = clean(brand_node.text).title() if brand_node else (title.split()[0].title() if title else None)

        tags = [clean(li.text) for li in t.select("ul.product-stats li") if clean(li.text)]

        if not title or not price:
            continue

        cards.append({
            "id": sku,
            "url_en": f"https://www.extra.com/en-sa/p/{sku}",
            "brand": brand,
            "title_en": title,
            "price_sar": price,
            "tags_en": tags,
        })

    return cards

# =================================================
# PDP + IMAGES
# =================================================
IMG_SEL   = "img[class^='svelte']"
TITLE_SEL = "h2.product-name"
TAG_SEL   = "div.card-title"

def scrape_pdp_and_images(driver, url_ar):
    driver.get(url_ar)
    warmup(driver)
    scroll_bottom(driver)

    soup = BeautifulSoup(driver.page_source, "html.parser")

    title_ar = clean(soup.select_one(TITLE_SEL).text) if soup.select_one(TITLE_SEL) else None
    tags_ar = [clean(n.text) for n in soup.select(TAG_SEL) if clean(n.text)]

    img_urls = []
    for img in soup.select(IMG_SEL):
        if len(img_urls) >= MAX_IMAGES:
            break

        src = img.get("src")
        if not src or "media.extra.com" not in src:
            continue
        if src.startswith("//"):
            src = "https:" + src

        src = src.split("?")[0] + "?fmt=auto&w=800"
        if src not in img_urls:
            img_urls.append(src)

    return title_ar, tags_ar, img_urls

def download_images_selenium(driver, urls, sku):
    save_dir = os.path.join(OUT_ROOT, GROUP, sku)
    os.makedirs(save_dir, exist_ok=True)

    paths = []
    for i, url in enumerate(urls[:MAX_IMAGES], 1):
        try:
            driver.get(url)
            time.sleep(0.8)

            data = driver.execute_async_script("""
                const cb = arguments[0];
                fetch(window.location.href)
                  .then(r => r.arrayBuffer())
                  .then(b => cb(new Uint8Array(b)))
                  .catch(_ => cb(null));
            """)

            if not data:
                continue

            fp = os.path.join(save_dir, f"{i:02d}.jpg")
            with open(fp, "wb") as f:
                f.write(bytearray(data))

            paths.append(os.path.relpath(fp, OUT_ROOT).replace("\\", "/"))

        except Exception as e:
            print(f"[IMG FAIL] {url} -> {e}")

    return paths

# =================================================
# MAIN
# =================================================
def main():
    seen = load_seen_ids(OUT_FILE)
    print(f"[INIT] existing products: {len(seen)}")

    driver = Driver(
        uc=True,
        headless=HEADLESS,
        incognito=True,
        locale_code=LOCALE
    )

    collected, page = 0, 1

    try:
        while collected < LIMIT:
            url = build_search_url(page)
            print(f"[PAGE {page}] {url}")

            driver.get(url)
            warmup(driver)
            scroll_bottom(driver)

            soup = BeautifulSoup(driver.page_source, "html.parser")
            cards = extract_listing(soup)
            if not cards:
                break

            for c in cards:
                if c["id"] in seen:
                    continue
                seen.add(c["id"])

                url_ar = to_ar_url(c["url_en"])
                title_ar, tags_ar, img_urls = scrape_pdp_and_images(driver, url_ar)
                img_paths = download_images_selenium(driver, img_urls, c["id"])

                # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
                # YENİ: image_to_text (SADECE EKLEME)
                # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
                abs_img_paths = [os.path.join(OUT_ROOT, p) for p in img_paths]
                print("image to text called")
                img_to_text = image_to_text(abs_img_paths) if abs_img_paths else None

                row = {
                    "id": c["id"],
                    "store": SITE_NAME.capitalize(),
                    "group": GROUP,
                    "url_en": c["url_en"],
                    "url": url_ar,
                    "brand": c["brand"],
                    "price_sar": c["price_sar"],
                    "title_en": c["title_en"],
                    "title_ar": title_ar,
                    "tags_en": c["tags_en"],
                    "tags_ar": tags_ar,
                    "image_urls": img_urls,
                    "image_paths": img_paths,
                    "image_to_text": img_to_text,
                    "text_search": clean(
                        " ".join([c["title_en"], c["brand"], GROUP] + c["tags_en"])
                    ),
                }

                with open(OUT_FILE, "a", encoding="utf-8") as f:
                    f.write(json.dumps(row, ensure_ascii=False) + "\n")

                collected += 1
                print(f"  [+] {c['id']} imgs={len(img_paths)} ({collected}/{LIMIT})")

                if collected >= LIMIT:
                    break

            page += 1

    finally:
        driver.quit()

    print(f"[DONE] {collected} new products → {OUT_FILE}")

if __name__ == "__main__":
    main()
