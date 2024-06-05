# cddvdvinylscrapper
PL:

Ten projekt to web scraper zaprojektowany do zbierania informacji o albumach CD, DVD i winylowych z cd-dvd-vinyl.pl.

## Funkcje

- Zbiera informacje o albumach, takie jak tytuł, autor, gatunek, cena, liczba nośników, typ nośnika i EAN.
- Przechowuje zebrane dane w bazie danych MongoDB.
- Udostępnia interfejs internetowy do przeglądania i sortowania zebranych danych.
- Paginacja i sortowanie listy albumów.

## Wymagania
- Docker: Do uruchamiania i zarządzania kontenerami.
- Docker Compose: Do uruchamiania wielokontenerowych aplikacji Docker.

## Instalacja

1. Sklonuj repozytorium:

   ```bash
   git clone https://github.com/SekcjaBoksu/cddvdvinylscrapper.git

2. Przejdź do katalogu projektu:

    ```bash
    cd cddvdvinylscrapper
3. Zbuduj i uruchom kontenery Docker:
    
    ```bash
    docker-compose up --build

## Użytkowanie

Otwórz przeglądarkę internetową i przejdź do http://localhost:5000.
Wprowadź nazwę artysty, aby zeskrobać informacje o jego albumach.
Przeglądaj i sortuj zebrane dane na stronie z listą.
## Punkty końcowe API
- /scrape (POST): Rozpoczyna proces skrobania dla podanego artysty.
- /check_scrape_status (GET): Sprawdza status procesu skrobania.
- /list (GET/POST): Wyświetla listę zeskrobanych albumów z możliwościąsortowania i paginacji.
- /norecords (GET): Wyświetla komunikat, gdy nie znaleziono żadnych rekordów dla podanego artysty.

EN:

This project is a web scraper designed to scrape CD, DVD, and vinyl album information from cd-dvd-vinyl.pl.

## Features

- Scrapes album information such as title, author, genre, price, media count, media type, and EAN.
- Stores the scraped data in a MongoDB database.
- Provides a web interface to view and sort the scraped data.
- Pagination and sorting of the album list.

## Requirements

- **Docker**: For running and managing containers.
- **Docker Compose**: For running multi-container Docker applications.

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/SekcjaBoksu/cddvdvinylscrapper.git

2. Navigate to the project directory:
    ```bash
    Navigate to the project directory:

3. Build and run the Docker containers:
    ```bash
    docker-compose up --build

## RUN

- Open your web browser and go to http://localhost:5000.
- Enter the name of an artist to scrape their album information.
- View and sort the scraped data on the list page.
## API Endpoints
- /scrape (POST): Starts the scraping process for a given artist.
- /check_scrape_status (GET): Checks the status of the scraping process.
- /list (GET/POST): Displays the list of scraped albums with sorting and pagination.
- /norecords (GET): Displays a message when no records are found for the given artist.
