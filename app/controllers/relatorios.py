from flask import Flask , Blueprint, render_template, request, redirect, url_for, flash
from app.controllers.auth import executar_query
from flask_login import LoginManager, current_user, login_required
from app import get_db_connection
import pymysql
from pymysql.err import IntegrityError

bp = Blueprint('relatorios', __name__, url_prefix='/relatorios')

@bp.route('/')
def index():
    return redirect(url_for('relatorios.relatorios'))

@bp.route('/relatorios')
@login_required
def relatorios():
    connection = get_db_connection()

    # Busca os dados necessários para os relatórios
    with connection.cursor(dictionary=True) as cursor:
        # Consulta os alunos
        cursor.execute("SELECT * FROM tb_alunos")
        alunos = cursor.fetchall()

        # Consulta a frequência nas aulas
        cursor.execute('SELECT * FROM tb_aula_frequencia')
        aula_frequencia = cursor.fetchall()

        # Consulta as atividades
        cursor.execute('SELECT * FROM tb_atividades')
        atividades = cursor.fetchall()

        # Consulta o relacionamento aluno-atividade
        cursor.execute('SELECT * FROM tb_aluno_atividade')
        alu_atividade = cursor.fetchall()

        # Consultar o relatório de faltas por aluno
        cursor.execute("""
            SELECT
                a.alu_nome AS Aluno,
                COUNT(af.freq_aula_id) AS Aulas,
                SUM(CASE WHEN af.freq_frequencia = 0 THEN 1 ELSE 0 END) AS Faltas
            FROM
                tb_aula_frequencia af
            JOIN
                tb_alunos a ON af.freq_alu_id = a.alu_id
            JOIN
                tb_aulas au ON af.freq_aula_id = au.aul_id
            GROUP BY
                a.alu_nome
            ORDER BY
                a.alu_nome;
        """)
        alunos_faltas = cursor.fetchall()

        # Consultar o relatório de médias ponderadas por aluno e disciplina
        cursor.execute("""
            SELECT 
                a.alu_nome AS Aluno, 
                d.dis_nome AS Disciplina, 
                SUM(aa.alunoativ_nota * atv.ati_peso) / SUM(atv.ati_peso) AS Media
            FROM 
                tb_aluno_atividade aa
            JOIN 
                tb_atividades atv ON aa.alunoativ_ati_id = atv.ati_id
            JOIN 
                tb_disciplinas d ON atv.ati_dis_id = d.dis_id
            JOIN 
                tb_alunos a ON aa.alunoativ_alu_id = a.alu_id
            WHERE 
                aa.alunoativ_situacao = 'Entregue'
            GROUP BY 
                a.alu_id, d.dis_id
            ORDER BY 
                a.alu_nome, d.dis_nome;
        """)
        medias_ponderadas = cursor.fetchall()

        # Organizar os dados de médias ponderadas por aluno e disciplina
        medias_por_aluno_e_disciplina = {}
        for media in medias_ponderadas:
            disciplina = media['Disciplina']
            aluno = media['Aluno']
            if disciplina not in medias_por_aluno_e_disciplina:
                medias_por_aluno_e_disciplina[disciplina] = {}
            medias_por_aluno_e_disciplina[disciplina][aluno] = round(media['Media'], 2)

        # Calcular percentual de frequência por aluno e filtrar os abaixo de 75%
        alunos_baixa_frequencia = []
        for aluno in alunos_faltas:
            aulas = aluno['Aulas']
            faltas = aluno['Faltas']
            if aulas > 0:
                frequencia = ((aulas - faltas) / aulas) * 100  # Calcular percentual de frequência
                if frequencia < 75:  # Filtrar alunos com frequência abaixo de 75%
                    aluno['Percentual'] = frequencia
                    alunos_baixa_frequencia.append(aluno)

        # Consultar relatório de trabalhos entregues, divididos por aluno e disciplina
        cursor.execute("""
            SELECT 
                d.dis_nome AS disciplina,
                a.alu_nome AS aluno,
                t.ati_descricao AS atividade,
                aa.alunoativ_situacao AS situacao,
                aa.alunoativ_nota AS nota,
                aa.alunoativ_data_entrega AS data_entrega,
                t.ati_data_entrega AS data_limite_entrega
            FROM 
                tb_aluno_atividade aa
            JOIN 
                tb_atividades t ON aa.alunoativ_ati_id = t.ati_id
            JOIN 
                tb_disciplinas d ON t.ati_dis_id = d.dis_id
            JOIN 
                tb_alunos a ON aa.alunoativ_alu_id = a.alu_id
            WHERE 
                aa.alunoativ_situacao = 'Entregue'
            ORDER BY 
                d.dis_nome, a.alu_nome, t.ati_descricao
        """)
        trabalhos_entregues = cursor.fetchall()

        # Organizar os dados em formato estruturado por disciplina e aluno
        trabalhos_por_aluno_e_disciplina = {}
        for trabalho in trabalhos_entregues:
            disciplina = trabalho['disciplina']
            aluno = trabalho['aluno']
            if disciplina not in trabalhos_por_aluno_e_disciplina:
                trabalhos_por_aluno_e_disciplina[disciplina] = {}
            if aluno not in trabalhos_por_aluno_e_disciplina[disciplina]:
                trabalhos_por_aluno_e_disciplina[disciplina][aluno] = []
            trabalhos_por_aluno_e_disciplina[disciplina][aluno].append({
                'atividade': trabalho['atividade'],
                'situacao': trabalho['situacao'],
                'nota': trabalho['nota'],
                'data_entrega': trabalho['data_entrega'].strftime('%d/%m/%Y %H:%M') if trabalho['data_entrega'] else 'Não informado',
                'data_limite_entrega': trabalho['data_limite_entrega'].strftime('%d/%m/%Y %H:%M') if trabalho['data_limite_entrega'] else 'Não informado'
            })

        # Consultar trabalhos entregues fora do prazo
        cursor.execute("""
            SELECT 
                d.dis_nome AS disciplina,
                a.alu_nome AS aluno,
                t.ati_descricao AS atividade,
                aa.alunoativ_situacao AS situacao,
                aa.alunoativ_nota AS nota,
                aa.alunoativ_data_entrega AS data_entrega,
                t.ati_data_entrega AS data_limite_entrega
            FROM 
                tb_aluno_atividade aa
            JOIN 
                tb_atividades t ON aa.alunoativ_ati_id = t.ati_id
            JOIN 
                tb_disciplinas d ON t.ati_dis_id = d.dis_id
            JOIN 
                tb_alunos a ON aa.alunoativ_alu_id = a.alu_id
            WHERE 
                aa.alunoativ_situacao = 'Entregue'
                AND aa.alunoativ_data_entrega > t.ati_data_entrega
            ORDER BY 
                d.dis_nome, a.alu_nome, t.ati_descricao
        """)
        trabalhos_fora_prazo = cursor.fetchall()

    # Organizar os dados de trabalhos fora do prazo
    trabalhos_fora_prazo_por_aluno_e_disciplina = {}
    for trabalho in trabalhos_fora_prazo:
        disciplina = trabalho['disciplina']
        aluno = trabalho['aluno']
        if disciplina not in trabalhos_fora_prazo_por_aluno_e_disciplina:
            trabalhos_fora_prazo_por_aluno_e_disciplina[disciplina] = {}
        if aluno not in trabalhos_fora_prazo_por_aluno_e_disciplina[disciplina]:
            trabalhos_fora_prazo_por_aluno_e_disciplina[disciplina][aluno] = []
        trabalhos_fora_prazo_por_aluno_e_disciplina[disciplina][aluno].append({
            'atividade': trabalho['atividade'],
            'situacao': trabalho['situacao'],
            'nota': trabalho['nota'],
            'data_entrega': trabalho['data_entrega'].strftime('%d/%m/%Y %H:%M') if trabalho['data_entrega'] else 'Não informado',
            'data_limite_entrega': trabalho['data_limite_entrega'].strftime('%d/%m/%Y %H:%M') if trabalho['data_limite_entrega'] else 'Não informado'
        })

    # Renderiza a página de relatórios com todos os dados
    return render_template(
        'relatorios/relatorios.html',
        alunos=alunos,
        aula_frequencia=aula_frequencia,
        atividades=atividades,
        alu_atividade=alu_atividade,
        alunos_faltas=alunos_faltas,
        alunos_baixa_frequencia=alunos_baixa_frequencia,
        trabalhos_por_aluno_e_disciplina=trabalhos_por_aluno_e_disciplina,
        medias_por_aluno_e_disciplina=medias_por_aluno_e_disciplina,
        trabalhos_fora_prazo_por_aluno_e_disciplina=trabalhos_fora_prazo_por_aluno_e_disciplina
    )

