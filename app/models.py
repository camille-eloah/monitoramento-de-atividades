from flask_login import UserMixin

class Professor(UserMixin):
    def __init__(self, prof_id, prof_nome, prof_email, prof_senha):
        self.id = prof_id
        self.prof_nome = prof_nome
        self.prof_email = prof_email
        self.prof_senha = prof_senha


    @staticmethod
    def get(prof_id):
        from app import get_db_connection
        
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM tb_professores WHERE prof_id = %s', (prof_id,))
            usuario = cursor.fetchone()
            if usuario:
                return Professor(usuario['prof_id'], usuario['prof_nome'], usuario['prof_email'], usuario['prof_senha'])
        return None