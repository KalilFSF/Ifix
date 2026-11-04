"""Inicializa Flask, sessão, rotas e erros HTTP; não cria schema ou registros no startup."""
# Ponto de entrada da aplicação: monta o Flask app (application factory),
# liga o SQLAlchemy/Flask-Login e registra os módulos (Monólito Modular:
# cada módulo de domínio tem seu próprio routes/controllers/services/
# models/repositories — ver backend/modules/). É este arquivo que você
# roda: `python app.py`.

import os
import socket
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, jsonify, redirect, request
from flask_login import LoginManager

from config import Config
from database import db
from exceptions import DominioError
from modules.usuarios.models.usuario import Usuario

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
# O front-end (HTML/CSS/JS puro) mora numa pasta irmã (frontend/), fora do backend/.
FRONTEND_DIR = os.path.join(os.path.dirname(BACKEND_DIR), "frontend")


def create_app(config_override=None):
    # Sem Jinja: frontend/ é servido inteiro como arquivo estático "puro".
    # static_url_path="" tira o prefixo /static, então frontend/index.html
    # vira a URL /index.html, frontend/css/style.css vira /css/style.css,
    # frontend/uploads/perfil/x.jpg vira /uploads/perfil/x.jpg, etc. — os
    # próprios arquivos HTML referenciam esses caminhos direto (ex:
    # <link href="/css/style.css">), sem precisar de url_for().
    app = Flask(
        __name__,
        static_folder=FRONTEND_DIR,
        static_url_path="",
    )
    app.config.from_mapping(Config.from_environment() if config_override is None else config_override)
    from serialization import IFixJSONProvider
    app.json = IFixJSONProvider(app)

    db.init_app(app)
    import retention
    from http_security import install_security
    app.config.setdefault("MAX_CONTENT_LENGTH",4*1024*1024)
    install_security(app)

    # Flask-Login cuida da sessão do usuário logado (cookie de sessão).
    # login_view é a rota para onde um usuário não autenticado é mandado
    # ao tentar acessar uma página com @login_required (ex: /cliente/home).
    login_manager = LoginManager()
    login_manager.login_view = "pages.index"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        # Flask-Login chama isso a cada request pra recarregar o usuário
        # a partir do id guardado no cookie de sessão.
        from http_security import BINDING_KEY,session_scope
        from flask import session
        if session.get(BINDING_KEY) != session_scope():
            return None
        try:
            return db.session.get(Usuario, int(user_id))
        except (TypeError,ValueError):
            return None

    @login_manager.unauthorized_handler
    def unauthorized():
        # Comportamento padrão do Flask-Login é sempre redirecionar pro
        # login_view. Isso é certo pra uma página (ex: /cliente/home), mas
        # quebraria uma chamada de API: o fetch seguiria o redirect, cairia
        # na página de login (HTML) e o `.json()` do JS falharia. Então,
        # pra rotas /api/..., devolve 401 em JSON em vez de redirecionar.
        if request.path.startswith("/api/"):
            return jsonify(ok=False, erro="Não autenticado."), 401
        return redirect("/")

    @app.errorhandler(DominioError)
    def tratar_erro_dominio(erro):
        # Rede de segurança: qualquer DominioError que suba de um Service sem
        # passar por um try/except de Controller vira a resposta certa (400/
        # 403/404/409) em vez de um 500 genérico do Flask. Os Controllers
        # antigos ainda tratam na mão; os novos podem só deixar propagar.
        return jsonify({"ok": False, "erro": erro.mensagem, **erro.extra}), erro.status_code

    @app.before_request
    def prevent_static_api_fallback():
        if request.path.startswith("/api/") and request.endpoint == "static":
            from werkzeug.routing import Map
            api_map = Map([rule.empty() for rule in app.url_map.iter_rules() if rule.endpoint != "static"])
            # 405 para um endpoint conhecido; 404 para uma API inexistente.
            api_map.bind(request.host).match(request.path,method=request.method)

    from werkzeug.exceptions import HTTPException
    from sqlalchemy.exc import SQLAlchemyError,OperationalError

    @app.errorhandler(HTTPException)
    def api_http_error(error):
        if not request.path.startswith("/api/"):
            return error
        messages = {400:"Requisição inválida.",401:"Não autenticado.",403:"Acesso negado.",404:"Recurso não encontrado.",
                    405:"Método não permitido.",413:"O envio excede o limite total de 4 MB.",429:"Muitas tentativas. Aguarde e tente novamente.",503:"Serviço temporariamente indisponível."}
        message = error.description if error.code in {403,429,503} else messages.get(error.code,"Não foi possível concluir a requisição.")
        response = jsonify(ok=False,erro=message)
        response.status_code = error.code or 500
        retry = error.get_headers()
        for key,value in retry:
            if key.lower() in {"retry-after","allow"}:
                response.headers[key] = value
        return response

    @app.errorhandler(Exception)
    def unexpected_error(error):
        db.session.rollback()
        # Nunca registrar str(error), parâmetros SQL, URL ou traceback: podem conter segredos.
        from database_errors import mysql_error_info
        code,category = mysql_error_info(error)
        if isinstance(error,SQLAlchemyError):
            app.logger.error("Falha de banco (%s; codigo=%s; categoria=%s).",
                type(error).__name__,code if code is not None else "indisponivel",category)
        else:
            app.logger.error("Falha interna (%s).",type(error).__name__)
        status = 409 if isinstance(error,OperationalError) and code in {1205,1213} else 500
        if request.path.startswith("/api/"):
            return jsonify(ok=False,erro="Operação concorrente. Tente novamente." if status==409 else "Não foi possível concluir a operação."),status
        return "Não foi possível abrir esta página.",status

    # Import tardio (depois do login_manager pronto) pra evitar import circular
    # entre os módulos e app.py.
    from page_routes import pages_bp
    from modules.atendimentos.routes import atendimentos_bp
    from modules.chat.routes import chat_bp
    from modules.notificacoes.routes import notificacoes_bp
    from modules.servicos.routes import servicos_bp
    from modules.usuarios.routes import usuarios_bp

    app.register_blueprint(pages_bp)
    app.register_blueprint(usuarios_bp)
    app.register_blueprint(servicos_bp)
    app.register_blueprint(atendimentos_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(notificacoes_bp)

    # Garante que as pastas usadas pelo app existam antes de qualquer upload/uso,
    # já que elas não são versionadas no git (uploads de usuário).
    if not os.environ.get("VERCEL"):
        os.makedirs(os.path.join(app.config["UPLOAD_FOLDER"], "perfil"), exist_ok=True)
        os.makedirs(os.path.join(app.config["UPLOAD_FOLDER"], "diplomas"), exist_ok=True)
        os.makedirs(os.path.join(app.config["UPLOAD_FOLDER"], "chamados"), exist_ok=True)

    return app


app = create_app()


def get_local_ip():
    """Descobre o IP da máquina na rede local, só pra exibir no console ao iniciar."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Não envia nada de fato: só usa uma conexão UDP "fake" pra perguntar
        # ao sistema operacional qual interface de rede seria usada.
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        sock.close()


if __name__ == "__main__":
    port = 5000
    local_ip = get_local_ip()

    # host="0.0.0.0" faz o servidor escutar em todas as interfaces de rede,
    # não só localhost — por isso dá pra acessar de outro aparelho na mesma rede.
    # Com debug=True o Flask usa um reloader que reinicia o processo a cada
    # mudança de arquivo; WERKZEUG_RUN_MAIN só existe no processo "de verdade"
    # (o filho), então isso evita imprimir a mensagem duas vezes.
    if os.environ.get("WERKZEUG_RUN_MAIN"):
        print(f" * Acesse pelo seu PC:      http://127.0.0.1:{port}")
        print(f" * Acesse por outro dispositivo na mesma rede: http://{local_ip}:{port}")

    app.run(host="0.0.0.0", port=port, debug=False)
