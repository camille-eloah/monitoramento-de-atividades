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
            # Buscar todos os alunos e disciplinas existentes
            cursor.execute("SELECT alu_id FROM tb_alunos")
            alunos = cursor.fetchall()

            cursor.execute("SELECT dis_id FROM tb_disciplinas")
            disciplinas = cursor.fetchall()

            # Para cada aluno e disciplina, calcular a média
            for aluno in alunos:
                for disciplina in disciplinas:
                    # Chama a função calcular_media
                    cursor.execute("SELECT calcular_media(%s, %s) AS media_calculada", (aluno['alu_id'], disciplina['dis_id']))
                    result = cursor.fetchone()  # Consumir o resultado da função
                    
                    # Debug: Verificar o que está sendo retornado
                    print(f"Resultado da função calcular_media para aluno {aluno['alu_id']} e disciplina {disciplina['dis_id']}: {result}")
                    
                    if result and 'media_calculada' in result:
                        media_calculada = result['media_calculada']  # Verifica se existe o campo 'media_calculada'
                        print(f"Média calculada (antes de verificação) para aluno {aluno['alu_id']} e disciplina {disciplina['dis_id']}: {media_calculada}")
                    else:
                        media_calculada = None  # Caso não haja retorno, definir como None
                    
                    # Verifique se a média é válida e um número real (float)
                    if media_calculada is not None:
                        try:
                            media_calculada = float(media_calculada)  # Forçar para tipo float
                            print(f"Média validada como float para aluno {aluno['alu_id']} e disciplina {disciplina['dis_id']}: {media_calculada}")
                        except ValueError:
                            print(f"Erro ao converter média para float para aluno {aluno['alu_id']} e disciplina {disciplina['dis_id']}: {media_calculada}")
                            media_calculada = None  # Se não for numérico, setar como None

                    # Adicionar debug para confirmar o valor de media_calculada
                    if media_calculada is not None:
                        print(f"Valor final da média para aluno {aluno['alu_id']} e disciplina {disciplina['dis_id']}: {media_calculada}")
                    else:
                        print(f"Média calculada é None para aluno {aluno['alu_id']} e disciplina {disciplina['dis_id']}")

                    if media_calculada is not None:
                        # Verificar a frequência antes de inserir ou atualizar a média
                        cursor.execute("""
                        SELECT COUNT(*) AS total_aulas
                        FROM tb_aulas
                        WHERE aul_dis_id = %s
                        """, (disciplina['dis_id'],))

                        total_aulas_result = cursor.fetchone()
                        total_aulas = total_aulas_result['total_aulas'] if total_aulas_result else 0
                        print(f"Total de aulas para disciplina {disciplina['dis_id']}: {total_aulas}")

                        cursor.execute("""
                        SELECT COUNT(*) AS aulas_presentes
                        FROM tb_aula_frequencia af
                        JOIN tb_aulas a ON af.freq_aula_id = a.aul_id
                        WHERE af.freq_alu_id = %s AND af.freq_frequencia = 1 AND a.aul_dis_id = %s
                        """, (aluno['alu_id'], disciplina['dis_id']))

                        aulas_presentes_result = cursor.fetchone()
                        aulas_presentes = aulas_presentes_result['aulas_presentes'] if aulas_presentes_result else 0
                        print(f"Aulas presentes para aluno {aluno['alu_id']} e disciplina {disciplina['dis_id']}: {aulas_presentes}")

                        # Calcula o percentual de frequência
                        if total_aulas > 0:
                            frequencia_percentual = (aulas_presentes / total_aulas) * 100
                        else:
                            frequencia_percentual = 0
                        print(f"Percentual de frequência para aluno {aluno['alu_id']} e disciplina {disciplina['dis_id']}: {frequencia_percentual}")

                        # Se a frequência for menor que 75%, define a média como -1
                        if frequencia_percentual < 75:
                            media_calculada = -1  # Definimos -1 para indicar frequência insuficiente
                            print(f"Frequência insuficiente para aluno {aluno['alu_id']} e disciplina {disciplina['dis_id']}. Média definida como -1.")

                    # Substituir a média insuficiente (-1) por None para não causar erro no banco de dados
                    if media_calculada == -1:
                        media_calculada = None  # Não vamos inserir -1 no banco, mas sim None

                    if media_calculada is not None:
                        # Atualiza ou insere a média
                        print(f"Inserindo ou atualizando média para aluno {aluno['alu_id']} e disciplina {disciplina['dis_id']}: {media_calculada}")
                        cursor.execute("""
                        INSERT INTO tb_aluno_media (media_alu_id, media_dis_id, media_calculada)
                        VALUES (%s, %s, %s)
                        ON DUPLICATE KEY UPDATE media_calculada = %s
                        """, (aluno['alu_id'], disciplina['dis_id'], media_calculada, media_calculada))

            connection.commit()  # Grava as médias no banco de dados

            # Agora busca todas as médias já calculadas
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

            # Substituir None por "Nota Insuficiente" e arredondar as médias normais
            for media in medias:
                if media['media_calculada'] is None:
                    media['media_calculada'] = "Nota Insuficiente"
                else:
                    media['media_calculada'] = round(media['media_calculada'], 2)  # Arredondar as médias normais

        return render_template('relatorios/media_alunos.html', medias=medias)

    except Exception as e:
        print(f"Erro ao calcular ou buscar médias: {e}")
        return "Erro ao calcular médias."

    finally:
        connection.close()
