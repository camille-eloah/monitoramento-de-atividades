from flask import Flask , Blueprint, render_template, request, redirect, url_for, flash
from app.controllers.auth import executar_query
from flask_login import LoginManager, current_user, login_required
from app import get_db_connection
import pymysql
from pymysql.err import IntegrityError

bp = Blueprint('logs', __name__, url_prefix='/logs')

from flask import Flask, Blueprint, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, current_user, login_required
from app import get_db_connection
import pymysql
from pymysql.err import IntegrityError

bp = Blueprint('logs', __name__, url_prefix='/logs')

@bp.route('/')
@bp.route('/logs')
@login_required  # Garante que o usuário esteja autenticado
def index():
    # Conecta ao banco de dados
    connection = get_db_connection()
    try:
        with connection.cursor(dictionary=True) as cursor:
            # Verifica se o usuário atual tem o perfil de administrador (prof_admin = 1)
            cursor.execute("SELECT prof_admin FROM tb_professores WHERE prof_id = %s", (current_user.id,))
            result = cursor.fetchone()

            if result and result['prof_admin'] == 1:
                # Se o usuário for um administrador, renderiza a página de logs
                return render_template('logs/logs.html')
            else:
                # Caso contrário, redireciona para a página inicial
                flash("Você não tem permissão para acessar essa página.", "warning")
                return redirect(url_for('index.index'))  # Altere 'home.index' para o nome correto da sua página inicial

    except Exception as e:
        flash(f"Erro ao verificar permissões: {e}", "danger")
        return redirect(url_for('index.index'))  # Em caso de erro, redireciona para a página inicial
    finally:
        connection.close()