from flask import Flask , Blueprint, render_template, request, redirect, url_for, flash
from app.controllers.auth import executar_query
from flask_login import LoginManager, current_user, login_required
from app import get_db_connection
import pymysql
from pymysql.err import IntegrityError

bp = Blueprint('relatorios', __name__, url_prefix='/relatorios')

@bp.route('/')
def index():
    return redirect(url_for('relatorios.relatorios'))

@bp.route('/relatorios')
@login_required
def relatorios():
    connection = get_db_connection()

    # Busca os dados necessários para os relatórios
    with connection.cursor(dictionary=True) as cursor:
        # Consulta os alunos
        cursor.execute("SELECT * FROM tb_alunos")
        alunos = cursor.fetchall()

        # Consulta a frequência nas aulas
        cursor.execute('SELECT * FROM tb_aula_frequencia')
        aula_frequencia = cursor.fetchall()

        # Consulta as atividades
        cursor.execute('SELECT * FROM tb_atividades')
        atividades = cursor.fetchall()

        # Consulta o relacionamento aluno-atividade
        cursor.execute('SELECT * FROM tb_aluno_atividade')
        alu_atividade = cursor.fetchall()

        # Consultar o relatório de faltas por aluno
        cursor.execute("""
            SELECT
                a.alu_nome AS Aluno,
                COUNT(af.freq_aula_id) AS Aulas,
                SUM(CASE WHEN af.freq_frequencia = 0 THEN 1 ELSE 0 END) AS Faltas
            FROM
                tb_aula_frequencia af
            JOIN
                tb_alunos a ON af.freq_alu_id = a.alu_id
            JOIN
                tb_aulas au ON af.freq_aula_id = au.aul_id
            GROUP BY
                a.alu_nome
            ORDER BY
                a.alu_nome;
        """)
        alunos_faltas = cursor.fetchall()

        # Consultar o relatório de médias ponderadas por aluno e disciplina
        cursor.execute("""
            SELECT 
                a.alu_nome AS Aluno, 
                d.dis_nome AS Disciplina, 
                SUM(aa.alunoativ_nota * atv.ati_peso) / SUM(atv.ati_peso) AS Media
            FROM 
                tb_aluno_atividade aa
            JOIN 
                tb_atividades atv ON aa.alunoativ_ati_id = atv.ati_id
            JOIN 
                tb_disciplinas d ON atv.ati_dis_id = d.dis_id
            JOIN 
                tb_alunos a ON aa.alunoativ_alu_id = a.alu_id
            WHERE 
                aa.alunoativ_situacao = 'Entregue'
            GROUP BY 
                a.alu_id, d.dis_id
            ORDER BY 
                a.alu_nome, d.dis_nome;
        """)
        medias_ponderadas = cursor.fetchall()

        # Organizar os dados de médias ponderadas por aluno e disciplina
        medias_por_aluno_e_disciplina = {}
        for media in medias_ponderadas:
            disciplina = media['Disciplina']
            aluno = media['Aluno']
            if disciplina not in medias_por_aluno_e_disciplina:
                medias_por_aluno_e_disciplina[disciplina] = {}
            medias_por_aluno_e_disciplina[disciplina][aluno] = round(media['Media'], 2)

        # Calcular percentual de frequência por aluno e filtrar os abaixo de 75%
        alunos_baixa_frequencia = []
        for aluno in alunos_faltas:
            aulas = aluno['Aulas']
            faltas = aluno['Faltas']
            if aulas > 0:
                frequencia = ((aulas - faltas) / aulas) * 100  # Calcular percentual de frequência
                if frequencia < 75:  # Filtrar alunos com frequência abaixo de 75%
                    aluno['Percentual'] = frequencia
                    alunos_baixa_frequencia.append(aluno)

        # Consultar relatório de trabalhos entregues, divididos por aluno e disciplina
        cursor.execute("""
            SELECT 
                d.dis_nome AS disciplina,
                a.alu_nome AS aluno,
                t.ati_descricao AS atividade,
                aa.alunoativ_situacao AS situacao,
                aa.alunoativ_nota AS nota,
                aa.alunoativ_data_entrega AS data_entrega,
                t.ati_data_entrega AS data_limite_entrega
            FROM 
                tb_aluno_atividade aa
            JOIN 
                tb_atividades t ON aa.alunoativ_ati_id = t.ati_id
            JOIN 
                tb_disciplinas d ON t.ati_dis_id = d.dis_id
            JOIN 
                tb_alunos a ON aa.alunoativ_alu_id = a.alu_id
            WHERE 
                aa.alunoativ_situacao = 'Entregue'
            ORDER BY 
                d.dis_nome, a.alu_nome, t.ati_descricao
        """)
        trabalhos_entregues = cursor.fetchall()

        # Organizar os dados em formato estruturado por disciplina e aluno
        trabalhos_por_aluno_e_disciplina = {}
        for trabalho in trabalhos_entregues:
            disciplina = trabalho['disciplina']
            aluno = trabalho['aluno']
            if disciplina not in trabalhos_por_aluno_e_disciplina:
                trabalhos_por_aluno_e_disciplina[disciplina] = {}
            if aluno not in trabalhos_por_aluno_e_disciplina[disciplina]:
                trabalhos_por_aluno_e_disciplina[disciplina][aluno] = []
            trabalhos_por_aluno_e_disciplina[disciplina][aluno].append({
                'atividade': trabalho['atividade'],
                'situacao': trabalho['situacao'],
                'nota': trabalho['nota'],
                'data_entrega': trabalho['data_entrega'].strftime('%d/%m/%Y %H:%M') if trabalho['data_entrega'] else 'Não informado',
                'data_limite_entrega': trabalho['data_limite_entrega'].strftime('%d/%m/%Y %H:%M') if trabalho['data_limite_entrega'] else 'Não informado'
            })

        # Consultar trabalhos entregues fora do prazo
        cursor.execute("""
            SELECT 
                d.dis_nome AS disciplina,
                a.alu_nome AS aluno,
                t.ati_descricao AS atividade,
                aa.alunoativ_situacao AS situacao,
                aa.alunoativ_nota AS nota,
                aa.alunoativ_data_entrega AS data_entrega,
                t.ati_data_entrega AS data_limite_entrega
            FROM 
                tb_aluno_atividade aa
            JOIN 
                tb_atividades t ON aa.alunoativ_ati_id = t.ati_id
            JOIN 
                tb_disciplinas d ON t.ati_dis_id = d.dis_id
            JOIN 
                tb_alunos a ON aa.alunoativ_alu_id = a.alu_id
            WHERE 
                aa.alunoativ_situacao = 'Entregue'
                AND aa.alunoativ_data_entrega > t.ati_data_entrega
            ORDER BY 
                d.dis_nome, a.alu_nome, t.ati_descricao
        """)
        trabalhos_fora_prazo = cursor.fetchall()

    # Organizar os dados de trabalhos fora do prazo
    trabalhos_fora_prazo_por_aluno_e_disciplina = {}
    for trabalho in trabalhos_fora_prazo:
        disciplina = trabalho['disciplina']
        aluno = trabalho['aluno']
        if disciplina not in trabalhos_fora_prazo_por_aluno_e_disciplina:
            trabalhos_fora_prazo_por_aluno_e_disciplina[disciplina] = {}
        if aluno not in trabalhos_fora_prazo_por_aluno_e_disciplina[disciplina]:
            trabalhos_fora_prazo_por_aluno_e_disciplina[disciplina][aluno] = []
        trabalhos_fora_prazo_por_aluno_e_disciplina[disciplina][aluno].append({
            'atividade': trabalho['atividade'],
            'situacao': trabalho['situacao'],
            'nota': trabalho['nota'],
            'data_entrega': trabalho['data_entrega'].strftime('%d/%m/%Y %H:%M') if trabalho['data_entrega'] else 'Não informado',
            'data_limite_entrega': trabalho['data_limite_entrega'].strftime('%d/%m/%Y %H:%M') if trabalho['data_limite_entrega'] else 'Não informado'
        })

    # Renderiza a página de relatórios com todos os dados
    return render_template(
        'relatorios/relatorios.html',
        alunos=alunos,
        aula_frequencia=aula_frequencia,
        atividades=atividades,
        alu_atividade=alu_atividade,
        alunos_faltas=alunos_faltas,
        alunos_baixa_frequencia=alunos_baixa_frequencia,
        trabalhos_por_aluno_e_disciplina=trabalhos_por_aluno_e_disciplina,
        medias_por_aluno_e_disciplina=medias_por_aluno_e_disciplina,
        trabalhos_fora_prazo_por_aluno_e_disciplina=trabalhos_fora_prazo_por_aluno_e_disciplina
    )

