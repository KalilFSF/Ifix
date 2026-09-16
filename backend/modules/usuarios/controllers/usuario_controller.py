from flask import jsonify, request
from flask_login import current_user, login_required

from exceptions import DominioError
from modules.usuarios.services.alterar_senha_service import AlterarSenhaService
from modules.usuarios.services.atualizar_usuario_service import AtualizarUsuarioService
from modules.usuarios.services.definir_foto_perfil_service import DefinirFotoPerfilService
from modules.usuarios.services.cadastrar_cliente_service import CadastrarClienteService
from modules.usuarios.services.cadastrar_tecnico_service import CadastrarTecnicoService
from modules.usuarios.services.converter_para_tecnico_service import ConverterParaTecnicoService
from modules.usuarios.services.definir_horario_atendimento_service import DefinirHorarioAtendimentoService
from modules.usuarios.services.listar_tecnicos_service import ListarTecnicosService
from utils import corpo_json, parsear_coordenada, somente_digitos


class UsuarioController:
    def __init__(self):
        self.cadastrar_cliente_service = CadastrarClienteService()
        self.cadastrar_tecnico_service = CadastrarTecnicoService()
        self.listar_tecnicos_service = ListarTecnicosService()
        self.atualizar_usuario_service = AtualizarUsuarioService()
        self.converter_para_tecnico_service = ConverterParaTecnicoService()
        self.definir_horario_atendimento_service = DefinirHorarioAtendimentoService()
        self.definir_foto_perfil_service = DefinirFotoPerfilService()
        self.alterar_senha_service = AlterarSenhaService()

    @login_required
    def me(self):
        """Payload base do usuário logado. A tela de perfil consome isto —
        por isso vem o endereço completo e o `perfil` técnico inteiro, e não
        só os três campos que a sidebar usava."""
        usuario = current_user
        dados = usuario.to_dict()

        if usuario.eh_tecnico and usuario.perfil_tecnico:
            perfil = usuario.perfil_tecnico
            dados["perfil"] = perfil.to_dict()
            dados["diplomas"] = [diploma.to_dict() for diploma in perfil.diplomas]
            # Mantidos no nível de cima por compatibilidade: role-chips.js e
            # o painel do técnico já liam daqui.
            dados["especialidade"] = perfil.especialidade
            dados["regiao_atendimento"] = perfil.regiao_atendimento
            dados["diplomas_count"] = len(perfil.diplomas)

        return jsonify(dados)

    @login_required
    def definir_horario_atendimento(self):
        # Sem try/except: DominioError sobe pro errorhandler global (app.py).
        dados = corpo_json()
        usuario = self.definir_horario_atendimento_service.executar(current_user, dados)
        return jsonify({
            "ok": True,
            "horario_inicio_atendimento": usuario.horario_inicio_atendimento,
            "horario_fim_atendimento": usuario.horario_fim_atendimento,
        })

    def cadastrar_cliente(self):
        dados = self._ler_dados_comuns(request.form)
        senha = request.form.get("senha", "")
        confirmar_senha = request.form.get("confirmar_senha", "")

        try:
            self.cadastrar_cliente_service.executar(dados, senha, confirmar_senha)
        except DominioError as erro:
            return jsonify(ok=False, erro=erro.mensagem, **erro.extra), erro.status_code

        # Redireciona pro login (não loga automaticamente).
        return jsonify(ok=True, redirect="/")

    def cadastrar_tecnico(self):
        dados = self._ler_dados_comuns(request.form)
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
        foto_perfil = request.files.get("foto_perfil")
        diplomas_arquivos = [arquivo for arquivo in request.files.getlist("diplomas") if arquivo.filename]

        try:
            self.cadastrar_tecnico_service.executar(dados, dados_tecnico, senha, confirmar_senha, foto_perfil, diplomas_arquivos)
        except DominioError as erro:
            return jsonify(ok=False, erro=erro.mensagem, **erro.extra), erro.status_code

        return jsonify(ok=True, redirect="/")

    @login_required
    def listar_tecnicos(self):
        return jsonify(self.listar_tecnicos_service.executar())

    @login_required
    def atualizar_me(self):
        dados = corpo_json()
        usuario = self.atualizar_usuario_service.executar(current_user, dados)
        return jsonify({"ok": True, "usuario": usuario.to_dict()})

    @login_required
    def definir_foto_perfil(self):
        usuario = self.definir_foto_perfil_service.executar(
            current_user, request.files.get("foto_perfil")
        )
        return jsonify({"ok": True, "foto_perfil": usuario.foto_perfil})

    @login_required
    def alterar_senha(self):
        dados = corpo_json()
        self.alterar_senha_service.executar(current_user, dados)
        return jsonify({"ok": True})

    @login_required
    def tornar_tecnico(self):
        if current_user.eh_tecnico:
            return jsonify({"ok": False, "erro": "Esta conta já possui perfil de técnico."}), 403

        dados_tecnico = {
            "especialidade": request.form.get("especialidade", "").strip(),
            "escolaridade": request.form.get("escolaridade", "").strip(),
            "curso_superior": request.form.get("curso_superior", "").strip(),
            "regiao_atendimento": request.form.get("regiao_atendimento", "").strip(),
            "cursos_experiencias": request.form.get("cursos_experiencias", "").strip(),
            "especializacoes": request.form.get("especializacoes", "").strip(),
        }
        foto_perfil = request.files.get("foto_perfil")
        diplomas_arquivos = [arquivo for arquivo in request.files.getlist("diplomas") if arquivo.filename]
        latitude = parsear_coordenada(request.form.get("latitude"))
        longitude = parsear_coordenada(request.form.get("longitude"))

        try:
            self.converter_para_tecnico_service.executar(
                current_user, dados_tecnico, foto_perfil, diplomas_arquivos, latitude, longitude
            )
        except DominioError as erro:
            return jsonify({"ok": False, "erro": erro.mensagem}), erro.status_code

        return jsonify({"ok": True, "redirect": "/tecnico/home"})

    @staticmethod
    def _ler_dados_comuns(form):
        """Lê do formulário os campos que cliente e técnico têm em comum
        (nome, contato, CPF, endereço) — parsing puro da requisição."""
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
            "latitude": parsear_coordenada(form.get("latitude")),
            "longitude": parsear_coordenada(form.get("longitude")),
        }
