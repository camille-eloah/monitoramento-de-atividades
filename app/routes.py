from flask import render_template, request, redirect
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

@app.route('/cad_aluno', methods=['POST', 'GET'])
def cad_aluno():
    connection = get_db_connection()
    alunos = []

    with connection.cursor() as cursor:
        cursor.execute("""
        SELECT * FROM tb_alunos
        """)
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
        except IntegrityError as e:
            if "Duplicate entry" in str(e):
                mensagem_erro = "Erro: Matrícula ou e-mail já cadastrados no sistema."
            else:
                mensagem_erro = "Erro ao cadastrar aluno. Tente novamente mais tarde."
            
            connection.close()
            return render_template('alunos/cad_aluno.html', alunos=alunos, mensagem_erro=mensagem_erro)

    connection.close()
    return render_template('alunos/cad_aluno.html', alunos=alunos)


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

@app.route('/cad_disciplinas', methods=['POST', 'GET'])
def cad_disciplinas():
    connection = get_db_connection()

    if request.method== "POST":
        nome = request.form['nome']
        prof_responsavel = request.form['prof_responsavel']
        carga_hr = request.form['carga_hr']
        
        query = """
        INSERT INTO tb_disciplinas (dis_nome, dis_prof_responsavel, dis_carga_hr)
        VALUES (%s, %s, %s)
        """
        executar_query(query, (nome, prof_responsavel, carga_hr))

    return render_template('disciplinas/cad_disciplinas.html')

#Editar Disciplinas 
@app.route('/edit_disciplinas/<string:dis_nome>', methods=['POST', 'GET']) 
def edit_disciplinas(dis_nome):
    connection = get_db_connection()

    with connection.cursor() as cursor:
            cursor.execute("""
            SELECT * from tb_disciplinas WHERE dis_nome = "%s"
            """, (dis_nome,))
            disciplina = cursor.fetchone()
    
    if request.method == 'POST':
        novo_nome = request.form['nome']
        nova_prof_responsavel = request.form.get['prof_responsavel']
        novo_carga_hr = request.form['carga_hr']  
    
        query = """
        UPDATE tb_disciplinas 
        SET dis_nome = %s, dis_prof_responsavel = %s, d s_carga_hr= %s
        WHERE dis_nome = %s
        """
        executar_query(query, (novo_nome, nova_prof_responsavel, novo_carga_hr))

        return redirect('/cad_disciplinas')

    connection.close()

    return render_template('disciplinas/edit_disciplina.html', disciplina = disciplina)


@app.route('/cad_atividades', methods=['POST', 'GET'])
def cad_atividades():
    if request.method== "POST":
        tipo = request.form['tipo']
        descricao = request.form['descricao']
        data_entr = request.form['data_entr']
        peso = request.form['peso']

    return render_template('atividades/cad_atividades.html')

@app.route('/gestao_freq', methods=['POST', 'GET'])
def gestao_freq():
    if request.method== "POST":
        chamada = request.form['chamada']

    return render_template('frequencia/gestao_freq.html')

@app.route('/relatorios')
def relatorios():
    return render_template('relatorios/relatorios.html')