@bp.route('/media_alunos')
@login_required
def media_alunos():
    """Calcula e exibe as médias dos alunos por disciplina."""
    connection = get_db_connection()

    try:
        with connection.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT alu_id FROM tb_alunos")
            alunos = cursor.fetchall()

            cursor.execute("SELECT dis_id FROM tb_disciplinas")
            disciplinas = cursor.fetchall()

            for aluno in alunos:
                for disciplina in disciplinas:
                    cursor.execute("SELECT calcular_media(%s, %s) AS media_calculada", (aluno['alu_id'], disciplina['dis_id']))
                    result = cursor.fetchone()

                    print(f"Resultado calcular_media para aluno {aluno['alu_id']}, disciplina {disciplina['dis_id']}: {result}")

                    if result and 'media_calculada' in result:
                        try:
                            media_calculada = float(result['media_calculada'])  # Garantir conversão para float
                        except (ValueError, TypeError):
                            media_calculada = None  # Se não for possível converter, definir como None
                    else:
                        media_calculada = None

                    print(f"Aluno {aluno['alu_id']}, Disciplina {disciplina['dis_id']} -> Média antes da frequência: {media_calculada}, Tipo: {type(media_calculada)}")

                    cursor.execute("""
                        SELECT COUNT(*) AS total_aulas FROM tb_aulas WHERE aul_dis_id = %s
                    """, (disciplina['dis_id'],))
                    total_aulas = cursor.fetchone().get('total_aulas', 0)

                    cursor.execute("""
                        SELECT COUNT(*) AS aulas_presentes
                        FROM tb_aula_frequencia af
                        JOIN tb_aulas a ON af.freq_aula_id = a.aul_id
                        WHERE af.freq_alu_id = %s AND af.freq_frequencia = 1 AND a.aul_dis_id = %s
                    """, (aluno['alu_id'], disciplina['dis_id']))
                    aulas_presentes = cursor.fetchone().get('aulas_presentes', 0)

                    frequencia_percentual = (aulas_presentes / total_aulas) * 100 if total_aulas > 0 else 0

                    print(f"Aluno {aluno['alu_id']}, Disciplina {disciplina['dis_id']} -> Total aulas: {total_aulas}, Presentes: {aulas_presentes}, Frequência: {frequencia_percentual:.2f}%, Tipo: {type(frequencia_percentual)}")

                    if frequencia_percentual < 75:
                        media_calculada = -1  # Definir -1 para indicar frequência insuficiente
                        print(f"Frequência insuficiente para aluno {aluno['alu_id']} na disciplina {disciplina['dis_id']}. Média definida como -1.")

                    # **Correção**: Certificar que `-1` seja tratado corretamente
                    if media_calculada == -1:
                        media_para_banco = -1.0  
                    else:
                        media_para_banco = float(media_calculada)  # Garantir que seja um float válido

                    print(f"Salvando média para aluno {aluno['alu_id']}, disciplina {disciplina['dis_id']}: {media_para_banco}, Tipo: {type(media_para_banco)}")

                    cursor.execute("""
                        INSERT INTO tb_aluno_media (media_alu_id, media_dis_id, media_calculada)
                        VALUES (%s, %s, %s)
                        ON DUPLICATE KEY UPDATE media_calculada = %s
                    """, (aluno['alu_id'], disciplina['dis_id'], media_para_banco, media_para_banco))

            connection.commit()

            query = """
            SELECT 
                a.alu_id, a.alu_nome, 
                d.dis_id, d.dis_nome, 
                m.media_calculada
            FROM tb_alunos a
            JOIN tb_aluno_media m ON a.alu_id = m.media_alu_id
            JOIN tb_disciplinas d ON m.media_dis_id = d.dis_id
            ORDER BY a.alu_nome, d.dis_nome;
            """
            cursor.execute(query)
            medias = cursor.fetchall()

            for media in medias:
                print(f"Banco de Dados -> Aluno {media['alu_id']}, Disciplina {media['dis_id']}, Média: {media['media_calculada']}, Tipo: {type(media['media_calculada'])}")

                if media['media_calculada'] is None:
                    media['media_calculada'] = "Nota Insuficiente"
                else:
                    media['media_calculada'] = round(float(media['media_calculada']), 2)

        return render_template('relatorios/media_alunos.html', medias=medias)

    except Exception as e:
        print(f"Erro ao calcular ou buscar médias: {e}")
        return "Erro ao calcular médias."

    finally:
        connection.close()

