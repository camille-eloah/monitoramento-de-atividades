from flask_login import UserMixin

class Professor(UserMixin):
    def __init__(self, prof_id, prof_nome, prof_email, prof_senha, prof_tipo):
        self.id = prof_id
        self.prof_nome = prof_nome
        self.prof_email = prof_email
        self.prof_senha = prof_senha

class Aluno(UserMixin):
    def __init__(self, alu_id, alu_nome, alu_matricula, alu_email, alu_curso , alu_data_nasc):
        self.id = alu_id
        self.alu_nome = alu_nome
        self.alu_matricula = alu_matricula
        self.alu_email = alu_email
        self.alu_curso = alu_curso
        self._data_nasc = alu_data_nasc

class Disciplinas(UserMixin):
    def __init__(self, dis_id, dis_nome,dis_prof_responsavel,dis_carga_hr):
        self.id = dis_id
        self.dis_nome = dis_nome
        self.dis_prof_responsavel = dis_prof_responsavel
        self.dis_carga_hr = dis_carga_hr


class Atividades(UserMixin):
    def __init__(self, ati_id, ati_tipo, ati_descricao, ati_data_entr, ati_peso):
        self.id = ati_id
        self.ati_tipo = ati_tipo
        self.ati_descricao = ati_descricao
        self.ati_data_entr = ati_data_entr
        self.ati_peso = ati_peso

class Frequencias(UserMixin):
    def __init__(self, fre_id, fre_chamada):
        self.id = fre_id
        self.fre_chamada = fre_chamada

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
