import psycopg2
from config import Config

class Database:
    def __init__(self):  

        self.connection = psycopg2.connect(
            dbname = Config.database_name,
            user = Config.database_user,
            password = Config.database_user_password,
            host = "localhost"
        )
        self.cursor = self.connection.cursor()  

    def add_users(self, user_id, user_teg, user_trophies):
        self.cursor.execute("INSERT INTO players (id, player_tag, trophies) VALUES (%s, %s, %s)", (user_id, user_teg, user_trophies))
        self.connection.commit()
    

    def check_user(self, user_id):
        self.cursor.execute(
            "SELECT EXISTS (SELECT 1 FROM players WHERE id = %s)",
            (user_id,)
        )
        return self.cursor.fetchone()[0]
