from flask import render_template, request, redirect
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from app import app, get_db_connection, routes
from werkzeug.security import generate_password_hash, check_password_hash

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/cad_aluno', methods=['POST', 'GET'])
def cad_aluno():
    if request.method== "POST":
        nome = request.form['nome']
        matricula = request.form['matricula']
        email = request.form['email']
        curso = request.form['curso']
        data_nasc = request.form['data_nasc']

    return render_template('alunos/cad_aluno.html') 

@app.route('/cad_disciplinas', methods=['POST', 'GET'])
def cad_disciplinas():
    if request.method== "POST":
        nome = request.form['nome']
        prof_responsavel = request.form['prof_responsavel']
        carga_hr = request.form['carga_hr']
        
    return render_template('disciplinas/cad_disciplinas.html')

@app.route('/cad_atividades', methods=['POST', 'GET'])
def cad_atividades():
    if request.method== "POST":
        tipo = request.form['tipo']
        descricao = request.form['descricao']
        data_entr = request.form['data_entr']
        peso = request.form['peso']

    return render_template('atividades/cad_atividades.html')

@app.route('/gestao_freq', methods=['POST', 'GET'])
def gestao_freq():
    if request.method== "POST":
        chamada = request.form['chamada']

    return render_template('frequencia/gestao_freq.html')

@app.route('/relatorios')
def relatorios():
    return render_template('relatorios/relatorios.html')
