from flask import Flask , Blueprint, render_template, request, redirect, url_for, flash
from app.controllers.auth import executar_query
from flask_login import LoginManager, current_user, login_required
from app import get_db_connection
import pymysql
from pymysql.err import IntegrityError

bp = Blueprint('cursos', __name__, url_prefix='/cursos')


@bp.route('/')
def index():
    return render_template('cursos/index.html') 

#Cadastrar cursos
@bp.route('/cad_curso', methods=['POST', 'GET'])
@login_required
def cad_curso():
    connection = get_db_connection()
    cursos = []

    # Exibe os cursos já cadastrados
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM tb_cursos")
        cursos = cursor.fetchall()

    if request.method == "POST":
        cur_nome = request.form['nome']
        cur_descricao = request.form['descricao']

        query = """
        INSERT INTO tb_cursos (cur_nome, cur_descricao)
        VALUES (%s, %s)
        """
        try:
            executar_query(query, (cur_nome, cur_descricao))
            flash("Curso cadastrado com sucesso!", "success")
        except IntegrityError as e:
            if "Duplicate entry" in str(e):
                flash("Erro: Curso duplicado ou já cadastrado.", "error")
            else:
                flash("Erro ao cadastrar o curso. Tente novamente mais tarde.", "error")
        
        return redirect(url_for('cursos.cad_curso'))

    connection.close()

    return render_template('cursos/cad_curso.html', cursos=cursos)

# Editar cursos
@bp.route('/edit_curso/<int:cur_id>', methods=['POST', 'GET'])
@login_required
def edit_curso(cur_id):
    connection = get_db_connection()

    # Selecionar atividade específica
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM tb_cursos WHERE cur_id = %s", (cur_id,))
        curso = cursor.fetchone()

    if request.method == 'POST':
        novo_nome = request.form['nome']
        nova_descricao = request.form['descricao']

        try:
            query = """
            UPDATE tb_cursos 
            SET cur_nome = %s, cur_descricao = %s
            WHERE cur_id = %s
            """
            executar_query(query, (novo_nome, nova_descricao, cur_id))

            # Mensagem flash de sucesso
            flash("Curso atualizado com sucesso!", "success")
            return redirect(url_for('cursos.cad_curso'))
        
        except Exception as e:
            # Mensagem flash de erro
            flash(f"Erro ao atualizar o curso: {str(e)}", "error")
            return render_template('cursos/edit_curso.html', curso=curso)

    connection.close()
    return render_template('cursos/edit_curso.html', curso=curso)


#Deletar Cursos
@bp.route('/delete_curso/<int:cur_id>', methods=['POST'])
@login_required
def delete_curso(cur_id):
    connection = get_db_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM tb_cursos WHERE cur_id = %s", (cur_id,))
            connection.commit()
            flash("Curso deletado com sucesso!", "success")
    except Exception as e:
        connection.rollback()
        flash(f"Erro ao deletar curso: {e}", "error")
    finally:
        connection.close()

    return redirect(url_for('cursos.cad_curso'))