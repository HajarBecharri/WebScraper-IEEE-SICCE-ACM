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
from save_to_json import save_to_json
from sjr_scraping import scrape_journal_data
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import re  # Pour extraire le nombre avec une expression régulière

# Configure logging
logging.basicConfig(level=logging.INFO)
# Configurer la connexion à MongoDB Atlas

chromedriver_path = r"C:\Users\pro\.wdm\drivers\chromedriver\win64\131.0.6778.108\chromedriver-win32\chromedriver.exe"


def scrape_sciencedirect(collection,topic,page_number):
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
    driver = uc.Chrome(service=service, options=options)
    wait = WebDriverWait(driver, 20)  # Increased timeout to 20 seconds
    # Store the main window handle
    main_window = driver.current_window_handle
    # URL of IEEE search
    search_url = f"https://www.sciencedirect.com/search?qs={topic_encoded}&language=fr&show=100&offset={100*(page_number-1)}"
    # Navigate to the search page
    logging.info(f"Navigating to URL: {search_url}")
    driver.get(search_url)
    time.sleep(5)  # Increased wait time
    try:
        # Récupérer les articles
        try:
                cookie_button = wait.until(EC.element_to_be_clickable((By.ID, "CybotCookiebotDialogBodyLevelButtonLevelOptinDeclineAll")))
                cookie_button.click()
                time.sleep(2)
        except:
                logging.info("No cookie banner found on ScienceDirect")
        logging.info("Tentative de récupération des articles...")
        articles = wait.until(EC.presence_of_all_elements_located(
                        (By.CLASS_NAME, "result-item-content")))

        logging.info(f"Nombre d'articles trouvés : {len(articles)}")
        research_data = []

        for i in range(len(articles)):
            try: 
                articles = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "result-item-content")))
                article = articles[i]  # Accédez directement à l'article actuel
         
                # Récupérer le lien et le titre
                title_element = article.find_element(By.CSS_SELECTOR, ".anchor.result-list-title-link")
                article_url = title_element.get_attribute("href")
                title_text = title_element.find_element(By.CSS_SELECTOR, ".anchor-text-container > span.anchor-text").text
                logging.info(f"article : {title_text}")
                #Récupérer publisher
                publisher = article.find_element(
        By.CSS_SELECTOR, ".srctitle-date-fields a .anchor-text-container .anchor-text span")
    

    # Extraire le texte du publisher
                publisher_text = publisher.text.strip()  # Exemple : "John Doe"
                print("Publisher:", publisher_text)

                # Récupérer les auteurs
                authors = [author.text for author in article.find_elements(By.CSS_SELECTOR, "ol.Authors.hor > li")]

                # Récupérer l'année
                date_elements = article.find_elements(By.CSS_SELECTOR, "span.srctitle-date-fields > span")
                publication_year = date_elements[1].text if len(date_elements) > 1 else "Année non trouvée"
                driver.get(article_url)
                try:
                    cited_by_section = wait.until(
                    EC.presence_of_element_located((By.ID, "preview-section-cited-by"))
                    )
                except TimeoutException:
                    print("L'élément avec l'ID 'preview-section-cited-by' n'a pas été trouvé.")
                    cited_by_section = None

    # Initialiser la valeur par défaut
                cited_count = None

                if cited_by_section:
                    try:
            # Trouver l'élément avec l'ID `citing-articles-header`
                        citing_header = cited_by_section.find_element(By.ID, "citing-articles-header")
            # Extraire le texte du <h2>
                        citing_text = citing_header.find_element(By.TAG_NAME, "h2").text.strip()
            # Extraire le nombre avec une expression régulière
                        match = re.search(r"Cited by \((\d+)\)", citing_text)
                        if match:
                            cited_count = match.group(1)  # Le nombre extrait
                    except NoSuchElementException:
                           print("Les détails des citations n'ont pas été trouvés.")

    # Afficher le résultat
                print(f"Nombre de citations : {cited_count}")
                try:
                 author_buttons = wait.until(EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, '.author-group .button-link.button-link-secondary.button-link-underline')))
                 logging.info(f"Nombre de boutons d'auteurs trouvés : {len(author_buttons)}")

                 laboratoire = []
                 pays=[]
                 for index, button in enumerate(author_buttons):
                  try:
                    if button.is_displayed() and button.is_enabled():
                       button.click()
                       time.sleep(5)  # Attendre un peu pour que le panneau latéral se charge

                    else:
                       logging.warning("Le bouton de l'auteur n'est pas interactif.")
                    
                # 3. Attendre que le panneau latéral apparaisse et récupérer les informations
                    side_panel = wait.until(EC.presence_of_element_located(
                    (By.CSS_SELECTOR, '.side-panel-content')))
                    side_panel_author = side_panel.find_element(By.CSS_SELECTOR, '.SidePanelAuthor')
                    side_panel_author_info = side_panel_author.find_element(By.CSS_SELECTOR, '.affiliation')
                     # 4. Extraire le texte du panneau latéral pour l'auteur
                    author_info_text = side_panel_author_info.get_attribute("innerText").strip()
               
                    logging.info(f"Information de l'auteur : {author_info_text}")

                # 5. Analyser l'information de l'auteur pour séparer le laboratoire et le pays
                # Supposons que le texte contient la forme "Laboratoire XYZ, Pays"
                    if author_info_text:
                     if ',' in author_info_text:
                         parts = author_info_text.rsplit(',', 1)
                         laboratory = parts[0].strip()
                         country = parts[1].strip()
                         if country not in pays:
                            pays.append(country)
                         if laboratory not in laboratoire:
                            laboratoire.append(laboratory)
    
                     else:

                        laboratory = author_info_text
                        if laboratory not in laboratoire:
                            laboratoire.append(laboratory)
                        
                    else:
                     logging.warning(f"Format de l'information de l'auteur non trouvé pour {author_info_text}")
                    
                    
                # Fermer le panneau latéral après extraction des informations
                    close_button = side_panel.find_element(By.CSS_SELECTOR, '.button-link.side-panel-close-btn.button-link-primary.button-link-icon-only')  # Assurez-vous que le bouton existe
                    if close_button.is_displayed():
                       close_button.click()
                       logging.warning("Le bouton de fermeture est click")
                       wait.until(EC.invisibility_of_element((By.CSS_SELECTOR, '.side-panel-content')))

                       time.sleep(3)    
                    else:
                       logging.warning("Le bouton de fermeture n'est pas visible.")
                  except Exception as e:
                    logging.error(f"Erreur lors de l'extraction des informations pour un auteur : {index}")
                    continue
                     
                 quartile=scrape_journal_data(publisher_text,publication_year,driver)
                 print(f"quartile:{quartile}")
                except Exception as e:
                 logging.error(f"Erreur lors de l'extraction des informations pour un auteur : {e}")
                 continue
                # Ajouter les données dans une liste
                site="ScienceDirect"
                data = {
                    "title": title_text,
                    "authors": authors,
                    "date": publication_year,
                    "pays":pays,
                    "laboratoire":laboratoire,
                    "publisher":publisher_text,
                    "quartile":quartile,
                    "topic":topic,
                    "citations":cited_count,
                    "site":site

                }
                 
                
                research_data.append(data)
                logging.info(f"Article scraped: {data}")
                
                # Insérer dans MongoDB
                """
                try:
                    collection.insert_one(data)
                    logging.info(f"Données insérées pour : {title_text}")
                except errors.PyMongoError as e:
                    logging.error(f"Erreur MongoDB : {e}")
                """
                save_to_json(data)
                driver.get(search_url)
                wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "result-item-content")))
                
            except Exception as e:
                logging.error(f"Erreur lors du traitement de l'article {article_url} : {e}")
                driver.back()
                wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "result-item-content")))
                
                continue

        return jsonify(research_data), 200

    except Exception as e:
        logging.error("Erreur lors du scraping de ScienceDirect : %s", traceback.format_exc())
        return jsonify({"error": "Erreur scraping", "details": str(e)}), 500

    finally:
        driver.quit()
        logging.info("WebDriver fermé.")

