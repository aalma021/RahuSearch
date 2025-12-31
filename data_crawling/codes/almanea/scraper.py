import os
import re
import json
import time
import requests
from urllib.parse import urljoin
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from seleniumbase import Driver
from selenium.common.exceptions import NoSuchElementException

from common.image_to_text import image_to_text

# -------------------------------------------------
# ENV
# -------------------------------------------------
load_dotenv()

BASE = os.getenv("BASE_URL")
LIST_URL = os.getenv("LIST_URL")
GROUP = os.getenv("GROUP", "Default")
LIMIT = int(os.getenv("LIMIT", 50))
MAX_IMAGES = int(os.getenv("MAX_IMAGES", 5))
HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"
LOCALE = os.getenv("LOCALE", "en_US")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

OUT_ROOT = os.path.join(BASE_DIR, "data")
OUT_FILE = os.path.join(OUT_ROOT, GROUP, f"products_{GROUP}.jsonl")

IMG_DOMAIN_FILTER = "imgs.dev-almanea.com/media/catalog/product"

os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)

# -------------------------------------------------
# HELPERS
# -------------------------------------------------
def clean(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()


def to_price(txt: str):
    if not txt:
        return None
    m = re.search(r"(\d[\d\.,]*)", txt)
    if not m:
        return None
    num = m.group(1).replace(",", "").replace(".", "")
    try:
        return int(num)
    except Exception:
        return None


def to_ar_url(url_en: str) -> str:
    return url_en.replace("/en/", "/ar/", 1)


def load_existing_ids(path):
    ids = set()
    if not os.path.exists(path):
        return ids
    with open(path, encoding="utf-8") as f:
        for line in f:
            try:
                ids.add(json.loads(line)["id"])
            except Exception:
                pass
    return ids


def append_jsonl(path, row):
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def normalize_img(src: str) -> str:
    if not src:
        return ""
    if src.startswith("//"):
        src = "https:" + src
    return src.split("?", 1)[0]


# -------------------------------------------------
# PAGINATION (BUTTON BASED)
# -------------------------------------------------
def page_button_exists(driver, page: int) -> bool:
    try:
        driver.find_element(
            "css selector",
            f'button[aria-label="Go to page {page}"]'
        )
        return True
    except NoSuchElementException:
        return False


def click_page(driver, page: int):
    btn = driver.find_element(
        "css selector",
        f'button[aria-label="Go to page {page}"]'
    )
    driver.execute_script(
        "arguments[0].scrollIntoView({block:'center'});", btn
    )
    time.sleep(0.3)
    btn.click()
    time.sleep(1.2)


# -------------------------------------------------
# LIST PAGE
# -------------------------------------------------
def extract_listing_products(soup: BeautifulSoup):
    anchors = soup.select('a[title][href^="/en/product/"]')
    for a in anchors:
        title = clean(a.get_text())
        href = a.get("href")
        if not title or not href:
            continue

        m = re.search(r"-p-([0-9A-Za-z]+)", href)
        pid = m.group(1) if m else None
        if not pid:
            continue

        price_node = a.find_next("span", class_=re.compile("font-semibold"))
        price = to_price(price_node.get_text()) if price_node else None
        if not price:
            continue

        brand_node = a.find_previous("p", class_=re.compile("text-zinc-500"))
        brand = clean(brand_node.get_text()) if brand_node else None

        yield {
            "id": pid,
            "title_en": title,
            "brand": brand,
            "price_sar": price,
            "url_en": urljoin(BASE, href),
        }


# -------------------------------------------------
# PDP
# -------------------------------------------------
def scrape_pdp(driver: Driver, url: str):
    driver.get(url)
    time.sleep(1)

    soup = BeautifulSoup(driver.page_source, "html.parser")

    title_ar_node = soup.select_one("h1.font-semibold")
    title_ar = clean(title_ar_node.get_text()) if title_ar_node else None

    img_urls = []
    for img in soup.select("div.swiper-slide img"):
        src = normalize_img(img.get("src"))
        if IMG_DOMAIN_FILTER in src and src not in img_urls:
            img_urls.append(src)
        if len(img_urls) >= MAX_IMAGES:
            break

    return title_ar, img_urls


def download_images(img_urls, save_dir):
    os.makedirs(save_dir, exist_ok=True)
    paths = []

    for i, url in enumerate(img_urls, 1):
        try:
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            ext = os.path.splitext(url)[-1] or ".jpg"
            fname = f"{i:02d}{ext}"
            fp = os.path.join(save_dir, fname)
            with open(fp, "wb") as f:
                f.write(r.content)
            paths.append(os.path.relpath(fp, OUT_ROOT).replace("\\", "/"))
        except Exception as e:
            print(f"[IMG FAIL] {url} -> {e}")

    return paths


# -------------------------------------------------
# MAIN
# -------------------------------------------------
def main():
    existing_ids = load_existing_ids(OUT_FILE)
    collected = 0

    driver = Driver(uc=True, headless=HEADLESS, locale_code=LOCALE)
    driver.set_window_size(1400, 1000)

    print(f"[START] {LIST_URL}")
    driver.get(LIST_URL)
    time.sleep(1)

    page = 1
    try:
        while collected < LIMIT:
            if page > 1:
                if not page_button_exists(driver, page):
                    print(f"[STOP] page {page} button not found")
                    break
                print(f"[CLICK] Go to page {page}")
                click_page(driver, page)

            soup = BeautifulSoup(driver.page_source, "html.parser")
            products = list(extract_listing_products(soup))
            if not products:
                print("[STOP] no products")
                break

            for p in products:
                pid = p["id"]
                if pid in existing_ids:
                    continue

                print(f"[NEW] {pid}")
                title_ar, img_urls = scrape_pdp(driver, to_ar_url(p["url_en"]))

                img_dir = os.path.join(OUT_ROOT, GROUP, pid)
                img_paths = download_images(img_urls, img_dir)

                # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
                # YENİ: image_to_text (SADECE EKLEME)
                # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
                abs_img_paths = [os.path.join(OUT_ROOT, p) for p in img_paths]
                print("image to text called ")
                img_to_text = image_to_text(abs_img_paths) if abs_img_paths else None
                record = {
                    **p,
                    "store": "Almanea",
                    "group": GROUP,
                    "url": to_ar_url(p["url_en"]),
                    "title_ar": title_ar,
                    "image_urls": img_urls,
                    "image_paths": img_paths,
                    "image_to_text": img_to_text,
                    "text_en": p["title_en"],
                    "text_ar": title_ar,
                    "text_search": clean(
                        " ".join(filter(None, [p["title_en"], title_ar, p["brand"], GROUP]))
                    ),
                }

                append_jsonl(OUT_FILE, record)
                existing_ids.add(pid)
                collected += 1

                if collected >= LIMIT:
                    break

            page += 1

    finally:
        driver.quit()

    print(f"[DONE] collected={collected}")


if __name__ == "__main__":
    main()
