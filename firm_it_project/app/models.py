# app/models.py
from app import create_app
import pymysql
# app/models.py
# app/models.py
import os

class Automation:
    def __init__(self):
        self.app = create_app()
        self.connection = self.app.mysql_connection

    def get_all_products(self):
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT * FROM automation")
                products = cursor.fetchall()
                # Добавляем относительный путь к картинкам
                for product in products:
                    # Используем replace для замены \ на /
                    product['image'] = os.path.join('images', 'automation', product['image']).replace("\\", "/")
                return products
        finally:
            self.connection.close()

