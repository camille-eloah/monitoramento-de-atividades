from flask import Flask , Blueprint, render_template, request, redirect, url_for, flash
from controllers.auth import executar_query
from flask_login import LoginManager, current_user, login_required
from app import app, get_db_connection
import pymysql
from pymysql.err import IntegrityError

bp = Blueprint('frequencias', __name__, url_prefix='/frequencias')

@bp.route('/')
def index():
    return render_template('frequencias/index.html') 

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

        return redirect(url_for('add_frequencia', aul_id=aul_id))

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
