from flask import Flask, request, jsonify, redirect, url_for, render_template
from pymongo import MongoClient
import os
import requests

app = Flask(__name__)

# Konfiguracja MongoDB
mongo_uri = os.getenv('MONGO_URI', 'mongodb://mongo:27017/')
client = MongoClient(mongo_uri)
db = client['Scrapper']
collection = db['scrapped_data']

temporary_albums = {}  # Słownik do przechowywania tymczasowych wyników scrapowania

@app.route('/')
def homepage():
    temporary_albums.clear()  # Wyczyść tymczasową listę przy wejściu na stronę główną
    return render_template('homepage.html')

@app.route('/scrape', methods=['POST'])
def scrape():
    try:
        artist_name = request.form['artistName']
        print(f"Przekazywanie nazwy artysty do scrapera: {artist_name}")
        return render_template('scrapper.html', artist_name=artist_name)
    except Exception as e:
        print(f"Błąd podczas przekazywania nazwy artysty: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/check_scrape_status')
def check_scrape_status():
    try:
        artist_name = request.args.get('artist_name')
        # Zapytanie do bazy danych z uwzględnieniem wielkości liter
        count = collection.count_documents({'Author': {'$regex': f'^{artist_name}$', '$options': 'i'}})
        print(f"Sprawdzanie statusu scrapowania dla artysty: {artist_name}, liczba znalezionych dokumentów: {count}")
        if count > 0:
            # Pobierz dokumenty i zapisz do tymczasowego bufora
            temporary_albums[artist_name.lower()] = list(collection.find({'Author': {'$regex': f'^{artist_name}$', '$options': 'i'}}))
            return jsonify({'status': 'completed'})
        else:
            # Wywołaj scrapera, jeśli nie znaleziono dokumentów
            response = requests.post('http://scrapper:5001/scrape', json={'artist_name': artist_name})
            print(f"Odpowiedź scrapera: {response.status_code} - {response.text}")
            if response.status_code == 200:
                return jsonify({'status': 'in_progress'})
            elif response.status_code == 300:
                return jsonify({'status': 'empty'})
            else:
                return jsonify({'status': 'error'})
    except Exception as e:
        print(f"Błąd podczas sprawdzania statusu scrapowania: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/norecords')
def norecords():
    return render_template('norecords.html')

def sort_albums(albums, sort_mode):
    if sort_mode == 'lowest-price':
        return sorted(albums, key=lambda x: float(x['Price'].replace(' zł', '').replace(',', '.')))
    elif sort_mode == 'highest-price':
        return sorted(albums, key=lambda x: float(x['Price'].replace(' zł', '').replace(',', '.')), reverse=True)
    elif sort_mode == 'alphabetical-asc':
        return sorted(albums, key=lambda x: x['Title'])
    elif sort_mode == 'alphabetical-desc':
        return sorted(albums, key=lambda x: x['Title'], reverse=True)
    return albums

@app.route('/list', methods=['GET', 'POST'])
def list_browser():
    try:
        artist_name = request.args.get('artist_name')
        sort_option = request.args.get('sort_option', 'alphabetical-asc')
        page = int(request.args.get('page', 1))
        per_page = 18

        albums = temporary_albums.get(artist_name.lower(), [])
        if not albums:
            # Jeśli nie ma danych w buforze, pobierz je z bazy danych
            albums = list(collection.find({'Author': {'$regex': f'^{artist_name}$', '$options': 'i'}}))
            temporary_albums[artist_name.lower()] = albums

        sorted_albums = sort_albums(albums, sort_option)
        total_albums = len(sorted_albums)
        total_pages = (total_albums + per_page - 1) // per_page
        paginated_albums = sorted_albums[(page - 1) * per_page:page * per_page]

        print(f"Znaleziono {len(albums)} albumów dla artysty: {artist_name}")

        return render_template('list_browser.html', albums=paginated_albums, sort_option=sort_option,
                               total_pages=total_pages, current_page=page, artist_name=artist_name)
    except Exception as e:
        print(f"Błąd podczas wyświetlania listy: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
