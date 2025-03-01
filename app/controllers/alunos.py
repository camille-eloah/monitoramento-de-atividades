from flask import Flask , Blueprint, render_template, request, redirect, url_for, flash
from controllers.alunos import executar_query
from app.models.models import Aluno
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from app import app, get_db_connection
import pymysql
from pymysql.err import IntegrityError

bp = Blueprint('alunos', __name__, url_prefix='/alunos')

@bp.route('/')
def index():
    return render_template('alunos/index.html') 
# Cadastrar aluno
@bp.route('/cad_aluno', methods=['POST', 'GET'])
@login_required
def cad_aluno():
    connection = get_db_connection()

    # Busca os alunos para exibir na página
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM tb_alunos")
        alunos = cursor.fetchall()

        cursor.execute('SELECT * FROM tb_cursos')
        cursos = cursor.fetchall()

    if request.method == "POST":
        nome = request.form['nome']
        matricula = request.form['matricula']
        email = request.form['email']
        curso = request.form['curso']
        data_nasc = request.form['data_nasc']

        query = """
        INSERT INTO tb_alunos (alu_nome, alu_matricula, alu_email, alu_curso, alu_data_nasc)
        VALUES (%s, %s, %s, %s, %s)
        """
        try:
            executar_query(query, (nome, matricula, email, curso, data_nasc))
            flash("Aluno cadastrado com sucesso!", "success")
        except IntegrityError as e:
            if "Duplicate entry" in str(e):
                flash("Erro: Matrícula ou e-mail já cadastrados no sistema.", "danger")
            else:
                flash("Erro ao cadastrar aluno. Tente novamente mais tarde.", "danger")

        return redirect(url_for('cad_aluno'))

    connection.close()
    return render_template('alunos/cad_aluno.html', alunos=alunos, cursos=cursos)

# Editar aluno
@bp.route('/edit_aluno/<int:alu_matricula>', methods=['POST', 'GET'])
@login_required
def edit_aluno(alu_matricula):
    connection = get_db_connection()
    aluno = None
    cursos = []

    try:
        # Selecionar aluno específico
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM tb_alunos WHERE alu_matricula = %s", (alu_matricula,))
            aluno = cursor.fetchone()

        # Selecionar cursos existentes
        with connection.cursor() as cursor:
            cursor.execute("SELECT cur_id, cur_nome FROM tb_cursos")  # Ajuste para a tabela correta
            cursos = cursor.fetchall()

        if not aluno:
            flash("Aluno não encontrado.", "warning")
            return redirect('/cad_aluno')

        if request.method == 'POST':
            novo_nome = request.form['nome']
            nova_matricula = request.form.get('matricula')
            novo_email = request.form['email']
            novo_curso = request.form['curso']  # ID do curso
            nova_data_nasc = request.form['data_nasc']

            # Validação simples dos campos
            if not all([novo_nome, nova_matricula, novo_email, novo_curso, nova_data_nasc]):
                flash("Por favor, preencha todos os campos corretamente.", "warning")
                return render_template('alunos/edit_aluno.html', aluno=aluno, cursos=cursos)

            query = """
            UPDATE tb_alunos 
            SET alu_nome = %s, alu_matricula = %s, alu_email = %s, alu_curso = %s, alu_data_nasc = %s
            WHERE alu_matricula = %s
            """
            with connection.cursor() as cursor:
                cursor.execute(query, (novo_nome, nova_matricula, novo_email, novo_curso, nova_data_nasc, alu_matricula))
            connection.commit()
            flash("Aluno atualizado com sucesso!", "success")
            return redirect('/cad_aluno')

    except Exception as e:
        flash(f"Erro inesperado: {str(e)}", "danger")
    finally:
        connection.close()

    return render_template('alunos/edit_aluno.html', aluno=aluno, cursos=cursos)

# Remover aluno
@bp.route('/delete_aluno/<int:alu_matricula>', methods=['POST'])
@login_required
def delete_aluno(alu_matricula):
    connection = get_db_connection()
    try:
        query = "DELETE FROM tb_alunos WHERE alu_matricula = %s"
        executar_query(query, (alu_matricula,))
        flash("Aluno removido com sucesso!", "success")
    except Exception as e:
        flash(f"Erro ao remover aluno: {e}", "danger")
    finally:
        connection.close()
    
    return redirect(url_for('cad_aluno'))



if __name__ == "__main__":
    app.run(debug=True)  # 'debug=True' ativa o modo de depuração (opcional)
