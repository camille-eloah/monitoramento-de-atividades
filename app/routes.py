from flask import render_template, request, redirect
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from app import app, get_db_connection, routes
from werkzeug.security import generate_password_hash, check_password_hash

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/cad_aluno')
def cad_aluno():
    return render_template('alunos/cad_aluno.html')

@app.route('/cad_disciplinas')
def cad_disciplinas():
    return render_template('disciplinas/cad_disciplinas.html')

@app.route('/cad_atividades')
def cad_atividades():
    return render_template('atividades/cad_atividades.html')

@app.route('/gestao_freq')
def gestao_freq():
    return render_template('frequencia/gestao_freq.html')

@app.route('/relatorios')
def relatorios():
    return render_template('relatorios/relatorios.html')
