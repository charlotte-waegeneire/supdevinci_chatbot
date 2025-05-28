import os
import requests
import shutil
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urldefrag


# ------------------------------------------------------------
# Paramètres
# ------------------------------------------------------------
BASE_URL = "https://www.supdevinci.fr/"
MAX_PAGES = 100

EXCLUDE_PATTERNS = [
    "/offres-emploi/", "/formation/", "/evenement/", "/conference/",
    "/campus/", "/author/", "/agenda-", "/actualites/", "/salon-jpo/",
    "/non-classe/", "equipe-", "cookies", "mentions-legales", "privacy",
    "documentation", "recrutement", "certifications", "/wp-content/"
]

visited = set()
found_links = set()
to_visit = [BASE_URL]
md_dir = "data/website_pages"
vector_dir = "data/vectorstore/supdevinci_web"
# ------------------------------------------------------------


# ------------------------------------------------------------
# Fonctions de scraping
# ------------------------------------------------------------
def crawl(url):
    try:
        res = requests.get(url, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        links = [a.get("href") for a in soup.find_all("a", href=True)]
        return [urljoin(url, l) for l in links if is_valid_internal(l)]
    except Exception as e:
        print(f"Erreur sur {url} : {e}")
        return []

def is_valid_internal(link):
    full_url = urljoin(BASE_URL, link)
    parsed = urlparse(full_url)
    return (
        parsed.netloc == "www.supdevinci.fr"
        and not any(ext in full_url for ext in EXCLUDE_PATTERNS)
        and not full_url.endswith((".pdf", ".jpg", ".png", ".zip"))
    )

def extract_text(html):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return soup.get_text(separator="\n", strip=True)

def url_to_filename(url):
    path = urlparse(url).path.strip("/").replace("/", "-")
    return "accueil.md" if not path else f"{path}.md"

# ------------------------------------------------------------


# ------------------------------------------------------------
# Nettoyage des répertoires
# ------------------------------------------------------------
os.makedirs(md_dir, exist_ok=True)
for file in os.listdir(md_dir):
    os.remove(os.path.join(md_dir, file))

os.makedirs(vector_dir, exist_ok=True)
for item in os.listdir(vector_dir):
    path = os.path.join(vector_dir, item)
    if os.path.isfile(path) or os.path.islink(path):
        os.remove(path)
    elif os.path.isdir(path):
        shutil.rmtree(path)
# ------------------------------------------------------------


# ------------------------------------------------------------
# Crawling
# ------------------------------------------------------------
print("Collecte des liens...\n")
while to_visit and len(visited) < MAX_PAGES:
    current = urldefrag(to_visit.pop())[0]
    if current in visited:
        continue
    visited.add(current)

    for link in crawl(current):
        clean_link = urldefrag(link)[0]
        if clean_link not in visited:
            to_visit.append(clean_link)
            found_links.add(clean_link)
# ------------------------------------------------------------


# ------------------------------------------------------------
# Scraping et création des fichiers .md
# ------------------------------------------------------------
print("\nScraping et création des fichiers .md...\n")
for url in sorted(found_links):
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        text = extract_text(res.text)
        filename = url_to_filename(url)
        filepath = os.path.join(md_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# {url}\n\n{text}")
        print(filename)
    except Exception as e:
        print(f"{url} : {e}")
# ------------------------------------------------------------

print(f"\n{len(found_links)} pages enregistrées dans : {md_dir}")