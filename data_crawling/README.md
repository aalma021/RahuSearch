## USAGE

## 1) .env SETTINGS

SITE_URL=...
GROUP=Tablets
LIMIT=50
MAX_IMAGES=5

## DESCRIPTIONS
- SITE_URL    : Full search/listing URL (whatever you want to scrape)
- GROUP       : Output folder name and dataset group
- LIMIT       : Total number of products to collect
- MAX_IMAGES  : Maximum number of images per product


## 2) RUNNING

Run commands from the project root:

make jarir
make extra
make almanea
make nahdi
make aldawaa

Run all scrapers (except noon):

make all


## 3) OUTPUT

Collected data is written to:

codes/<site>/data/<GROUP>/products_<GROUP>.jsonl

Duplicate products are skipped.
Scraping runs incrementally (append-only).
