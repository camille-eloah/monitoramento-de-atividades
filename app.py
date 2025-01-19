from flask import Flask, redirect, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/cad_aluno')
def cad_aluno():
    return render_template('cad_aluno.html')

@app.route('/cad_disciplinas')
def cad_disciplinas():
    return render_template('cad_disciplinas.html')

@app.route('/gestao_freq')
def gestao_freq():
    return render_template('gestao_freq.html')

@app.route('/relatorios')
def relatorios():
    return render_template('relatorios.html')

# É PRA FAZER O QUE? :(


if __name__ == '__main__':
    app.run(debug=True)
