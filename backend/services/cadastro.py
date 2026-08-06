from flask import current_app

from database import db
from models import Diploma, PerfilTecnico, Usuario
from utils import DOCUMENT_EXTENSIONS, IMAGE_EXTENSIONS, extensao_permitida, salvar_arquivo


class CadastroService:
    @staticmethod
    def criar_usuario(dados, senha, role):
        usuario = Usuario(
            nome=dados["nome"],
            email=dados["email"],
            telefone=dados["telefone"],
            cpf=dados["cpf"],
            data_nascimento=dados["data_nascimento"],
            pais=dados["pais"],
            cep=dados["cep"] or None,
            estado=dados["estado"] or None,
            cidade=dados["cidade"] or None,
            bairro=dados["bairro"] or None,
            endereco=dados["endereco"] or None,
            numero=dados["numero"] or None,
            complemento=dados["complemento"] or None,
            role=role,
        )
        usuario.set_senha(senha)
        return usuario

    @staticmethod
    def criar_tecnico(usuario, dados_tecnico, foto_perfil, diplomas_arquivos):
        upload_folder = current_app.config["UPLOAD_FOLDER"]
        nome_foto = salvar_arquivo(foto_perfil, upload_folder + "/perfil")

        perfil = PerfilTecnico(
            especialidade=dados_tecnico["especialidade"],
            escolaridade=dados_tecnico["escolaridade"],
            curso_superior=dados_tecnico["curso_superior"] or None,
            regiao_atendimento=dados_tecnico["regiao_atendimento"],
            cursos_experiencias=dados_tecnico["cursos_experiencias"] or None,
            especializacoes=dados_tecnico["especializacoes"] or None,
            foto_perfil=nome_foto,
        )

        for arquivo in diplomas_arquivos:
            nome_arquivo = salvar_arquivo(arquivo, upload_folder + "/diplomas")
            perfil.diplomas.append(Diploma(arquivo=nome_arquivo))

        usuario.perfil_tecnico = perfil
        return usuario

    @staticmethod
    def validar_dados_comuns(dados, senha, confirmar_senha):
        if not dados["nome"] or len(dados["nome"]) < 3:
            return "Informe seu nome completo."
        if not dados["email"] or "@" not in dados["email"]:
            return "Informe um email válido."
        if not dados["telefone"]:
            return "Informe um telefone válido."
        if not dados["cpf"] or len(dados["cpf"]) != 11:
            return "Informe um CPF válido."
        if Usuario.query.filter_by(cpf=dados["cpf"]).first() is not None:
            return "Já existe uma conta com este CPF."
        if Usuario.query.filter_by(email=dados["email"]).first() is not None:
            return "Já existe uma conta com este email."
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

    @staticmethod
    def validar_tecnico(dados_tecnico, foto_perfil, diplomas_arquivos):
        if not dados_tecnico.get("especialidade"):
            return "Informe sua especialidade."
        if dados_tecnico.get("escolaridade") not in {"Ensino médio", "Técnico", "Superior cursando", "Superior completo"}:
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

    @staticmethod
    def salvar(usuario):
        db.session.add(usuario)
        db.session.commit()
        return usuario
