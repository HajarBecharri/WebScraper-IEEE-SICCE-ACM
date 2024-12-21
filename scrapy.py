from flask import Flask, jsonify
from selenium.webdriver.common.keys import Keys
import logging
from pymongo import MongoClient
from pymongo import errors
import logging
import undetected_chromedriver as uc
from acm_scraping import scrape_acm
from ieee_scraping import scrape_ieee_research
from science_direct_scraping import scrape_sciencedirect
app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
# Configurer la connexion à MongoDB Atlas
try:
    client = MongoClient('mongodb+srv://hajar:EtqS9hqygUtTRScG@cluster0.oa1urd4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
    db = client['IEEE']
    collection = db['search']
    
    # Test de connexion à MongoDB
    client.admin.command('ping')  # Envoi d'une commande ping pour vérifier la connexion
    logging.info("Connexion à MongoDB réussie.")

except errors.ServerSelectionTimeoutError as e:
    logging.error(f"Erreur de connexion à MongoDB : {e}")
    raise SystemExit("Échec de la connexion à la base de données, arrêtez l'application.")
chromedriver_path = r"C:\Users\pro\.wdm\drivers\chromedriver\win64\131.0.6778.108\chromedriver-win32\chromedriver.exe"

topic="science"
page_number=1
@app.route('/scrape_ieee', methods=['GET'])
def scraping_ieee_research():
    # Configurez le Service pour Selenium
    articles = scrape_ieee_research(collection,topic,page_number)
    return jsonify(articles), 200 if articles else 500

@app.route('/scrape_sciencedirect', methods=['GET'])
def scraping_sciencedirect():
   articles = scrape_sciencedirect(collection,topic,page_number)
   return jsonify(articles), 200 if articles else 500


@app.route('/scrape-acmm', methods=['GET'])
def get_acm_articles():
    """Endpoint pour récupérer les articles scrappés."""
    logging.info("Début du scraping des articles ACM...")
    articles = scrape_acm(collection,topic,page_number)
    return jsonify(articles), 200 if articles else 500



if __name__ == '__main__':
    app.run(debug=True)
    