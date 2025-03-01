from flask import Blueprint
from main import app

controllers = Blueprint('controllers',__name__ )

all = [
    'routes',
    'alunos',
    'disciplinas',
    'cursos',
    'auth',
    'relatorios',
    'aulas',
    'entregas',
    'disciplinas',
    'aluno_disciplina',
    'atividades'
]