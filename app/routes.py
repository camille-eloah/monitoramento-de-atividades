from flask import render_template, request, redirect, url_for, flash
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from app import app, get_db_connection
from werkzeug.security import generate_password_hash, check_password_hash

from pymysql.err import IntegrityError

@app.route('/')
def index():
    return render_template('index.html')

def executar_query(query, params=None):
    connection = get_db_connection()
    try: 
        with connection.cursor() as cursor: 
            cursor.execute(query, params)
            connection.commit()
    finally: 
        connection.close()

# Cadastrar aluno
@app.route('/cad_aluno', methods=['POST', 'GET'])
def cad_aluno():
    connection = get_db_connection()

    # Busca os alunos para exibir na página
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM tb_alunos")
        alunos = cursor.fetchall()

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
    return render_template('alunos/cad_aluno.html', alunos=alunos)

# Editar aluno
@app.route('/edit_aluno/<int:alu_matricula>', methods=['POST', 'GET']) 
def edit_aluno(alu_matricula):
    connection = get_db_connection()

    with connection.cursor() as cursor:
            cursor.execute("""
            SELECT * from tb_alunos WHERE alu_matricula = "%s"
            """, (alu_matricula,))
            aluno = cursor.fetchone()
    
    if request.method == 'POST':
        novo_nome = request.form['nome']
        nova_matricula = request.form.get('matricula')
        novo_email = request.form['email']  
        novo_curso = request.form['curso']
        nova_data_nasc = request.form['data_nasc']

        query = """
        UPDATE tb_alunos 
        SET alu_nome = %s, alu_matricula = %s, alu_email = %s, alu_curso = %s, alu_data_nasc = %s
        WHERE alu_matricula = %s
        """
        executar_query(query, (novo_nome, nova_matricula, novo_email, novo_curso, nova_data_nasc, alu_matricula))

        return redirect('/cad_aluno')

    connection.close()

    return render_template('alunos/edit_aluno.html', aluno=aluno)

# Cadastrar disciplina
@app.route('/cad_disciplinas', methods=['POST', 'GET'])
def cad_disciplinas():
    connection = get_db_connection()
    disciplinas = []

    if request.method == "POST":
        nome = request.form['nome']
        prof_responsavel = request.form['prof_responsavel']
        carga_hr = request.form['carga_hr']
        
        query = """
        INSERT INTO tb_disciplinas (dis_nome, dis_prof_responsavel, dis_carga_hr)
        VALUES (%s, %s, %s)
        """
        try:
            executar_query(query, (nome, prof_responsavel, carga_hr))
        except Exception as e:
            flash(f"Erro ao cadastrar disciplina: {e}", category="error")

    # Realiza a consulta novamente para obter a lista atualizada
    with connection.cursor() as cursor:
        cursor.execute("""
        SELECT * FROM tb_disciplinas
        """)
        disciplinas = cursor.fetchall()

    connection.close()

    return render_template('disciplinas/cad_disciplinas.html', disciplinas=disciplinas)


# Editar disciplina
@app.route('/edit_disciplinas/<int:dis_id>', methods=['POST', 'GET']) 
def edit_disciplinas(dis_id):
    connection = get_db_connection()

    with connection.cursor() as cursor:
            cursor.execute("""
            SELECT * from tb_disciplinas WHERE dis_id = "%s"
            """, (dis_id,))
            disciplina = cursor.fetchone()
    
    if request.method == 'POST':
        novo_nome = request.form['nome']
        nova_prof_responsavel = request.form.get('prof_responsavel')
        novo_carga_hr = request.form['carga_hr']  
    
        query = """
        UPDATE tb_disciplinas 
        SET dis_nome = %s, dis_prof_responsavel = %s, dis_carga_hr= %s
        WHERE dis_id = %s
        """
        executar_query(query, (novo_nome, nova_prof_responsavel, novo_carga_hr, dis_id))

        return redirect('/cad_disciplinas')

    connection.close()

    return render_template('disciplinas/edit_disciplina.html', disciplina = disciplina)

# Cadastrar atividades
@app.route('/cad_atividades', methods=['POST', 'GET'])
def cad_atividades():
    connection = get_db_connection()
    atividades = []

    # Selecionar atividades existentes
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM tb_atividades")
        atividades = cursor.fetchall()

    if request.method == "POST":
        tipo = request.form['tipo']
        descricao = request.form['descricao']
        data_entr = request.form['data_entr']
        peso = request.form['peso']

        query = """
        INSERT INTO tb_atividades (ati_tipo, ati_descricao, ati_data_entr, ati_peso)
        VALUES (%s, %s, %s, %s)
        """
        try:
            executar_query(query, (tipo, descricao, data_entr, peso))
        except IntegrityError as e:
            if "Duplicate entry" in str(e):
                mensagem_erro = "Erro: Atividade duplicada ou já cadastrada."
            else:
                mensagem_erro = "Erro ao cadastrar a atividade. Tente novamente mais tarde."
            
            connection.close()
            return render_template('atividades/cad_atividades.html', atividades=atividades, mensagem_erro=mensagem_erro)

    connection.close()
    return render_template('atividades/cad_atividades.html', atividades=atividades)


# Editar atividades
@app.route('/edit_atividade/<int:ati_id>', methods=['POST', 'GET'])
def edit_atividades(ati_id):
    connection = get_db_connection()

    # Selecionar atividade específica
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM tb_atividades WHERE ati_id = %s", (ati_id,))
        atividade = cursor.fetchone()

    if request.method == 'POST':
        novo_tipo = request.form['tipo']
        nova_descricao = request.form['descricao']
        nova_data_entr = request.form['data_entr']
        novo_peso = request.form['peso']

        query = """
        UPDATE tb_atividades 
        SET ati_tipo = %s, ati_descricao = %s, ati_data_entr = %s, ati_peso = %s
        WHERE ati_id = %s
        """
        executar_query(query, (novo_tipo, nova_descricao, nova_data_entr, novo_peso, ati_id))

        return redirect('/cad_atividades')

    connection.close()
    return render_template('atividades/edit_atividades.html', atividade=atividade)

# Cadastro de aulas
@app.route('/cad_aulas', methods=['POST', 'GET'])
def cad_aulas():
    connection = get_db_connection()
    aulas = []

    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM tb_aulas")
        aulas = cursor.fetchall()

    if request.method == "POST":
        aul_descricao = request.form['descricao']
        aul_data = request.form['data']

        query = """
        INSERT INTO tb_aulas (aul_descricao, aul_data)
        VALUES (%s, %s)
        """
        try:
            executar_query(query, (aul_descricao, aul_data))
        except IntegrityError as e:
            if "Duplicate entry" in str(e):
                mensagem_erro = "Erro: Aula duplicada ou já cadastrada."
            else:
                mensagem_erro = "Erro ao cadastrar a aula. Tente novamente mais tarde."
            
            connection.close()
            return render_template('aulas/cad_aulas.html', aulas=aulas, mensagem_erro=mensagem_erro)

    connection.close()
    return render_template('aulas/cad_aulas.html', aulas=aulas )

@app.route('/relatorios')
def relatorios():
    return render_template('relatorios/relatorios.html')
