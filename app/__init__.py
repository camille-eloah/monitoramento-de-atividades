from flask import Flask
from flask_login import LoginManager
import mysql.connector
from mysql.connector import Error
import os

DB_NAME = "db_monitoramento"

def create_database():
    """Cria o banco de dados caso ele não exista."""
    try:
        connection = mysql.connector.connect(
            host='127.0.0.1',
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', '')
        )
        cursor = connection.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
        connection.commit()
    except Error as e:
        print(f"Erro ao criar o banco de dados: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def get_db_connection():
    """Garante que o banco existe e retorna uma conexão com ele."""
    create_database()  # Garante que o banco existe antes de tentar conectar
    try:
        connection = mysql.connector.connect(
            host='127.0.0.1',
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=DB_NAME
        )
        return connection
    except Error as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        return None

def check_permissions():
    """Verifica se o usuário tem permissões para criar funções no banco de dados."""
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("SHOW GRANTS FOR CURRENT_USER;")
            grants = cursor.fetchall()

            # Verifica se a permissão CREATE ROUTINE está presente
            if any("CREATE ROUTINE" in grant[0] for grant in grants):
                print("Permissão para criar funções presente.")
            else:
                print("Permissão para criar funções não encontrada.")
        except Error as e:
            print(f"Erro ao verificar permissões: {e}")
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

def initialize_database():
    """Executa o script de criação das tabelas e funções."""
    connection = get_db_connection()
    try:
        with connection.cursor(dictionary=True) as cursor:
            with open("init_db.sql", "r", encoding="utf-8") as f:
                sql_script = f.read()

                # Divide o script em comandos individuais
                statements = [stmt.strip() for stmt in sql_script.split(';') if stmt.strip()]
                
                # Executa cada comando individualmente
                for stmt in statements:
                    try:
                        print(f"Executando: {stmt}")
                        cursor.execute(stmt)
                    except Exception as e:
                        print(f"Erro ao executar o comando: {stmt}\nErro: {e}")
                        continue  # Continue executando os próximos comandos

        connection.commit()
    except Exception as e:
        print(f"Erro ao executar o script SQL: {e}")
    finally:
        connection.close()

    # Cria as funções, procedimentos e triggers separadamente
    create_function_calcular_media()
    create_procedure_registrar_nota()
    create_trigger_verificar_frequencia()
    create_trigger_log_notas()

def create_function_calcular_media():
    """Executa a criação da função calcular_media."""
    connection = get_db_connection()
    try:
        with connection.cursor(dictionary=True) as cursor:
            # Drop the function if it already exists
            drop_function_sql = "DROP FUNCTION IF EXISTS calcular_media;"
            print("Removendo função calcular_media existente (se houver)...")
            cursor.execute(drop_function_sql)

            # Script SQL para criar a função
            create_function_sql = """
            CREATE FUNCTION calcular_media(id_aluno INT, id_disciplina INT)
            RETURNS FLOAT
            DETERMINISTIC
            BEGIN
                DECLARE total_notas FLOAT DEFAULT 0;
                DECLARE total_peso INT DEFAULT 0;
                DECLARE media FLOAT;

                -- Calcula a soma das notas ponderadas e o peso total
                SELECT SUM(a.alunoativ_nota * b.ati_peso), SUM(b.ati_peso)
                INTO total_notas, total_peso
                FROM tb_aluno_atividade a
                JOIN tb_atividades b ON a.alunoativ_ati_id = b.ati_id
                WHERE a.alunoativ_alu_id = id_aluno
                AND b.ati_dis_id = id_disciplina
                AND a.alunoativ_situacao = 'Entregue';

                -- Calcula a média ponderada
                IF total_peso > 0 THEN
                    SET media = total_notas / total_peso;
                ELSE
                    SET media = 0;  -- Caso não haja atividades entregues ou peso, a média é 0
                END IF;

                -- Registra ou atualiza a média na tabela tb_aluno_media
                INSERT INTO tb_aluno_media (media_alu_id, media_dis_id, media_calculada)
                VALUES (id_aluno, id_disciplina, media)
                ON DUPLICATE KEY UPDATE media_calculada = media;  -- Se já existir um registro, atualiza a média

                RETURN media;
            END;
            """
            # Executa a criação da função
            print("Criando função calcular_media...")
            cursor.execute(create_function_sql)
            print("Função calcular_media criada com sucesso!")
        connection.commit()
    except Exception as e:
        print(f"Erro ao criar a função calcular_media: {e}")
    finally:
        connection.close()

def create_procedure_registrar_nota():
    """Executa a criação do procedimento registrar_nota."""
    connection = get_db_connection()
    try:
        with connection.cursor(dictionary=True) as cursor:
            # Drop the procedure if it already exists
            drop_procedure_sql = "DROP PROCEDURE IF EXISTS registrar_nota;"
            print("Removendo procedimento registrar_nota existente (se houver)...")
            cursor.execute(drop_procedure_sql)

            # Script SQL para criar o procedimento
            create_procedure_sql = """
            CREATE PROCEDURE registrar_nota(
                IN id_aluno INT,
                IN id_disciplina INT,
                IN nota FLOAT,
                IN tipo_avaliacao VARCHAR(200),
                IN peso INT
            )
            BEGIN
                DECLARE atividade_id INT;
                DECLARE nota_existente FLOAT;

                -- Verifica se já existe uma atividade para a disciplina com o tipo de avaliação fornecido
                SELECT ati_id
                INTO atividade_id
                FROM tb_atividades
                WHERE ati_dis_id = id_disciplina
                AND ati_tipo = tipo_avaliacao
                LIMIT 1;

                -- Se a atividade não existir, cria uma nova
                IF atividade_id IS NULL THEN
                    -- Insere uma nova atividade com o peso especificado
                    INSERT INTO tb_atividades(ati_dis_id, ati_tipo, ati_peso, ati_descricao, ati_data_entrega)
                    VALUES (id_disciplina, tipo_avaliacao, peso, CONCAT(tipo_avaliacao, ' para ', (SELECT dis_nome FROM tb_disciplinas WHERE dis_id = id_disciplina)), NOW());
                    
                    -- Recupera o id da atividade recém-criada
                    SET atividade_id = LAST_INSERT_ID();
                END IF;

                -- Verifica se o aluno já tem uma nota registrada para essa atividade
                SELECT alunoativ_nota
                INTO nota_existente
                FROM tb_aluno_atividade
                WHERE alunoativ_alu_id = id_aluno
                AND alunoativ_ati_id = atividade_id
                LIMIT 1;

                -- Se a nota já existir, atualiza a nota
                IF nota_existente IS NOT NULL THEN
                    UPDATE tb_aluno_atividade
                    SET alunoativ_nota = nota
                    WHERE alunoativ_alu_id = id_aluno
                    AND alunoativ_ati_id = atividade_id;
                ELSE
                    -- Caso contrário, insere a nota
                    INSERT INTO tb_aluno_atividade(alunoativ_alu_id, alunoativ_ati_id, alunoativ_nota, alunoativ_situacao, alunoativ_data_entrega)
                    VALUES (id_aluno, atividade_id, nota, 'Entregue', NOW());
                END IF;
            END;
            """
            # Executa a criação do procedimento
            print("Criando procedimento registrar_nota...")
            cursor.execute(create_procedure_sql)
            print("Procedimento registrar_nota criado com sucesso!")
        connection.commit()
    except Exception as e:
        print(f"Erro ao criar o procedimento registrar_nota: {e}")
    finally:
        connection.close()

def create_trigger_verificar_frequencia():
    """Executa a criação do trigger verificar_frequencia."""
    connection = get_db_connection()
    try:
        with connection.cursor(dictionary=True) as cursor:
            # Drop the trigger if it already exists
            drop_trigger_sql = "DROP TRIGGER IF EXISTS verificar_frequencia;"
            print("Removendo trigger verificar_frequencia existente (se houver)...")
            cursor.execute(drop_trigger_sql)

            # Script SQL para criar o trigger
            create_trigger_sql = """
            CREATE TRIGGER verificar_frequencia
            BEFORE INSERT ON tb_aluno_media
            FOR EACH ROW
            BEGIN
                DECLARE total_aulas INT;
                DECLARE aulas_presentes INT;
                DECLARE frequencia_percentual FLOAT;

                -- Calcula o total de aulas e o total de frequências presentes do aluno na disciplina
                SELECT COUNT(*) INTO total_aulas
                FROM tb_aulas
                WHERE aul_dis_id = NEW.media_dis_id;  -- Disciplina relacionada ao aluno

                SELECT COUNT(*) INTO aulas_presentes
                FROM tb_aula_frequencia af
                JOIN tb_aulas a ON af.freq_aula_id = a.aul_id
                WHERE af.freq_alu_id = NEW.media_alu_id  -- Aluno relacionado à frequência
                AND af.freq_frequencia = 1
                AND a.aul_dis_id = NEW.media_dis_id;  -- Disciplina relacionada à aula

                -- Calcula o percentual de frequência
                IF total_aulas > 0 THEN
                    SET frequencia_percentual = (aulas_presentes / total_aulas) * 100;
                ELSE
                    SET frequencia_percentual = 0;  -- Se não houver aulas, a frequência é considerada 0
                END IF;

                -- Verifica se a frequência é menor que 75% e impede o cálculo da média
                IF frequencia_percentual < 75 THEN
                    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Frequência insuficiente para calcular a média (menor que 75%)';
                END IF;
            END;
            """
            # Executa a criação do trigger
            print("Criando trigger verificar_frequencia...")
            cursor.execute(create_trigger_sql)
            print("Trigger verificar_frequencia criado com sucesso!")
        connection.commit()
    except Exception as e:
        print(f"Erro ao criar o trigger verificar_frequencia: {e}")
    finally:
        connection.close()

def create_trigger_log_notas():
    """Executa a criação dos triggers para log de notas."""
    connection = get_db_connection()
    try:
        with connection.cursor(dictionary=True) as cursor:
            # Drop the triggers if they already exist
            drop_trigger_insert_sql = "DROP TRIGGER IF EXISTS log_notas;"
            drop_trigger_update_sql = "DROP TRIGGER IF EXISTS log_notas_update;"
            drop_trigger_delete_sql = "DROP TRIGGER IF EXISTS log_notas_delete;"
            print("Removendo triggers de log de notas existentes (se houver)...")
            cursor.execute(drop_trigger_insert_sql)
            cursor.execute(drop_trigger_update_sql)
            cursor.execute(drop_trigger_delete_sql)

            # Script SQL para criar os triggers
            create_trigger_insert_sql = """
            CREATE TRIGGER log_notas
            AFTER INSERT ON tb_aluno_atividade
            FOR EACH ROW
            BEGIN
                -- Registro de inserção de nota
                INSERT INTO logs_notas (operacao, aluno_id, disciplina_id, nota, tipo_avaliacao, peso)
                VALUES ('INSERT', NEW.alunoativ_alu_id, (SELECT ati_dis_id FROM tb_atividades WHERE ati_id = NEW.alunoativ_ati_id), NEW.alunoativ_nota, 
                        (SELECT ati_tipo FROM tb_atividades WHERE ati_id = NEW.alunoativ_ati_id), 
                        (SELECT ati_peso FROM tb_atividades WHERE ati_id = NEW.alunoativ_ati_id));
            END;
            """
            create_trigger_update_sql = """
            CREATE TRIGGER log_notas_update
            AFTER UPDATE ON tb_aluno_atividade
            FOR EACH ROW
            BEGIN
                -- Registro de atualização de nota
                INSERT INTO logs_notas (operacao, aluno_id, disciplina_id, nota, tipo_avaliacao, peso)
                VALUES ('UPDATE', NEW.alunoativ_alu_id, (SELECT ati_dis_id FROM tb_atividades WHERE ati_id = NEW.alunoativ_ati_id), NEW.alunoativ_nota, 
                        (SELECT ati_tipo FROM tb_atividades WHERE ati_id = NEW.alunoativ_ati_id), 
                        (SELECT ati_peso FROM tb_atividades WHERE ati_id = NEW.alunoativ_ati_id));
            END;
            """
            create_trigger_delete_sql = """
            CREATE TRIGGER log_notas_delete
            AFTER DELETE ON tb_aluno_atividade
            FOR EACH ROW
            BEGIN
                -- Registro de exclusão de nota
                INSERT INTO logs_notas (operacao, aluno_id, disciplina_id, nota, tipo_avaliacao, peso)
                VALUES ('DELETE', OLD.alunoativ_alu_id, (SELECT ati_dis_id FROM tb_atividades WHERE ati_id = OLD.alunoativ_ati_id), OLD.alunoativ_nota, 
                        (SELECT ati_tipo FROM tb_atividades WHERE ati_id = OLD.alunoativ_ati_id), 
                        (SELECT ati_peso FROM tb_atividades WHERE ati_id = OLD.alunoativ_ati_id));
            END;
            """
            # Executa a criação dos triggers
            print("Criando triggers de log de notas...")
            cursor.execute(create_trigger_insert_sql)
            cursor.execute(create_trigger_update_sql)
            cursor.execute(create_trigger_delete_sql)
            print("Triggers de log de notas criados com sucesso!")
        connection.commit()
    except Exception as e:
        print(f"Erro ao criar os triggers de log de notas: {e}")
    finally:
        connection.close()

def create_app():
    # Criar a aplicação Flask
    app = Flask(__name__)
    app.secret_key = 'SUPERULTRASEGREDO'  # Idealmente, use uma variável de ambiente

    # Criar e inicializar o banco de dados
    initialize_database()

    # Configuração do Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    from app.models.models import Professor

    @login_manager.user_loader
    def load_user(prof_id):
        return Professor.get(prof_id)

    # Importação e registro dos Blueprints
    from app.controllers import (
        aluno_disciplina, alunos, atividades, aulas, cursos, 
        disciplinas, relatorios, auth, index
    )
    
    app.register_blueprint(aluno_disciplina.bp)
    app.register_blueprint(alunos.bp)
    app.register_blueprint(atividades.bp)
    app.register_blueprint(aulas.bp)
    app.register_blueprint(cursos.bp)
    app.register_blueprint(disciplinas.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(relatorios.bp)
    app.register_blueprint(index.bp)

    return app