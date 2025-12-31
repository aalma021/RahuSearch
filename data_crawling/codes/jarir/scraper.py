import os, re, json, time
import requests
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from seleniumbase import Driver

from common.image_to_text import image_to_text

# ================= ENV =================
load_dotenv()

SITE_NAME  = os.getenv("SITE_NAME", "jarir")
GROUP      = os.getenv("GROUP", "Default")
START_URL  = os.getenv("START_URL")
LIMIT      = int(os.getenv("LIMIT", 50))
MAX_IMAGES = int(os.getenv("MAX_IMAGES", 5))
HEADLESS   = os.getenv("HEADLESS", "false").lower() == "true"
LOCALE     = os.getenv("LOCALE", "en_US")

OUT_ROOT = f"data"
OUT_FILE = os.path.join(OUT_ROOT, GROUP, f"products_{GROUP}.jsonl")
os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)

# ================= UTILS =================
def clean(s):
    return re.sub(r"\s+", " ", s or "").strip()

def to_price(txt):
    if not txt:
        return None
    nums = re.findall(r"[\d][\d,\.]*", txt)
    return int(nums[-1].replace(",", "")) if nums else None

def load_seen(path):
    s = set()
    if not os.path.isfile(path):
        return s
    with open(path, "r", encoding="utf-8") as f:
        for l in f:
            try:
                s.add(json.loads(l)["id"])
            except:
                pass
    return s

def append_jsonl(path, row):
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())

# ================= IMAGE HELPERS =================
IMG_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
    "Referer": "https://www.jarir.com/",
}

def normalize_img_url(url):
    if not url:
        return None
    if "/cdn-cgi/image/" in url and "/https://" in url:
        return "https://" + url.split("/https://", 1)[1]
    if url.startswith("//"):
        return "https:" + url
    return url

def download_images(urls, pid):
    save_dir = os.path.join(OUT_ROOT, GROUP, pid)
    os.makedirs(save_dir, exist_ok=True)
    paths = []

    with requests.Session() as s:
        s.headers.update(IMG_HEADERS)

        for i, raw in enumerate(urls[:MAX_IMAGES], 1):
            try:
                url = normalize_img_url(raw)
                if not url:
                    continue

                r = s.get(url, timeout=30)
                r.raise_for_status()

                ext = ".jpg"
                m = re.search(r"\.(jpg|jpeg|png|webp)(?:\?|$)", url, re.I)
                if m:
                    ext = "." + m.group(1).lower()

                fp = os.path.join(save_dir, f"{i:02d}{ext}")
                with open(fp, "wb") as f:
                    f.write(r.content)

                paths.append(os.path.relpath(fp, OUT_ROOT).replace("\\", "/"))

            except Exception as e:
                print(f"[IMG FAIL] {pid} → {url} → {e}")

    return paths

# ================= MAIN =================
def main():
    seen = load_seen(OUT_FILE)
    print(f"[INIT] seen={len(seen)}")

    driver = Driver(
        uc=True,
        headless=HEADLESS,
        incognito=True,
        locale_code=LOCALE
    )

    collected = 0
    last_height = 0
    stagnant = 0

    try:
        print(f"[OPEN] {START_URL}")
        driver.get(START_URL)
        time.sleep(3)

        while collected < LIMIT and stagnant < 6:
            soup = BeautifulSoup(driver.page_source, "html.parser")
            tiles = soup.select("div.product-tile")
            print(f"[SCAN] tiles={len(tiles)}")

            for t in tiles:
                if collected >= LIMIT:
                    break

                pid = t.get("data-cnstrc-item-id")
                if not pid or pid in seen:
                    continue
                seen.add(pid)

                title_node = t.select_one(".product-title__title")
                title = clean(title_node.text) if title_node else None
                if not title:
                    continue

                price_node = t.select_one(".price span:last-child")
                price = to_price(price_node.text) if price_node else None
                if price is None:
                    continue

                a = t.select_one("a.product-tile__link[href]")
                if not a:
                    continue
                url_en = "https://www.jarir.com" + a["href"]

                tags = [
                    clean(x.text)
                    for x in t.select("span.product-title__info--box")
                    if clean(x.text)
                ]

                img_urls = []
                for img in t.select("img.image--contain"):
                    src = img.get("src")
                    if not src or "ak-asset.jarir.com" not in src:
                        continue
                    if src not in img_urls:
                        img_urls.append(src)
                    if len(img_urls) >= MAX_IMAGES:
                        break

                print(f"[ITEM] {pid} imgs={len(img_urls)}")

                image_paths = download_images(img_urls, pid)

                # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
                # YENİ: image_to_text (SADECE EKLEME)
                # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
                abs_img_paths = [os.path.join(OUT_ROOT, p) for p in image_paths]
                print("image to text called")
                img_to_text = image_to_text(abs_img_paths) if abs_img_paths else None

                row = {
                    "id": pid,
                    "store": "Jarir",
                    "group": GROUP,
                    "url_en": url_en,
                    "url": url_en,
                    "brand": title.split()[0],
                    "price_sar": price,
                    "title_en": title,
                    "title_ar": None,
                    "tags_en": tags,
                    "tags_ar": None,
                    "image_urls": img_urls,
                    "image_paths": image_paths,
                    "image_to_text": img_to_text,
                    "text_search": clean(" ".join([title, GROUP] + tags)),
                }

                append_jsonl(OUT_FILE, row)
                collected += 1
                print(f"  [+] SAVED {pid} imgs={len(image_paths)} ({collected}/{LIMIT})")

            driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(1.2)
            h = driver.execute_script("return document.body.scrollHeight")
            stagnant = stagnant + 1 if h == last_height else 0
            last_height = h

    except KeyboardInterrupt:
        print("\n[STOPPED] User interrupted safely.")

    finally:
        driver.quit()

    print(f"[DONE] {collected} → {OUT_FILE}")

if __name__ == "__main__":
    main()
