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

from save_to_json import save_to_json
from sjr_scraping import scrape_journal_data
from urllib.parse import quote
from selenium.common.exceptions import NoSuchElementException
# Configure logging
logging.basicConfig(level=logging.INFO)
# Configurer la connexion à MongoDB Atlas

chromedriver_path = r"C:\Users\pro\.wdm\drivers\chromedriver\win64\131.0.6778.108\chromedriver-win32\chromedriver.exe"



def scrape_acm(collection,topic,page_number):
    topic_encoded = quote(topic)
    """Scrape les articles du site ACM."""
    
    # Configurez le Service pour Selenium
    service = Service(chromedriver_path)

# Configurez les options pour Chrome
    options = webdriver.ChromeOptions()
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
    url = f"https://dl.acm.org/action/doSearch?AllField={topic_encoded}&startPage={page_number-1}&pageSize=50"
    logging.info(f"Navigating to URL: {url}")
    driver.get(url)
    time.sleep(10)
    try:
     
        cookie_accept_button = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.ID, 'CybotCookiebotDialogBodyLevelButtonLevelOptinDeclineAll'))  # Remplacez par la bonne classe ou ID
)
        cookie_accept_button.click()
        logging.info("Pop-up de cookies fermé avec succès.")
        time.sleep(5)
        # Attendre que les articles soient chargés
        #articles = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "issue-item.issue-item--search")))
        articles = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "issue-item__content")))
        #articles = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "issue-item__title")))
        
        
        data = []
        
        logging.info(f"Nombre d'articles trouvés : {len(articles)}")

        for i in range(len(articles)):
            articles = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "issue-item__content")))
            article=articles[i]
            try:
        
              container = article.find_element(By.CLASS_NAME, "metric-holder")
        
            except TimeoutException:
              print("Le conteneur 'metric-holder' n'a pas été trouvé.")
              container = None

    # Initialiser les valeurs par défaut
            citations = None
            views = None

            if container:
        # Extraire les citations (gérer les exceptions au cas par cas)
               try:
                citation_element = container.find_element(By.CLASS_NAME, "citation")
                citations = citation_element.find_element(By.TAG_NAME, "span").text.strip()
               except NoSuchElementException:
                print("Les citations ne sont pas disponibles.")

        # Extraire les vues (gérer les exceptions au cas par cas)
               try:
                 views_element = container.find_element(By.CLASS_NAME, "metric")
                 views = views_element.find_element(By.TAG_NAME, "span").text.strip()
               except NoSuchElementException:
                 print("Les vues ne sont pas disponibles.")

    # Afficher les résultats
            print(f"Citations: {citations}")
            print(f"Vues: {views}")

       

            article_title=article.find_element(By.CLASS_NAME, "issue-item__title")
            publisher=article.find_element(By.CLASS_NAME, "epub-section__title").text
            logging.info(f"Publisher : {publisher}")
            pays=[]
            labos=[]
            try:
                logging.info(f"Traitement de l'article {i}...")

                # Titre et lien de l'article
                title_span = article_title.find_element(By.CLASS_NAME, "hlFld-Title")
                title_link = title_span.find_element(By.TAG_NAME, "a")
                title_html = title_link.get_attribute("innerHTML")
                title = BeautifulSoup(title_html, "html.parser").get_text(strip=True)  # Nettoyer le titre
                article_href = title_link.get_attribute("href")
                logging.info(f"Titre : {title}")
                
                authors = []
                # Cliquer sur le lien pour aller à la page de l'article
                driver.get(article_href)
                time.sleep(10)  # Attendre que la page de l'article soit chargée

                # Récupérer la date de publication de la page de l'article
                try:
                    core_published_div = driver.find_element(By.CLASS_NAME, "core-published")
                    publish_date_span = core_published_div.find_element(By.CLASS_NAME, "core-date-published")
                    publish_date = publish_date_span.text
                    publish_date = publish_date.split()[-1]  # Récupère le dernier élément
                    logging.info(f"Date de publication : {publish_date}")
                except Exception as e:
                    logging.error(f"Erreur lors de la récupération de la date de publication pour l'article {title}: {e}")
                    publish_date = ""
                wait.until(EC.presence_of_element_located((By.CLASS_NAME, "contributors")))

                # Extraire les informations des auteurs
                logging.info("Récupération des informations des auteurs.")
                contributors_div = driver.find_element(By.CLASS_NAME, "contributors")
                authors_span = contributors_div.find_element(By.CLASS_NAME, "authors")
                
                # Rechercher l'élément avec l'attribut role="list"
                role_list = authors_span.find_element(By.XPATH, './/span[@role="list"]')
                logging.info("Trouvé l'élément avec le rôle 'list'.")

                # Récupérer tous les éléments span de type roleListitem
                author_items = role_list.find_elements(By.XPATH, './/span[@role="listitem"]')
                logging.info(f"Nombre d'auteurs trouvés: {len(author_items)}")
      
                print(f"Nombre total d'auteurs : {len(author_items)}")
                for author_item in author_items:
                  try:
                     authors.append(author_item.text.strip())
                     logging.info(f"Extraction des informations pour l'auteur: {author_item.text.strip()}")           
                     author_link = author_item.find_element(By.XPATH, './/a[@aria-controls]')
                     author_link.click()
                     logging.info(f"Clic sur le lien de l'auteur: {author_link.get_attribute('title')}")

                # Attendre que les détails de l'auteur soient chargés
                     time.sleep(6)
                # Récupérer le nom de l'auteur
                     author_name_span = author_item.find_element(By.CLASS_NAME, "dropBlock")
                # Identifier le bloc qui contient les détails de l'auteur
                     author_details_div = author_name_span.find_element(By.TAG_NAME, "div")
                     content_div = author_details_div.find_element(By.CLASS_NAME, "dropBlock__body").find_element(By.CLASS_NAME, "content")

                # Extraire les affiliations ou autres détails de l'auteur
                     affiliations_div = content_div.find_element(By.CLASS_NAME, "affiliations")
                     author_affiliation = affiliations_div.text  # Extraire les affiliations de l'auteur
                     affiliation_parts = [part.strip() for part in author_affiliation.split(',')]
                     if affiliation_parts:  # Vérifier si affiliation_parts n'est pas vide
    # Ajouter le pays (dernier élément) si ce pays n'est pas déjà dans la liste
                       country = affiliation_parts[-1]
                       if country not in pays:
                          pays.append(country)
                       labo_actuel = ", ".join(affiliation_parts[:2]) if len(affiliation_parts) >= 2 else "Non spécifié"
                       if labo_actuel not in labos:
                          labos.append(labo_actuel)
                     header_element = driver.find_element(By.CLASS_NAME, "container.header--first-row")
                     header_element.click()
                     logging.info("Div fermé en cliquant sur le header.")
                     time.sleep(5)
                  except Exception as e:
                    logging.error(f"Erreur lors de l'extraction des informations d'un auteur : {e}")
                    
                quartile=scrape_journal_data(publisher,publish_date,driver)
                print(f"quartile:{quartile}")
                # Ajouter l'article et ses informations dans la liste
                site="ACM"
                data={
                    "title": title,
                    "authors": authors,
                    "date": publish_date,
                    "pays":pays,
                    "laboratoire":labos,
                    "publisher":publisher,
                    "quartile":quartile,
                    "topic":topic,
                    "citations":citations,
                    "views":views,
                    "site":site
                }
                """
                try:
                    collection.insert_one(data)
                    logging.info(f"Données insérées pour : {title}")
                except errors.PyMongoError as e:
                    logging.error(f"Erreur MongoDB : {e}")
                """
                save_to_json(data)
                driver.get(url)  # Cela permet de revenir à la page des résultats
                time.sleep(5)
            except Exception as e:
                logging.error(f"Erreur lors du traitement de l'article {article_href} : {e}")
                continue

        return data
    except Exception as e:
        logging.error(f"Erreur générale lors du scraping : {e}")
        return []
    finally:
        driver.quit()