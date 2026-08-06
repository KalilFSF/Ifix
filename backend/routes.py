# Todas as rotas do app, agrupadas num Blueprint "auth" (registrado em app.py).
#
# Duas famílias de rota aqui:
#   - Páginas: servem um arquivo .html puro (sem Jinja) de frontend/,
#     só com um redirect antes se o usuário não pode ver aquela página.
#   - API (/api/...): recebem os formulários via fetch (JS) e respondem
#     em JSON, nunca em HTML — quem decide o que mostrar na tela é o JS.

import os

from flask import Blueprint, current_app, jsonify, redirect, request
from flask_login import current_user, login_required, login_user, logout_user

from config import FRONTEND_DIR
from controllers.atendimento import AtendimentoController
from controllers.auth_controller import AuthController
from controllers.servico_controller import ServicoController
from controllers.tecnico_controller import TecnicoController
from controllers.usuario_controller import UsuarioController
from database import db
from models import Usuario
from services.auth_service import AuthService
from services.cadastro import CadastroService
from utils import (
    somente_digitos,
    validar_cpf,
    validar_data_nascimento,
)

auth_bp = Blueprint("auth", __name__)

ESCOLARIDADES_VALIDAS = {"Ensino médio", "Técnico", "Superior cursando", "Superior completo"}

PAGES_DIR = os.path.join(FRONTEND_DIR, "pages")


def _home_path(usuario):
    """Monta a URL da área inicial certa pro papel do usuário
    (/cliente/home ou /tecnico/home), usada depois do login/redirects."""
    return f"/{usuario.role}/home"


def _ler_dados_comuns(form):
    """Lê do formulário os campos que cliente e técnico têm em comum
    (nome, contato, CPF, endereço). Usado tanto no cadastro de cliente
    quanto no de técnico, pra não duplicar essa leitura duas vezes."""
    return {
        "nome": form.get("nome", "").strip(),
        "email": form.get("email", "").strip().lower(),
        "telefone": form.get("telefone", "").strip(),
        "cpf": somente_digitos(form.get("cpf", "")),
        "data_nascimento": form.get("data_nascimento", "").strip(),
        "pais": form.get("pais", "").strip(),
        "cep": form.get("cep", "").strip(),
        "estado": form.get("estado", "").strip().upper(),
        "cidade": form.get("cidade", "").strip(),
        "bairro": form.get("bairro", "").strip(),
        "endereco": form.get("endereco", "").strip(),
        "numero": form.get("numero", "").strip(),
        "complemento": form.get("complemento", "").strip(),
    }


def _validar_dados_comuns(dados, senha, confirmar_senha):
    """Compatibilidade com o fluxo antigo do cadastro e validações base."""
    if not dados["nome"] or len(dados["nome"]) < 3:
        return "Informe seu nome completo."
    if not dados["email"] or "@" not in dados["email"]:
        return "Informe um email válido."
    if not dados["telefone"]:
        return "Informe um telefone válido."

    if not validar_cpf(dados["cpf"]):
        return "Informe um CPF válido."
    if Usuario.query.filter_by(cpf=dados["cpf"]).first() is not None:
        return "Já existe uma conta com este CPF."

    data_nascimento = validar_data_nascimento(dados["data_nascimento"])
    if data_nascimento is None:
        return "Informe uma data de nascimento válida (entre 01/01/1900 e hoje)."
    dados["data_nascimento"] = data_nascimento

    if not dados["pais"]:
        return "Selecione o país."

    if dados["pais"] != "Outro":
        campos_endereco = (
            dados["cep"], dados["estado"], dados["cidade"], dados["bairro"],
            dados["endereco"], dados["numero"],
        )
        if not all(campos_endereco):
            return "Preencha o endereço completo (CEP, estado, cidade, bairro, endereço e número)."

    if len(senha) < 6:
        return "A senha deve ter pelo menos 6 caracteres."
    if senha != confirmar_senha:
        return "As senhas não coincidem."
    if Usuario.query.filter_by(email=dados["email"]).first() is not None:
        return "Já existe uma conta com este email."

    return None


def _criar_usuario_base(dados, senha, role):
    """Compatibilidade com o fluxo antigo do cadastro."""
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


# ======================================================================
# PÁGINAS (servem o .html puro; a lógica de exibir erro/dado dinâmico é
# toda feita pelo JS de cada página, chamando as rotas /api/... abaixo)
# ======================================================================

@auth_bp.route("/")
def index():
    """Página de login (frontend/index.html). Se já estiver logado, pula
    direto pra área inicial certa em vez de mostrar o form de novo."""
    if current_user.is_authenticated:
        return redirect(_home_path(current_user))
    return current_app.send_static_file("index.html")


@auth_bp.route("/cadastro")
def cadastro():
    """Mostra a tela de "Cliente ou Técnico?" com os dois formulários
    escondidos (a troca entre eles é feita no JS, cadastro.js)."""
    if current_user.is_authenticated:
        return redirect(_home_path(current_user))
    return current_app.send_static_file("pages/cadastro.html")


