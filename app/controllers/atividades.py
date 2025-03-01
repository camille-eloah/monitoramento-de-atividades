from flask import Flask , Blueprint, render_template, request, redirect, url_for, flash
from controllers.auth import executar_query
from flask_login import LoginManager, current_user, login_required
from app import app, get_db_connection
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
                return redirect('/cad_atividades')
            
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
            return redirect('/cad_atividades')

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

    return redirect('/cad_atividades')
