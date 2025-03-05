from flask import Flask
from flask_login import LoginManager
import pymysql

# Configuração do Banco de Dados
DB_NAME = "db_monitoramento"

def create_database():
    """Cria o banco de dados caso ele não exista."""
    connection = pymysql.connect(
        host='127.0.0.1',
        user='root',
        password='',
        cursorclass=pymysql.cursors.DictCursor
    )
    with connection.cursor() as cursor:
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
    connection.commit()
    connection.close()

def get_db_connection():
    """Garante que o banco existe e retorna uma conexão com ele."""
    create_database()  # Garante que o banco existe antes de tentar conectar
    connection = pymysql.connect(
        host='127.0.0.1',
        user='root',
        password='',
        database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor
    )
    return connection

def initialize_database():
    """Executa o script de criação das tabelas."""
    connection = get_db_connection()
    with connection.cursor() as cursor:
        with open("init_db.sql", "r", encoding="utf-8") as f:
            sql_script = f.read()
            for statement in sql_script.split(";"):
                if statement.strip():  # Evita comandos vazios
                    cursor.execute(statement)
    connection.commit()
    connection.close()

def create_app():
    # Criar a aplicação Flask
    app = Flask(__name__)
    app.secret_key = 'SUPERULTRASEGREDO'  # Idealmente, use uma variável de ambiente

    # Criar e inicializar o banco de dados
    initialize_database()

    # Configuração do Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    from app.models.models import Professor

    @login_manager.user_loader
    def load_user(prof_id):
        return Professor.get(prof_id)

    # Importação e registro dos Blueprints
    from app.controllers import (
        aluno_disciplina, alunos, atividades, aulas, cursos, 
        disciplinas, relatorios, auth, index
    )
    
    app.register_blueprint(aluno_disciplina.bp)
    app.register_blueprint(alunos.bp)
    app.register_blueprint(atividades.bp)
    app.register_blueprint(aulas.bp)
    app.register_blueprint(cursos.bp)
    app.register_blueprint(disciplinas.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(relatorios.bp)
    app.register_blueprint(index.bp)

    return app
