import asyncio
import aiohttp
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify
from pymongo import MongoClient
from urllib.parse import urljoin
import os
import json
from bson import ObjectId
from multiprocessing import Pool, cpu_count, get_context

sem = asyncio.Semaphore(10)

app = Flask(__name__)


mongo_uri = os.getenv('MONGO_URI', 'mongodb://mongo:27017/')
client = MongoClient(mongo_uri)
db = client['Scrapper']


if 'scrapped_data' not in db.list_collection_names():
    print("Tworzenie kolekcji 'scrapped_data'")
    collection = db.create_collection('scrapped_data')
else:
    print("Kolekcja 'scrapped_data' już istnieje")
    collection = db['scrapped_data']

@app.route('/')
def home():
    return "Scrapper działa!"

class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        return json.JSONEncoder.default(self, obj)

app.json_encoder = JSONEncoder

def convert_objectid_to_str(data):
    if isinstance(data, list):
        for item in data:
            if '_id' in item and isinstance(item['_id'], ObjectId):
                item['_id'] = str(item['_id'])
    elif isinstance(data, dict):
        if '_id' in data and isinstance(data['_id'], ObjectId):
            data['_id'] = str(data['_id'])
    return data

async def fetch_page(session, page_number, artist_name):
    artist_name_formatted = artist_name.replace(' ', '+')
    url = f'https://www.cd-dvd-vinyl.pl/f/{artist_name_formatted},art/szukanie,0,0,0,{page_number}.html'
    async with sem:
        try:
            async with session.get(url) as response:
                response.raise_for_status()
                return await response.text()
        except aiohttp.ClientError as e:
            print(f"Błąd pobierania strony {page_number}: {e}")
            return ""

async def check_page_exists(session, page_number, artist_name):
    html_content = await fetch_page(session, page_number, artist_name)
    if not html_content:
        return False

    soup = BeautifulSoup(html_content, 'lxml')
    return not soup.find('p', class_='error-bar')

def find_total_pages(artist_name):
    async def find():
        async with aiohttp.ClientSession() as session:
            page_number = 1
            while True:
                exists = await check_page_exists(session, page_number, artist_name)
                if not exists:
                    break
                page_number += 1
            return page_number - 1

    new_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(new_loop)
    return new_loop.run_until_complete(find())

def process_page_sync(page_number, artist_name, base_url):
    async def fetch_and_process():
        async with aiohttp.ClientSession() as session:
            html_content = await fetch_page(session, page_number, artist_name)
            if not html_content:
                return [], False

            soup = BeautifulSoup(html_content, 'lxml')

            if soup.find('p', class_='error-bar'):
                return [], True

            items = soup.find_all('a', {'title': True, 'href': True})
            data = []

            for item in items:
                title = item.find('span', class_='tit')
                author = item.find('span', class_='autor')
                price = item.find('span', class_='val')
                genre = item.find('li', {'href': True, 'title': True})
                media = item.find('li', class_='media')
                ean = item.find('li', string=lambda text: text and text.startswith('EAN:'))
                img = item.find('img')

                if title and author and price and genre and media and img:
                    author_text = author.get_text(strip=True)

                    if author_text.lower() != artist_name.lower():
                        continue

                    title_text = title.get_text(strip=True)
                    price_text = price.get_text(strip=True)
                    genre_text = genre.get_text(strip=True) if genre else "Nieokreślony"
                    media_text = media.find_all('div', class_='splited')

                    if len(media_text) == 2:
                        media_count = media_text[0].get_text(strip=True).replace("Nośników: ", "")
                        media_type = media_text[1].get_text(strip=True)
                    else:
                        media_count = "Nieznane"
                        media_type = "Nieznany"
                    
                    ean_text = ean.get_text(strip=True).replace("EAN: ", "") if ean else "Nieznany"

                    data.append({'Author': author_text, 'Title': title_text, 'Genre': genre_text, 'Price': price_text,
                                 'Media Count': media_count, 'Media Type': media_type, 'EAN': ean_text,
                                 'Image URL': urljoin(base_url, img['src'])})


                    print(f"Zescrapowano {ean_text}")

            return data, False

    new_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(new_loop)
    return new_loop.run_until_complete(fetch_and_process())

def save_to_database_sync(collection, data):
    print(f"Próba zapisu {len(data)} rekordów do bazy danych")
    for record in data:
        # Sprawdzenie, czy rekord już istnieje w bazie
        existing_record = collection.find_one({'EAN': record['EAN']})
        if existing_record:
            print(f"Rekord o EAN {record['EAN']} już istnieje w bazie. Pomijam zapis.")
        else:
            collection.insert_one(record)
            print(f"Zapisano rekord o EAN {record['EAN']} do bazy danych MongoDB.")

def chunk_list(lst, chunk_size):
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]

def main_sync(artist_name):
    base_url = "https://www.cd-dvd-vinyl.pl/"
    max_pages = find_total_pages(artist_name)
    all_data = []
    page_numbers = list(range(1, max_pages + 1))
    chunk_size = cpu_count()

    ctx = get_context("spawn")
    with ctx.Pool(cpu_count()) as pool:
        for page_chunk in chunk_list(page_numbers, chunk_size):
            results = pool.starmap(process_page_sync, [(i, artist_name, base_url) for i in page_chunk])
            for page_data, no_more_results in results:
                all_data.extend(page_data)
                if no_more_results:
                    break

    save_to_database_sync(collection, all_data)
    return all_data

@app.route('/scrape', methods=['POST'])
def scrape():
    data = request.json
    artist_name = data['artist_name']
    print(f"Rozpoczynanie scrapowania dla artysty: {artist_name}")
    
    all_data = main_sync(artist_name)

    if all_data:
        print(f"Scrapowanie zakończone, liczba rekordów: {len(all_data)}")
        all_data = convert_objectid_to_str(all_data)
        return jsonify({"message": "Scrapping zakończony", "albums": all_data}), 200
    else:
        print("Nie znaleziono żadnych danych do zapisania.")
        return jsonify({"message": "Nie znaleziono żadnych danych do zapisania."}), 300

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
