from flask import render_template, request, redirect, url_for, flash
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from app import app, get_db_connection
from werkzeug.security import generate_password_hash, check_password_hash

import pymysql
from pymysql.err import IntegrityError 

from app.models import Professor

from passlib.context import CryptContext

# Configuração do contexto do Passlib para usar bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Cadastro (usuário)
@app.route('/cadastro', methods=['POST', 'GET'])
def cadastro():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['pass']
        confirmar_senha = request.form['confirm_pass']

        # Verificar se as senhas coincidem
        if senha != confirmar_senha:
            flash("As senhas não coincidem. Por favor, tente novamente.", category="error")
            return redirect(url_for('cadastro'))

        # Gerar a senha criptografada com passlib
        hashed_senha = pwd_context.hash(senha)
        
        connection = get_db_connection()
        try:
            # Inserir o novo usuário no banco de dados
            with connection.cursor() as cursor:
                cursor.execute('INSERT INTO tb_professores (prof_nome, prof_email, prof_senha) VALUES (%s, %s, %s)', 
                               (nome, email, hashed_senha))
                connection.commit()

            # Mensagem de sucesso
            flash('Usuário cadastrado com sucesso!', 'success')
            return redirect('login')  # Redireciona para o login

        except IntegrityError as e:
            # Tratamento de erro de duplicidade (e-mail ou nome já existente)
            if e.args[0] == 1062:
                flash("Já existe um usuário com esse nome ou e-mail.", 'error')
            else:
                flash("Erro ao cadastrar o usuário. Tente novamente mais tarde.", 'error')

        finally:
            connection.close()

    return render_template('auth/cadastro.html')  # Renderiza o formulário de cadastro


# Login
@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        nome = request.form['nome']
        senha = request.form['senha'] 

        # Conectar ao banco de dados
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Verifique se está pegando o usuário correto
            cursor.execute('SELECT * FROM tb_professores WHERE prof_nome = %s', (nome,))
            usuario = cursor.fetchone()

            # Depuração: Verifique o que está sendo recuperado
            print("Usuário encontrado:", usuario)

            if usuario:
                # Depuração: Imprime a senha recuperada do banco e a senha informada
                print("Nome do Usuário:", usuario['prof_nome'])
                print("Senha informada:", senha)
                print("Senha armazenada (hash):", usuario['prof_senha'])

                # Usando passlib para verificar se a senha informada corresponde ao hash armazenado
                if pwd_context.verify(senha, usuario['prof_senha']):
                    # Se a senha estiver correta
                    professor = Professor(usuario['prof_id'], usuario['prof_nome'], usuario['prof_email'], usuario['prof_senha'])
                    login_user(professor)
                    flash('Login realizado com sucesso!', 'success')
                    return redirect('/')
                else:
                    flash('Nome de usuário ou senha inválidos.', 'error')
            else:
                flash('Nome de usuário ou senha inválidos.', 'error')

        connection.close()

    return render_template('auth/login.html')  # Renderiza o template de login

# Logout
@app.route('/logout')
@login_required
def logout():
    logout_user() 
    flash('Você foi desconectado com sucesso.', 'success')
    return redirect('/index')

@app.route('/index')
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

        cursor.execute('SELECT * FROM tb_cursos')
        cursos = cursor.fetchall()

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
    return render_template('alunos/cad_aluno.html', alunos=alunos, cursos=cursos)

