from flask_login import UserMixin

class Professor(UserMixin):
    def __init__(self, prof_id, prof_nome, prof_email, prof_senha):
        self.id = prof_id
        self.prof_nome = prof_nome
        self.prof_email = prof_email
        self.prof_senha = prof_senha


    '''@staticmethod
    def get(user_id):
        from app import get_db_connection
        
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM tb_usuarios WHERE user_id = %s', (user_id,))
            usuario = cursor.fetchone()
            if usuario:
                return User(usuario['user_id'], usuario['user_nome'], usuario['user_email'], usuario['user_senha'], usuario['user_tipo'])
        return None'''
