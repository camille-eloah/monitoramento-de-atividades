from flask import Flask
from flask_login import LoginManager
import pymysql

app = Flask(__name__)
app.secret_key = 'SUPERULTRASEGREDO'  

login_manager = LoginManager(app)
login_manager.login_view = 'login'  

def get_db_connection():
    connection = pymysql.connect(
        host='127.0.0.1',
        user='root',
        password='',
        database='monitoramento',
        cursorclass=pymysql.cursors.DictCursor
    )
    return connection

from app.models import Professor

@login_manager.user_loader
def load_user(user_id):
    return Professor.get(user_id)

from app import routes
from app import models