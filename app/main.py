import logging
import logging.config
import yaml
import zipfile
import os
from fastapi import FastAPI, HTTPException, Path
from pydantic import BaseModel
from typing import List, Optional
import csv
from datetime import datetime
from io import BytesIO
from fastapi.responses import StreamingResponse
import hashlib

# Carrega a configuração de logging do arquivo YAML
def setup_logging():
    # Defina o diretório de trabalho para o diretório onde o script está localizado
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    with open("logging_config.yaml", "r") as file:
        config = yaml.safe_load(file)
        logging.config.dictConfig(config)

setup_logging()


logger = logging.getLogger("app_logger")



class EventCreate(BaseModel):
    title: str
    date: str  # Exemplo: "2024-12-25"
    location: str
    capacity: int


class EventResponse(BaseModel):
    id: int
    title: str
    date: str
    location: str
    capacity: int


CSV_FILE = "events.csv"

app = FastAPI()

@app.get("/hello-world")
def read_root():
    logger.info("API root endpoint accessed.")
    return {"message": "Academic Event Manager - API is running!"}


def inicializar_csv():
    try:
        with open(CSV_FILE, mode="x", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["id","title", "date", "location", "capacity"])  # Cabeçalhos
    except FileExistsError:
        pass

inicializar_csv()


