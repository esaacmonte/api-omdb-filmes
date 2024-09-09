import requests
import pandas as pd
import sqlite3
from collections import defaultdict

# Define classes
class Movie:
    def __init__(self, title, year, box_office, actors, movie_type):
        self.title = title
        self.year = year
        self.box_office = box_office
        self.actors = actors
        self.movie_type = movie_type

class OMDBClient:
    def __init__(self, api_key):
        self.api_key = api_key

    def search_movies(self, year):
        url = f'http://www.omdbapi.com/'
        params = {
            'apikey': self.api_key,
            's': year,
            'type': 'movie',
            'page': 1
        }

        movies = []
        while True:
            response = requests.get(url, params=params)
            data = response.json()
            if data.get('Response') == 'True':
                movies.extend(data.get('Search', []))
                params['page'] += 1
                if params['page'] > int(data.get('totalResults', 0)) // 10 + 1:
                    break
            else:
                break
        return movies

    def get_movie_details(self, imdb_id):
        url = f'http://www.omdbapi.com/'
        params = {
            'apikey': self.api_key,
            'i': imdb_id
        }
        response = requests.get(url, params=params)
        return response.json()

    def parse_movie_data(self, data):
        title = data.get('Title', 'Unknown')
        year = data.get('Year', 'Unknown')

        # Verifica o valor de BoxOffice
        box_office = data.get('BoxOffice', 'N/A')
        if box_office == 'N/A':
            box_office = 'Não Disponível'

        actors = data.get('Actors', 'Unknown').split(', ')    
        movie_type = data.get('Type', 'Unknown')
        return Movie(title, year, box_office, actors, movie_type)

class MovieDatabase:
    def __init__(self):
        self.movies_by_year = defaultdict(list)
        self.movies_by_box_office = defaultdict(list)
        self.actors_movies = defaultdict(list)

    def add_movie(self, movie):
        self.movies_by_year[movie.year].append(movie)
        self.movies_by_box_office[movie.box_office].append(movie)
        for actor in movie.actors:
            self.actors_movies[actor].append(movie)

# Classe para gerenciar o banco de dados SQLite
class SQLiteDatabase:
    def __init__(self, db_name):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        # Criação da tabela de filmes com a coluna 'type'
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS movies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                year TEXT,
                box_office TEXT,
                actors TEXT,
                type TEXT
            )
        ''')
        self.conn.commit()

    def insert_movie(self, movie):
        # Inserir filme no banco de dados
        self.cursor.execute('''
            INSERT INTO movies (title, year, box_office, actors, type) 
            VALUES (?, ?, ?, ?, ?)
        ''', (movie.title, movie.year, movie.box_office, ', '.join(movie.actors), movie.movie_type))
        self.conn.commit()

    def close(self):
        self.conn.close()

def main():
    api_key = 'cdc63305'  # Substitua pela sua chave de API
    client = OMDBClient(api_key)
    movie_db = MovieDatabase()
    
    # Cria o banco de dados SQLite
    sqlite_db = SQLiteDatabase('movies_v3.db')

    # Buscar todos os filmes de 2024
    movies_data = client.search_movies('2023')

    movies_list = []
    for movie_data in movies_data:
        movie_details = client.get_movie_details(movie_data['imdbID'])

        # Filtrar apenas filmes de 2024
        if movie_details.get('Year') == '2023':
            movie = client.parse_movie_data(movie_details)
            movie_db.add_movie(movie)
            movies_list.append({
                'Title': movie.title,
                'Year': movie.year,
                'BoxOffice': movie.box_office,
                'Actors': ', '.join(movie.actors),
                'Type': movie.movie_type
            })

            # Inserir o filme no banco de dados
            sqlite_db.insert_movie(movie)

    # Criar DataFrame
    df = pd.DataFrame(movies_list)
    print(df)

    # Fechar conexão com o banco de dados
    sqlite_db.close()

if __name__ == '__main__':
    main()