# Editar aluno
@app.route('/edit_aluno/<int:alu_matricula>', methods=['POST', 'GET'])
def edit_aluno(alu_matricula):
    connection = get_db_connection()
    aluno = None
    cursos = []

    try:
        # Selecionar aluno específico
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM tb_alunos WHERE alu_matricula = %s", (alu_matricula,))
            aluno = cursor.fetchone()

        # Selecionar cursos existentes
        with connection.cursor() as cursor:
            cursor.execute("SELECT cur_id, cur_nome FROM tb_cursos")  # Ajuste para a tabela correta
            cursos = cursor.fetchall()

        if not aluno:
            flash("Aluno não encontrado.", "warning")
            return redirect('/cad_aluno')

        if request.method == 'POST':
            novo_nome = request.form['nome']
            nova_matricula = request.form.get('matricula')
            novo_email = request.form['email']
            novo_curso = request.form['curso']  # ID do curso
            nova_data_nasc = request.form['data_nasc']

            # Validação simples dos campos
            if not all([novo_nome, nova_matricula, novo_email, novo_curso, nova_data_nasc]):
                flash("Por favor, preencha todos os campos corretamente.", "warning")
                return render_template('alunos/edit_aluno.html', aluno=aluno, cursos=cursos)

            query = """
            UPDATE tb_alunos 
            SET alu_nome = %s, alu_matricula = %s, alu_email = %s, alu_curso = %s, alu_data_nasc = %s
            WHERE alu_matricula = %s
            """
            with connection.cursor() as cursor:
                cursor.execute(query, (novo_nome, nova_matricula, novo_email, novo_curso, nova_data_nasc, alu_matricula))
            connection.commit()
            flash("Aluno atualizado com sucesso!", "success")
            return redirect('/cad_aluno')

    except Exception as e:
        flash(f"Erro inesperado: {str(e)}", "danger")
    finally:
        connection.close()

    return render_template('alunos/edit_aluno.html', aluno=aluno, cursos=cursos)

# Remover aluno
@app.route('/delete_aluno/<int:alu_matricula>', methods=['POST'])
def delete_aluno(alu_matricula):
    connection = get_db_connection()
    try:
        query = "DELETE FROM tb_alunos WHERE alu_matricula = %s"
        executar_query(query, (alu_matricula,))
        flash("Aluno removido com sucesso!", "success")
    except Exception as e:
        flash(f"Erro ao remover aluno: {e}", "danger")
    finally:
        connection.close()
    
    return redirect(url_for('cad_aluno'))

# Cadastrar disciplina
@app.route('/cad_disciplinas', methods=['POST', 'GET'])
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
@app.route('/edit_disciplinas/<int:dis_id>', methods=['POST', 'GET']) 
def edit_disciplinas(dis_id):
    connection = get_db_connection()

    # Obter detalhes da disciplina
    with connection.cursor() as cursor:
        cursor.execute("""
        SELECT * FROM tb_disciplinas WHERE dis_id = %s
        """, (dis_id,))
        disciplina = cursor.fetchone()

        cursor.execute("""
        SELECT * FROM tb_disciplinas WHERE dis_id = %s
        """, (dis_id,))
        disciplinas = cursor.fetchall()

        cursor.execute("""
        SELECT * FROM tb_professores
        """)
        professores = cursor.fetchall()

        # Obter IDs dos cursos associados à disciplina
        cursor.execute("""
        SELECT cd_cur_id FROM tb_cursos_disciplinas WHERE cd_dis_id = %s
        """, (dis_id,))
        cursos_associados_ids = [row['cd_cur_id'] for row in cursor.fetchall()]

        # Obter todos os cursos
        cursor.execute("""
        SELECT * FROM tb_cursos
        """)
        cursos = cursor.fetchall()

        # Obter nomes dos cursos associados
        cursos_associados = [
            curso for curso in cursos if curso['cur_id'] in cursos_associados_ids
        ]

    if request.method == 'POST':
        novo_nome = request.form['nome']
        nova_prof_responsavel = request.form.get('prof_responsavel')
        nova_carga_hr = request.form['carga_hr']
        novos_cursos_ids = request.form.getlist('curso_id')  # Cursos selecionados no formulário

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

        return redirect('/cad_disciplinas')

    connection.close()

    return render_template(
        'disciplinas/edit_disciplina.html',
        disciplinas=disciplinas,
        disciplina=disciplina,
        cursos=cursos,
        cursos_associados_ids=cursos_associados_ids,
        cursos_associados=cursos_associados,
        professores=professores
    )


