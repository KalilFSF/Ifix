# Ponto de entrada da aplicação: monta o Flask app (application factory),
# liga o SQLAlchemy/Flask-Login e registra os módulos (Monólito Modular:
# cada módulo de domínio tem seu próprio routes/controllers/services/
# models/repositories — ver backend/modules/). É este arquivo que você
# roda: `python app.py`.

import os
import socket

from flask import Flask, jsonify, redirect, request
from flask_login import LoginManager

from config import Config
from database import db
from modules.usuarios.models.usuario import Usuario

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
# O front-end (HTML/CSS/JS puro) mora numa pasta irmã (frontend/), fora do backend/.
FRONTEND_DIR = os.path.join(os.path.dirname(BACKEND_DIR), "frontend")


def create_app():
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
    app.config.from_object(Config)

    db.init_app(app)

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
        return db.session.get(Usuario, int(user_id))

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

    # Import tardio (depois do login_manager pronto) pra evitar import circular
    # entre os módulos e app.py.
    from page_routes import pages_bp
    from modules.atendimentos.routes import atendimentos_bp
    from modules.servicos.routes import servicos_bp
    from modules.usuarios.routes import usuarios_bp

    app.register_blueprint(pages_bp)
    app.register_blueprint(usuarios_bp)
    app.register_blueprint(servicos_bp)
    app.register_blueprint(atendimentos_bp)

    # Garante que as pastas usadas pelo app existam antes de qualquer upload/uso,
    # já que elas não são versionadas no git (uploads de usuário, banco local).
    os.makedirs(os.path.join(app.config["UPLOAD_FOLDER"], "perfil"), exist_ok=True)
    os.makedirs(os.path.join(app.config["UPLOAD_FOLDER"], "diplomas"), exist_ok=True)
    os.makedirs(os.path.join(app.config["UPLOAD_FOLDER"], "chamados"), exist_ok=True)
    os.makedirs(os.path.join(BACKEND_DIR, "database"), exist_ok=True)

    # As Models de todo módulo precisam estar importadas (registradas no
    # metadata do SQLAlchemy) antes do create_all() — os imports acima já
    # importam os módulos inteiros (routes -> controllers -> services ->
    # models), então a esta altura já estão todas carregadas.
    with app.app_context():
        db.create_all()
        _garantir_colunas_servicos()

    return app


def _garantir_colunas_servicos():
    """Migration leve sem Alembic: adiciona colunas novas em servicos se o
    SQLite antigo ainda não as tiver (create_all não altera tabelas existentes)."""
    from sqlalchemy import inspect, text

    inspector = inspect(db.engine)
    if "servicos" not in inspector.get_table_names():
        return
    colunas = {coluna["name"] for coluna in inspector.get_columns("servicos")}
    alteracoes = []
    if "tipo_equipamento" not in colunas:
        alteracoes.append(
            "ALTER TABLE servicos ADD COLUMN tipo_equipamento "
            "VARCHAR(20) NOT NULL DEFAULT 'notebook'"
        )
    if "garantia" not in colunas:
        alteracoes.append(
            "ALTER TABLE servicos ADD COLUMN garantia "
            "BOOLEAN NOT NULL DEFAULT 0"
        )
    if not alteracoes:
        return
    with db.engine.begin() as conn:
        for sql in alteracoes:
            conn.execute(text(sql))


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

    app.run(host="0.0.0.0", port=port, debug=True)
