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
        
        return redirect(url_for('aulas.cad_aulas'))

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

        return redirect(url_for('aulas.cad_aulas'))

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

    return redirect(url_for('aulas.cad_aulas'))

@bp.route('/add_frequencia/<int:aul_id>', methods=['GET', 'POST'])
@login_required
def add_frequencia(aul_id):
    connection = get_db_connection()
    if request.method == "POST":
        print("Conteúdo do form:", request.form)
        
        try:
            with connection.cursor() as cursor:
                # Processa cada aluno e sua frequência
                for alu_id in request.form:
                    if alu_id.startswith('frequencias['):  # Verifica se a chave pertence à frequência
                        # Extrai o ID do aluno
                        aluno_id = int(alu_id.split('[')[1].split(']')[0])  # Extraindo o alu_id
                        
                        # Obtém o valor da frequência (0 ou 1)
                        frequencia = int(request.form[alu_id])  # Pega o valor inserido pelo usuário (0 ou 1)

                        print(f"Aluno ID: {aluno_id}, Frequência: {frequencia}")  # Debug

                        # Verifica se já existe uma entrada na tabela de frequências
                        cursor.execute("""
                            SELECT * FROM tb_aula_frequencia
                            WHERE freq_aula_id = %s AND freq_alu_id = %s
                        """, (aul_id, aluno_id))

                        existing = cursor.fetchone()

                        if existing:
                            # Se já existir, atualiza a frequência
                            cursor.execute("""
                                UPDATE tb_aula_frequencia
                                SET freq_frequencia = %s
                                WHERE freq_aula_id = %s AND freq_alu_id = %s
                            """, (frequencia, aul_id, aluno_id))
                        else:
                            # Se não existir, insere uma nova entrada
                            cursor.execute("""
                                INSERT INTO tb_aula_frequencia (freq_aula_id, freq_alu_id, freq_frequencia)
                                VALUES (%s, %s, %s)
                            """, (aul_id, aluno_id, frequencia))

            connection.commit()
            flash("Frequência salva com sucesso!", "success")
        except Exception as e:
            connection.rollback()
            flash(f"Erro ao salvar frequência: {str(e)}", "error")

        return redirect(url_for('aulas.add_frequencia', aul_id=aul_id))

    # Busca alunos e frequências da aula
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT a.alu_id, a.alu_nome, IFNULL(f.freq_frequencia, 0) AS freq_frequencia
            FROM tb_alunos a
            LEFT JOIN tb_aula_frequencia f ON a.alu_id = f.freq_alu_id AND f.freq_aula_id = %s
            WHERE a.alu_id IN (SELECT ad_alu_id FROM tb_alunos_disciplinas WHERE ad_dis_id = (SELECT aul_dis_id FROM tb_aulas WHERE aul_id = %s))
        """, (aul_id, aul_id))

        alunos_frequencia = cursor.fetchall()
        print("alunos_frequencia:", alunos_frequencia)  # Verificando os alunos e suas frequências

    connection.close()
    return render_template('aulas/add_frequencia.html', alunos=alunos_frequencia, aul_id=aul_id)
