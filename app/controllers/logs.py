from flask import Flask , Blueprint, render_template, request, redirect, url_for, flash
from app.controllers.auth import executar_query
from flask_login import LoginManager, current_user, login_required
from app import get_db_connection
import pymysql
from pymysql.err import IntegrityError

bp = Blueprint('logs', __name__, url_prefix='/logs')

@bp.route('/')
@bp.route('/logs')
@login_required 
def index():
    # Conecta ao banco de dados
    connection = get_db_connection()
    try:
        with connection.cursor(dictionary=True) as cursor:
            # Verifica se o usuário atual tem o perfil de administrador (prof_admin = 1)
            cursor.execute("SELECT prof_admin FROM tb_professores WHERE prof_id = %s", (current_user.id,))
            result = cursor.fetchone()

            if result and result['prof_admin'] == 1:
                # Se o usuário for um administrador, buscar os logs de notas
                cursor.execute("SELECT * FROM logs_notas ORDER BY data_operacao DESC")
                logs = cursor.fetchall()

                # Renderiza a página de logs com os logs encontrados
                return render_template('logs/logs.html', logs=logs)

            else:
                # Caso contrário, redireciona para a página inicial
                flash("Você não tem permissão para acessar essa página.", "warning")
                return redirect(url_for('index.index')) 

    except Exception as e:
        flash(f"Erro ao verificar permissões ou buscar logs: {e}", "danger")
        return redirect(url_for('index.index'))  # Em caso de erro, redireciona para a página inicial
    finally:
        connection.close()