# Remover disciplina
@app.route('/delete_disciplina/<int:dis_id>', methods=['POST'])
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

    return redirect(url_for('cad_disciplinas'))

# Adicionar alunos na disciplina
@app.route('/adicionar_alunos_disciplina/<int:dis_id>', methods=['GET', 'POST'])
def adicionar_alunos_disciplina(dis_id):
    connection = get_db_connection()
    alunos = []
    disciplina = None

    # Busca todos os alunos
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM tb_alunos")
        alunos = cursor.fetchall()

        # Busca a disciplina
        cursor.execute("SELECT * FROM tb_disciplinas WHERE dis_id = %s", (dis_id,))
        disciplina = cursor.fetchone()

    if request.method == "POST":
        # Recebe os alunos selecionados para associar
        alunos_selecionados = request.form.getlist('alunos')  # Lista de IDs dos alunos selecionados

        try:
            with connection.cursor() as cursor:
                for aluno_id in alunos_selecionados:
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

    connection.close()
    return render_template('disciplinas/adicionar_aluno_disciplina.html', alunos=alunos, disciplina=disciplina)


# Cadastrar atividades
@app.route('/cad_atividades', methods=['POST', 'GET'])
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

                with connection.cursor() as cursor:
                    cursor.execute("""
                    SELECT a.ati_id, a.ati_tipo, a.ati_descricao, a.ati_data_entrega, a.ati_peso, d.dis_nome
                    FROM tb_atividades a
                    INNER JOIN tb_disciplinas d ON a.ati_dis_id = d.dis_id
                    """)
                    
                    atividades = cursor.fetchall()

            except IntegrityError as e:
                if "Duplicate entry" in str(e):
                    flash("Erro: Atividade duplicada ou já cadastrada.", "danger")
                else:
                    flash(f"Erro ao cadastrar a atividade: {str(e)}", "danger")
            except Exception as e:
                flash(f"Erro inesperado: {str(e)}", "danger")

        # Após cadastro ou ao carregar a página, buscar atividades novamente
        with connection.cursor() as cursor:
            cursor.execute("""
            SELECT a.ati_id, a.ati_tipo, a.ati_descricao, a.ati_data_entrega, a.ati_peso, d.dis_nome
            FROM tb_atividades a
            INNER JOIN tb_disciplinas d ON a.ati_dis_id = d.dis_id
            """)
            atividades = cursor.fetchall()

    finally:
        connection.close()

    return render_template(
        'atividades/cad_atividades.html', atividades=atividades, disciplinas=disciplinas
    )

# Editar atividades
@app.route('/edit_atividade/<int:ati_id>', methods=['POST', 'GET'])
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
@app.route('/delete_atividade/<int:ati_id>', methods=['POST'])
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

