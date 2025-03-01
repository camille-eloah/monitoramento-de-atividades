from flask import render_template, request, redirect, url_for, flash, Blueprint
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from app import app, get_db_connection
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

import pymysql
from pymysql.err import IntegrityError 

from models.models import Professor

from passlib.context import CryptContext

bp = Blueprint('auth', __name__, url_prefix='/auth',  template_folder='../templates')

# Configuração do contexto do Passlib para usar bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@bp.route('/')
def index():
    return render_template('auth/index.html') 

# Cadastro (usuário)
@bp.route('/cadastro', methods=['POST', 'GET'])
def cadastro():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['pass']
        confirmar_senha = request.form['confirm_pass']

        # Verificar se as senhas coincidem
        if senha != confirmar_senha:
            flash("As senhas não coincidem. Por favor, tente novamente.", category="error")
            return redirect(url_for('cadastro'))

        # Gerar a senha criptografada com passlib
        hashed_senha = pwd_context.hash(senha)
        
        connection = get_db_connection()
        try:
            # Inserir o novo usuário no banco de dados
            with connection.cursor() as cursor:
                cursor.execute('INSERT INTO tb_professores (prof_nome, prof_email, prof_senha) VALUES (%s, %s, %s)', 
                               (nome, email, hashed_senha))
                connection.commit()

            # Mensagem de sucesso
            flash('Usuário cadastrado com sucesso!', 'success')
            return redirect('login')  # Redireciona para o login

        except IntegrityError as e:
            # Tratamento de erro de duplicidade (e-mail ou nome já existente)
            if e.args[0] == 1062:
                flash("Já existe um usuário com esse nome ou e-mail.", 'error')
            else:
                flash("Erro ao cadastrar o usuário. Tente novamente mais tarde.", 'error')

        finally:
            connection.close()

    return render_template('auth/cadastro.html')  # Renderiza o formulário de cadastro


# Login
@bp.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        nome = request.form['nome']
        senha = request.form['senha'] 

        # Conectar ao banco de dados
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Verifique se está pegando o usuário correto
            cursor.execute('SELECT * FROM tb_professores WHERE prof_nome = %s', (nome,))
            usuario = cursor.fetchone()

            # Depuração: Verifique o que está sendo recuperado
            print("Usuário encontrado:", usuario)

            if usuario:
                # Depuração: Imprime a senha recuperada do banco e a senha informada
                print("Nome do Usuário:", usuario['prof_nome'])
                print("Senha informada:", senha)
                print("Senha armazenada (hash):", usuario['prof_senha'])

                # Usando passlib para verificar se a senha informada corresponde ao hash armazenado
                if pwd_context.verify(senha, usuario['prof_senha']):
                    # Se a senha estiver correta
                    professor = Professor(usuario['prof_id'], usuario['prof_nome'], usuario['prof_email'], usuario['prof_senha'])
                    login_user(professor)
                    flash('Login realizado com sucesso!', 'success')
                    return redirect('/')
                else:
                    flash('Nome de usuário ou senha inválidos.', 'error')
            else:
                flash('Nome de usuário ou senha inválidos.', 'error')

        connection.close()

    return render_template('auth/login.html')  # Renderiza o template de login

# Logout
@bp.route('/logout')
@login_required
def logout():
    logout_user() 
    flash('Você foi desconectado com sucesso.', 'success')
    return redirect('/index')

@bp.route('/index')
@bp.route('/')
@login_required
def index():
    return render_template('index.html')

def executar_query(query, params=None):
    connection = get_db_connection()
    try: 
        with connection.cursor() as cursor: 
            cursor.execute(query, params)
            connection.commit()
    finally: 
        connection.close()



