# Rotas de PÁGINA (servem um arquivo .html puro de frontend/, só com um
# redirect antes se o usuário não pode ver aquela página). Não é um módulo
# de domínio — não toca Model/Service, só decide qual página HTML mostrar
# pro papel/sessão atual. A lógica de "o que mostrar na tela" é toda do
# JS de cada página, que chama a API dos módulos em modules/*/routes.py.

from flask import Blueprint, current_app, redirect
from flask_login import current_user, login_required, logout_user

pages_bp = Blueprint("pages", __name__)


def _home_path(usuario):
    """Monta a URL da área inicial certa pro papel do usuário
    (/cliente/home ou /tecnico/home), usada depois do login/redirects."""
    return f"/{usuario.role}/home"


@pages_bp.route("/")
def index():
    """Página de login (frontend/index.html). Se já estiver logado, pula
    direto pra área inicial certa em vez de mostrar o form de novo."""
    if current_user.is_authenticated:
        return redirect(_home_path(current_user))
    return current_app.send_static_file("index.html")


@pages_bp.route("/cadastro")
def cadastro():
    """Mostra a tela de "Cliente ou Técnico?" com os dois formulários
    escondidos (a troca entre eles é feita no JS, cadastro.js)."""
    if current_user.is_authenticated:
        return redirect(_home_path(current_user))
    return current_app.send_static_file("pages/cadastro.html")


@pages_bp.route("/cliente/home")
@login_required
def cliente_home():
    # @login_required barra quem não está logado; o if abaixo barra um
    # técnico logado de entrar na área de cliente (e vice-versa) trocando a URL.
    if current_user.role != "cliente":
        return redirect(_home_path(current_user))
    return current_app.send_static_file("pages/cliente-home.html")


@pages_bp.route("/tecnico/home")
@login_required
def tecnico_home():
    if current_user.role != "tecnico":
        return redirect(_home_path(current_user))
    return current_app.send_static_file("pages/tecnico-home.html")


@pages_bp.route("/cliente/chamados")
@login_required
def cliente_chamados():
    if current_user.role != "cliente":
        return redirect(_home_path(current_user))
    return current_app.send_static_file("pages/cliente-chamados.html")


@pages_bp.route("/cliente/tornar-tecnico")
@login_required
def cliente_tornar_tecnico():
    if current_user.role != "cliente":
        return redirect(_home_path(current_user))
    return current_app.send_static_file("pages/tornar-tecnico.html")


@pages_bp.route("/logout")
@login_required
def logout():
    # Link normal (<a href="/logout">), não precisa passar por JSON:
    # o navegador só navega pra "/" depois de encerrar a sessão.
    logout_user()
    return redirect("/")