# Função para gravar um evento no CSV
def gravar_evento(evento: EventResponse):
    with open(CSV_FILE, mode="a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([evento.id, evento.title, evento.date, evento.location, evento.capacity])

# Função para carregar eventos do CSV
def carregar_eventos() -> List[EventResponse]:
    eventos = []
    with open(CSV_FILE, mode="r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            try:
                row['id'] = int(row['id'])
                eventos.append(EventResponse(**row))
            except ValueError:
                logger.error(f"Valor inválido para id: {row['id']}")
                continue  # Ignora a linha com valor inválido
    return eventos

# Função para salvar todos os eventos de volta no CSV
def salvar_eventos(eventos: List[EventResponse]):
    with open(CSV_FILE, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["id", "title", "date", "location", "capacity"])  # Cabeçalhos
        for evento in eventos:
            writer.writerow([evento.id, evento.title, evento.date, evento.location, evento.capacity])
# Função para contar a quantidade de eventos no CSV
def contar_eventos() -> int:
    with open(CSV_FILE, mode="r") as file:
        reader = csv.reader(file)
        next(reader)  # Ignora a primeira linha (cabeçalho)
        return sum(1 for row in reader)  # Conta o número de linhas restantes
    

# Função para compactar o arquivo CSV em um ZIP
def compactar_csv_em_zip():
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, mode='w', compression=zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.write(CSV_FILE, os.path.basename(CSV_FILE))  # Adiciona o CSV ao arquivo ZIP
    zip_buffer.seek(0)  # Volta o ponteiro do buffer para o início
    return zip_buffer  

# Função para calcular o hash SHA256 do arquivo CSV
def calcular_hash_sha256() -> str:
    sha256_hash = hashlib.sha256()
    with open(CSV_FILE, "rb") as f:  # Abrindo o arquivo em modo binário
        # Ler e atualizar o hash com os dados do arquivo em blocos
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


# Rota para criar um evento
@app.post("/api/v1/eventos/", response_model=EventCreate)
def criar_evento(evento: EventCreate):
    try:
        # Valida a data
        datetime.strptime(evento.date, "%Y-%m-%d")
        if evento.capacity <= 0:
            raise HTTPException(status_code=400, detail="Capacidade deve ser maior que zero.")
    except ValueError:
        logger.error("Failed to create event: Invalid date format.")
        raise HTTPException(status_code=400, detail="Formato de data inválido. Use AAAA-MM-DD.")

    # Calcula o próximo ID
    eventos = carregar_eventos()
    if eventos:
        max_id = max(e.id for e in eventos if e.id is not None)
        new_id = max_id + 1
    else:
        new_id = 1  # Primeiro ID

    novo_evento = EventResponse(id=new_id, **evento.dict())

    # Grava o evento no CSV
    gravar_evento(novo_evento)
    logger.info(f"Evento criado: {novo_evento}")
    return novo_evento


# Rota para listar todos os eventos
@app.get("/api/v1/eventos/", response_model=List[EventResponse])
def listar_eventos():
    eventos = carregar_eventos()
    logger.info("Todos os eventos foram listados.")
    return eventos


# Rota para buscar um evento pelo título
@app.get("/api/v1/eventos/{id}", response_model=EventResponse)
def buscar_evento(id: int):
    eventos = carregar_eventos()
    for evento in eventos:
        if evento.id == id:
            logger.info(f"Evento encontrado: {evento}")
            return evento
    logger.warning(f"Busca falhou: Evento '{id}' não encontrado.")
    raise HTTPException(status_code=404, detail="Evento não encontrado.")


# Rota para atualizar um evento
@app.put("/api/v1/eventos/{id}", response_model=EventResponse)
def atualizar_evento(id: int, evento_atualizado: EventCreate):
    eventos = carregar_eventos()
    evento_encontrado = False

    try:
        # Valida a data
        datetime.strptime(evento_atualizado.date, "%Y-%m-%d")
        if evento_atualizado.capacity <= 0:
            raise HTTPException(status_code=400, detail="Capacidade deve ser maior que zero.")
    except ValueError:
        logger.error("Failed to create event: Invalid date format.")
        raise HTTPException(status_code=400, detail="Formato de data inválido. Use AAAA-MM-DD.")

    for i, evento in enumerate(eventos):
        if evento.id == id:
            eventos[i] = EventResponse(id=id, **evento_atualizado.dict())
            evento_encontrado = True
            break

    if not evento_encontrado:
        logger.warning(f"Tentativa de atualização falhou: Evento '{id}' não encontrado.")
        raise HTTPException(status_code=404, detail="Evento não encontrado.")

    salvar_eventos(eventos)
    logger.info(f"Evento atualizado: {evento_atualizado}")
    return eventos[i].dict()  # Converte a resposta para um dicionário



# Rota para excluir um evento
@app.delete("/api/v1/eventos/{id}", response_model=dict)
def excluir_evento(id: int):
    eventos = carregar_eventos()
    evento_encontrado = None
    eventos_filtrados = []

    for evento in eventos:
        if evento.id == id:
            evento_encontrado = evento
        else:
            eventos_filtrados.append(evento)

    if evento_encontrado is None:
        logger.warning(f"Tentativa de exclusão falhou: Evento '{id}' não encontrado.")
        raise HTTPException(status_code=404, detail="Evento não encontrado.")

    salvar_eventos(eventos_filtrados)
    logger.info(f"Evento excluído: {evento_encontrado.title}")
    return {"message": f"Evento '{evento_encontrado.title}' excluído com sucesso."}

# Rota para mostrar a quantidade de eventos cadastrados
@app.get("/api/v1/eventos/quantidadetotal/", response_model=dict)
def quantidade_eventos():
    quantidade = contar_eventos()
    logger.info(f"Quantidade de eventos cadastrados: {quantidade}")
    return {"quantidade": quantidade}


# Rota para compactar o CSV em um arquivo ZIP e permitir o download
@app.get("/api/v1/eventos/compactar/", response_class=StreamingResponse)
def compactar_eventos():
    zip_buffer = compactar_csv_em_zip()
    # Retorna o arquivo ZIP para o cliente
    return StreamingResponse(zip_buffer, media_type="application/zip", headers={"Content-Disposition": "attachment; filename=events.zip"})


# Rota para filtrar eventos por atributos específicos
@app.get("/api/v1/eventos/filtro/", response_model=List[EventCreate])
def filtrar_eventos(
    title: Optional[str] = None,
    date: Optional[str] = None,
    location: Optional[str] = None,
    capacity_min: Optional[int] = None,
    capacity_max: Optional[int] = None
):
    eventos = carregar_eventos()

    # Filtrando eventos com base nos parâmetros fornecidos
    if title:
        eventos = [evento for evento in eventos if title.lower() in evento.title.lower()]
    if date:
        eventos = [evento for evento in eventos if date == evento.date]
    if location:
        eventos = [evento for evento in eventos if location.lower() in evento.location.lower()]
    if capacity_min is not None:
        eventos = [evento for evento in eventos if evento.capacity >= capacity_min]
    if capacity_max is not None:
        eventos = [evento for evento in eventos if evento.capacity <= capacity_max]

    logger.info(f"{len(eventos)} eventos encontrados com os filtros aplicados.")
    return eventos



# Rota para retornar o hash SHA256 do arquivo CSV
@app.get("/api/v1/eventos/hash/", response_model=dict)
def hash_csv():
    hash_value = calcular_hash_sha256()
    logger.info(f"Hash SHA256 do arquivo CSV: {hash_value}")
    return {"hash_sha256": hash_value}