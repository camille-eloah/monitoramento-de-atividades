from flask import Flask
from flask_login import LoginManager
import pymysql

def get_db_connection():
    connection = pymysql.connect(
        host='127.0.0.1',
        user='root',
        password='',
        database='db_monitoramento',
        cursorclass=pymysql.cursors.DictCursor
    )
    return connection

def create_app():
    # Criação do aplicativo Flask
    app = Flask(__name__)
    app.secret_key = 'SUPERULTRASEGREDO'  # Idealmente, use uma variável de ambiente ou algo mais seguro

    # Configuração do Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'  # Garantindo que o caminho para login esteja correto
    
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
