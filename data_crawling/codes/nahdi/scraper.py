import os
import json
import time
import re
from urllib.parse import urlencode, unquote, urlparse, parse_qs, urlunparse

import requests
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from seleniumbase import Driver

from common.image_to_text import image_to_text

# -------------------------------------------------
# ENV
# -------------------------------------------------
load_dotenv()

SITE_URL = os.getenv("SITE_URL")
GROUP = os.getenv("GROUP", "nahdi")
LIMIT = int(os.getenv("LIMIT", 50))
MAX_PAGES = int(os.getenv("MAX_PAGES", 5))
HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"
LOCALE = os.getenv("LOCALE", "en-SA")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

OUT_ROOT = os.path.join(BASE_DIR, "data")
OUT_FILE = os.path.join(OUT_ROOT, GROUP, f"products_{GROUP}.jsonl")
os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)

if not SITE_URL:
    raise RuntimeError("SITE_URL must be defined")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
}

# -------------------------------------------------
# DRIVER
# -------------------------------------------------
driver = Driver(browser="chrome", headless=HEADLESS, uc=True, locale_code=LOCALE)

# -------------------------------------------------
# HELPERS
# -------------------------------------------------
def clean(text):
    if not text:
        return None
    return re.sub(r"\s+", " ", text).strip()

def parse_price(text):
    if not text:
        return None
    text = text.replace(",", "").strip()
    try:
        return float(re.findall(r"\d+\.?\d*", text)[0])
    except:
        return None

def load_seen_ids():
    seen = set()
    if os.path.exists(OUT_FILE):
        with open(OUT_FILE, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    seen.add(json.loads(line)["id"])
                except:
                    pass
    return seen

def build_page_url(page: int) -> str:
    pu = urlparse(SITE_URL)
    qs = parse_qs(pu.query)

    qs["page"] = [str(page)]

    return urlunparse((
        pu.scheme,
        pu.netloc,
        pu.path,
        "",
        urlencode(qs, doseq=True),
        ""
    ))

# -------------------------------------------------
# PDP (AR) – _next/image FIX
# -------------------------------------------------
def scrape_pdp_ar(url_en: str, pid: str):
    url_ar = url_en.replace("/en-sa/", "/ar-sa/")
    driver.get(url_ar)
    time.sleep(2)

    soup = BeautifulSoup(driver.page_source, "html.parser")

    h1 = soup.find("h1")
    title_ar = clean(h1.text) if h1 else None

    image_urls = []
    for img in soup.find_all("img"):
        src = img.get("src", "") or ""
        if "_next/image" not in src:
            continue

        parsed = urlparse(src)
        qs = parse_qs(parsed.query)
        real_url = qs.get("url", [None])[0]
        if not real_url:
            continue

        real_url = unquote(real_url)
        if "ecombe.nahdionline.com/media/catalog/product" in real_url:
            if real_url not in image_urls:
                image_urls.append(real_url)

        if len(image_urls) >= 5:
            break

    image_paths = []
    if image_urls:
        save_dir = os.path.join(OUT_ROOT, GROUP, pid)
        os.makedirs(save_dir, exist_ok=True)

        for i, img_url in enumerate(image_urls, start=1):
            fp = os.path.join(save_dir, f"{i:02d}.jpg")
            try:
                r = requests.get(img_url, headers=HEADERS, timeout=30)
                if r.ok:
                    with open(fp, "wb") as f:
                        f.write(r.content)
                    image_paths.append(fp.replace(OUT_ROOT + "/", ""))
            except:
                pass

    if image_paths:
        print(f"[IMG] {pid} → {len(image_paths)} images downloaded")
    else:
        print(f"[IMG] {pid} → no images")

    return title_ar, image_urls, image_paths

# -------------------------------------------------
# SCRAPER (SITE_URL BASED)
# -------------------------------------------------
def scrape():
    seen = load_seen_ids()
    written = 0

    with open(OUT_FILE, "a", encoding="utf-8") as f:
        for page in range(1, MAX_PAGES + 1):
            if written >= LIMIT:
                break

            url = build_page_url(page)
            print(f"[INFO] Page {page} → {url}")

            driver.get(url)
            time.sleep(3)

            soup = BeautifulSoup(driver.page_source, "html.parser")
            cards = soup.select("div.js-plp-product")
            if not cards:
                print("[WARN] No products found")
                break

            for card in cards:
                if written >= LIMIT:
                    break

                link_tag = card.select_one("a[href*='/pdp/']")
                if not link_tag:
                    continue

                product_url = f"{urlparse(SITE_URL).scheme}://{urlparse(SITE_URL).netloc}{link_tag.get('href')}"
                pid_match = re.search(r"/pdp/(\d+)", product_url)
                pid = pid_match.group(1) if pid_match else None
                if not pid or pid in seen:
                    continue
                seen.add(pid)

                title_en = clean(
                    card.select_one("span.line-clamp-3").get_text(strip=True)
                    if card.select_one("span.line-clamp-3") else None
                )

                img_tag = card.select_one("img")
                image = img_tag.get("src") if img_tag else None

                price_current = None
                price_old = None
                price_block = card.select("span[dir='ltr']")
                if price_block:
                    if len(price_block) >= 1:
                        price_current = parse_price(price_block[0].get_text())
                    if len(price_block) >= 2:
                        price_old = parse_price(price_block[1].get_text())

                title_ar, image_urls, image_paths = scrape_pdp_ar(product_url, pid)

                # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
                # YENİ: image_to_text (SADECE EKLEME)
                # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
                abs_img_paths = [os.path.join(OUT_ROOT, p) for p in image_paths]
                print("image to text called")
                img_to_text = image_to_text(abs_img_paths) if abs_img_paths else None

                product = {
                    "id": pid,
                    "store": "nahdionline",
                    "title_en": title_en,
                    "title_ar": title_ar,
                    "price": price_current,
                    "old_price": price_old,
                    "currency": "SAR",
                    "url_en": product_url,
                    "url": product_url.replace("/en-sa/", "/ar-sa/"),
                    "image": image,
                    "image_urls": image_urls,
                    "image_paths": image_paths,
                    "image_to_text": img_to_text,
                    "group": GROUP
                }

                f.write(json.dumps(product, ensure_ascii=False) + "\n")
                f.flush()
                os.fsync(f.fileno())
                written += 1

            print(f"[INFO] Added so far: {written}")

    print(f"[DONE] Incremental save → {OUT_FILE}")
    driver.quit()

# -------------------------------------------------
# RUN
# -------------------------------------------------
if __name__ == "__main__":
    scrape()
