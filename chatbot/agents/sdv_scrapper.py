import os
import shutil
from typing import List, Set
from urllib.parse import urldefrag, urljoin, urlparse

from bs4 import BeautifulSoup
import requests

from chatbot.utils import get_env_variable

_ROOT_DIR = get_env_variable("ROOT_DIR")


class WebScraper:
    def __init__(self, base_url: str, max_pages: int = 100):
        self.base_url = base_url
        self.max_pages = max_pages
        self.exclude_patterns = [
            "/offres-emploi/",
            "/formation/",
            "/evenement/",
            "/conference/",
            "/campus/",
            "/author/",
            "/agenda-",
            "/actualites/",
            "/salon-jpo/",
            "/non-classe/",
            "equipe-",
            "cookies",
            "mentions-legales",
            "privacy",
            "documentation",
            "recrutement",
            "certifications",
            "/wp-content/",
        ]
        self.visited = set()
        self.found_links = set()
        self.to_visit = [base_url]

    def is_valid_internal_link(self, link: str) -> bool:
        """Vérifie si un lien est valide et interne au site."""
        full_url = urljoin(self.base_url, link)
        parsed = urlparse(full_url)
        domain = urlparse(self.base_url).netloc

        return (
            parsed.netloc == domain
            and not any(pattern in full_url for pattern in self.exclude_patterns)
            and not full_url.endswith((".pdf", ".jpg", ".png", ".zip"))
        )

    def crawl_page(self, url: str) -> List[str]:
        """Récupère tous les liens valides d'une page."""
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            links = [
                a.get("href") for a in soup.find_all("a", href=True) if a.get("href")
            ]
            valid_links = []

            for link in links:
                full_link = urljoin(url, link)
                if self.is_valid_internal_link(link):
                    valid_links.append(full_link)

            return valid_links

        except Exception as e:
            print(f"Erreur lors du crawling de {url} : {e}")
            return []

    def collect_all_links(self) -> Set[str]:
        """Collecte tous les liens du site jusqu'à MAX_PAGES."""
        print("Collecte des liens...\n")

        while self.to_visit and len(self.visited) < self.max_pages:
            current_url = urldefrag(self.to_visit.pop())[0]

            if current_url in self.visited:
                continue

            self.visited.add(current_url)

            page_links = self.crawl_page(current_url)

            for link in page_links:
                clean_link = urldefrag(link)[0]
                if clean_link not in self.visited:
                    self.to_visit.append(clean_link)
                    self.found_links.add(clean_link)

        return self.found_links

    def extract_text_from_html(self, html: str) -> str:
        """Extrait le texte propre d'un contenu HTML."""
        soup = BeautifulSoup(html, "html.parser")

        for tag in soup(["script", "style", "noscript", "nav", "footer", "aside"]):
            tag.decompose()

        return soup.get_text(separator="\n", strip=True)

    def url_to_filename(self, url: str) -> str:
        """Convertit une URL en nom de fichier valide."""
        path = urlparse(url).path.strip("/").replace("/", "-")
        return "accueil.md" if not path else f"{path}.md"

    def scrape_page_content(self, url: str) -> str:
        """Récupère et extrait le contenu textuel d'une page."""
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return self.extract_text_from_html(response.text)
        except Exception as e:
            print(f"Erreur lors du scraping de {url} : {e}")
            return ""

    def save_page_as_markdown(self, url: str, content: str, output_dir: str) -> bool:
        """Sauvegarde le contenu d'une page en fichier Markdown."""
        if not content.strip():
            return False

        filename = self.url_to_filename(url)
        filepath = os.path.join(output_dir, filename)

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"# {url}\n\n{content}")
            print(f"✓ {filename}")
            return True
        except Exception as e:
            print(f"Erreur lors de la sauvegarde de {filename} : {e}")
            return False

    def setup_directories(self, md_dir: str, vector_dir: str):
        """Prépare les répertoires de sortie (les vide s'ils existent)."""
        os.makedirs(md_dir, exist_ok=True)
        for file in os.listdir(md_dir):
            file_path = os.path.join(md_dir, file)
            if os.path.isfile(file_path):
                os.remove(file_path)

        os.makedirs(vector_dir, exist_ok=True)
        for item in os.listdir(vector_dir):
            item_path = os.path.join(vector_dir, item)
            if os.path.isfile(item_path) or os.path.islink(item_path):
                os.remove(item_path)
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)

    def scrape_all_pages(self, md_dir: str) -> int:
        """Scrape toutes les pages collectées et les sauvegarde."""
        print("\nScraping et création des fichiers .md...\n")

        saved_count = 0
        total_links = len(self.found_links)

        for i, url in enumerate(sorted(self.found_links), 1):
            print(f"[{i}/{total_links}] ", end="")

            content = self.scrape_page_content(url)
            if self.save_page_as_markdown(url, content, md_dir):
                saved_count += 1

        return saved_count

    def run_full_scrape(
        self,
        md_dir: str = os.path.join(_ROOT_DIR, "chatbot/data/website_pages/"),
        vector_dir: str = os.path.join(
            _ROOT_DIR, "chatbot/data/vectorstore/supdevinci_web/"
        ),
    ):
        """Lance le processus complet de scraping."""
        print(f"🚀 Début du scraping de {self.base_url}")
        print(f"📁 Répertoire de sortie : {md_dir}")
        print(f"🎯 Limite : {self.max_pages} pages\n")

        self.setup_directories(md_dir, vector_dir)

        self.collect_all_links()
        print(f"📊 {len(self.found_links)} liens uniques trouvés")

        saved_count = self.scrape_all_pages(md_dir)

        print("\n✅ Scraping terminé !")
        print(f"📄 {saved_count} pages sauvegardées dans : {md_dir}")

        return saved_count


def main():
    """Fonction principale pour lancer le scraping."""
    base_url = "https://www.supdevinci.fr/"
    max_pages = 100

    scraper = WebScraper(base_url, max_pages)
    scraper.run_full_scrape()


if __name__ == "__main__":
    main()
