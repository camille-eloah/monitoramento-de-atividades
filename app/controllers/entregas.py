from flask import Flask , Blueprint, render_template, request, redirect, url_for, flash
from app.controllers.auth import executar_query
from flask_login import LoginManager, current_user, login_required
from app import get_db_connection
import pymysql
from pymysql.err import IntegrityError

bp = Blueprint('entregas', __name__, url_prefix='/entregas')

@bp.route('/')
def index():
    return render_template('entregas/index.html') 

@bp.route('/registro_entrega/<int:ati_id>', methods=['GET', 'POST'])
@login_required
def registro_entrega(ati_id):
    connection = get_db_connection()

    if request.method == 'POST':
        for aluno_id in request.form.getlist('aluno_id'):
            situacao = request.form.get(f'situacao_{aluno_id}')
            nota = request.form.get(f'nota_{aluno_id}')
            data_entrega = request.form.get(f'data_entrega_{aluno_id}')
            if situacao and nota and data_entrega:
                query_check = """
                    SELECT alunoativ_id
                    FROM tb_aluno_atividade
                    WHERE alunoativ_alu_id = %s AND alunoativ_ati_id = %s
                """
                with connection.cursor() as cursor:
                    cursor.execute(query_check, (aluno_id, ati_id))
                    existing_record = cursor.fetchone()

                if existing_record:
                    query_update = """
                        UPDATE tb_aluno_atividade
                        SET alunoativ_situacao = %s, alunoativ_nota = %s, alunoativ_data_entrega = %s
                        WHERE alunoativ_alu_id = %s AND alunoativ_ati_id = %s
                    """
                    executar_query(query_update, (situacao, float(nota), data_entrega, aluno_id, ati_id))
                else:
                    query_insert = """
                        INSERT INTO tb_aluno_atividade (alunoativ_alu_id, alunoativ_ati_id, alunoativ_situacao, alunoativ_nota, alunoativ_data_entrega)
                        VALUES (%s, %s, %s, %s, %s)
                    """
                    executar_query(query_insert, (aluno_id, ati_id, situacao, float(nota), data_entrega))

        flash("Entregas registradas com sucesso!", "success")
        return redirect(f'/registro_entrega/{ati_id}')

    with connection.cursor() as cursor:
        # Buscar informações da atividade
        cursor.execute("""
            SELECT ati_tipo, ati_descricao, ati_data_entrega, ati_dis_id
            FROM tb_atividades
            WHERE ati_id = %s
        """, (ati_id,))
        atividade = cursor.fetchone()

        # Buscar o nome da disciplina associada à atividade
        cursor.execute("""
            SELECT dis_nome
            FROM tb_disciplinas
            WHERE dis_id = %s
        """, (atividade['ati_dis_id'],))
        disciplina = cursor.fetchone()

        # Buscar os alunos e suas informações de entrega
        cursor.execute("""
            SELECT a.alu_id, a.alu_nome, 
                   COALESCE(aa.alunoativ_situacao, 'Em andamento') AS situacao,
                   COALESCE(aa.alunoativ_nota, 0) AS nota,
                   COALESCE(aa.alunoativ_data_entrega, NULL) AS data_entrega
            FROM tb_alunos a
            JOIN tb_alunos_disciplinas ad ON a.alu_id = ad.ad_alu_id
            LEFT JOIN tb_aluno_atividade aa 
                   ON a.alu_id = aa.alunoativ_alu_id AND aa.alunoativ_ati_id = %s
            WHERE ad.ad_dis_id = %s
        """, (ati_id, atividade['ati_dis_id']))
        alunos = cursor.fetchall()

    # Formatar a data de entrega no formato necessário
    for aluno in alunos:
        if aluno['data_entrega']:
            aluno['data_entrega'] = aluno['data_entrega'].strftime('%Y-%m-%dT%H:%M')

    return render_template(
        'atividades/registro_entrega.html',
        atividade=atividade,
        disciplina=disciplina,
        alunos=alunos,
        ati_id=ati_id
    )