from fastapi import FastAPI, HTTPException, Request
from typing import List, Optional
from pydantic import BaseModel
import time
import asyncpg
import os

# Função para obter a conexão com o banco de dados PostgreSQL
async def get_database():
    DATABASE_URL = os.environ.get("PGURL", "postgres://postgres:postgres@db:5432/agendamento_consultas") 
    return await asyncpg.connect(DATABASE_URL)

app = FastAPI()

# Definindo a classe para o corpo da requisição
# Modelo para adicionar novos medicos
class Medico(BaseModel):
    id: Optional[int] = None
    nome: str
    crm: str
    especialidade: str

class Consulta(BaseModel):
    id: Optional[int] = None
    medico_id: int
    nome_medico: Optional[str] = None
    data: str
    valor: float
    tipo: str
    convenio: str

class MedicoBase(BaseModel):
    nome: str
    crm: str
    especialidade: str

# Modelo para atualizar atributos de um Médico (exceto o ID)
class AtualizarMedico(BaseModel):
    nome: Optional[str] = None
    crm: Optional[str] = None
    especialidade: Optional[str] = None

# Modelo para atualizar atributos de uma Consulta (exceto o ID)
class AtualizarConsulta(BaseModel):
    medico_id: Optional[int] = None
    data: Optional[str] = None
    valor: Optional[float] = None
    tipo: Optional[str] = None
    convenio: Optional[str] = None

# Middleware para logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    print(f"Path: {request.url.path}, Method: {request.method}, Process Time: {process_time:.4f}s")
    return response

# Função para verificar se o medico existe usando o crm do médico
async def medico_existe(crm: str, conn: asyncpg.Connection):
    try:
        query = "SELECT * FROM medico WHERE crm = $1"
        result = await conn.fetchval(query, crm)
        return result is not None
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Falha ao verificar se o médico existe: {str(e)}")

# Função para verificar se a consulta existe usando o crm do médico
async def consulta_existe(medico_id: int, data:str, conn: asyncpg.Connection):
    data = data.replace("T", " ")
    try:
        query = "SELECT * FROM consultas WHERE medico_id = $1 AND data = $2"
        result = await conn.fetchval(query, medico_id, data)
        return result is not None
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Falha ao verificar se a consulta existe: {str(e)}")

# 1. Adicionar um novo medico
@app.post("/api/v1/medicos/", status_code=201)
async def adicionar_medico(medico: Medico):
    conn = await get_database()
    if await medico_existe(medico.crm, conn):
        raise HTTPException(status_code=400, detail="Médico já existe.")
    try:
        query = "INSERT INTO medico (nome, crm, especialidade) VALUES ($1, $2, $3)"
        async with conn.transaction():
            result = await conn.execute(query, medico.nome, medico.crm, medico.especialidade)
            return {"message": "Médico adicionado com sucesso!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Falha ao adicionar o médico: {str(e)}")
    finally:
        await conn.close()

# 2. Listar todos os medicos
@app.get("/api/v1/medicos/", response_model=List[Medico])
async def listar_medicos():
    conn = await get_database()
    try:
        # Buscar todos os medicos no banco de dados
        query = "SELECT * FROM medico"
        rows = await conn.fetch(query)
        medicos = [dict(row) for row in rows]
        return medicos
    finally:
        await conn.close()

# 3. Buscar medico por ID
@app.get("/api/v1/medicos/{medico_id}")
async def listar_medico_por_id(medico_id: int):
    conn = await get_database()
    try:
        # Buscar o medico por ID
        query = "SELECT * FROM medico WHERE id = $1"
        medico = await conn.fetchrow(query, medico_id)
        if medico is None:
            raise HTTPException(status_code=404, detail="Medico não encontrado.")
        return dict(medico)
    finally:
        await conn.close()

# 5. Atualizar atributos de um medico pelo ID (exceto o ID)
@app.patch("/api/v1/medicos/{medico_id}")
async def atualizar_medico(medico_id: int, medico_atualizacao: AtualizarMedico):
    conn = await get_database()
    try:
        # Verificar se o medico existe
        query = "SELECT * FROM medico WHERE id = $1"
        medico = await conn.fetchrow(query, medico_id)
        if medico is None:
            raise HTTPException(status_code=404, detail="Médico não encontrado.")

        # Atualizar apenas os campos fornecidos
        update_query = """
            UPDATE medico
            SET nome = COALESCE($1, nome),
                crm = COALESCE($2, crm),
                especialidade = COALESCE($3, especialidade)
            WHERE id = $4
        """
        await conn.execute(
            update_query,
            medico_atualizacao.nome,
            medico_atualizacao.crm,
            medico_atualizacao.especialidade,
            medico_id
        )
        return {"message": "Médico atualizado com sucesso!"}
    finally:
        await conn.close()

