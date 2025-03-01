from flask import Flask , Blueprint, render_template, request, redirect, url_for, flash
from app.controllers.auth import executar_query
from flask_login import LoginManager, current_user, login_required
from app import get_db_connection
import pymysql
from pymysql.err import IntegrityError

bp = Blueprint('aulas', __name__, url_prefix='/aulas')

@bp.route('/')
def index():
    return render_template('aulas/index.html') 

# Cadastro de aulas
@bp.route('/cad_aulas', methods=['POST', 'GET'])
@login_required
def cad_aulas():
    connection = get_db_connection()
    aulas = []
    professores = []
    disciplinas = []

    # Coleta os professores e disciplinas para o formulário
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM tb_professores")
        professores = cursor.fetchall()

        cursor.execute("SELECT * FROM tb_disciplinas")
        disciplinas = cursor.fetchall()

    # Exibe as aulas já cadastradas
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM tb_aulas")
        aulas = cursor.fetchall()

    if request.method == "POST":
        aul_descricao = request.form['descricao']  
        aul_data = request.form['data']
        aul_prof_id = request.form['professor'] 
        aul_dis_id = request.form['disciplina'] 

        query_aula = """
        INSERT INTO tb_aulas (aul_descricao, aul_data, aul_prof_id, aul_dis_id)
        VALUES (%s, %s, %s, %s)
        """
        try:
            with connection.cursor() as cursor:
                # Inserir a nova aula
                cursor.execute(query_aula, (aul_descricao, aul_data, aul_prof_id, aul_dis_id))
                aula_id = connection.insert_id()  # Obter o ID da aula recém-criada

                # Obter os alunos da disciplina correspondente
                cursor.execute("""
                SELECT ad_alu_id 
                FROM tb_alunos_disciplinas
                WHERE ad_dis_id = %s
                """, (aul_dis_id,))
                alunos = cursor.fetchall()
                
                print("Resultado da consulta alunos:", alunos)

                # Inicializar frequência com "1" para cada aluno
                query_frequencia = """
                INSERT INTO tb_aula_frequencia (freq_aula_id, freq_alu_id, freq_frequencia)
                VALUES (%s, %s, %s)
                """
                for aluno in alunos:
                    cursor.execute(query_frequencia, (aula_id, aluno['ad_alu_id'], 1))  # Use 'ad_alu_id' corretamente

                # Confirmar as alterações
                connection.commit()

            flash("Aula cadastrada com sucesso e frequência inicializada!", "success")
        except IntegrityError as e:
            connection.rollback()
            if "Duplicate entry" in str(e):
                flash("Erro: Aula duplicada ou já cadastrada.", "error")
            else:
                flash("Erro ao cadastrar a aula. Tente novamente mais tarde.", "error")
        except Exception as e:
            connection.rollback()
            flash(f"Erro inesperado: {str(e)}", "error")
        
        return redirect(url_for('cad_aulas'))

    connection.close()
    return render_template('aulas/cad_aulas.html', aulas=aulas, professores=professores, disciplinas=disciplinas)


#Editar aulas
@bp.route('/edit_aula/<int:aul_id>', methods=['POST', 'GET'])
@login_required
def edit_aula(aul_id):
    connection = get_db_connection()

    # Selecionar aula específica
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM tb_aulas WHERE aul_id = %s", (aul_id,))
        aula = cursor.fetchone()

        cursor.execute('SELECT * FROM tb_professores')
        professores = cursor.fetchall()

        cursor.execute("SELECT * FROM tb_disciplinas")
        disciplinas = cursor.fetchall()

    if request.method == 'POST':
        nova_descricao = request.form['descricao']
        nova_data = request.form['data']
        

        query = """
        UPDATE tb_aulas 
        SET aul_descricao = %s, aul_data = %s
        WHERE aul_id = %s
        """
        executar_query(query, (nova_descricao, nova_data, aul_id))

        return redirect('/cad_aulas')

    connection.close()
    return render_template('aulas/edit_aula.html', aula=aula, professores=professores, disciplinas=disciplinas)

#Deletar aulas
@bp.route('/delete_aula/<int:aul_id>', methods=['POST'])
@login_required
def delete_aula(aul_id):
    connection = get_db_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM tb_aulas WHERE aul_id = %s", (aul_id,))
            connection.commit()
            flash("Aula deletada com sucesso!", "success")
    except Exception as e:
        connection.rollback()
        flash(f"Erro ao deletar aula: {e}", "error")
    finally:
        connection.close()

    return redirect('/cad_aulas')

