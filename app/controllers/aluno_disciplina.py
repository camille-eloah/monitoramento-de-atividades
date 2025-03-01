from flask import Flask , Blueprint, render_template, request, redirect, url_for, flash
from app.controllers.alunos import executar_query
from app.models.models import Aluno
from flask_login import LoginManager, current_user, login_required
from app import app, get_db_connection

bp = Blueprint('aluno_disciplina', __name__, url_prefix='')

@bp.route('/')
def index():
    return render_template('aluno_disciplina/index.html') 

# Adicionar alunos na disciplina
@bp.route('/adicionar_alunos_disciplina/<int:dis_id>', methods=['GET', 'POST'])
@login_required
def adicionar_alunos_disciplina(dis_id):
    connection = get_db_connection()
    alunos = []
    disciplina = None
    alunos_associados = []
    ids_alunos_associados = []  # Lista para armazenar os ids dos alunos associados

    # Busca todos os alunos
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM tb_alunos")
        alunos = cursor.fetchall()

        # Busca a disciplina
        cursor.execute("SELECT * FROM tb_disciplinas WHERE dis_id = %s", (dis_id,))
        disciplina = cursor.fetchone()

        # Busca alunos já associados à disciplina
        cursor.execute("""
            SELECT a.alu_id, a.alu_nome
            FROM tb_alunos a
            JOIN tb_alunos_disciplinas ad ON a.alu_id = ad.ad_alu_id
            WHERE ad.ad_dis_id = %s
        """, (dis_id,))
        alunos_associados = cursor.fetchall()

        # Criar a lista de ids de alunos associados
        ids_alunos_associados = [aluno['alu_id'] for aluno in alunos_associados]

    if request.method == "POST":
        if 'adicionar' in request.form:
            # Recebe os alunos selecionados para associar
            alunos_selecionados = request.form.getlist('alunos')  # Lista de IDs dos alunos selecionados

            try:
                with connection.cursor() as cursor:
                    for aluno_id in alunos_selecionados:
                        # Verifica se o aluno já está associado à disciplina
                        cursor.execute("""
                            SELECT 1 FROM tb_alunos_disciplinas WHERE ad_alu_id = %s AND ad_dis_id = %s
                        """, (aluno_id, dis_id))

                        if not cursor.fetchone():  # Se o aluno não estiver associado
                            # Insere na tabela de relacionamento tb_alunos_disciplinas
                            cursor.execute("""
                                INSERT INTO tb_alunos_disciplinas (ad_alu_id, ad_dis_id)
                                VALUES (%s, %s)
                            """, (aluno_id, dis_id))

                connection.commit()
                flash("Alunos adicionados à disciplina com sucesso!", "success")
            except Exception as e:
                connection.rollback()
                flash(f"Erro ao adicionar alunos: {str(e)}", "error")

            return redirect(url_for('adicionar_alunos_disciplina', dis_id=dis_id))

        elif 'remover' in request.form:
            # Recebe os alunos para remover
            aluno_remover_id = request.form['aluno_id']  # ID do aluno a ser removido

            try:
                with connection.cursor() as cursor:
                    # Remove o aluno da tabela de relacionamento tb_alunos_disciplinas
                    cursor.execute("""
                        DELETE FROM tb_alunos_disciplinas
                        WHERE ad_alu_id = %s AND ad_dis_id = %s
                    """, (aluno_remover_id, dis_id))

                connection.commit()
                flash("Aluno removido da disciplina com sucesso!", "success")
            except Exception as e:
                connection.rollback()
                flash(f"Erro ao remover aluno: {str(e)}", "error")

            return redirect(url_for('adicionar_alunos_disciplina', dis_id=dis_id))

    connection.close()
    return render_template('disciplinas/adicionar_aluno_disciplina.html', 
                           alunos=alunos, 
                           alunos_associados=alunos_associados, 
                           ids_alunos_associados=ids_alunos_associados, 
                           disciplina=disciplina)