@auth_bp.route("/cliente/home")
@login_required
def cliente_home():
    # @login_required barra quem não está logado; o if abaixo barra um
    # técnico logado de entrar na área de cliente (e vice-versa) trocando a URL.
    if current_user.role != "cliente":
        return redirect(_home_path(current_user))
    return current_app.send_static_file("pages/cliente-home.html")


@auth_bp.route("/tecnico/home")
@login_required
def tecnico_home():
    if current_user.role != "tecnico":
        return redirect(_home_path(current_user))
    return current_app.send_static_file("pages/tecnico-home.html")


@auth_bp.route("/logout")
@login_required
def logout():
    # Link normal (<a href="/logout">), não precisa passar por JSON:
    # o navegador só navega pra "/" depois de encerrar a sessão.
    logout_user()
    return redirect("/")


# ======================================================================
# API (sempre responde em JSON — quem consome é o JS das páginas)
# ======================================================================

@auth_bp.route("/api/login", methods=["POST"])
def api_login():
    return AuthController.login()


@auth_bp.route("/api/cadastro/cliente", methods=["POST"])
def api_cadastro_cliente():
    dados = _ler_dados_comuns(request.form)
    senha = request.form.get("senha", "")
    confirmar_senha = request.form.get("confirmar_senha", "")

    erro = CadastroService.validar_dados_comuns(dados, senha, confirmar_senha)
    if erro:
        return jsonify(ok=False, erro=erro), 400

    usuario = CadastroService.criar_usuario(dados, senha, "cliente")
    CadastroService.salvar(usuario)

    # Redireciona pro login (não loga automaticamente): mesmo comportamento
    # de antes, só que quem navega agora é o JS (window.location.href).
    return jsonify(ok=True, redirect="/")


@auth_bp.route("/api/cadastro/tecnico", methods=["POST"])
def api_cadastro_tecnico():
    dados = _ler_dados_comuns(request.form)
    dados_tecnico = {
        "especialidade": request.form.get("especialidade", "").strip(),
        "escolaridade": request.form.get("escolaridade", "").strip(),
        "curso_superior": request.form.get("curso_superior", "").strip(),
        "regiao_atendimento": request.form.get("regiao_atendimento", "").strip(),
        "cursos_experiencias": request.form.get("cursos_experiencias", "").strip(),
        "especializacoes": request.form.get("especializacoes", "").strip(),
    }
    senha = request.form.get("senha", "")
    confirmar_senha = request.form.get("confirmar_senha", "")

    erro = CadastroService.validar_dados_comuns(dados, senha, confirmar_senha)

    foto_perfil = request.files.get("foto_perfil")
    diplomas_arquivos = [arquivo for arquivo in request.files.getlist("diplomas") if arquivo.filename]

    if not erro:
        erro = CadastroService.validar_tecnico(dados_tecnico, foto_perfil, diplomas_arquivos)

    if erro:
        return jsonify(ok=False, erro=erro), 400

    usuario = CadastroService.criar_usuario(dados, senha, "tecnico")
    usuario = CadastroService.criar_tecnico(usuario, dados_tecnico, foto_perfil, diplomas_arquivos)
    CadastroService.salvar(usuario)

    return jsonify(ok=True, redirect="/")


@auth_bp.route("/api/me")
@login_required
def api_me():
    return UsuarioController.me()


@auth_bp.route("/api/me", methods=["PATCH"])
@login_required
def api_atualizar_me():
    return UsuarioController.atualizar_me()


@auth_bp.route("/api/tecnicos")
@login_required
def api_tecnicos():
    return UsuarioController.listar_tecnicos()


@auth_bp.route("/api/tecnico/perfil")
@login_required
def api_perfil_tecnico():
    return TecnicoController.perfil()


@auth_bp.route("/api/tecnico/perfil", methods=["PATCH"])
@login_required
def api_atualizar_perfil_tecnico():
    return TecnicoController.atualizar_perfil()


@auth_bp.route("/api/servicos", methods=["GET"])
def api_servicos():
    return ServicoController.listar()


@auth_bp.route("/api/servicos", methods=["POST"])
@login_required
def api_criar_servico():
    return ServicoController.criar()


@auth_bp.route("/api/servicos/<int:servico_id>")
@login_required
def api_detalhes_servico(servico_id):
    return ServicoController.detalhes(servico_id)


@auth_bp.route("/api/servicos/<int:servico_id>/aceitar", methods=["POST"])
@login_required
def api_aceitar_servico(servico_id):
    return ServicoController.atribuir_tecnico(servico_id)


@auth_bp.route("/api/servicos/<int:servico_id>/status", methods=["PATCH"])
@login_required
def api_status_servico(servico_id):
    return ServicoController.atualizar_status(servico_id)


@auth_bp.route("/api/servicos/<int:servico_id>/atendimentos", methods=["POST"])
@login_required
def api_criar_atendimento(servico_id):
    return ServicoController.criar_atendimento(servico_id)


@auth_bp.route("/api/atendimentos")
@login_required
def api_atendimentos():
    return AtendimentoController.listar()


@auth_bp.route("/api/atendimentos/<int:atendimento_id>/status", methods=["PATCH"])
@login_required
def api_status_atendimento(atendimento_id):
    return AtendimentoController.atualizar_status(atendimento_id)
