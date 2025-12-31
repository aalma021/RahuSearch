import os
import json
import time
import re
import requests
from urllib.parse import urljoin, urlparse

from dotenv import load_dotenv
from seleniumbase import Driver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup

from common.image_to_text import image_to_text

# -------------------------------------------------
# ENV
# -------------------------------------------------
load_dotenv()

START_URL  = os.getenv("START_URL")
GROUP      = os.getenv("GROUP", "aldawaa")
LIMIT      = int(os.getenv("LIMIT", 20))
MAX_IMAGES = int(os.getenv("MAX_IMAGES", 5))
HEADLESS   = os.getenv("HEADLESS", "false").lower() == "true"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

OUT_ROOT = os.path.join(BASE_DIR, "data")
OUT_FILE = os.path.join(OUT_ROOT, GROUP, f"products_{GROUP}.jsonl")
os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)

BASE_URL = "https://www.al-dawaa.com"

# -------------------------------------------------
# DRIVER
# -------------------------------------------------
driver = Driver(browser="chrome", headless=HEADLESS, uc=True)

# -------------------------------------------------
# HELPERS
# -------------------------------------------------
def clean(t):
    return re.sub(r"\s+", " ", t).strip() if t else None

def normalize_to_1200(src: str) -> str:
    return (
        src.replace("_65.webp", "_1200.webp")
           .replace("_96.webp", "_1200.webp")
           .replace("_300.webp", "_1200.webp")
           .replace("_515.webp", "_1200.webp")
    )

def wait_for_title_en(card, timeout=10):
    start = time.time()
    while time.time() - start < timeout:
        node = card.select_one("div.product-name")
        if node:
            text = clean(node.get_text())
            if text:
                return text
        time.sleep(0.5)
    return None

def build_page_url(base_url: str, page: int) -> str:
    if "currentPage=" in base_url:
        return re.sub(r"currentPage=\d+", f"currentPage={page}", base_url)
    sep = "&" if "?" in base_url else "?"
    return f"{base_url}{sep}currentPage={page}"

# -------------------------------------------------
# DUPLICATE GUARD
# -------------------------------------------------
def load_existing_ids(path: str) -> set:
    ids = set()
    if not os.path.exists(path):
        return ids

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                obj = json.loads(line)
                if "id" in obj:
                    ids.add(str(obj["id"]))
            except Exception:
                pass
    return ids

# -------------------------------------------------
# IMAGE EXTRACT
# -------------------------------------------------
def extract_images_and_session(url_ar: str):
    driver.get(url_ar)
    time.sleep(6)

    image_urls = []
    root = driver.find_element(By.CSS_SELECTOR, "aldawaa-product-image")

    for img in root.find_elements(By.CSS_SELECTOR, "img"):
        src = img.get_attribute("src")
        if src:
            image_urls.append(normalize_to_1200(src))

    image_urls = list(dict.fromkeys(image_urls))[:MAX_IMAGES]

    session = requests.Session()
    session.headers.update({
        "User-Agent": driver.execute_script("return navigator.userAgent;"),
        "Referer": url_ar,
    })

    for c in driver.get_cookies():
        session.cookies.set(c["name"], c["value"])

    return image_urls, session

# -------------------------------------------------
# PDP
# -------------------------------------------------
def scrape_pdp(url_en: str, pid: str):
    url_ar = url_en.replace("/en/", "/ar/")
    image_urls, session = extract_images_and_session(url_ar)

    soup = BeautifulSoup(driver.page_source, "lxml")
    title_ar = clean(soup.find("h1").get_text() if soup.find("h1") else None)

    image_paths = []
    if image_urls:
        out_dir = os.path.join(OUT_ROOT, GROUP, pid)
        os.makedirs(out_dir, exist_ok=True)

        for i, url in enumerate(image_urls, 1):
            name = os.path.basename(urlparse(url).path)
            out_path = os.path.join(out_dir, f"{i:02d}_{name}")
            try:
                r = session.get(url, timeout=20)
                r.raise_for_status()
                with open(out_path, "wb") as f:
                    f.write(r.content)
                image_paths.append(out_path.replace(OUT_ROOT + "/", ""))
            except Exception:
                pass

    return title_ar, image_urls, image_paths

# -------------------------------------------------
# SCRAPER
# -------------------------------------------------
def scrape():
    seen_urls = set()
    written = 0
    page = 1

    existing_ids = load_existing_ids(OUT_FILE)
    print(f"[INIT] Loaded {len(existing_ids)} existing products")

    with open(OUT_FILE, "a", encoding="utf-8") as f:
        while written < LIMIT:
            page_url = build_page_url(START_URL, page)
            print(f"[PAGE] {page_url}")

            driver.get(page_url)
            time.sleep(5)

            soup = BeautifulSoup(driver.page_source, "lxml")
            cards = soup.select("div.item-box")

            if not cards:
                print("[STOP] No more products on site")
                break

            for card in cards:
                if written >= LIMIT:
                    break

                a = card.select_one("a[href*='/p/']")
                if not a:
                    continue

                url = urljoin(BASE_URL, a.get("href"))
                if url in seen_urls:
                    continue
                seen_urls.add(url)

                m = re.search(r"/p/(\d+)", url)
                if not m:
                    continue
                pid = m.group(1)

                if pid in existing_ids:
                    continue

                title_en = wait_for_title_en(card, timeout=10)
                if not title_en:
                    continue

                title_ar, imgs, paths = scrape_pdp(url, pid)

                # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
                # YENİ: image_to_text (SADECE EKLEME)
                # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
                abs_img_paths = [os.path.join(OUT_ROOT, p) for p in paths]
                print("image to text called")
                img_to_text = image_to_text(abs_img_paths) if abs_img_paths else None

                f.write(json.dumps({
                    "id": pid,
                    "store": "al-dawaa",
                    "title_en": title_en,
                    "title_ar": title_ar,
                    "url": url,
                    "image_urls": imgs,
                    "image_paths": paths,
                    "image_to_text": img_to_text,
                    "group": GROUP
                }, ensure_ascii=False) + "\n")

                existing_ids.add(pid)
                written += 1
                print(f"[OK] {pid} ({written}/{LIMIT})")

            page += 1

    driver.quit()
    print("[DONE]")

# -------------------------------------------------
if __name__ == "__main__":
    scrape()
