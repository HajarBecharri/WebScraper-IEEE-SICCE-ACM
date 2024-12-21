from flask import Flask, jsonify
from pymongo import MongoClient
import json

app = Flask(__name__)

# Connexion à MongoDB
client = MongoClient('mongodb+srv://hajar:EtqS9hqygUtTRScG@cluster0.oa1urd4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
db = client['IEEE']
collection = db['search']

# Chemin du fichier JSON
json_file = 'research_data.json'

@app.route('/reset_data', methods=['POST'])
def reset_data():
    """
    Supprime tous les documents de la collection, recharge les données JSON et les retourne.
    """
    try:
        # Supprimer tous les documents existants
        collection.delete_many({})
        
        # Charger les nouvelles données du fichier JSON
        with open(json_file, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        # Insérer les nouvelles données
        collection.insert_many(data)
        
        # Retourner les nouveaux documents
        documents = list(collection.find())
        for doc in documents:
            doc['_id'] = str(doc['_id'])  # Convertir ObjectId en chaîne de caractères
        return jsonify({"message": "Données réinitialisées avec succès.", "documents": documents}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get_data', methods=['GET'])
def get_data():
    """
    Retourne tous les documents de la collection.
    """
    try:
        documents = list(collection.find())
        for doc in documents:
            doc['_id'] = str(doc['_id'])  # Convertir ObjectId en chaîne de caractères
        return jsonify({"documents": documents}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
