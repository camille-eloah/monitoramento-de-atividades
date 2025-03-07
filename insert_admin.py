import pymysql
from passlib.context import CryptContext

# Conexão com o banco de dados
def get_db_connection():
    return pymysql.connect(
        host='localhost', 
        user='root', 
        password='',  
        database='db_monitoramento',  
        cursorclass=pymysql.cursors.DictCursor
    )

# Configuração do contexto do Passlib para usar bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def insert_admin():
    # Dados do admin
    admin_nome = "admin"
    admin_email = "admin@gmail.com"
    admin_senha = "123"
    admin_prof_admin = 1 
    
    # Criptografando a senha com passlib (bcrypt)
    hashed_senha = pwd_context.hash(admin_senha)

    # Inserir o admin no banco de dados
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # SQL para inserir o usuário admin
            insert_query = """
                INSERT INTO tb_professores (prof_nome, prof_email, prof_senha, prof_admin)
                VALUES (%s, %s, %s, %s);
            """
            cursor.execute(insert_query, (admin_nome, admin_email, hashed_senha, admin_prof_admin))
            connection.commit()
            print("Usuário admin inserido com sucesso!")
    
    except pymysql.MySQLError as e:
        print(f"Erro ao inserir admin: {e}")
    finally:
        connection.close()

if __name__ == "__main__":
    insert_admin()
