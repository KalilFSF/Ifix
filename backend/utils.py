# Funções auxiliares de validação e upload, usadas pelas rotas de cadastro
# (routes.py). Ficam separadas pra não inchar routes.py com lógica que não
# é sobre "o que fazer com a requisição", e sim "como validar um dado".

import os
import re
import uuid
from datetime import date, datetime

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


def extensao_permitida(filename, extensoes):
    """Checa se a extensão do arquivo (ex: 'jpg') está no conjunto permitido."""
    return bool(filename) and "." in filename and filename.rsplit(".", 1)[1].lower() in extensoes


def salvar_arquivo(arquivo, pasta_destino):
    """Salva um arquivo enviado por upload com um nome único e retorna o nome salvo.

    O prefixo uuid4 evita que dois uploads com o mesmo nome de arquivo
    (ex: "foto.jpg" de dois técnicos diferentes) se sobrescrevam no disco.
    secure_filename() limpa o nome original de caracteres perigosos
    (ex: "../../etc/passwd" viraria só "etc_passwd").
    """
    nome_seguro = secure_filename(arquivo.filename)
    nome_final = f"{uuid.uuid4().hex}_{nome_seguro}"

    os.makedirs(pasta_destino, exist_ok=True)
    arquivo.save(os.path.join(pasta_destino, nome_final))

    return nome_final


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
