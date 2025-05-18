import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Base URL of the companies to scrape
COMP = {
    "DIPD": "https://www.cse.lk/pages/company-profile/company-profile.component.html?symbol=DIPD.N0000",
    "REXP": "https://www.cse.lk/pages/company-profile/company-profile.component.html?symbol=REXP.N0000"
}

DOWNLOAD_DIR = "data/raw"

# Function to download a file from a URL
def download_file(url, save_path):
    try:
        response = requests.get(url)
        response.raise_for_status()
        with open(save_path, 'wb') as file:
            file.write(response.content)
        print(f"Downloaded: {save_path}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to download {url}: {e}")

# Function to scrape the website and download PDF files
def scrape_and_download_pdfs(base_url, company):
    try:
        response = requests.get(base_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all PDF links on the page
        pdf_links = [
            urljoin(base_url, link['href'])
            for link in soup.find_all('a', href=True)
            if link['href'].endswith('.pdf')
        ]

        # Ensure save folder exists
        save_folder = os.path.join(DOWNLOAD_DIR, company)
        os.makedirs(save_folder, exist_ok=True)

        # Download each PDF file
        for pdf_url in pdf_links:
            file_name = pdf_url.split("/")[-1]
            save_path = os.path.join(save_folder, file_name)
            download_file(pdf_url, save_path)

    except requests.exceptions.RequestException as e:
        print(f"Failed to scrape {base_url}: {e}")

def main():
    for company, base_url in COMP.items():
        print(f"Scraping {company}...")
        scrape_and_download_pdfs(base_url, company)
        print(f"Finished scraping {company}.\n")

if __name__ == "__main__":
    main()
