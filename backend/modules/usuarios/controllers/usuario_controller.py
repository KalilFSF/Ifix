from flask import jsonify, request
from flask_login import current_user, login_required

from exceptions import DominioError
from modules.usuarios.services.atualizar_usuario_service import AtualizarUsuarioService
from modules.usuarios.services.cadastrar_cliente_service import CadastrarClienteService
from modules.usuarios.services.cadastrar_tecnico_service import CadastrarTecnicoService
from modules.usuarios.services.converter_para_tecnico_service import ConverterParaTecnicoService
from modules.usuarios.services.listar_tecnicos_service import ListarTecnicosService
from utils import parsear_coordenada, somente_digitos


class UsuarioController:
    def __init__(self):
        self.cadastrar_cliente_service = CadastrarClienteService()
        self.cadastrar_tecnico_service = CadastrarTecnicoService()
        self.listar_tecnicos_service = ListarTecnicosService()
        self.atualizar_usuario_service = AtualizarUsuarioService()
        self.converter_para_tecnico_service = ConverterParaTecnicoService()

    @login_required
    def me(self):
        usuario = current_user
        dados = {
            "id": usuario.id,
            "nome": usuario.nome,
            "email": usuario.email,
            "telefone": usuario.telefone,
            "cidade": usuario.cidade,
            "estado": usuario.estado,
            "role": usuario.role,
            "eh_tecnico": usuario.eh_tecnico,
        }

        if usuario.eh_tecnico and usuario.perfil_tecnico:
            perfil = usuario.perfil_tecnico
            dados.update({
                "especialidade": perfil.especialidade,
                "regiao_atendimento": perfil.regiao_atendimento,
                "foto_perfil": perfil.foto_perfil,
                "diplomas_count": len(perfil.diplomas),
            })

        return jsonify(dados)

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
        tecnicos = self.listar_tecnicos_service.executar()
        return jsonify([tecnico.to_dict() for tecnico in tecnicos])

    @login_required
    def atualizar_me(self):
        dados = request.get_json(silent=True) or {}
        usuario = self.atualizar_usuario_service.executar(current_user, dados)
        return jsonify({"ok": True, "usuario": usuario.to_dict()})

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
