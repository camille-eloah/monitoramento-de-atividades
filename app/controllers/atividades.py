from flask import Flask , Blueprint, render_template, request, redirect, url_for, flash
from app.controllers.auth import executar_query
from flask_login import LoginManager, current_user, login_required
from app import get_db_connection
import pymysql
from pymysql.err import IntegrityError

bp = Blueprint('atividades', __name__, url_prefix='/atividades')

@bp.route('/')
def index():
    return render_template('atividades/index.html') 

# Cadastrar atividades
@bp.route('/cad_atividades', methods=['POST', 'GET'])
@login_required
def cad_atividades():
    connection = get_db_connection()
    atividades = []
    disciplinas = []

    try:
        # Selecionar disciplinas existentes
        with connection.cursor() as cursor:
            cursor.execute("SELECT dis_id, dis_nome FROM tb_disciplinas")
            disciplinas = cursor.fetchall()

        if request.method == "POST":
            dis_id = request.form['disciplina']  # Obter ID da disciplina
            tipo = request.form['tipo']
            descricao = request.form['descricao']
            data_entr = request.form['data_entr']
            peso = request.form['peso']

            query = """
            INSERT INTO tb_atividades (ati_dis_id, ati_tipo, ati_descricao, ati_data_entrega, ati_peso)
            VALUES (%s, %s, %s, %s, %s)
            """
            try:
                executar_query(query, (dis_id, tipo, descricao, data_entr, peso))
                flash("Atividade cadastrada com sucesso!", "success")

                # Atualizar a lista de atividades após inserção
                with connection.cursor() as cursor:
                    cursor.execute(""" 
                    SELECT a.ati_id, a.ati_tipo, a.ati_descricao, a.ati_data_entrega, a.ati_peso, d.dis_nome
                    FROM tb_atividades a
                    INNER JOIN tb_disciplinas d ON a.ati_dis_id = d.dis_id
                    """)
                    atividades = cursor.fetchall()
                return redirect(url_for('atividades.cad_atividades'))
            
            except IntegrityError as e:
                if "Duplicate entry" in str(e):
                    flash("Erro: Atividade duplicada ou já cadastrada.", "danger")
                else:
                    flash(f"Erro ao cadastrar a atividade: {str(e)}", "danger")
            except Exception as e:
                flash(f"Erro inesperado: {str(e)}", "danger")

        # Buscar as atividades também no método GET
        with connection.cursor() as cursor:
            cursor.execute(""" 
            SELECT a.ati_id, a.ati_tipo, a.ati_descricao, a.ati_data_entrega, a.ati_peso, d.dis_nome
            FROM tb_atividades a
            INNER JOIN tb_disciplinas d ON a.ati_dis_id = d.dis_id
            """)
            atividades = cursor.fetchall()

    finally:
        connection.close()

    return render_template('atividades/cad_atividades.html', atividades=atividades, disciplinas=disciplinas)

# Editar atividades
@bp.route('/edit_atividade/<int:ati_id>', methods=['POST', 'GET'])
@login_required
def edit_atividade(ati_id):
    connection = get_db_connection()
    atividade = None
    disciplinas = []

    try:
        # Selecionar atividade específica
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM tb_atividades WHERE ati_id = %s", (ati_id,))
            atividade = cursor.fetchone()

        # Selecionar disciplinas existentes para preencher o select
        with connection.cursor() as cursor:
            cursor.execute("SELECT dis_id, dis_nome FROM tb_disciplinas")
            disciplinas = cursor.fetchall()

        if not atividade:
            flash("Atividade não encontrada.", "warning")
            return redirect('/cad_atividades')

        if request.method == 'POST':
            dis_id = request.form.get('disciplina')  # Obter ID da disciplina
            novo_tipo = request.form.get('tipo')
            nova_descricao = request.form.get('descricao')
            nova_data_entr = request.form.get('data_entr')
            novo_peso = request.form.get('peso')

            # Validação simples dos campos
            if not all([dis_id, novo_tipo, nova_descricao, nova_data_entr, novo_peso]):
                flash("Por favor, preencha todos os campos corretamente.", "warning")
                return render_template('atividades/edit_atividade.html', atividade=atividade, disciplinas=disciplinas)

            query = """
            UPDATE tb_atividades 
            SET ati_dis_id = %s, ati_tipo = %s, ati_descricao = %s, ati_data_entrega = %s, ati_peso = %s
            WHERE ati_id = %s
            """
            with connection.cursor() as cursor:
                cursor.execute(query, (dis_id, novo_tipo, nova_descricao, nova_data_entr, novo_peso, ati_id))
            connection.commit()
            flash("Atividade atualizada com sucesso!", "success")
            return redirect(url_for('atividades.cad_atividades'))

    except Exception as e:
        flash(f"Erro inesperado: {str(e)}", "danger")
    finally:
        connection.close()

    return render_template('atividades/edit_atividade.html', atividade=atividade, disciplinas=disciplinas)

# Deletar atividade
@bp.route('/delete_atividade/<int:ati_id>', methods=['POST'])
@login_required
def delete_atividade(ati_id):
    connection = get_db_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM tb_atividades WHERE ati_id = %s", (ati_id,))
            connection.commit()
            flash("Atividade deletada com sucesso!", "success")
    except Exception as e:
        connection.rollback()
        flash(f"Erro ao deletar atividade: {e}", "error")
    finally:
        connection.close()

    return redirect(url_for('atividades.cad_atividades'))

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
        return redirect(url_for('atividades.registro_entrega', ati_id=ati_id))


    with connection.cursor() as cursor:
        # Buscar informações da atividade
        cursor.execute("""
            SELECT ati_id, ati_tipo, ati_descricao, ati_data_entrega, ati_dis_id
            FROM tb_atividades
            WHERE ati_id = %s
        """, (ati_id,))
        atividade = cursor.fetchone()

        if not atividade or 'ati_id' not in atividade:
            flash("Atividade não encontrada!", "danger")
            return redirect(url_for('atividades.index'))

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