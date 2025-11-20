from flask import Flask
from config import DB_CONFIG
import pymysql
from flask import session
import socket

def create_app():
    app = Flask(__name__)
    app.secret_key = '123'  
    
    socket.gethostbyaddr = lambda ip: (ip, [], [ip])
     
    # Подключение к MySQL
    app.mysql_connection = pymysql.connect(
        host=DB_CONFIG['host'],
        port=DB_CONFIG['port'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        db=DB_CONFIG['database'],
        cursorclass=pymysql.cursors.DictCursor
    )

    # Регистрация маршрутов
    from app.routes import main_routes
    app.register_blueprint(main_routes)

    return app
