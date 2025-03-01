from flask import Flask , Blueprint, render_template, request, redirect, url_for, flash
from controllers.auth import executar_query
from flask_login import LoginManager, current_user, login_required
from app import app, get_db_connection
import pymysql
from pymysql.err import IntegrityError

bp = Blueprint('relatorios', __name__, url_prefix='/relatorios')

@bp.route('/')
def index():
    return render_template('relatorios/index.html') 

@bp.route('/relatorios')
@login_required
def relatorios():
    connection = get_db_connection()

    # Busca os dados necessários para os relatórios
    with connection.cursor() as cursor:
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
