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
from selenium.common.exceptions import NoSuchElementException
from save_to_json import save_to_json
from sjr_scraping import scrape_journal_data
from urllib.parse import quote

# Configure logging
logging.basicConfig(level=logging.INFO)
# Configurer la connexion à MongoDB Atlas

chromedriver_path = r"C:\Users\pro\.wdm\drivers\chromedriver\win64\131.0.6778.108\chromedriver-win32\chromedriver.exe"


def scrape_ieee_research(collection,topic,page_number):
    # Configurez le Service pour Selenium
    topic_encoded = quote(topic)
    service = Service(chromedriver_path)

    options = webdriver.ChromeOptions()
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--enable-unsafe-swiftshader')
        # Add user agent to avoid detection
    options.add_argument(
            'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36')


# Initialisez le WebDriver
    driver = webdriver.Chrome(service=service, options=options)
    wait = WebDriverWait(driver, 20)  # Increased timeout to 20 seconds
    # Store the main window handle
    main_window = driver.current_window_handle
    # URL of IEEE search
    search_url = f"https://ieeexplore.ieee.org/search/searchresult.jsp?newsearch=true&queryText={topic_encoded}&highlight=true&returnType=SEARCH&matchPubs=true&pageNumber={page_number}&returnFacets=ALL"
    # Navigate to the search page
    logging.info(f"Navigating to URL: {search_url}")
    driver.get(search_url)
    time.sleep(5)  # Increased wait time
    
    
    # Initialize a list to store the search results
    research_data = []

    try:
        logging.info("Page loaded.")
        
        # Wait for the search results container
        results_container = wait.until(EC.presence_of_element_located(
                        (By.TAG_NAME, "xpl-results-list")))
    # Get all article elements
        articles = results_container.find_elements(By.CLASS_NAME, "List-results-items")
        for i in range(len(articles)):
           
           articles_new = results_container.find_elements(By.CLASS_NAME, "List-results-items")
           article=articles_new[i]
           title_link = article.find_element(By.CSS_SELECTOR, ".fw-bold")
           article_url = title_link.get_attribute("href")
           # Extraire le texte du titre
           title_text = title_link.text
           print("Titre:", title_text)
           logging.info(f"Collected data for article: {title_text}")
           authors=article.find_element(By.CSS_SELECTOR,".author")
           # Attendre que le tag xpl-publisher soit visible
           publisher_tag = wait.until(EC.visibility_of_element_located((By.TAG_NAME, "xpl-publisher")))

           publisher = publisher_tag.find_element(By.CSS_SELECTOR, 
        "span.text-base-md-lh.publisher-info-container.black-tooltip span:nth-of-type(2)").text 
           print(f"publisher:{publisher}")
   
           date_element = wait.until(EC.visibility_of_element_located(
        (By.CSS_SELECTOR, "div.publisher-info-container span:first-of-type")))  # Sélecteur CSS pour le premier <span>
           des_element = wait.until(EC.visibility_of_element_located(
        (By.CSS_SELECTOR, "div.description.text-base-md-lh a:first-of-type")))  # Sélecteur CSS pour le premier <a>

          # Obtenir le texte de l'élément <a>
           description = des_element.text

    
           # Extraire le texte brut
           date_text = date_element.text.strip()  # Ex: "Year: 2009"

           # Extraire uniquement l'année avec une méthode simple
           year = date_text.split(":")[1].strip() if ":" in date_text else date_text
           print("Année:", year)  # Output attendu : 2009
           
    # Afficher le texte
           
           driver.execute_script(f"window.open('{article_url}', '_blank');")
           time.sleep(2)

            # Switch to the new tab
           new_window = [window for window in driver.window_handles if window != main_window][-1]
           driver.switch_to.window(new_window)
           try:
            container = WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.CLASS_NAME, "document-banner-metric-container"))
)
        
        # Initialiser les valeurs par défaut
            citations = None
            views = None
        
        # Rechercher les métriques à l'intérieur du conteneur
            metrics = container.find_elements(By.CLASS_NAME, "document-banner-metric-count")
        
        # Vérifier et extraire les données
            if len(metrics) > 0:
               citations = metrics[0].text.strip()
            if len(metrics) > 1:
               views = metrics[1].text.strip()
        
        # Afficher les résultats
            print(f"Citations: {citations}")
            print(f"Vues: {views}")
    
           except NoSuchElementException:
            print("Le conteneur des métriques n'a pas été trouvé.")
            # Wait for article page to load
           divs = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.u-mb-1")))
           abstract_div=divs[1]
           abstract=abstract_div.find_element(By.TAG_NAME, "div")
           abstract_text=abstract.text
           authors_path = "authors"
           authors_url = article_url + authors_path
           print(authors_url)
           time.sleep(2)
           driver.get(authors_url)
           authors_section = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "section.col-12.authors-tab.document-tab"))
        )
           authors_containers = authors_section.find_elements(By.CSS_SELECTOR, "div.mobile-authors-container.hide-desktop")
           labs_list = []  # To store lab names
           pays_list=[]
           for author in authors_containers:
              try:
                 author_item = author.find_element(By.TAG_NAME, "xpl-author-item")
                 author_card = author_item.find_element(By.CLASS_NAME, "author-card.text-base-md-lh")
                 row = author_card.find_element(By.CLASS_NAME, "row.g-0")
                 col = row.find_element(By.CLASS_NAME, "col-24-24")
                 sub_divs = col.find_elements(By.TAG_NAME, "div")
                 for index, sub_div in enumerate(sub_divs, start=1):
                    sub_div_html = sub_div.get_attribute("outerHTML")
                    logging.info(f"Contenu du sous-div {index} : {sub_div_html}")
                 if len(sub_divs) >= 2:
                     author_name_element = sub_divs[0].find_element(By.TAG_NAME, "span")
                     print(author_name_element.text.strip())
                     author_name = author_name_element.get_attribute("innerText") if author_name_element else "Nom non trouvé"
        
        # Deuxième div : Labo (contient un div supplémentaire)
                     lab_details_element = sub_divs[2]
                   
                     lab_details = lab_details_element.get_attribute("innerText") if lab_details_element else "Détails du laboratoire non trouvés"
                     split_details = lab_details.split(',')

                   # Prendre la première partie (avant la première virgule) et la dernière partie (après la dernière virgule)
                     lab_name = ', '.join([split_details[0].strip(), split_details[1].strip()])  # deux premières parties
                     pays=split_details[-1].strip()  # dernière partie, enlever les espaces superflus

                     if lab_name not in labs_list:
                       labs_list.append(lab_name)
                     if pays not in pays_list:
                       pays_list.append(pays)
              except Exception as e:
                logging.error(f"Error processing an author: {e}")
                continue
           quartile=scrape_journal_data(publisher,year,driver)
           print(f"quartile:{quartile}")
           driver.switch_to.window(main_window)
           site="IEEE"
           # Créer un dictionnaire avec les données extraites
           research_data = {
        "title": title_text,
        "authors": authors.text,
        "date": year,
        "pays":pays_list,
        "laboratoire":labs_list,
        "publisher":publisher,
        "quartile":quartile,
        "topic":topic,
        "citations":citations,
        "views":views,
        "site":site
    }
           print(f"data: {research_data}")
           """
           try:
                collection.insert_one(research_data)
                logging.info(f"Données insérées pour : {title_text}")
           except errors.PyMongoError as e:
                    logging.error(f"Erreur MongoDB : {e}")
           """
           save_to_json(research_data)
        driver.close()
        time.sleep(1)

    except Exception as e:
        logging.error(f"Error extracting search data: {e}")
        return jsonify({"error": "Error extracting search data"}), 500

    finally:
        driver.quit()  # Close the browser after scraping
        logging.info("WebDriver closed.")

    return jsonify(research_data)