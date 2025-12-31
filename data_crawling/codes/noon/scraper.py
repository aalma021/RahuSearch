import os, re, json, time, requests
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from seleniumbase import Driver

# ================= ENV =================
load_dotenv()

START_URL = os.getenv("START_URL")  # https://www.noon.com/uae-en/search/?q=iphone
GROUP     = os.getenv("GROUP", "iphone")
LIMIT     = int(os.getenv("LIMIT", 50))
HEADLESS  = os.getenv("HEADLESS", "true").lower() == "true"
MAX_IMAGES = 5

OUT_ROOT = "data/noon"
OUT_FILE = f"{OUT_ROOT}/{GROUP}/products.jsonl"
os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)

BASE = "https://www.noon.com"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
HEADERS = {"User-Agent": UA}


# ================= UTILS =================
def clean(s):
    return re.sub(r"\s+", " ", s or "").strip()


def to_price(txt):
    if not txt:
        return None
    m = re.search(r"(\d[\d,\.]*)", txt)
    if not m:
        return None
    try:
        return int(float(m.group(1).replace(",", "")))
    except:
        return None


def append(row):
    with open(OUT_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())


# ================= PDP =================
def scrape_pdp(driver, url_ar, pid):
    print(f"    [PDP] OPEN {url_ar}")
    driver.get(url_ar)
    time.sleep(2)

    soup = BeautifulSoup(driver.page_source, "html.parser")

    # ---- title_ar ----
    t = soup.select_one("span.ProductTitle-module-scss-module__EXiEUa__title")
    title_ar = clean(t.text) if t else None
    print(f"    [PDP] title_ar = {title_ar}")

    # ---- images (MAX 5) ----
    img_urls = []
    for img in soup.select("button img"):
        src = img.get("src", "")
        if "nooncdn.com/p/pnsku/" not in src:
            continue

        clean_src = src.split("?")[0]
        if clean_src not in img_urls:
            img_urls.append(clean_src)

        if len(img_urls) >= MAX_IMAGES:
            break

    print(f"    [PDP] found {len(img_urls)} images")

    image_paths = []
    if img_urls:
        save_dir = f"{OUT_ROOT}/{GROUP}/{pid}"
        os.makedirs(save_dir, exist_ok=True)

        for idx, url in enumerate(img_urls, 1):
            try:
                fp = f"{save_dir}/{idx:02d}.jpg"
                r = requests.get(url, headers=HEADERS, timeout=30)
                if r.ok:
                    with open(fp, "wb") as f:
                        f.write(r.content)
                    image_paths.append(fp.replace(OUT_ROOT + "/", ""))
                    print(f"    [IMG] saved {fp}")
            except Exception as e:
                print(f"    [IMG] fail {url} → {e}")

    return title_ar, img_urls, image_paths


# ================= MAIN =================
def main():
    driver = Driver(uc=True, headless=HEADLESS)
    collected = 0

    print(f"[START] {START_URL}")
    driver.get(START_URL)
    time.sleep(3)

    soup = BeautifulSoup(driver.page_source, "html.parser")

    # ---- PLP LINKS ----
    product_links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/p/" in href and "uae-en" in href:
            url = href if href.startswith("http") else BASE + href
            if url not in product_links:
                product_links.append(url)

    print(f"[PLP] found {len(product_links)} product links")

    # ---- ITEMS ----
    for url_en in product_links:
        if collected >= LIMIT:
            break

        print(f"\n[ITEM] OPEN {url_en}")
        driver.get(url_en)
        time.sleep(2)

        soup = BeautifulSoup(driver.page_source, "html.parser")

        # title_en
        h1 = soup.find("h1")
        title_en = clean(h1.text) if h1 else None
        print(f"[ITEM] title_en = {title_en}")
        if not title_en:
            print("[SKIP] no title_en")
            continue

        # price
        price_node = soup.find("strong")
        price = to_price(price_node.text if price_node else None)
        print(f"[ITEM] price = {price}")
        if not price:
            print("[SKIP] no price")
            continue

        # pid
        pid_match = re.search(r"/([^/]+)/p/", url_en)
        pid = pid_match.group(1) if pid_match else None
        print(f"[ITEM] pid = {pid}")
        if not pid:
            print("[SKIP] no pid")
            continue

        # PDP (AR)
        title_ar, img_urls, img_paths = scrape_pdp(
            driver, url_en.replace("/uae-en/", "/uae-ar/"), pid
        )

        append({
            "id": pid,
            "store": "Noon",
            "group": GROUP,
            "url_en": url_en,
            "url": url_en.replace("/uae-en/", "/uae-ar/"),
            "price_aed": price,
            "title_en": title_en,
            "title_ar": title_ar,
            "image_urls": img_urls,
            "image_paths": img_paths,
        })

        collected += 1
        print(f"[SAVED] {pid} ({collected}/{LIMIT})")

    driver.quit()
    print(f"\n[DONE] {collected} ürün → {OUT_FILE}")


if __name__ == "__main__":
    main()
