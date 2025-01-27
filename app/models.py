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

class AulaFrequencia:
    def __init__(self, freq_id, aul_id, aluno_id, presenca):
        self.freq_id = freq_id
        self.freq_aul_id = aul_id
        self.freq_alu_id = aluno_id
        self.freq_frequencia = presenca

    @staticmethod
    def salvar_frequencia(aul_id, frequencias):
        """
        Salva a frequência dos alunos para uma aula no banco de dados.
        
        :param aul_id: ID da aula
        :param frequencias: Lista de dicionários com aluno_id e presença
        """
        from app import get_db_connection

        connection = get_db_connection()
        with connection.cursor() as cursor:
            for freq in frequencias:
                cursor.execute(
                    'INSERT INTO tb_aula_frequencia (freq_aula_id, freq_alu_id, freq_frequencia) VALUES (%s, %s, %s)',
                    (aul_id, freq['freq_alu_id'], freq['freq_frequencia'])
                )
        connection.commit()

    @staticmethod
    def listar_frequencia(aul_id):
        """
        Lista as frequências de uma aula específica.
        
        :param aul_id: ID da aula
        :return: Lista de frequências (dicionários com aluno_id e presença)
        """
        from app import get_db_connection

        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM tb_aula_frequencia WHERE freq_aul_id = %s', (aul_id,))
            frequencias = cursor.fetchall()
            return frequencias
