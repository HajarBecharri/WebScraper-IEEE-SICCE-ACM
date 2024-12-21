import logging
from flask import Flask, jsonify
from selenium.common.exceptions import TimeoutException
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains
import time
from selenium.webdriver.common.keys import Keys
import logging
from pymongo import MongoClient
from pymongo import errors
from bson import ObjectId
import logging
import traceback
from bs4 import BeautifulSoup
import undetected_chromedriver as uc
from urllib.parse import quote

# Configure logging
logging.basicConfig(level=logging.INFO)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def scrape_journal_data(journal_name, year, driver):
    try:
        logging.info(f"Starting data scraping for journal: {journal_name} for year: {year}")
        
        # Step 1: Access SCImago website
        journal_name_encoded = quote(journal_name)
        driver.get(f"https://www.scimagojr.com/journalsearch.php?q={journal_name_encoded}")
        wait = WebDriverWait(driver, 10)
        logging.info("Accessed SCImago website.")

      
        # Step 3: Select the journal link
        try:
           journal_link = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, 'journalsearch.php') and contains(@href, 'sid')]")))
           journal_link.click()
           logging.info("Selected the journal link.")
        except TimeoutException:
           logging.warning("Journal link not found. Returning an empty quartile.")
           return ""


        # Step 4: Close any pop-up ad if present
        try:
            close_button = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.CLASS_NAME, "ns-jhssl-e-5.close-button")))
            close_button.click()
            logging.info("Closed pop-up ad.")
        except Exception:
            logging.warning("No pop-up ad to close.")

        # Step 5: Click the table button to view quartile data
        table_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".combo_buttons .combo_button.table_button")))
        table_button.click()
        time.sleep(2)
        logging.info("Opened quartile table.")

        # Step 6: Scrape table data containing Quartiles
        table = driver.find_element(By.XPATH, "//div[@class='cellslide']/table")
        rows = table.find_elements(By.XPATH, ".//tbody/tr")
        
        quartile_data = {}
        for row in rows:
            cols = row.find_elements(By.TAG_NAME, "td")
            if len(cols) >= 2:
    # Si trois colonnes, ignorer la première (catégorie) et prendre les deux dernières
                if len(cols) == 3:
                   year_text, quartile = [col.text.strip() for col in cols[1:]]
                else:
        # Si deux colonnes, prendre directement les deux
                   year_text, quartile = [col.text.strip() for col in cols]
    
    # Ajouter l'année et le quartile au dictionnaire
                try:
                   quartile_data[int(year_text)] = quartile
                except ValueError:
                   logging.warning(f"Invalid year format: {year_text}. Skipping this row.")

        if quartile_data:
            logging.info(f"Successfully scraped quartile data: {quartile_data}")

        # Return quartile for the given year or the most recent year
        if year in quartile_data:
            logging.info(f"Quartile for year {year}: {quartile_data[year]}")
            time.sleep(5)
            return quartile_data[year]
        else:
            most_recent_year = max(quartile_data)
            logging.info(f"Year {year} not found. Returning most recent quartile for year {most_recent_year}: {quartile_data[most_recent_year]}")     
            time.sleep(5)
            return quartile_data[most_recent_year]

    except Exception as e:
        logging.error(f"Error occurred while scraping data for {journal_name}: {e}")
        
        time.sleep(5)
        return ""