# 6. Remover um medico pelo ID
@app.delete("/api/v1/medicos/{medico_id}")
async def remover_medico(medico_id: int):
    conn = await get_database()
    try:
        # Verificar se o medico existe
        query = "SELECT * FROM medico WHERE id = $1"
        medico = await conn.fetchrow(query, medico_id)
        if medico is None:
            raise HTTPException(status_code=404, detail="Médico não encontrado.")

        # Remover o médico do banco de dados
        delete_query = "DELETE FROM medico WHERE id = $1"
        await conn.execute(delete_query, medico_id)
        return {"message": "Médico removido com sucesso!"}
    finally:
        await conn.close()

# 7. Resetar repositorio de médicos
@app.delete("/api/v1/medicos/")
async def resetar_medicos():
    init_sql = os.getenv("INIT_SQL", "db/init.sql")
    conn = await get_database()
    try:
        # Read SQL file contents
        with open(init_sql, 'r') as file:
            sql_commands = file.read()
        # Execute SQL commands
        await conn.execute(sql_commands)
        return {"message": "Banco de dados limpo com sucesso!"}
    finally:
        await conn.close()

# 8. Criar uma nova consulta
@app.post("/api/v1/consultas/", status_code=201)
async def adicionar_consulta(consulta: Consulta):
    consulta.data = consulta.data.replace("T", " ")
    conn = await get_database()
    if await consulta_existe(consulta.medico_id, consulta.data, conn):
        raise HTTPException(status_code=400, detail="O Médico já está ocupado nesse horário.")
    try:
        query = "INSERT INTO consultas (medico_id, data, valor, tipo, convenio) VALUES ($1, $2, $3, $4, $5)"
        async with conn.transaction():
            result = await conn.execute(query, consulta.medico_id, str(consulta.data), consulta.valor, consulta.tipo, consulta.convenio)
            return {"message": "Consulta adicionada com sucesso!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Falha ao adicionar a consulta: {str(e)}")
    finally:
        await conn.close()

# 9. Listar todas as consultas
@app.get("/api/v1/consultas/", response_model=List[Consulta])
async def listar_consultas():
    conn = await get_database()
    try:
        # Buscar todas as consultas no banco de dados
        query = "SELECT A.*, B.nome AS nome_medico FROM consultas A INNER JOIN medico B ON B.ID = A.medico_id"
        rows = await conn.fetch(query)
        consultas = [dict(row) for row in rows]
        return consultas
    finally:
        await conn.close()

# 10. Buscar consulta por ID
@app.get("/api/v1/consultas/{consulta_id}")
async def listar_consulta_por_id(consulta_id: int):
    conn = await get_database()
    try:
        # Buscar a consulta por ID
        query = "SELECT * FROM consultas WHERE id = $1"
        consulta = await conn.fetchrow(query, consulta_id)
        if consulta is None:
            raise HTTPException(status_code=404, detail="Consulta não encontrada.")
        return dict(consulta)
    finally:
        await conn.close()

# 11. Atualizar atributos de uma consulta pelo ID (exceto o ID)
@app.patch("/api/v1/consultas/{consulta_id}")
async def atualizar_consulta(consulta_id: int, consulta_atualizacao: AtualizarConsulta):
    conn = await get_database()
    try:
        # Verificar se a consulta existe
        query = "SELECT A.*, B.nome AS nome_medico FROM consultas A INNER JOIN medico B ON B.ID = A.medico_id WHERE A.id = $1"
        consulta = await conn.fetchrow(query, consulta_id)
        if consulta is None:
            raise HTTPException(status_code=404, detail="Consulta não encontrada.")

        # Atualizar apenas os campos fornecidos
        update_query = """
            UPDATE consultas
            SET medico_id = COALESCE($1, medico_id),
                data = COALESCE($2, data),
                valor = COALESCE($3, valor),
                tipo = COALESCE($4, tipo),
                convenio = COALESCE($5, convenio)
            WHERE id = $6
        """
        await conn.execute(
            update_query,
            consulta_atualizacao.medico_id,
            consulta_atualizacao.data,
            consulta_atualizacao.valor,
            consulta_atualizacao.tipo,
            consulta_atualizacao.convenio,
            consulta_id
        )
        return {"message": "Consulta atualizada com sucesso!"}
    finally:
        await conn.close()

# 11. Remover uma consulta pelo ID
@app.delete("/api/v1/consultas/{consulta_id}")
async def remover_consulta(consulta_id: int):
    conn = await get_database()
    try:
        # Verificar se a consulta existe
        query = "SELECT A.*, B.nome AS nome_medico FROM consultas A INNER JOIN medico B ON B.ID = A.medico_id WHERE A.id = $1"
        consulta = await conn.fetchrow(query, consulta_id)
        if consulta is None:
            raise HTTPException(status_code=404, detail="Consulta não encontrada.")

        # Remover a consulta do banco de dados
        delete_query = "DELETE FROM consultas WHERE id = $1"
        await conn.execute(delete_query, consulta_id)
        return {"message": "Consulta removida com sucesso!"}
    finally:
        await conn.close()