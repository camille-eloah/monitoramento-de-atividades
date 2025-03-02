from flask import Flask , Blueprint, render_template, request, redirect, url_for, flash
from app.controllers.auth import executar_query
from flask_login import LoginManager, current_user, login_required
from app import get_db_connection



bp = Blueprint('disciplinas', __name__, url_prefix='/disciplinas')

@bp.route('/')
def index():
    return render_template('disciplinas/index.html') 

# Cadastrar disciplina
@bp.route('/cad_disciplinas', methods=['POST', 'GET'])
@login_required
def cad_disciplinas():
    connection = get_db_connection()
    disciplinas = []
    cursos = []
    professores = []

    if request.method == "POST":
        nome = request.form['nome']
        prof_responsavel = request.form['prof_responsavel']
        carga_hr = request.form['carga_hr']
        curso_ids = request.form.getlist('curso_id')  # Permite selecionar vários cursos

        try:
            # Inserir a disciplina
            query = """
            INSERT INTO tb_disciplinas (dis_nome, dis_prof_responsavel, dis_carga_hr)
            VALUES (%s, %s, %s)
            """
            with connection.cursor() as cursor:
                cursor.execute(query, (nome, prof_responsavel, carga_hr))
                connection.commit()

                # Recuperar o ID da disciplina recém inserida
                disciplina_id = cursor.lastrowid

                # Associar a disciplina aos cursos
                for curso_id in curso_ids:
                    cursor.execute("""
                    INSERT INTO tb_cursos_disciplinas (cd_cur_id, cd_dis_id)
                    VALUES (%s, %s)
                    """, (curso_id, disciplina_id))
                connection.commit()

            flash("Disciplina cadastrada com sucesso!", category="success")
        except Exception as e:
            connection.rollback()
            flash(f"Erro ao cadastrar disciplina: {e}", category="error")

    # Consultar disciplinas, cursos e professores
    with connection.cursor() as cursor:
        # Buscar todas as disciplinas
        cursor.execute("""
        SELECT d.*, p.prof_nome 
        FROM tb_disciplinas d
        LEFT JOIN tb_professores p ON d.dis_prof_responsavel = p.prof_id
        """)
        disciplinas = cursor.fetchall()

        # Para cada disciplina, buscar os cursos associados
        disciplinas_com_cursos = []
        for disciplina in disciplinas:
            cursor.execute("""
            SELECT c.cur_nome 
            FROM tb_cursos_disciplinas cd
            JOIN tb_cursos c ON cd.cd_cur_id = c.cur_id
            WHERE cd.cd_dis_id = %s
            """, (disciplina['dis_id'],))
            cursos_associados = [row['cur_nome'] for row in cursor.fetchall()]
            disciplina['cursos_associados'] = cursos_associados
            disciplinas_com_cursos.append(disciplina)

        # Buscar todos os cursos
        cursor.execute('SELECT * FROM tb_cursos')
        cursos = cursor.fetchall()

        # Buscar todos os professores
        cursor.execute('SELECT * FROM tb_professores')
        professores = cursor.fetchall()

    connection.close()

    return render_template(
        'disciplinas/cad_disciplinas.html',
        disciplinas=disciplinas_com_cursos,
        cursos=cursos,
        professores=professores
    )


# Editar disciplina
@bp.route('/edit_disciplinas/<int:dis_id>', methods=['POST', 'GET']) 
@login_required
def edit_disciplinas(dis_id):
    connection = get_db_connection()

    # Obter detalhes da disciplina
    with connection.cursor() as cursor:
        cursor.execute("""
        SELECT * FROM tb_disciplinas WHERE dis_id = %s
        """, (dis_id,))
        disciplina = cursor.fetchone()

        # Obter todos os professores para exibição
        cursor.execute("""
        SELECT * FROM tb_professores
        """)
        professores = cursor.fetchall()

        # Obter todos os cursos
        cursor.execute("""
        SELECT * FROM tb_cursos
        """)
        cursos = cursor.fetchall()

        # Obter IDs dos cursos associados à disciplina
        cursor.execute("""
        SELECT cd_cur_id FROM tb_cursos_disciplinas WHERE cd_dis_id = %s
        """, (dis_id,))
        cursos_associados_ids = [row['cd_cur_id'] for row in cursor.fetchall()]

    if request.method == 'POST':
        novo_nome = request.form['nome']
        nova_prof_responsavel = request.form.get('prof_responsavel')
        nova_carga_hr = request.form['carga_hr']
        novos_cursos_ids = request.form.getlist('curso_id')  # IDs dos cursos selecionados

        try:
            with connection.cursor() as cursor:
                # Atualizar detalhes da disciplina
                cursor.execute("""
                UPDATE tb_disciplinas 
                SET dis_nome = %s, dis_prof_responsavel = %s, dis_carga_hr = %s
                WHERE dis_id = %s
                """, (novo_nome, nova_prof_responsavel, nova_carga_hr, dis_id))

                # Atualizar associações de cursos
                # Remover associações antigas
                cursor.execute("""
                DELETE FROM tb_cursos_disciplinas WHERE cd_dis_id = %s
                """, (dis_id,))

                # Inserir novas associações
                for curso_id in novos_cursos_ids:
                    cursor.execute("""
                    INSERT INTO tb_cursos_disciplinas (cd_cur_id, cd_dis_id)
                    VALUES (%s, %s)
                    """, (curso_id, dis_id))

                connection.commit()

            flash("Disciplina atualizada com sucesso!", category="success")
        except Exception as e:
            connection.rollback()
            flash(f"Erro ao atualizar disciplina: {e}", category="error")

        return redirect (url_for('disciplinas.cad_disciplinas'))

    connection.close()

    return render_template(
        'disciplinas/edit_disciplina.html',
        disciplina=disciplina,
        cursos=cursos,
        cursos_associados_ids=cursos_associados_ids,
        professores=professores
    )


# Remover disciplina
@bp.route('/delete_disciplina/<int:dis_id>', methods=['POST'])
@login_required
def delete_disciplina(dis_id):
    connection = get_db_connection()

    try:
        query = "DELETE FROM tb_disciplinas WHERE dis_id = %s"
        executar_query(query, (dis_id,))
        flash("Disciplina removida com sucesso!", "success")
    except Exception as e:
        flash(f"Erro ao remover disciplina: {e}", "danger")
    finally:
        connection.close()

    return redirect(url_for('disciplinas.cad_disciplinas'))