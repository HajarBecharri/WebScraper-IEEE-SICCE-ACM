import json
import os
json_file = 'research_data.json'

# Fonction pour ajouter les données au fichier JSON
def save_to_json(data):
    # Vérifier si le fichier existe
    if os.path.exists(json_file):
        try:
            # Si le fichier existe, on charge son contenu
            with open(json_file, 'r', encoding='utf-8') as file:
                existing_data = json.load(file)
        except json.JSONDecodeError:
            # Si le fichier est vide ou corrompu, on initialise une liste vide
            existing_data = []
    else:
        # Si le fichier n'existe pas, on crée une liste vide
        existing_data = []

    # Ajouter les nouvelles données à la liste
    existing_data.append(data)

    # Sauvegarder les données dans le fichier JSON
    with open(json_file, 'w', encoding='utf-8') as file:
        json.dump(existing_data, file, ensure_ascii=False, indent=4)

    print(f"Data saved to {json_file}")