from flask import Flask
from app import create_app
from app.controllers import aluno_disciplina, alunos, atividades, aulas, cursos, disciplinas, relatorios, entregas
from controllers import auth

# Criação do aplicativo Flask
app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
