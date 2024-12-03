from flask import Flask, render_template, request, redirect, url_for, jsonify
import requests
import os

app = Flask(__name__)

# Definindo as variáveis de ambiente
API_BASE_URL = "http://backend:8000"

# Rota para a página inicial
@app.route('/')
def index():
    return render_template('index.html')

# Rota para exibir o formulário de cadastro medico
@app.route('/cadastro_medicos', methods=['GET'])
def inserir_medico_form():
    return render_template('cadastro.html')

# Rota para enviar os dados do formulário de cadastro para a API
@app.route('/inserir', methods=['POST'])
def inserir_medico():
    nome = request.form['nome']
    crm = request.form['crm']
    especialidade = request.form['especialidade']

    payload = {
        'nome': nome,
        'crm': crm,
        'especialidade' : especialidade
    }

    response = requests.post(f'{API_BASE_URL}/api/v1/medicos/', json=payload)
    
    if response.status_code == 201:
        return redirect(url_for('listar_medicos'))
    else:
        return "Erro ao inserir médico", 500

# Rota para listar todos os médicos
@app.route('/lista_medicos', methods=['GET'])
def listar_medicos():
    response = requests.get(f'{API_BASE_URL}/api/v1/medicos/')
    try:
        medicos = response.json()
    except:
        medicos = []
    return render_template('lista_medicos.html', medicos=medicos)

# Rota para exibir o formulário de edição de medicos
@app.route('/atualizar/<int:medico_id>', methods=['GET'])
def atualizar_medico_form(medico_id):
    response = requests.get(f"{API_BASE_URL}/api/v1/medicos/")
    #filtrando apenas o componente correspondente ao ID
    medicos = [medico for medico in response.json() if medico['id'] == medico_id]
    if len(medicos) == 0:
        return "Médico não encontrado", 404
    medico = medicos[0]
    return render_template('atualizar.html', medico=medico)

# Rota para enviar os dados do formulário de edição de medico para a API
@app.route('/atualizar/<int:medico_id>', methods=['POST'])
def atualizar_medico(medico_id):
    nome = request.form['nome']
    crm = request.form['crm']
    especialidade = request.form['especialidade']

    payload = {
        'id': medico_id,
        'nome': nome,
        'crm': crm,
        'especialidade' : especialidade,
    }

    response = requests.patch(f"{API_BASE_URL}/api/v1/medicos/{medico_id}", json=payload)
    
    if response.status_code == 200:
        return redirect(url_for('listar_medicos'))
    else:
        return "Erro ao atualizar médico", 500

# Rota para excluir um medico
@app.route('/excluir/<int:medico_id>', methods=['POST'])
def excluir_medico(medico_id):
    response = requests.delete(f"{API_BASE_URL}/api/v1/medicos/{medico_id}")
    
    if response.status_code == 200  :
        return redirect(url_for('listar_medicos'))
    else:
        return "Erro ao excluir médico", 500

# Rota para exibir o cadastro de novas consultas
@app.route('/marcar_consulta/<int:medico_id>', methods=['GET'])
def marcar_consulta_form(medico_id):
    return render_template('marcar_consulta.html',medico_id=medico_id)

# Rota para marcar uma consulta com um médico
@app.route('/marcar_consulta/<int:medico_id>', methods=['POST'])
def marcar_consulta(medico_id):
    data = request.form['data']
    valor = request.form['valor']
    tipo = request.form['tipo']
    convenio = request.form['convenio']

    payload = {
        'medico_id': medico_id,
        'data': data,
        'valor': valor,
        'tipo': tipo,
        'convenio': convenio,
    }

    # ============ NO BACK DEVE ACEITAR O ID NA URL ==========
    response = requests.put(f"{API_BASE_URL}/api/v1/consultas/{medico_id}", json=payload)
    
    if response.status_code == 200:
        return redirect(url_for('listar_consultas'))
    else:
        return "Erro ao marcar a consulta", 500

# Rota para listar todas as consultas
@app.route('/lista_consultas', methods=['GET'])
def listar_consultas():
    response = requests.get(f"{API_BASE_URL}/api/v1/consultas/")
    try:
        consultas = response.json()
    except:
        consultas = []
    return render_template('lista_consultas.html', vendas=consultas)

#Rota para resetar o database
@app.route('/reset-database', methods=['GET'])
def resetar_database():
    response = requests.delete(f"{API_BASE_URL}/api/v1/medicos/")
    
    if response.status_code == 200  :
        return render_template('confirmacao.html')
    else:
        return "Erro ao resetar o database", 500


if __name__ == '__main__':
    app.run(debug=True, port=3000, host='0.0.0.0')
