from flask import jsonify, request
from flask_login import current_user, login_required

from exceptions import DominioError
from modules.atendimentos.services.avaliar_service import AvaliarService
from modules.atendimentos.services.listar_avaliacoes_service import ListarAvaliacoesService
from modules.atendimentos.services.listar_orcamentos_service import ListarOrcamentosService
from modules.servicos.services.atribuir_tecnico_service import AtribuirTecnicoService
from modules.servicos.services.atualizar_status_servico_service import AtualizarStatusServicoService
from modules.servicos.services.cancelar_servico_service import CancelarServicoService, ExcluirServicoService
from modules.servicos.services.criar_servico_service import CriarServicoService
from modules.servicos.services.listar_meus_servicos_service import ListarMeusServicosService
from modules.servicos.services.obter_detalhes_servico_service import ObterDetalhesServicoService
from modules.servicos.services.obter_historico_servico_service import ObterHistoricoServicoService
from modules.servicos.services.solicitar_tecnicos_service import SolicitarTecnicosService


class ServicoController:
    def __init__(self):
        self.criar_servico_service = CriarServicoService()
        self.listar_meus_servicos_service = ListarMeusServicosService()
        self.obter_detalhes_servico_service = ObterDetalhesServicoService()
        self.atualizar_status_servico_service = AtualizarStatusServicoService()
        self.obter_historico_servico_service = ObterHistoricoServicoService()
        self.solicitar_tecnicos_service = SolicitarTecnicosService()
        self.atribuir_tecnico_service = AtribuirTecnicoService()
        self.cancelar_servico_service = CancelarServicoService()
        self.excluir_servico_service = ExcluirServicoService()
        self.listar_orcamentos_service = ListarOrcamentosService()
        self.avaliar_service = AvaliarService()
        self.listar_avaliacoes_service = ListarAvaliacoesService()

    @login_required
    def meus(self):
        status = request.args.get("status")
        # ?como=cliente|tecnico — técnico no modo cliente lista o que abriu;
        # no painel técnico lista o que atende. Sem o parâmetro, usa o role.
        como = (request.args.get("como") or current_user.role or "").strip().lower()
        if como not in {"cliente", "tecnico"}:
            return jsonify({"ok": False, "erro": "Parâmetro 'como' inválido."}), 400
        if como == "tecnico" and not current_user.eh_tecnico:
            return jsonify({"ok": False, "erro": "Acesso negado."}), 403

        servicos = self.listar_meus_servicos_service.executar(current_user.id, como, status)
        return jsonify([servico.to_dict_painel() for servico in servicos])

    @login_required
    def criar(self):
        # Aceita JSON ou multipart (com fotos). Qualquer usuário autenticado
        # pode abrir chamado — inclusive quem também é técnico.
        if request.content_type and "multipart/form-data" in request.content_type:
            dados = {
                "tipo_equipamento": (request.form.get("tipo_equipamento") or "").strip(),
                "categoria": (request.form.get("categoria") or "").strip(),
                "equipamento": (request.form.get("equipamento") or "").strip(),
                "titulo": (request.form.get("titulo") or "").strip(),
                "descricao": (request.form.get("descricao") or "").strip(),
                "preco_estimado": request.form.get("preco_estimado") or 0,
                "garantia": request.form.get("garantia"),
                "latitude": request.form.get("latitude"),
                "longitude": request.form.get("longitude"),
            }
            fotos = [f for f in request.files.getlist("fotos") if f and f.filename]
        else:
            dados = request.get_json(silent=True) or {}
            fotos = []

        try:
            servico = self.criar_servico_service.executar(dados, current_user, fotos)
        except DominioError as erro:
            return jsonify({"ok": False, "erro": erro.mensagem}), erro.status_code

        return jsonify({"ok": True, "servico": servico.to_dict()})

    @login_required
    def detalhes(self, servico_id):
        try:
            servico = self.obter_detalhes_servico_service.executar(servico_id)
        except DominioError as erro:
            return jsonify({"ok": False, "erro": erro.mensagem}), erro.status_code

        payload = servico.to_dict()
        payload["atendimentos"] = [atendimento.to_dict() for atendimento in servico.atendimentos]
        return jsonify(payload)

    @login_required
    def atualizar_status(self, servico_id):
        dados = request.get_json(silent=True) or {}
        status = dados.get("status")
        if not status:
            return jsonify({"ok": False, "erro": "Status é obrigatório."}), 400

        try:
            servico = self.atualizar_status_servico_service.executar(servico_id, status, current_user)
        except DominioError as erro:
            return jsonify({"ok": False, "erro": erro.mensagem}), erro.status_code

        return jsonify({"ok": True, "servico": servico.to_dict()})

    @login_required
    def cancelar(self, servico_id):
        try:
            servico = self.cancelar_servico_service.executar(servico_id, current_user)
        except DominioError as erro:
            return jsonify({"ok": False, "erro": erro.mensagem}), erro.status_code

        return jsonify({"ok": True, "servico": servico.to_dict()})

    @login_required
    def excluir(self, servico_id):
        try:
            self.excluir_servico_service.executar(servico_id, current_user)
        except DominioError as erro:
            return jsonify({"ok": False, "erro": erro.mensagem}), erro.status_code

        return jsonify({"ok": True, "excluido": True})

    @login_required
    def historico(self, servico_id):
        try:
            entradas = self.obter_historico_servico_service.executar(servico_id, current_user)
        except DominioError as erro:
            return jsonify({"ok": False, "erro": erro.mensagem}), erro.status_code

        return jsonify([entrada.to_dict() for entrada in entradas])

    @login_required
    def orcamentos(self, servico_id):
        try:
            atendimentos = self.listar_orcamentos_service.executar(servico_id, current_user)
        except DominioError as erro:
            return jsonify({"ok": False, "erro": erro.mensagem}), erro.status_code

        return jsonify([atendimento.to_dict_com_tecnico() for atendimento in atendimentos])

    @login_required
    def avaliar(self, servico_id):
        dados = request.get_json(silent=True) or {}
        try:
            avaliacao = self.avaliar_service.executar(servico_id, current_user, dados)
        except DominioError as erro:
            return jsonify({"ok": False, "erro": erro.mensagem}), erro.status_code

        return jsonify({"ok": True, "avaliacao": avaliacao.to_dict()})

    @login_required
    def avaliacoes(self, servico_id):
        try:
            avaliacoes = self.listar_avaliacoes_service.executar(servico_id, current_user)
        except DominioError as erro:
            return jsonify({"ok": False, "erro": erro.mensagem}), erro.status_code

        return jsonify([avaliacao.to_dict() for avaliacao in avaliacoes])

    @login_required
    def solicitar(self, servico_id):
        dados = request.get_json(silent=True) or {}
        tecnico_ids = dados.get("tecnico_ids") or []
        # Dono do chamado pode solicitar técnicos (mesmo sendo técnico em outra conta).
        if not tecnico_ids:
            return jsonify({"ok": False, "erro": "Informe ao menos um tecnico_id."}), 400

        try:
            solicitacoes = self.solicitar_tecnicos_service.executar(servico_id, tecnico_ids, current_user)
        except DominioError as erro:
            return jsonify({"ok": False, "erro": erro.mensagem}), erro.status_code

        return jsonify({"ok": True, "solicitacoes": [solicitacao.to_dict() for solicitacao in solicitacoes]})

    @login_required
    def atribuir_tecnico(self, servico_id):
        """Legado — ver AtribuirTecnicoService."""
        if not current_user.eh_tecnico:
            return jsonify({"ok": False, "erro": "Apenas técnicos podem aceitar serviços."}), 403

        try:
            servico = self.atribuir_tecnico_service.executar(servico_id, current_user.id)
        except DominioError as erro:
            return jsonify({"ok": False, "erro": erro.mensagem}), erro.status_code

        return jsonify({"ok": True, "servico": servico.to_dict()})