# Cadastro de aulas
@app.route('/cad_aulas', methods=['POST', 'GET'])
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

                # Inicializar frequência com "1" para cada aluno
                query_frequencia = """
                INSERT INTO tb_aula_frequencia (freq_aula_id, freq_alu_id, freq_frequencia)
                VALUES (%s, %s, %s)
                """
                for aluno in alunos:
                    cursor.execute(query_frequencia, (aula_id, aluno['alu_id'], 1))

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
@app.route('/edit_aula/<int:aul_id>', methods=['POST', 'GET'])
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
        SET aul_descricao = %s, aul_data = %s,
        WHERE aul_id = %s
        """
        executar_query(query, (nova_descricao, nova_data, aul_id))

        return redirect('/cad_aulas')

    connection.close()
    return render_template('aulas/edit_aula.html', aula=aula, professores=professores, disciplinas=disciplinas)

#Deletar aulas
@app.route('/delete_aula/<int:aul_id>', methods=['POST'])
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


#Cadastrar cursos
@app.route('/cad_curso', methods=['POST', 'GET'])
def cad_curso():
    connection = get_db_connection()
    cursos = []

    # Exibe os cursos já cadastrados
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM tb_cursos")
        cursos = cursor.fetchall()

    if request.method == "POST":
        cur_nome = request.form['nome']
        cur_descricao = request.form['descricao']

        query = """
        INSERT INTO tb_cursos (cur_nome, cur_descricao)
        VALUES (%s, %s)
        """
        try:
            executar_query(query, (cur_nome, cur_descricao))
            flash("Curso cadastrados", "success")
        except IntegrityError as e:
            if "Duplicate entry" in str(e):
                flash("Erro: Curso duplicado ou já cadastrado.", "error")
            else:
                flash("Erro ao cadastrar o curso. Tente novamente mais tarde.", "error")
        
        return redirect(url_for('cad_curso'))

    connection.close()

    return render_template('cursos/cad_curso.html', cursos=cursos)

# Editar cursos
@app.route('/edit_curso/<int:cur_id>', methods=['POST', 'GET'])
def edit_curso(cur_id):
    connection = get_db_connection()

    # Selecionar atividade específica
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM tb_cursos WHERE cur_id = %s", (cur_id,))
        curso = cursor.fetchone()

    if request.method == 'POST':
        novo_nome = request.form['nome']
        nova_descricao = request.form['descricao']

        query = """
        UPDATE tb_cursos 
        SET cur_nome = %s, cur_descricao = %s
        WHERE cur_id = %s
        """
        executar_query(query, (novo_nome, nova_descricao, cur_id))

        return redirect('/cad_curso')

    connection.close()
    return render_template('cursos/edit_curso.html', curso=curso)

#Deletar Cursos
@app.route('/delete_curso/<int:cur_id>', methods=['POST'])
def delete_curso(cur_id):
    connection = get_db_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM tb_cursos WHERE cur_id = %s", (cur_id,))
            connection.commit()
            flash("Curso deletado com sucesso!", "success")
    except Exception as e:
        connection.rollback()
        flash(f"Erro ao deletar curso: {e}", "error")
    finally:
        connection.close()

    return redirect('/cad_curso')

@app.route('/add_frequencia/<int:aul_id>', methods=['GET', 'POST'])
def add_frequencia(aul_id):
    connection = get_db_connection()
    if request.method == "POST":
        frequencias = request.form.getlist('frequencias')  # Frequências enviadas do formulário
        try:
            with connection.cursor() as cursor:
                # Atualiza a frequência de cada aluno
                for alu_id, frequencia in request.form.getlist('frequencias'):
                    cursor.execute("""
                    UPDATE tb_aula_frequencia
                    SET freq_frequencia = %s
                    WHERE freq_aula_id = %s AND freq_alu_id = %s
                    """, (int(frequencia), aul_id, int(alu_id)))

            connection.commit()
            flash("Frequência salva com sucesso!", "success")
        except Exception as e:
            connection.rollback()
            flash(f"Erro ao salvar frequência: {str(e)}", "error")

        return redirect(url_for('add_frequencia', aul_id=aul_id))

    # Busca alunos e frequências da aula
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT a.alu_id, a.alu_nome, IFNULL(f.freq_frequencia, 1) AS freq_frequencia
            FROM tb_alunos a
            LEFT JOIN tb_aula_frequencia f ON a.alu_id = f.freq_alu_id AND f.freq_aula_id = %s
            WHERE a.alu_id IN (SELECT ad_alu_id FROM tb_alunos_disciplinas WHERE ad_dis_id = (SELECT aul_dis_id FROM tb_aulas WHERE aul_id = %s))
        """, (aul_id, aul_id))

        alunos_frequencia = cursor.fetchall()
        print("alunos_frequencia:", alunos_frequencia)

    connection.close()
    return render_template('aulas/add_frequencia.html', alunos=alunos_frequencia, aul_id=aul_id)


@app.route('/relatorios')
def relatorios():
    return render_template('relatorios/relatorios.html')
