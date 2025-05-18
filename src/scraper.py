from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import os
import time
import requests

COMPANIES = {
    "DIPD": "https://www.cse.lk/pages/company-profile/company-profile.component.html?symbol=DIPD.N0000",
    "REXP": "https://www.cse.lk/pages/company-profile/company-profile.component.html?symbol=REXP.N0000"
}

BASE_SAVE_DIR = "data/raw"


def setup_driver():
    options = Options()
    options.add_argument("--headless")  # Optional: run browser in background
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver


def download_pdf(url, save_dir):
    os.makedirs(save_dir, exist_ok=True)
    filename = url.split("/")[-1]
    save_path = os.path.join(save_dir, filename)

    if os.path.exists(save_path):
        print(f"✅ Already downloaded: {filename}")
        return

    try:
        response = requests.get(url)
        response.raise_for_status()
        with open(save_path, "wb") as f:
            f.write(response.content)
        print(f"✅ Downloaded: {filename}")
    except Exception as e:
        print(f"❌ Error downloading {url}: {e}")


from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import os
import time
import requests

COMPANIES = {
    "DIPD": "https://www.cse.lk/pages/company-profile/company-profile.component.html?symbol=DIPD.N0000",
    "REXP": "https://www.cse.lk/pages/company-profile/company-profile.component.html?symbol=REXP.N0000"
}

BASE_SAVE_DIR = "data/raw"


def setup_driver():
    options = Options()
    options.add_argument("--headless")  # Optional: run browser in background
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver


def download_pdf(url, save_dir):
    os.makedirs(save_dir, exist_ok=True)
    filename = url.split("/")[-1]
    save_path = os.path.join(save_dir, filename)

    if os.path.exists(save_path):
        print(f"✅ Already downloaded: {filename}")
        return

    try:
        response = requests.get(url)
        response.raise_for_status()
        with open(save_path, "wb") as f:
            f.write(response.content)
        print(f"✅ Downloaded: {filename}")
    except Exception as e:
        print(f"❌ Error downloading {url}: {e}")


def scrape_company(driver, company, url):
    print(f"\n🔍 Scraping ONLY QUARTERLY PDF reports for {company}...")
    driver.get(url)
    time.sleep(5)  # Allow JS to load all sections

    try:
        # Locate the quarterly section directly (ID = 21b)
        quarterly_section = driver.find_element(By.ID, "21b")

        # Look for PDF links only inside the quarterly section
        links = quarterly_section.find_elements(By.XPATH, './/a[contains(@href, ".pdf")]')

        if not links:
            print("⚠️ No quarterly PDF links found.")
            return

        for link in links:
            pdf_url = link.get_attribute("href")
            if pdf_url and "/upload_report_file/" in pdf_url:
                download_pdf(pdf_url, os.path.join(BASE_SAVE_DIR, company))
    except Exception as e:
        print(f"❌ Error scraping quarterly PDFs for {company}: {e}")



def main():
    driver = setup_driver()
    for company, url in COMPANIES.items():
        scrape_company(driver, company, url)
    driver.quit()



if __name__ == "__main__":
    main()
