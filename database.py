import pymysql
from peewee import MySQLDatabase
from pymysql import MySQLError

DB_HOST = 'localhost'
DB_PORT = 3306
DB_USERNAME = 'root'
DB_PASSWORD = 'root'
DB_NAME = 'pc'

def init_database():
    try:
        connection = pymysql.connect(
            host=DB_HOST,
            user=DB_USERNAME,
            password=DB_PASSWORD
        )
        
        with connection.cursor() as cursor:
            cursor.execute(f'CREATE DATABASE IF NOT EXISTS {DB_NAME}')
            print(f'База данных {DB_NAME} успешно создана.')
    except MySQLError as e:
        print(f'Ошибка при создании базы данных: {e}.')
    
    finally:
        if 'connection' in locals() and connection:
            connection.close()

init_database()

db_connection = MySQLDatabase(
    DB_NAME,
    user=DB_USERNAME,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT
)