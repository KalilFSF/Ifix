# Funções auxiliares de validação e upload, usadas pelas rotas de cadastro
# (routes.py). Ficam separadas pra não inchar routes.py com lógica que não
# é sobre "o que fazer com a requisição", e sim "como validar um dado".

import math
import os
import re
import uuid
from datetime import date, datetime, timezone

import cloudinary
import cloudinary.uploader

cloudinary.config(
    cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME"),
    api_key=os.environ.get("CLOUDINARY_API_KEY"),
    api_secret=os.environ.get("CLOUDINARY_API_SECRET"),
)

from werkzeug.utils import secure_filename

IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
DOCUMENT_EXTENSIONS = IMAGE_EXTENSIONS | {"pdf"}


def somente_digitos(valor):
    """Remove tudo que não é número (usado pra tirar a máscara do CPF antes de salvar/validar)."""
    return re.sub(r"\D", "", valor or "")


def validar_cpf(cpf):
    """Valida um CPF pelo algoritmo padrão dos dígitos verificadores.

    Cada um dos 2 últimos dígitos do CPF é calculado a partir dos 9 (ou 10)
    dígitos anteriores, multiplicando-os por pesos decrescentes e tirando o
    resto da divisão por 11. Se o dígito informado não bater com o
    calculado, o CPF é inválido (não existe, mesmo que tenha 11 números).
    """
    cpf = somente_digitos(cpf)

    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False

    for posicao in (9, 10):
        soma = sum(int(cpf[indice]) * ((posicao + 1) - indice) for indice in range(posicao))
        digito = (soma * 10 % 11) % 10
        if digito != int(cpf[posicao]):
            return False

    return True


def validar_data_nascimento(valor):
    """Converte a string 'YYYY-MM-DD' do <input type="date"> em date e valida o intervalo.

    Retorna um `date` se for válida, ou None se o formato/intervalo estiver errado
    (a rota usa esse None pra decidir se mostra a mensagem de erro).
    """
    try:
        data_convertida = datetime.strptime(valor, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None

    if data_convertida < date(1900, 1, 1) or data_convertida > date.today():
        return None

    return data_convertida


RAIO_TERRA_KM = 6371.0


def haversine_km(lat1, lon1, lat2, lon2):
    """Distância em linha reta (km) entre duas coordenadas, pela fórmula de
    Haversine — Python puro, sem PostGIS/geopy (usado pelo ranking de
    técnicos em SelecionarTecnicosService)."""
    lat1_rad, lon1_rad, lat2_rad, lon2_rad = map(math.radians, (lat1, lon1, lat2, lon2))
    delta_lat = lat2_rad - lat1_rad
    delta_lon = lon2_rad - lon1_rad

    a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    return RAIO_TERRA_KM * c


def isoformat_utc(dt):
    """Serializa um datetime pra ISO 8601 com o offset UTC explícito.

    Toda data do projeto é gravada como datetime.now(timezone.utc), mas o
    Postgres (TIMESTAMP WITHOUT TIME ZONE, o tipo do db.DateTime puro) joga
    fora o tzinfo ao salvar — o valor lido de volta vem "naive". Sem
    recolocar o offset aqui, dt.isoformat() sai sem sufixo de fuso, e o
    front (new Date(str) em JS) interpreta a string como horário LOCAL em
    vez de UTC, mostrando a hora errada.
    """
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def parsear_coordenada(valor):
    """Converte a string de latitude/longitude vinda do formulário (captura
    via navigator.geolocation no front) em float, ou None se vazia/inválida
    — a coordenada é sempre opcional, nunca bloqueia cadastro/chamado."""
    if valor in (None, ""):
        return None
    try:
        return float(valor)
    except (TypeError, ValueError):
        return None


def extensao_permitida(filename, extensoes):
    """Checa se a extensão do arquivo (ex: 'jpg') está no conjunto permitido."""
    return bool(filename) and "." in filename and filename.rsplit(".", 1)[1].lower() in extensoes


def salvar_arquivo(arquivo, pasta_destino):
    """Envia o arquivo pro Cloudinary com um nome único e retorna a URL pública dele.

    O prefixo uuid4 evita que dois uploads com o mesmo nome de arquivo
    (ex: "foto.jpg" de dois técnicos diferentes) se sobrescrevam. A pasta_destino
    vira o "folder" dentro do Cloudinary, mantendo a mesma organização que
    tínhamos localmente (perfil/, diplomas/, chamados/).
    """
    nome_seguro = secure_filename(arquivo.filename)
    nome_sem_extensao = os.path.splitext(nome_seguro)[0]
    public_id = f"{uuid.uuid4().hex}_{nome_sem_extensao}"

    resultado = cloudinary.uploader.upload(
        arquivo,
        public_id=public_id,
        folder=pasta_destino,
    )

    return resultado["secure_url"]


ESCOLARIDADES_VALIDAS = {"Ensino médio", "Técnico", "Superior cursando", "Superior completo"}


def validar_campos_comuns(dados, senha, confirmar_senha):
    """Validação de formato/obrigatoriedade dos campos comuns a cliente e
    técnico (nome, email, cpf, senha, endereço) — não toca o banco; checagem
    de unicidade (email/cpf já cadastrado) é regra de negócio e fica a
    cargo de cada Service de cadastro, que já tem acesso à Model."""
    if not dados["nome"] or len(dados["nome"]) < 3:
        return "Informe seu nome completo."
    if not dados["email"] or "@" not in dados["email"]:
        return "Informe um email válido."
    if not dados["telefone"]:
        return "Informe um telefone válido."
    if not dados["cpf"] or len(dados["cpf"]) != 11:
        return "Informe um CPF válido."

    data_nascimento = validar_data_nascimento(dados["data_nascimento"])
    if data_nascimento is None:
        return "Informe uma data de nascimento válida (entre 01/01/1900 e hoje)."
    dados["data_nascimento"] = data_nascimento

    if len(senha) < 6:
        return "A senha deve ter pelo menos 6 caracteres."
    if senha != confirmar_senha:
        return "As senhas não coincidem."
    if not dados["pais"]:
        return "Selecione o país."
    if dados["pais"] != "Outro":
        campos_endereco = (
            dados["cep"],
            dados["estado"],
            dados["cidade"],
            dados["bairro"],
            dados["endereco"],
            dados["numero"],
        )
        if not all(campos_endereco):
            return "Preencha o endereço completo (CEP, estado, cidade, bairro, endereço e número)."
    return None


def validar_dados_tecnico(dados_tecnico, foto_perfil, diplomas_arquivos):
    """Validação de formato dos campos específicos de técnico — não toca o banco."""
    if not dados_tecnico.get("especialidade"):
        return "Informe sua especialidade."
    if dados_tecnico.get("escolaridade") not in ESCOLARIDADES_VALIDAS:
        return "Selecione sua escolaridade."
    if not dados_tecnico.get("regiao_atendimento"):
        return "Informe a região de atendimento."
    if foto_perfil is None or foto_perfil.filename == "":
        return "Envie uma foto de perfil."
    if not extensao_permitida(foto_perfil.filename, IMAGE_EXTENSIONS):
        return "A foto de perfil deve ser uma imagem (png, jpg, jpeg ou webp)."
    for arquivo in diplomas_arquivos:
        if not extensao_permitida(arquivo.filename, DOCUMENT_EXTENSIONS):
            return "Diplomas e certificados devem ser imagem ou PDF."
    return None
