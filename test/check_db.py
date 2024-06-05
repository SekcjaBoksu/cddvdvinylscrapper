from pymongo import MongoClient

# Połączenie z MongoDB
client = MongoClient("mongodb://mongo:27017/")
db = client["Scrapper"]
collection = db["scrapped_data"]

# Wydrukowanie wszystkich dokumentów w kolekcji
for doc in collection.find():
    print(doc)
